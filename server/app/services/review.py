"""
Review workflow - collects changes from execution and presents them for approval.
"""

import os
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class FileChange:
    """A single file change to review."""
    filepath: str
    action: str  # created, modified, deleted
    original_content: str
    new_content: str
    approved: bool = False


@dataclass
class ReviewSession:
    """A review session for an execution."""
    exec_id: str
    changes: list[FileChange]
    backup_dir: str | None = None


_reviews: dict[str, ReviewSession] = {}


def create_review(exec_id: str, changes: list[dict]) -> str:
    """Create a review session from execution results."""
    review_id = str(len(_reviews) + 1)
    
    file_changes = []
    for c in changes:
        file_changes.append(FileChange(
            filepath=c.get("filepath", ""),
            action=c.get("action", "modified"),
            original_content=c.get("original", ""),
            new_content=c.get("new", ""),
        ))
    
    _reviews[review_id] = ReviewSession(
        exec_id=exec_id,
        changes=file_changes,
    )
    
    logger.info(f"Review created: {review_id}, {len(file_changes)} changes")
    return review_id


def get_review(review_id: str) -> dict:
    """Get review details."""
    review = _reviews.get(review_id)
    if not review:
        return {"error": "Review not found"}
    
    return {
        "review_id": review_id,
        "exec_id": review.exec_id,
        "total_changes": len(review.changes),
        "approved": sum(1 for c in review.changes if c.approved),
        "changes": [
            {
                "filepath": c.filepath,
                "action": c.action,
                "approved": c.approved,
                "diff_lines": len(c.new_content.split("\n")) - len(c.original_content.split("\n")),
            }
            for c in review.changes
        ],
    }


def approve_change(review_id: str, filepath: str, workspace_path: str) -> dict:
    """Approve a single change and apply it."""
    review = _reviews.get(review_id)
    if not review:
        return {"error": "Review not found"}
    
    change = next((c for c in review.changes if c.filepath == filepath), None)
    if not change:
        return {"error": f"File not in review: {filepath}"}
    
    try:
        full_path = Path(workspace_path) / filepath
        
        if change.action == "deleted":
            if full_path.exists():
                full_path.unlink()
        else:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(change.new_content, encoding="utf-8")
        
        change.approved = True
        logger.info(f"Applied change: {filepath}")
        return {"status": "applied", "filepath": filepath}
        
    except Exception as e:
        return {"error": str(e)}


def approve_all(review_id: str, workspace_path: str) -> dict:
    """Approve and apply all changes."""
    review = _reviews.get(review_id)
    if not review:
        return {"error": "Review not found"}
    
    applied = 0
    errors = []
    
    for change in review.changes:
        result = approve_change(review_id, change.filepath, workspace_path)
        if result.get("status") == "applied":
            applied += 1
        else:
            errors.append(result.get("error", "Unknown error"))
    
    return {"applied": applied, "errors": errors}


def reject_change(review_id: str, filepath: str) -> dict:
    """Reject a single change."""
    review = _reviews.get(review_id)
    if not review:
        return {"error": "Review not found"}
    
    change = next((c for c in review.changes if c.filepath == filepath), None)
    if not change:
        return {"error": f"File not in review: {filepath}"}
    
    change.approved = False
    change.new_content = change.original_content
    return {"status": "rejected", "filepath": filepath}


def reject_all(review_id: str) -> dict:
    """Reject all changes."""
    review = _reviews.get(review_id)
    if not review:
        return {"error": "Review not found"}
    
    for change in review.changes:
        change.approved = False
        change.new_content = change.original_content
    
    return {"status": "all_rejected", "count": len(review.changes)}