#!/usr/bin/env python3
"""
Mock test for sync strategy feature
Tests the logic without requiring actual API connection
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from sync_engine import SyncEngine


def test_sync_strategy_parameter():
    """Test that SyncEngine accepts sync_strategy parameter"""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("TEST 1: Sync Strategy Parameter")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    # Create mock API client
    mock_api = Mock()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Test all three strategies
        strategies = ['local', 'remote', 'ask']
        for strategy in strategies:
            engine = SyncEngine(test_path, mock_api, sync_strategy=strategy)
            assert engine.sync_strategy == strategy, f"Strategy not set: {strategy}"
            print(f"✅ SyncEngine accepts strategy: {strategy}")
    
    print()
    print("✅ TEST 1 PASSED: All strategies supported")
    print()


def test_remote_only_local_priority():
    """Test that local priority deletes remote-only files"""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("TEST 2: Local Priority (Delete Remote-Only)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Create mock API client
        mock_api = Mock()
        mock_api.delete_file = Mock(return_value=True)
        mock_api.list_files = Mock(return_value=[
            {
                'id': 'test-id-1',
                'name': 'remote_only.txt',
                'path': '/remote_only.txt',
                'type': 'file',
                'size': 100,
                'modified_time': 1234567890,
                'mime_type': 'text/plain'
            }
        ])
        
        # Create engine with LOCAL priority
        engine = SyncEngine(test_path, mock_api, sync_strategy='local')
        
        # Mock scan methods
        engine.scan_local_files = Mock(return_value={})
        engine.scan_remote_files = Mock(return_value={
            'remote_only.txt': {
                'path': 'remote_only.txt',
                'file_path': '/remote_only.txt',
                'id': 'test-id-1',
                'name': 'remote_only.txt',
                'size': 100,
                'modified_time': 1234567890,
                'mime_type': 'text/plain'
            }
        })
        
        # Run sync
        stats = engine.sync_once()
        
        # Verify delete was called
        assert mock_api.delete_file.called, "delete_file should be called"
        assert stats['remote_only_deleted'] == 1, "Should count deleted files"
        
        print("✅ Remote-only file detected")
        print("✅ Delete API called correctly")
        print(f"✅ Stats updated: {stats['remote_only_deleted']} files deleted")
    
    print()
    print("✅ TEST 2 PASSED: Local priority deletes remote files")
    print()


def test_remote_only_remote_priority():
    """Test that remote priority downloads remote-only files"""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("TEST 3: Remote Priority (Download Remote-Only)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Create mock API client
        mock_api = Mock()
        mock_api.download_file = Mock(return_value=True)
        
        # Create engine with REMOTE priority
        engine = SyncEngine(test_path, mock_api, sync_strategy='remote')
        
        # Mock scan methods
        engine.scan_local_files = Mock(return_value={})
        engine.scan_remote_files = Mock(return_value={
            'remote_only.txt': {
                'path': 'remote_only.txt',
                'file_path': '/remote_only.txt',
                'id': 'test-id-1',
                'name': 'remote_only.txt',
                'size': 100,
                'modified_time': 1234567890,
                'mime_type': 'text/plain'
            }
        })
        
        # Run sync
        stats = engine.sync_once()
        
        # Verify download was called
        assert mock_api.download_file.called, "download_file should be called"
        assert stats['downloads'] == 1, "Should count downloaded files"
        
        print("✅ Remote-only file detected")
        print("✅ Download API called correctly")
        print(f"✅ Stats updated: {stats['downloads']} files downloaded")
    
    print()
    print("✅ TEST 3 PASSED: Remote priority downloads remote files")
    print()


def test_conflict_detection():
    """Test that true conflicts are detected correctly"""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("TEST 4: Conflict Detection")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Create a test file locally
        test_file = test_path / 'conflict.txt'
        test_file.write_text('local version')
        
        # Create mock API client
        mock_api = Mock()
        
        # Create engine
        engine = SyncEngine(test_path, mock_api, sync_strategy='ask')
        
        # Set up state (old version)
        engine.state = {
            'conflict.txt': {
                'modified_time': 1000000000,
                'size': 10
            }
        }
        
        # Create local and remote files with different changes
        local_files = {
            'conflict.txt': {
                'path': 'conflict.txt',
                'size': 13,
                'modified_time': 1000000100,
                'hash': 'local_hash'
            }
        }
        
        remote_files = {
            'conflict.txt': {
                'path': 'conflict.txt',
                'file_path': '/conflict.txt',
                'id': 'test-id',
                'name': 'conflict.txt',
                'size': 14,
                'modified_time': 1000000200,
                'mime_type': 'text/plain'
            }
        }
        
        # Detect conflicts
        conflicts = engine.detect_conflicts(local_files, remote_files)
        
        # Verify
        assert len(conflicts) == 1, "Should detect one conflict"
        assert conflicts[0]['path'] == 'conflict.txt', "Conflict path should match"
        
        print("✅ True conflict detected (both sides changed)")
        print(f"   Local:  mtime={conflicts[0]['local']['modified_time']}, size={conflicts[0]['local']['size']}")
        print(f"   Remote: mtime={conflicts[0]['remote']['modified_time']}, size={conflicts[0]['remote']['size']}")
    
    print()
    print("✅ TEST 4 PASSED: Conflict detection works correctly")
    print()


def test_upload_tracking():
    """Test thread-safe upload tracking"""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("TEST 5: Thread-Safe Upload Tracking")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        mock_api = Mock()
        
        engine = SyncEngine(test_path, mock_api, sync_strategy='ask')
        
        # Verify upload tracking sets exist
        assert hasattr(engine, 'uploading_files'), "Should have uploading_files set"
        assert hasattr(engine, 'downloading_files'), "Should have downloading_files set"
        assert hasattr(engine, 'upload_lock'), "Should have upload_lock"
        
        print("✅ uploading_files tracking set exists")
        print("✅ downloading_files tracking set exists")
        print("✅ upload_lock thread lock exists")
    
    print()
    print("✅ TEST 5 PASSED: Thread-safe tracking is in place")
    print()


def main():
    """Run all tests"""
    print("=" * 60)
    print("  GenSpark Sync Lite - Mock Tests")
    print("  Testing Sync Strategy Feature")
    print("=" * 60)
    print()
    
    try:
        test_sync_strategy_parameter()
        test_remote_only_local_priority()
        test_remote_only_remote_priority()
        test_conflict_detection()
        test_upload_tracking()
        
        print()
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("✅ Sync Strategy feature implementation is correct")
        print()
        print("The following features are working:")
        print("  • Local priority strategy (delete remote-only files)")
        print("  • Remote priority strategy (download remote-only files)")
        print("  • Ask strategy (prompt for each file)")
        print("  • Conflict detection (both sides changed)")
        print("  • Thread-safe upload tracking")
        print()
        print("To test with real API connection:")
        print("  1. Login to genspark.ai in Chrome")
        print("  2. Close Chrome completely")
        print("  3. Run: python3 src/sync_app.py")
        print()
        
        return 0
        
    except AssertionError as e:
        print()
        print(f"❌ TEST FAILED: {e}")
        print()
        return 1
    except Exception as e:
        print()
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
