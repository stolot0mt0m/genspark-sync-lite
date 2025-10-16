#!/usr/bin/env python3
"""
Test Complete Download Flow
Tests downloading all files including those in folders
"""

import sys
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from genspark_api import GenSparkAPIClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('DownloadTest')

def main():
    # Initialize API client
    api_client = GenSparkAPIClient()
    
    # Load cookies from Chrome
    logger.info("Loading cookies from Chrome...")
    if not api_client.load_cookies_from_chrome():
        logger.error("❌ Failed to load cookies from Chrome!")
        return False
    
    # Test connection
    logger.info("Testing API connection...")
    if not api_client.test_connection():
        logger.error("❌ API connection failed!")
        return False
    
    logger.info("✅ API connection successful!")
    
    # List all files using new endpoint
    logger.info("\n📁 Listing all files from AI Drive...")
    items = api_client.list_files()
    
    if not items:
        logger.error("❌ No items returned from API")
        return False
    
    # Separate folders and files
    folders = [item for item in items if item.get('type') == 'directory']
    files = [item for item in items if item.get('type') == 'file']
    
    # Filter out thumbnails
    real_files = [f for f in files if not (f['name'].startswith('thumb_') and f['name'].endswith('.jpg'))]
    
    logger.info(f"\n📊 Summary:")
    logger.info(f"  Total items: {len(items)}")
    logger.info(f"  Folders: {len(folders)}")
    logger.info(f"  Files: {len(files)}")
    logger.info(f"  Real files (no thumbnails): {len(real_files)}")
    
    # Show folder structure
    if folders:
        logger.info(f"\n📁 Folders found:")
        for folder in folders:
            logger.info(f"  - {folder['path']} (id: {folder['id']})")
    
    # Test downloading a few files from different locations
    logger.info(f"\n⬇️  Testing downloads...")
    
    # Create test download directory
    test_dir = Path(__file__).parent / 'test_downloads'
    test_dir.mkdir(exist_ok=True)
    logger.info(f"Download directory: {test_dir}")
    
    # Separate root files and folder files
    root_files = [f for f in real_files if not '/' in f['path'].strip('/') or f['path'].count('/') == 1]
    folder_files = [f for f in real_files if f['path'].count('/') > 1]
    
    logger.info(f"\n📄 Root files: {len(root_files)}")
    logger.info(f"📁 Files in folders: {len(folder_files)}")
    
    # Test a few downloads from each category
    test_files = []
    
    # Add up to 2 root files
    test_files.extend(root_files[:2])
    
    # Add up to 3 folder files
    test_files.extend(folder_files[:3])
    
    logger.info(f"\n🧪 Testing {len(test_files)} downloads:")
    
    success_count = 0
    fail_count = 0
    
    for file_info in test_files:
        file_path = file_info['path']
        file_name = file_info['name']
        file_id = file_info['id']
        
        # Create subdirectories if needed
        relative_path = file_path.lstrip('/')
        local_path = test_dir / relative_path
        
        logger.info(f"\n  Testing: {file_path}")
        logger.info(f"    Name: {file_name}")
        logger.info(f"    Local: {local_path}")
        
        try:
            result = api_client.download_file(file_id, file_name, file_path, local_path)
            
            if result:
                # Verify file exists
                if local_path.exists():
                    size = local_path.stat().st_size
                    logger.info(f"    ✅ Success! Size: {size} bytes")
                    success_count += 1
                else:
                    logger.error(f"    ❌ Download claimed success but file doesn't exist")
                    fail_count += 1
            else:
                logger.error(f"    ❌ Download failed")
                fail_count += 1
                
        except Exception as e:
            logger.error(f"    ❌ Exception: {e}")
            fail_count += 1
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 Download Test Results:")
    logger.info(f"  Total files: {len(real_files)}")
    logger.info(f"  Root files: {len(root_files)}")
    logger.info(f"  Folder files: {len(folder_files)}")
    logger.info(f"  Tested: {len(test_files)}")
    logger.info(f"  ✅ Successful: {success_count}")
    logger.info(f"  ❌ Failed: {fail_count}")
    logger.info(f"{'='*60}")
    
    if fail_count == 0:
        logger.info("✅ All tested downloads successful!")
        logger.info(f"\n💡 Next step: Run full sync with ./launch.sh to download all {len(real_files)} files")
        return True
    else:
        logger.error(f"❌ {fail_count} downloads failed - need to investigate")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
