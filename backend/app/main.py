"""
Main FastAPI application for CodeForge backend.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CodeForge Backend",
    description="AI coding server running on Android via Termux",
    version="0.0.1",
)

# Allow CORS for VS Code extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""
    response: str


@app.get("/health")
async def health_check():
    """Health check endpoint to verify server is running."""
    return {"status": "healthy", "version": "0.0.1"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint.
    Receives a message from the VS Code extension and returns a response.
    Currently returns an echo until llama.cpp is connected.
    """
    logger.info(f"Received message: {request.message}")

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # TODO: Replace with actual llama.cpp inference
    response_text = f"[Echo] You said: {request.message}"

    return ChatResponse(response=response_text)


@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "name": "CodeForge Backend",
        "message": "AI coding server is running",
    }