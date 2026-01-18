#!/bin/bash
# Start the Smart Summary & Insight Service

echo "Starting Smart Summary & Insight Service..."
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "✗ Virtual environment not found. Please run: python3 -m venv venv && pip install -r requirements.txt"
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠ Warning: .env file not found. Creating from template..."
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
    echo "✓ .env file created"
fi

echo ""
echo "🚀 Starting server on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "📖 Alternative Docs: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python -m app.main
