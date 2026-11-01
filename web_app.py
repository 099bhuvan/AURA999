"""AURA Web Application Server Entrypoint.

Starts high-performance asynchronous FastAPI web server serving the
cinematic AURA command center directly over HTTP/WebSocket.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Ensure root directory is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.web.server import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    host = "0.0.0.0"
    print(f"==========================================================")
    print(f" ◈ Launching AURA Cloud Web Command Center on {host}:{port}")
    print(f"==========================================================")
    uvicorn.run("app.web.server:app", host=host, port=port, reload=False, workers=1)
