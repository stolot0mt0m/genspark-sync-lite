#!/usr/bin/env python3
"""
GenSpark AI Drive HTTP API Client
Lightweight API client using direct HTTP calls (no browser automation)
"""

import requests
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import browser_cookie3


class GenSparkAPIClient:
    """HTTP client for GenSpark AI Drive API"""
    
    BASE_URL = "https://www.genspark.ai"
    AI_DRIVE_URL = f"{BASE_URL}/aidrive/files/"  # Web UI for AI Drive
    API_BASE = f"{BASE_URL}/api/aidrive"  # API base path
    
    def __init__(self):
        self.session = requests.Session()
        self.logger = logging.getLogger('GenSparkAPI')
        self.cookies_loaded = False
        
        # Add browser-like headers to avoid detection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
            'Referer': 'https://www.genspark.ai/aidrive/files/',
            'Origin': 'https://www.genspark.ai',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        })
        
    def load_cookies_from_chrome(self) -> bool:
        """Extract session cookies from Chrome browser"""
        try:
            self.logger.info("Loading cookies from Chrome...")
            
            # Extract cookies from Chrome for genspark.ai domain
            cookies = browser_cookie3.chrome(domain_name='genspark.ai')
            
            # Add cookies to session
            for cookie in cookies:
                self.session.cookies.set_cookie(cookie)
            
            self.cookies_loaded = True
            self.logger.info(f"Loaded {len(self.session.cookies)} cookies from Chrome")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load cookies: {e}")
            return False
    
    def list_files(self, limit: int = 100, folder_path: str = None) -> Optional[List[Dict[str, Any]]]:
        """
        List all files and folders in AI Drive
        
        Args:
            limit: Maximum number of items to retrieve (default: 100)
            folder_path: Optional folder path to list (e.g., "/GitHub_Deployment")
            
        Returns:
            List of file/folder dictionaries or None on error
        """
        try:
            # Discovered from Chrome DevTools:
            # Root: GET /api/aidrive/ls/files/?filter_type=all&sort_by=modified_desc&file_type=all
            # Folder: GET /api/aidrive/ls/files/{folder_name}/?filter_type=all&sort_by=modified_desc&file_type=all
            
            if folder_path:
                # Remove leading slash for URL
                folder_name = folder_path.lstrip('/')
                url = f"{self.API_BASE}/ls/files/{folder_name}/"
            else:
                url = f"{self.API_BASE}/ls/files/"
            
            params = {
                "filter_type": "all",
                "sort_by": "modified_desc",
                "file_type": "all"
            }
            
            self.logger.debug(f"Listing files: {url}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            self.logger.info(f"Retrieved {len(items)} items from AI Drive" + (f" (folder: {folder_path})" if folder_path else ""))
            return items
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to list files: {e}")
            return None
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific file"""
        try:
            # File metadata is part of list response
            # For now, we filter from list_files()
            files = self.list_files()
            if files:
                for file in files:
                    if file.get("id") == file_id:
                        return file
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get file metadata: {e}")
            return None
    
    def download_file(self, file_id: str, file_name: str, file_path: str, destination: Path) -> bool:
        """
        Download a file from AI Drive
        
        Args:
            file_id: Unique file ID  
            file_name: Original filename
            file_path: Full path from API (e.g. "/folder/file.txt" or "/file.txt")
            destination: Local path to save file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # GenSpark uses path-based download endpoint
            # Pattern: /api/aidrive/download/files{path}
            # Examples:
            #   /api/aidrive/download/files/beschreibung.txt (root file)
            #   /api/aidrive/download/files/GitHub_Deployment/DEPLOYMENT_INSTRUCTIONS.md (in folder)
            
            # Remove leading slash from path for URL construction
            clean_path = file_path.lstrip('/')
            url = f"{self.BASE_URL}/api/aidrive/download/files/{clean_path}"
            
            self.logger.info(f"Downloading: {file_name}")
            
            # Follow redirects to Azure Blob Storage
            response = self.session.get(url, stream=True, timeout=60, allow_redirects=True)
            response.raise_for_status()
            
            # Write to destination
            destination.parent.mkdir(parents=True, exist_ok=True)
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.logger.info(f"Downloaded: {file_name} → {destination}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download {file_name}: {e}")
            return False
    
    def request_upload_url(self, filename: str, filesize: int = 0) -> Optional[tuple]:
        """
        Request upload URL from GenSpark (Step 1 of 3-step upload)
        
        Args:
            filename: Name of file to upload
            filesize: Size of file in bytes (not used currently)
            
        Returns:
            Tuple of (upload_url, token) or None
        """
        try:
            # Discovered from Chrome DevTools:
            # GET /api/aidrive/get_upload_url/files/{filename}
            from urllib.parse import quote
            # CRITICAL: safe='/' preserves folder structure (e.g., "Folder/file.txt")
            # Without it, "/" becomes "%2F" which API rejects
            encoded_filename = quote(filename, safe='/')
            url = f"{self.API_BASE}/get_upload_url/files/{encoded_filename}"
            
            self.logger.info(f"Requesting upload URL for: {filename}")
            self.logger.debug(f"URL: {url}")
            response = self.session.get(url, timeout=10)
            
            # Check for "EntryAlreadyExistsError" (file already exists)
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', {})
                    if isinstance(error_detail, dict):
                        error_type = error_detail.get('error_type', '')
                        if error_type == 'EntryAlreadyExistsError':
                            self.logger.info(f"File already exists in AI Drive: {filename}")
                            # Return special tuple to signal "already exists"
                            return ('ALREADY_EXISTS', None)
                except:
                    pass
            
            # Log response status for other errors
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    self.logger.error(f"get_upload_url failed [{response.status_code}]: {error_data}")
                except:
                    self.logger.error(f"get_upload_url failed [{response.status_code}]: {response.text[:200]}")
            
            response.raise_for_status()
            
            data = response.json()
            
            # Response format: {"status": "success", "data": {"upload_url": "...", "token": "..."}}
            if data.get("status") == "success":
                upload_data = data.get("data", {})
                upload_url = upload_data.get("upload_url")
                token = upload_data.get("token")
                
                if upload_url and token:
                    self.logger.info(f"✅ Got upload URL and token for: {filename}")
                    return (upload_url, token)
            
            self.logger.error(f"No upload_url or token in response: {data}")
            return None
                
        except Exception as e:
            self.logger.error(f"Failed to request upload URL for '{filename}': {e}")
            # Log response if available
            try:
                if hasattr(e, 'response') and e.response is not None:
                    self.logger.error(f"Response: {e.response.text[:500]}")
            except:
                pass
            return None
    
    def create_folder(self, folder_path: str) -> bool:
        """
        Create a folder in AI Drive
        
        Args:
            folder_path: Folder path (e.g., "TestOrdner" or "Parent/Child")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Discovered from Chrome DevTools:
            # POST /api/aidrive/mkdir/files/{folder_name}/
            from urllib.parse import quote
            # CRITICAL: safe='/' preserves nested folder structure (e.g., "Parent/Child")
            # Without it, "/" becomes "%2F" which API rejects
            encoded_path = quote(folder_path, safe='/')
            url = f"{self.API_BASE}/mkdir/files/{encoded_path}/"
            
            self.logger.info(f"Creating folder: {folder_path}")
            response = self.session.post(url, timeout=10)
            
            # Check if folder already exists (status 400 with "already exists" message)
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '').lower()
                    if 'already exists' in error_detail:
                        self.logger.debug(f"Folder already exists: {folder_path}")
                        return True
                except:
                    pass
            
            # Log other errors
            if response.status_code != 200:
                try:
                    self.logger.error(f"mkdir failed [{response.status_code}]: {response.json()}")
                except:
                    self.logger.error(f"mkdir failed [{response.status_code}]: {response.text[:200]}")
            
            response.raise_for_status()
            
            self.logger.info(f"Folder created: {folder_path}")
            return True
                
        except Exception as e:
            # Catch any other exceptions
            self.logger.error(f"Failed to create folder: {e}")
            return False
    
    def confirm_upload(self, filename: str, token: str) -> bool:
        """
        Confirm upload to GenSpark (Step 3 of 3-step upload)
        
        Args:
            filename: Name of uploaded file
            token: Upload token from get_upload_url response
            
        Returns:
            True if confirmed successfully
        """
        try:
            # Discovered from Chrome DevTools:
            # POST /api/aidrive/confirm_upload/files/{filename}
            # Body: {"token": "..."}
            from urllib.parse import quote
            # CRITICAL: safe='/' preserves folder structure (e.g., "Folder/file.txt")
            # Without it, "/" becomes "%2F" which API rejects
            encoded_filename = quote(filename, safe='/')
            url = f"{self.API_BASE}/confirm_upload/files/{encoded_filename}"
            
            payload = {"token": token}
            
            self.logger.info(f"Confirming upload for: {filename}")
            self.logger.debug(f"URL: {url}")
            response = self.session.post(url, json=payload, timeout=10)
            
            # Check for "Entry already exists" (file was already confirmed, treat as success)
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'already exists' in str(error_detail).lower():
                        self.logger.info(f"File already confirmed in AI Drive: {filename} (treating as success)")
                        return True
                except:
                    pass
            
            # Log response status for other errors
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    self.logger.error(f"confirm_upload failed [{response.status_code}]: {error_data}")
                except:
                    self.logger.error(f"confirm_upload failed [{response.status_code}]: {response.text[:200]}")
            
            response.raise_for_status()
            
            self.logger.info(f"✅ Upload confirmed for: {filename}")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to confirm upload for '{filename}': {e}")
            # Log response for debugging
            try:
                if hasattr(e, 'response') and e.response is not None:
                    self.logger.error(f"Response: {e.response.text[:500]}")
            except:
                pass
            return False
    
    def upload_file(self, local_path: Path, remote_filename: str) -> bool:
        """
        Upload a file to AI Drive using 3-step process:
        1. Create folder if needed (for files in folders)
        2. GET upload URL from GenSpark
        3. PUT file to Azure Blob Storage
        4. POST confirm to GenSpark
        
        Args:
            local_path: Local file path
            remote_filename: Desired filename or path in AI Drive (e.g., "file.txt" or "Folder/file.txt")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Step 0: Create folder if file is in a folder
            if '/' in remote_filename:
                # Extract folder path (everything before last /)
                folder_path = '/'.join(remote_filename.split('/')[:-1])
                if not self.create_folder(folder_path):
                    self.logger.error(f"Failed to create folder: {folder_path}")
                    # Continue anyway - folder might already exist
            
            # Continue with normal upload process
            # Step 1: Request upload URL and token from GenSpark
            upload_result = self.request_upload_url(remote_filename)
            if not upload_result:
                return False
            
            # Check if file already exists
            if upload_result[0] == 'ALREADY_EXISTS':
                self.logger.info(f"✅ File already in AI Drive (no upload needed): {remote_filename}")
                return True  # Treat as success
            
            upload_url, token = upload_result
            
            # Step 2: Upload file directly to Azure Blob Storage
            self.logger.info(f"Uploading to Azure: {local_path.name}")
            
            # Read file content
            with open(local_path, 'rb') as f:
                file_content = f.read()
            
            # PUT to Azure Blob Storage
            # Based on Chrome DevTools, headers needed:
            # - x-ms-blob-type: BlockBlob
            # - Content-Type: image/jpeg (or appropriate type)
            import mimetypes
            content_type, _ = mimetypes.guess_type(str(local_path))
            
            headers = {
                "x-ms-blob-type": "BlockBlob",
                "Content-Type": content_type or "application/octet-stream"
            }
            
            response = requests.put(
                upload_url,
                data=file_content,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            
            self.logger.info(f"Uploaded to Azure: {remote_filename}")
            
            # Step 3: Confirm upload with GenSpark using token
            if not self.confirm_upload(remote_filename, token):
                self.logger.error("Upload succeeded but confirmation failed")
                return False
            
            self.logger.info(f"✅ Upload complete: {remote_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload {remote_filename}: {e}")
            return False
    
    def delete_file(self, file_id: str, filename: str, file_path: str = None) -> bool:
        """
        Delete a file from AI Drive
        
        Args:
            file_id: Unique file ID
            filename: Filename
            file_path: Full file path (e.g., "/folder/file.txt")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use path-based delete if available, otherwise use ID
            if file_path:
                from urllib.parse import quote
                clean_path = file_path.lstrip('/')
                encoded_path = quote(clean_path, safe='/')
                url = f"{self.API_BASE}/delete/files/{encoded_path}"
            else:
                url = f"{self.API_BASE}/files/{file_id}"
            
            self.logger.info(f"Deleting: {filename}")
            response = self.session.delete(url, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Deleted: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete {filename}: {e}")
            return False
    
    def update_file(self, local_path: Path, remote_filename: str, file_id: str = None, file_path: str = None) -> bool:
        """
        Update an existing file in AI Drive (delete + re-upload)
        
        For files in folders: Delete may timeout, so we log warning and continue
        The sync engine will retry in next cycle if needed
        
        Args:
            local_path: Local file path
            remote_filename: Remote filename or path
            file_id: File ID (for deletion)
            file_path: Full file path (for deletion)
            
        Returns:
            True if successfully updated, False otherwise
        """
        try:
            self.logger.info(f"Updating file: {remote_filename}")
            
            # Step 1: Try to delete old version
            if file_id:
                # Use ID-based delete (works for root files)
                if not self.delete_file(file_id, remote_filename):
                    self.logger.debug(f"ID-based delete failed, skipping delete step")
            elif file_path:
                # Use path-based delete (may timeout for folder files)
                if not self.delete_file('', remote_filename, file_path):
                    self.logger.debug(f"Path-based delete failed, skipping delete step")
            
            # Step 2: Upload new version (will handle "already exists")
            return self.upload_file(local_path, remote_filename)
            
        except Exception as e:
            self.logger.error(f"Failed to update {remote_filename}: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test if API connection and authentication works"""
        try:
            if not self.cookies_loaded:
                self.logger.warning("Cookies not loaded, attempting to load...")
                if not self.load_cookies_from_chrome():
                    return False
            
            # Try to list files as connection test
            files = self.list_files()
            return files is not None
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    client = GenSparkAPIClient()
    
    # Load cookies from Chrome
    if client.load_cookies_from_chrome():
        # Test connection
        if client.test_connection():
            print("✅ API connection successful!")
            
            # List files
            files = client.list_files()
            if files:
                print(f"\n📁 Found {len(files)} items:")
                for file in files[:5]:  # Show first 5
                    print(f"  - {file['name']} ({file['type']}, {file['size']} bytes)")
        else:
            print("❌ API connection failed!")
    else:
        print("❌ Failed to load cookies from Chrome!")
