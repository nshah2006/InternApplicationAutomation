"""
FastAPI application main entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import resume, form_schema, mapping, preview, ai_generation, github, admin
from app.db.database import engine, Base
from app.core.logging_config import setup_logging
from app.middleware.logging_middleware import LoggingMiddleware

# Initialize structured logging
setup_logging()

# Create database tables on startup
# TODO: Remove this in production - use migrations instead
# Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Resume Application Automation API",
    description="API for resume parsing, form schema extraction, and field mapping",
    version="1.0.0"
)

# Add logging middleware (must be before CORS)
app.add_middleware(LoggingMiddleware)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure specific origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(resume.router)
app.include_router(form_schema.router)
app.include_router(mapping.router)
app.include_router(preview.router)
app.include_router(ai_generation.router)
app.include_router(github.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Resume Application Automation API",
        "version": "1.0.0",
        "endpoints": {
            "upload_resume": "POST /upload-resume",
            "extract_form_schema": "POST /extract-form-schema",
            "mapping_review": "GET /mapping-review",
            "preview_autofill": "POST /preview/autofill",
            "ai_generate_text": "POST /ai-generation/generate",
            "ai_approve": "POST /ai-generation/approve",
            "ai_history": "GET /ai-generation/history/{resume_id}"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

