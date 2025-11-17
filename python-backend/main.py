from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional
import os
import time
from dotenv import load_dotenv

from models.database import init_db
from routes import projects, chat, files, git
from utils.logger import logger

load_dotenv()

app = FastAPI(title="Novel Writer API", version="1.0.0")

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses with timing"""
    start_time = time.time()

    # Log incoming request
    logger.info(f"Incoming request: {request.method} {request.url.path}")

    # Process request
    try:
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log response
        logger.log_response(
            request.method,
            str(request.url.path),
            response.status_code,
            duration_ms
        )

        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.log_exception(e, {
            "method": request.method,
            "path": str(request.url.path)
        }, "request_handler")
        logger.log_response(
            request.method,
            str(request.url.path),
            500,
            duration_ms,
            str(e)
        )
        raise

# CORS middleware - Allow all localhost variations for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:5173",
        "tauri://localhost",
        "http://localhost",
        "http://127.0.0.1"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Log server startup"""
    logger.info("=" * 60)
    logger.info("NovelWriter Backend Server Starting")
    logger.info(f"Version: 1.0.0")
    logger.info(f"Environment: {os.getenv('ENV', 'development')}")
    logger.info("=" * 60)

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.log_exception(e, operation="database_initialization")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log server shutdown"""
    logger.info("NovelWriter Backend Server Shutting Down")
    logger.info("=" * 60)

# Include routers
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(git.router, prefix="/git", tags=["git"])

logger.info("All routers registered successfully")


@app.get("/")
async def root():
    return {"message": "Novel Writer API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description='Novel Writer Backend Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload (development)')

    args = parser.parse_args()

    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info(f"Auto-reload: {args.reload}")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )
