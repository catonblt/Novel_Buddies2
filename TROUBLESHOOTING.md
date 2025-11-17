# Backend Connection Troubleshooting Guide

## Symptom
Backend starts successfully but frontend shows "Backend server is not responding. Please start it on port 8000."

---

## Step-by-Step Troubleshooting

### **Step 1: Verify Backend is Actually Running**

Open a terminal and run:

```bash
# Check if process is running
ps aux | grep uvicorn

# Check if port 8000 is listening
# On Linux/Mac:
lsof -i :8000
# OR
netstat -tulpn | grep 8000

# On Windows:
netstat -ano | findstr :8000
```

**Expected output:**
- You should see a uvicorn process
- Port 8000 should show as LISTEN

**If nothing shows:** Backend is not running. Start it with:
```bash
cd python-backend
python3 -m uvicorn main:app --reload --port 8000
```

---

### **Step 2: Test Backend Health Endpoint Directly**

#### Test A: Using curl
```bash
curl -v http://localhost:8000/health
```

**Expected output:**
```
HTTP/1.1 200 OK
...
{"status":"healthy"}
```

#### Test B: Using browser
Open your browser and go to:
```
http://localhost:8000/health
```

**Expected output:** You should see:
```json
{"status":"healthy"}
```

#### Test C: Using 127.0.0.1
```bash
curl -v http://127.0.0.1:8000/health
```

**If any of these fail:**
- Backend is not listening on port 8000
- Check backend terminal for errors
- Try restarting the backend

---

### **Step 3: Check Backend Logs**

Look at the terminal where backend is running. You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
2025-XX-XX XX:XX:XX | NovelWriter | INFO | Logger initialized...
2025-XX-XX XX:XX:XX | NovelWriter | INFO | NovelWriter Backend Server Starting
2025-XX-XX XX:XX:XX | NovelWriter | INFO | Database initialized successfully
INFO:     Application startup complete.
```

**If you see errors:** Share the error message for specific help.

---

### **Step 4: Test CORS from Browser Console**

Open your browser's Developer Tools (F12) and run this in the Console:

```javascript
// Test 1: Basic fetch
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(data => console.log('✓ Success:', data))
  .catch(err => console.error('✗ Error:', err));

// Test 2: Check for CORS errors
fetch('http://localhost:8000/health', {
  method: 'GET',
  mode: 'cors',
  headers: { 'Content-Type': 'application/json' }
})
  .then(r => r.json())
  .then(data => console.log('✓ CORS Success:', data))
  .catch(err => console.error('✗ CORS Error:', err));
```

**Expected output:**
```
✓ Success: {status: "healthy"}
✓ CORS Success: {status: "healthy"}
```

**If you see CORS error:**
```
Access to fetch at 'http://localhost:8000/health' from origin 'http://localhost:1420'
has been blocked by CORS policy
```

This means CORS is the issue. Jump to **Step 6**.

---

### **Step 5: Check Frontend Configuration**

#### Check API Base URL
Open `src/lib/api.ts` and verify line 4:
```typescript
const API_BASE_URL = 'http://localhost:8000';
```

**Should be:** `http://localhost:8000` (no trailing slash)

#### Check What URL Frontend is Actually Using
In your browser console (F12 → Console tab), look for log messages when the app loads:

```
[INFO] Checking backend health...
[API Request] GET http://localhost:8000/health
```

**Look for:**
- Is it trying to connect to the right URL?
- Any error messages about "Failed to fetch"?

---

### **Step 6: Verify CORS Configuration**

Check `python-backend/main.py` lines 57-72:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "tauri://localhost",
        "http://localhost",
        "http://127.0.0.1"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**If this looks different:** You might not have pulled the latest changes.

**To verify CORS is working:**
```bash
curl -v -H "Origin: http://localhost:1420" http://localhost:8000/health
```

**Expected output:** Should include:
```
Access-Control-Allow-Origin: http://localhost:1420
```

---

### **Step 7: Test from Tauri Context**

If you're running the Tauri app (not browser), check the Tauri console output.

#### On Development Mode:
When running `npm run tauri dev`, look for console output showing:
- What origin Tauri is using
- Any fetch errors
- Network errors

#### Check Tauri DevTools:
Right-click in the app → "Inspect Element" (if available) → Console tab

Look for JavaScript errors or fetch failures.

---

### **Step 8: Check Firewall/Antivirus**

Sometimes firewall or antivirus software blocks localhost connections.

**Test:**
```bash
# Temporarily bind backend to all interfaces
cd python-backend
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then test again: `curl http://localhost:8000/health`

**If this works:** Your firewall is blocking 127.0.0.1. Add an exception for Python/uvicorn.

---

### **Step 9: Check Network Tab in DevTools**

Open browser DevTools (F12) → Network tab → Reload your app

**Look for:**
1. A request to `http://localhost:8000/health`
2. Click on it to see:
   - **Status:** Should be `200 OK`
   - **Response:** Should be `{"status":"healthy"}`
   - **Headers → Response Headers:** Should include `Access-Control-Allow-Origin`

**If you see:**
- **Status: (failed)** → Backend not reachable
- **Status: (blocked:other)** → CORS issue
- **Status: (canceled)** → Request was aborted
- **Status: 404** → Wrong URL
- **Status: 500** → Backend error

---

### **Step 10: Test Different URL Variations**

Try changing the API base URL in `src/lib/api.ts`:

```typescript
// Try these one at a time:
const API_BASE_URL = 'http://localhost:8000';      // Current
const API_BASE_URL = 'http://127.0.0.1:8000';      // Try this
const API_BASE_URL = 'http://0.0.0.0:8000';        // Or this
```

Rebuild and test after each change.

---

## Common Issues and Solutions

### Issue 1: "Failed to fetch" in Console
**Cause:** Backend not running or wrong URL
**Fix:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `API_BASE_URL` in `src/lib/api.ts`

---

### Issue 2: CORS Error
**Cause:** Tauri origin not in allow_origins list
**Fix:**
1. Find actual origin in browser console
2. Add it to `allow_origins` in `python-backend/main.py`
3. Restart backend

---

### Issue 3: Backend Starts Then Stops
**Cause:** Port already in use or crash
**Fix:**
```bash
# Kill all uvicorn processes
pkill -9 uvicorn
# Check what's using port 8000
lsof -i :8000
# Kill it
kill -9 <PID>
# Restart backend
cd python-backend
python3 -m uvicorn main:app --reload --port 8000
```

---

### Issue 4: Works in Browser but Not in Tauri
**Cause:** Tauri uses different origin (tauri://localhost)
**Fix:** Check Tauri console logs for actual origin and add to CORS

---

### Issue 5: "Connection Refused"
**Cause:** Backend not listening on the right interface
**Fix:** Start backend with:
```bash
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Quick Diagnosis Script

Run this to check everything at once:

```bash
#!/bin/bash

echo "=== Backend Connection Diagnostic ==="
echo ""

echo "1. Checking if backend process is running..."
ps aux | grep uvicorn | grep -v grep || echo "   ✗ Backend not running!"

echo ""
echo "2. Checking if port 8000 is listening..."
lsof -i :8000 || echo "   ✗ Port 8000 not listening!"

echo ""
echo "3. Testing health endpoint with curl..."
curl -s http://localhost:8000/health || echo "   ✗ Health endpoint not responding!"

echo ""
echo "4. Testing with 127.0.0.1..."
curl -s http://127.0.0.1:8000/health || echo "   ✗ 127.0.0.1 not responding!"

echo ""
echo "5. Testing CORS headers..."
curl -I -H "Origin: http://localhost:1420" http://localhost:8000/health | grep -i "access-control" || echo "   ✗ CORS headers missing!"

echo ""
echo "6. Checking backend logs (last 10 lines)..."
tail -10 ~/.local/share/NovelWriter/logs/application.log || echo "   ✗ No logs found!"

echo ""
echo "=== Diagnostic Complete ==="
```

Save this as `diagnose.sh`, make it executable (`chmod +x diagnose.sh`), and run it: `./diagnose.sh`

---

## What Information to Provide

If none of the above fixes your issue, please provide:

1. **Output of diagnostic script above**
2. **Backend terminal output** (full startup log)
3. **Browser console errors** (DevTools → Console)
4. **Network tab screenshot** (DevTools → Network → health request)
5. **Your operating system** (Windows/Mac/Linux)
6. **How you're running the app** (npm run dev? Tauri dev? Built installer?)

This will help identify the exact issue!
