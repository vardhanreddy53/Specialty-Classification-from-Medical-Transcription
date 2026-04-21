#!/bin/bash
cd "$(dirname "$0")/.."
echo "Starting Medical Classifier..."
echo "Loading models into memory, please wait..."

# Activate the virtual environment on Unix/macOS
source venv/bin/activate

# Start the Flask app (which opens the browser automatically)
python3 app.py
