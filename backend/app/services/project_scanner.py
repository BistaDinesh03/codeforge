"""
Scans project directories and collects file information.
Knows which folders and files to ignore.
"""

import os
from pathlib import Path
from typing import Generator

# Folders and files to ignore during scanning
IGNORED_DIRS: set[str] = {
    "node_modules",
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",  # Rust
    "vendor",  # Go/PHP
    ".idea",
    ".vscode",
    "logs",
    "models",  # AI model files (huge)
}

IGNORED_FILES: set[str] = {
    ".DS_Store",
    "Thumbs.db",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
}

# File extensions we care about
CODE_EXTENSIONS: set[str] = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".kt", ".swift",
    ".c", ".cpp", ".h", ".hpp",
    ".rs", ".go", ".rb", ".php",
    ".html", ".css", ".scss",
    ".json", ".yaml", ".yml", ".toml",
    ".md", ".txt", ".sh", ".bash",
    ".sql", ".graphql", ".proto",
}


class ProjectFile:
    """Represents a single file in the project."""

    def __init__(self, path: Path, relative_path: str, content: str):
        self.path = path
        self.relative_path = relative_path
        self.content = content
        self.extension = path.suffix

    def __repr__(self):
        return f"ProjectFile({self.relative_path})"


def scan_project(root_path: str | Path) -> list[ProjectFile]:
    """
    Scans a project directory and returns all relevant code files.

    Args:
        root_path: Path to the project root directory.

    Returns:
        List of ProjectFile objects.
    """
    root = Path(root_path).resolve()
    files: list[ProjectFile] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Remove ignored directories from the walk
        dirnames[:] = [
            d for d in dirnames
            if d not in IGNORED_DIRS
            and not d.startswith(".")
        ]

        current_dir = Path(dirpath)

        for filename in filenames:
            file_path = current_dir / filename

            # Skip ignored files
            if filename in IGNORED_FILES:
                continue

            # Skip files without recognized extensions
            if file_path.suffix.lower() not in CODE_EXTENSIONS:
                continue

            # Skip very large files (> 1MB)
            try:
                if file_path.stat().st_size > 1_000_000:
                    continue
            except OSError:
                continue

            # Try to read the file
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                relative_path = str(file_path.relative_to(root))
                files.append(ProjectFile(file_path, relative_path, content))
            except (OSError, UnicodeDecodeError):
                continue

    return files


def get_file_count(root_path: str | Path) -> int:
    """Returns the number of scannable files in the project."""
    return len(scan_project(root_path))