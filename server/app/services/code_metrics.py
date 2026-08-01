"""
Code metrics - analyzes project health, complexity, risks.
No AI needed. Pure static analysis.
"""

import re
from pathlib import Path
from dataclasses import dataclass
from app.services.project_scanner import scan_project
from app.services.symbol_index import build_workspace_index
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ProjectHealth:
    architecture: int
    maintainability: int
    complexity: int
    documentation: int
    testing: int
    security: int
    overall: int


def analyze_project(workspace_path: str) -> dict:
    """Complete project analysis returning health scores, risks, and stats."""
    files = scan_project(workspace_path, load_content=True)
    index = build_workspace_index(workspace_path)
    
    # Calculate metrics
    total_lines = 0
    total_functions = 0
    total_classes = 0
    file_sizes = []
    function_sizes = []
    todos = 0
    commented_lines = 0
    test_files = 0
    
    for f in files:
        lines = f.content.split("\n")
        total_lines += len(lines)
        file_sizes.append({"file": f.relative_path, "lines": len(lines), "size_kb": f.size_bytes / 1024})
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                commented_lines += 1
            if "TODO" in stripped or "FIXME" in stripped or "HACK" in stripped:
                todos += 1
        
        if "test" in f.relative_path.lower() or f.relative_path.endswith("_test.py") or f.relative_path.endswith(".test.js"):
            test_files += 1
        
        f.unload_content()
    
    # Function sizes
    for s in index.symbols:
        if s.kind in ("function", "method"):
            total_functions += 1
            function_sizes.append({"name": s.name, "file": s.file, "line": s.line})
    
    total_classes = len([s for s in index.symbols if s.kind == "class"])
    
    # Health scores
    comment_ratio = (commented_lines / max(total_lines, 1)) * 100
    test_ratio = (test_files / max(len(files), 1)) * 100
    todo_density = (todos / max(total_lines, 1)) * 1000
    
    architecture = score_architecture(files, index)
    maintainability = score_maintainability(total_lines, total_functions, comment_ratio)
    complexity = score_complexity(file_sizes, function_sizes, len(files))
    documentation = score_documentation(comment_ratio)
    testing = score_testing(test_ratio)
    security = score_security(files, index)
    overall = (architecture + maintainability + complexity + documentation + testing + security) // 6
    
    # Top risks
    risks = find_risks(file_sizes, function_sizes, index, todos, files)
    
    # Largest files
    largest = sorted(file_sizes, key=lambda x: x["lines"], reverse=True)[:10]
    
    return {
        "project": str(Path(workspace_path).name),
        "files": len(files),
        "total_lines": total_lines,
        "total_functions": total_functions,
        "total_classes": total_classes,
        "test_files": test_files,
        "todos": todos,
        "health": {
            "architecture": architecture,
            "maintainability": maintainability,
            "complexity": complexity,
            "documentation": documentation,
            "testing": testing,
            "security": security,
            "overall": overall,
        },
        "risks": risks[:8],
        "largest_files": largest,
        "languages": index.languages if hasattr(index, 'languages') else {},
    }


def score_architecture(files, index) -> int:
    """Score based on file organization and structure."""
    score = 70  # Start neutral
    if len(files) < 10: score -= 10
    if len(files) > 100: score -= 5
    classes = len([s for s in index.symbols if s.kind == "class"])
    if classes > 5: score += 10
    if classes > 20: score += 5
    return min(100, max(0, score))


def score_maintainability(total_lines, total_functions, comment_ratio) -> int:
    score = 70
    if total_lines > 10000: score -= 15
    if total_lines < 500: score += 10
    if comment_ratio > 10: score += 10
    if comment_ratio < 2: score -= 15
    if total_functions > 100: score -= 5
    return min(100, max(0, score))


def score_complexity(file_sizes, function_sizes, file_count) -> int:
    score = 70
    large_files = [f for f in file_sizes if f["lines"] > 500]
    if len(large_files) > 5: score -= 20
    elif len(large_files) > 2: score -= 10
    avg_file_size = sum(f["lines"] for f in file_sizes) / max(file_count, 1)
    if avg_file_size > 300: score -= 10
    if avg_file_size < 100: score += 10
    return min(100, max(0, score))


def score_documentation(comment_ratio) -> int:
    if comment_ratio > 20: return 90
    if comment_ratio > 10: return 75
    if comment_ratio > 5: return 60
    if comment_ratio > 2: return 40
    return 20


def score_testing(test_ratio) -> int:
    if test_ratio > 30: return 90
    if test_ratio > 15: return 75
    if test_ratio > 5: return 50
    if test_ratio > 0: return 30
    return 10


def score_security(files, index) -> int:
    score = 80
    sensitive_patterns = ["password", "secret", "api_key", "token", "private_key"]
    for f in files:
        for pattern in sensitive_patterns:
            if pattern in f.content.lower():
                score -= 5
                break
        f.unload_content()
    return min(100, max(0, score))


def find_risks(file_sizes, function_sizes, index, todos, files) -> list[dict]:
    risks = []
    
    # Large files
    for f in sorted(file_sizes, key=lambda x: x["lines"], reverse=True)[:3]:
        if f["lines"] > 500:
            risks.append({"type": "large_file", "severity": "high" if f["lines"] > 1000 else "medium", "file": f["file"], "detail": f"{f['lines']} lines — consider splitting", "lines": f["lines"]})
    
    # Too many TODOs
    if todos > 10:
        risks.append({"type": "todos", "severity": "medium", "file": "multiple", "detail": f"{todos} TODOs found — clean up", "count": todos})
    
    # No tests
    test_files = [f for f in files if "test" in f.relative_path.lower()]
    if len(test_files) == 0:
        risks.append({"type": "no_tests", "severity": "high", "file": "project", "detail": "No test files found", "count": 0})
    
    return risks