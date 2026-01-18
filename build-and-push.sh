#!/bin/bash

# Docker Build & Push Script
# Usage: ./build-and-push.sh [tag]
# Example: ./build-and-push.sh latest
# Example: ./build-and-push.sh v1.0.0

IMAGE_NAME="hashdev89/llmassesment"
TAG=${1:-latest}
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐳 Building Docker Image"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Image: ${FULL_IMAGE_NAME}"
echo ""

# Build the image
docker build -t ${FULL_IMAGE_NAME} .

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📤 Pushing to Docker Hub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Push the image
docker push ${FULL_IMAGE_NAME}

if [ $? -ne 0 ]; then
    echo "❌ Push failed! Make sure you're logged in: docker login"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Successfully pushed: ${FULL_IMAGE_NAME}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To pull and run:"
echo "  docker pull ${FULL_IMAGE_NAME}"
echo "  docker run -d -p 8000:8000 -e ANTHROPIC_API_KEY=your-key ${FULL_IMAGE_NAME}"
