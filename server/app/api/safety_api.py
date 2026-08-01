"""
Safety API - checkpoints, validation, rollback.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from app.services.safety import (
    create_checkpoint, rollback_to_checkpoint, list_checkpoints,
    validate_action, create_backup, restore_backup,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/safety", tags=["safety"])


class CheckpointRequest(BaseModel):
    workspace_path: str
    label: str = ""


class RollbackRequest(BaseModel):
    workspace_path: str
    tag: str


class ValidateRequest(BaseModel):
    action: str
    filepath: str
    workspace_path: str


@router.post("/checkpoint")
async def checkpoint(request: CheckpointRequest):
    tag = create_checkpoint(request.workspace_path, request.label)
    return {"tag": tag, "created": bool(tag)}


@router.post("/rollback")
async def rollback(request: RollbackRequest):
    return rollback_to_checkpoint(request.workspace_path, request.tag)


@router.get("/checkpoints/{workspace_path}")
async def checkpoints(workspace_path: str):
    tags = list_checkpoints(workspace_path)
    return {"checkpoints": tags}


@router.post("/validate")
async def validate(request: ValidateRequest):
    return validate_action(request.action, request.filepath, request.workspace_path)


@router.post("/backup")
async def backup(request: ValidateRequest):
    path = create_backup(request.filepath, request.workspace_path)
    return {"backup_path": path}