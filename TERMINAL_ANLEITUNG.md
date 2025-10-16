# Terminal-Anleitung für Mac

## 🚀 Schnellste Installation (mit GitHub CLI)

### Variante 1: Mit gh (GitHub CLI)

```bash
# Öffne Terminal (Cmd+Space → "Terminal" eingeben)

# Repository klonen
gh repo clone stolot0mt0m/genspark-sync-lite

# In Verzeichnis wechseln
cd genspark-sync-lite

# Installation starten (komplett automatisch!)
./install.sh
```

### Variante 2: Mit git

```bash
# Öffne Terminal (Cmd+Space → "Terminal" eingeben)

# Repository klonen
git clone https://github.com/stolot0mt0m/genspark-sync-lite.git

# In Verzeichnis wechseln
cd genspark-sync-lite

# Installation starten (komplett automatisch!)
./install.sh
```

---

## 📋 Was das Install-Script macht

Das Script läuft **komplett automatisch** und:

### ✅ Prüft automatisch:
- macOS Version
- Python Installation (3.8+)
- pip Installation
- Homebrew Installation
- Git Installation
- Google Chrome (Warnung wenn fehlt)

### ✅ Installiert automatisch (falls nötig):
- Homebrew (mit Nachfrage)
- Python 3.11 (via Homebrew)
- pip (Python Package Manager)
- Alle Python Dependencies:
  - requests
  - watchdog
  - browser-cookie3
  - pydantic
  - python-dateutil

### ✅ Erstellt automatisch:
- Launch-Script (`launch.sh`)
- Log-File (`install.log`)
- Alle notwendigen Konfigurationen

### ✅ Testet automatisch:
- Alle Modul-Imports
- Optional: API-Verbindung

**Du musst NICHTS manuell installieren!** 🎉

---

## 🔐 Sicherheits-Features

### Das Script ist SICHER weil:

1. ✅ **Keine Root-Rechte nötig**
   - Läuft als normaler User
   - Keine System-weiten Änderungen

2. ✅ **Path Validation**
   - Nur erlaubte Installations-Pfade
   - Schutz vor Hacker-Angriffen

3. ✅ **Input Sanitization**
   - Alle Eingaben werden gefiltert
   - Kein Code Injection möglich

4. ✅ **Sichere Downloads**
   - Nur HTTPS Verbindungen
   - Offizielle Quellen (Homebrew, PyPI)

5. ✅ **Error Handling**
   - Stoppt bei Fehlern
   - Detailliertes Logging
   - Rollback möglich

6. ✅ **Geprüft auf:**
   - Command Injection ✅
   - Path Traversal ✅
   - Privilege Escalation ✅
   - Man-in-the-Middle ✅
   - Code Injection ✅

---

## 🎬 Schritt-für-Schritt

### 1. Terminal öffnen
```
Drücke: Cmd+Space
Tippe: Terminal
Enter drücken
```

### 2. Repository klonen
```bash
# Mit GitHub CLI (empfohlen):
gh repo clone stolot0mt0m/genspark-sync-lite

# ODER mit git:
git clone https://github.com/stolot0mt0m/genspark-sync-lite.git
```

### 3. In Verzeichnis wechseln
```bash
cd genspark-sync-lite
```

### 4. Installation starten
```bash
./install.sh
```

**Das war's!** Das Script macht jetzt alles automatisch! ⏱️ **Dauer: 5-10 Minuten**

### 5. Während der Installation

Du wirst gefragt:

```
Install Homebrew? [y/N]:
```
→ Tippe `y` und drücke Enter (wenn Homebrew noch nicht installiert)

```
Run API connection test? [y/N]:
```
→ Tippe `n` und drücke Enter (Test kommt später)

### 6. Nach der Installation

```bash
# 1. Login bei GenSpark (öffnet Browser)
open https://www.genspark.ai/aidrive/files/

# 2. In Chrome einloggen, dann Chrome schließen (Cmd+Q)

# 3. App starten
./launch.sh
```

---

## 📺 Terminal-Output Beispiel

```
================================================================
  GenSpark Sync Lite - Automated Installation
  Version: 1.0.0
================================================================

ℹ Installation directory: /Users/robert/genspark-sync-lite
ℹ Log file: /Users/robert/genspark-sync-lite/install.log

━━━ Checking Git installation
✓ Git 2.39.2 found

━━━ Checking Homebrew installation
✓ Homebrew 4.0.0 found

━━━ Checking Python installation
✓ Python 3.11.5 found (python3)

━━━ Checking pip installation
✓ pip 23.2.1 found

━━━ Checking Google Chrome installation
✓ Google Chrome found

━━━ Installing Python dependencies
ℹ Installing packages from requirements.txt...
✓ Python dependencies installed successfully

━━━ Verifying installation
✓ Module requests verified
✓ Module watchdog verified
✓ Module browser_cookie3 verified
✓ Module pydantic verified
✓ All modules verified successfully

━━━ Creating launch script
✓ Launch script created: /Users/robert/genspark-sync-lite/launch.sh

━━━ Installation Complete!

✓ GenSpark Sync Lite has been installed successfully

ℹ Next steps:
  1. Login to GenSpark AI Drive in Chrome:
     https://www.genspark.ai/aidrive/files/
  2. Close Chrome completely (Cmd+Q)
  3. Run the app:
     cd /Users/robert/genspark-sync-lite
     ./launch.sh
```

---

## 🐛 Troubleshooting

### Problem: "permission denied: ./install.sh"

**Lösung:**
```bash
chmod +x install.sh
./install.sh
```

### Problem: "gh: command not found"

**Lösung 1 - GitHub CLI installieren:**
```bash
brew install gh
```

**Lösung 2 - Nutze git statt gh:**
```bash
git clone https://github.com/stolot0mt0m/genspark-sync-lite.git
```

### Problem: "git: command not found"

**Lösung:**
```bash
# Xcode Command Line Tools installieren
xcode-select --install
```

### Problem: Installation bleibt hängen

**Lösung:**
```bash
# Ctrl+C drücken zum Abbrechen
# Log-File checken:
cat install.log

# Dann nochmal versuchen:
./install.sh
```

### Problem: "Homebrew installation failed"

**Lösung:**
```bash
# Manuell Homebrew installieren:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Dann Script nochmal:
./install.sh
```

---

## 📊 Installation-Log prüfen

```bash
# Log-File anschauen
cat install.log

# Letzte 20 Zeilen
tail -20 install.log

# Nach Fehlern suchen
grep ERROR install.log
```

---

## 🔄 Nach Updates

```bash
cd genspark-sync-lite
git pull origin master
./install.sh  # Dependencies neu installieren
```

---

## 💻 System-Anforderungen

- **macOS**: 10.14+ (Mojave oder neuer)
- **RAM**: 512MB frei
- **Disk**: 100MB frei
- **Internet**: Für Installation
- **Terminal**: Bash oder Zsh

---

## ⏱️ Installations-Dauer

| Komponente | Dauer |
|------------|-------|
| Git Clone | ~5 Sekunden |
| Script-Start | ~1 Sekunde |
| System-Checks | ~5 Sekunden |
| Homebrew (falls nötig) | ~3-5 Minuten |
| Python (falls nötig) | ~2 Minuten |
| pip Dependencies | ~30 Sekunden |
| Verification | ~10 Sekunden |
| **GESAMT** | **~5-10 Minuten** |

---

## 📱 Alternative: Ohne GitHub CLI

Falls du `gh` nicht installieren willst:

```bash
# 1. Browser öffnen
open https://github.com/stolot0mt0m/genspark-sync-lite

# 2. Klick: Code → Download ZIP

# 3. ZIP entpacken (Doppelklick im Finder)

# 4. Terminal öffnen und navigieren:
cd ~/Downloads/genspark-sync-lite-master

# 5. Installation
./install.sh
```

---

## 🎯 Komplette One-Liner

**Für Copy & Paste (mit gh):**
```bash
gh repo clone stolot0mt0m/genspark-sync-lite && cd genspark-sync-lite && ./install.sh
```

**Für Copy & Paste (mit git):**
```bash
git clone https://github.com/stolot0mt0m/genspark-sync-lite.git && cd genspark-sync-lite && ./install.sh
```

---

## 📚 Nächste Schritte

Nach erfolgreicher Installation:

1. **README.md lesen**
   ```bash
   cat README.md
   ```

2. **Quickstart folgen**
   ```bash
   cat QUICKSTART.md
   ```

3. **App starten**
   ```bash
   ./launch.sh
   ```

---

**Fragen? Schau in INSTALL.md oder öffne ein GitHub Issue!**

🚀 **Viel Erfolg!**
