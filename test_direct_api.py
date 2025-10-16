#!/usr/bin/env python3
"""
Direct API test to verify URL encoding behavior
Tests the exact request that works in Web UI
"""

import requests
from urllib.parse import quote

def test_folder_upload_encoding():
    """Test different encoding strategies for folder names with spaces"""
    
    # This is the exact URL from the Web UI that WORKS
    working_url = "https://www.genspark.ai/api/aidrive/get_upload_url/files/Test%20Mit%20Leerzeichen/test_upload.md"
    
    print("=== Testing URL Encoding Strategies ===\n")
    print(f"✅ Working URL from Web UI:\n{working_url}\n")
    
    # Strategy 1: quote() entire path
    path1 = "Test Mit Leerzeichen/test_upload.md"
    encoded1 = quote(path1)
    url1 = f"https://www.genspark.ai/api/aidrive/get_upload_url/files/{encoded1}"
    print(f"Strategy 1 - quote(full_path):")
    print(f"  Input:  {path1}")
    print(f"  Encoded: {encoded1}")
    print(f"  URL:    {url1}")
    print(f"  Match:  {url1 == working_url}\n")
    
    # Strategy 2: quote() with safe='/' to preserve slashes
    encoded2 = quote(path1, safe='/')
    url2 = f"https://www.genspark.ai/api/aidrive/get_upload_url/files/{encoded2}"
    print(f"Strategy 2 - quote(full_path, safe='/'):")
    print(f"  Input:  {path1}")
    print(f"  Encoded: {encoded2}")
    print(f"  URL:    {url2}")
    print(f"  Match:  {url2 == working_url}\n")
    
    # Strategy 3: Manual encoding (what Web UI might do)
    manual = "Test%20Mit%20Leerzeichen/test_upload.md"
    url3 = f"https://www.genspark.ai/api/aidrive/get_upload_url/files/{manual}"
    print(f"Strategy 3 - Manual encoding:")
    print(f"  Encoded: {manual}")
    print(f"  URL:    {url3}")
    print(f"  Match:  {url3 == working_url}\n")
    
    # Analysis
    print("=== Analysis ===")
    if url2 == working_url:
        print("✅ Strategy 2 matches Web UI: quote(path, safe='/')")
        print("   This preserves slashes while encoding spaces")
        return "safe_slash"
    elif url1 == working_url:
        print("⚠️  Strategy 1 matches but encodes slashes too")
        return "quote_all"
    else:
        print("❌ None match - manual inspection needed")
        return None

if __name__ == "__main__":
    result = test_folder_upload_encoding()
    
    print(f"\n=== Recommendation ===")
    if result == "safe_slash":
        print("Change quote(filename) to quote(filename, safe='/')")
        print("This will preserve folder structure in URLs")
