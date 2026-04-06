from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.core.database import get_db
from app.models.models import Job, Company, Industry
from app.schemas.schemas import JobOut, JobListOut, SearchQuery
import math

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListOut)
async def list_jobs(
    q: str | None = Query(None),
    location: str | None = Query(None),
    job_type: str | None = Query(None),
    remote: bool | None = Query(None),
    industry_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Job).where(Job.is_active == True).order_by(Job.is_featured.desc(), Job.created_at.desc())

    if q:
        stmt = stmt.where(or_(Job.title.ilike(f"%{q}%"), Job.description.ilike(f"%{q}%")))
    if location:
        stmt = stmt.where(Job.location.ilike(f"%{location}%"))
    if remote is not None:
        stmt = stmt.where(Job.remote == remote)
    if industry_id:
        stmt = stmt.where(Job.industry_id == industry_id)
    if job_type:
        stmt = stmt.where(Job.job_type == job_type)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    jobs = (await db.scalars(stmt.offset((page - 1) * limit).limit(limit))).all()

    return JobListOut(
        jobs=[JobOut.model_validate(j) for j in jobs],
        total=total or 0,
        page=page,
        pages=math.ceil((total or 0) / limit),
    )


@router.get("/featured", response_model=list[JobOut])
async def featured_jobs(db: AsyncSession = Depends(get_db)):
    stmt = select(Job).where(Job.is_active == True, Job.is_featured == True).limit(6)
    jobs = (await db.scalars(stmt)).all()
    return [JobOut.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job or not job.is_active:
        raise HTTPException(status_code=404, detail="Job not found")
    job.views += 1
    return JobOut.model_validate(job)
