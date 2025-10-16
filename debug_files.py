#!/usr/bin/env python3
"""
Debug script to show all files with parent_id and path info
"""

import sys
sys.path.insert(0, 'src')

from genspark_api import GenSparkAPIClient
import json

client = GenSparkAPIClient()

if client.load_cookies_from_chrome():
    files = client.list_files(limit=100)
    
    if files:
        print(f"\n📁 Found {len(files)} files:\n")
        print("=" * 120)
        
        # Group by parent_id
        by_parent = {}
        for f in files:
            parent = f.get('parent_id', 'unknown')
            if parent not in by_parent:
                by_parent[parent] = []
            by_parent[parent].append(f)
        
        for parent_id, file_list in by_parent.items():
            is_root = ':root' in parent_id
            print(f"\n{'📂 ROOT' if is_root else '📁 Folder'}: {parent_id}")
            print("-" * 120)
            
            for f in file_list[:10]:  # Show first 10 per folder
                name = f['name']
                path = f.get('path', '')
                full_path = f"{path}/{name}" if path else name
                
                print(f"  {'✅' if is_root else '❌'} {name:50s} | path: {path:30s} | parent: {parent_id[:20]}")
            
            if len(file_list) > 10:
                print(f"  ... and {len(file_list) - 10} more files")
        
        print("\n" + "=" * 120)
        print("\n🔍 Analysis:")
        print(f"  Total files: {len(files)}")
        print(f"  Root files (work): {sum(1 for f in files if ':root' in f.get('parent_id', ''))}")
        print(f"  Folder files (fail): {sum(1 for f in files if ':root' not in f.get('parent_id', ''))}")
        
        # Sample download URLs
        print("\n🌐 Sample Download URLs:")
        for f in files[:5]:
            name = f['name']
            path = f.get('path', '')
            full_path = f"{path}/{name}" if path else name
            
            url1 = f"https://www.genspark.ai/api/aidrive/download/files/{name}"
            url2 = f"https://www.genspark.ai/api/aidrive/download/files/{full_path}"
            
            print(f"\n  File: {name}")
            print(f"    Path: '{path}'")
            print(f"    URL1 (name only): {url1}")
            if path:
                print(f"    URL2 (with path):  {url2}")
    else:
        print("❌ No files found")
else:
    print("❌ Failed to load cookies")
