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
    API_BASE = f"{BASE_URL}/api/aidrive/recent"  # Discovered via Chrome DevTools Network tab
    
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
    
    def list_files(self, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        List all files and folders in AI Drive
        
        Args:
            limit: Maximum number of items to retrieve (default: 100)
            
        Returns:
            List of file/folder dictionaries or None on error
        """
        try:
            # TEMPORARY: Fall back to working endpoint for root files
            # TODO: Discover correct endpoint for folders+files from Chrome DevTools
            url = f"{self.API_BASE}/files"
            params = {
                "limit": limit
            }
            
            self.logger.debug(f"Listing files: {url}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            self.logger.info(f"Retrieved {len(items)} items from AI Drive")
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
    
    def request_upload_url(self, filename: str) -> Optional[Dict[str, str]]:
        """
        Request upload URL and token for a file
        
        Args:
            filename: Name of file to upload
            
        Returns:
            Dict with 'upload_url', 'token', 'expires_at' or None
        """
        try:
            # Upload endpoint pattern: /api/aidrive/upload/files/{filename}
            url = f"{self.BASE_URL}/api/aidrive/upload/files/{filename}"
            
            self.logger.debug(f"Requesting upload URL for: {filename}")
            response = self.session.post(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == "success":
                upload_data = data.get("data", {})
                self.logger.info(f"Got upload URL for: {filename}")
                return upload_data
            else:
                self.logger.error(f"Upload URL request failed: {data.get('message')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to request upload URL: {e}")
            return None
    
    def upload_file(self, local_path: Path, remote_filename: str) -> bool:
        """
        Upload a file to AI Drive
        
        Args:
            local_path: Local file path
            remote_filename: Desired filename in AI Drive
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Step 1: Request upload URL
            upload_data = self.request_upload_url(remote_filename)
            if not upload_data:
                return False
            
            upload_url = upload_data.get("upload_url")
            token = upload_data.get("token")
            
            if not upload_url or not token:
                self.logger.error("Invalid upload URL response")
                return False
            
            # Step 2: Upload file to Azure Blob Storage
            self.logger.info(f"Uploading: {local_path.name}")
            
            with open(local_path, 'rb') as f:
                headers = {
                    "x-ms-blob-type": "BlockBlob",
                    "Authorization": f"Bearer {token}"
                }
                
                response = requests.put(
                    upload_url,
                    data=f,
                    headers=headers,
                    timeout=60
                )
                response.raise_for_status()
            
            self.logger.info(f"Uploaded: {remote_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload {remote_filename}: {e}")
            return False
    
    def delete_file(self, file_id: str, filename: str) -> bool:
        """
        Delete a file from AI Drive
        
        Args:
            file_id: Unique file ID
            filename: Filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete endpoint (needs verification)
            url = f"{self.API_BASE}/files/{file_id}"
            
            self.logger.info(f"Deleting: {filename}")
            response = self.session.delete(url, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Deleted: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete {filename}: {e}")
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
