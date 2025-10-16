# Log Optimization für Produktionsbetrieb

## Änderungen

### 1. **Reduzierte Routine-Logs** (INFO → DEBUG)
Alle wiederkehrenden, nicht-kritischen Operationen wurden auf DEBUG-Level gesetzt:

- Cookie-Loading aus Chrome
- Upload/Download-URLs anfordern
- Azure Blob Storage Upload-Details
- Datei-Scan Details (remote/local)
- SQLite State-Loading
- Einzelne Datei-Operationen (Upload/Download/Delete)

### 2. **Kompakte Sync-Zusammenfassung**
Statt vieler einzelner Logs pro Datei:
```
✅ Sync: ↑2 | ↓1 | 🗑️→3 | 🗑️←1
```

Bedeutung:
- `↑2` = 2 Uploads
- `↓1` = 1 Download
- `🗑️→3` = 3 Remote-Deletions (lokal gelöscht → remote löschen)
- `🗑️←1` = 1 Local-Deletion (remote gelöscht → lokal löschen)

### 3. **Keine Logs bei "Keine Änderungen"**
Wenn nichts passiert, wird nichts geloggt. Stille = Alles OK.

### 4. **Gruppierte Operation-Logs**
Statt:
```
Deleting from remote: file1.txt
Deleting from remote: file2.txt
Deleting from remote: file3.txt
```

Jetzt:
```
🗑️  Propagating 3 local deletions to AI Drive
```

### 5. **Entfernte überflüssige Logs**
- "Starting sync cycle" → DEBUG
- "Files to upload: X" → nur wenn X > 0
- "Scanning X folders" → DEBUG
- "Polling AI Drive for changes..." → DEBUG
- Detaillierte Conflict-Logs → kompakte Warnung

## Vorher vs. Nachher

### Vorher (> 20 Zeilen pro Sync):
```
2025-10-16 23:59:08,123 - INFO - Starting sync cycle...
2025-10-16 23:59:08,234 - INFO - Retrieved 45 items from AI Drive
2025-10-16 23:59:08,345 - INFO - Scanning 3 folders for files...
2025-10-16 23:59:08,456 - DEBUG - Scanning folder: Robert
2025-10-16 23:59:08,567 - INFO - Retrieved 12 items from AI Drive (folder: /Robert)
2025-10-16 23:59:08,678 - DEBUG - Scanning folder: TestOrdner
2025-10-16 23:59:08,789 - INFO - Retrieved 8 items from AI Drive (folder: /TestOrdner)
2025-10-16 23:59:08,890 - INFO - Local: 67 files, Remote: 65 files
2025-10-16 23:59:09,001 - INFO - 📥 Files deleted from AI Drive: 1
2025-10-16 23:59:09,112 - INFO - Deleting file (deleted from remote): Robert/MalWasNeues.txt
2025-10-16 23:59:09,223 - INFO - ✅ Deleted local file: Robert/MalWasNeues.txt
2025-10-16 23:59:09,334 - INFO - Files to download: 0
2025-10-16 23:59:09,445 - INFO - Files to upload: 1
2025-10-16 23:59:09,556 - INFO - Uploading new file: beschreibung.txt
2025-10-16 23:59:09,667 - INFO - Requesting upload URL for: beschreibung.txt
2025-10-16 23:59:09,778 - INFO - ✅ Got upload URL and token for: beschreibung.txt
2025-10-16 23:59:09,889 - INFO - Uploading to Azure: beschreibung.txt
2025-10-16 23:59:10,001 - INFO - Uploaded to Azure: beschreibung.txt
2025-10-16 23:59:10,112 - INFO - Confirming upload for: beschreibung.txt
2025-10-16 23:59:10,223 - INFO - ✅ Upload confirmed for: beschreibung.txt
2025-10-16 23:59:10,334 - INFO - ✅ Upload complete: beschreibung.txt
2025-10-16 23:59:10,445 - INFO - Sync complete: 1 uploads, 1 local deletions
```

### Nachher (2-3 Zeilen pro Sync):
```
2025-10-16 23:59:08,123 - INFO - 🗑️  Propagating 1 remote deletions locally
2025-10-16 23:59:09,445 - INFO - 📤 Uploading 1 new local files
2025-10-16 23:59:10,445 - INFO - ✅ Sync: ↑1 | 🗑️←1
```

**Bei keinen Änderungen: Keine Logs! 🎯**

## Log-Levels

### INFO (Produktion):
- ✅ Sync-Zusammenfassungen (nur bei Änderungen)
- 🗑️ Deletion-Operationen (gruppiert)
- 📤 Upload/Download-Gruppen (X Dateien)
- ⚠️ Warnungen (Conflicts, Errors)
- 🚀 Start/Stop der App

### DEBUG (Entwicklung):
- Einzelne Datei-Operationen
- API-Requests Details
- Database-Operations
- Folder-Scanning
- Cookie-Loading
- State-Loading

### ERROR:
- API-Fehler
- Datei-Operationen fehlgeschlagen
- Connection-Probleme

## Effekt
- **~80% weniger Logs** im Produktionsbetrieb
- **Bessere Übersicht** bei täglicher Nutzung
- **Schnelleres Scannen** der wichtigen Events
- **Kein Log-Spam** bei Idle-Zustand

## Weitere Optimierung möglich
Bei Bedarf kann der `poll_interval` auf 60s oder 120s erhöht werden, um noch weniger Logs zu generieren.
