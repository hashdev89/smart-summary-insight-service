# Docker Build & Push Instructions

## Prerequisites

1. Docker installed on your machine
2. Docker Hub account (hashdev89)
3. Logged into Docker Hub

## Step 1: Login to Docker Hub

```bash
docker login
# Enter your Docker Hub username and password
```

## Step 2: Build the Docker Image

```bash
# Build the image
docker build -t hashdev89/llmassesment:latest .

# Or build with a specific tag
docker build -t hashdev89/llmassesment:v1.0.0 .
```

## Step 3: Test the Image Locally (Optional)

```bash
# Run the container locally
docker run -d \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-api-key-here \
  -e CLAUDE_MODEL=claude-3-5-haiku-20241022 \
  --name llmassesment-test \
  hashdev89/llmassesment:latest

# Check if it's running
curl http://localhost:8000/api/v1/health

# Stop and remove
docker stop llmassesment-test
docker rm llmassesment-test
```

## Step 4: Push to Docker Hub

```bash
# Push latest tag
docker push hashdev89/llmassesment:latest

# Or push with specific tag
docker push hashdev89/llmassesment:v1.0.0

# Push multiple tags
docker tag hashdev89/llmassesment:latest hashdev89/llmassesment:v1.0.0
docker push hashdev89/llmassesment:latest
docker push hashdev89/llmassesment:v1.0.0
```

## Quick Build & Push Script

Create a file `build-and-push.sh`:

```bash
#!/bin/bash

# Set variables
IMAGE_NAME="hashdev89/llmassesment"
TAG=${1:-latest}

echo "Building Docker image: ${IMAGE_NAME}:${TAG}"
docker build -t ${IMAGE_NAME}:${TAG} .

echo "Pushing to Docker Hub: ${IMAGE_NAME}:${TAG}"
docker push ${IMAGE_NAME}:${TAG}

echo "✅ Done! Image pushed: ${IMAGE_NAME}:${TAG}"
```

Make it executable and run:
```bash
chmod +x build-and-push.sh
./build-and-push.sh latest
./build-and-push.sh v1.0.0
```

## Using Docker Compose

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Environment Variables

When running the container, you need to provide:

```bash
docker run -d \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-api-key \
  hashdev89/llmassesment:latest
```

Or use a `.env` file with docker-compose:
```bash
ANTHROPIC_API_KEY=your-api-key-here
CLAUDE_MODEL=claude-3-5-haiku-20241022
MAX_TOKENS=1200
TEMPERATURE=0.3
```

## Pull and Run from Docker Hub

Once pushed, others can pull and run:

```bash
# Pull the image
docker pull hashdev89/llmassesment:latest

# Run it
docker run -d \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-api-key \
  hashdev89/llmassesment:latest
```

## Tags Convention

- `latest` - Most recent stable version
- `v1.0.0` - Specific version
- `v1.0.0-beta` - Beta/development version

## Troubleshooting

### Build fails
- Check Dockerfile syntax
- Ensure all files are in correct locations
- Check .dockerignore isn't excluding needed files

### Push fails
- Verify you're logged in: `docker login`
- Check image name matches your Docker Hub username
- Ensure you have push permissions

### Container won't start
- Check environment variables are set
- View logs: `docker logs <container-name>`
- Check port 8000 isn't already in use


