#!/usr/bin/env python3
"""
Test download URLs for files in folders
"""

import sys
sys.path.insert(0, 'src')

from genspark_api import GenSparkAPIClient
import requests

client = GenSparkAPIClient()

if client.load_cookies_from_chrome():
    files = client.list_files(limit=100)
    
    # Find one root file and one folder file
    root_file = None
    folder_file = None
    
    for f in files:
        if ':root' in f.get('parent_id', '') and not root_file:
            root_file = f
        elif ':root' not in f.get('parent_id', '') and not folder_file:
            folder_file = f
        
        if root_file and folder_file:
            break
    
    print("=" * 80)
    print("Testing Download URL Patterns")
    print("=" * 80)
    
    for test_file, label in [(root_file, "ROOT FILE"), (folder_file, "FOLDER FILE")]:
        if not test_file:
            continue
            
        file_id = test_file['id']
        file_name = test_file['name']
        parent_id = test_file.get('parent_id', '')
        
        print(f"\n{label}: {file_name}")
        print(f"  ID: {file_id}")
        print(f"  Parent: {parent_id}")
        print()
        
        # Test different URL patterns
        patterns = [
            f"https://www.genspark.ai/api/aidrive/download/files/{file_name}",
            f"https://www.genspark.ai/api/aidrive/download/{file_id}",
            f"https://www.genspark.ai/api/aidrive/download/files/{file_id}",
            f"https://www.genspark.ai/api/aidrive/files/{file_id}/download",
        ]
        
        for url in patterns:
            try:
                response = client.session.get(url, timeout=5, allow_redirects=False)
                
                if response.status_code == 200:
                    print(f"  ✅ {response.status_code} | {url}")
                    print(f"     Content-Type: {response.headers.get('content-type')}")
                    print(f"     Size: {len(response.content)} bytes")
                elif response.status_code in [301, 302]:
                    location = response.headers.get('Location', '')[:80]
                    print(f"  ↪️  {response.status_code} | {url}")
                    print(f"     Redirect: {location}")
                elif response.status_code == 400:
                    print(f"  ❌ {response.status_code} | {url}")
                elif response.status_code == 404:
                    print(f"  ⚫ {response.status_code} | {url}")
                else:
                    print(f"  ⚠️  {response.status_code} | {url}")
                    
            except Exception as e:
                print(f"  💥 Error | {url}")
                print(f"     {e}")
        
        print()
    
    print("=" * 80)
else:
    print("❌ Failed to load cookies")
