# Quick Start Guide

## Running the Backend Service

### Step 1: Activate Virtual Environment
```bash
source venv/bin/activate
```

### Step 2: Set Up Environment Variables
Create a `.env` file in the project root (if not already created):
```bash
ANTHROPIC_API_KEY=your-api-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

### Step 3: Start the Server
```bash
python -m app.main
```

Or use the run script:
```bash
./run.sh
```

The server will start at: **http://localhost:8000**

## Testing the API

### Option 1: Interactive API Documentation (No Frontend Needed!)
Once the server is running, open your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

You can test the API directly from these pages!

### Option 2: Use the Example Script
```bash
# In a new terminal (with venv activated)
python example_usage.py
```

### Option 3: Use cURL
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

### Option 4: Use Python Requests
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    json={
        "notes": ["Customer reported login issues"],
        "structured_data": {
            "data": {"customer_id": "12345"}
        }
    }
)
print(response.json())
```

## Do You Need a Frontend?

**Short answer: No!** This is a backend API service that can be used in multiple ways:

1. **Direct API calls** (as shown above)
2. **Existing applications** - integrate into your current system
3. **Command-line tools** - build CLI tools that call the API
4. **Mobile apps** - any mobile app can call the REST API
5. **Custom frontend** - if you want a web UI, you can build one

## If You Want to Build a Frontend

If you'd like a web interface, you can build one with:
- **React** - Modern JavaScript framework
- **Next.js** - React with server-side rendering
- **Vue.js** - Alternative JavaScript framework
- **Plain HTML/JavaScript** - Simple static page

The API is ready to be consumed by any frontend framework!

## Example Frontend Integration

If you build a React/Next.js frontend, you would call the API like this:

```javascript
// React/Next.js example
const analyzeData = async (notes, structuredData) => {
  const response = await fetch('http://localhost:8000/api/v1/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      notes: notes,
      structured_data: structuredData
    })
  });
  
  const result = await response.json();
  return result;
};
```

## Production Deployment

For production, you might want to:
1. Use a production ASGI server (Gunicorn + Uvicorn workers)
2. Add authentication/authorization
3. Deploy to cloud (AWS, GCP, Azure, etc.)
4. Build a frontend if needed
5. Add monitoring and logging

But for development and testing, the current setup is perfect!

