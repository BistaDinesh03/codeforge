"""
Symbol index - extracts functions, classes, imports from project files.
Gives AI a map of the codebase before making changes.
"""

import re
from pathlib import Path
from dataclasses import dataclass, field
from app.services.project_scanner import scan_project, ProjectFile
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Symbol:
    """A named code element (function, class, variable)."""
    name: str
    kind: str  # function, class, method, variable, import
    file: str  # relative path
    line: int
    parent: str | None = None  # class name for methods


@dataclass
class WorkspaceIndex:
    """Complete index of a project's symbols and structure."""
    symbols: list[Symbol] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)
    total_symbols: int = 0


def extract_symbols(file: ProjectFile) -> list[Symbol]:
    """Extract symbols from a single file."""
    symbols = []
    try:
        lines = file.content.split("\n")
    except Exception:
        return symbols

    current_class = None
    ext = file.extension.lower()

    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("#") or line_stripped.startswith("//"):
            continue

        # Python
        if ext == ".py":
            # Class
            m = re.match(r"class\s+(\w+)", line_stripped)
            if m:
                current_class = m.group(1)
                symbols.append(Symbol(name=m.group(1), kind="class", file=file.relative_path, line=i))
                continue
            # Function/method
            m = re.match(r"def\s+(\w+)", line_stripped)
            if m:
                symbols.append(Symbol(name=m.group(1), kind="method" if current_class else "function", file=file.relative_path, line=i, parent=current_class))
                continue
            # Import
            m = re.match(r"(?:from\s+(\S+)\s+)?import\s+(.+)", line_stripped)
            if m:
                symbols.append(Symbol(name=m.group(2).split("#")[0].strip(), kind="import", file=file.relative_path, line=i))

        # JavaScript/TypeScript
        elif ext in (".js", ".ts", ".jsx", ".tsx"):
            m = re.match(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)", line_stripped)
            if m:
                symbols.append(Symbol(name=m.group(1), kind="function", file=file.relative_path, line=i))
                continue
            m = re.match(r"(?:export\s+)?class\s+(\w+)", line_stripped)
            if m:
                current_class = m.group(1)
                symbols.append(Symbol(name=m.group(1), kind="class", file=file.relative_path, line=i))
                continue
            m = re.match(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(.*\)\s*=>", line_stripped)
            if m:
                symbols.append(Symbol(name=m.group(1), kind="function", file=file.relative_path, line=i))
                continue

    return symbols


def build_workspace_index(root_path: str) -> WorkspaceIndex:
    """Build a complete symbol index of the project."""
    files = scan_project(root_path, load_content=True)
    index = WorkspaceIndex()
    index.files = [f.relative_path for f in files]

    for f in files:
        symbols = extract_symbols(f)
        index.symbols.extend(symbols)
        if f.extension:
            lang = f.extension.lstrip(".")
            index.languages[lang] = index.languages.get(lang, 0) + 1
        f.unload_content()

    index.total_symbols = len(index.symbols)
    logger.info(f"Indexed {index.total_symbols} symbols across {len(files)} files")
    return index


def get_symbols_by_kind(index: WorkspaceIndex, kind: str) -> list[Symbol]:
    """Filter symbols by kind (function, class, etc)."""
    return [s for s in index.symbols if s.kind == kind]


def find_symbol(index: WorkspaceIndex, name: str) -> list[Symbol]:
    """Find all symbols matching a name."""
    return [s for s in index.symbols if name.lower() in s.name.lower()]