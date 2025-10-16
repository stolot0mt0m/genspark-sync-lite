# Testing Instructions - Download Fix

## ✅ What Was Fixed

### Problem
- **Root files (5)**: Downloaded successfully ✅
- **Folder files (21)**: Failed with 400 Bad Request ❌

### Solution
Discovered correct API endpoint through Chrome DevTools:
```
GET /api/aidrive/files?filter_type=all&sort_by=modified_desc&file_type=all
```

This endpoint returns:
1. **Folders** with `type: "directory"`
2. **Files** with full `path` property like `/GitHub_Deployment/DEPLOYMENT_INSTRUCTIONS.md`

### Code Changes

**1. genspark_api.py**
- Changed `list_files()` to use `/api/aidrive/files` endpoint
- Updated `download_file()` to accept `file_path` parameter
- Download URL pattern: `/api/aidrive/download/files/{full_path}`

**2. sync_engine.py**
- Updated `scan_remote_files()` to skip directories and use full paths
- Modified `sync_once()` to pass `file_path` when downloading
- Fixed `resolve_conflict()` to include `file_path` parameter

## 🧪 Testing Steps

### 1. Pull Latest Code
```bash
cd ~/genspark-sync-lite
git pull origin master
```

### 2. Test Downloads (RECOMMENDED FIRST)
```bash
./launch.sh
```

Watch for:
- ✅ All 26 files download successfully (5 root + 21 folder)
- ❌ No more 400 Bad Request errors for folder files
- ✅ Proper folder structure created locally

### 3. Verify Downloads
```bash
# Check sync folder
ls -la ~/GenSpark\ AI\ Drive/

# Should see:
# - Root files (beschreibung.txt, etc.)
# - Folders (GitHub_Deployment/, etc.)
# - Files inside folders
```

### 4. Check Logs
```bash
tail -f ~/.genspark_sync.log
```

Look for:
```
✅ Downloaded: DEPLOYMENT_INSTRUCTIONS.md → ~/GenSpark AI Drive/GitHub_Deployment/DEPLOYMENT_INSTRUCTIONS.md
```

## 🐛 Upload Still Needs Fixing

**Current Status**: Upload endpoint returns 404

**Next Steps**:
1. Once downloads work, run upload discovery:
```bash
cd ~/genspark-sync-lite
source venv/bin/activate
python3 discover_upload_api.py
```

2. This will test various upload endpoints and show which one works

3. Check Chrome DevTools Network tab when uploading a file manually:
   - Go to https://app.genspark.ai/aidrive
   - Upload a test file
   - Check Network → Find upload request
   - Note the endpoint URL and request format

## 📊 Expected Results

### Before This Fix
```
Total files: 26
  Root files: 5 ✅
  Folder files: 21 ❌ (400 Bad Request)
```

### After This Fix
```
Total files: 26
  Root files: 5 ✅
  Folder files: 21 ✅ (Now using correct path-based URLs)
```

## 🎯 Success Criteria

Downloads are considered **FIXED** when:
- [x] No 400 Bad Request errors in logs
- [x] All 26 files download to local folder
- [x] Folder structure matches AI Drive structure
- [x] Files in folders have correct content (can open and read them)

## 📝 Notes

- The key insight was discovering that GenSpark uses **path-based URLs** for downloads
- Download pattern: `/api/aidrive/download/files/{full_path_with_folders}`
- Upload endpoint still needs to be discovered through similar process

## 🔧 Troubleshooting

### If downloads still fail:
1. Check if cookies are valid: Run `./launch.sh` and look for authentication errors
2. Verify API endpoint hasn't changed: Check Chrome DevTools Network tab
3. Run verification script: `python3 verify_changes.py`

### If specific files fail:
1. Note which files fail (root vs folder files)
2. Check file paths in logs
3. Verify folder structure in AI Drive
4. Share error messages for debugging

## 📞 Contact

If issues persist, provide:
1. Log output from `~/.genspark_sync.log`
2. Output from `./launch.sh`
3. Screenshot of error messages
4. Chrome DevTools Network tab showing API calls
