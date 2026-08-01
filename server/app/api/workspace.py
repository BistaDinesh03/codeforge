"""
Workspace intelligence API - project structure, symbols, dependencies.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

from app.services.symbol_index import build_workspace_index, find_symbol
from app.services.dependency_graph import build_dependency_graph, get_impact_report
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/workspace", tags=["workspace"])


class WorkspaceRequest(BaseModel):
    path: str


class SymbolInfo(BaseModel):
    name: str
    kind: str
    file: str
    line: int


class WorkspaceSummary(BaseModel):
    files: int
    symbols: int
    languages: dict


@router.post("/summary")
async def summary(request: WorkspaceRequest):
    """Get a summary of the workspace structure."""
    try:
        index = build_workspace_index(request.path)
        return {
            "files": len(index.files),
            "symbols": index.total_symbols,
            "languages": index.languages,
            "functions": len([s for s in index.symbols if s.kind == "function"]),
            "classes": len([s for s in index.symbols if s.kind == "class"]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/symbols")
async def symbols(request: WorkspaceRequest):
    """Get all symbols in the workspace."""
    try:
        index = build_workspace_index(request.path)
        return {
            "total": index.total_symbols,
            "symbols": [
                {"name": s.name, "kind": s.kind, "file": s.file, "line": s.line}
                for s in index.symbols[:200]  # Limit to 200
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dependencies")
async def dependencies(request: WorkspaceRequest):
    """Get dependency graph."""
    try:
        graph = build_dependency_graph(request.path)
        return {
            "files": len(graph),
            "total_edges": sum(len(deps) for deps in graph.values()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/impact")
async def impact(file: str, path: str):
    """Check impact of changing a file."""
    try:
        graph = build_dependency_graph(path)
        report = get_impact_report(graph, file)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))