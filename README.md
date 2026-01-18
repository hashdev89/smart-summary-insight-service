# Smart Summary & Insight Service

An AI-powered backend service that analyzes structured business data and unstructured notes to generate concise summaries, key insights, and suggested follow-up actions.

## Features

- **RESTful API** with `/analyze` endpoint
- **Thoughtful prompt engineering** with context size management
- **Pluggable AI provider design** (currently Claude API)
- **Request caching** for deduplication and performance
- **Async processing** support
- **Comprehensive error handling** and validation
- **Clean architecture** with separation of concerns
- **Docker support** for easy deployment
- **Web frontend** included for easy testing

## Architecture

```
.
├── app/                    # Core application
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Configuration management
│   ├── models/            # Pydantic schemas for request/response
│   │   └── schemas.py
│   ├── services/          # Business logic layer
│   │   ├── ai_service.py  # LLM interaction service
│   │   ├── prompt_builder.py # Prompt engineering
│   │   └── cache_service.py  # Caching layer
│   └── api/               # API routes and controllers
│       └── routes.py
├── frontend/              # Web frontend
│   └── index.html
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── requirements.txt       # Python dependencies (8 packages)
└── README.md             # This file
```

## Quick Start

### Prerequisites

- Python 3.9 or higher (or Docker)
- Anthropic Claude API key

### Option 1: Using Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hashdev89/smart-summary-insight-service.git
   cd smart-summary-insight-service
   ```

2. **Create a `.env` file:**
   ```bash
   cat > .env << EOL
   ANTHROPIC_API_KEY=your-api-key-here
   CLAUDE_MODEL=claude-3-5-sonnet-20241022
   MAX_TOKENS=2000
   TEMPERATURE=0.7
   ENABLE_CACHE=true
   CACHE_TTL_SECONDS=3600
   HOST=0.0.0.0
   PORT=8000
   EOL
   ```

3. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

   The service will be available at `http://localhost:8000`

4. **Or build and run manually:**
   ```bash
   docker build -t smart-summary-service .
   docker run -d -p 8000:8000 --env-file .env smart-summary-service
   ```

### Option 2: Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hashdev89/smart-summary-insight-service.git
   cd smart-summary-insight-service
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file:**
   ```bash
   cat > .env << EOL
   ANTHROPIC_API_KEY=your-api-key-here
   CLAUDE_MODEL=claude-3-5-sonnet-20241022
   MAX_TOKENS=2000
   TEMPERATURE=0.7
   ENABLE_CACHE=true
   CACHE_TTL_SECONDS=3600
   HOST=0.0.0.0
   PORT=8000
   EOL
   ```

5. **Run the service:**
   ```bash
   python -m app.main
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Using the Service

### Web Frontend

A simple HTML frontend is included for easy testing:

1. **Start the backend server** (using Docker or locally)

2. **Serve the frontend:**
   ```bash
   cd frontend
   python3 -m http.server 8080
   ```

3. **Open in browser:** `http://localhost:8080`

   The frontend provides a user-friendly interface to test the API without writing any code!

### API Endpoints

- **API Base**: `http://localhost:8000`
- **Interactive API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)
- **Health Check**: `http://localhost:8000/api/v1/health`

### POST /api/v1/analyze

Analyze structured data and free-text notes.

**Request Body:**
```json
{
  "structured_data": {
    "data": {
      "customer_id": "12345",
      "event_type": "support_ticket",
      "priority": "high",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  },
  "notes": [
    "Customer reported login issues",
    "Issue persists after password reset",
    "Customer is frustrated and considering cancellation"
  ]
}
```

**Response:**
```json
{
  "summary": "Customer experiencing persistent login issues despite password reset, showing frustration and potential churn risk.",
  "insights": [
    {
      "title": "Login Issue Persistence",
      "description": "Problem continues after standard password reset procedure",
      "category": "Technical Issue",
      "priority": "high"
    },
    {
      "title": "Customer Churn Risk",
      "description": "Customer expressing frustration and considering cancellation",
      "category": "Business Risk",
      "priority": "high"
    }
  ],
  "next_actions": [
    {
      "action": "Escalate to senior support team immediately",
      "priority": "high",
      "rationale": "Standard resolution failed, customer at risk of churn"
    },
    {
      "action": "Schedule follow-up call within 24 hours",
      "priority": "high",
      "rationale": "Proactive engagement needed to retain customer"
    }
  ],
  "metadata": {
    "confidence_score": 0.85,
    "model_version": "claude-3-5-sonnet-20241022",
    "processing_time_ms": 1234.56,
    "tokens_used": 450,
    "timestamp": "2024-01-15T10:31:00Z"
  }
}
```

### Example cURL Request

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": ["Customer reported issue with payment processing"],
    "structured_data": {
      "data": {
        "customer_id": "12345",
        "transaction_amount": 99.99
      }
    }
  }'
```

### Example Python Request

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    json={
        "notes": ["Customer reported issue with payment processing"],
        "structured_data": {
            "data": {
                "customer_id": "12345",
                "transaction_amount": 99.99
            }
        }
    }
)

print(response.json())
```

## Configuration

Environment variables (in `.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | **Required** |
| `CLAUDE_MODEL` | Claude model version | `claude-3-5-sonnet-20241022` |
| `MAX_TOKENS` | Maximum tokens in response | `2000` |
| `TEMPERATURE` | Model temperature (0-1) | `0.7` |
| `ENABLE_CACHE` | Enable response caching | `true` |
| `CACHE_TTL_SECONDS` | Cache time-to-live | `3600` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

## Dependencies

The project uses only 8 essential Python packages:

- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server
- `pydantic` - Data validation
- `pydantic-settings` - Settings management
- `anthropic` - Claude API client
- `python-dotenv` - Environment variable management
- `python-multipart` - Form data support
- `cachetools` - Caching implementation

## Docker & CI/CD

### Docker

The project includes:
- **Dockerfile** - Multi-stage build for optimized image size
- **docker-compose.yml** - Easy orchestration with environment variables

### GitHub Actions

Automated CI/CD pipeline (`.github/workflows/docker-build-push.yml`):
- Automatically builds and pushes Docker image on push to `main` branch
- Supports manual workflow dispatch with custom tags
- Pushes to Docker Hub: `hashdev89/llmassesment`

## Design Decisions

### Prompt Engineering

The service uses a structured prompt design:

1. **System Prompt**: Defines the AI's role, output format, and guidelines
2. **User Prompt**: Organized sections for structured data and notes
3. **Context Management**: Automatic truncation if input exceeds token limits
4. **JSON Output**: Structured JSON response for reliable parsing

### Architecture Patterns

- **Separation of Concerns**: Clear boundaries between API, services, and models
- **Pluggable Design**: AI service can be extended to support other providers
- **Caching Layer**: Reduces API calls and improves response time
- **Error Handling**: Comprehensive error handling at each layer

### Context Size Management

- Token estimation: ~4 characters per token
- Automatic truncation when input exceeds limits
- Preserves structure by truncating from the middle

## Production Considerations

Before deploying to production:

1. **Security**:
   - Use environment variables for API keys (never commit `.env`)
   - Add authentication/authorization
   - Configure CORS appropriately (currently allows all origins)
   - Add rate limiting

2. **Performance**:
   - Use production-grade ASGI server (e.g., Gunicorn with Uvicorn workers)
   - Consider Redis for distributed caching
   - Add connection pooling for API clients

3. **Monitoring**:
   - Add structured logging
   - Implement health checks (already included)
   - Add metrics collection (Prometheus, etc.)
   - Set up error tracking (Sentry, etc.)

4. **Scalability**:
   - Consider background job processing (Celery, etc.)
   - Implement request queuing for high load
   - Add horizontal scaling support

## License

Internal use only.

## Repository

- **GitHub**: https://github.com/hashdev89/smart-summary-insight-service
- **Docker Hub**: https://hub.docker.com/r/hashdev89/llmassesment

Design & Developed by Hash with help of AI
