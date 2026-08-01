"""
Tool system - gives the AI ability to read, write, search, and run commands.
All destructive actions require explicit user approval.
"""

import os
import re
import subprocess
from pathlib import Path
from dataclasses import dataclass
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    action: str
    message: str
    content: str = ""
    requires_approval: bool = False


def read_file(filepath: str, base_path: str) -> ToolResult:
    """Read a file's contents."""
    full_path = Path(base_path) / filepath
    if not full_path.exists():
        return ToolResult(success=False, action="read", message=f"File not found: {filepath}")
    try:
        content = full_path.read_text(encoding="utf-8", errors="ignore")
        return ToolResult(success=True, action="read", message=f"Read {len(content)} chars", content=content)
    except Exception as e:
        return ToolResult(success=False, action="read", message=str(e))


def write_file(filepath: str, content: str, base_path: str, approved: bool = False) -> ToolResult:
    """Write content to a file. Requires approval."""
    if not approved:
        return ToolResult(success=False, action="write", message="Approval required", requires_approval=True)
    full_path = Path(base_path) / filepath
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return ToolResult(success=True, action="write", message=f"Written {len(content)} chars to {filepath}")
    except Exception as e:
        return ToolResult(success=False, action="write", message=str(e))


def create_file(filepath: str, content: str, base_path: str, approved: bool = False) -> ToolResult:
    """Create a new file. Requires approval."""
    return write_file(filepath, content, base_path, approved)


def delete_file(filepath: str, base_path: str, approved: bool = False) -> ToolResult:
    """Delete a file. Requires explicit approval."""
    if not approved:
        return ToolResult(success=False, action="delete", message="Approval required", requires_approval=True)
    full_path = Path(base_path) / filepath
    try:
        if full_path.exists():
            full_path.unlink()
            return ToolResult(success=True, action="delete", message=f"Deleted {filepath}")
        return ToolResult(success=False, action="delete", message=f"File not found: {filepath}")
    except Exception as e:
        return ToolResult(success=False, action="delete", message=str(e))


def replace_text(filepath: str, old_text: str, new_text: str, base_path: str, approved: bool = False) -> ToolResult:
    """Replace text in a file. Requires approval."""
    if not approved:
        return ToolResult(success=False, action="replace", message="Approval required", requires_approval=True)
    full_path = Path(base_path) / filepath
    try:
        content = full_path.read_text(encoding="utf-8")
        if old_text not in content:
            return ToolResult(success=False, action="replace", message="Text not found in file")
        new_content = content.replace(old_text, new_text)
        full_path.write_text(new_content, encoding="utf-8")
        return ToolResult(success=True, action="replace", message=f"Replaced text in {filepath}")
    except Exception as e:
        return ToolResult(success=False, action="replace", message=str(e))


def search_project(query: str, base_path: str) -> ToolResult:
    """Search for text across the project."""
    results = []
    base = Path(base_path)
    for filepath in base.rglob("*"):
        if filepath.is_file() and filepath.suffix in {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".html", ".css", ".json", ".yaml", ".md"}:
            if any(skip in filepath.parts for skip in {"node_modules", ".git", "__pycache__", "venv", "dist"}):
                continue
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                if query.lower() in content.lower():
                    # Find line numbers
                    lines = content.split("\n")
                    matching_lines = [i+1 for i, line in enumerate(lines) if query.lower() in line.lower()]
                    results.append({
                        "file": str(filepath.relative_to(base)),
                        "matches": len(matching_lines),
                        "lines": matching_lines[:5],
                    })
            except Exception:
                continue
    
    return ToolResult(
        success=True,
        action="search",
        message=f"Found {len(results)} files matching '{query}'",
        content=str(results[:20]),
    )


def run_terminal(command: str, approved: bool = False) -> ToolResult:
    """Run a terminal command. Requires explicit approval."""
    if not approved:
        return ToolResult(success=False, action="terminal", message="Approval required", requires_approval=True)
    
    # Safety: block dangerous commands
    dangerous = ["rm -rf", "sudo", "format", "mkfs", "dd if=", "> /dev/", "fork bomb"]
    if any(d in command.lower() for d in dangerous):
        return ToolResult(success=False, action="terminal", message="Command blocked for safety")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        return ToolResult(
            success=result.returncode == 0,
            action="terminal",
            message=f"Exit code: {result.returncode}",
            content=output[:2000],
        )
    except subprocess.TimeoutExpired:
        return ToolResult(success=False, action="terminal", message="Command timed out")
    except Exception as e:
        return ToolResult(success=False, action="terminal", message=str(e))