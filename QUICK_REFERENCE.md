# ⚡ GenSpark Sync Lite - Quick Reference

**One-Page Cheat Sheet für Robert**

---

## 🚀 Quick Start (3 Commands)

```bash
# 1. Navigate to project
cd ~/genspark-sync-lite

# 2. Run cookie diagnostics
source venv/bin/activate && python3 debug_cookies.py

# 3. If successful → Start app
./launch.sh
```

---

## 📂 Important Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `launch.sh` | Start the app | Every time you want to run sync |
| `debug_cookies.py` | Fix 403 error | When authentication fails |
| `install.sh` | Setup environment | First time only |
| `NEXT_STEPS.md` | Action plan | Read after cookie fix |
| `COOKIE_FIX.md` | Detailed troubleshooting | If debug script fails |
| `STATUS.md` | Project overview | Understand current state |

---

## 🔧 Common Tasks

### Start Sync App
```bash
cd ~/genspark-sync-lite && ./launch.sh
```

### Stop Sync App
```bash
# Press Ctrl+C in terminal
```

### Test Authentication
```bash
cd ~/genspark-sync-lite
source venv/bin/activate
python3 debug_cookies.py
```

### Fix 403 Error
```bash
# 1. Open Chrome → https://www.genspark.ai/aidrive/files/
# 2. Login fresh
# 3. Close Chrome with Cmd+Q (not just window close!)
# 4. Run debug_cookies.py again
```

### Check Sync Status
```bash
# Look at terminal output where app is running
# Or check: ~/.genspark_sync_state.json
cat ~/.genspark_sync_state.json | python3 -m json.tool
```

### View Logs
```bash
# Logs are printed to terminal in real-time
# Or check macOS Console.app for system logs
```

---

## 📊 What to Check

### ✅ Success Indicators
```
✅ SUCCESS! API call worked!
   Found X files in AI Drive

🔄 Starting GenSpark Sync Lite...
   Sync Folder: /Users/robert/GenSpark AI Drive

📥 Uploaded: test.txt
📤 Downloaded: remote_file.pdf
✅ Sync cycle completed
```

### ❌ Error Indicators
```
❌ 403 FORBIDDEN - Authentication failed!
   → Run fresh Chrome login + debug_cookies.py

❌ Connection refused
   → Check internet connection

❌ File conflict detected
   → App will ask which version to keep
```

---

## 🎯 Key Locations

### Sync Folder (where files sync)
```bash
~/GenSpark AI Drive/
```

### App Installation
```bash
~/genspark-sync-lite/
```

### State File (tracking)
```bash
~/.genspark_sync_state.json
```

### Virtual Environment
```bash
~/genspark-sync-lite/venv/
```

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| 403 Forbidden | Fresh Chrome login (Cmd+Q) → `debug_cookies.py` |
| No cookies found | Login to genspark.ai in Chrome first |
| Permission denied | `chmod +x launch.sh install.sh debug_cookies.py` |
| Module not found | `source venv/bin/activate` |
| Port already in use | Not applicable (no server needed) |
| File not syncing | Check if file is in exclusion list (.DS_Store, etc.) |

---

## 📱 Status Emoji Guide

| Emoji | Meaning | Action |
|-------|---------|--------|
| 🟢 | Working perfectly | Continue using |
| 🟡 | Issue detected | Check documentation |
| 🔴 | Critical error | Stop and fix |
| ⏸️ | Paused/Waiting | User action needed |
| 🔄 | Syncing | Normal operation |
| ✅ | Success | All good |
| ❌ | Failure | Investigate |

---

## 🎬 Next Actions (Priority Order)

1. **HIGH:** Run `debug_cookies.py` on your Mac
2. **HIGH:** Report if you see "✅ SUCCESS!" or "❌ 403"
3. **MEDIUM:** If success → Test file upload/download
4. **LOW:** If stable → Request LaunchAgent setup

---

## 📞 What to Send Me

### If Working ✅
```
"✅ Works! API call successful. Found 42 files."
```

### If 403 Error ❌
```
Complete output of: python3 debug_cookies.py
Plus:
- macOS version: sw_vers
- Python version: python3 --version
- Chrome version: chrome://version/ (first line)
```

### If Different Error ⚠️
```
Complete error message + stack trace
```

---

## 💡 Pro Tips

1. **Always close Chrome with Cmd+Q** (not just close window)
2. **Keep terminal open** while app runs (it's not a background service yet)
3. **Check ~/GenSpark AI Drive/** for synced files
4. **Don't edit .genspark_sync_state.json manually** (app manages it)
5. **For conflicts, choose carefully** (no undo yet)

---

## 🔗 Quick Links

**Web Interface:**  
https://www.genspark.ai/aidrive/files/

**API Endpoint:**  
https://www.genspark.ai/api/side/wget_upload_url/

**Documentation Files:**
- [README.md](README.md) - Full documentation
- [QUICKSTART.md](QUICKSTART.md) - Setup guide
- [NEXT_STEPS.md](NEXT_STEPS.md) - Action plan
- [COOKIE_FIX.md](COOKIE_FIX.md) - 403 troubleshooting
- [STATUS.md](STATUS.md) - Project status

---

## ⏱️ Time Estimates

| Task | Time |
|------|------|
| Fix 403 error | 5 min |
| Test first upload | 2 min |
| Test first download | 1 min |
| Stability test | 30 min |
| LaunchAgent setup | 10 min |
| **Total to Production** | **~1 hour** |

---

## 🎓 Technical Stack (for reference)

**Languages:** Python 3.11+  
**Libraries:** requests, watchdog, browser-cookie3, pydantic  
**Platform:** macOS 10.14+  
**Browser:** Chrome (for cookie extraction)  
**API:** GenSpark AI Drive REST API  
**Storage:** Azure Blob (backend)

---

**Last Updated:** 2025-10-16 18:55  
**Status:** 🟡 Ready for user testing

---

**Pro Tip:** Bookmark this file in your browser for quick access! 📌
