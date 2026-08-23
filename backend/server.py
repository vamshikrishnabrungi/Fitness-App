"""Supervisor entrypoint shim.

The platform's supervisor runs `uvicorn server:app` from /app/backend. The real
Runlete application lives at backend.app.main. This shim makes /app importable
and re-exports the ASGI app so the managed process serves it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app  # noqa: E402,F401
