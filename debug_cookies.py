#!/usr/bin/env python3
"""
Cookie Debugging Script for GenSpark AI Drive
Shows exactly which cookies are extracted and validates authentication
"""

import browser_cookie3
import requests
import logging
from datetime import datetime
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CookieDebug')

def format_timestamp(ts):
    """Convert timestamp to readable format"""
    try:
        if ts:
            return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        return 'N/A'
    except:
        return 'Invalid'

def analyze_cookies():
    """Extract and analyze cookies from Chrome"""
    logger.info("=" * 70)
    logger.info("🔍 GenSpark Cookie Diagnostics")
    logger.info("=" * 70)
    
    try:
        # Extract cookies from Chrome
        logger.info("\n📥 Extracting cookies from Chrome...")
        cookies = browser_cookie3.chrome(domain_name='genspark.ai')
        cookie_list = list(cookies)
        
        logger.info(f"✅ Found {len(cookie_list)} cookies for genspark.ai\n")
        
        if len(cookie_list) == 0:
            logger.error("❌ NO COOKIES FOUND!")
            logger.error("\n🔧 Troubleshooting Steps:")
            logger.error("1. Open Chrome and navigate to: https://www.genspark.ai/aidrive/files/")
            logger.error("2. Login if needed")
            logger.error("3. Verify you can see your files")
            logger.error("4. Close Chrome COMPLETELY (Cmd+Q on Mac)")
            logger.error("5. Run this script again")
            return False
        
        # Critical session cookies to look for
        critical_cookies = ['session', 'auth_token', 'csrf_token', '__Secure-next-auth.session-token']
        found_critical = []
        
        logger.info("📋 Cookie Details:")
        logger.info("-" * 70)
        
        for i, cookie in enumerate(cookie_list, 1):
            # Check if critical
            is_critical = cookie.name.lower() in [c.lower() for c in critical_cookies]
            marker = "🔑 CRITICAL" if is_critical else "  "
            
            if is_critical:
                found_critical.append(cookie.name)
            
            # Display cookie info
            logger.info(f"\n{marker} Cookie #{i}: {cookie.name}")
            logger.info(f"     Domain: {cookie.domain}")
            logger.info(f"     Path: {cookie.path}")
            logger.info(f"     Secure: {cookie.secure}")
            logger.info(f"     HttpOnly: {getattr(cookie, 'has_nonstandard_attr', lambda x: False)('HttpOnly')}")
            logger.info(f"     Expires: {format_timestamp(cookie.expires)}")
            
            # Show value (truncated for security)
            value = cookie.value if cookie.value else ""
            if len(value) > 50:
                logger.info(f"     Value: {value[:25]}...{value[-25:]} (length: {len(value)})")
            else:
                logger.info(f"     Value: {value}")
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("📊 Cookie Summary:")
        logger.info(f"   Total Cookies: {len(cookie_list)}")
        logger.info(f"   Critical Cookies Found: {len(found_critical)}")
        
        if found_critical:
            logger.info(f"   🔑 Critical cookies: {', '.join(found_critical)}")
        else:
            logger.warning("   ⚠️  NO CRITICAL SESSION COOKIES FOUND!")
            logger.warning("   This might explain the 403 error!")
        
        # Test API call with these cookies
        logger.info("\n" + "=" * 70)
        logger.info("🌐 Testing API Connection...")
        logger.info("=" * 70)
        
        session = requests.Session()
        for cookie in cookie_list:
            session.cookies.set_cookie(cookie)
        
        # Add common headers that browser sends
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
            'Referer': 'https://www.genspark.ai/aidrive/files/',
            'Origin': 'https://www.genspark.ai',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        session.headers.update(headers)
        
        try:
            url = "https://www.genspark.ai/api/side/wget_upload_url/files"
            params = {
                "filter_type": "all",
                "sort_by": "modified_desc",
                "file_type": "all"
            }
            
            logger.info(f"\n📡 Making test request to: {url}")
            logger.info(f"   Parameters: {params}")
            logger.info(f"   Cookies sent: {len(session.cookies)}")
            
            response = session.get(url, params=params, timeout=10)
            
            logger.info(f"\n📬 Response Status: {response.status_code}")
            logger.info(f"   Response Headers:")
            for key, value in response.headers.items():
                logger.info(f"     {key}: {value}")
            
            if response.status_code == 200:
                logger.info("\n✅ SUCCESS! API call worked!")
                data = response.json()
                items = data.get("items", [])
                logger.info(f"   Found {len(items)} files in AI Drive")
                return True
            elif response.status_code == 403:
                logger.error("\n❌ 403 FORBIDDEN - Authentication failed!")
                logger.info(f"   Response body: {response.text[:500]}")
                logger.error("\n🔧 Troubleshooting:")
                logger.error("1. Your session cookies might be expired or invalid")
                logger.error("2. Open Chrome and login fresh at: https://www.genspark.ai/aidrive/files/")
                logger.error("3. Make sure you can see your files in the web interface")
                logger.error("4. Close Chrome COMPLETELY (Cmd+Q)")
                logger.error("5. Run this script again within 5 minutes")
                return False
            else:
                logger.error(f"\n❌ Unexpected status code: {response.status_code}")
                logger.info(f"   Response: {response.text[:500]}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"\n❌ Request failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during cookie analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("\n🚀 Starting cookie diagnostics...\n")
    
    success = analyze_cookies()
    
    logger.info("\n" + "=" * 70)
    if success:
        logger.info("✅ All checks passed! Your sync app should work now.")
    else:
        logger.error("❌ Issues detected. Follow troubleshooting steps above.")
    logger.info("=" * 70 + "\n")
    
    sys.exit(0 if success else 1)
