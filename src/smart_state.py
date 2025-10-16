#!/usr/bin/env python3
"""
Smart State Management with SQLite
High-performance state tracking with indexes and quick hash
"""

import sqlite3
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime


class SmartSyncState:
    """SQLite-based state management with performance optimizations"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.logger = logging.getLogger('SmartState')
        self.conn: Optional[sqlite3.Connection] = None
        
        # Open connection
        self.connect()
        
        # Create schema if needed
        self.create_schema()
        
        self.logger.info(f"Smart state initialized: {db_path}")
    
    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False  # Allow multi-threading
        )
        # Enable Write-Ahead Logging for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")
        # Return rows as dictionaries
        self.conn.row_factory = sqlite3.Row
    
    def create_schema(self):
        """Create tables and indexes"""
        # Main files table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                size INTEGER NOT NULL,
                mtime REAL NOT NULL,
                quick_hash TEXT,
                full_hash TEXT,
                remote_id TEXT,
                last_sync INTEGER,
                status TEXT DEFAULT 'synced'
            )
        """)
        
        # Indexes for fast queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_mtime 
            ON files(mtime)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_last_sync 
            ON files(last_sync)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status 
            ON files(status)
        """)
        
        # Metadata table for tracking
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        self.conn.commit()
        self.logger.debug("Database schema created/verified")
    
    def get_quick_hash(self, file_path: Path) -> Optional[str]:
        """
        Calculate quick hash (first 8KB only)
        Much faster than full file hash
        """
        try:
            with open(file_path, 'rb') as f:
                # Read only first 8KB
                chunk = f.read(8192)
                if not chunk:
                    return None
                return hashlib.md5(chunk).hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate quick hash for {file_path}: {e}")
            return None
    
    def get_file_state(self, path: str) -> Optional[Dict[str, Any]]:
        """Get state for a specific file"""
        cursor = self.conn.execute(
            "SELECT * FROM files WHERE path = ?",
            (path,)
        )
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_all_files(self) -> Dict[str, Dict[str, Any]]:
        """Get all files from state (for compatibility with old code)"""
        cursor = self.conn.execute("SELECT * FROM files")
        result = {}
        
        for row in cursor:
            path = row['path']
            result[path] = {
                'size': row['size'],
                'modified_time': int(row['mtime']),
                'quick_hash': row['quick_hash'],
                'full_hash': row['full_hash'],
                'remote_id': row['remote_id'],
                'last_sync': row['last_sync'],
                'status': row['status']
            }
        
        return result
    
    def get_changed_files(self, since_timestamp: int) -> List[str]:
        """Get files changed since timestamp (FAST with index)"""
        cursor = self.conn.execute("""
            SELECT path FROM files
            WHERE mtime > ? OR last_sync > ?
        """, (since_timestamp, since_timestamp))
        
        return [row['path'] for row in cursor]
    
    def update_file(self, path: str, size: int, mtime: float, 
                   quick_hash: Optional[str] = None,
                   remote_id: Optional[str] = None,
                   status: str = 'synced'):
        """Update or insert file state"""
        now = int(datetime.now().timestamp())
        
        self.conn.execute("""
            INSERT INTO files (path, size, mtime, quick_hash, remote_id, last_sync, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                size = excluded.size,
                mtime = excluded.mtime,
                quick_hash = excluded.quick_hash,
                remote_id = excluded.remote_id,
                last_sync = excluded.last_sync,
                status = excluded.status
        """, (path, size, mtime, quick_hash, remote_id, now, status))
        
        self.conn.commit()
    
    def update_file_batch(self, files: List[Dict[str, Any]]):
        """Batch update multiple files (much faster)"""
        now = int(datetime.now().timestamp())
        
        data = []
        for file_info in files:
            data.append((
                file_info['path'],
                file_info['size'],
                file_info['mtime'],
                file_info.get('quick_hash'),
                file_info.get('remote_id'),
                now,
                file_info.get('status', 'synced')
            ))
        
        self.conn.executemany("""
            INSERT INTO files (path, size, mtime, quick_hash, remote_id, last_sync, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                size = excluded.size,
                mtime = excluded.mtime,
                quick_hash = excluded.quick_hash,
                remote_id = excluded.remote_id,
                last_sync = excluded.last_sync,
                status = excluded.status
        """, data)
        
        self.conn.commit()
    
    def delete_file(self, path: str):
        """Remove file from state"""
        self.conn.execute("DELETE FROM files WHERE path = ?", (path,))
        self.conn.commit()
    
    def delete_files_batch(self, paths: List[str]):
        """Delete multiple files (batch operation)"""
        if not paths:
            return
        
        placeholders = ','.join('?' * len(paths))
        self.conn.execute(
            f"DELETE FROM files WHERE path IN ({placeholders})",
            paths
        )
        self.conn.commit()
    
    def file_exists(self, path: str) -> bool:
        """Check if file exists in state (FAST with primary key)"""
        cursor = self.conn.execute(
            "SELECT 1 FROM files WHERE path = ? LIMIT 1",
            (path,)
        )
        return cursor.fetchone() is not None
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about state"""
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'synced' THEN 1 ELSE 0 END) as synced,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(size) as total_size
            FROM files
        """)
        
        row = cursor.fetchone()
        return {
            'total': row['total'],
            'synced': row['synced'],
            'pending': row['pending'],
            'total_size': row['total_size'] or 0
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def migrate_json_to_sqlite(json_path: Path, db_path: Path) -> bool:
    """
    Migrate old JSON state to SQLite
    Returns True if migration was performed
    """
    import json
    
    logger = logging.getLogger('Migration')
    
    # Check if JSON exists and SQLite doesn't
    if not json_path.exists():
        return False
    
    if db_path.exists():
        logger.info("SQLite database already exists, skipping migration")
        return False
    
    logger.info(f"Migrating JSON state to SQLite: {json_path} → {db_path}")
    
    try:
        # Load old JSON state
        with open(json_path, 'r') as f:
            old_state = json.load(f)
        
        logger.info(f"Loaded {len(old_state)} files from JSON")
        
        # Create new SQLite state
        state = SmartSyncState(db_path)
        
        # Migrate data in batches
        batch = []
        for path, file_info in old_state.items():
            batch.append({
                'path': path,
                'size': file_info.get('size', 0),
                'mtime': file_info.get('modified_time', 0),
                'quick_hash': None,  # Will be calculated on next scan
                'remote_id': None,
                'status': 'synced'
            })
            
            # Batch insert every 100 files
            if len(batch) >= 100:
                state.update_file_batch(batch)
                batch = []
        
        # Insert remaining files
        if batch:
            state.update_file_batch(batch)
        
        state.close()
        
        # Rename old JSON as backup
        backup_path = json_path.with_suffix('.json.backup')
        json_path.rename(backup_path)
        
        logger.info(f"✅ Migration complete! Old file backed up to: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # Clean up partial database
        if db_path.exists():
            db_path.unlink()
        return False


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test SQLite state
    test_db = Path("/tmp/test_state.db")
    if test_db.exists():
        test_db.unlink()
    
    state = SmartSyncState(test_db)
    
    # Add some test data
    state.update_file("test1.txt", 1024, 1234567890.0, "abc123")
    state.update_file("test2.txt", 2048, 1234567891.0, "def456")
    state.update_file("folder/test3.txt", 512, 1234567892.0, "ghi789")
    
    # Query
    print("\nAll files:")
    print(state.get_all_files())
    
    print("\nChanged since 1234567890:")
    print(state.get_changed_files(1234567890))
    
    print("\nStats:")
    print(state.get_stats())
    
    state.close()
    
    print(f"\n✅ Test complete! Database created at: {test_db}")
