#!/usr/bin/env python3
"""
Test different download endpoint patterns
"""

import requests
import browser_cookie3
import json

# Setup session
session = requests.Session()

# Load cookies
cookies = browser_cookie3.chrome(domain_name='genspark.ai')
for cookie in cookies:
    session.cookies.set_cookie(cookie)

# Add headers
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.genspark.ai/aidrive/files/',
    'Origin': 'https://www.genspark.ai',
})

# Test file from your list
test_file_id = "56ffa943-79b2-43a6-901e-8f04514eddbd"  # beschreibung.txt
test_file_name = "beschreibung.txt"

print("=" * 70)
print("Testing Download Endpoints")
print("=" * 70)
print(f"\nTest File: {test_file_name}")
print(f"File ID: {test_file_id}\n")

# Possible endpoint patterns
endpoints = [
    f"https://www.genspark.ai/api/aidrive/download/{test_file_id}",
    f"https://www.genspark.ai/api/aidrive/files/{test_file_id}/download",
    f"https://www.genspark.ai/api/aidrive/files/{test_file_id}",
    f"https://www.genspark.ai/aidrive/api/download/{test_file_id}",
    f"https://www.genspark.ai/aidrive/files/api/download/{test_file_id}",
    f"https://www.genspark.ai/api/files/{test_file_id}/download",
    f"https://www.genspark.ai/api/download?id={test_file_id}",
    f"https://www.genspark.ai/api/aidrive/download?fileId={test_file_id}",
]

for url in endpoints:
    try:
        print(f"Testing: {url}")
        response = session.get(url, timeout=5, allow_redirects=False)
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            print(f"  Content-Type: {content_type}")
            
            if 'json' in content_type.lower():
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=2)[:200]}")
                
                # Look for download URL in response
                if 'url' in data:
                    print(f"  ✅ FOUND DOWNLOAD URL!")
                    print(f"  URL: {data['url'][:100]}...")
                elif 'download_url' in data:
                    print(f"  ✅ FOUND DOWNLOAD URL!")
                    print(f"  URL: {data['download_url'][:100]}...")
            else:
                print(f"  Response length: {len(response.content)} bytes")
                if len(response.content) < 1000:
                    print(f"  Content (first 200 chars): {response.text[:200]}")
                    
        elif response.status_code == 302 or response.status_code == 301:
            location = response.headers.get('Location', '')
            print(f"  Redirect to: {location[:100]}")
            if 'blob.core.windows.net' in location:
                print(f"  ✅ DIRECT AZURE BLOB REDIRECT!")
                
        elif response.status_code == 404:
            print(f"  ❌ Not Found")
        elif response.status_code == 403:
            print(f"  ⚠️  Forbidden")
        else:
            print(f"  Response: {response.text[:200]}")
        
        print()
        
    except Exception as e:
        print(f"  ❌ Error: {e}\n")

print("=" * 70)
