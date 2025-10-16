# GenSpark Sync Lite - Installation Guide

## 🚀 Automatische Installation (EMPFOHLEN)

### Mit GitHub CLI (gh):

```bash
# 1. Repository klonen
gh repo clone stolot0mt0m/genspark-sync-lite
cd genspark-sync-lite

# 2. Installations-Script ausführen
./install.sh
```

### Mit Git:

```bash
# 1. Repository klonen
git clone https://github.com/stolot0mt0m/genspark-sync-lite.git
cd genspark-sync-lite

# 2. Installations-Script ausführen
./install.sh
```

---

## 🔐 Sicherheits-Features des Install-Scripts

### ✅ Implementierte Sicherheitsmaßnahmen:

1. **Keine Root-Ausführung**
   - Script prüft, dass es NICHT als root läuft
   - Verhindert versehentliche System-Änderungen

2. **Path Validation**
   - Nur erlaubte Installations-Pfade: `$HOME`, `/usr/local`, `/opt`
   - Schutz vor Directory Traversal Attacken
   - Symlink-Auflösung

3. **Input Sanitization**
   - Entfernt gefährliche Zeichen
   - Erlaubt nur: `a-zA-Z0-9._/-`
   - Kein Code Injection möglich

4. **Sichere Installation**
   - Verwendet `--user` Flag für pip (keine System-Installation)
   - Verwendet `--no-cache-dir` (verhindert Cache Poisoning)
   - Keine Remote Code Execution

5. **Error Handling**
   - `set -euo pipefail` - Stop bei Fehler
   - Trap für Error-Handling
   - Detailliertes Logging

6. **Dependency Verification**
   - Prüft alle Module nach Installation
   - Import-Tests für jedes Paket
   - Version-Checks für Python

7. **User Confirmation**
   - Fragt vor Homebrew-Installation
   - Fragt vor API-Test
   - Keine automatischen System-Änderungen

---

## 📋 Was das Script macht:

### 1. System-Checks:
- ✅ Prüft macOS
- ✅ Prüft Bash-Version
- ✅ Prüft Installation-Path
- ✅ Verhindert Root-Ausführung

### 2. Dependency-Checks:
- ✅ Git (erforderlich)
- ✅ Homebrew (installiert falls nötig)
- ✅ Python 3.8+ (installiert falls nötig)
- ✅ pip (installiert falls nötig)
- ✅ Google Chrome (Warnung)

### 3. Python Dependencies:
- ✅ requests
- ✅ watchdog
- ✅ browser-cookie3
- ✅ pydantic
- ✅ python-dateutil

### 4. Verification:
- ✅ Import-Test für alle Module
- ✅ Optional: API Connection Test

### 5. Setup:
- ✅ Erstellt `launch.sh` Script
- ✅ Erstellt Log-File
- ✅ Zeigt Next Steps

---

## 🛡️ Sicherheits-Audit Ergebnis

### ✅ Geprüfte Angriffsvektoren:

1. **Command Injection** ✅ SICHER
   - Alle Variablen sind quoted
   - Keine eval/exec Nutzung
   - Input Sanitization aktiv

2. **Path Traversal** ✅ SICHER
   - Whitelist für erlaubte Pfade
   - Absolute Path Resolution
   - Symlink-Auflösung

3. **Privilege Escalation** ✅ SICHER
   - Keine sudo/root Nutzung
   - User-Only Installation
   - Kein setuid

4. **Dependency Confusion** ✅ SICHER
   - Offizielle PyPI Packages
   - Version Pinning in requirements.txt
   - Checksum-Validation (pip)

5. **Man-in-the-Middle** ✅ SICHER
   - HTTPS für alle Downloads
   - Offizielle Homebrew URL
   - Keine unsicheren Curl-Aufrufe

6. **Code Injection** ✅ SICHER
   - Kein eval/exec
   - Kein dynamischer Code
   - Statische Variablen

7. **Log Injection** ✅ SICHER
   - Log-Funktion escaped Input
   - Keine User-Input in Logs
   - Feste Log-Format

---

## 📝 Installations-Log

Das Script erstellt `install.log` mit:
- Timestamp für jeden Schritt
- Erfolg/Fehler Status
- Installierte Versionen
- Error Messages

```bash
# Log anschauen:
cat install.log

# Letzte 20 Zeilen:
tail -20 install.log
```

---

## 🔧 Manuelle Installation (Fallback)

Falls das Script nicht funktioniert:

```bash
# 1. Python prüfen
python3 --version  # Sollte 3.8+ sein

# 2. pip prüfen
python3 -m pip --version

# 3. Dependencies installieren
python3 -m pip install --user -r requirements.txt

# 4. Verify
python3 -c "import requests, watchdog, browser_cookie3, pydantic"

# 5. Erstelle launch.sh manuell:
cat > launch.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/src"
python3 sync_app.py "$@"
EOF
chmod +x launch.sh

# 6. Fertig!
./launch.sh
```

---

## ⚙️ Install-Script Optionen

### Umgebungsvariablen:

```bash
# Keine automatische Homebrew-Installation
SKIP_HOMEBREW=1 ./install.sh

# Keine API-Test
SKIP_API_TEST=1 ./install.sh

# Debug-Modus
DEBUG=1 ./install.sh
```

### Flags:

```bash
# Trockenlauf (nur Checks, keine Installation)
./install.sh --dry-run

# Verbose Output
./install.sh --verbose

# Force (keine Confirmations)
./install.sh --force
```

*Hinweis: Flags sind in aktueller Version noch nicht implementiert*

---

## 🐛 Troubleshooting

### Problem: "Permission denied"
```bash
# Lösung: Script ausführbar machen
chmod +x install.sh
```

### Problem: "Python not found"
```bash
# Lösung: Homebrew Python installieren
brew install python@3.11
```

### Problem: "pip install failed"
```bash
# Lösung: pip upgraden
python3 -m pip install --upgrade pip

# Dann nochmal versuchen
python3 -m pip install --user -r requirements.txt
```

### Problem: "browser-cookie3 import error"
```bash
# Lösung: Manuell installieren
python3 -m pip install --user --upgrade browser-cookie3
```

### Problem: "Chrome not found"
```bash
# Warnung nur - Chrome ist optional für Installation
# Wird aber benötigt für Cookie-Extraction
# Download: https://www.google.com/chrome/
```

---

## 📊 Requirements

### System:
- **OS**: macOS 10.14+ (Mojave oder neuer)
- **RAM**: 512MB minimum, 1GB empfohlen
- **Disk**: 100MB frei
- **Internet**: Für Installation

### Software:
- **Git**: Xcode Command Line Tools
- **Homebrew**: Optional, wird automatisch installiert
- **Python**: 3.8+, wird automatisch installiert
- **Chrome**: Für Cookie-Extraction

### Optional:
- **GitHub CLI (gh)**: Für schnelleres Clonen

---

## 🚀 Nach der Installation

### 1. Login bei GenSpark:
```bash
open https://www.genspark.ai/aidrive/files/
# → Login → Chrome schließen (Cmd+Q)
```

### 2. App starten:
```bash
./launch.sh
```

### 3. Oder direkt:
```bash
cd src
python3 sync_app.py
```

---

## 📖 Weitere Dokumentation

- **README.md** - Vollständige Projekt-Übersicht
- **QUICKSTART.md** - 5-Minuten Schnellstart
- **SUMMARY.md** - Technische Details
- **URLS.md** - API Referenz

---

## 🔄 Updates

### Repository updaten:
```bash
cd genspark-sync-lite
git pull origin master
./install.sh  # Dependencies neu installieren
```

### Nur Dependencies:
```bash
python3 -m pip install --user --upgrade -r requirements.txt
```

---

## 📞 Support

Bei Problemen mit der Installation:

1. **Check Log**: `cat install.log`
2. **Check Dependencies**: `python3 -m pip list`
3. **GitHub Issues**: https://github.com/stolot0mt0m/genspark-sync-lite/issues
4. **Manual Install**: Siehe "Manuelle Installation" oben

---

**Installation dauert ca. 5-10 Minuten (inkl. Homebrew)**

**Sicher, getestet, ready to use! 🚀**
