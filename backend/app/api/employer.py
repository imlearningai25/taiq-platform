from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.models import Job, Company, UserRole, Application, User
from app.schemas.schemas import JobCreate, JobOut, EmployerApplicationOut
from app.api.applications import get_current_user
from slugify import slugify
import uuid

router = APIRouter(prefix="/employer/jobs", tags=["employer"])
employer_router = APIRouter(prefix="/employer", tags=["employer"])


def require_employer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.employer, UserRole.admin):
        raise HTTPException(status_code=403, detail="Employer account required")
    return current_user


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def post_job(
    payload: JobCreate,
    current_user: User = Depends(require_employer),
    db: AsyncSession = Depends(get_db),
):
    company = await db.scalar(select(Company).where(Company.owner_id == current_user.id))
    if not company:
        raise HTTPException(status_code=400, detail="Create a company profile first")

    slug = f"{slugify(payload.title)}-{uuid.uuid4().hex[:6]}"
    job = Job(
        company_id=company.id,
        industry_id=payload.industry_id,
        title=payload.title,
        slug=slug,
        description=payload.description,
        requirements=payload.requirements,
        benefits=payload.benefits,
        location=payload.location,
        remote=payload.remote,
        job_type=payload.job_type,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        skills_required=payload.skills_required,
    )
    db.add(job)
    await db.flush()
    return JobOut.model_validate(job)


@router.get("", response_model=list[JobOut])
async def my_jobs(
    current_user: User = Depends(require_employer),
    db: AsyncSession = Depends(get_db),
):
    company = await db.scalar(select(Company).where(Company.owner_id == current_user.id))
    if not company:
        return []
    jobs = (await db.scalars(select(Job).where(Job.company_id == company.id).order_by(Job.created_at.desc()))).all()
    return [JobOut.model_validate(j) for j in jobs]


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    current_user: User = Depends(require_employer),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    company = await db.scalar(select(Company).where(Company.owner_id == current_user.id))
    if not company or job.company_id != company.id:
        raise HTTPException(status_code=403, detail="Not your job posting")
    job.is_active = False   # soft delete


@employer_router.get("/applications", response_model=list[EmployerApplicationOut])
async def employer_applications(
    current_user: User = Depends(require_employer),
    db: AsyncSession = Depends(get_db),
):
    company = await db.scalar(select(Company).where(Company.owner_id == current_user.id))
    if not company:
        return []
    stmt = (
        select(Application)
        .options(
            selectinload(Application.job).selectinload(Job.company),
            selectinload(Application.candidate),
        )
        .join(Job, Application.job_id == Job.id)
        .where(Job.company_id == company.id)
        .order_by(Application.applied_at.desc())
        .limit(50)
    )
    apps = (await db.scalars(stmt)).all()
    return [EmployerApplicationOut.model_validate(a) for a in apps]
