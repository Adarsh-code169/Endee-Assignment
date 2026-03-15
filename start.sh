#!/bin/bash

# Start Endee in the background
echo "Starting Endee Vector Database..."
BINARY=$(find /app/endee/build -name 'ndd-*' -type f | head -n 1)
NDD_DATA_DIR=/app/data $BINARY &

# Wait for Endee to be ready
echo "Waiting for Endee to start..."
sleep 5

# Start FastAPI and Streamlit
echo "Starting FastAPI and Streamlit..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
