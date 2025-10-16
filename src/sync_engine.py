#!/usr/bin/env python3
"""
Bi-directional Sync Engine
Synchronizes local folder with GenSpark AI Drive
"""

import logging
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Set, Optional, List, Any
from datetime import datetime
from genspark_api import GenSparkAPIClient


class SyncEngine:
    """Manages bi-directional synchronization between local and AI Drive"""
    
    def __init__(self, local_root: Path, api_client: GenSparkAPIClient):
        self.local_root = Path(local_root)
        self.api_client = api_client
        self.logger = logging.getLogger('SyncEngine')
        
        # State file tracking
        self.state_file = self.local_root / '.genspark_sync_state.json'
        self.state: Dict[str, Dict[str, Any]] = {}
        self.load_state()
        
        # Track files currently being downloaded (to avoid re-uploading)
        self.downloading_files: Set[str] = set()
        
        # Sync statistics
        self.stats = {
            'uploads': 0,
            'downloads': 0,
            'conflicts': 0,
            'errors': 0
        }
    
    def load_state(self):
        """Load sync state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
                self.logger.info(f"Loaded state: {len(self.state)} files tracked")
            except Exception as e:
                self.logger.error(f"Failed to load state: {e}")
                self.state = {}
        else:
            self.state = {}
    
    def save_state(self):
        """Save sync state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
    
    def get_file_hash(self, path: Path) -> str:
        """Calculate MD5 hash of file"""
        try:
            md5 = hashlib.md5()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to hash {path}: {e}")
            return ""
    
    def scan_local_files(self) -> Dict[str, Dict[str, Any]]:
        """Scan local folder and return file metadata"""
        local_files = {}
        
        for path in self.local_root.rglob('*'):
            if path.is_file() and not self._should_ignore(path):
                relative_path = str(path.relative_to(self.local_root))
                
                local_files[relative_path] = {
                    'path': relative_path,
                    'size': path.stat().st_size,
                    'modified_time': int(path.stat().st_mtime),
                    'hash': self.get_file_hash(path)
                }
        
        return local_files
    
    def scan_remote_files(self) -> Dict[str, Dict[str, Any]]:
        """Scan AI Drive and return file metadata"""
        remote_files = {}
        
        items = self.api_client.list_files()
        if not items:
            return remote_files
        
        for item in items:
            # Skip directories - we only sync files
            if item.get('type') == 'directory':
                continue
                
            if item['type'] == 'file':
                # Skip thumbnail files (they're generated, not real user files)
                if item['name'].startswith('thumb_') and item['name'].endswith('.jpg'):
                    continue
                
                # API returns full path like "/Github_Ready_Repository" or "/Investments/file.txt"
                file_path = item['path']
                relative_path = file_path.lstrip('/')  # Remove leading slash for local path
                
                remote_files[relative_path] = {
                    'path': relative_path,
                    'file_path': file_path,  # Keep original path for download URL
                    'id': item['id'],
                    'name': item['name'],
                    'size': item['size'],
                    'modified_time': item['modified_time'],
                    'mime_type': item.get('mime_type', '')
                }
        
        return remote_files
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored"""
        ignore_patterns = {
            '.genspark_sync_state.json',
            '.genspark_sync_config.json',
            '.genspark_sync.log',
            '.DS_Store',
            '__pycache__',
            '.git',
            'node_modules',
        }
        
        # Check if any part matches ignore patterns
        for part in path.parts:
            if part in ignore_patterns:
                return True
        
        # Ignore hidden files
        if path.name.startswith('.'):
            return True
        
        return False
    
    def detect_conflicts(self, local_files: Dict, remote_files: Dict) -> List[Dict[str, Any]]:
        """Detect conflicting files that exist in both places with different content"""
        conflicts = []
        
        for path in set(local_files.keys()) & set(remote_files.keys()):
            local = local_files[path]
            remote = remote_files[path]
            
            # Compare by modified time and size
            if local['modified_time'] != remote['modified_time'] or local['size'] != remote['size']:
                # Check if we have state for this file
                state = self.state.get(path, {})
                state_mtime = state.get('modified_time', 0)
                
                # Both changed since last sync
                if (local['modified_time'] > state_mtime and 
                    remote['modified_time'] > state_mtime):
                    conflicts.append({
                        'path': path,
                        'local': local,
                        'remote': remote,
                        'state': state
                    })
        
        return conflicts
    
    def resolve_conflict(self, conflict: Dict[str, Any], resolution: str) -> bool:
        """
        Resolve a conflict
        
        Args:
            conflict: Conflict data
            resolution: 'local' (keep local), 'remote' (keep remote), 'skip' (do nothing)
        
        Returns:
            True if resolved successfully
        """
        path = conflict['path']
        
        if resolution == 'local':
            # Upload local version
            local_path = self.local_root / path
            if self.api_client.upload_file(local_path, conflict['remote']['name']):
                self.logger.info(f"Conflict resolved (kept local): {path}")
                self.stats['uploads'] += 1
                return True
                
        elif resolution == 'remote':
            # Download remote version
            local_path = self.local_root / path
            if self.api_client.download_file(
                conflict['remote']['id'],
                conflict['remote']['name'],
                conflict['remote']['file_path'],  # Add file_path parameter
                local_path
            ):
                self.logger.info(f"Conflict resolved (kept remote): {path}")
                self.stats['downloads'] += 1
                return True
        
        elif resolution == 'skip':
            self.logger.info(f"Conflict skipped: {path}")
            return True
        
        return False
    
    def sync_once(self) -> Dict[str, int]:
        """Perform one sync cycle"""
        self.logger.info("Starting sync cycle...")
        
        # Scan both sides
        local_files = self.scan_local_files()
        remote_files = self.scan_remote_files()
        
        self.logger.info(f"Local: {len(local_files)} files, Remote: {len(remote_files)} files")
        
        # Detect conflicts
        conflicts = self.detect_conflicts(local_files, remote_files)
        
        if conflicts:
            self.logger.warning(f"Found {len(conflicts)} conflicts - manual resolution needed")
            for conflict in conflicts:
                path = conflict['path']
                local = conflict['local']
                remote = conflict['remote']
                self.logger.warning(f"⚠️  CONFLICT: {path}")
                self.logger.warning(f"    Local:  size={local['size']} bytes, mtime={local['modified_time']}")
                self.logger.warning(f"    Remote: size={remote['size']} bytes, mtime={remote['modified_time']}")
                self.logger.warning(f"    → Both files changed since last sync - keeping both versions")
            self.stats['conflicts'] += len(conflicts)
            # Don't return early - continue with non-conflicting files
            # return self.stats
        
        # Download new remote files
        remote_only = set(remote_files.keys()) - set(local_files.keys())
        self.logger.info(f"Files to download: {len(remote_only)}")
        for path in remote_only:
            remote = remote_files[path]
            local_path = self.local_root / path
            
            self.logger.info(f"Downloading new file: {path}")
            
            # Mark as downloading to avoid file watcher re-uploading
            self.downloading_files.add(path)
            
            try:
                # Pass file_path parameter for correct download URL construction
                if self.api_client.download_file(
                    remote['id'], 
                    remote['name'], 
                    remote['file_path'],  # Full path like "/folder/file.txt"
                    local_path
                ):
                    self.state[path] = {
                        'modified_time': remote['modified_time'],
                        'size': remote['size']
                    }
                    self.stats['downloads'] += 1
            finally:
                # Remove from downloading set after a delay (file watcher needs time)
                # We'll clean this up after sync completes
                pass
        
        # Upload new local files
        local_only = set(local_files.keys()) - set(remote_files.keys())
        self.logger.info(f"Files to upload: {len(local_only)}")
        for path in local_only:
            local = local_files[path]
            local_path = self.local_root / path
            
            self.logger.info(f"Uploading new file: {path}")
            
            if self.api_client.upload_file(local_path, Path(path).name):
                self.state[path] = {
                    'modified_time': local['modified_time'],
                    'size': local['size']
                }
                self.stats['uploads'] += 1
        
        # Update state for unchanged files
        common_files = set(local_files.keys()) & set(remote_files.keys())
        for path in common_files:
            if path not in conflicts:
                local = local_files[path]
                self.state[path] = {
                    'modified_time': local['modified_time'],
                    'size': local['size']
                }
        
        self.save_state()
        
        # Clear downloading files after a short delay
        # (File watcher events are debounced by 2 seconds)
        import threading
        def clear_downloading():
            time.sleep(3)
            self.downloading_files.clear()
        threading.Thread(target=clear_downloading, daemon=True).start()
        
        self.logger.info(f"Sync complete: {self.stats['uploads']} uploads, {self.stats['downloads']} downloads")
        return self.stats
    
    def handle_local_change(self, path: Path, event_type: str):
        """Handle a local file change"""
        relative_path = str(path.relative_to(self.local_root))
        
        # Skip if we're currently downloading this file
        if relative_path in self.downloading_files:
            self.logger.debug(f"Skipping upload for {relative_path} (currently downloading)")
            return
        
        if event_type in ['created', 'modified']:
            # Upload file
            self.logger.info(f"Uploading: {relative_path}")
            if self.api_client.upload_file(path, path.name):
                self.state[relative_path] = {
                    'modified_time': int(path.stat().st_mtime),
                    'size': path.stat().st_size
                }
                self.save_state()
                self.stats['uploads'] += 1
        
        elif event_type == 'deleted':
            # Delete from remote (if exists)
            remote_files = self.scan_remote_files()
            if relative_path in remote_files:
                remote = remote_files[relative_path]
                self.logger.info(f"Deleting from remote: {relative_path}")
                self.api_client.delete_file(remote['id'], remote['name'])
            
            # Remove from state
            if relative_path in self.state:
                del self.state[relative_path]
                self.save_state()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize
    api_client = GenSparkAPIClient()
    
    if not api_client.load_cookies_from_chrome():
        print("❌ Failed to load cookies!")
        exit(1)
    
    if not api_client.test_connection():
        print("❌ API connection failed!")
        exit(1)
    
    # Create sync engine
    sync_folder = Path.home() / "GenSpark Sync Test"
    sync_folder.mkdir(exist_ok=True)
    
    engine = SyncEngine(sync_folder, api_client)
    
    # Perform sync
    stats = engine.sync_once()
    print(f"\n📊 Sync Stats:")
    print(f"  Uploads: {stats['uploads']}")
    print(f"  Downloads: {stats['downloads']}")
    print(f"  Conflicts: {stats['conflicts']}")
    print(f"  Errors: {stats['errors']}")
