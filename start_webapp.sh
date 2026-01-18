#!/bin/bash
# Startup script for Commercial Real Estate Scraper Web App (Mac/Linux)

echo "========================================"
echo "🏢 Starting Web App..."
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Create output directory
mkdir -p output

# Start the app
echo ""
echo "========================================"
echo "✅ Starting server..."
echo "========================================"
echo ""

python app.py
