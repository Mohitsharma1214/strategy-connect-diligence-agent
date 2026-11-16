#!/usr/bin/env bash
set -e

echo "Starting StrategyConnect Diligence Agent Reproduction..."

# Ensure virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install --quiet matplotlib numpy
fi

# Run the complete pipeline
.venv/bin/python main.py
