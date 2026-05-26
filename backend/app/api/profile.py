from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.models import User, CandidateProfile, SavedJob, Company, Job
from app.schemas.schemas import UserOut, SavedJobOut
from app.api.applications import get_current_user
from app.core.security import verify_password, get_password_hash
from app.core.activity import track
from app.models.models import ActivityLog
from app.schemas.schemas import ActivityLogOut
from pydantic import BaseModel
from typing import Any
import os
import uuid
import logging

logger = logging.getLogger(__name__)

UPLOAD_DIR = "/app/uploads/resumes"
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10 MB

router = APIRouter(prefix="/me", tags=["profile"])


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ProfileUpdate(BaseModel):
    headline: str | None = None
    summary: str | None = None
    skills: list[str] = []
    experience_years: int | None = None
    location: str | None = None
    linkedin_url: str | None = None
    open_to_remote: bool = True
    desired_salary_min: float | None = None
    desired_salary_max: float | None = None
    resume_url: str | None = None


class ProfileOut(BaseModel):
    user: UserOut
    profile: dict[str, Any] | None
    company: dict[str, Any] | None = None
    model_config = {"from_attributes": True}


@router.get("", response_model=ProfileOut)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await db.scalar(
        select(CandidateProfile).where(CandidateProfile.user_id == current_user.id)
    )
    profile_data = None
    if profile:
        profile_data = {
            "headline": profile.headline,
            "summary": profile.summary,
            "skills": profile.skills or [],
            "experience_years": profile.experience_years,
            "location": profile.location,
            "linkedin_url": profile.linkedin_url,
            "open_to_remote": profile.open_to_remote,
            "desired_salary_min": float(profile.desired_salary_min) if profile.desired_salary_min else None,
            "desired_salary_max": float(profile.desired_salary_max) if profile.desired_salary_max else None,
            "resume_url": profile.resume_url,
        }

    company_data = None
    from app.models.models import UserRole
    if current_user.role in (UserRole.employer, UserRole.admin):
        company = await db.scalar(select(Company).where(Company.owner_id == current_user.id))
        if company:
            company_data = {
                "id": company.id,
                "name": company.name,
                "description": company.description,
                "website": company.website,
                "logo_url": company.logo_url,
                "size": company.size,
                "headquarters": company.headquarters,
                "is_verified": company.is_verified,
            }

    return ProfileOut(
        user=UserOut.model_validate(current_user),
        profile=profile_data,
        company=company_data,
    )


@router.patch("")
async def update_user_info(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.phone is not None:
        current_user.phone = payload.phone
    await db.flush()
    await track(db, current_user, "profile_basic_updated", "Updated basic profile information (name/phone)")
    return UserOut.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    current_user.hashed_password = get_password_hash(payload.new_password)
    await db.flush()
    await track(db, current_user, "password_changed", "Account password changed")
    return {"message": "Password changed successfully"}


@router.put("/profile")
async def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await db.scalar(
        select(CandidateProfile).where(CandidateProfile.user_id == current_user.id)
    )
    if not profile:
        profile = CandidateProfile(user_id=current_user.id)
        db.add(profile)

    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(profile, k, v)

    await db.flush()
    await track(db, current_user, "profile_professional_updated", "Updated professional profile information")
    return {"message": "Profile updated successfully"}


@router.get("/saved", response_model=list[SavedJobOut])
async def get_saved_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(SavedJob)
        .options(selectinload(SavedJob.job).selectinload(Job.company))
        .where(SavedJob.user_id == current_user.id)
        .order_by(SavedJob.saved_at.desc())
    )
    saved = (await db.scalars(stmt)).all()
    return [SavedJobOut.model_validate(s) for s in saved]


@router.post("/saved/{job_id}", status_code=status.HTTP_201_CREATED)
async def save_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(Job, job_id)
    if not job or not job.is_active:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = await db.scalar(
        select(SavedJob).where(
            SavedJob.user_id == current_user.id,
            SavedJob.job_id == job_id,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Job already saved")

    saved = SavedJob(user_id=current_user.id, job_id=job_id)
    db.add(saved)
    await db.flush()
    await track(db, current_user, "job_saved", f"Saved job: {job.title}")
    return {"message": "Job saved successfully"}


@router.delete("/saved/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    saved = await db.scalar(
        select(SavedJob).where(
            SavedJob.user_id == current_user.id,
            SavedJob.job_id == job_id,
        )
    )
    if not saved:
        raise HTTPException(status_code=404, detail="Saved job not found")
    await db.delete(saved)
    await db.flush()
    await track(db, current_user, "job_unsaved", "Removed a job from saved list")


@router.get("/activities", response_model=list[ActivityLogOut])
async def get_my_activities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ActivityLog)
        .where(ActivityLog.user_id == current_user.id)
        .order_by(ActivityLog.created_at.desc())
    )
    logs = (await db.scalars(stmt)).all()
    return [ActivityLogOut.model_validate(l) for l in logs]


@router.post("/resume")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF, DOC, and DOCX files are allowed")

    contents = await file.read()
    if len(contents) > MAX_RESUME_SIZE:
        raise HTTPException(status_code=413, detail="File too large — maximum 10 MB")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Delete old resume file if it exists
    profile = await db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    if profile and profile.resume_url:
        old_path = _url_to_path(profile.resume_url)
        if old_path and os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

    filename = f"{current_user.id}_{uuid.uuid4().hex[:12]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    resume_url = f"/uploads/resumes/{filename}"

    if not profile:
        profile = CandidateProfile(user_id=current_user.id)
        db.add(profile)
    profile.resume_url = resume_url
    await db.flush()
    await track(db, current_user, "resume_uploaded", f"Uploaded resume: {file.filename}")
    return {"resume_url": resume_url, "filename": file.filename}


@router.delete("/resume", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    if not profile or not profile.resume_url:
        raise HTTPException(status_code=404, detail="No resume uploaded")

    old_path = _url_to_path(profile.resume_url)
    if old_path and os.path.exists(old_path):
        try:
            os.remove(old_path)
        except OSError as e:
            logger.warning(f"Could not delete resume file {old_path}: {e}")

    profile.resume_url = None
    await db.flush()
    await track(db, current_user, "resume_deleted", "Removed resume")


def _url_to_path(resume_url: str) -> str | None:
    """Convert a /uploads/resumes/... URL to the local filesystem path."""
    prefix = "/uploads/resumes/"
    if resume_url and resume_url.startswith(prefix):
        return os.path.join(UPLOAD_DIR, resume_url[len(prefix):])
    return None
