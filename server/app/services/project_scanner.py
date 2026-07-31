"""
Project Scanner - walks project directories and collects file metadata.
Skips irrelevant folders (node_modules, .git, etc.) and large files.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Directories to skip
IGNORED_DIRS: set[str] = {
    "node_modules", ".git", ".svn", ".hg", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".tox", "venv", ".venv",
    "env", ".env", "dist", "build", ".next", ".nuxt",
    "target", "vendor", ".idea", ".vscode", "logs",
    "models",  # Skip our own models folder
    ".mypy_cache", ".ruff_cache",
}

# Files to skip by name
IGNORED_FILES: set[str] = {
    ".DS_Store", "Thumbs.db",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Pipfile.lock", "Cargo.lock",
    "go.sum", "composer.lock",
}

# File extensions we care about
CODE_EXTENSIONS: set[str] = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs",
    ".java", ".kt", ".kts", ".swift",
    ".c", ".cpp", ".cc", ".h", ".hpp", ".hh",
    ".rs", ".go", ".rb", ".php",
    ".html", ".css", ".scss", ".less",
    ".json", ".yaml", ".yml", ".toml",
    ".md", ".txt", ".rst",
    ".sql", ".graphql", ".proto",
    ".sh", ".bash", ".zsh", ".fish",
    ".dockerfile", ".dockerignore",
    ".env.example", ".gitignore",
}

# Max file size to read (skip huge files)
MAX_FILE_SIZE = 1_000_000  # 1 MB


@dataclass
class ProjectFile:
    """Represents a single file in a project."""
    path: Path          # Absolute path
    relative_path: str  # Path relative to project root
    extension: str      # File extension
    size_bytes: int     # File size
    _content: Optional[str] = None  # Cached content
    
    @property
    def content(self) -> str:
        """Lazy-load file content on first access."""
        if self._content is None:
            try:
                self._content = self.path.read_text(
                    encoding="utf-8", errors="ignore"
                )
            except (OSError, UnicodeDecodeError):
                self._content = ""
        return self._content
    
    def unload_content(self) -> None:
        """Free memory by clearing cached content."""
        self._content = None
    
    def __repr__(self) -> str:
        return f"ProjectFile({self.relative_path})"


def scan_project(root_path: str | Path, load_content: bool = False) -> list[ProjectFile]:
    """
    Scan a project directory and return all relevant files.
    
    Args:
        root_path: Path to the project root.
        load_content: If True, pre-load file contents. 
                      If False, lazy-load on first access (memory efficient).
    
    Returns:
        List of ProjectFile objects.
    """
    root = Path(root_path).resolve()
    
    if not root.exists():
        raise FileNotFoundError(f"Project directory not found: {root}")
    
    files: list[ProjectFile] = []
    skipped_dirs = 0
    skipped_files = 0
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Filter out ignored directories in-place
        original_count = len(dirnames)
        dirnames[:] = [
            d for d in dirnames
            if d not in IGNORED_DIRS and not d.startswith(".")
        ]
        skipped_dirs += original_count - len(dirnames)
        
        current_dir = Path(dirpath)
        
        for filename in filenames:
            file_path = current_dir / filename
            
            # Skip ignored files
            if filename in IGNORED_FILES:
                skipped_files += 1
                continue
            
            # Skip files without recognized extensions
            ext = file_path.suffix.lower()
            if ext not in CODE_EXTENSIONS:
                continue
            
            # Skip large files
            try:
                size = file_path.stat().st_size
                if size > MAX_FILE_SIZE:
                    skipped_files += 1
                    continue
            except OSError:
                continue
            
            # Create file record
            relative = str(file_path.relative_to(root))
            proj_file = ProjectFile(
                path=file_path,
                relative_path=relative,
                extension=ext,
                size_bytes=size,
            )
            
            # Pre-load content if requested
            if load_content:
                _ = proj_file.content
            
            files.append(proj_file)
    
    logger.info(
        f"Scanned {root}: {len(files)} files found "
        f"(skipped {skipped_dirs} dirs, {skipped_files} files)"
    )
    
    return files


def get_file_count(root_path: str | Path) -> int:
    """Quick count of scannable files without reading content."""
    return len(scan_project(root_path, load_content=False))


def get_project_summary(root_path: str | Path) -> dict:
    """Get a summary of the project structure."""
    files = scan_project(root_path, load_content=False)
    
    extensions = {}
    for f in files:
        ext = f.extension or ".unknown"
        extensions[ext] = extensions.get(ext, 0) + 1
    
    return {
        "root": str(Path(root_path).resolve()),
        "total_files": len(files),
        "extensions": dict(sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:10]),
    }