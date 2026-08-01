"""
Tools API - file operations and terminal commands.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.tools import (
    read_file, write_file, create_file, delete_file,
    replace_text, search_project, run_terminal, ToolResult,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/tools", tags=["tools"])


class ReadRequest(BaseModel):
    filepath: str
    base_path: str


class WriteRequest(BaseModel):
    filepath: str
    content: str
    base_path: str
    approved: bool = False


class ReplaceRequest(BaseModel):
    filepath: str
    old_text: str
    new_text: str
    base_path: str
    approved: bool = False


class SearchRequest(BaseModel):
    query: str
    base_path: str


class TerminalRequest(BaseModel):
    command: str
    approved: bool = False


@router.post("/read")
async def tool_read(request: ReadRequest):
    result = read_file(request.filepath, request.base_path)
    return {"success": result.success, "message": result.message, "content": result.content[:5000]}


@router.post("/write")
async def tool_write(request: WriteRequest):
    result = write_file(request.filepath, request.content, request.base_path, request.approved)
    if result.requires_approval:
        return {"success": False, "message": "Approval required", "requires_approval": True}
    return {"success": result.success, "message": result.message}


@router.post("/create")
async def tool_create(request: WriteRequest):
    result = create_file(request.filepath, request.content, request.base_path, request.approved)
    return {"success": result.success, "message": result.message, "requires_approval": result.requires_approval}


@router.post("/delete")
async def tool_delete(request: ReadRequest):
    return {"success": False, "message": "Approval required", "requires_approval": True}


@router.post("/replace")
async def tool_replace(request: ReplaceRequest):
    result = replace_text(request.filepath, request.old_text, request.new_text, request.base_path, request.approved)
    return {"success": result.success, "message": result.message, "requires_approval": result.requires_approval}


@router.post("/search")
async def tool_search(request: SearchRequest):
    result = search_project(request.query, request.base_path)
    return {"success": True, "message": result.message, "content": result.content}


@router.post("/terminal")
async def tool_terminal(request: TerminalRequest):
    if not request.approved:
        return {"success": False, "message": "Terminal commands require explicit approval", "requires_approval": True}
    result = run_terminal(request.command, request.approved)
    return {"success": result.success, "message": result.message, "content": result.content}