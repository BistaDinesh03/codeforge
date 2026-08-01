"""
Memory system - stores project conventions, user preferences, and past tasks.
Data saved to ~/.codeforge/memory/ as JSON files.
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

MEMORY_DIR = Path.home() / ".codeforge" / "memory"


@dataclass
class ProjectMemory:
    """Memory for a specific project."""
    project_path: str
    conventions: dict = field(default_factory=dict)
    preferences: dict = field(default_factory=dict)
    past_tasks: list[dict] = field(default_factory=list)
    last_updated: str = ""


def _get_memory_path(project_path: str) -> Path:
    """Get the memory file path for a project."""
    project_hash = str(abs(hash(project_path)))[:12]
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    return MEMORY_DIR / f"{project_hash}.json"


def load_memory(project_path: str) -> ProjectMemory:
    """Load memory for a project."""
    filepath = _get_memory_path(project_path)
    if filepath.exists():
        try:
            data = json.loads(filepath.read_text())
            return ProjectMemory(
                project_path=project_path,
                conventions=data.get("conventions", {}),
                preferences=data.get("preferences", {}),
                past_tasks=data.get("past_tasks", []),
                last_updated=data.get("last_updated", ""),
            )
        except Exception:
            pass
    return ProjectMemory(project_path=project_path)


def save_memory(memory: ProjectMemory) -> None:
    """Save memory for a project."""
    filepath = _get_memory_path(memory.project_path)
    memory.last_updated = time.strftime("%Y-%m-%d %H:%M:%S")
    filepath.write_text(json.dumps({
        "conventions": memory.conventions,
        "preferences": memory.preferences,
        "past_tasks": memory.past_tasks[-50:],  # Keep last 50 tasks
        "last_updated": memory.last_updated,
    }, indent=2))


def remember_convention(project_path: str, key: str, value: str) -> dict:
    """Remember a project convention (e.g., indent=4, quotes=single)."""
    memory = load_memory(project_path)
    memory.conventions[key] = value
    save_memory(memory)
    logger.info(f"Remembered convention: {key}={value}")
    return {"key": key, "value": value}


def remember_preference(project_path: str, key: str, value: str) -> dict:
    """Remember a user preference."""
    memory = load_memory(project_path)
    memory.preferences[key] = value
    save_memory(memory)
    return {"key": key, "value": value}


def remember_task(project_path: str, goal: str, result: str) -> dict:
    """Remember a completed task."""
    memory = load_memory(project_path)
    memory.past_tasks.append({
        "goal": goal,
        "result": result,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_memory(memory)
    return {"goal": goal, "remembered": True}


def get_memory_context(project_path: str) -> str:
    """Get memory as a context string for AI prompts."""
    memory = load_memory(project_path)
    parts = []
    
    if memory.conventions:
        parts.append("Project Conventions:")
        for k, v in memory.conventions.items():
            parts.append(f"  - {k}: {v}")
    
    if memory.preferences:
        parts.append("User Preferences:")
        for k, v in memory.preferences.items():
            parts.append(f"  - {k}: {v}")
    
    if memory.past_tasks:
        parts.append("Recent Tasks:")
        for task in memory.past_tasks[-5:]:
            parts.append(f"  - {task['goal']}")
    
    return "\n".join(parts) if parts else ""


def auto_detect_conventions(project_path: str) -> dict:
    """Auto-detect conventions from project files."""
    from app.services.project_scanner import scan_project
    
    files = scan_project(project_path, load_content=True)
    detected = {}
    
    indent_counts = {"2": 0, "4": 0, "tab": 0}
    quote_counts = {"single": 0, "double": 0}
    
    for f in files[:50]:  # Sample first 50 files
        for line in f.content.split("\n")[:100]:
            # Detect indentation
            if line.startswith("    "):
                indent_counts["4"] += 1
            elif line.startswith("  "):
                indent_counts["2"] += 1
            elif line.startswith("\t"):
                indent_counts["tab"] += 1
            
            # Detect quote style
            if "'" in line:
                quote_counts["single"] += 1
            if '"' in line:
                quote_counts["double"] += 1
        f.unload_content()
    
    # Determine most common
    best_indent = max(indent_counts, key=indent_counts.get)
    if indent_counts[best_indent] > 0:
        detected["indent"] = best_indent
    
    best_quote = max(quote_counts, key=quote_counts.get)
    if quote_counts[best_quote] > 0:
        detected["quotes"] = best_quote
    
    # Save detected conventions
    for k, v in detected.items():
        remember_convention(project_path, k, v)
    
    return detected