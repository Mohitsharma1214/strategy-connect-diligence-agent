#!/usr/bin/env bash
set -e

# Base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

# Ensure virtual environment python exists
if [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
else
    PYTHON_BIN="python3"
fi

# Configure Ollama environment
export HOME="/tmp"
export OLLAMA_MODELS="/tmp/ollama_models"
export OLLAMA_HOST="http://127.0.0.1:11435"

# Check if Ollama daemon is available; launch background runner if not already active
if command -v ollama >/dev/null 2>&1; then
    if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && ! curl -s http://127.0.0.1:11435/api/tags >/dev/null 2>&1; then
        ollama serve >/dev/null 2>&1 &
        OLLAMA_PID=$!
        sleep 1.5
    fi
fi

# Execute main pipeline with all forwarded arguments
exec "$PYTHON_BIN" main.py "$@"
