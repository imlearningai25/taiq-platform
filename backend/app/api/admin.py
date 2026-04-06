"""
Admin API — site settings, mode toggle, and future admin operations.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime, timezone
import logging

from app.core.database import get_db
from app.models.models import SiteSettings, SiteMode, User, UserRole
from app.schemas.schemas import SiteSettingsOut, SiteSettingsUpdate
from app.api.applications import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


# ── Auth helpers ──────────────────────────────────────────────────────────────
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def get_or_create_settings(db: AsyncSession) -> SiteSettings:
    """Return the single SiteSettings row, creating it with defaults if absent."""
    try:
        s = await db.scalar(select(SiteSettings).where(SiteSettings.id == 1))
        if not s:
            s = SiteSettings(
                id=1,
                mode=SiteMode.live,
                construction_title="We Are Building Something Great",
                construction_message="TaIQ is currently undergoing scheduled maintenance. Back shortly.",
                construction_eta="",
                updated_at=datetime.now(timezone.utc),
            )
            db.add(s)
            await db.flush()
            await db.refresh(s)
        return s
    except Exception as e:
        logger.error(f"get_or_create_settings error: {e}")
        raise


# ── Public: read current mode (called by every page on load) ──────────────────
@router.get("/site-settings", response_model=SiteSettingsOut)
async def get_site_settings(db: AsyncSession = Depends(get_db)):
    s = await get_or_create_settings(db)
    return SiteSettingsOut.model_validate(s)


# ── Admin: update mode + construction content ─────────────────────────────────
@router.put("/site-settings", response_model=SiteSettingsOut)
async def update_site_settings(
    payload: SiteSettingsUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    # Validate mode value explicitly so we return a clean 400, not a 500
    if payload.mode not in ("live", "construction"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{payload.mode}'. Must be 'live' or 'construction'."
        )

    try:
        s = await get_or_create_settings(db)

        # Apply all fields
        s.mode = SiteMode(payload.mode)
        s.updated_by = current_user.id
        s.updated_at = datetime.now(timezone.utc)   # set explicitly — don't rely on onupdate

        if payload.construction_title is not None:
            s.construction_title = payload.construction_title
        if payload.construction_message is not None:
            s.construction_message = payload.construction_message
        if payload.construction_eta is not None:
            s.construction_eta = payload.construction_eta

        await db.flush()
        await db.refresh(s)   # re-read from DB to get fresh values
        logger.info(f"Site mode set to '{s.mode.value}' by admin {current_user.email}")
        return SiteSettingsOut.model_validate(s)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_site_settings error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


# ── Admin: platform overview stats ────────────────────────────────────────────
@router.get("/overview")
async def admin_overview(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func
    from app.models.models import Job, Company, Application

    try:
        total_users        = await db.scalar(select(func.count(User.id))) or 0
        total_jobs         = await db.scalar(select(func.count(Job.id))) or 0
        total_companies    = await db.scalar(select(func.count(Company.id))) or 0
        total_applications = await db.scalar(select(func.count(Application.id))) or 0
        site               = await get_or_create_settings(db)

        return {
            "total_users": total_users,
            "total_jobs": total_jobs,
            "total_companies": total_companies,
            "total_applications": total_applications,
            "site_mode": site.mode.value,
        }
    except Exception as e:
        logger.error(f"admin_overview error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
