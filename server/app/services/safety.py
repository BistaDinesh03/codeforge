"""
Safety system - checkpoints, validation, rollback.
Never lose work. Never run dangerous commands.
"""

import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from app.core.logging_config import get_logger

logger = get_logger(__name__)

CHECKPOINT_DIR = Path.home() / ".codeforge" / "checkpoints"

# Dangerous patterns that require explicit approval
DANGEROUS_PATTERNS = [
    "rm -rf", "rm -r", "sudo", "format", "mkfs",
    "dd if=", "> /dev/sda", "fork bomb", ":(){ :|:& };:",
    "chmod 777", "chown -R", "git push --force",
    "DROP TABLE", "DELETE FROM", "TRUNCATE",
]

# Files never to modify
PROTECTED_FILES = [
    ".env", ".env.local", ".env.production",
    ".git", ".gitignore", "package-lock.json", "yarn.lock",
    "node_modules", "venv", "__pycache__",
]


def create_checkpoint(workspace_path: str, label: str = "") -> str:
    """Create a git-based checkpoint before multi-file edits."""
    workspace = Path(workspace_path)
    if not (workspace / ".git").exists():
        logger.warning("No git repo found, skipping checkpoint")
        return ""
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tag = f"codeforge-{timestamp}"
        if label:
            tag += f"-{label.replace(' ', '_')}"
        
        subprocess.run(["git", "-C", str(workspace), "add", "-A"], capture_output=True)
        subprocess.run(
            ["git", "-C", str(workspace), "commit", "-m", f"CodeForge checkpoint: {label or timestamp}"],
            capture_output=True,
        )
        subprocess.run(["git", "-C", str(workspace), "tag", tag], capture_output=True)
        
        logger.info(f"Checkpoint created: {tag}")
        return tag
    except Exception as e:
        logger.error(f"Checkpoint failed: {e}")
        return ""


def rollback_to_checkpoint(workspace_path: str, tag: str) -> dict:
    """Rollback to a git checkpoint."""
    workspace = Path(workspace_path)
    try:
        result = subprocess.run(
            ["git", "-C", str(workspace), "checkout", tag, "--", "."],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            logger.info(f"Rollback successful: {tag}")
            return {"status": "rolled_back", "tag": tag}
        return {"error": result.stderr}
    except Exception as e:
        return {"error": str(e)}


def list_checkpoints(workspace_path: str) -> list[str]:
    """List all CodeForge checkpoints."""
    workspace = Path(workspace_path)
    try:
        result = subprocess.run(
            ["git", "-C", str(workspace), "tag", "-l", "codeforge-*"],
            capture_output=True, text=True,
        )
        return [t.strip() for t in result.stdout.split("\n") if t.strip()]
    except Exception:
        return []


def is_safe_file(filepath: str) -> bool:
    """Check if a file is safe to modify."""
    path = Path(filepath)
    for part in path.parts:
        if part in PROTECTED_FILES:
            return False
    if path.name in PROTECTED_FILES:
        return False
    return True


def is_safe_command(command: str) -> tuple[bool, str]:
    """Check if a terminal command is safe to run."""
    cmd_lower = command.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in cmd_lower:
            return False, f"Command blocked: contains dangerous pattern '{pattern}'"
    return True, ""


def validate_action(action: str, filepath: str, workspace_path: str) -> dict:
    """Validate an action before execution."""
    issues = []
    
    # Check protected files
    if not is_safe_file(filepath):
        issues.append(f"Protected file: {filepath}")
    
    # Check file exists for modify/delete
    full_path = Path(workspace_path) / filepath
    if action == "modify" and not full_path.exists():
        issues.append(f"File does not exist: {filepath}")
    if action == "create" and full_path.exists():
        issues.append(f"File already exists: {filepath} (use modify instead)")
    
    # Check file extension
    dangerous_extensions = {".exe", ".dll", ".so", ".dylib", ".bin"}
    if full_path.suffix in dangerous_extensions:
        issues.append(f"Cannot modify binary file: {filepath}")
    
    return {
        "safe": len(issues) == 0,
        "issues": issues,
        "action": action,
        "filepath": filepath,
    }


def create_backup(filepath: str, workspace_path: str) -> str:
    """Create a backup of a single file before modifying."""
    src = Path(workspace_path) / filepath
    if not src.exists():
        return ""
    
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = CHECKPOINT_DIR / f"{src.name}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
    shutil.copy2(src, backup_path)
    return str(backup_path)


def restore_backup(backup_path: str, original_path: str) -> bool:
    """Restore a file from backup."""
    try:
        shutil.copy2(backup_path, original_path)
        return True
    except Exception:
        return False