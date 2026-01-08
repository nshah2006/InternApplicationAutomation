#!/usr/bin/env python3
"""
Run FastAPI development server.

Usage:
    python run_server.py [--host HOST] [--port PORT]
    
Default: http://localhost:8000
"""

import sys
import argparse
import uvicorn


def main():
    """Run the FastAPI server."""
    parser = argparse.ArgumentParser(description='Run FastAPI development server')
    parser.add_argument('--host', default='localhost', help='Host to bind to (default: localhost)')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to (default: 8000)')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload on code changes')
    
    args = parser.parse_args()
    
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == '__main__':
    main()

