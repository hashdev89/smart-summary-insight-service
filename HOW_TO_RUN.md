# How to Run the Service

## Step-by-Step Instructions

### 1. Start the Backend Server

Open a terminal and run:

```bash
# Navigate to the project directory
cd /Volumes/HashSSD/mywork/LLMAssesment

# Activate the virtual environment
source venv/bin/activate

# Start the server
python -m app.main
```

You should see output like:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**The server is now running at: http://localhost:8000**

### 2. Test the API (Choose one method)

#### Option A: Interactive API Documentation (Easiest!)
Open your web browser and go to:
- **http://localhost:8000/docs** - Interactive Swagger UI
- Click "Try it out" on the `/analyze` endpoint
- Fill in the request and click "Execute"

#### Option B: Use the Web Frontend
1. Keep the server running (from Step 1)
2. Open `frontend/index.html` in your browser:
   - Double-click the file, or
   - Right-click → Open With → Browser
3. Enter your data and click "Analyze"

#### Option C: Use the Example Script
Open a **new terminal** (keep server running in the first one):

```bash
cd /Volumes/HashSSD/mywork/LLMAssesment
source venv/bin/activate
python example_usage.py
```

#### Option D: Use cURL
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": ["Customer reported login issues"],
    "structured_data": {
      "data": {
        "customer_id": "12345",
        "priority": "high"
      }
    }
  }'
```

## Quick Reference

### Start Server
```bash
source venv/bin/activate
python -m app.main
```

### Stop Server
Press `Ctrl+C` in the terminal where the server is running

### Test API
- Browser: http://localhost:8000/docs
- Frontend: Open `frontend/index.html`
- Script: `python example_usage.py`

## Troubleshooting

### "Module not found" error
Make sure virtual environment is activated:
```bash
source venv/bin/activate
```

### "Port already in use" error
Another process is using port 8000. Either:
- Stop the other process, or
- Change the port in `.env` file: `PORT=8001`

### "API key not found" error
Make sure `.env` file exists in the project root with your API key.

