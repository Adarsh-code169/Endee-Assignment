#!/bin/bash

# Start FastAPI and Streamlit
echo "Starting FastAPI on port ${PORT:-8000} and Streamlit on 8501..."
PORT=${PORT:-8000}
uvicorn backend.main:app --host 0.0.0.0 --port $PORT &
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
