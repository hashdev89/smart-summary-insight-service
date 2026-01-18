#!/bin/bash
# Simple script to run the Smart Summary & Insight Service

echo "🚀 Starting Smart Summary & Insight Service..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env file with default settings..."
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
    echo "✅ .env file created"
fi

echo ""
echo "✅ Virtual environment activated"
echo "✅ Configuration loaded"
echo ""
echo "🌐 Server starting on http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🎨 Frontend: Open frontend/index.html in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the server
python -m app.main
