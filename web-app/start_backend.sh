#!/bin/bash

echo "🚀 Starting Ableton Rack Analyzer Backend..."

# Start Flask backend
cd backend

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate
pip install -r requirements.txt

echo "✅ Starting backend server..."
python app.py
