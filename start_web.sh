#!/bin/bash

# Start the Value Agent Web Interface
echo "🚀 Starting Value Agent Web Interface..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run 'python3 -m venv .venv' first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Install web dependencies if not already installed
echo "📦 Installing web dependencies..."
pip install -r web_requirements.txt

# Start the Flask app
echo "🌐 Starting Flask server on port 5001..."
python web_app.py
echo ""
echo "✅ Web interface started successfully!"
echo "🌐 Open your browser to: http://localhost:5001"
echo "🛑 Press Ctrl+C to stop the server"
