"""Insights API - health, risks, personality, awards, stories."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.code_metrics import analyze_project
from app.services.personality import analyze_file_personality, get_all_personalities
from app.services.story_generator import get_file_story, get_project_awards
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