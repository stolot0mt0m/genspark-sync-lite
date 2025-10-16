# GenSpark Sync Lite - Quick Start

## 🚀 In 5 Minuten startklar!

### 1️⃣ Chrome vorbereiten
```bash
# Öffne Chrome und gehe zu:
# https://www.genspark.ai/aidrive/files/
# Logge dich ein
# Dann: Chrome KOMPLETT schließen (Cmd+Q)
```

### 2️⃣ Dependencies installieren
```bash
cd /home/user/webapp/genspark-sync-lite
pip3 install -r requirements.txt
```

### 3️⃣ API testen
```bash
./test_api.sh
```

**Erwartete Ausgabe:**
```
✅ API connection successful!
📁 Found X items:
  - beschreibung.txt (file, 664 bytes)
  - ...
```

### 4️⃣ App starten
```bash
cd src
python3 sync_app.py
```

**Interaktive Eingaben:**
```
Sync folder: /Users/robert/GenSpark AI Drive
Use this folder? [Y/n]: Y

Default poll interval: 30 seconds
Change poll interval? [y/N]: N
```

### 5️⃣ Testen!

**Terminal 1: App läuft**
```bash
python3 sync_app.py
# Logs erscheinen hier
```

**Terminal 2: Dateien erstellen**
```bash
cd ~/GenSpark\ AI\ Drive

# Test 1: Neue Datei
echo "Hello World" > test.txt
# → Sollte in Terminal 1 Upload-Log sehen

# Test 2: Datei ändern
echo "Updated" >> test.txt
# → Sollte Upload-Log sehen

# Test 3: Datei löschen
rm test.txt
# → Sollte Delete-Log sehen
```

---

## 📊 Was passiert?

### Lokale Änderungen → Cloud
```
1. Du erstellst/änderst Datei
2. Watchdog erkennt sofort
3. Upload zu AI Drive
4. Fertig! (< 1 Sekunde)
```

### Cloud Änderungen → Lokal
```
1. Jemand ändert Datei in AI Drive
2. Poller checkt alle 30s
3. Download zur lokalen Folder
4. Fertig! (max. 30s Delay)
```

---

## ⚠️ Troubleshooting

### "Failed to load cookies from Chrome"

**Ursache:** Chrome läuft noch oder Cookies nicht lesbar

**Lösung:**
```bash
# 1. Chrome komplett beenden
pkill -9 "Google Chrome"

# 2. Neu einloggen bei genspark.ai
open https://www.genspark.ai

# 3. Chrome schließen und App neu starten
```

### "API connection failed"

**Ursache:** Session abgelaufen oder Internet-Problem

**Lösung:**
```bash
# 1. Teste Internet
ping genspark.ai

# 2. Neu einloggen in Chrome
# 3. App neu starten
```

### "Permission denied" beim Cookie-Lesen

**Ursache:** macOS Keychain Zugriff

**Lösung:**
```bash
# Erlaube Zugriff auf Chrome Cookies
# Dialog erscheint beim ersten Start → "Allow"
```

---

## 🎯 Nächste Schritte

1. **Dauerhaft laufen lassen:**
   ```bash
   # In Screen-Session oder Tmux
   screen -S genspark
   python3 src/sync_app.py
   # Ctrl+A, D zum Detachen
   ```

2. **LaunchAgent erstellen** (Auto-Start bei Login)
   ```bash
   # TODO: LaunchAgent Anleitung folgt
   ```

3. **Mehrere Ordner syncen:**
   ```bash
   # Starte mehrere Instanzen mit verschiedenen Folders
   python3 src/sync_app.py  # Folder 1
   # In neuem Terminal:
   python3 src/sync_app.py  # Folder 2
   ```

---

## 📝 Wichtige Dateien

```
~/GenSpark AI Drive/
├── .genspark_sync_state.json    # Sync Status
├── .genspark_sync.log            # Activity Log
└── deine_dateien...              # Deine Dateien
```

**Logs anschauen:**
```bash
tail -f ~/GenSpark\ AI\ Drive/.genspark_sync.log
```

**State anschauen:**
```bash
cat ~/GenSpark\ AI\ Drive/.genspark_sync_state.json | python3 -m json.tool
```

---

## 💡 Pro Tips

### Schnellere Sync bei Aktivität
```bash
# Poll Interval auf 10s setzen
python3 src/sync_app.py
# Bei "Change poll interval?" → yes → 10
```

### Nur bestimmte Dateien syncen
```bash
# Erstelle .genspark_sync_config.json
{
  "exclude_patterns": [
    "*.log",
    "*.tmp",
    "node_modules",
    ".git"
  ]
}
```

### Multiple Accounts
```bash
# Nutze verschiedene Chrome Profiles
# Jedes Profile hat eigene Cookies
```

---

**Viel Erfolg! 🚀**

Bei Fragen: Schau in README.md oder check die Logs!
