"""
Execution engine - runs plans step-by-step with progress tracking and recovery.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from app.services.tools import read_file, write_file, create_file, search_project, ToolResult
from app.services.inference import chat
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    step_id: int
    status: StepStatus
    description: str
    file: str
    result: str = ""
    error: str = ""


@dataclass
class ExecutionState:
    plan_id: str
    goal: str
    steps: list[StepResult]
    current_step: int
    status: str  # pending, running, paused, complete, failed
    started_at: float = 0.0
    workspace_path: str = ""


# In-memory store
_executions: dict[str, ExecutionState] = {}


def start_execution(plan_id: str, steps: list[dict], workspace_path: str, goal: str) -> str:
    """Initialize execution of a plan."""
    exec_id = str(len(_executions) + 1)
    step_results = [
        StepResult(
            step_id=s["id"],
            status=StepStatus.PENDING,
            description=s.get("description", ""),
            file=s.get("file", ""),
        )
        for s in steps
    ]
    _executions[exec_id] = ExecutionState(
        plan_id=plan_id,
        goal=goal,
        steps=step_results,
        current_step=0,
        status="running",
        started_at=time.time(),
        workspace_path=workspace_path,
    )
    logger.info(f"Execution started: {exec_id}, {len(steps)} steps")
    return exec_id


def execute_next_step(exec_id: str) -> StepResult:
    """Execute the next pending step."""
    state = _executions.get(exec_id)
    if not state:
        raise ValueError(f"Execution not found: {exec_id}")
    
    if state.status == "paused":
        raise RuntimeError("Execution is paused")
    
    # Find next pending step
    pending = [s for s in state.steps if s.status == StepStatus.PENDING]
    if not pending:
        state.status = "complete"
        logger.info(f"Execution complete: {exec_id}")
        return StepResult(step_id=-1, status=StepStatus.COMPLETE, description="All steps complete", file="")
    
    step = pending[0]
    step.status = StepStatus.RUNNING
    state.current_step = step.step_id
    
    try:
        logger.info(f"Executing step {step.step_id}: {step.description}")
        
        # Read the file first
        if step.file and step.file != "unknown":
            result = read_file(step.file, state.workspace_path)
            current_content = result.content if result.success else ""
        else:
            current_content = ""
        
        # Ask AI to perform the step
        prompt = f"""
You are executing a step in a coding plan.

GOAL: {state.goal}
CURRENT STEP: {step.description}
FILE: {step.file}
CURRENT FILE CONTENT:{current_content[:3000]}


Return ONLY the new file content or code to write.
If creating a new file, return the full file content.
If modifying an existing file, return the complete modified file.
Do NOT include explanations. Return ONLY code.
"""
        
        result = chat(message=prompt, temperature=0.2, max_tokens=2000)
        new_content = result.text.strip()
        
        # Extract code block if present
        if "```" in new_content:
            code_match = new_content.split("```")[1]
            if code_match.startswith(("python", "javascript", "typescript", "js", "ts", "go", "rust")):
                new_content = "\n".join(code_match.split("\n")[1:])
        
        step.result = new_content[:500]
        step.status = StepStatus.COMPLETE
        logger.info(f"Step {step.step_id} complete")
        
    except Exception as e:
        step.status = StepStatus.FAILED
        step.error = str(e)
        logger.error(f"Step {step.step_id} failed: {e}")
    
    return step


def get_execution_status(exec_id: str) -> dict:
    """Get current execution status."""
    state = _executions.get(exec_id)
    if not state:
        return {"error": "Execution not found"}
    
    completed = sum(1 for s in state.steps if s.status == StepStatus.COMPLETE)
    failed = sum(1 for s in state.steps if s.status == StepStatus.FAILED)
    
    return {
        "exec_id": exec_id,
        "goal": state.goal,
        "status": state.status,
        "current_step": state.current_step,
        "total_steps": len(state.steps),
        "completed": completed,
        "failed": failed,
        "pending": len(state.steps) - completed - failed,
        "steps": [
            {"id": s.step_id, "status": s.status.value, "description": s.description, "file": s.file}
            for s in state.steps
        ],
    }


def pause_execution(exec_id: str) -> dict:
    """Pause an execution."""
    state = _executions.get(exec_id)
    if state:
        state.status = "paused"
        return {"status": "paused"}
    return {"error": "Not found"}


def resume_execution(exec_id: str) -> dict:
    """Resume a paused execution."""
    state = _executions.get(exec_id)
    if state:
        state.status = "running"
        return {"status": "running"}
    return {"error": "Not found"}