"""
Scans project directories and collects file information.
Optimized for memory - stores only metadata, reads content on demand.
"""

import os
import asyncio
from pathlib import Path

IGNORED_DIRS: set[str] = {
    "node_modules", ".git", ".svn", ".hg", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".tox", "venv", ".venv",
    "env", ".env", "dist", "build", ".next", ".nuxt",
    "target", "vendor", ".idea", ".vscode", "logs", "models",
}

IGNORED_FILES: set[str] = {
    ".DS_Store", "Thumbs.db", "package-lock.json", "yarn.lock",
    "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock",
}

CODE_EXTENSIONS: set[str] = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt", ".swift",
    ".c", ".cpp", ".h", ".hpp", ".rs", ".go", ".rb", ".php",
    ".html", ".css", ".scss", ".json", ".yaml", ".yml", ".toml",
    ".md", ".txt", ".sh", ".bash", ".sql", ".graphql", ".proto",
}

MAX_FILE_SIZE = 1_000_000  # 1MB


class ProjectFile:
    """Represents a single file with lazy content loading."""

    def __init__(self, path: Path, relative_path: str):
        self.path = path
        self.relative_path = relative_path
        self.extension = path.suffix
        self._content: str | None = None

    @property
    def content(self) -> str:
        """Lazy-load file content. Only reads when accessed."""
        if self._content is None:
            try:
                self._content = self.path.read_text(encoding="utf-8", errors="ignore")
            except (OSError, UnicodeDecodeError):
                self._content = ""
        return self._content

    def unload_content(self) -> None:
        """Free memory by clearing cached content."""
        self._content = None

    def __repr__(self):
        return f"ProjectFile({self.relative_path})"


def scan_project(root_path: str | Path, load_content: bool = False) -> list[ProjectFile]:
    """
    Scans a project directory and returns all relevant code files.
    
    Args:
        root_path: Path to the project root.
        load_content: If True, load file contents immediately.
                      If False, load lazily on first access (memory efficient).
    """
    root = Path(root_path).resolve()
    files: list[ProjectFile] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in IGNORED_DIRS and not d.startswith(".")
        ]

        current_dir = Path(dirpath)

        for filename in filenames:
            file_path = current_dir / filename

            if filename in IGNORED_FILES:
                continue
            if file_path.suffix.lower() not in CODE_EXTENSIONS:
                continue

            try:
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            relative_path = str(file_path.relative_to(root))
            proj_file = ProjectFile(file_path, relative_path)

            # Pre-load content if requested (for indexing)
            if load_content:
                _ = proj_file.content

            files.append(proj_file)

    return files


async def scan_project_async(root_path: str | Path, load_content: bool = True) -> list[ProjectFile]:
    """Async wrapper that runs scan_project in a thread pool."""
    return await asyncio.to_thread(scan_project, root_path, load_content)


def get_file_count(root_path: str | Path) -> int:
    """Returns the number of scannable files without reading content."""
    return len(scan_project(root_path, load_content=False))