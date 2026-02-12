#!/bin/bash
# Start script for production deployment

# Start background collector in background
python -c "from app import start_background_collector; start_background_collector()" &

# Start Flask app with Gunicorn
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120
