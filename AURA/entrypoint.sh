#!/bin/bash
set -e

export PORT=${PORT:-10000}
echo "=========================================================="
echo " ◈ Launching AURA Cloud Web Command Center on port $PORT"
echo "=========================================================="
exec python3 web_app.py
