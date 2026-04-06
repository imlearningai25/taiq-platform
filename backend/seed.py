"""
Seed script — run once after first container startup:
  docker compose exec backend python seed.py
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.core.database import Base
from app.core.security import get_password_hash
from app.models.models import (
    User, UserRole, Company, Industry, Job, JobType,
    Testimonial, BlogPost, CandidateProfile
)
from datetime import datetime, timedelta

engine = create_async_engine(settings.DATABASE_URL, echo=False)
Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as db:
        # ── Industries ────────────────────────────────────────────────────────
        industries_data = [
            ("Technology", "technology", "💻"),
            ("Healthcare", "healthcare", "🏥"),
            ("Finance", "finance", "💰"),
            ("Engineering", "engineering", "⚙️"),
            ("Marketing", "marketing", "📣"),
            ("Education", "education", "🎓"),
            ("Manufacturing", "manufacturing", "🏭"),
            ("Retail", "retail", "🛍️"),
            ("Logistics", "logistics", "🚚"),
            ("Legal", "legal", "⚖️"),
        ]
        industry_map = {}
        for name, slug, icon in industries_data:
            existing = await db.scalar(select(Industry).where(Industry.slug == slug))
            if not existing:
                ind = Industry(name=name, slug=slug, icon=icon)
                db.add(ind)
                await db.flush()
                industry_map[slug] = ind.id
            else:
                industry_map[slug] = existing.id
        print("✅ Industries seeded")

        # ── Admin user ────────────────────────────────────────────────────────
        admin = await db.scalar(select(User).where(User.email == "admin@taiq.us"))
        if not admin:
            admin = User(
                email="admin@taiq.us",
                hashed_password=get_password_hash("Admin@1234!"),
                full_name="Admin User",
                role=UserRole.admin,
            )
            db.add(admin)
            await db.flush()
        print("✅ Admin user created (admin@taiq.us / Admin@1234!)")

        # ── Employer users + companies ────────────────────────────────────────
        employers = [
            ("hr@acmetech.com", "Acme Technologies", "New York, NY", "500-1000", "technology"),
            ("jobs@dataflow.io", "DataFlow Inc.", "San Francisco, CA", "50-200", "technology"),
            ("recruit@metrohealth.org", "MetroHealth System", "Cleveland, OH", "1000+", "healthcare"),
            ("talent@fintechpartners.com", "FinTech Partners", "Austin, TX", "200-500", "finance"),
            ("hr@cloudnative.io", "CloudNative Corp", "Seattle, WA", "100-200", "technology"),
        ]
        company_map = {}
        for email, co_name, hq, size, industry_slug in employers:
            emp = await db.scalar(select(User).where(User.email == email))
            if not emp:
                emp = User(
                    email=email,
                    hashed_password=get_password_hash("Employer@1234!"),
                    full_name=f"{co_name} HR",
                    role=UserRole.employer,
                )
                db.add(emp)
                await db.flush()

            co = await db.scalar(select(Company).where(Company.owner_id == emp.id))
            if not co:
                from slugify import slugify
                co = Company(
                    owner_id=emp.id,
                    name=co_name,
                    slug=slugify(co_name),
                    headquarters=hq,
                    size=size,
                    industry_id=industry_map.get(industry_slug),
                    is_verified=True,
                )
                db.add(co)
                await db.flush()
            company_map[co_name] = co.id
        print("✅ Employers + Companies seeded")

        # ── Candidate ─────────────────────────────────────────────────────────
        cand = await db.scalar(select(User).where(User.email == "candidate@demo.com"))
        if not cand:
            cand = User(
                email="candidate@demo.com",
                hashed_password=get_password_hash("Candidate@1234!"),
                full_name="Jane Demo",
                role=UserRole.candidate,
            )
            db.add(cand)
            await db.flush()
            profile = CandidateProfile(
                user_id=cand.id,
                headline="Full-Stack Software Engineer",
                summary="Passionate engineer with 6 years building scalable web applications.",
                skills=["Python", "React", "AWS", "PostgreSQL", "Docker"],
                experience_years=6,
                location="New York, NY",
                open_to_remote=True,
            )
            db.add(profile)
        print("✅ Candidate user seeded (candidate@demo.com / Candidate@1234!)")

        # ── Jobs ──────────────────────────────────────────────────────────────
        jobs_data = [
            {
                "title": "Senior Software Engineer",
                "company": "Acme Technologies",
                "industry": "technology",
                "location": "New York, NY", "remote": True,
                "job_type": JobType.full_time,
                "salary_min": 130000, "salary_max": 170000,
                "skills_required": ["Python", "AWS", "React", "PostgreSQL"],
                "is_featured": True,
                "description": "Join our platform engineering team to build next-gen distributed systems serving 50M+ users.",
                "requirements": "6+ years Python, experience with distributed systems, AWS expertise required.",
                "benefits": "Competitive salary, 401k matching, comprehensive health insurance, remote-first culture.",
            },
            {
                "title": "Data Scientist – ML Platform",
                "company": "DataFlow Inc.",
                "industry": "technology",
                "location": "San Francisco, CA", "remote": True,
                "job_type": JobType.full_time,
                "salary_min": 120000, "salary_max": 160000,
                "skills_required": ["Python", "TensorFlow", "SQL", "Spark"],
                "is_featured": True,
                "description": "Build and deploy ML models that power real-time analytics for Fortune 500 clients.",
                "requirements": "MS/PhD in CS or related field, 3+ years ML engineering experience.",
                "benefits": "Equity package, unlimited PTO, $5K annual learning budget.",
            },
            {
                "title": "Registered Nurse – ICU",
                "company": "MetroHealth System",
                "industry": "healthcare",
                "location": "Cleveland, OH", "remote": False,
                "job_type": JobType.full_time,
                "salary_min": 72000, "salary_max": 95000,
                "skills_required": ["Critical Care", "BLS", "ACLS", "IV Therapy"],
                "is_featured": False,
                "description": "Provide exceptional patient care in our 40-bed ICU. Night and day shifts available.",
                "requirements": "Active RN license, BSN preferred, 2+ years ICU experience.",
                "benefits": "Sign-on bonus up to $10K, tuition reimbursement, shift differentials.",
            },
            {
                "title": "Product Manager – Growth",
                "company": "FinTech Partners",
                "industry": "finance",
                "location": "Austin, TX", "remote": True,
                "job_type": JobType.full_time,
                "salary_min": 115000, "salary_max": 145000,
                "skills_required": ["Product Strategy", "A/B Testing", "SQL", "Roadmapping"],
                "is_featured": False,
                "description": "Own and drive the growth product roadmap for our consumer fintech app with 2M users.",
                "requirements": "4+ years PM experience, fintech or consumer app background strongly preferred.",
                "benefits": "Stock options, flexible hybrid schedule, wellness stipend.",
            },
            {
                "title": "DevOps Engineer",
                "company": "CloudNative Corp",
                "industry": "technology",
                "location": "Remote", "remote": True,
                "job_type": JobType.contract,
                "salary_min": 95000, "salary_max": 130000,
                "skills_required": ["Kubernetes", "Docker", "Terraform", "CI/CD", "AWS"],
                "is_featured": False,
                "description": "6-month contract to help migrate legacy infrastructure to Kubernetes-native architecture.",
                "requirements": "4+ years DevOps/SRE, Kubernetes CKA certification preferred.",
                "benefits": "Remote, competitive contract rate, potential for full-time conversion.",
            },
            {
                "title": "UX/UI Designer",
                "company": "Acme Technologies",
                "industry": "technology",
                "location": "New York, NY", "remote": False,
                "job_type": JobType.full_time,
                "salary_min": 85000, "salary_max": 115000,
                "skills_required": ["Figma", "User Research", "Prototyping", "Design Systems"],
                "is_featured": False,
                "description": "Shape the visual language and user experience of products used by millions worldwide.",
                "requirements": "4+ years UX design, strong portfolio, experience with design systems.",
                "benefits": "Creative environment, flexible PTO, design conference budget.",
            },
        ]

        from slugify import slugify
        import uuid
        for jd in jobs_data:
            slug = f"{slugify(jd['title'])}-{uuid.uuid4().hex[:6]}"
            existing = await db.scalar(select(Job).where(Job.title == jd["title"]))
            if not existing:
                job = Job(
                    company_id=company_map.get(jd["company"], 1),
                    industry_id=industry_map.get(jd["industry"]),
                    title=jd["title"],
                    slug=slug,
                    description=jd["description"],
                    requirements=jd["requirements"],
                    benefits=jd["benefits"],
                    location=jd["location"],
                    remote=jd["remote"],
                    job_type=jd["job_type"],
                    salary_min=jd["salary_min"],
                    salary_max=jd["salary_max"],
                    skills_required=jd["skills_required"],
                    is_featured=jd.get("is_featured", False),
                    is_active=True,
                    expires_at=datetime.utcnow() + timedelta(days=60),
                )
                db.add(job)
        print("✅ Jobs seeded")

        # ── Testimonials ──────────────────────────────────────────────────────
        testimonials = [
            ("Sarah Johnson", "Software Engineer", "Google", "TaIQ connected me with my dream job in just 2 weeks. The platform is intuitive and the team is incredibly supportive throughout the entire process.", 5),
            ("Michael Chen", "HR Director", "Pfizer", "We have been using TaIQ to source top-tier candidates and the quality of applicants is consistently excellent. Highly recommended for any growing company.", 5),
            ("Priya Patel", "Data Scientist", "Goldman Sachs", "After months of searching on other platforms, TaIQ matched me with the perfect role that aligned with both my skills and career goals.", 5),
            ("James Williams", "Operations Manager", "Amazon", "The talent pool on TaIQ is exceptional. We filled 12 positions in a single quarter, saving us significant time and recruiting costs.", 4),
            ("Emma Rodriguez", "UX Designer", "Apple", "Simple, clean, and effective. I uploaded my resume, filled in my preferences, and had 5 interview invitations within a week.", 5),
            ("David Kim", "CFO", "Tesla", "TaIQ has become our primary recruiting channel. The quality of candidates and the platform support are unmatched in the industry.", 5),
        ]
        for name, role, company, content, rating in testimonials:
            existing = await db.scalar(select(Testimonial).where(Testimonial.name == name))
            if not existing:
                db.add(Testimonial(name=name, role=role, company=company, content=content, rating=rating, is_active=True))
        print("✅ Testimonials seeded")

        # ── Blog posts ────────────────────────────────────────────────────────
        posts = [
            ("10 Resume Mistakes Costing You Interviews", "career-advice", "Career Advice",
             "Discover the most common resume pitfalls and how to fix them to land more callbacks from top employers."),
            ("The 15 Fastest-Growing Jobs in Tech for 2025", "tech-jobs-2025", "Industry Trends",
             "AI, cybersecurity, and cloud computing are reshaping the workforce. Here's where the opportunities lie."),
            ("How to Build a Winning Employer Brand in 2025", "employer-branding-2025", "Hiring Guide",
             "Top candidates have options. Learn how leading companies attract elite talent in a competitive market."),
        ]
        for title, slug, category, excerpt in posts:
            existing = await db.scalar(select(BlogPost).where(BlogPost.slug == slug))
            if not existing:
                db.add(BlogPost(
                    title=title, slug=slug, category=category,
                    excerpt=excerpt, content=excerpt + " [Full content here]",
                    author_id=admin.id, is_published=True,
                    published_at=datetime.utcnow() - timedelta(days=5),
                ))
        print("✅ Blog posts seeded")

        await db.commit()
        print("\n🎉 All seed data committed successfully!")
        print("\n── Demo credentials ─────────────────────────────────────────")
        print("  Admin:     admin@taiq.us     / Admin@1234!")
        print("  Candidate: candidate@demo.com          / Candidate@1234!")
        print("  Employer:  hr@acmetech.com             / Employer@1234!")
        print("─────────────────────────────────────────────────────────────")


if __name__ == "__main__":
    asyncio.run(seed())
