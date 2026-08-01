"""
Review API - approve/reject changes with diff preview.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.review import (
    create_review, get_review, approve_change, approve_all,
    reject_change, reject_all,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/review", tags=["review"])


class CreateReviewRequest(BaseModel):
    exec_id: str
    changes: list[dict]


class ApproveRequest(BaseModel):
    review_id: str
    filepath: str
    workspace_path: str


class ApproveAllRequest(BaseModel):
    review_id: str
    workspace_path: str


class RejectRequest(BaseModel):
    review_id: str
    filepath: str


@router.post("/create")
async def create(request: CreateReviewRequest):
    review_id = create_review(request.exec_id, request.changes)
    return {"review_id": review_id}


@router.get("/{review_id}")
async def get(review_id: str):
    return get_review(review_id)


@router.post("/approve")
async def approve(request: ApproveRequest):
    return approve_change(request.review_id, request.filepath, request.workspace_path)


@router.post("/approve-all")
async def approve_all_changes(request: ApproveAllRequest):
    return approve_all(request.review_id, request.workspace_path)


@router.post("/reject")
async def reject(request: RejectRequest):
    return reject_change(request.review_id, request.filepath)


@router.post("/reject-all/{review_id}")
async def reject_all_changes(review_id: str):
    return reject_all(review_id)