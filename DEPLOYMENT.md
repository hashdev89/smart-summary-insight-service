# Deployment Guide

## Docker Deployment

### Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000

# Run the application
CMD ["python", "-m", "app.main"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - CLAUDE_MODEL=claude-3-5-haiku-20241022
      - MAX_TOKENS=1200
      - TEMPERATURE=0.3
    volumes:
      - ./app:/app/app
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./frontend:/usr/share/nginx/html
    depends_on:
      - backend
    restart: unless-stopped
```

### Build and Run

```bash
# Build and start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## Production Deployment

### Using Gunicorn + Uvicorn

1. **Install Gunicorn:**
   ```bash
   pip install gunicorn
   ```

2. **Create `gunicorn_config.py`:**
   ```python
   bind = "0.0.0.0:8000"
   workers = 4
   worker_class = "uvicorn.workers.UvicornWorker"
   timeout = 120
   keepalive = 5
   ```

3. **Run with Gunicorn:**
   ```bash
   gunicorn app.main:app -c gunicorn_config.py
   ```

### Environment Variables

Set these in your production environment:

```bash
ANTHROPIC_API_KEY=your-api-key
CLAUDE_MODEL=claude-3-5-haiku-20241022
MAX_TOKENS=1200
TEMPERATURE=0.3
ENABLE_CACHE=true
CACHE_TTL_SECONDS=3600
HOST=0.0.0.0
PORT=8000
```

### Process Management

Use systemd, PM2, or supervisor to manage the backend process:

**systemd service** (`/etc/systemd/system/smart-insight.service`):

```ini
[Unit]
Description=Smart Summary & Insight Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/LLMAssesment
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Frontend Deployment

### Static Hosting

The frontend is a static HTML file and can be deployed to:

- **Netlify**: Drag and drop the `frontend` folder
- **Vercel**: Connect your repo and set build directory to `frontend`
- **GitHub Pages**: Push `frontend` folder to `gh-pages` branch
- **AWS S3 + CloudFront**: Upload to S3 bucket and serve via CloudFront
- **Nginx**: Copy `frontend` folder to `/var/www/html`

### Update API URL for Production

Before deploying, update the default API URL in `frontend/index.html`:

```javascript
// Change from:
value="http://localhost:8000/api/v1"

// To your production URL:
value="https://api.yourdomain.com/api/v1"
```

## Health Check Endpoint

The backend provides a health check endpoint:

```bash
GET /api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "service": "Smart Summary & Insight Service",
  "version": "1.0.0"
}
```

Use this for:
- Load balancer health checks
- Monitoring systems
- Container orchestration (Kubernetes, Docker Swarm)
- CI/CD pipelines

## Monitoring

### Recommended Monitoring

1. **Application Logs**: Monitor FastAPI logs for errors
2. **Health Checks**: Set up periodic health check monitoring
3. **API Metrics**: Track request count, response times, error rates
4. **Token Usage**: Monitor Anthropic API usage and costs

### Example Health Check Script

```bash
#!/bin/bash
# health_check.sh

API_URL="http://localhost:8000/api/v1/health"

response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)

if [ $response -eq 200 ]; then
    echo "✅ Backend is healthy"
    exit 0
else
    echo "❌ Backend health check failed (HTTP $response)"
    exit 1
fi
```

## Security Considerations

1. **API Keys**: Never commit `.env` files
2. **CORS**: Configure CORS appropriately for production
3. **Rate Limiting**: Add rate limiting middleware
4. **Authentication**: Add API key or OAuth authentication
5. **HTTPS**: Always use HTTPS in production
6. **Input Validation**: Already handled by Pydantic models

## Scaling

### Horizontal Scaling

- Use a load balancer (nginx, HAProxy) in front of multiple backend instances
- Use Redis for distributed caching instead of in-memory cache
- Consider using a message queue (RabbitMQ, Redis) for async processing

### Vertical Scaling

- Increase `workers` in Gunicorn config
- Adjust `max_tokens` and `temperature` for performance
- Use faster models (Sonnet instead of Haiku) if budget allows

