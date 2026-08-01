"""
Dependency graph - tracks which files import which other files.
Helps AI understand the impact of changes.
"""

import re
from pathlib import Path
from app.services.project_scanner import scan_project
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def build_dependency_graph(root_path: str) -> dict[str, list[str]]:
    """
    Build a dependency graph: {file: [files_it_depends_on]}.
    """
    files = scan_project(root_path, load_content=True)
    graph: dict[str, list[str]] = {}

    for f in files:
        deps = extract_imports(f)
        graph[f.relative_path] = deps
        f.unload_content()

    logger.info(f"Dependency graph built: {len(graph)} files")
    return graph


def extract_imports(file) -> list[str]:
    """Extract imported module names from a file."""
    imports = []
    ext = file.extension.lower()

    try:
        lines = file.content.split("\n")
    except Exception:
        return imports

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Python: import X or from X import Y
        if ext == ".py":
            m = re.match(r"import\s+(\w+)", line)
            if m:
                imports.append(m.group(1))
            m = re.match(r"from\s+(\w+)", line)
            if m:
                imports.append(m.group(1))

        # JS/TS: import ... from './X' or require('./X')
        elif ext in (".js", ".ts", ".jsx", ".tsx"):
            m = re.search(r"(?:from\s+['\"]|require\(['\"])(\./.+?|@\S+)['\"]", line)
            if m:
                imports.append(m.group(1))

    return imports


def get_dependents(graph: dict[str, list[str]], target_file: str) -> list[str]:
    """Find all files that depend on target_file."""
    target_name = Path(target_file).stem
    dependents = []
    for file, deps in graph.items():
        if any(target_name in dep for dep in deps):
            dependents.append(file)
    return dependents


def get_impact_report(graph: dict[str, list[str]], target_file: str) -> dict:
    """Report how many files would be affected by changing target_file."""
    dependents = get_dependents(graph, target_file)
    return {
        "file": target_file,
        "imported_by": len(dependents),
        "affected_files": dependents[:20],  # Top 20
    }