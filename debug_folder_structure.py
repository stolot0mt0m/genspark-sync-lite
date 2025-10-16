#!/usr/bin/env python3
"""
Debug Folder Structure
Shows what the API returns for folders and files
"""

import sys
import json
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from genspark_api import GenSparkAPIClient

def main():
    api_client = GenSparkAPIClient()
    
    # Load cookies
    if not api_client.load_cookies_from_chrome():
        print("❌ Failed to load cookies!")
        return
    
    # List all items
    items = api_client.list_files()
    if not items:
        print("❌ No items returned!")
        return
    
    print(f"\n📊 Total items: {len(items)}")
    print("=" * 80)
    
    # Separate folders and files
    folders = [item for item in items if item.get('type') == 'directory']
    files = [item for item in items if item.get('type') == 'file']
    
    print(f"\n📁 FOLDERS ({len(folders)}):")
    print("-" * 80)
    for folder in folders:
        print(f"\nFolder: {folder.get('name')}")
        print(f"  ID: {folder.get('id')}")
        print(f"  Path: {folder.get('path')}")
        print(f"  Type: {folder.get('type')}")
    
    print(f"\n📄 FILES ({len(files)}):")
    print("-" * 80)
    for file in files:
        path = file.get('path', '')
        print(f"\nFile: {file.get('name')}")
        print(f"  Path: {path}")
        print(f"  ID: {file.get('id')}")
        # Check if file is in a folder
        if '/' in path.strip('/') and path.count('/') > 1:
            print(f"  ⚠️  IN FOLDER!")
    
    print("\n" + "=" * 80)
    print("💡 QUESTION: Do we see files inside folders?")
    files_in_folders = [f for f in files if '/' in f.get('path', '').strip('/') and f.get('path', '').count('/') > 1]
    print(f"   Files in folders: {len(files_in_folders)}")
    print(f"   Root files only: {len(files) - len(files_in_folders)}")
    
    if len(files_in_folders) == 0:
        print("\n❌ API does NOT return files inside folders!")
        print("💡 We need to make separate API calls for each folder")
    else:
        print("\n✅ API returns files with full paths!")
        print("💡 We can use the paths directly")

if __name__ == "__main__":
    main()
