#!/bin/bash
# Simple run script for the service

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the service
python -m app.main

