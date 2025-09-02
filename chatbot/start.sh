#!/bin/bash

# Chatbot API Startup Script

echo "🤖 Starting Chatbot API Server..."
echo "================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data
echo "✅ Created data directory"

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed"
else
    echo "⚠️  requirements.txt not found, skipping dependency installation"
fi

# Check if config.json exists, create default if not
if [ ! -f "config.json" ]; then
    echo "⚠️  config.json not found, will use default configuration"
fi

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development

# Start the server
echo "🚀 Starting server..."
echo "📍 Server will be available at: http://localhost:5002"
echo "📖 API documentation: http://localhost:5002"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py