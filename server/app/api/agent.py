"""
Agent API - planning, execution, and status endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.planner import create_plan, format_plan_for_display
from app.services.executor import (
    start_execution, execute_next_step, get_execution_status,
    pause_execution, resume_execution,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])


class PlanRequest(BaseModel):
    goal: str
    workspace_path: str


class ExecuteRequest(BaseModel):
    plan_id: str
    steps: list[dict]
    workspace_path: str
    goal: str


_plans: dict[str, dict] = {}


@router.post("/plan")
async def plan(request: PlanRequest):
    if not request.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")
    try:
        plan = create_plan(request.goal, request.workspace_path)
        plan_id = str(len(_plans) + 1)
        _plans[plan_id] = {"plan": plan, "status": "created"}
        return {
            "plan_id": plan_id,
            "goal": plan.goal,
            "summary": plan.summary,
            "risk_level": plan.risk_level,
            "affected_files": plan.affected_files,
            "steps": [{"id":s.id,"action":s.action,"file":s.file,"description":s.description,"risk":s.risk} for s in plan.steps],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute(request: ExecuteRequest):
    try:
        exec_id = start_execution(request.plan_id, request.steps, request.workspace_path, request.goal)
        return {"exec_id": exec_id, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/next")
async def execute_next(exec_id: str):
    try:
        step = execute_next_step(exec_id)
        return {"step": step.step_id, "status": step.status.value, "result": step.result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{exec_id}")
async def status(exec_id: str):
    return get_execution_status(exec_id)


@router.post("/pause/{exec_id}")
async def pause(exec_id: str):
    return pause_execution(exec_id)


@router.post("/resume/{exec_id}")
async def resume(exec_id: str):
    return resume_execution(exec_id)