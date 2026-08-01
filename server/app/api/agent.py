"""
Agent API - planning and execution endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.planner import create_plan, format_plan_for_display
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])


class PlanRequest(BaseModel):
    goal: str
    workspace_path: str


class PlanResponse(BaseModel):
    goal: str
    summary: str
    risk_level: str
    affected_files: list[str]
    estimated_steps: int
    steps: list[dict]
    formatted_plan: str


# Store plans in memory (in production, use a database)
_plans: dict[str, dict] = {}


@router.post("/plan", response_model=PlanResponse)
async def plan(request: PlanRequest):
    """Create an execution plan for a goal."""
    if not request.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")
    
    try:
        plan = create_plan(request.goal, request.workspace_path)
        
        # Store plan
        plan_id = str(len(_plans) + 1)
        _plans[plan_id] = {
            "plan": plan,
            "status": "created",
        }
        
        return PlanResponse(
            goal=plan.goal,
            summary=plan.summary,
            risk_level=plan.risk_level,
            affected_files=plan.affected_files,
            estimated_steps=plan.estimated_steps,
            steps=[{
                "id": s.id,
                "action": s.action,
                "file": s.file,
                "description": s.description,
                "risk": s.risk,
            } for s in plan.steps],
            formatted_plan=format_plan_for_display(plan),
        )
    except Exception as e:
        logger.error(f"Plan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans")
async def list_plans():
    """List all created plans."""
    return {
        "total": len(_plans),
        "plans": [
            {"id": pid, "goal": p["plan"].goal, "status": p["status"]}
            for pid, p in _plans.items()
        ],
    }