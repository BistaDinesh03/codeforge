"""
Planning engine - decomposes user goals into execution plans.
Uses AI to analyze the workspace and create step-by-step plans.
"""

import json
from dataclasses import dataclass, field
from app.services.symbol_index import build_workspace_index
from app.services.dependency_graph import build_dependency_graph, get_impact_report
from app.services.inference import chat
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PlanStep:
    """A single step in an execution plan."""
    id: int
    action: str  # create, modify, delete, test, run
    file: str
    description: str
    risk: str  # low, medium, high
    dependencies: list[str] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    """A complete plan for achieving a goal."""
    goal: str
    summary: str
    steps: list[PlanStep]
    affected_files: list[str]
    estimated_steps: int
    risk_level: str
    workspace_summary: dict = field(default_factory=dict)


def create_plan(goal: str, workspace_path: str) -> ExecutionPlan:
    """
    Create an execution plan for a user goal.
    
    1. Analyze workspace structure
    2. Ask AI to decompose the goal
    3. Return structured plan
    """
    # Gather workspace context
    index = build_workspace_index(workspace_path)
    graph = build_dependency_graph(workspace_path)
    
    # Build context for AI
    context = f"""
You are an expert software architect. Given a user's goal and their project structure,
create a detailed step-by-step execution plan.

PROJECT STRUCTURE:
- Files: {len(index.files)}
- Languages: {index.languages}
- Functions: {len([s for s in index.symbols if s.kind == 'function'])}
- Classes: {len([s for s in index.symbols if s.kind == 'class'])}
- Key files: {', '.join(index.files[:15])}

USER GOAL: {goal}

Return ONLY a JSON object with this exact structure:
{{
    "summary": "Brief 1-sentence summary",
    "risk_level": "low/medium/high",
    "steps": [
        {{
            "action": "create/modify/delete/test/run",
            "file": "path/to/file",
            "description": "What to do",
            "risk": "low/medium/high"
        }}
    ],
    "affected_files": ["file1", "file2"]
}}

Rules:
- Be specific about file paths
- Order steps logically (create before modify)
- Include testing steps
- Consider dependencies between files
- Keep steps atomic (one clear action per step)
"""
    
    # Ask AI for plan
    try:
        result = chat(message=context, temperature=0.3, max_tokens=1000)
        response_text = result.text.strip()
        
        # Extract JSON from response
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            plan_data = json.loads(response_text[json_start:json_end])
        else:
            raise ValueError("No JSON found in AI response")
        
        # Build plan
        steps = []
        for i, step_data in enumerate(plan_data.get("steps", []), 1):
            steps.append(PlanStep(
                id=i,
                action=step_data.get("action", "modify"),
                file=step_data.get("file", "unknown"),
                description=step_data.get("description", ""),
                risk=step_data.get("risk", "low"),
            ))
        
        plan = ExecutionPlan(
            goal=goal,
            summary=plan_data.get("summary", ""),
            steps=steps,
            affected_files=plan_data.get("affected_files", []),
            estimated_steps=len(steps),
            risk_level=plan_data.get("risk_level", "medium"),
            workspace_summary={
                "files": len(index.files),
                "symbols": index.total_symbols,
                "languages": index.languages,
            },
        )
        
        logger.info(f"Plan created: {plan.estimated_steps} steps, risk={plan.risk_level}")
        return plan
        
    except Exception as e:
        logger.error(f"Planning failed: {e}")
        raise


def format_plan_for_display(plan: ExecutionPlan) -> str:
    """Format a plan as human-readable text."""
    lines = [
        f"Goal: {plan.goal}",
        f"Summary: {plan.summary}",
        f"Risk Level: {plan.risk_level.upper()}",
        f"Affected Files: {len(plan.affected_files)}",
        f"Steps: {plan.estimated_steps}",
        "",
        "Steps:",
    ]
    for step in plan.steps:
        icon = {"create": "➕", "modify": "✏️", "delete": "🗑️", "test": "🧪", "run": "▶️"}.get(step.action, "📝")
        lines.append(f"  {icon} [{step.risk.upper()}] {step.file}: {step.description}")
    
    return "\n".join(lines)