"""
Main FastAPI application for CodeForge backend.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from pathlib import Path

from app.services.project_scanner import scan_project
from app.services.bm25_search import BM25Search

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

# Project path - will be configured via extension
PROJECT_ROOT = Path.cwd()


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str
    project_path: str | None = None


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""
    response: str


class SearchRequest(BaseModel):
    """Request body for search endpoint."""
    query: str
    project_path: str | None = None
    top_k: int = 5


class SearchResponse(BaseModel):
    """Response body for search endpoint."""
    results: list[dict]


@app.get("/health")
async def health_check():
    """Health check endpoint to verify server is running."""
    return {"status": "healthy", "version": "0.0.1"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint.
    Receives a message and returns a response.
    Includes relevant project files as context.
    """
    logger.info(f"Received message: {request.message}")

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Determine project path
    project_path = request.project_path or str(PROJECT_ROOT)

    # Search for relevant files
    try:
        files = scan_project(project_path)
        bm25 = BM25Search()
        bm25.build_index(files)
        relevant_files = bm25.search(request.message, top_k=3)
        
        # Build context from relevant files
        context_parts = []
        for file, score in relevant_files:
            context_parts.append(
                f"// File: {file.relative_path} (relevance: {score:.2f})\n"
                f"{file.content[:500]}..."
            )
        
        context = "\n\n".join(context_parts) if context_parts else "No relevant files found."
        
        # TODO: Replace with actual AI response using context
        response_text = (
            f"Found {len(relevant_files)} relevant files:\n\n{context}"
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        response_text = f"[Error scanning project: {str(e)}]"

    return ChatResponse(response=response_text)


@app.post("/search", response_model=SearchResponse)
async def search_project(request: SearchRequest):
    """
    Search endpoint.
    Finds project files relevant to a query.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    project_path = request.project_path or str(PROJECT_ROOT)

    try:
        files = scan_project(project_path)
        bm25 = BM25Search()
        bm25.build_index(files)
        results = bm25.search(request.query, top_k=request.top_k)

        return SearchResponse(
            results=[
                {
                    "path": file.relative_path,
                    "score": round(score, 3),
                    "snippet": file.content[:200]
                }
                for file, score in results
            ]
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "name": "CodeForge Backend",
        "message": "AI coding server is running",
    }