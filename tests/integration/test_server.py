#!/usr/bin/env python3
"""
Test server for MultiCardz™ drag-drop system.
Run with: python test_server.py
"""

import uvicorn
from apps.user.main import create_app

if __name__ == "__main__":
    app = create_app()
    print("🚀 Starting MultiCardz™ Test Server")
    print("📍 Open http://localhost:8001 to test the drag-drop system")
    print("📍 API health check: http://localhost:8001/api/v2/health")
    print("📍 Press Ctrl+C to stop")

    uvicorn.run(app, host="127.0.0.1", port=8001, reload=False, log_level="info")