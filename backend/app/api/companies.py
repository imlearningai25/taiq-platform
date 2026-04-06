from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import Company, User
from app.schemas.schemas import CompanyCreate, CompanyOut, CompanyBrief
from app.api.applications import get_current_user
from slugify import slugify

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyBrief])
async def list_companies(db: AsyncSession = Depends(get_db)):
    companies = (await db.scalars(select(Company).limit(50))).all()
    return [CompanyBrief.model_validate(c) for c in companies]


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    slug = slugify(payload.name)
    # Make slug unique
    existing = await db.scalar(select(Company).where(Company.slug == slug))
    if existing:
        slug = f"{slug}-{current_user.id}"

    company = Company(
        owner_id=current_user.id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        website=payload.website,
        size=payload.size,
        headquarters=payload.headquarters,
        industry_id=payload.industry_id,
    )
    db.add(company)
    await db.flush()
    return CompanyOut.model_validate(company)


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(company_id: int, db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyOut.model_validate(company)
