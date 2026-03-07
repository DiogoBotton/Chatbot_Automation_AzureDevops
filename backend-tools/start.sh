#!/bin/bash
set -e

echo "🚀 Iniciando aplicação FastAPI..."
exec uv run uvicorn main:app --host 0.0.0.0 --port 5000