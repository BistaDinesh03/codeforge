"""
Update management API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.updater import (
    check_for_updates,
    perform_update,
    rollback_to_backup,
    get_current_version,
    UpdateInfo,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/update", tags=["update"])


class UpdateCheckResponse(BaseModel):
    """Response from update check."""
    update_available: bool
    current_version: str
    latest_version: str | None = None
    release_notes: str | None = None
    download_size_mb: float | None = None


class UpdateResult(BaseModel):
    """Result of an update operation."""
    success: bool
    message: str
    version: str


@router.get("/check", response_model=UpdateCheckResponse)
async def check_update():
    """Check if a newer version is available on GitHub."""
    current = get_current_version()
    update = check_for_updates()
    
    if update:
        return UpdateCheckResponse(
            update_available=True,
            current_version=current,
            latest_version=update.version,
            release_notes=update.notes,
            download_size_mb=update.size_mb,
        )
    
    return UpdateCheckResponse(
        update_available=False,
        current_version=current,
    )


@router.post("/apply", response_model=UpdateResult)
async def apply_update():
    """Download and apply the latest update."""
    update = check_for_updates()
    
    if not update:
        raise HTTPException(status_code=400, detail="No update available")
    
    try:
        success = perform_update(update.download_url)
        
        if success:
            return UpdateResult(
                success=True,
                message=f"Updated to {update.version}. Restart server to apply.",
                version=update.version,
            )
        else:
            raise HTTPException(status_code=500, detail="Update failed. Previous version restored.")
            
    except Exception as e:
        logger.error(f"Update failed: {e}")
        rollback_to_backup()
        raise HTTPException(
            status_code=500,
            detail=f"Update failed: {str(e)}. Previous version restored."
        )


@router.post("/rollback", response_model=UpdateResult)
async def rollback():
    """Rollback to the previous version."""
    success = rollback_to_backup()
    
    if success:
        return UpdateResult(
            success=True,
            message="Rolled back to previous version. Restart server to apply.",
            version=get_current_version(),
        )
    
    raise HTTPException(status_code=500, detail="Rollback failed. No backup found.")