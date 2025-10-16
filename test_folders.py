#!/usr/bin/env python3
"""
Find folder information from API
"""

import sys
sys.path.insert(0, 'src')

from genspark_api import GenSparkAPIClient
import json

client = GenSparkAPIClient()

if client.load_cookies_from_chrome():
    # Get all items (files AND folders)
    response = client.session.get(
        "https://www.genspark.ai/api/aidrive/recent/files",
        params={"limit": 100},
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        
        print(f"📦 Found {len(items)} items\n")
        print("=" * 100)
        
        # Separate files and folders
        folders = [item for item in items if item.get('type') == 'folder']
        files = [item for item in items if item.get('type') == 'file']
        
        print(f"\n📁 FOLDERS ({len(folders)}):")
        print("-" * 100)
        for folder in folders:
            folder_id = folder.get('id', 'unknown')
            folder_name = folder.get('name', 'unknown')
            parent_id = folder.get('parent_id', 'unknown')
            
            print(f"  {folder_name:40s} | ID: {folder_id} | Parent: {parent_id}")
        
        print(f"\n📄 FILES ({len(files)}) - First 10:")
        print("-" * 100)
        for file in files[:10]:
            file_name = file.get('name', 'unknown')
            parent_id = file.get('parent_id', 'unknown')
            is_root = ':root' in parent_id
            
            print(f"  {'✅' if is_root else '❌'} {file_name:40s} | Parent: {parent_id}")
        
        # Build parent_id → folder_name mapping
        print("\n🗺️  Parent ID → Folder Name Mapping:")
        print("-" * 100)
        folder_map = {}
        for folder in folders:
            folder_id = folder.get('id')
            folder_name = folder.get('name')
            if folder_id:
                folder_map[folder_id] = folder_name
                print(f"  {folder_id} → {folder_name}")
        
        # Show example download URLs
        print("\n🌐 Example Download URLs with Folder Names:")
        print("-" * 100)
        for file in files[:5]:
            file_name = file.get('name')
            parent_id = file.get('parent_id', '')
            
            if ':root' in parent_id:
                url = f"https://www.genspark.ai/api/aidrive/download/files/{file_name}"
                print(f"\n  ✅ ROOT: {file_name}")
                print(f"     {url}")
            else:
                folder_name = folder_map.get(parent_id, 'UNKNOWN_FOLDER')
                url = f"https://www.genspark.ai/api/aidrive/download/files/{folder_name}/{file_name}"
                print(f"\n  📁 FOLDER: {folder_name}/{file_name}")
                print(f"     {url}")
        
        print("\n" + "=" * 100)
    else:
        print(f"❌ API returned {response.status_code}")
        print(response.text[:500])
else:
    print("❌ Failed to load cookies")
