"""
Insights API - project health, risks, personality, awards.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.code_metrics import analyze_project
from app.services.project_scanner import scan_project
from app.services.symbol_index import build_workspace_index
from app.services.dependency_graph import build_dependency_graph
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/insights", tags=["insights"])


class AnalyzeRequest(BaseModel):
    workspace_path: str


@router.post("/health")
async def health(request: AnalyzeRequest):
    """Get project health scores."""
    try:
        return analyze_project(request.workspace_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risks")
async def risks(request: AnalyzeRequest):
    """Get top project risks."""
    data = analyze_project(request.workspace_path)
    return {"risks": data["risks"]}


@router.post("/awards")
async def awards(request: AnalyzeRequest):
    """Generate fun awards based on metrics."""
    data = analyze_project(request.workspace_path)
    files = scan_project(request.workspace_path)
    index = build_workspace_index(request.workspace_path)
    
    award_list = []
    
    # Longest file
    largest = sorted(data["largest_files"], key=lambda x: x["lines"], reverse=True)
    if largest:
        award_list.append({"award": "Biggest File", "file": largest[0]["file"], "detail": f"{largest[0]['lines']} lines of pure dedication"})
    
    # Most TODOs
    todo_counts = {}
    for f in files:
        count = f.content.upper().count("TODO")
        if count > 0:
            todo_counts[f.relative_path] = count
        f.unload_content()
    if todo_counts:
        worst = max(todo_counts, key=todo_counts.get)
        award_list.append({"award": "Most TODOs", "file": worst, "detail": f"{todo_counts[worst]} TODOs — the procrastination champion"})
    
    # Oldest file (by git)
    award_list.append({"award": "Most Functions", "file": f"{data['total_functions']} functions", "detail": "across the entire project"})
    
    return {"awards": award_list}


@router.post("/personality/{filepath:path}")
async def personality(filepath: str, workspace_path: str):
    """Get personality for a specific file."""
    try:
        from pathlib import Path
        full_path = Path(workspace_path) / filepath
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        content = full_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")
        functions = len([l for l in lines if l.strip().startswith(("def ", "function ", "class "))])
        imports = len([l for l in lines if l.strip().startswith(("import ", "from ", "require("))])
        todos = content.upper().count("TODO")
        
        # Determine personality
        if len(lines) > 500 and functions > 20:
            persona = "The Overworked Employee"
            desc = f"I handle {functions} functions across {len(lines)} lines. Please split me up."
        elif len(lines) > 1000:
            persona = "The Monster File"
            desc = f"{len(lines)} lines. Even I'm scared of myself."
        elif imports > 10:
            persona = "The Social Butterfly"
            desc = f"I import {imports} things. I know everyone."
        elif todos > 5:
            persona = "The Procrastinator"
            desc = f"{todos} TODOs. I'll fix them tomorrow."
        elif functions == 0:
            persona = "The Configuration File"
            desc = "I don't do much, but everyone needs me."
        else:
            persona = "The Quiet Hero"
            desc = f"I do my job with {len(lines)} lines. No drama."
        
        return {
            "file": filepath,
            "personality": persona,
            "description": desc,
            "lines": len(lines),
            "functions": functions,
            "imports": imports,
            "todos": todos,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))