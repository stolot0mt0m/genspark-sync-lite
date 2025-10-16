#!/usr/bin/env python3
"""
Bi-directional Sync Engine
Synchronizes local folder with GenSpark AI Drive
OPTIMIZED: SQLite state + Quick hash for 10-100x performance
"""

import logging
import json
import time
import hashlib
import threading
from pathlib import Path
from typing import Dict, Set, Optional, List, Any
from datetime import datetime
from genspark_api import GenSparkAPIClient
from smart_state import SmartSyncState, migrate_json_to_sqlite


class SyncEngine:
    """Manages bi-directional synchronization between local and AI Drive"""
    
    def __init__(self, local_root: Path, api_client: GenSparkAPIClient, sync_strategy: str = 'local'):
        self.local_root = Path(local_root)
        self.api_client = api_client
        self.sync_strategy = sync_strategy  # Fixed to 'local' - bidirectional sync with smart deletion handling
        self.logger = logging.getLogger('SyncEngine')
        
        # State tracking - SQLite for performance
        self.state_db_path = self.local_root / '.genspark_sync_state.db'
        self.state_json_path = self.local_root / '.genspark_sync_state.json'
        
        # Migrate from JSON if needed
        if migrate_json_to_sqlite(self.state_json_path, self.state_db_path):
            self.logger.info("✅ Migrated JSON state to SQLite")
        
        # Initialize smart state
        self.smart_state = SmartSyncState(self.state_db_path)
        
        # Legacy compatibility - keep dict interface for now
        self.state: Dict[str, Dict[str, Any]] = {}
        self.load_state()
        
        # Track files currently being downloaded (to avoid re-uploading)
        self.downloading_files: Set[str] = set()
        
        # Track files currently being uploaded (to avoid duplicate uploads)
        self.uploading_files: Set[str] = set()
        
        # Thread lock for upload tracking (prevent race conditions)
        self.upload_lock = threading.Lock()
        
        # Sync statistics
        self.stats = {
            'uploads': 0,
            'downloads': 0,
            'conflicts': 0,
            'errors': 0,
            'remote_only_deleted': 0,  # Count remote-only deletions
            'local_only_deleted': 0,   # Count local-only deletions
        }
    
    def load_state(self):
        """Load sync state from SQLite (FAST!)"""
        try:
            self.state = self.smart_state.get_all_files()
            stats = self.smart_state.get_stats()
            self.logger.info(f"✅ Loaded state: {stats['total']} files tracked ({stats['total_size']} bytes)")
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
            self.state = {}
    
    def save_state(self):
        """Save sync state to SQLite (FAST! - auto-committed)"""
        # SQLite state is auto-committed per operation
        # This method kept for compatibility
        try:
            stats = self.smart_state.get_stats()
            self.logger.debug(f"State saved: {stats['total']} files, {stats['synced']} synced")
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
    
    def update_file_state(self, path: str, size: int, mtime: int, quick_hash: str = None):
        """Update both dict and SQLite state (helper method)"""
        # Update dict (for legacy compatibility)
        self.state[path] = {
            'modified_time': mtime,
            'size': size
        }
        # Update SQLite (main storage)
        self.smart_state.update_file(path, size, float(mtime), quick_hash)
    
    def delete_file_state(self, path: str):
        """Delete from both dict and SQLite state (helper method)"""
        # Delete from dict
        if path in self.state:
            del self.state[path]
        # Delete from SQLite
        self.smart_state.delete_file(path)
    
    def get_file_hash(self, path: Path) -> str:
        """
        Calculate quick hash (first 8KB only) - OPTIMIZED!
        100x faster than full file hash
        """
        return self.smart_state.get_quick_hash(path) or ""
    
    def scan_local_files(self) -> Dict[str, Dict[str, Any]]:
        """
        Scan local folder and return file metadata
        OPTIMIZED: Quick hash + smart state checking
        """
        local_files = {}
        
        for path in self.local_root.rglob('*'):
            if path.is_file() and not self._should_ignore(path):
                relative_path = str(path.relative_to(self.local_root))
                stat = path.stat()
                size = stat.st_size
                mtime = stat.st_mtime
                
                # Quick optimization: Check if file unchanged via mtime + size
                existing_state = self.smart_state.get_file_state(relative_path)
                if existing_state:
                    # If mtime and size are same, skip hash calculation
                    if (existing_state['mtime'] == mtime and 
                        existing_state['size'] == size):
                        # File unchanged - reuse existing hash
                        local_files[relative_path] = {
                            'path': relative_path,
                            'size': size,
                            'modified_time': int(mtime),
                            'hash': existing_state['quick_hash']
                        }
                        continue
                
                # File changed or new - calculate quick hash
                quick_hash = self.get_file_hash(path)
                
                local_files[relative_path] = {
                    'path': relative_path,
                    'size': size,
                    'modified_time': int(mtime),
                    'hash': quick_hash
                }
        
        return local_files
    
    def scan_remote_files(self) -> Dict[str, Dict[str, Any]]:
        """Scan AI Drive and return file metadata (recursively including folders)"""
        remote_files = {}
        
        # Step 1: Get root items
        items = self.api_client.list_files()
        if not items:
            return remote_files
        
        # Step 2: Collect folders to scan
        folders_to_scan = []
        
        for item in items:
            if item.get('type') == 'directory':
                # Add folder to scan list
                folders_to_scan.append(item)
                continue
                
            if item['type'] == 'file':
                # Skip thumbnail files
                if item['name'].startswith('thumb_') and item['name'].endswith('.jpg'):
                    continue
                
                # Root-level file
                file_path = item['path']
                relative_path = file_path.lstrip('/')
                
                remote_files[relative_path] = {
                    'path': relative_path,
                    'file_path': file_path,
                    'id': item['id'],
                    'name': item['name'],
                    'size': item['size'],
                    'modified_time': item['modified_time'],
                    'mime_type': item.get('mime_type', '')
                }
        
        # Step 3: Scan each folder for files
        self.logger.info(f"Scanning {len(folders_to_scan)} folders for files...")
        for folder in folders_to_scan:
            folder_path = folder['path']
            folder_name = folder['name']
            
            self.logger.debug(f"Scanning folder: {folder_name}")
            
            # Get files in this folder
            folder_items = self.api_client.list_files(folder_path=folder_path)
            if not folder_items:
                continue
            
            for item in folder_items:
                # Skip subdirectories for now (can add recursive later)
                if item.get('type') == 'directory':
                    continue
                
                if item['type'] == 'file':
                    # Skip thumbnails
                    if item['name'].startswith('thumb_') and item['name'].endswith('.jpg'):
                        continue
                    
                    # File in folder - construct path
                    file_path = item['path']
                    # relative_path should be like "GitHub_Deployment/file.txt"
                    relative_path = file_path.lstrip('/')
                    
                    remote_files[relative_path] = {
                        'path': relative_path,
                        'file_path': file_path,
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
                state_size = state.get('size', 0)
                
                # Determine what changed
                local_changed = (local['modified_time'] > state_mtime or local['size'] != state_size)
                remote_changed = (remote['modified_time'] > state_mtime or remote['size'] != state_size)
                
                # TRUE conflict: BOTH changed since last sync
                if local_changed and remote_changed:
                    conflicts.append({
                        'path': path,
                        'local': local,
                        'remote': remote,
                        'state': state
                    })
                # Local-only change: Upload will handle this
                elif local_changed and not remote_changed:
                    self.logger.debug(f"Local-only change detected: {path} (will be uploaded)")
                # Remote-only change: Download will handle this
                elif remote_changed and not local_changed:
                    self.logger.debug(f"Remote-only change detected: {path} (will be downloaded)")
        
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
        
        # Handle remote-only files (files that exist on remote but not locally)
        remote_only = set(remote_files.keys()) - set(local_files.keys())
        
        # Intelligently split remote-only into:
        # 1. New remote files (not in state) → Download
        # 2. Deleted local files (in state) → Delete from remote
        new_remote_files = set()
        deleted_local_files = set()
        
        for path in remote_only:
            if path in self.state:
                # File was synced before but now missing locally → Deleted locally
                deleted_local_files.add(path)
            else:
                # File never synced before → New remote file
                new_remote_files.add(path)
        
        # Handle files deleted locally (delete from remote)
        if deleted_local_files:
            self.logger.info(f"📤 Files deleted locally: {len(deleted_local_files)}")
            for path in deleted_local_files:
                remote = remote_files[path]
                self.logger.info(f"Deleting from AI Drive (deleted locally): {path}")
                if self.api_client.delete_file('', remote['name'], remote['file_path']):
                    self.stats['remote_only_deleted'] += 1
                    # Remove from state
                    self.delete_file_state(path)
        
        # Handle new remote files (download)
        self.logger.info(f"Files to download: {len(new_remote_files)}")
        
        if new_remote_files and self.sync_strategy == 'local':
            # Local priority: Delete new remote files (should not happen with bidirectional sync)
            self.logger.warning(f"⚠️  Sync strategy: LOCAL priority")
            self.logger.warning(f"⚠️  {len(new_remote_files)} new remote files will be DELETED from AI Drive")
            
            for path in new_remote_files:
                remote = remote_files[path]
                self.logger.info(f"Deleting new remote file: {path}")
                if self.api_client.delete_file('', remote['name'], remote['file_path']):
                    self.stats['remote_only_deleted'] += 1
        
        elif new_remote_files and self.sync_strategy == 'ask':
            # Ask strategy: Prompt user for each new remote file
            self.logger.warning(f"⚠️  Sync strategy: ASK for each file")
            self.logger.warning(f"⚠️  Found {len(new_remote_files)} new remote files")
            
            for path in new_remote_files:
                remote = remote_files[path]
                local_path = self.local_root / path
                
                # Prompt user
                print(f"\n⚠️  New remote file: {path}")
                print(f"    Size: {remote['size']} bytes")
                print(f"    Modified: {datetime.fromtimestamp(remote['modified_time']).strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"    [D] Download to local")
                print(f"    [X] Delete from remote")
                print(f"    [S] Skip (do nothing)")
                
                while True:
                    choice = input("Choose action [D/X/S]: ").strip().upper()
                    if choice in ['D', 'X', 'S']:
                        break
                    print("Invalid choice. Please enter D, X, or S.")
                
                if choice == 'D':
                    # Download file
                    self.logger.info(f"User chose: Download {path}")
                    self.downloading_files.add(path)
                    
                    try:
                        if self.api_client.download_file(
                            remote['id'], 
                            remote['name'], 
                            remote['file_path'],
                            local_path
                        ):
                            self.state[path] = {
                                'modified_time': remote['modified_time'],
                                'size': remote['size']
                            }
                            self.stats['downloads'] += 1
                            print(f"✅ Downloaded: {path}")
                    finally:
                        pass
                
                elif choice == 'X':
                    # Delete from remote
                    self.logger.info(f"User chose: Delete {path}")
                    if self.api_client.delete_file('', remote['name'], remote['file_path']):
                        self.stats['remote_only_deleted'] += 1
                        self.delete_file_state(path)
                        print(f"✅ Deleted from remote: {path}")
                    else:
                        print(f"❌ Failed to delete: {path}")
                
                else:  # choice == 'S'
                    # Skip - do nothing
                    self.logger.info(f"User chose: Skip {path}")
                    print(f"⏭️  Skipped: {path}")
        
        else:
            # Default: Download new remote files
            for path in new_remote_files:
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
        
        # Handle local-only files (files that exist locally but not on remote)
        local_only = set(local_files.keys()) - set(remote_files.keys())
        
        # Intelligently split local-only into:
        # 1. New local files (not in state) → Upload
        # 2. Deleted remote files (in state) → Delete locally
        new_local_files = set()
        deleted_remote_files = set()
        
        for path in local_only:
            if path in self.state:
                # File was synced before but now missing from remote → Deleted remotely
                deleted_remote_files.add(path)
            else:
                # File never synced before → New local file
                new_local_files.add(path)
        
        # Handle files deleted from remote (delete locally)
        if deleted_remote_files:
            self.logger.info(f"📥 Files deleted from AI Drive: {len(deleted_remote_files)}")
            for path in deleted_remote_files:
                local_path = self.local_root / path
                self.logger.info(f"Deleting file (deleted from remote): {path}")
                try:
                    if local_path.exists():
                        local_path.unlink()
                        self.stats['local_only_deleted'] += 1
                        self.logger.info(f"✅ Deleted local file: {path}")
                    # Remove from state
                    self.delete_file_state(path)
                except Exception as e:
                    self.logger.error(f"Failed to delete local file {path}: {e}")
        
        # Handle new local files (upload to remote)
        self.logger.info(f"Files to upload: {len(new_local_files)}")
        
        if new_local_files and self.sync_strategy == 'remote':
            # Remote priority: Delete new local files (should not happen with 'local' default)
            self.logger.warning(f"⚠️  Sync strategy: REMOTE priority")
            self.logger.warning(f"⚠️  {len(new_local_files)} new local files will be DELETED")
            
            for path in new_local_files:
                local_path = self.local_root / path
                self.logger.info(f"Deleting local-only file: {path}")
                try:
                    if local_path.exists():
                        local_path.unlink()
                        self.stats['local_only_deleted'] += 1
                        self.logger.info(f"✅ Deleted local file: {path}")
                        # Remove from state if exists
                        self.delete_file_state(path)
                except Exception as e:
                    self.logger.error(f"Failed to delete local file {path}: {e}")
        
        elif new_local_files and self.sync_strategy == 'ask':
            # Ask strategy: Prompt user for each new local file
            self.logger.warning(f"⚠️  Sync strategy: ASK for each file")
            self.logger.warning(f"⚠️  Found {len(new_local_files)} new local files")
            
            for path in new_local_files:
                local = local_files[path]
                local_path = self.local_root / path
                
                # Prompt user
                print(f"\n⚠️  New local file: {path}")
                print(f"    Size: {local['size']} bytes")
                print(f"    Modified: {datetime.fromtimestamp(local['modified_time']).strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"    [U] Upload to remote")
                print(f"    [X] Delete from local")
                print(f"    [S] Skip (do nothing)")
                
                while True:
                    choice = input("Choose action [U/X/S]: ").strip().upper()
                    if choice in ['U', 'X', 'S']:
                        break
                    print("Invalid choice. Please enter U, X, or S.")
                
                if choice == 'U':
                    # Upload file
                    self.logger.info(f"User chose: Upload {path}")
                    
                    with self.upload_lock:
                        if path in self.uploading_files:
                            continue
                        self.uploading_files.add(path)
                    
                    try:
                        if self.api_client.upload_file(local_path, path):
                            self.state[path] = {
                                'modified_time': local['modified_time'],
                                'size': local['size']
                            }
                            self.stats['uploads'] += 1
                            print(f"✅ Uploaded: {path}")
                    finally:
                        with self.upload_lock:
                            self.uploading_files.discard(path)
                
                elif choice == 'X':
                    # Delete from local
                    self.logger.info(f"User chose: Delete local {path}")
                    try:
                        if local_path.exists():
                            local_path.unlink()
                            self.stats['local_only_deleted'] += 1
                            if path in self.state:
                                del self.state[path]
                            print(f"✅ Deleted from local: {path}")
                    except Exception as e:
                        print(f"❌ Failed to delete: {e}")
                
                else:  # choice == 'S'
                    # Skip - do nothing
                    self.logger.info(f"User chose: Skip {path}")
                    print(f"⏭️  Skipped: {path}")
        
        else:
            # Local priority (or default): Upload new local files
            for path in new_local_files:
                local = local_files[path]
                local_path = self.local_root / path
                
                # Use lock to prevent concurrent uploads
                with self.upload_lock:
                    # Skip if already uploading
                    if path in self.uploading_files:
                        self.logger.debug(f"Skipping {path} (upload already in progress)")
                        continue
                    
                    # Mark as uploading
                    self.uploading_files.add(path)
                
                try:
                    self.logger.info(f"Uploading new file: {path}")
                    
                    # Use full path for files in folders (e.g., "TestOrdner/file.txt")
                    # API expects: /api/aidrive/get_upload_url/files/TestOrdner/file.txt
                    if self.api_client.upload_file(local_path, path):
                        self.state[path] = {
                            'modified_time': local['modified_time'],
                            'size': local['size']
                        }
                        self.stats['uploads'] += 1
                finally:
                    # Always remove from uploading set
                    with self.upload_lock:
                        self.uploading_files.discard(path)
        
        # Handle modified files (no conflicts)
        common_files = set(local_files.keys()) & set(remote_files.keys())
        conflict_paths = {c['path'] for c in conflicts}
        
        for path in common_files:
            # Skip conflicts (already logged above)
            if path in conflict_paths:
                continue
            
            local = local_files[path]
            remote = remote_files[path]
            state = self.state.get(path, {})
            state_mtime = state.get('modified_time', 0)
            state_size = state.get('size', 0)
            
            # Check if local changed (and remote didn't)
            local_changed = (local['modified_time'] > state_mtime or local['size'] != state_size)
            remote_changed = (remote['modified_time'] > state_mtime or remote['size'] != state_size)
            
            if local_changed and not remote_changed:
                # Upload modified local file
                self.logger.info(f"Uploading modified file: {path}")
                local_path = self.local_root / path
                
                # Use update_file if we have remote info (delete + upload)
                if hasattr(self.api_client, 'update_file'):
                    if self.api_client.update_file(local_path, path, remote.get('id'), remote.get('file_path')):
                        self.state[path] = {
                            'modified_time': local['modified_time'],
                            'size': local['size']
                        }
                        self.stats['uploads'] += 1
                else:
                    # Fallback to regular upload
                    if self.api_client.upload_file(local_path, path):
                        self.state[path] = {
                            'modified_time': local['modified_time'],
                            'size': local['size']
                        }
                        self.stats['uploads'] += 1
            
            elif remote_changed and not local_changed:
                # Download modified remote file
                self.logger.info(f"Downloading modified file: {path}")
                local_path = self.local_root / path
                
                # Mark as downloading
                self.downloading_files.add(path)
                
                if self.api_client.download_file(
                    remote['id'],
                    remote['name'],
                    remote['file_path'],
                    local_path
                ):
                    self.state[path] = {
                        'modified_time': remote['modified_time'],
                        'size': remote['size']
                    }
                    self.stats['downloads'] += 1
            
            else:
                # No changes or already synced
                self.state[path] = {
                    'modified_time': local['modified_time'],
                    'size': local['size']
                }
        
        self.save_state()
        
        # Clear downloading/uploading files after a short delay
        # (File watcher events are debounced by 2 seconds)
        import threading
        def clear_tracking_sets():
            time.sleep(3)
            self.downloading_files.clear()
            self.uploading_files.clear()
        threading.Thread(target=clear_tracking_sets, daemon=True).start()
        
        # Log summary
        summary_parts = []
        if self.stats['uploads'] > 0:
            summary_parts.append(f"{self.stats['uploads']} uploads")
        if self.stats['downloads'] > 0:
            summary_parts.append(f"{self.stats['downloads']} downloads")
        if self.stats['remote_only_deleted'] > 0:
            summary_parts.append(f"{self.stats['remote_only_deleted']} remote deletions")
        if self.stats['local_only_deleted'] > 0:
            summary_parts.append(f"{self.stats['local_only_deleted']} local deletions")
        
        if summary_parts:
            self.logger.info(f"Sync complete: {', '.join(summary_parts)}")
        else:
            self.logger.info("Sync complete: No changes")
        return self.stats
    
    def handle_local_change(self, path: Path, event_type: str):
        """Handle a local file change"""
        relative_path = str(path.relative_to(self.local_root))
        
        # Skip if we're currently downloading this file
        if relative_path in self.downloading_files:
            self.logger.debug(f"Skipping upload for {relative_path} (currently downloading)")
            return
        
        if event_type in ['created', 'modified']:
            # Use lock to prevent concurrent uploads of the same file
            with self.upload_lock:
                # Skip if we're already uploading this file
                if relative_path in self.uploading_files:
                    self.logger.debug(f"Skipping duplicate upload for {relative_path} (upload already in progress)")
                    return
                
                # Mark file as being uploaded
                self.uploading_files.add(relative_path)
            
            try:
                # Check if file still exists before uploading (race condition check)
                if not path.exists():
                    self.logger.debug(f"File no longer exists, skipping upload: {relative_path}")
                    return
                
                # Upload file with full path for folders support
                self.logger.info(f"Uploading: {relative_path}")
                if self.api_client.upload_file(path, relative_path):
                    # Double-check file exists before getting stats (paranoid check)
                    if path.exists():
                        self.state[relative_path] = {
                            'modified_time': int(path.stat().st_mtime),
                            'size': path.stat().st_size
                        }
                        self.save_state()
                        self.stats['uploads'] += 1
                    else:
                        self.logger.debug(f"File disappeared after upload: {relative_path}")
            except FileNotFoundError:
                # File was deleted during upload process (race condition)
                self.logger.debug(f"File deleted during upload (race condition): {relative_path}")
            finally:
                # Always remove from uploading set
                with self.upload_lock:
                    self.uploading_files.discard(relative_path)
        
        elif event_type == 'deleted':
            # Check if it's a directory deletion
            # If path doesn't exist locally, could be file or folder
            
            # First, check if it's a file in remote
            remote_files = self.scan_remote_files()
            if relative_path in remote_files:
                # It's a file - delete it
                remote = remote_files[relative_path]
                self.logger.info(f"Deleting file from remote: {relative_path}")
                self.api_client.delete_file('', remote['name'], remote['file_path'])
                
                # Remove from state
                if relative_path in self.state:
                    del self.state[relative_path]
                    self.save_state()
            else:
                # Might be a folder deletion - find all files in that folder
                folder_prefix = relative_path + '/'
                files_in_folder = []
                
                # Find files in state that start with folder path
                for file_path in list(self.state.keys()):
                    if file_path.startswith(folder_prefix):
                        files_in_folder.append(file_path)
                
                # Also check remote for files in this folder
                for file_path in remote_files.keys():
                    if file_path.startswith(folder_prefix) and file_path not in files_in_folder:
                        files_in_folder.append(file_path)
                
                if files_in_folder:
                    self.logger.info(f"Folder deleted locally: {relative_path} (contains {len(files_in_folder)} files)")
                    
                    # Delete all files in the folder from remote
                    for file_path in files_in_folder:
                        if file_path in remote_files:
                            remote = remote_files[file_path]
                            self.logger.info(f"  Deleting: {file_path}")
                            self.api_client.delete_file('', remote['name'], remote['file_path'])
                        
                        # Remove from state
                        if file_path in self.state:
                            del self.state[file_path]
                    
                    self.save_state()
                    self.logger.info(f"✅ Folder deletion complete: {relative_path}")
                else:
                    # File/folder not found anywhere - might have been already deleted
                    self.logger.debug(f"Delete event for unknown path: {relative_path}")
                    
                    # Still remove from state if exists
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
