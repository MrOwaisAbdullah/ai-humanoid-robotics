import json
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the FastAPI app
from main import app

# Vercel entry point handler
def handler(request):
    """
    Vercel serverless function handler
    """
    return app(request.scope, receive, send)

async def receive():
    """ASGI receive callable"""
    return {
        "type": "http.request",
        "body": b"",
        "more_body": False,
    }

async def send(message):
    """ASGI send callable"""
    pass