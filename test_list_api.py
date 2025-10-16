#!/usr/bin/env python3
"""
Test the /aidrive/files/api/list endpoint to see what it returns
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

print("=" * 70)
print("Testing: GET /aidrive/files/api/list")
print("=" * 70)

url = "https://www.genspark.ai/aidrive/files/api/list"

response = session.get(url, timeout=10)

print(f"\nStatus: {response.status_code}")
print(f"\nContent-Type: {response.headers.get('content-type')}")
print(f"\nResponse Length: {len(response.text)} bytes")
print(f"\nFirst 500 characters:")
print("-" * 70)
print(response.text[:500])
print("-" * 70)

# Try to find JSON patterns
if '{' in response.text or '[' in response.text:
    print("\n🔍 Looking for JSON data...")
    # Try to extract JSON from HTML
    import re
    json_matches = re.findall(r'(\{.*?\}|\[.*?\])', response.text, re.DOTALL)
    if json_matches:
        print(f"Found {len(json_matches)} potential JSON objects")
        for i, match in enumerate(json_matches[:3]):
            if len(match) > 100:
                print(f"\nJSON #{i+1} (first 200 chars):")
                print(match[:200])

# Check if it's a Next.js page
if '__NEXT_DATA__' in response.text:
    print("\n✅ This is a Next.js page!")
    print("Looking for __NEXT_DATA__...")
    
    # Extract __NEXT_DATA__
    import re
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text, re.DOTALL)
    if match:
        try:
            next_data = json.loads(match.group(1))
            print("\n✅ Successfully parsed __NEXT_DATA__!")
            print(f"\nKeys: {list(next_data.keys())}")
            
            # Look for file data in props
            if 'props' in next_data:
                print(f"\nProps keys: {list(next_data['props'].keys())}")
                
                if 'pageProps' in next_data['props']:
                    page_props = next_data['props']['pageProps']
                    print(f"\nPageProps keys: {list(page_props.keys())}")
                    
                    # Save to file for inspection
                    with open('next_data.json', 'w') as f:
                        json.dump(next_data, f, indent=2)
                    print("\n✅ Saved full data to: next_data.json")
                    
        except Exception as e:
            print(f"\n❌ Failed to parse __NEXT_DATA__: {e}")

print("\n" + "=" * 70)
