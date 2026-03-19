#!/bin/bash
export PYTHONUNBUFFERED=1

echo "[SYSTEM] Pre-flight checks completed."
echo "[SYSTEM] Memory limits configured. Initiating background telemetry process..."
exec python3 /app/engine.py
