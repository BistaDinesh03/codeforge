"""
Project indexing and context API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.project_scanner import scan_project, get_project_summary
from app.services.bm25_search import get_search_engine, invalidate_cache
from app.services.context_builder import build_context, ContextResult
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/project", tags=["project"])


class ScanRequest(BaseModel):
    """Request to scan a project directory."""
    path: str = Field(..., description="Absolute path to project root")


class SearchRequest(BaseModel):
    """Request to search project files."""
    query: str = Field(..., min_length=1, description="Search query")
    path: str = Field(..., description="Project root path")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")


class ContextRequest(BaseModel):
    """Request for context-aware search."""
    query: str = Field(..., min_length=1, description="User's question")
    path: str = Field(..., description="Project root path")


@router.post("/scan")
async def scan(request: ScanRequest):
    """Scan a project directory and return summary."""
    try:
        summary = get_project_summary(request.path)
        return {
            "status": "success",
            "project": summary,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search(request: SearchRequest):
    """Search project files by query."""
    try:
        engine = get_search_engine(request.path)
        results = engine.search(request.query, top_k=request.top_k)
        
        return {
            "status": "success",
            "query": request.query,
            "results": [
                {
                    "path": file.relative_path,
                    "score": round(score, 2),
                    "language": file.extension.lstrip("."),
                    "snippet": file.content[:200] + "..." if len(file.content) > 200 else file.content,
                }
                for file, score in results
            ],
            "index_stats": engine.stats,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/context")
async def context(request: ContextRequest):
    """Get relevant files and build context for AI."""
    try:
        result = build_context(
            query=request.query,
            project_path=request.path,
        )
        
        return {
            "status": "success",
            **result.to_dict(),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/reindex")
async def reindex(request: ScanRequest):
    """Force rebuild the search index."""
    try:
        invalidate_cache(request.path)
        engine = get_search_engine(request.path, force_rebuild=True)
        
        return {
            "status": "success",
            "message": "Index rebuilt",
            "stats": engine.stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))