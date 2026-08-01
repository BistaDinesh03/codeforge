"""
Memory API - store and retrieve project knowledge.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from app.services.memory import (
    load_memory, remember_convention, remember_preference,
    remember_task, get_memory_context, auto_detect_conventions,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryRequest(BaseModel):
    project_path: str
    key: str
    value: str = ""


class TaskRequest(BaseModel):
    project_path: str
    goal: str
    result: str = ""


@router.get("/{project_path}")
async def get_memory(project_path: str):
    """Get all memory for a project."""
    memory = load_memory(project_path)
    return {
        "conventions": memory.conventions,
        "preferences": memory.preferences,
        "past_tasks": memory.past_tasks[-10:],
    }


@router.post("/convention")
async def set_convention(request: MemoryRequest):
    return remember_convention(request.project_path, request.key, request.value)


@router.post("/preference")
async def set_preference(request: MemoryRequest):
    return remember_preference(request.project_path, request.key, request.value)


@router.post("/task")
async def set_task(request: TaskRequest):
    return remember_task(request.project_path, request.goal, request.result)


@router.get("/context/{project_path}")
async def context(project_path: str):
    """Get memory as context for AI prompts."""
    context_text = get_memory_context(project_path)
    return {"context": context_text}


@router.post("/detect/{project_path}")
async def detect(project_path: str):
    """Auto-detect project conventions."""
    detected = auto_detect_conventions(project_path)
    return {"detected": detected}