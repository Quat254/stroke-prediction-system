#!/bin/bash

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required to run this application."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create database directory
mkdir -p database

# Run the application
python3 app.py
