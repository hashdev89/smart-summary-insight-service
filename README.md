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

## Architecture

```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── models/              # Pydantic schemas for request/response
│   └── schemas.py
├── services/            # Business logic layer
│   ├── ai_service.py    # LLM interaction service
│   ├── prompt_builder.py # Prompt engineering
│   └── cache_service.py  # Caching layer
└── api/                 # API routes and controllers
    └── routes.py
```

## Setup & Installation

### Prerequisites

- Python 3.9 or higher
- Anthropic Claude API key

### Installation Steps

1. **Clone or navigate to the project directory:**
   ```bash
   cd /Volumes/HashSSD/mywork/LLMAssesment
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

4. **Configure environment variables:**
   
   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```

## Running the Service

### Quick Start (Easiest Way)

```bash
# Option 1: Use the start script
./start_server.sh

# Option 2: Manual start
source venv/bin/activate
python -m app.main
```

Or using uvicorn directly:

```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The service will be available at:
- **API**: `http://localhost:8000`
- **Interactive API Docs**: `http://localhost:8000/docs` (Test the API here!)
- **Alternative Docs**: `http://localhost:8000/redoc`

### Using the Web Frontend

A simple HTML frontend is included! After starting the server:

1. Open `frontend/index.html` in your web browser
2. Or serve it with a simple HTTP server:
   ```bash
   # Python 3
   cd frontend && python -m http.server 8080
   # Then open http://localhost:8080
   ```

The frontend provides a user-friendly interface to test the API without writing any code!

## API Usage

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
    "notes": "Customer reported issue with payment processing",
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
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Required |
| `CLAUDE_MODEL` | Claude model version | `claude-3-5-sonnet-20241022` |
| `MAX_TOKENS` | Maximum tokens in response | `2000` |
| `TEMPERATURE` | Model temperature (0-1) | `0.7` |
| `ENABLE_CACHE` | Enable response caching | `true` |
| `CACHE_TTL_SECONDS` | Cache time-to-live | `3600` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

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

## Testing

Run tests with pytest:

```bash
pytest tests/
```

Basic test coverage includes:
- API endpoint validation
- Prompt builder functionality
- Health check endpoint

## Evaluation & Improvement

### Output Quality Evaluation

To evaluate and improve outputs:

1. **Confidence Scores**: The service returns confidence scores (0.0-1.0) based on data completeness
2. **A/B Testing**: Compare different prompt variations
3. **Human Review**: Sample outputs for quality assessment
4. **Metrics**: Track processing time, token usage, and error rates

### Potential Improvements

- **Fine-tuning**: Fine-tune prompts based on domain-specific feedback
- **Output Validation**: Add schema validation for LLM responses
- **Retry Logic**: Implement exponential backoff for API failures
- **Rate Limiting**: Add rate limiting for production use
- **Monitoring**: Add logging and metrics collection
- **Batch Processing**: Support batch analysis requests
- **Streaming**: Support streaming responses for long analyses

## Production Considerations

Before deploying to production:

1. **Security**:
   - Use environment variables for API keys (never commit `.env`)
   - Add authentication/authorization
   - Configure CORS appropriately
   - Add rate limiting

2. **Performance**:
   - Use production-grade ASGI server (e.g., Gunicorn with Uvicorn workers)
   - Consider Redis for distributed caching
   - Add connection pooling for API clients

3. **Monitoring**:
   - Add structured logging
   - Implement health checks
   - Add metrics collection (Prometheus, etc.)
   - Set up error tracking (Sentry, etc.)

4. **Scalability**:
   - Consider background job processing (Celery, etc.)
   - Implement request queuing for high load
   - Add horizontal scaling support

## License

Internal use only.

Design & Developed by Hash with help of AI
