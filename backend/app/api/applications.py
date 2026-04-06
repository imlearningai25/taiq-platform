from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.activity import track
from app.models.models import Application, Job, User
from app.schemas.schemas import ApplicationCreate, ApplicationOut
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/applications", tags=["applications"])
bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check job exists
    job = await db.get(Job, payload.job_id)
    if not job or not job.is_active:
        raise HTTPException(status_code=404, detail="Job not found")

    # Prevent duplicate applications
    existing = await db.scalar(
        select(Application).where(
            Application.job_id == payload.job_id,
            Application.candidate_id == current_user.id,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Already applied to this job")

    # Resolve resume: explicit upload > profile resume
    resume_url = payload.resume_url
    if not resume_url and hasattr(current_user, 'profile') and current_user.profile:
        resume_url = current_user.profile.resume_url

    app = Application(
        job_id=payload.job_id,
        candidate_id=current_user.id,
        cover_letter=payload.cover_letter,
        resume_url=resume_url,
        referral_source=payload.referral_source,
        referral_email=payload.referral_email if payload.referral_source == "employee_referral" else None,
    )
    db.add(app)
    await db.flush()

    # Reload with eager relationships to avoid MissingGreenlet on job.company
    loaded_app = await db.scalar(
        select(Application)
        .options(selectinload(Application.job).selectinload(Job.company))
        .where(Application.id == app.id)
    )

    ref_note = f" (via {payload.referral_source})" if payload.referral_source else ""
    await track(db, current_user, "job_applied", f"Applied to job: {job.title}{ref_note}")
    return ApplicationOut.model_validate(loaded_app)


@router.get("/my", response_model=list[ApplicationOut])
async def my_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Application)
        .options(selectinload(Application.job).selectinload(Job.company))
        .where(Application.candidate_id == current_user.id)
        .order_by(Application.applied_at.desc())
    )
    apps = (await db.scalars(stmt)).all()
    return [ApplicationOut.model_validate(a) for a in apps]


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw_application(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app = await db.get(Application, app_id)
    if not app or app.candidate_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")
    await db.delete(app)
    await track(db, current_user, "application_withdrawn", "Withdrew a job application")
