"""
Story generator - creates life stories for files based on git history.
Tells the journey of a file: commits, rewrites, refactors, production incidents.
"""

import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class FileStory:
    file: str
    age: str
    total_commits: int
    total_authors: int
    first_commit: str
    last_commit: str
    lines_added: int
    lines_deleted: int
    net_change: int
    story: str
    timeline: list[dict]


def get_file_story(filepath: str, workspace_path: str) -> FileStory:
    """Generate a life story for a file from git history."""
    workspace = Path(workspace_path)
    file_rel = Path(filepath)
    
    if not (workspace / ".git").exists():
        return _no_git_story(filepath)
    
    try:
        # Get commit count
        log = _git(workspace, f'log --oneline --follow -- "{file_rel}"')
        commits = [l for l in log.split("\n") if l.strip()]
        total = len(commits)
        
        if total == 0:
            return _no_git_story(filepath)
        
        # First and last commit
        first = _git(workspace, f'log --reverse --format="%H|%an|%ad" --date=short --follow -- "{file_rel}" | head -1').strip()
        last = _git(workspace, f'log -1 --format="%H|%an|%ad" --date=short -- "{file_rel}"').strip()
        
        first_parts = first.split("|") if first else ["?", "?", "?"]
        last_parts = last.split("|") if last else ["?", "?", "?"]
        
        # Stats
        stats = _git(workspace, f'log --format="" --numstat --follow -- "{file_rel}"')
        added = sum(int(l.split()[0]) for l in stats.split("\n") if l.strip() and l.split()[0].isdigit())
        deleted = sum(int(l.split()[1]) for l in stats.split("\n") if l.strip() and len(l.split()) > 1 and l.split()[1].isdigit())
        
        # Authors
        authors = _git(workspace, f'log --format="%an" --follow -- "{file_rel}"')
        unique_authors = len(set(a.strip() for a in authors.split("\n") if a.strip()))
        
        # Build story
        name = file_rel.stem
        ext = file_rel.suffix
        age_days = _days_since(first_parts[2]) if len(first_parts) > 2 else 0
        
        if total > 100:
            story = f"I'm {name}{ext}. I was born {first_parts[2]} and have survived {total} commits by {unique_authors} developers. I've seen {added} lines added and {deleted} lines deleted. I'm a veteran. I've survived rewrites, refactors, and at least one production incident that nobody talks about."
        elif total > 20:
            story = f"I'm {name}{ext}. I started as a small file {age_days} days ago. {total} commits later, I've grown to handle real responsibilities. {unique_authors} people have shaped me into what I am today."
        elif total > 5:
            story = f"I'm {name}{ext}. I'm relatively new — just {total} commits old. But I'm learning fast and contributing to the team."
        else:
            story = f"I'm {name}{ext}. I'm the newest member of this codebase. Only {total} commits so far, but I have big dreams."
        
        if deleted > added * 2:
            story += f" I've lost {deleted - added} more lines than I've gained. Character development."
        elif added > deleted * 3:
            story += f" I've grown by {added - deleted} lines. Some call it scope creep. I call it career growth."
        
        return FileStory(
            file=filepath,
            age=f"{age_days} days" if age_days > 0 else "today",
            total_commits=total,
            total_authors=unique_authors,
            first_commit=first_parts[2] if len(first_parts) > 2 else "unknown",
            last_commit=last_parts[2] if len(last_parts) > 2 else "unknown",
            lines_added=added,
            lines_deleted=deleted,
            net_change=added - deleted,
            story=story,
            timeline=_build_timeline(workspace, file_rel, commits[:5]),
        )
    except Exception as e:
        logger.warning(f"Story generation failed for {filepath}: {e}")
        return _no_git_story(filepath)


def _no_git_story(filepath: str) -> FileStory:
    p = Path(filepath)
    return FileStory(
        file=filepath,
        age="unknown",
        total_commits=0,
        total_authors=0,
        first_commit="unknown",
        last_commit="unknown",
        lines_added=0,
        lines_deleted=0,
        net_change=0,
        story=f"I'm {p.name}. I exist, but my history is a mystery. (No git repository found)",
        timeline=[],
    )


def _git(workspace: Path, command: str) -> str:
    try:
        result = subprocess.run(
            f'git -C "{workspace}" {command}',
            shell=True, capture_output=True, text=True, timeout=10
        )
        return result.stdout
    except Exception:
        return ""


def _days_since(date_str: str) -> int:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return (datetime.now() - d).days
    except Exception:
        return 0


def _build_timeline(workspace: Path, file: Path, commits: list[str]) -> list[dict]:
    timeline = []
    for c in commits[:5]:
        parts = c.split(" ", 1)
        if len(parts) >= 2:
            timeline.append({"hash": parts[0][:7], "message": parts[1][:80]})
    return timeline


def get_project_awards(workspace_path: str) -> list[dict]:
    """Generate fun awards for the entire project."""
    from app.services.code_metrics import analyze_project
    from app.services.project_scanner import scan_project
    
    data = analyze_project(workspace_path)
    files = scan_project(workspace_path)
    awards = []
    
    # Largest file
    if data["largest_files"]:
        f = data["largest_files"][0]
        awards.append({"award": "🏆 Biggest File", "file": f["file"], "detail": f"{f['lines']} lines of pure dedication"})
    
    # Most TODOs
    todo_map = {}
    for f in files:
        c = f.content.upper().count("TODO")
        if c > 0: todo_map[f.relative_path] = c
        f.unload_content()
    if todo_map:
        worst = max(todo_map, key=todo_map.get)
        awards.append({"award": "📝 Most TODOs", "file": worst, "detail": f"{todo_map[worst]} TODOs — champion procrastinator"})
    
    # Most functions
    awards.append({"award": "⚡ Total Functions", "detail": f"{data['total_functions']} functions across {data['files']} files"})
    
    # Lines of code
    awards.append({"award": "📊 Project Size", "detail": f"{data['total_lines']} lines of code"})
    
    # Test coverage mention
    if data["test_files"] > 0:
        awards.append({"award": "🧪 Tests Found", "detail": f"{data['test_files']} test files — someone cares about quality"})
    else:
        awards.append({"award": "🎲 Living Dangerously", "detail": "No test files found — respect the confidence"})
    
    # Health
    h = data["health"]
    if h["overall"] >= 80:
        awards.append({"award": "🌟 Overall Health", "detail": f"{h['overall']}/100 — This project is in great shape"})
    
    return awards