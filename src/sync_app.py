#!/usr/bin/env python3
"""
GenSpark Sync Lite - Main Application
Lightweight bi-directional sync without browser automation
"""

import logging
import time
import signal
import sys
from pathlib import Path
from typing import Optional
import threading

from genspark_api import GenSparkAPIClient
from file_watcher import LocalFileWatcher
from sync_engine import SyncEngine


class GenSparkSyncApp:
    """Main sync application"""
    
    def __init__(self, sync_folder: Path, poll_interval: int = 30, sync_strategy: str = 'ask'):
        self.sync_folder = Path(sync_folder)
        self.poll_interval = poll_interval
        self.sync_strategy = sync_strategy  # 'local', 'remote', or 'ask'
        
        # Components
        self.api_client: Optional[GenSparkAPIClient] = None
        self.sync_engine: Optional[SyncEngine] = None
        self.file_watcher: Optional[LocalFileWatcher] = None
        
        # State
        self.is_running = False
        self.poller_thread: Optional[threading.Thread] = None
        
        # Logging
        self.logger = logging.getLogger('SyncApp')
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging"""
        log_file = self.sync_folder / '.genspark_sync.log'
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def initialize(self) -> bool:
        """Initialize all components"""
        self.logger.info("Initializing GenSpark Sync Lite...")
        
        # Create sync folder if not exists
        self.sync_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize API client
        self.api_client = GenSparkAPIClient()
        
        # Load cookies from Chrome
        if not self.api_client.load_cookies_from_chrome():
            self.logger.error("Failed to load cookies from Chrome")
            self.logger.info("Please ensure:")
            self.logger.info("  1. You're logged into genspark.ai in Chrome")
            self.logger.info("  2. Chrome is closed (for browser-cookie3 to read cookies)")
            return False
        
        # Test API connection
        if not self.api_client.test_connection():
            self.logger.error("Failed to connect to GenSpark API")
            return False
        
        self.logger.info("✅ API connection successful")
        
        # Initialize sync engine
        self.sync_engine = SyncEngine(self.sync_folder, self.api_client, sync_strategy=self.sync_strategy)
        
        # Initialize file watcher
        self.file_watcher = LocalFileWatcher(
            watch_path=self.sync_folder,
            on_created=lambda event: self.sync_engine.handle_local_change(Path(event.src_path), 'created'),
            on_modified=lambda event: self.sync_engine.handle_local_change(Path(event.src_path), 'modified'),
            on_deleted=lambda event: self.sync_engine.handle_local_change(Path(event.src_path), 'deleted'),
            debounce_seconds=2.0
        )
        
        self.logger.info("✅ All components initialized")
        return True
    
    def _ai_drive_poller(self):
        """Background thread that polls AI Drive for changes"""
        self.logger.info(f"Starting AI Drive poller (interval: {self.poll_interval}s)")
        
        last_sync = 0
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Check if it's time to sync
                if current_time - last_sync >= self.poll_interval:
                    self.logger.debug("Polling AI Drive for changes...")
                    
                    # Perform sync
                    stats = self.sync_engine.sync_once()
                    
                    # Log if there were changes
                    if stats['uploads'] > 0 or stats['downloads'] > 0:
                        self.logger.info(
                            f"Sync: {stats['downloads']} downloads, "
                            f"{stats['uploads']} uploads, "
                            f"{stats['conflicts']} conflicts"
                        )
                    
                    last_sync = current_time
                
                # Sleep for 1 second and check again
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Poller error: {e}")
                time.sleep(5)  # Back off on error
    
    def start(self):
        """Start the sync application"""
        if self.is_running:
            self.logger.warning("App is already running")
            return
        
        self.logger.info("🚀 Starting GenSpark Sync Lite...")
        self.logger.info(f"📁 Sync folder: {self.sync_folder}")
        
        # Start file watcher
        self.file_watcher.start()
        self.logger.info("✅ File watcher started")
        
        # Initial sync
        self.logger.info("Performing initial sync...")
        stats = self.sync_engine.sync_once()
        self.logger.info(
            f"Initial sync complete: {stats['downloads']} downloads, "
            f"{stats['uploads']} uploads, {stats['conflicts']} conflicts"
        )
        
        # Start poller thread
        self.is_running = True
        self.poller_thread = threading.Thread(target=self._ai_drive_poller, daemon=True)
        self.poller_thread.start()
        self.logger.info("✅ AI Drive poller started")
        
        self.logger.info("🎉 GenSpark Sync Lite is now running!")
        self.logger.info(f"   - Local changes: Uploaded immediately")
        self.logger.info(f"   - Remote changes: Checked every {self.poll_interval}s")
    
    def stop(self):
        """Stop the sync application"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping GenSpark Sync Lite...")
        
        # Stop poller
        self.is_running = False
        if self.poller_thread:
            self.poller_thread.join(timeout=5)
        
        # Stop file watcher
        if self.file_watcher:
            self.file_watcher.stop()
        
        # Save final state
        if self.sync_engine:
            self.sync_engine.save_state()
        
        self.logger.info("✅ GenSpark Sync Lite stopped")
    
    def print_stats(self):
        """Print current statistics"""
        if self.sync_engine:
            stats = self.sync_engine.stats
            print("\n📊 Sync Statistics:")
            print(f"   Uploads: {stats['uploads']}")
            print(f"   Downloads: {stats['downloads']}")
            print(f"   Conflicts: {stats['conflicts']}")
            print(f"   Errors: {stats['errors']}")


def main():
    """Main entry point"""
    print("=" * 60)
    print("  GenSpark Sync Lite - Lightweight Bi-directional Sync")
    print("  No browser automation, minimal resources")
    print("=" * 60)
    print()
    
    # Get sync folder from user or use default
    default_folder = Path.home() / "GenSpark AI Drive"
    
    print(f"Sync folder: {default_folder}")
    response = input("Use this folder? [Y/n]: ").strip().lower()
    
    if response in ['n', 'no']:
        folder_path = input("Enter sync folder path: ").strip()
        sync_folder = Path(folder_path).expanduser()
    else:
        sync_folder = default_folder
    
    # Get poll interval
    print(f"\nDefault poll interval: 30 seconds")
    response = input("Change poll interval? [y/N]: ").strip().lower()
    
    if response in ['y', 'yes']:
        try:
            poll_interval = int(input("Enter poll interval (seconds): ").strip())
        except ValueError:
            print("Invalid input, using default (30s)")
            poll_interval = 30
    else:
        poll_interval = 30
    
    # Get initial sync strategy
    print(f"\n⚠️  Initial Sync Strategy (for remote-only folders/files):")
    print("  [L] Local priority - Delete remote files that don't exist locally")
    print("  [R] Remote priority - Download remote files that don't exist locally")
    print("  [A] Ask - Prompt for each conflict (default)")
    response = input("Choose strategy [L/R/A]: ").strip().upper()
    
    if response == 'L':
        sync_strategy = 'local'
        print("✅ Using LOCAL priority - Remote-only items will be deleted")
    elif response == 'R':
        sync_strategy = 'remote'
        print("✅ Using REMOTE priority - Remote-only items will be downloaded")
    else:
        sync_strategy = 'ask'
        print("✅ Using ASK mode - Will prompt for conflicts")
    
    print()
    
    # Create app with sync strategy
    app = GenSparkSyncApp(sync_folder, poll_interval, sync_strategy)
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        print("\n\nReceived interrupt signal...")
        app.stop()
        app.print_stats()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize
    if not app.initialize():
        print("\n❌ Initialization failed!")
        print("\n💡 Troubleshooting:")
        print("  1. Make sure you're logged into genspark.ai in Chrome")
        print("  2. Close Chrome completely (so cookies can be read)")
        print("  3. Run this app again")
        sys.exit(1)
    
    # Start
    app.start()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
