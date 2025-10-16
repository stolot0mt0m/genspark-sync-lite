#!/usr/bin/env python3
"""
Local File System Watcher
Monitors local folder for changes using watchdog
"""

import logging
import time
from pathlib import Path
from typing import Callable, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class LocalFileWatcher(FileSystemEventHandler):
    """Watches local folder for file changes"""
    
    def __init__(
        self,
        watch_path: Path,
        on_created: Callable[[Path], None],
        on_modified: Callable[[Path], None],
        on_deleted: Callable[[Path], None],
        debounce_seconds: float = 2.0
    ):
        self.watch_path = Path(watch_path)
        self.on_created = on_created
        self.on_modified = on_modified
        self.on_deleted = on_deleted
        self.debounce_seconds = debounce_seconds
        
        # Debouncing: Track recently processed files
        self._recent_events: Set[tuple] = set()
        self._last_event_time: dict = {}
        
        self.observer = Observer()
        self.logger = logging.getLogger('FileWatcher')
        self.is_running = False
        
        # Exclusion patterns
        self.exclude_patterns = {
            '.DS_Store',
            '.genspark_sync_state.json',
            '.genspark_sync_config.json',
            '.genspark_sync.log',
            '__pycache__',
            '.git',
            'node_modules',
            '.venv',
            'venv',
        }
    
    def should_ignore(self, path: Path) -> bool:
        """Check if file/folder should be ignored"""
        # Check if any part of path matches exclusion patterns
        for part in path.parts:
            if part in self.exclude_patterns:
                return True
        
        # Ignore hidden files (except our config files)
        if path.name.startswith('.') and path.name not in self.exclude_patterns:
            return True
        
        # Ignore temporary files
        if path.name.endswith('.tmp') or path.name.endswith('.swp'):
            return True
        
        return False
    
    def _should_process_event(self, event_type: str, path: Path) -> bool:
        """Check if event should be processed (debouncing)"""
        event_key = (event_type, str(path))
        current_time = time.time()
        
        # Check if we recently processed this event
        if event_key in self._recent_events:
            last_time = self._last_event_time.get(event_key, 0)
            if current_time - last_time < self.debounce_seconds:
                return False
        
        # Update tracking
        self._recent_events.add(event_key)
        self._last_event_time[event_key] = current_time
        
        # Clean up old events (older than 10 seconds)
        to_remove = []
        for key, timestamp in self._last_event_time.items():
            if current_time - timestamp > 10.0:
                to_remove.append(key)
        
        for key in to_remove:
            self._recent_events.discard(key)
            del self._last_event_time[key]
        
        return True
    
    def on_created(self, event: FileSystemEvent):
        """Handle file/directory creation"""
        if event.is_directory:
            return
        
        path = Path(event.src_path)
        
        if self.should_ignore(path):
            return
        
        if not self._should_process_event('created', path):
            return
        
        self.logger.info(f"File created: {path.name}")
        try:
            self.on_created(path)
        except Exception as e:
            self.logger.error(f"Error handling created event: {e}")
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification"""
        if event.is_directory:
            return
        
        path = Path(event.src_path)
        
        if self.should_ignore(path):
            return
        
        if not self._should_process_event('modified', path):
            return
        
        self.logger.info(f"File modified: {path.name}")
        try:
            self.on_modified(path)
        except Exception as e:
            self.logger.error(f"Error handling modified event: {e}")
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion"""
        if event.is_directory:
            return
        
        path = Path(event.src_path)
        
        if self.should_ignore(path):
            return
        
        if not self._should_process_event('deleted', path):
            return
        
        self.logger.info(f"File deleted: {path.name}")
        try:
            self.on_deleted(path)
        except Exception as e:
            self.logger.error(f"Error handling deleted event: {e}")
    
    def start(self):
        """Start watching the folder"""
        if self.is_running:
            self.logger.warning("Watcher is already running")
            return
        
        if not self.watch_path.exists():
            self.logger.error(f"Watch path does not exist: {self.watch_path}")
            return
        
        self.logger.info(f"Starting file watcher on: {self.watch_path}")
        self.observer.schedule(self, str(self.watch_path), recursive=True)
        self.observer.start()
        self.is_running = True
    
    def stop(self):
        """Stop watching the folder"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping file watcher")
        self.observer.stop()
        self.observer.join()
        self.is_running = False


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    def on_created(path: Path):
        print(f"✅ Created: {path}")
    
    def on_modified(path: Path):
        print(f"✏️ Modified: {path}")
    
    def on_deleted(path: Path):
        print(f"🗑️ Deleted: {path}")
    
    # Watch current directory
    watch_path = Path.cwd()
    watcher = LocalFileWatcher(
        watch_path=watch_path,
        on_created=on_created,
        on_modified=on_modified,
        on_deleted=on_deleted
    )
    
    try:
        watcher.start()
        print(f"👀 Watching: {watch_path}")
        print("Press Ctrl+C to stop...")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
        watcher.stop()
