# Manuelle Installation - Wenn install.sh fehlschlägt

## 🔧 Wenn das automatische Script Probleme hat

Falls `./install.sh` fehlschlägt, folge dieser manuellen Anleitung:

---

## 📋 Schritt-für-Schritt Manuelle Installation

### 1. Diagnose durchführen

```bash
cd genspark-sync-lite
./debug_install.sh
```

**Zeig mir den Output!** Das hilft beim Debuggen.

---

### 2. Dependencies manuell installieren

```bash
# Navigiere ins Projekt
cd ~/genspark-sync-lite  # oder wo auch immer du es geklont hast

# Installiere Python Dependencies
python3 -m pip install --user -r requirements.txt

# Warte bis fertig... (kann 30-60 Sekunden dauern)
```

**Erwartete Ausgabe:**
```
Successfully installed requests-2.31.0 watchdog-3.0.0 browser-cookie3-0.19.1 pydantic-2.5.0 python-dateutil-2.8.2
```

---

### 3. Verify Installation

```bash
# Test ob alle Module funktionieren
python3 -c "import requests, watchdog, browser_cookie3, pydantic"

# Wenn kein Error → Erfolg!
```

---

### 4. Launch Script erstellen

```bash
# Erstelle launch.sh manuell
cat > launch.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/src"
python3 sync_app.py "$@"
EOF

# Mach es ausführbar
chmod +x launch.sh
```

---

### 5. App starten

```bash
# Vor dem Start: Login bei GenSpark
open https://www.genspark.ai/aidrive/files/
# → Login → Chrome schließen (Cmd+Q)

# App starten
./launch.sh
```

---

## 🐛 Häufige Probleme

### Problem: "pip: command not found"

**Lösung:**
```bash
# Verwende python3 -m pip statt pip
python3 -m pip install --user -r requirements.txt
```

### Problem: "No module named 'pip'"

**Lösung:**
```bash
# Installiere pip via get-pip.py
curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
python3 /tmp/get-pip.py --user
rm /tmp/get-pip.py

# Dann nochmal:
python3 -m pip install --user -r requirements.txt
```

### Problem: "Permission denied"

**Lösung:**
```bash
# Verwende --user Flag (kein sudo!)
python3 -m pip install --user -r requirements.txt
```

### Problem: "ERROR: Could not find a version..."

**Lösung:**
```bash
# Update pip zuerst
python3 -m pip install --user --upgrade pip

# Dann Dependencies
python3 -m pip install --user -r requirements.txt
```

### Problem: "import requests: ModuleNotFoundError"

**Lösung:**
```bash
# Prüfe wo pip installiert
python3 -m pip show requests

# Prüfe Python sys.path
python3 -c "import sys; print('\n'.join(sys.path))"

# Stelle sicher dass User site-packages im PATH ist
python3 -c "import site; print(site.USER_SITE)"

# Falls nicht im PATH, füge hinzu:
export PYTHONPATH="$(python3 -c 'import site; print(site.USER_SITE)'):$PYTHONPATH"
```

---

## 📊 Requirements File Inhalt

Falls du Packages einzeln installieren musst:

```bash
python3 -m pip install --user requests>=2.31.0
python3 -m pip install --user watchdog>=3.0.0
python3 -m pip install --user browser-cookie3>=0.19.1
python3 -m pip install --user pydantic>=2.5.0
python3 -m pip install --user python-dateutil>=2.8.2
```

---

## 🚀 Alternative: Virtual Environment

Wenn nichts hilft, nutze venv:

```bash
cd genspark-sync-lite

# Virtual Environment erstellen
python3 -m venv venv

# Aktivieren
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Launch Script anpassen
cat > launch.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/venv/bin/activate"
cd "${SCRIPT_DIR}/src"
python sync_app.py "$@"
EOF

chmod +x launch.sh

# App starten
./launch.sh
```

---

## 🔍 Debug Checklist

Bevor du um Hilfe fragst, check:

- [ ] Python Version: `python3 --version` (mindestens 3.8)
- [ ] pip funktioniert: `python3 -m pip --version`
- [ ] Requirements installiert: `python3 -m pip list | grep requests`
- [ ] Import test: `python3 -c "import requests"`
- [ ] Chrome installiert: `/Applications/Google Chrome.app` existiert
- [ ] Login bei GenSpark: https://www.genspark.ai/aidrive/files/

---

## 📞 Wenn gar nichts funktioniert

1. **Run debug script:**
   ```bash
   ./debug_install.sh > debug_output.txt
   ```

2. **Check Log:**
   ```bash
   cat install.log
   ```

3. **GitHub Issue öffnen:**
   - Gehe zu: https://github.com/stolot0mt0m/genspark-sync-lite/issues
   - Füge `debug_output.txt` und `install.log` hinzu
   - Beschreibe dein System (macOS Version, Python Version)

---

## ✅ Nach erfolgreicher manueller Installation

Teste die App:

```bash
# 1. Login bei GenSpark (Chrome öffnen)
open https://www.genspark.ai/aidrive/files/
# → Login → Chrome schließen (Cmd+Q)

# 2. Test-Ordner erstellen (optional)
mkdir -p ~/GenSparkSyncTest

# 3. App starten
./launch.sh

# 4. Sync-Ordner wählen
# Wenn gefragt: ~/GenSparkSyncTest oder ein anderer Ordner

# 5. Testen
echo "Test file" > ~/GenSparkSyncTest/test.txt
# → Sollte hochgeladen werden (check Logs)
```

---

**Wenn manuelle Installation funktioniert, kannst du das Script ignorieren und direkt `./launch.sh` nutzen!** 🎉
