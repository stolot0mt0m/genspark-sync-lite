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

# Check if it's a Nuxt.js page
if 'nuxt' in response.text.lower() or '_nuxt' in response.text.lower():
    print("\n✅ This is a Nuxt.js page!")
    
    # Nuxt uses different patterns - look for window.__NUXT__ or embedded data
    import re
    
    # Pattern 1: window.__NUXT__
    match = re.search(r'window\.__NUXT__\s*=\s*({.*?});', response.text, re.DOTALL)
    if match:
        try:
            nuxt_data = json.loads(match.group(1))
            print("\n✅ Successfully parsed window.__NUXT__!")
            print(f"\nKeys: {list(nuxt_data.keys())}")
            
            with open('nuxt_data.json', 'w') as f:
                json.dump(nuxt_data, f, indent=2)
            print("\n✅ Saved full data to: nuxt_data.json")
            
        except Exception as e:
            print(f"\n❌ Failed to parse window.__NUXT__: {e}")
    
    # Pattern 2: Look for JSON in script tags
    script_matches = re.findall(r'<script[^>]*>(.*?)</script>', response.text, re.DOTALL | re.IGNORECASE)
    print(f"\n🔍 Found {len(script_matches)} script tags")
    
    for i, script in enumerate(script_matches):
        if len(script) > 100 and ('{' in script or '[' in script):
            print(f"\nScript #{i+1} (first 300 chars):")
            print(script[:300])
    
    # Pattern 3: Look for data-* attributes with JSON
    data_attrs = re.findall(r'data-[^=]+="({[^"]+}|\[[^\]]+\])"', response.text)
    if data_attrs:
        print(f"\n🔍 Found {len(data_attrs)} data attributes with JSON")

# Alternative: Use Playwright to get rendered data
print("\n" + "=" * 70)
print("💡 ALTERNATIVE APPROACH:")
print("=" * 70)
print("""
Since the page is client-side rendered (Nuxt.js), the file data 
is loaded via JavaScript AFTER the page loads.

We need to:
1. Find the actual API endpoint that JavaScript calls
2. Or use browser automation to wait for data to load

Next step: Open Chrome DevTools and:
1. Go to: https://www.genspark.ai/aidrive/files/
2. Open DevTools (Cmd+Option+I)
3. Go to Network tab
4. Filter by 'Fetch/XHR'
5. Reload the page
6. Look for API calls that return JSON with file list
7. Copy the exact URL of that request
""")

print("\n" + "=" * 70)
