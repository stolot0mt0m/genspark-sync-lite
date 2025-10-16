#!/usr/bin/env python3
"""
Upload API Discovery
Tests various upload endpoint patterns to find the correct one
"""

import sys
import logging
from pathlib import Path
import tempfile

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from genspark_api import GenSparkAPIClient

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('UploadDiscovery')

def test_upload_endpoints(api_client):
    """Test various upload endpoint patterns"""
    
    # Create a small test file
    test_content = b"Test file for upload endpoint discovery"
    test_filename = "test_upload_discovery.txt"
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(test_content)
        tmp_path = Path(tmp.name)
    
    logger.info(f"Created test file: {tmp_path}")
    
    # Test different endpoint patterns
    endpoints_to_test = [
        # Based on download pattern
        ("POST", "/api/aidrive/upload/files/{filename}"),
        ("POST", "/api/aidrive/files"),
        ("POST", "/api/aidrive/files/upload"),
        
        # Based on similar patterns from other GenSpark APIs
        ("POST", "/api/side/wget_upload_url/files/{filename}"),
        ("POST", "/api/side/upload"),
        
        # Generic patterns
        ("PUT", "/api/aidrive/files/{filename}"),
        ("POST", "/api/aidrive/upload"),
    ]
    
    logger.info(f"\n{'='*70}")
    logger.info("🔍 Testing Upload Endpoints")
    logger.info(f"{'='*70}\n")
    
    for method, endpoint_pattern in endpoints_to_test:
        endpoint = endpoint_pattern.replace("{filename}", test_filename)
        url = f"{api_client.BASE_URL}{endpoint}"
        
        logger.info(f"\n📤 Testing: {method} {endpoint}")
        logger.info(f"   URL: {url}")
        
        try:
            # Prepare request based on method
            if method == "POST":
                # Try JSON request first (for getting upload URL)
                response = api_client.session.post(url, timeout=10)
            elif method == "PUT":
                # Try direct file upload
                with open(tmp_path, 'rb') as f:
                    response = api_client.session.put(url, data=f, timeout=10)
            
            logger.info(f"   Status: {response.status_code}")
            
            # Log response
            try:
                data = response.json()
                logger.info(f"   Response: {data}")
                
                if response.status_code == 200:
                    logger.info(f"   ✅ SUCCESS! Endpoint works!")
                elif response.status_code == 404:
                    logger.info(f"   ❌ 404 Not Found")
                elif response.status_code == 400:
                    logger.info(f"   ⚠️  400 Bad Request - Endpoint exists but needs different format")
                elif response.status_code == 403:
                    logger.info(f"   🔒 403 Forbidden - Endpoint exists but authentication issue")
                else:
                    logger.info(f"   ⚠️  {response.status_code} - Unexpected response")
                    
            except:
                logger.info(f"   Response (text): {response.text[:200]}")
                
        except Exception as e:
            logger.error(f"   ❌ Exception: {e}")
    
    # Clean up
    tmp_path.unlink()
    logger.info(f"\n{'='*70}")
    logger.info("Discovery complete!")
    logger.info(f"{'='*70}\n")

def analyze_list_response(api_client):
    """
    Analyze the list_files response to understand the file structure
    This might give us hints about upload patterns
    """
    logger.info(f"\n{'='*70}")
    logger.info("📋 Analyzing File Structure from List API")
    logger.info(f"{'='*70}\n")
    
    items = api_client.list_files()
    if not items:
        logger.error("No items returned")
        return
    
    # Look at a sample file's structure
    sample_file = None
    for item in items:
        if item.get('type') == 'file':
            sample_file = item
            break
    
    if sample_file:
        logger.info("Sample file structure:")
        for key, value in sample_file.items():
            logger.info(f"  {key}: {value}")
    
    # Check if there's any upload-related metadata
    logger.info("\n💡 Looking for upload-related hints...")
    
    # Check for any fields that might indicate upload endpoints
    if sample_file:
        interesting_fields = ['url', 'upload_url', 'write_url', 'put_url', 'post_url']
        for field in interesting_fields:
            if field in sample_file:
                logger.info(f"  Found {field}: {sample_file[field]}")

def main():
    # Initialize API client
    api_client = GenSparkAPIClient()
    
    # Load cookies from Chrome
    logger.info("Loading cookies from Chrome...")
    if not api_client.load_cookies_from_chrome():
        logger.error("❌ Failed to load cookies from Chrome!")
        logger.info("\n💡 This script needs to run on a Mac with Chrome browser")
        logger.info("   Please run it locally with: python3 discover_upload_api.py")
        return False
    
    # Test connection
    logger.info("Testing API connection...")
    if not api_client.test_connection():
        logger.error("❌ API connection failed!")
        return False
    
    logger.info("✅ API connection successful!\n")
    
    # First, analyze the list response
    analyze_list_response(api_client)
    
    # Then test upload endpoints
    test_upload_endpoints(api_client)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
