"""
Personality engine - assigns personalities to files based on real metrics.
Every personality is backed by actual code measurements.
"""

from pathlib import Path
from dataclasses import dataclass
from app.services.project_scanner import scan_project
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class FilePersonality:
    file: str
    personality: str
    description: str
    greeting: str
    metrics: dict
    suggestions: list[str]


def analyze_file_personality(filepath: str, workspace_path: str) -> FilePersonality:
    """Assign a personality to a file based on its metrics."""
    full_path = Path(workspace_path) / filepath
    
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    content = full_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.split("\n")
    line_count = len(lines)
    
    # Measure
    functions = sum(1 for l in lines if l.strip().startswith(("def ", "function ", "class ", "async def ", "public ", "private ", "protected ")))
    imports = sum(1 for l in lines if l.strip().startswith(("import ", "from ", "require(", "using ")))
    todos = content.upper().count("TODO") + content.upper().count("FIXME") + content.upper().count("HACK")
    comments = sum(1 for l in lines if l.strip().startswith(("#", "//", "/*", "*", "<!--")))
    empty_lines = sum(1 for l in lines if not l.strip())
    
    comment_ratio = (comments / max(line_count, 1)) * 100
    nesting = max_depth(content)
    
    # Determine personality
    persona, greeting, desc, suggestions = get_persona(
        filepath, line_count, functions, imports, todos, comment_ratio, nesting
    )
    
    return FilePersonality(
        file=filepath,
        personality=persona,
        description=desc,
        greeting=greeting,
        metrics={
            "lines": line_count,
            "functions": functions,
            "imports": imports,
            "todos": todos,
            "comments_pct": round(comment_ratio, 1),
            "max_nesting": nesting,
        },
        suggestions=suggestions,
    )


def max_depth(content: str) -> int:
    """Estimate maximum nesting depth."""
    depth = 0
    current = 0
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.endswith("{") or stripped.endswith(":") and not stripped.startswith(("#", "//")):
            current += 1
            depth = max(depth, current)
        if stripped == "}" or stripped == "end" or stripped == ")":
            current = max(0, current - 1)
    return depth


def get_persona(filepath: str, lines: int, funcs: int, imports: int, todos: int, comments: float, nesting: int):
    """Determine personality from metrics."""
    ext = Path(filepath).suffix.lower()
    name = Path(filepath).stem
    
    # The Monster File
    if lines > 1000:
        return (
            "The Monster File",
            f"Hello. I'm {name}{ext}. I contain {lines} lines. Even I'm scared of myself. Opening me in an editor is an act of courage.",
            f"A massive {lines}-line file that handles way too much. Functions are lost inside me like socks in a dryer.",
            [f"Split into {name}/ folder with separate files by concern", "Extract reusable utilities", "Consider a refactor sprint"],
        )
    
    # The Overworked Employee
    if lines > 400 and funcs > 15:
        return (
            "The Overworked Employee",
            f"I'm {name}{ext}. I handle {funcs} functions across {lines} lines. I haven't taken a vacation since 2022. Please, split me up before I collapse.",
            f"This file does the work of {funcs // 5} files. Authentication, validation, business logic — all in one place. It's tired.",
            [f"Extract into {name}/ with focused modules", "Move validation to separate file", "Create dedicated service classes"],
        )
    
    # The Procrastinator
    if todos > 5:
        return (
            "The Procrastinator",
            f"Hey... I'm {name}{ext}. I have {todos} TODOs. I'll fix them tomorrow. Or next week. Definitely before the deadline.",
            f"A graveyard of good intentions. {todos} TODOs, each one a promise that was never kept.",
            ["Schedule a TODO cleanup session", "Convert TODOs to actual tickets", "Delete TODOs older than 6 months"],
        )
    
    # The Social Butterfly
    if imports > 15:
        return (
            "The Social Butterfly",
            f"I'm {name}{ext}. I import {imports} different things. I know everyone in this project. If I break, the entire app stops working.",
            f"Imports from {imports} sources. This file is the project's social hub — everyone depends on it.",
            ["Reduce dependencies where possible", "Consider splitting by concern", "Document why each import is needed"],
        )
    
    # The Ancient Wizard
    if comments > 30:
        return (
            "The Ancient Wizard",
            f"I am {name}{ext}. My {comments}% comment ratio speaks of ancient knowledge. Some say the original author's spirit still lives in these comments.",
            f"Extremely well-documented at {comments:.0f}% comments. A rare and precious artifact.",
            ["Ensure comments are still accurate", "Remove outdated documentation", "Keep up the good work"],
        )
    
    # The Lucky Survivor
    if funcs == 0 and lines < 30:
        return (
            "The Lucky Survivor",
            f"I'm {name}{ext}. I'm only {lines} lines. I do almost nothing, yet nobody has deleted me. I must be important... right?",
            f"A tiny file with no functions. Its purpose is a mystery, yet here it stands.",
            ["Check if this file is still needed", "Document its purpose or remove it"],
        )
    
    # The Copy-Paste Machine
    if nesting > 4:
        return (
            "The Copy-Paste Machine",
            f"I'm {name}{ext}. My code nests {nesting} levels deep. Even I can't follow my own logic anymore.",
            f"Nested {nesting} levels deep — a pyramid of if-statements and loops.",
            ["Flatten nested logic with early returns", "Extract deeply nested blocks into functions", "Use guard clauses"],
        )
    
    # The Perfectionist
    if comments > 15 and funcs > 5 and lines < 300:
        return (
            "The Perfectionist",
            f"I'm {name}{ext}. {lines} lines, {funcs} functions, {comments:.0f}% comments. Everything in its right place.",
            f"Well-structured and documented. A model citizen of the codebase.",
            ["Keep maintaining this standard", "Use as an example for other files"],
        )
    
    # Default: The Quiet Hero
    return (
        "The Quiet Hero",
        f"I'm {name}{ext}. I do my job with {lines} lines and {funcs} functions. No drama, no TODOs, no excessive imports. Just solid, reliable code.",
        f"A well-balanced file that does its job without complaints.",
        ["Keep up the good work", "Consider adding a few comments for newcomers"],
    )


def get_all_personalities(workspace_path: str, top_n: int = 10) -> list[FilePersonality]:
    """Get personalities for the most interesting files in a project."""
    files = scan_project(workspace_path)
    
    # Score files by "interestingness"
    scored = []
    for f in files:
        lines = f.content.count("\n") + 1
        funcs = sum(1 for l in f.content.split("\n") if l.strip().startswith(("def ", "function ", "class ")))
        todos = f.content.upper().count("TODO")
        interest = lines * 0.5 + funcs * 2 + todos * 3
        scored.append((f.relative_path, interest))
        f.unload_content()
    
    # Get top N most interesting files
    scored.sort(key=lambda x: x[1], reverse=True)
    personalities = []
    for filepath, _ in scored[:top_n]:
        try:
            p = analyze_file_personality(filepath, workspace_path)
            personalities.append(p)
        except Exception:
            pass
    
    return personalities