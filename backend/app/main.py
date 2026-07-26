"""
Main FastAPI application for CodeForge backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CodeForge Backend",
    description="AI coding server running on Android via Termux",
    version="0.0.1",
)

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint to verify server is running."""
    return {"status": "healthy", "version": "0.0.1"}


@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "name": "CodeForge Backend",
        "message": "AI coding server is running",
    }