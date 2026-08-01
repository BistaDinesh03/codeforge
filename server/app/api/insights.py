"""Insights API - health, risks, personality, awards, stories, code map."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.code_metrics import analyze_project
from app.services.personality import analyze_file_personality, get_all_personalities
from app.services.story_generator import get_file_story, get_project_awards
from app.services.dependency_graph import build_dependency_graph, get_impact_report
from app.services.symbol_index import build_workspace_index
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/insights", tags=["insights"])


class AnalyzeRequest(BaseModel):
    workspace_path: str


@router.post("/health")
async def health(request: AnalyzeRequest):
    try: return analyze_project(request.workspace_path)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.post("/risks")
async def risks(request: AnalyzeRequest):
    return {"risks": analyze_project(request.workspace_path)["risks"]}


@router.post("/personalities")
async def personalities(request: AnalyzeRequest):
    try: return get_all_personalities(request.workspace_path)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.post("/story/{filepath:path}")
async def story(filepath: str, workspace_path: str):
    try: return get_file_story(filepath, workspace_path)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.post("/awards")
async def awards(request: AnalyzeRequest):
    try: return get_project_awards(request.workspace_path)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.post("/map")
async def code_map(request: AnalyzeRequest):
    """Build an interactive code map."""
    try:
        index = build_workspace_index(request.workspace_path)
        graph = build_dependency_graph(request.workspace_path)
        
        # Group files by folder
        folders = {}
        for f in index.files:
            folder = str(f).split("/")[0] if "/" in str(f) else "root"
            if folder not in folders: folders[folder] = []
            folders[folder].append(str(f))
        
        # Find top connections
        connections = []
        for file, deps in list(graph.items())[:50]:
            for dep in deps[:5]:
                connections.append({"from": file, "to": dep})
        
        return {
            "folders": [{"name": k, "files": v[:20], "count": len(v)} for k, v in folders.items()],
            "connections": connections[:30],
            "total_files": len(index.files),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explore/{filepath:path}")
async def explore_file(filepath: str, workspace_path: str):
    """Explore a file's dependencies."""
    try:
        graph = build_dependency_graph(workspace_path)
        deps = graph.get(filepath, [])
        impact = get_impact_report(graph, filepath)
        index = build_workspace_index(workspace_path)
        symbols = [s for s in index.symbols if s.file == filepath][:20]
        
        return {
            "file": filepath,
            "imports": deps,
            "imported_by": impact["affected_files"][:10],
            "imported_by_count": impact["imported_by"],
            "symbols": [{"name": s.name, "kind": s.kind, "line": s.line} for s in symbols],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))