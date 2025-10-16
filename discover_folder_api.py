#!/usr/bin/env python3
"""
Discover folder API endpoint
"""

import sys
sys.path.insert(0, 'src')

from genspark_api import GenSparkAPIClient

client = GenSparkAPIClient()

if client.load_cookies_from_chrome():
    print("=" * 80)
    print("Testing Folder API Endpoints")
    print("=" * 80)
    
    # Possible folder/tree endpoints
    endpoints = [
        "/api/aidrive/files",
        "/api/aidrive/folders",
        "/api/aidrive/tree",
        "/api/aidrive/list",
        "/api/aidrive/all",
        "/aidrive/api/files",
        "/aidrive/api/folders",
        "/aidrive/files/api/folders",
    ]
    
    for endpoint in endpoints:
        url = f"https://www.genspark.ai{endpoint}"
        
        try:
            print(f"\nTesting: {endpoint}")
            response = client.session.get(url, timeout=5)
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                
                if 'json' in content_type.lower():
                    data = response.json()
                    
                    # Check if it has items
                    if 'items' in data:
                        items = data['items']
                        folders = [i for i in items if i.get('type') == 'folder']
                        files = [i for i in items if i.get('type') == 'file']
                        
                        print(f"  ✅ JSON Response")
                        print(f"     Items: {len(items)}")
                        print(f"     Folders: {len(folders)}")
                        print(f"     Files: {len(files)}")
                        
                        if folders:
                            print(f"  🎯 FOUND FOLDER API!")
                            print(f"     Sample folders:")
                            for folder in folders[:3]:
                                print(f"       - {folder.get('name')} (ID: {folder.get('id')})")
                    else:
                        print(f"  ⚠️  JSON but no 'items' key")
                        print(f"     Keys: {list(data.keys())[:10]}")
                else:
                    print(f"  ⚠️  HTML response")
                    
            elif response.status_code == 404:
                print(f"  ❌ Not Found")
            elif response.status_code == 403:
                print(f"  ⚠️  Forbidden")
            else:
                print(f"  ⚠️  Status: {response.status_code}")
                
        except Exception as e:
            print(f"  💥 Error: {e}")
    
    print("\n" + "=" * 80)
    print("\n💡 Alternative: Use file_id instead of folder/filename")
    print("=" * 80)
    
    # Test if we can download by file_id directly
    print("\nTesting download by file_id...")
    
    # Get a folder file
    response = client.session.get(
        "https://www.genspark.ai/api/aidrive/recent/files",
        params={"limit": 100},
        timeout=10
    )
    
    if response.status_code == 200:
        files = response.json().get('items', [])
        folder_file = None
        
        for f in files:
            if ':root' not in f.get('parent_id', ''):
                folder_file = f
                break
        
        if folder_file:
            file_id = folder_file['id']
            file_name = folder_file['name']
            
            print(f"\nTest file: {file_name}")
            print(f"File ID: {file_id}")
            
            # Test download by ID
            test_urls = [
                f"https://www.genspark.ai/api/aidrive/download/{file_id}",
                f"https://www.genspark.ai/api/aidrive/files/{file_id}/download",
                f"https://www.genspark.ai/api/aidrive/download/id/{file_id}",
            ]
            
            for url in test_urls:
                try:
                    print(f"\n  Testing: {url}")
                    response = client.session.get(url, timeout=5, allow_redirects=False)
                    
                    if response.status_code == 200:
                        print(f"    ✅ 200 OK - Direct download!")
                        print(f"    Size: {len(response.content)} bytes")
                    elif response.status_code in [301, 302]:
                        location = response.headers.get('Location', '')[:80]
                        print(f"    ↪️  {response.status_code} Redirect")
                        print(f"    To: {location}")
                    elif response.status_code == 404:
                        print(f"    ❌ 404 Not Found")
                    elif response.status_code == 400:
                        print(f"    ❌ 400 Bad Request")
                    else:
                        print(f"    ⚠️  {response.status_code}")
                        
                except Exception as e:
                    print(f"    💥 Error: {e}")
    
    print("\n" + "=" * 80)
else:
    print("❌ Failed to load cookies")
