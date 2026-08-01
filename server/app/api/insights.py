"""Insights API - health, risks, personality, awards, story."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.code_metrics import analyze_project
from app.services.personality import analyze_file_personality, get_all_personalities
from app.services.project_scanner import scan_project
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
    data = analyze_project(request.workspace_path)
    return {"risks": data["risks"]}


@router.post("/personality/{filepath:path}")
async def personality(filepath: str, workspace_path: str):
    try:
        return analyze_file_personality(filepath, workspace_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personalities")
async def personalities(request: AnalyzeRequest):
    try:
        return get_all_personalities(request.workspace_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/awards")
async def awards(request: AnalyzeRequest):
    data = analyze_project(request.workspace_path)
    files = scan_project(request.workspace_path)
    award_list = []
    
    largest = sorted(data["largest_files"], key=lambda x: x["lines"], reverse=True)
    if largest:
        award_list.append({"award": "Longest File", "file": largest[0]["file"], "detail": f"{largest[0]['lines']} lines"})
    
    todo_counts = {}
    for f in files:
        c = f.content.upper().count("TODO")
        if c > 0: todo_counts[f.relative_path] = c
        f.unload_content()
    if todo_counts:
        worst = max(todo_counts, key=todo_counts.get)
        award_list.append({"award": "Most TODOs", "file": worst, "detail": f"{todo_counts[worst]} TODOs"})
    
    award_list.append({"award": "Total Functions", "detail": f"{data['total_functions']} across the project"})
    award_list.append({"award": "Total Lines", "detail": f"{data['total_lines']} lines of code"})
    
    return {"awards": award_list}