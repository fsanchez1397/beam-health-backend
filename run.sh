#!/bin/bash
# Activate virtual environment and run the FastAPI server
# If using uv, activate with: source .venv/bin/activate
# If using traditional venv, activate with: source venv/bin/activate

if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

uvicorn main:app --reload --port 8000

