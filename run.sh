#!/bin/bash

echo "Starting MyFigPoint Application..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Initialize database if it doesn't exist
if [ ! -f "myfigpoint.db" ]; then
    echo "Initializing database..."
    python init_db.py
fi

# Run the application
echo "Starting the application..."
python run.py