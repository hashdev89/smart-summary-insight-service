# How to Start the Server

## Quick Start

**Open a terminal and run these commands:**

```bash
cd /Volumes/HashSSD/mywork/LLMAssesment
source venv/bin/activate
python -m app.main
```

**You should see output like:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Then Open in Browser

Once you see "Uvicorn running on http://0.0.0.0:8000", open:

**http://localhost:8000/docs**

You should see the interactive API documentation.

## Alternative: Use the Script

```bash
./RUN_ME.sh
```

## Troubleshooting

### If you see "Module not found"
Make sure you activated the virtual environment:
```bash
source venv/bin/activate
```

### If port 8000 is already in use
Change the port in `.env` file or kill the process using port 8000:
```bash
lsof -ti:8000 | xargs kill -9
```

### If the page is still blank
1. Make sure the server is actually running (check terminal output)
2. Try: http://localhost:8000 (should show JSON)
3. Try: http://localhost:8000/api/v1/health (should show {"status": "healthy"})
4. Check browser console for errors (F12 → Console)

