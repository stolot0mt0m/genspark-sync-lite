#!/usr/bin/env python3
"""
Test script to debug folder upload with spaces
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from genspark_api import GenSparkAPIClient

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    logger.info("=== Testing Folder Upload with Spaces ===")
    
    # Initialize API client
    client = GenSparkAPIClient()
    
    # Load cookies
    if not client.load_cookies_from_chrome():
        logger.error("Failed to load cookies")
        return
    
    # Test connection
    logger.info("Testing connection...")
    if not client.test_connection():
        logger.error("Connection test failed")
        return
    
    logger.info("✅ Connection successful")
    
    # Test 1: Create folder with spaces
    folder_name = "Test Mit Leerzeichen"
    logger.info(f"\n=== Test 1: Create folder '{folder_name}' ===")
    result = client.create_folder(folder_name)
    logger.info(f"Result: {result}")
    
    # Test 2: Upload file to folder with spaces
    test_file = Path("/tmp/test_code_upload.txt")
    remote_path = f"{folder_name}/test_code_upload.txt"
    
    logger.info(f"\n=== Test 2: Upload file to '{remote_path}' ===")
    logger.info(f"Local file: {test_file}")
    logger.info(f"Remote path: {remote_path}")
    
    result = client.upload_file(test_file, remote_path)
    logger.info(f"Upload result: {result}")
    
    if result:
        logger.info("✅ Upload successful!")
    else:
        logger.error("❌ Upload failed!")

if __name__ == "__main__":
    main()
