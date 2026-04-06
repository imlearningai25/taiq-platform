from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.models import Industry, Testimonial, Job, Company, User, Application
from app.schemas.schemas import IndustryOut, TestimonialOut, StatsOut, BlogPostOut
from app.models.models import BlogPost

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/stats", response_model=StatsOut)
async def get_stats(db: AsyncSession = Depends(get_db)):
    total_jobs = await db.scalar(select(func.count(Job.id)).where(Job.is_active == True)) or 0
    total_companies = await db.scalar(select(func.count(Company.id))) or 0
    total_candidates = await db.scalar(select(func.count(User.id))) or 0
    placements = await db.scalar(select(func.count(Application.id))) or 0
    return StatsOut(
        total_jobs=total_jobs,
        total_companies=total_companies,
        total_candidates=total_candidates,
        placements_this_month=placements,
    )


@router.get("/industries", response_model=list[IndustryOut])
async def get_industries(db: AsyncSession = Depends(get_db)):
    industries = (await db.scalars(select(Industry))).all()
    return [IndustryOut.model_validate(i) for i in industries]


@router.get("/testimonials", response_model=list[TestimonialOut])
async def get_testimonials(db: AsyncSession = Depends(get_db)):
    stmt = select(Testimonial).where(Testimonial.is_active == True).limit(6)
    testimonials = (await db.scalars(stmt)).all()
    return [TestimonialOut.model_validate(t) for t in testimonials]


@router.get("/blog", response_model=list[BlogPostOut])
async def get_blog_posts(db: AsyncSession = Depends(get_db)):
    stmt = select(BlogPost).where(BlogPost.is_published == True).order_by(BlogPost.published_at.desc()).limit(3)
    posts = (await db.scalars(stmt)).all()
    return [BlogPostOut.model_validate(p) for p in posts]
