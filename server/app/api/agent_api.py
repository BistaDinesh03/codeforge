"""
Unified Agent API - complete task lifecycle: plan, execute, review, checkpoint.
Replaces agent.py, tools_api.py, review_api.py, safety.py endpoints.
"""

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.planner import create_plan
from app.services.executor import start_execution, execute_next_step, get_execution_status
from app.services.review import create_review, get_review, approve_all
from app.services.safety import create_checkpoint, rollback_to_checkpoint
from app.services.tools import read_file, search_project
from app.services.memory import get_memory_context, remember_task
from app.services.symbol_index import build_workspace_index
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])

# In-memory task store
_tasks: dict[str, dict] = {}


class TaskRequest(BaseModel):
    goal: str
    workspace_path: str


class TaskStatus(BaseModel):
    task_id: str
    goal: str
    status: str  # analyzing, planning, awaiting_approval, executing, validating, review, complete, failed
    progress: str = ""
    plan: dict | None = None
    steps: list[dict] = []
    current_step: int = 0


@router.post("/task")
async def create_task(request: TaskRequest):
    """Create a new agent task. Returns plan for approval."""
    if not request.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")
    
    task_id = str(len(_tasks) + 1)
    
    try:
        # Step 1: Analyze workspace
        _tasks[task_id] = {"status": "analyzing", "goal": request.goal}
        index = build_workspace_index(request.workspace_path)
        memory_ctx = get_memory_context(request.workspace_path)
        
        # Step 2: Create plan
        _tasks[task_id]["status"] = "planning"
        plan = create_plan(request.goal, request.workspace_path)
        
        # Store task
        _tasks[task_id] = {
            "goal": request.goal,
            "status": "awaiting_approval",
            "plan": {
                "summary": plan.summary,
                "risk_level": plan.risk_level,
                "affected_files": plan.affected_files,
                "steps": [{"id": s.id, "action": s.action, "file": s.file, "description": s.description, "risk": s.risk} for s in plan.steps],
            },
            "workspace_path": request.workspace_path,
            "workspace_summary": {
                "files": index.total_symbols if hasattr(index, 'total_symbols') else len(index.files),
                "languages": index.languages if hasattr(index, 'languages') else {},
            },
            "memory_context": memory_ctx,
        }
        
        return {"task_id": task_id, "status": "awaiting_approval", "plan": _tasks[task_id]["plan"]}
        
    except Exception as e:
        _tasks[task_id]["status"] = "failed"
        logger.error(f"Task creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}")
async def get_task(task_id: str):
    """Get task status and details."""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, **task}


@router.post("/task/{task_id}/approve")
async def approve_task(task_id: str):
    """Approve the plan and start execution."""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != "awaiting_approval":
        raise HTTPException(status_code=400, detail=f"Task is {task['status']}, not awaiting approval")
    
    try:
        # Create checkpoint before execution
        tag = create_checkpoint(task["workspace_path"], task["goal"][:50])
        
        # Start execution
        exec_id = start_execution(task_id, task["plan"]["steps"], task["workspace_path"], task["goal"])
        task["status"] = "executing"
        task["exec_id"] = exec_id
        task["checkpoint_tag"] = tag
        
        # Execute first step
        step = execute_next_step(exec_id)
        task["current_step"] = step.step_id
        task["steps"] = [{"id": step.step_id, "status": step.status.value, "description": step.description}]
        
        return {"task_id": task_id, "status": "executing", "current_step": step.step_id, "checkpoint": tag}
        
    except Exception as e:
        task["status"] = "failed"
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{task_id}/next")
async def next_step(task_id: str):
    """Execute the next step."""
    task = _tasks.get(task_id)
    if not task or "exec_id" not in task:
        raise HTTPException(status_code=404, detail="Task not executing")
    
    step = execute_next_step(task["exec_id"])
    task["current_step"] = step.step_id
    task["steps"].append({"id": step.step_id, "status": step.status.value, "description": step.description})
    
    # Check if all steps complete
    status = get_execution_status(task["exec_id"])
    if status.get("status") == "complete":
        task["status"] = "review"
        # Create review
        review_id = create_review(task["exec_id"], task["steps"])
        task["review_id"] = review_id
        # Remember task
        remember_task(task["workspace_path"], task["goal"], "completed")
    
    return {"task_id": task_id, "step": step.step_id, "status": step.status.value}


@router.post("/task/{task_id}/pause")
async def pause_task(task_id: str):
    task = _tasks.get(task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "paused"
    return {"task_id": task_id, "status": "paused"}


@router.post("/task/{task_id}/resume")
async def resume_task(task_id: str):
    task = _tasks.get(task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "executing"
    return {"task_id": task_id, "status": "executing"}


@router.post("/task/{task_id}/review")
async def review_task(task_id: str):
    """Get review for completed task."""
    task = _tasks.get(task_id)
    if not task or "review_id" not in task:
        raise HTTPException(status_code=404, detail="No review available")
    return get_review(task["review_id"])


@router.post("/task/{task_id}/apply")
async def apply_task(task_id: str):
    """Apply all approved changes."""
    task = _tasks.get(task_id)
    if not task or "review_id" not in task:
        raise HTTPException(status_code=404, detail="No review to apply")
    result = approve_all(task["review_id"], task["workspace_path"])
    task["status"] = "complete"
    return {"task_id": task_id, "status": "complete", "applied": result["applied"]}


@router.post("/task/{task_id}/rollback")
async def rollback_task(task_id: str):
    """Rollback to checkpoint."""
    task = _tasks.get(task_id)
    if not task or "checkpoint_tag" not in task:
        raise HTTPException(status_code=404, detail="No checkpoint available")
    result = rollback_to_checkpoint(task["workspace_path"], task["checkpoint_tag"])
    task["status"] = "rolled_back"
    return result


@router.get("/tasks")
async def list_tasks():
    """List all tasks."""
    return {
        "total": len(_tasks),
        "tasks": [{"task_id": tid, "goal": t["goal"], "status": t["status"]} for tid, t in _tasks.items()],
    }