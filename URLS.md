# GenSpark AI Drive - URL Reference

## 🌐 Web Interface

### AI Drive Files
```
https://www.genspark.ai/aidrive/files/
```
**Beschreibung:** Haupt-Interface für AI Drive  
**Verwendung:** 
- Login
- Dateien ansehen
- Manuelles Upload/Download
- Cookie Session generieren

---

## 🔌 API Endpoints

### Base URL
```
https://www.genspark.ai/api/side/wget_upload_url
```

### 1. List Files
```
GET /api/side/wget_upload_url/files
    ?filter_type=all
    &sort_by=modified_desc
    &file_type=all
```

**Query Parameters:**
- `filter_type`: `all` | `file` | `directory`
- `sort_by`: `modified_desc` | `modified_asc` | `name_asc` | `name_desc`
- `file_type`: `all` | specific mime type

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "filename.txt",
      "path": "/subfolder",
      "type": "file",
      "mime_type": "text/plain",
      "modified_time": 1760625870,
      "size": 664,
      "parent_id": "c25a82be-6311-4406-a7c2-70fce03c81b3:root",
      "thumbnail": null
    }
  ]
}
```

### 2. Request Upload URL
```
POST /api/side/wget_upload_url/files/{filename}
```

**Headers:**
- `Cookie`: Session cookie from Chrome

**Response:**
```json
{
  "status": "success",
  "message": "Upload URL generated successfully",
  "data": {
    "upload_url": "https://gensparkstorageprodwest.blob.core.windows.net/web-drive/...",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": 1706827506
  }
}
```

### 3. Upload File to Azure Blob
```
PUT {upload_url}
```

**Headers:**
- `x-ms-blob-type`: `BlockBlob`
- `Authorization`: `Bearer {token}`
- `Content-Type`: File mime type

**Body:** Binary file data

**Response:** HTTP 201 Created (no body)

### 4. Download File
```
GET /api/side/wget_upload_url/files/{filename}
```

**Headers:**
- `Cookie`: Session cookie

**Response:** Binary file data

### 5. Delete File (TODO - needs verification)
```
DELETE /api/side/wget_upload_url/files/{file_id}
```

---

## 🔐 Authentication

### Cookie-Based Session

**Domain:** `genspark.ai`

**Required Cookies:**
- Session cookie (exact name TBD)
- Possible other auth cookies

**How to obtain:**
1. Open Chrome
2. Navigate to https://www.genspark.ai/aidrive/files/
3. Login with credentials
4. Cookies are automatically stored in Chrome
5. `browser-cookie3` extracts them for API use

**Cookie Lifespan:**
- Unknown expiry time
- Need to re-login when expired
- App detects expired session via 401/403 responses

---

## 📊 Storage Backend

### Azure Blob Storage

**Endpoint:**
```
https://gensparkstorageprodwest.blob.core.windows.net/
```

**Container:**
```
web-drive
```

**Path Structure:**
```
/web-drive/{user_id}/{file_id}
```

**Example:**
```
https://gensparkstorageprodwest.blob.core.windows.net/web-drive/c25a82be-6311-4406-a7c2-70fce03c81b3/56ffa943-79b2-43a6-901e-8f04514eddbd
```

---

## 🧪 Testing Endpoints

### Manual Test with curl

```bash
# 1. Extract cookies from Chrome (manual)
# Open Chrome DevTools → Application → Cookies → Copy cookie value

# 2. List files
curl -H "Cookie: session=YOUR_SESSION_COOKIE" \
  "https://www.genspark.ai/api/side/wget_upload_url/files?filter_type=all&sort_by=modified_desc&file_type=all"

# 3. Request upload URL
curl -X POST \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  "https://www.genspark.ai/api/side/wget_upload_url/files/test.txt"

# 4. Upload file (using response from step 3)
curl -X PUT \
  -H "x-ms-blob-type: BlockBlob" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: text/plain" \
  --data-binary @test.txt \
  "YOUR_UPLOAD_URL"

# 5. Download file
curl -H "Cookie: session=YOUR_SESSION_COOKIE" \
  "https://www.genspark.ai/api/side/wget_upload_url/files/test.txt" \
  -o downloaded.txt
```

---

## 🔍 Discovery Notes

### How APIs were discovered:
1. Open Chrome DevTools (F12)
2. Navigate to https://www.genspark.ai/aidrive/files/
3. Network Tab → Filter: Fetch/XHR
4. Upload a file → Observe requests
5. Refresh page → Observe file listing requests
6. Analyze request/response patterns

### What's confirmed:
- ✅ List Files API
- ✅ Upload URL Request API
- ✅ Azure Blob Upload pattern
- ✅ Cookie-based authentication

### What needs verification:
- ⏳ Delete API endpoint
- ⏳ Move/Rename API
- ⏳ Create Directory API
- ⏳ Thumbnail generation API
- ⏳ Exact cookie names
- ⏳ Session expiry time

---

## 📝 API Limitations (Known)

### Rate Limiting
- Unknown - needs testing
- Probably present to prevent abuse

### File Size Limits
- Unknown - needs testing
- Azure Blob supports up to 4.75 TB per blob

### Concurrent Uploads
- Unknown - needs testing
- Probably limited per account

### API Versioning
- No version in URL path
- May break without notice
- Monitor for changes

---

## 🚨 Important Notes

### Security
- ⚠️ Never commit cookies to git
- ⚠️ Never share session tokens
- ⚠️ Cookies grant full account access
- ⚠️ Use HTTPS only

### Stability
- 🟡 Unofficial API (no public docs)
- 🟡 May change without notice
- 🟡 No SLA or support
- 🟡 Use at own risk

### Best Practices
- ✅ Implement retry logic
- ✅ Handle 401/403 gracefully
- ✅ Respect rate limits
- ✅ Log all API calls
- ✅ Monitor for breaking changes

---

**Last Updated:** 2025-10-16  
**Status:** URLs verified by Robert  
**Next:** Test all endpoints with real account
