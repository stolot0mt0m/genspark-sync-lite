#!/usr/bin/env python3
"""
GenSpark API Endpoint Discovery Tool
Automatically finds the correct API endpoints by testing various patterns
"""

import requests
import browser_cookie3
import logging
from typing import Optional, List, Dict
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('APIDiscovery')


class EndpointDiscovery:
    """Discover working API endpoints for GenSpark AI Drive"""
    
    BASE_URL = "https://www.genspark.ai"
    
    # Possible API endpoint patterns to test
    ENDPOINT_PATTERNS = [
        "/api/files",
        "/api/v1/files",
        "/api/aidrive/files",
        "/aidrive/api/files",
        "/api/drive/files",
        "/api/storage/files",
        "/api/side/files",
        "/api/file/list",
        "/files/api/list",
        "/api/aidrive/list",
        "/aidrive/files/api/list",
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self._setup_session()
        
    def _setup_session(self):
        """Setup session with cookies and headers"""
        # Load cookies from Chrome
        try:
            cookies = browser_cookie3.chrome(domain_name='genspark.ai')
            for cookie in cookies:
                self.session.cookies.set_cookie(cookie)
            logger.info(f"✅ Loaded {len(self.session.cookies)} cookies")
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            
        # Add browser headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'{self.BASE_URL}/aidrive/files/',
            'Origin': self.BASE_URL,
        })
    
    def test_endpoint(self, endpoint: str, method: str = 'GET') -> Optional[Dict]:
        """Test a single endpoint"""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            logger.info(f"Testing: {method} {url}")
            
            if method == 'GET':
                response = self.session.get(url, timeout=5)
            else:
                response = self.session.post(url, timeout=5)
            
            logger.info(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"  ✅ SUCCESS! Found working endpoint!")
                try:
                    data = response.json()
                    logger.info(f"  Response type: {type(data)}")
                    if isinstance(data, dict):
                        logger.info(f"  Keys: {list(data.keys())[:10]}")
                    return {
                        'endpoint': endpoint,
                        'method': method,
                        'status': 200,
                        'data': data
                    }
                except:
                    logger.info(f"  Response is not JSON")
                    return {
                        'endpoint': endpoint,
                        'method': method,
                        'status': 200,
                        'data': response.text[:200]
                    }
            elif response.status_code == 404:
                logger.info(f"  ❌ 404 Not Found")
            elif response.status_code == 403:
                logger.info(f"  ⚠️  403 Forbidden (endpoint exists but no access)")
                return {
                    'endpoint': endpoint,
                    'method': method,
                    'status': 403,
                    'note': 'Endpoint exists but requires authentication'
                }
            elif response.status_code == 401:
                logger.info(f"  ⚠️  401 Unauthorized (endpoint exists)")
                return {
                    'endpoint': endpoint,
                    'method': method,
                    'status': 401,
                    'note': 'Endpoint exists but needs authentication'
                }
            else:
                logger.info(f"  ⚠️  Unexpected: {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.info(f"  ⏱️  Timeout")
        except Exception as e:
            logger.info(f"  ❌ Error: {e}")
        
        return None
    
    def discover_all(self) -> List[Dict]:
        """Try all endpoint patterns"""
        logger.info("=" * 70)
        logger.info("🔍 GenSpark API Endpoint Discovery")
        logger.info("=" * 70)
        logger.info(f"\nTesting {len(self.ENDPOINT_PATTERNS)} endpoint patterns...\n")
        
        working_endpoints = []
        
        for pattern in self.ENDPOINT_PATTERNS:
            # Test GET
            result = self.test_endpoint(pattern, 'GET')
            if result:
                working_endpoints.append(result)
            
            # Test POST
            result = self.test_endpoint(pattern, 'POST')
            if result:
                working_endpoints.append(result)
        
        return working_endpoints
    
    def discover_with_params(self) -> Optional[Dict]:
        """Try common parameter combinations"""
        logger.info("\n" + "=" * 70)
        logger.info("🔍 Testing with common parameters...")
        logger.info("=" * 70 + "\n")
        
        base_endpoints = [
            "/api/files",
            "/api/aidrive/files",
            "/aidrive/api/files",
        ]
        
        param_sets = [
            {},
            {'type': 'all'},
            {'filter': 'all'},
            {'sort': 'modified'},
            {'page': 1, 'limit': 10},
        ]
        
        for endpoint in base_endpoints:
            for params in param_sets:
                url = f"{self.BASE_URL}{endpoint}"
                try:
                    logger.info(f"Testing: GET {url} with params={params}")
                    response = self.session.get(url, params=params, timeout=5)
                    logger.info(f"  Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        logger.info(f"  ✅ SUCCESS!")
                        data = response.json()
                        return {
                            'endpoint': endpoint,
                            'params': params,
                            'data': data
                        }
                except Exception as e:
                    logger.info(f"  ❌ Error: {e}")
        
        return None


def main():
    """Main discovery routine"""
    discovery = EndpointDiscovery()
    
    # Discover basic endpoints
    working = discovery.discover_all()
    
    # Try with parameters
    param_result = discovery.discover_with_params()
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 Discovery Summary")
    logger.info("=" * 70)
    
    if working:
        logger.info(f"\n✅ Found {len(working)} working endpoints:\n")
        for result in working:
            logger.info(f"  {result['method']} {result['endpoint']}")
            logger.info(f"    Status: {result['status']}")
            if 'note' in result:
                logger.info(f"    Note: {result['note']}")
            logger.info("")
    else:
        logger.warning("\n❌ No working endpoints found!")
        logger.warning("\n🔧 Next steps:")
        logger.warning("1. Open Chrome DevTools (Cmd+Option+I)")
        logger.warning("2. Go to Network tab")
        logger.warning("3. Navigate to: https://www.genspark.ai/aidrive/files/")
        logger.warning("4. Filter by 'Fetch/XHR'")
        logger.warning("5. Look for API calls when page loads")
        logger.warning("6. Copy the exact endpoint URL")
    
    if param_result:
        logger.info("✅ Found endpoint with working parameters:")
        logger.info(f"  Endpoint: {param_result['endpoint']}")
        logger.info(f"  Params: {param_result['params']}")
    
    logger.info("=" * 70 + "\n")


if __name__ == "__main__":
    main()
