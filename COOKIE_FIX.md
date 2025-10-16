# 🔧 Cookie Authentication Fix - Schnellanleitung

## Problem
Die App lädt 14 Cookies von Chrome, bekommt aber trotzdem **403 Forbidden** vom GenSpark API.

## Ursache
- Session-Cookies sind abgelaufen oder ungültig
- ODER: Browser-Header fehlen (wird jetzt automatisch hinzugefügt)
- ODER: Du bist in Chrome nicht eingeloggt

---

## ✅ Lösung: 3-Schritte-Fix

### Schritt 1: Fresh Login in Chrome
```bash
# 1. Öffne Chrome
# 2. Gehe zu: https://www.genspark.ai/aidrive/files/
# 3. Login mit deinen Zugangsdaten
# 4. Verifiziere, dass du deine Dateien siehst
# 5. WICHTIG: Chrome KOMPLETT schließen (Cmd+Q auf Mac, nicht nur Fenster zu!)
```

**Warum Cmd+Q?**
- Nur so werden die Cookies in den macOS Keychain geschrieben
- Ein einfaches Fenster-Schließen reicht NICHT

---

### Schritt 2: Cookie-Diagnostics laufen lassen
```bash
cd ~/genspark-sync-lite
source venv/bin/activate
python3 debug_cookies.py
```

**Was das Script macht:**
- ✅ Zeigt alle 14 Cookies im Detail
- ✅ Markiert kritische Session-Cookies (🔑)
- ✅ Testet API-Call mit diesen Cookies
- ✅ Gibt dir konkrete Fehlermeldungen

**Erwartetes Ergebnis:**
```
🔑 CRITICAL Cookie #3: __Secure-next-auth.session-token
     Domain: .genspark.ai
     Value: eyJhbGciOiJkaXIiLCJlbmMiOi... (sehr lang)
     Expires: 2025-11-15 18:43:22

✅ SUCCESS! API call worked!
   Found 42 files in AI Drive
```

---

### Schritt 3: Sync-App neu starten
```bash
# Falls der Debug erfolgreich war:
./launch.sh

# Die App sollte jetzt ohne 403-Fehler starten
```

---

## 🔍 Was wurde am Code geändert?

### 1. Browser-Header hinzugefügt (genspark_api.py)
```python
# NEU: Session sendet jetzt Browser-Header
self.session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.genspark.ai/aidrive/files/',
    'Origin': 'https://www.genspark.ai',
    'Sec-Fetch-Mode': 'cors',
    # ... weitere Header
})
```

**Grund:** GenSpark API prüft vermutlich auf Browser-typische Header. Ohne diese sieht der Request wie ein Bot aus → 403.

### 2. Debug-Script erstellt (debug_cookies.py)
- Zeigt **alle** Cookie-Details
- Identifiziert kritische Session-Cookies
- Testet API-Call direkt
- Gibt konkrete Troubleshooting-Tipps

---

## 🎯 Nächste Schritte nach Fix

Sobald die Cookie-Authentication funktioniert:

1. **Test Upload**: 
   ```bash
   echo "Test" > ~/GenSpark\ AI\ Drive/test.txt
   # App sollte automatisch hochladen
   ```

2. **Test Download**: 
   ```bash
   # Erstelle Datei im Web-Interface
   # App sollte sie nach 30-60 Sekunden herunterladen
   ```

3. **Conflict-Test**:
   ```bash
   # Bearbeite dieselbe Datei lokal UND im Web
   # App sollte Konflikt erkennen
   ```

---

## 🚨 Wenn es immer noch nicht funktioniert

### Symptom: Debug zeigt "NO CRITICAL COOKIES FOUND"
**Lösung:**
- Du warst nicht eingeloggt in Chrome
- Wiederhole Schritt 1 (Fresh Login)

### Symptom: Debug zeigt Cookies, aber trotzdem 403
**Mögliche Ursachen:**
1. **Cookie-Domain falsch**: 
   - Sollte `.genspark.ai` sein (mit Punkt am Anfang)
   - Oder `genspark.ai` (ohne Subdomain)

2. **API-Endpoint geändert**:
   ```bash
   # Teste manuell im Browser DevTools:
   # 1. Öffne https://www.genspark.ai/aidrive/files/
   # 2. F12 → Network Tab
   # 3. Filter: Fetch/XHR
   # 4. Schaue welche API-Calls gemacht werden
   # 5. Kopiere den exakten Endpoint
   ```

3. **CSRF-Token erforderlich**:
   - Manche APIs brauchen zusätzlich ein CSRF-Token im Header
   - Ist im Cookie oder als Meta-Tag im HTML

### Symptom: "browser_cookie3 Fehler auf macOS"
```bash
# Gib Python Keychain-Zugriff:
# System Settings → Privacy & Security → Full Disk Access
# Füge Terminal.app hinzu (oder iTerm, je nachdem)
```

---

## 📝 Technische Details

### Cookie-Extraktion auf macOS
```python
browser_cookie3.chrome(domain_name='genspark.ai')
```

**Was passiert intern:**
1. Liest Chrome's Cookie-Datenbank: `~/Library/Application Support/Google/Chrome/Default/Cookies`
2. Die Datenbank ist verschlüsselt (SQLite + AES)
3. Entschlüsselungs-Key liegt im macOS Keychain
4. `browser_cookie3` nutzt `keyring`-Library für Keychain-Zugriff
5. Gibt Python `http.cookiejar.Cookie` Objekte zurück

### Warum Chrome schließen (Cmd+Q)?
Chrome hält die Cookie-Datenbank im Memory und schreibt nur bei:
- Explizitem Beenden (Cmd+Q)
- Automatischem Sync-Intervall (ca. alle 30 Sekunden)

Ein einfaches Fenster-Schließen reicht NICHT.

---

## 🎓 Für später: LaunchAgent Setup

Sobald die App stabil läuft, kannst du sie als macOS-Service einrichten:

```bash
# Erstelle LaunchAgent (kommt später)
cat > ~/Library/LaunchAgents/com.genspark.sync.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" ...>
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.genspark.sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USER/genspark-sync-lite/launch.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Lade Service
launchctl load ~/Library/LaunchAgents/com.genspark.sync.plist
```

**Aber erst nach erfolgreichem Test!**

---

## 📞 Support

Falls das Problem weiterhin besteht:
1. Führe `debug_cookies.py` aus
2. Kopiere die komplette Ausgabe
3. Schicke sie mir zusammen mit:
   - macOS Version (`sw_vers`)
   - Chrome Version (chrome://version/)
   - Python Version (`python3 --version`)

---

**Stand:** 2025-10-16 (nach 403-Fehler-Analyse)
