"""
Hugging Face Spaces Entry Point

This file serves as the entry point for Hugging Face Spaces deployment.
It imports and runs the FastAPI application configured for HF Spaces.
"""

import os

import uvicorn

from app.main import app

if __name__ == "__main__":
    # Hugging Face Spaces configuration
    port = int(os.environ.get("PORT", 7860))
    host = "0.0.0.0"

    print(f"🚀 Starting Farming Assistant API on {host}:{port}")
    print(f"📊 Environment: {'Production' if not os.getenv('DEBUG') else 'Development'}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
