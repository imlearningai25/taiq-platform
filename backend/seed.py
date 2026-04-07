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
                is_email_verified=True,
            )
            db.add(admin)
            await db.flush()
        else:
            admin.is_email_verified = True
        print("✅ Admin user created (admin@taiq.us / Admin@1234!)")

        # ── Employer users + companies ────────────────────────────────────────
        employers = [
            ("hr@acmetech.com",          "Acme Technologies",    "New York, NY",       "500-1000", "technology"),
            ("jobs@dataflow.io",          "DataFlow Inc.",         "San Francisco, CA",  "50-200",   "technology"),
            ("recruit@metrohealth.org",   "MetroHealth System",   "Cleveland, OH",      "1000+",    "healthcare"),
            ("talent@fintechpartners.com","FinTech Partners",      "Austin, TX",         "200-500",  "finance"),
            ("hr@cloudnative.io",         "CloudNative Corp",     "Seattle, WA",        "100-200",  "technology"),
            ("hiring@novabio.com",        "NovaBio Labs",         "Boston, MA",         "200-500",  "healthcare"),
            ("jobs@greenbridge.com",      "GreenBridge Energy",   "Denver, CO",         "500-1000", "engineering"),
            ("recruit@lexacorp.com",      "LexaCorp Legal",       "Chicago, IL",        "50-200",   "legal"),
            ("hr@retailnext.com",         "RetailNext",           "Atlanta, GA",        "200-500",  "retail"),
            ("talent@edupath.org",        "EduPath Learning",     "Remote",             "50-200",   "education"),
            ("jobs@swiftlogix.com",       "SwiftLogix",           "Dallas, TX",         "500-1000", "logistics"),
            ("hr@nimblemfg.com",          "Nimble Manufacturing", "Detroit, MI",        "1000+",    "manufacturing"),
            # Batch 2 employers
            ("jobs@horizonai.io",         "Horizon AI",           "San Francisco, CA",  "50-200",   "technology"),
            ("hr@peakwellness.com",       "Peak Wellness Group",  "Miami, FL",          "200-500",  "healthcare"),
            ("talent@vaultcapital.com",   "Vault Capital",        "New York, NY",       "50-200",   "finance"),
            ("jobs@terranova.build",      "TerraNova Builders",   "Phoenix, AZ",        "500-1000", "engineering"),
            ("hr@brightminds.edu",        "BrightMinds Academy",  "Boston, MA",         "200-500",  "education"),
            ("recruit@nexuslaw.com",      "Nexus Law Group",      "Washington, DC",     "50-200",   "legal"),
            ("jobs@urbanstore.com",       "Urban Store Co.",      "Los Angeles, CA",    "500-1000", "retail"),
            ("hr@alphalogistics.com",     "Alpha Logistics",      "Chicago, IL",        "1000+",    "logistics"),
            ("talent@primecast.com",      "PrimeCast Media",      "New York, NY",       "100-200",  "marketing"),
            ("jobs@steelcraft.io",        "SteelCraft Industries","Pittsburgh, PA",     "500-1000", "manufacturing"),
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
                    is_email_verified=True,
                )
                db.add(emp)
                await db.flush()
            else:
                emp.is_email_verified = True

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
                is_email_verified=True,
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
        else:
            cand.is_email_verified = True
        print("✅ Candidate user seeded (candidate@demo.com / Candidate@1234!)")

        # ── Jobs ──────────────────────────────────────────────────────────────
        jobs_data = [
            # ── Technology ──────────────────────────────────────────────────
            {"title":"Senior Software Engineer","company":"Acme Technologies","industry":"technology","location":"New York, NY","remote":True,"job_type":JobType.full_time,"salary_min":130000,"salary_max":170000,"skills_required":["Python","AWS","React","PostgreSQL"],"is_featured":True,"description":"Join our platform engineering team to build next-gen distributed systems serving 50M+ users.","requirements":"6+ years Python, experience with distributed systems, AWS expertise required.","benefits":"Competitive salary, 401k matching, comprehensive health insurance, remote-first culture."},
            {"title":"Data Scientist – ML Platform","company":"DataFlow Inc.","industry":"technology","location":"San Francisco, CA","remote":True,"job_type":JobType.full_time,"salary_min":120000,"salary_max":160000,"skills_required":["Python","TensorFlow","SQL","Spark"],"is_featured":True,"description":"Build and deploy ML models that power real-time analytics for Fortune 500 clients.","requirements":"MS/PhD in CS or related field, 3+ years ML engineering experience.","benefits":"Equity package, unlimited PTO, $5K annual learning budget."},
            {"title":"DevOps Engineer","company":"CloudNative Corp","industry":"technology","location":"Remote","remote":True,"job_type":JobType.contract,"salary_min":95000,"salary_max":130000,"skills_required":["Kubernetes","Docker","Terraform","CI/CD","AWS"],"is_featured":False,"description":"6-month contract to migrate legacy infrastructure to Kubernetes-native architecture.","requirements":"4+ years DevOps/SRE, Kubernetes CKA certification preferred.","benefits":"Remote, competitive contract rate, potential for full-time conversion."},
            {"title":"UX/UI Designer","company":"Acme Technologies","industry":"technology","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":85000,"salary_max":115000,"skills_required":["Figma","User Research","Prototyping","Design Systems"],"is_featured":False,"description":"Shape the visual language and user experience of products used by millions worldwide.","requirements":"4+ years UX design, strong portfolio, experience with design systems.","benefits":"Creative environment, flexible PTO, design conference budget."},
            {"title":"Full-Stack Engineer","company":"DataFlow Inc.","industry":"technology","location":"San Francisco, CA","remote":True,"job_type":JobType.full_time,"salary_min":115000,"salary_max":155000,"skills_required":["React","Node.js","TypeScript","PostgreSQL","Redis"],"is_featured":True,"description":"Build the full product stack for our analytics platform used by 300+ enterprise customers.","requirements":"5+ years full-stack experience, TypeScript required, GraphQL a plus.","benefits":"Equity, 100% remote, $3K home office stipend."},
            {"title":"Backend Engineer – Golang","company":"CloudNative Corp","industry":"technology","location":"Seattle, WA","remote":True,"job_type":JobType.full_time,"salary_min":125000,"salary_max":165000,"skills_required":["Go","gRPC","Kubernetes","PostgreSQL"],"is_featured":False,"description":"Design and scale high-throughput microservices powering our cloud infrastructure platform.","requirements":"4+ years Go, experience with gRPC and distributed systems.","benefits":"Remote-first, stock options, annual team retreat."},
            {"title":"Machine Learning Engineer","company":"DataFlow Inc.","industry":"technology","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":135000,"salary_max":175000,"skills_required":["Python","PyTorch","MLflow","Kubernetes","SQL"],"is_featured":True,"description":"Productionise ML research into scalable inference pipelines serving millions of predictions daily.","requirements":"3+ years MLOps/ML engineering, PyTorch required, familiarity with feature stores.","benefits":"Top-tier compensation, research time allocation, GPU workstation."},
            {"title":"iOS Developer","company":"Acme Technologies","industry":"technology","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":105000,"salary_max":140000,"skills_required":["Swift","SwiftUI","Xcode","REST APIs","Core Data"],"is_featured":False,"description":"Build delightful mobile experiences for 10M+ iPhone users across our consumer app suite.","requirements":"4+ years Swift, App Store shipped app required, SwiftUI experience preferred.","benefits":"MacBook Pro, health + dental + vision, flexible hours."},
            {"title":"Android Developer","company":"Acme Technologies","industry":"technology","location":"New York, NY","remote":True,"job_type":JobType.full_time,"salary_min":100000,"salary_max":135000,"skills_required":["Kotlin","Jetpack Compose","Android SDK","MVVM","Firebase"],"is_featured":False,"description":"Craft high-quality Android experiences and improve app performance for our global user base.","requirements":"3+ years Kotlin, shipped production Android app, Compose experience a strong plus.","benefits":"Remote option, 401k, gym membership."},
            {"title":"Cloud Infrastructure Engineer","company":"CloudNative Corp","industry":"technology","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":120000,"salary_max":160000,"skills_required":["AWS","Terraform","Python","Linux","Monitoring"],"is_featured":False,"description":"Design and operate AWS infrastructure for SaaS products serving enterprise clients globally.","requirements":"5+ years cloud engineering, AWS Solutions Architect cert preferred.","benefits":"Fully remote, quarterly bonuses, learning stipend."},
            {"title":"QA Automation Engineer","company":"DataFlow Inc.","industry":"technology","location":"San Francisco, CA","remote":True,"job_type":JobType.full_time,"salary_min":90000,"salary_max":120000,"skills_required":["Selenium","Cypress","Python","CI/CD","API Testing"],"is_featured":False,"description":"Build comprehensive test automation frameworks to ensure quality across our entire product suite.","requirements":"3+ years test automation, Cypress or Playwright required.","benefits":"Remote-friendly, flexible PTO, equipment budget."},
            {"title":"Security Engineer","company":"Acme Technologies","industry":"technology","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":130000,"salary_max":175000,"skills_required":["Penetration Testing","AWS Security","Python","SIEM","SOC 2"],"is_featured":False,"description":"Protect our platform and 50M users by leading security reviews, pen tests, and incident response.","requirements":"5+ years application security, OSCP or CEH preferred.","benefits":"Top compensation, security conference budget, stock."},
            {"title":"Staff Engineer – Platform","company":"Acme Technologies","industry":"technology","location":"New York, NY","remote":True,"job_type":JobType.full_time,"salary_min":180000,"salary_max":230000,"skills_required":["System Design","Python","AWS","Leadership","PostgreSQL"],"is_featured":True,"description":"Drive technical strategy and architecture for our core platform serving 50M+ users globally.","requirements":"10+ years engineering, proven track record of large-scale system design.","benefits":"Top-of-market comp, equity, executive visibility."},
            {"title":"Frontend Engineer – React","company":"DataFlow Inc.","industry":"technology","location":"San Francisco, CA","remote":True,"job_type":JobType.full_time,"salary_min":110000,"salary_max":150000,"skills_required":["React","TypeScript","GraphQL","CSS","Webpack"],"is_featured":False,"description":"Build performant, beautiful UIs for our data analytics dashboard used by 10,000+ analysts.","requirements":"4+ years React, TypeScript required, experience with data-heavy UIs a plus.","benefits":"Unlimited PTO, 100% health coverage, remote."},
            {"title":"Site Reliability Engineer","company":"CloudNative Corp","industry":"technology","location":"Seattle, WA","remote":True,"job_type":JobType.full_time,"salary_min":130000,"salary_max":170000,"skills_required":["Kubernetes","Prometheus","Go","Python","Incident Management"],"is_featured":False,"description":"Own availability, latency, and performance for cloud-native infrastructure serving enterprise SLAs.","requirements":"4+ years SRE, strong Kubernetes experience, on-call comfortable.","benefits":"Strong comp, incident-free bonuses, remote."},
            {"title":"Data Engineer","company":"DataFlow Inc.","industry":"technology","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":105000,"salary_max":140000,"skills_required":["Apache Spark","dbt","Python","Snowflake","Airflow"],"is_featured":False,"description":"Build reliable data pipelines that power analytics and ML across the entire DataFlow product suite.","requirements":"3+ years data engineering, dbt or Airflow required.","benefits":"Remote-first, equity, learning budget."},
            {"title":"Junior Software Developer","company":"CloudNative Corp","industry":"technology","location":"Seattle, WA","remote":False,"job_type":JobType.full_time,"salary_min":70000,"salary_max":95000,"skills_required":["Python","JavaScript","Git","SQL","REST APIs"],"is_featured":False,"description":"Kickstart your engineering career working on real-world cloud infrastructure and developer tools.","requirements":"CS degree or bootcamp grad, 1+ year coding experience, eager to learn.","benefits":"Mentorship program, education budget, health benefits."},
            {"title":"Engineering Manager","company":"Acme Technologies","industry":"technology","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":170000,"salary_max":210000,"skills_required":["Engineering Leadership","System Design","Python","Agile","Hiring"],"is_featured":False,"description":"Lead a team of 8 engineers building core platform features. 50% coding, 50% leadership.","requirements":"5+ years engineering, 2+ years managing, technical depth required.","benefits":"Equity, executive perks, leadership development budget."},
            {"title":"AI/LLM Engineer","company":"DataFlow Inc.","industry":"technology","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":150000,"salary_max":200000,"skills_required":["Python","LLMs","LangChain","RAG","Vector Databases"],"is_featured":True,"description":"Build production LLM applications that help enterprise customers extract insight from their data at scale.","requirements":"Strong Python, hands-on LLM experience, familiarity with embeddings and RAG pipelines.","benefits":"Cutting-edge work, remote, top compensation."},
            {"title":"Blockchain Developer","company":"FinTech Partners","industry":"finance","location":"Austin, TX","remote":True,"job_type":JobType.full_time,"salary_min":120000,"salary_max":160000,"skills_required":["Solidity","Ethereum","Web3.js","TypeScript","Smart Contracts"],"is_featured":False,"description":"Build and audit smart contracts for our DeFi products. Deep blockchain engineering role.","requirements":"3+ years Solidity, understanding of DeFi protocols, security-minded.","benefits":"Token allocation, remote, cutting-edge work."},
            {"title":"Technical Writer","company":"CloudNative Corp","industry":"technology","location":"Remote","remote":True,"job_type":JobType.part_time,"salary_min":55000,"salary_max":75000,"skills_required":["Technical Writing","Markdown","Developer Docs","API Documentation"],"is_featured":False,"description":"Create clear, accurate developer documentation for our cloud infrastructure APIs and SDKs.","requirements":"3+ years technical writing for developer audiences, understanding of REST APIs.","benefits":"Flexible hours, remote, creative autonomy."},

            # ── Healthcare ──────────────────────────────────────────────────
            {"title":"Registered Nurse – ICU","company":"MetroHealth System","industry":"healthcare","location":"Cleveland, OH","remote":False,"job_type":JobType.full_time,"salary_min":72000,"salary_max":95000,"skills_required":["Critical Care","BLS","ACLS","IV Therapy"],"is_featured":False,"description":"Provide exceptional patient care in our 40-bed ICU. Night and day shifts available.","requirements":"Active RN license, BSN preferred, 2+ years ICU experience.","benefits":"Sign-on bonus up to $10K, tuition reimbursement, shift differentials."},
            {"title":"Clinical Research Coordinator","company":"NovaBio Labs","industry":"healthcare","location":"Boston, MA","remote":False,"job_type":JobType.full_time,"salary_min":60000,"salary_max":80000,"skills_required":["GCP","Clinical Trials","IRB","Data Collection","CTMS"],"is_featured":False,"description":"Coordinate Phase II/III clinical trials for our oncology pipeline. Work with PIs and regulatory teams.","requirements":"2+ years CRC experience, GCP certified, CTMS experience.","benefits":"Mission-driven work, full benefits, research conference budget."},
            {"title":"Physician Assistant – Urgent Care","company":"MetroHealth System","industry":"healthcare","location":"Cleveland, OH","remote":False,"job_type":JobType.full_time,"salary_min":95000,"salary_max":120000,"skills_required":["Clinical Assessment","Diagnosis","EMR","Patient Care","Suturing"],"is_featured":False,"description":"Deliver high-quality urgent care in a fast-paced, community-focused clinic setting.","requirements":"PA-C license, 2+ years urgent care or EM experience preferred.","benefits":"CME allowance, malpractice coverage, sign-on bonus."},
            {"title":"Radiologist Technologist","company":"MetroHealth System","industry":"healthcare","location":"Cleveland, OH","remote":False,"job_type":JobType.full_time,"salary_min":58000,"salary_max":78000,"skills_required":["MRI","CT Scan","X-Ray","PACS","Patient Positioning"],"is_featured":False,"description":"Perform and assist in diagnostic imaging procedures across modalities in our hospital system.","requirements":"ARRT certification, 2+ years imaging experience.","benefits":"Shift differential, full benefits, tuition assistance."},
            {"title":"Bioinformatics Scientist","company":"NovaBio Labs","industry":"healthcare","location":"Boston, MA","remote":True,"job_type":JobType.full_time,"salary_min":100000,"salary_max":135000,"skills_required":["Python","R","Genomics","NGS","Bioconductor"],"is_featured":False,"description":"Analyze large genomic datasets to discover biomarkers and support drug development pipelines.","requirements":"PhD in bioinformatics or computational biology, NGS pipeline experience.","benefits":"Research publications encouraged, equity, flexible hours."},
            {"title":"Medical Laboratory Scientist","company":"NovaBio Labs","industry":"healthcare","location":"Boston, MA","remote":False,"job_type":JobType.full_time,"salary_min":60000,"salary_max":82000,"skills_required":["PCR","Cell Culture","ELISA","Mass Spectrometry","Lab Safety"],"is_featured":False,"description":"Conduct laboratory assays and experiments supporting pre-clinical and clinical research programs.","requirements":"BS in Medical Lab Science or Biochemistry, ASCP certification preferred.","benefits":"Cutting-edge research environment, full benefits."},
            {"title":"Healthcare Data Analyst","company":"MetroHealth System","industry":"healthcare","location":"Cleveland, OH","remote":True,"job_type":JobType.full_time,"salary_min":65000,"salary_max":88000,"skills_required":["SQL","Tableau","Epic","Healthcare Analytics","Python"],"is_featured":False,"description":"Turn patient and operational data into actionable insights that improve care outcomes across our system.","requirements":"3+ years data analytics, healthcare domain knowledge, SQL proficient.","benefits":"Remote option, professional development, health benefits."},
            {"title":"Pharmacist – Retail","company":"MetroHealth System","industry":"healthcare","location":"Cleveland, OH","remote":False,"job_type":JobType.full_time,"salary_min":110000,"salary_max":130000,"skills_required":["Medication Dispensing","Patient Counseling","PharmD","Drug Interactions","Immunizations"],"is_featured":False,"description":"Deliver patient-centered pharmacy services and medication therapy management at our outpatient pharmacy.","requirements":"PharmD, active Ohio pharmacist license.","benefits":"Loan repayment assistance, competitive pay, full benefits."},
            {"title":"Mental Health Counselor","company":"MetroHealth System","industry":"healthcare","location":"Cleveland, OH","remote":True,"job_type":JobType.full_time,"salary_min":52000,"salary_max":72000,"skills_required":["CBT","Motivational Interviewing","Mental Health Assessment","Case Management","Telehealth"],"is_featured":False,"description":"Provide evidence-based counseling to patients via telehealth and in-person in our behavioral health division.","requirements":"LPC or LISW, 2+ years clinical experience.","benefits":"Supervision toward licensure, flexible scheduling, full benefits."},
            {"title":"Surgical Technologist","company":"MetroHealth System","industry":"healthcare","location":"Cleveland, OH","remote":False,"job_type":JobType.full_time,"salary_min":48000,"salary_max":65000,"skills_required":["Sterile Technique","Surgical Instruments","OR Procedures","Anatomy","Team Collaboration"],"is_featured":False,"description":"Support surgical teams in the operating room, maintaining the sterile field and passing instruments.","requirements":"CST certification, 1+ year OR experience preferred.","benefits":"Shift bonuses, tuition assistance, 403(b)."},

            # ── Finance ──────────────────────────────────────────────────────
            {"title":"Product Manager – Growth","company":"FinTech Partners","industry":"finance","location":"Austin, TX","remote":True,"job_type":JobType.full_time,"salary_min":115000,"salary_max":145000,"skills_required":["Product Strategy","A/B Testing","SQL","Roadmapping"],"is_featured":False,"description":"Own and drive the growth product roadmap for our consumer fintech app with 2M users.","requirements":"4+ years PM experience, fintech or consumer app background strongly preferred.","benefits":"Stock options, flexible hybrid schedule, wellness stipend."},
            {"title":"Financial Analyst","company":"FinTech Partners","industry":"finance","location":"Austin, TX","remote":False,"job_type":JobType.full_time,"salary_min":72000,"salary_max":98000,"skills_required":["Financial Modeling","Excel","SQL","FP&A","Tableau"],"is_featured":False,"description":"Support strategic planning with financial models, variance analysis, and executive-level reporting.","requirements":"2+ years FP&A, CFA Level I a plus, strong Excel modeling skills.","benefits":"Performance bonus, 401k match, hybrid schedule."},
            {"title":"Risk Analyst","company":"FinTech Partners","industry":"finance","location":"Austin, TX","remote":False,"job_type":JobType.full_time,"salary_min":85000,"salary_max":115000,"skills_required":["Risk Management","Python","SQL","Credit Risk","Regulatory Compliance"],"is_featured":False,"description":"Identify, model and mitigate financial risk across our lending and payments product lines.","requirements":"3+ years credit or market risk, Python for data analysis required.","benefits":"Stock options, hybrid, competitive pay."},
            {"title":"Compliance Officer","company":"FinTech Partners","industry":"finance","location":"Austin, TX","remote":False,"job_type":JobType.full_time,"salary_min":95000,"salary_max":130000,"skills_required":["AML","KYC","BSA","Regulatory Reporting","FINRA"],"is_featured":False,"description":"Ensure our fintech products meet all regulatory requirements. Work closely with legal and product.","requirements":"5+ years compliance in fintech or banking, CAMS certification preferred.","benefits":"Hybrid, bonus, comprehensive benefits."},
            {"title":"Quantitative Analyst","company":"FinTech Partners","industry":"finance","location":"Austin, TX","remote":True,"job_type":JobType.full_time,"salary_min":130000,"salary_max":180000,"skills_required":["Python","Statistics","Machine Learning","Algorithmic Trading","SQL"],"is_featured":False,"description":"Build quantitative models to price products, manage risk, and identify alpha in our trading division.","requirements":"PhD or MS in Quantitative Finance, Statistics, or Math. Strong Python.","benefits":"Top compensation, performance bonus, intellectual challenge."},
            {"title":"Investment Banking Analyst","company":"FinTech Partners","industry":"finance","location":"Austin, TX","remote":False,"job_type":JobType.full_time,"salary_min":100000,"salary_max":140000,"skills_required":["DCF Modeling","M&A","Pitch Decks","Excel","Bloomberg"],"is_featured":False,"description":"Support M&A transactions and capital raises for mid-market technology and fintech companies.","requirements":"1-3 years IB experience or top-tier MBA, strong financial modeling.","benefits":"High learning curve, deal exposure, competitive bonus."},
            {"title":"Bookkeeper","company":"FinTech Partners","industry":"finance","location":"Austin, TX","remote":True,"job_type":JobType.part_time,"salary_min":42000,"salary_max":58000,"skills_required":["QuickBooks","Accounts Payable","Accounts Receivable","Bank Reconciliation","Excel"],"is_featured":False,"description":"Maintain accurate financial records, process invoices, and support month-end close for our operations team.","requirements":"2+ years bookkeeping, QuickBooks proficiency, attention to detail.","benefits":"Flexible hours, remote, growth opportunities."},
            {"title":"Treasury Manager","company":"FinTech Partners","industry":"finance","location":"Austin, TX","remote":False,"job_type":JobType.full_time,"salary_min":110000,"salary_max":145000,"skills_required":["Cash Management","FX Hedging","Treasury Systems","Banking Relationships","Excel"],"is_featured":False,"description":"Manage corporate liquidity, FX exposure, and banking relationships for a high-growth fintech.","requirements":"6+ years treasury, CTP certification preferred.","benefits":"Equity, hybrid, strong growth path."},

            # ── Engineering ──────────────────────────────────────────────────
            {"title":"Civil Engineer – Infrastructure","company":"GreenBridge Energy","industry":"engineering","location":"Denver, CO","remote":False,"job_type":JobType.full_time,"salary_min":80000,"salary_max":110000,"skills_required":["AutoCAD","Civil 3D","Stormwater Management","Site Design","PE License"],"is_featured":False,"description":"Design and manage civil engineering aspects of utility-scale solar and wind energy projects.","requirements":"PE license preferred, 4+ years civil design experience, renewable energy a plus.","benefits":"Meaningful work, competitive pay, 401k, relocation assistance."},
            {"title":"Electrical Engineer – Power Systems","company":"GreenBridge Energy","industry":"engineering","location":"Denver, CO","remote":False,"job_type":JobType.full_time,"salary_min":90000,"salary_max":125000,"skills_required":["Power Systems","SCADA","AutoCAD Electrical","PLC Programming","Grid Interconnection"],"is_featured":False,"description":"Design electrical systems for utility-scale renewable energy facilities from concept to commissioning.","requirements":"BSEE, 4+ years power systems design, grid interconnection experience strongly preferred.","benefits":"Equity stake, relocation, mission-driven culture."},
            {"title":"Structural Engineer","company":"GreenBridge Energy","industry":"engineering","location":"Denver, CO","remote":False,"job_type":JobType.full_time,"salary_min":85000,"salary_max":115000,"skills_required":["STAAD Pro","Structural Analysis","Foundation Design","AutoCAD","PE License"],"is_featured":False,"description":"Perform structural analysis and design for solar mounting systems, substations, and O&M facilities.","requirements":"PE license, 4+ years structural engineering, renewable energy experience preferred.","benefits":"Dynamic projects, competitive comp, collaborative team."},
            {"title":"Mechanical Engineer – Product","company":"Nimble Manufacturing","industry":"engineering","location":"Detroit, MI","remote":False,"job_type":JobType.full_time,"salary_min":78000,"salary_max":105000,"skills_required":["SolidWorks","GD&T","FEA","DFM","Manufacturing Processes"],"is_featured":False,"description":"Design and develop precision mechanical components for automotive and aerospace manufacturing.","requirements":"BSME, 3+ years product design, SolidWorks proficiency required.","benefits":"Tuition reimbursement, patent support, strong benefits package."},
            {"title":"Manufacturing Engineer","company":"Nimble Manufacturing","industry":"engineering","location":"Detroit, MI","remote":False,"job_type":JobType.full_time,"salary_min":72000,"salary_max":98000,"skills_required":["Lean Manufacturing","Six Sigma","CAD","Process Improvement","FMEA"],"is_featured":False,"description":"Optimize production processes, reduce waste, and improve quality for our precision parts facility.","requirements":"3+ years manufacturing engineering, Six Sigma Green Belt a plus.","benefits":"Overtime pay, advancement opportunities, 401k."},
            {"title":"Environmental Engineer","company":"GreenBridge Energy","industry":"engineering","location":"Denver, CO","remote":True,"job_type":JobType.full_time,"salary_min":75000,"salary_max":100000,"skills_required":["Environmental Impact Assessment","NEPA","Permitting","GIS","Stormwater"],"is_featured":False,"description":"Lead environmental permitting and compliance for utility-scale renewable energy projects nationwide.","requirements":"BS in Environmental Engineering or Science, 3+ years NEPA permitting experience.","benefits":"Meaningful mission, remote-friendly, travel stipend."},
            {"title":"Quality Control Engineer","company":"Nimble Manufacturing","industry":"manufacturing","location":"Detroit, MI","remote":False,"job_type":JobType.full_time,"salary_min":65000,"salary_max":88000,"skills_required":["CMM","SPC","APQP","ISO 9001","Measurement Systems Analysis"],"is_featured":False,"description":"Develop and maintain quality systems ensuring our precision parts exceed customer specifications.","requirements":"3+ years QC in automotive or aerospace, CMM operation required.","benefits":"Production bonus, full benefits, stable company."},
            {"title":"Process Engineer – Chemical","company":"Nimble Manufacturing","industry":"manufacturing","location":"Detroit, MI","remote":False,"job_type":JobType.full_time,"salary_min":80000,"salary_max":108000,"skills_required":["Process Optimization","Chemical Engineering","PLC","Safety","Hazop"],"is_featured":False,"description":"Improve chemical processing operations for our coating and surface treatment production lines.","requirements":"BS Chemical Engineering, 4+ years process engineering in manufacturing.","benefits":"Technical growth, tuition support, full benefits."},

            # ── Marketing ──────────────────────────────────────────────────
            {"title":"Marketing Manager","company":"Acme Technologies","industry":"marketing","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":90000,"salary_max":120000,"skills_required":["Digital Marketing","SEO","Content Strategy","Google Analytics","HubSpot"],"is_featured":False,"description":"Lead integrated marketing campaigns across digital and offline channels for our B2B SaaS products.","requirements":"5+ years B2B marketing, martech stack experience, strong copywriting.","benefits":"Performance bonus, creative freedom, growth path."},
            {"title":"Content Marketing Specialist","company":"DataFlow Inc.","industry":"marketing","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":65000,"salary_max":88000,"skills_required":["Content Writing","SEO","WordPress","Social Media","Analytics"],"is_featured":False,"description":"Create compelling content that drives organic growth and thought leadership for our data platform.","requirements":"3+ years content marketing, technical writing ability, strong SEO understanding.","benefits":"100% remote, creative autonomy, learning stipend."},
            {"title":"SEO Specialist","company":"RetailNext","industry":"marketing","location":"Atlanta, GA","remote":True,"job_type":JobType.full_time,"salary_min":58000,"salary_max":80000,"skills_required":["SEO","Ahrefs","Google Search Console","Content Optimization","Link Building"],"is_featured":False,"description":"Drive organic traffic growth for our retail analytics platform through technical and content SEO.","requirements":"3+ years SEO, strong analytics background, e-commerce SEO preferred.","benefits":"Remote, flexible hours, equipment allowance."},
            {"title":"Paid Media Manager","company":"RetailNext","industry":"marketing","location":"Atlanta, GA","remote":True,"job_type":JobType.full_time,"salary_min":70000,"salary_max":95000,"skills_required":["Google Ads","Facebook Ads","PPC","Attribution","A/B Testing"],"is_featured":False,"description":"Manage $2M+ annual paid media budget across Google, Meta, and LinkedIn for our SaaS products.","requirements":"4+ years paid media management, strong ROAS mindset, B2B SaaS preferred.","benefits":"Performance bonus, remote, career growth."},
            {"title":"Brand Designer","company":"Acme Technologies","industry":"marketing","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":72000,"salary_max":98000,"skills_required":["Adobe Creative Suite","Brand Identity","Motion Graphics","Typography","Print Design"],"is_featured":False,"description":"Develop and evolve our brand identity across digital, print, and event touchpoints.","requirements":"4+ years brand design, strong portfolio, motion graphics a plus.","benefits":"Creative culture, equipment budget, flexible PTO."},
            {"title":"Email Marketing Specialist","company":"FinTech Partners","industry":"marketing","location":"Austin, TX","remote":True,"job_type":JobType.full_time,"salary_min":58000,"salary_max":78000,"skills_required":["Mailchimp","HubSpot","Segmentation","Copywriting","A/B Testing"],"is_featured":False,"description":"Own our email marketing channel, driving engagement and conversion across 500K+ subscribers.","requirements":"3+ years email marketing, Klaviyo or HubSpot expertise, strong copywriting.","benefits":"Remote, growth potential, great team."},
            {"title":"Social Media Manager","company":"RetailNext","industry":"marketing","location":"Atlanta, GA","remote":True,"job_type":JobType.part_time,"salary_min":40000,"salary_max":55000,"skills_required":["LinkedIn","Instagram","Content Calendar","Analytics","Community Management"],"is_featured":False,"description":"Grow and engage our social media presence across LinkedIn, Twitter/X, and Instagram.","requirements":"2+ years social media management, B2B SaaS experience preferred.","benefits":"Flexible schedule, remote, creative freedom."},

            # ── Education ──────────────────────────────────────────────────
            {"title":"Curriculum Developer","company":"EduPath Learning","industry":"education","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":65000,"salary_max":88000,"skills_required":["Instructional Design","ADDIE","Articulate 360","LMS","Assessment Design"],"is_featured":False,"description":"Design engaging online curriculum for K-12 and corporate learning programs across our platform.","requirements":"3+ years instructional design, Articulate 360 required, K-12 experience preferred.","benefits":"100% remote, meaningful mission, professional development."},
            {"title":"Online Instructor – Data Science","company":"EduPath Learning","industry":"education","location":"Remote","remote":True,"job_type":JobType.contract,"salary_min":50000,"salary_max":70000,"skills_required":["Python","Data Science","Machine Learning","Teaching","Curriculum Design"],"is_featured":False,"description":"Create and teach online data science courses to adult learners on our platform.","requirements":"Industry data science experience, passion for teaching, prior online instruction a plus.","benefits":"Flexible schedule, royalty on course sales, remote."},
            {"title":"Learning & Development Manager","company":"Nimble Manufacturing","industry":"education","location":"Detroit, MI","remote":False,"job_type":JobType.full_time,"salary_min":72000,"salary_max":98000,"skills_required":["Training Design","LMS Administration","Onboarding","Leadership Development","Needs Assessment"],"is_featured":False,"description":"Build and run training programs that upskill our 1,200-person manufacturing workforce.","requirements":"5+ years L&D, manufacturing or industrial environment preferred, LMS admin experience.","benefits":"Meaningful impact, full benefits, tuition reimbursement."},
            {"title":"K-12 Science Teacher","company":"EduPath Learning","industry":"education","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":48000,"salary_max":68000,"skills_required":["Science Education","Curriculum Design","Zoom Teaching","Student Assessment","NGSS"],"is_featured":False,"description":"Teach online science courses to middle and high school students on our virtual learning platform.","requirements":"Teaching certification, 2+ years classroom experience, enthusiasm for virtual instruction.","benefits":"Remote, summers flexible, passionate community."},
            {"title":"EdTech Product Manager","company":"EduPath Learning","industry":"education","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":90000,"salary_max":120000,"skills_required":["Product Management","EdTech","Agile","User Research","Data Analysis"],"is_featured":False,"description":"Lead product development for our adaptive learning platform serving 500K+ students.","requirements":"4+ years PM experience, EdTech background a strong plus.","benefits":"Mission-driven work, equity, remote-first."},

            # ── Legal ──────────────────────────────────────────────────────
            {"title":"Corporate Attorney","company":"LexaCorp Legal","industry":"legal","location":"Chicago, IL","remote":False,"job_type":JobType.full_time,"salary_min":130000,"salary_max":185000,"skills_required":["M&A","Contract Negotiation","Corporate Law","Due Diligence","SEC Compliance"],"is_featured":False,"description":"Advise clients on M&A transactions, corporate governance, and securities compliance.","requirements":"JD from top law school, 4+ years big law corporate experience, IL bar.","benefits":"High-profile deals, billable bonus, firm events."},
            {"title":"Paralegal – Litigation","company":"LexaCorp Legal","industry":"legal","location":"Chicago, IL","remote":False,"job_type":JobType.full_time,"salary_min":52000,"salary_max":72000,"skills_required":["Legal Research","Westlaw","Case Management","Document Review","E-Discovery"],"is_featured":False,"description":"Support litigation attorneys in case preparation, document review, and court filings.","requirements":"Paralegal certificate or relevant degree, 2+ years litigation support.","benefits":"Professional development, health benefits, mentored growth."},
            {"title":"Legal Operations Manager","company":"LexaCorp Legal","industry":"legal","location":"Chicago, IL","remote":True,"job_type":JobType.full_time,"salary_min":95000,"salary_max":130000,"skills_required":["Legal Tech","Contract Management","Process Improvement","Vendor Management","Analytics"],"is_featured":False,"description":"Modernize and optimize legal operations using technology and data-driven process improvements.","requirements":"5+ years legal operations, legal tech expertise (Ironclad, Clio, etc.).","benefits":"Remote-friendly, growth path, competitive comp."},
            {"title":"Employment Attorney","company":"LexaCorp Legal","industry":"legal","location":"Chicago, IL","remote":False,"job_type":JobType.full_time,"salary_min":110000,"salary_max":155000,"skills_required":["Employment Law","EEOC","ADA","Litigation","Compliance"],"is_featured":False,"description":"Counsel employers on labor relations, discrimination claims, and employment policy compliance.","requirements":"JD, 3+ years employment law, IL bar admission.","benefits":"Billable bonus, client variety, professional events."},
            {"title":"Contract Specialist","company":"GreenBridge Energy","industry":"legal","location":"Denver, CO","remote":True,"job_type":JobType.full_time,"salary_min":72000,"salary_max":98000,"skills_required":["Contract Review","Negotiation","Risk Assessment","EPC Contracts","Power Purchase Agreements"],"is_featured":False,"description":"Review, negotiate, and manage commercial contracts for large-scale renewable energy projects.","requirements":"3+ years contract management, energy sector contracts preferred.","benefits":"Mission-driven, remote-flexible, growth company."},

            # ── Retail ──────────────────────────────────────────────────────
            {"title":"Retail Store Manager","company":"RetailNext","industry":"retail","location":"Atlanta, GA","remote":False,"job_type":JobType.full_time,"salary_min":55000,"salary_max":78000,"skills_required":["Team Leadership","Inventory Management","Sales","Customer Service","POS Systems"],"is_featured":False,"description":"Lead a high-performing retail team, drive sales goals, and deliver exceptional customer experiences.","requirements":"3+ years retail management, proven sales leadership track record.","benefits":"Performance bonus, discount, advancement opportunities."},
            {"title":"E-Commerce Manager","company":"RetailNext","industry":"retail","location":"Atlanta, GA","remote":True,"job_type":JobType.full_time,"salary_min":75000,"salary_max":100000,"skills_required":["Shopify","E-Commerce Strategy","Digital Marketing","Analytics","Inventory"],"is_featured":False,"description":"Own and grow our direct-to-consumer e-commerce channel from product listings to conversion optimization.","requirements":"4+ years e-commerce management, Shopify or Magento experience required.","benefits":"Remote, performance bonus, cross-functional impact."},
            {"title":"Buyer – Apparel","company":"RetailNext","industry":"retail","location":"Atlanta, GA","remote":False,"job_type":JobType.full_time,"salary_min":62000,"salary_max":85000,"skills_required":["Merchandise Planning","Vendor Negotiation","Trend Forecasting","Open-to-Buy","Retail Math"],"is_featured":False,"description":"Source, negotiate, and manage apparel assortments that drive sales across our 200+ store network.","requirements":"3+ years retail buying experience, strong vendor relationships.","benefits":"Merchandise discount, travel, competitive comp."},
            {"title":"Visual Merchandiser","company":"RetailNext","industry":"retail","location":"Atlanta, GA","remote":False,"job_type":JobType.full_time,"salary_min":42000,"salary_max":58000,"skills_required":["Visual Merchandising","Store Layout","Brand Standards","Creative Design","Planogram"],"is_featured":False,"description":"Create compelling in-store displays and experiences that drive foot traffic and product engagement.","requirements":"2+ years visual merchandising, retail or agency background.","benefits":"Creative role, travel, employee discount."},
            {"title":"Supply Chain Analyst – Retail","company":"RetailNext","industry":"retail","location":"Atlanta, GA","remote":True,"job_type":JobType.full_time,"salary_min":60000,"salary_max":82000,"skills_required":["Supply Chain","Demand Planning","Excel","SAP","Inventory Optimization"],"is_featured":False,"description":"Optimize inventory levels, forecast demand, and improve supply chain efficiency across our store network.","requirements":"2+ years supply chain analytics, retail preferred, SAP experience a plus.","benefits":"Remote option, professional development, strong team."},

            # ── Logistics ──────────────────────────────────────────────────
            {"title":"Logistics Coordinator","company":"SwiftLogix","industry":"logistics","location":"Dallas, TX","remote":False,"job_type":JobType.full_time,"salary_min":48000,"salary_max":65000,"skills_required":["Freight Management","TMS","Carrier Negotiation","Customs","Excel"],"is_featured":False,"description":"Coordinate domestic and international freight shipments, ensuring on-time delivery and cost efficiency.","requirements":"2+ years logistics coordination, TMS experience, attention to detail.","benefits":"Growth company, full benefits, advancement track."},
            {"title":"Supply Chain Manager","company":"SwiftLogix","industry":"logistics","location":"Dallas, TX","remote":False,"job_type":JobType.full_time,"salary_min":85000,"salary_max":115000,"skills_required":["S&OP","Supplier Management","Demand Planning","SAP","Lean"],"is_featured":False,"description":"Lead end-to-end supply chain strategy and operations for our 3PL clients in the consumer goods sector.","requirements":"6+ years supply chain management, APICS certification preferred.","benefits":"Profit sharing, full benefits, leadership exposure."},
            {"title":"Warehouse Supervisor","company":"SwiftLogix","industry":"logistics","location":"Dallas, TX","remote":False,"job_type":JobType.full_time,"salary_min":52000,"salary_max":72000,"skills_required":["Warehouse Operations","WMS","Team Leadership","Safety","Inventory Control"],"is_featured":False,"description":"Supervise daily warehouse operations including receiving, picking, packing, and shipping for our fulfillment center.","requirements":"3+ years warehouse supervision, WMS experience, forklift certified preferred.","benefits":"Shift bonus, full benefits, overtime opportunities."},
            {"title":"Fleet Manager","company":"SwiftLogix","industry":"logistics","location":"Dallas, TX","remote":False,"job_type":JobType.full_time,"salary_min":70000,"salary_max":95000,"skills_required":["Fleet Management","DOT Compliance","Driver Management","GPS Tracking","Preventive Maintenance"],"is_featured":False,"description":"Oversee a fleet of 150 trucks, ensuring compliance, safety, and operational efficiency.","requirements":"5+ years fleet management, DOT knowledge, CDL Class A a plus.","benefits":"Company vehicle, competitive comp, growth path."},
            {"title":"Freight Broker","company":"SwiftLogix","industry":"logistics","location":"Dallas, TX","remote":True,"job_type":JobType.full_time,"salary_min":45000,"salary_max":80000,"skills_required":["Load Board","Carrier Relations","Negotiation","DAT","Sales"],"is_featured":False,"description":"Match shippers with carriers, negotiate rates, and build lasting carrier relationships to grow our brokerage book.","requirements":"1+ year freight brokerage experience, hunter mentality, strong negotiation.","benefits":"Uncapped commission, remote, training provided."},

            # ── Manufacturing ───────────────────────────────────────────────
            {"title":"Production Supervisor","company":"Nimble Manufacturing","industry":"manufacturing","location":"Detroit, MI","remote":False,"job_type":JobType.full_time,"salary_min":65000,"salary_max":88000,"skills_required":["Production Planning","Team Leadership","Safety","5S","OEE"],"is_featured":False,"description":"Lead production teams on our automotive parts manufacturing line, ensuring quality, safety, and throughput targets.","requirements":"4+ years manufacturing supervision, automotive sector preferred.","benefits":"Shift differential, profit sharing, full benefits."},
            {"title":"CNC Machinist","company":"Nimble Manufacturing","industry":"manufacturing","location":"Detroit, MI","remote":False,"job_type":JobType.full_time,"salary_min":52000,"salary_max":72000,"skills_required":["CNC Machining","G-Code","Blueprints","Metrology","Tooling Setup"],"is_featured":False,"description":"Set up and operate CNC mills and lathes to produce precision components for automotive and aerospace clients.","requirements":"3+ years CNC machining, fanuc controls preferred, blueprint reading required.","benefits":"Skilled trade premium, overtime, 401k."},
            {"title":"Industrial Engineer","company":"Nimble Manufacturing","industry":"manufacturing","location":"Detroit, MI","remote":False,"job_type":JobType.full_time,"salary_min":75000,"salary_max":100000,"skills_required":["Time Study","Value Stream Mapping","AutoCAD","Ergonomics","Capacity Planning"],"is_featured":False,"description":"Design efficient production systems and drive continuous improvement initiatives across our facilities.","requirements":"BS Industrial Engineering, 3+ years manufacturing IE experience.","benefits":"Leadership track, tuition reimbursement, full benefits."},
            {"title":"Maintenance Technician","company":"Nimble Manufacturing","industry":"manufacturing","location":"Detroit, MI","remote":False,"job_type":JobType.full_time,"salary_min":48000,"salary_max":68000,"skills_required":["Preventive Maintenance","PLC Troubleshooting","Hydraulics","Electrical","CMMS"],"is_featured":False,"description":"Maintain and repair production equipment to maximize uptime in our precision manufacturing facility.","requirements":"3+ years industrial maintenance, electrical and mechanical knowledge required.","benefits":"Overtime, tool allowance, full benefits."},

            # ── Additional cross-industry ────────────────────────────────────
            {"title":"Data Analyst","company":"RetailNext","industry":"technology","location":"Atlanta, GA","remote":True,"job_type":JobType.full_time,"salary_min":68000,"salary_max":90000,"skills_required":["SQL","Python","Tableau","Google Analytics","Excel"],"is_featured":False,"description":"Analyse customer and product data to generate insights that drive merchandising and marketing decisions.","requirements":"2+ years data analysis, SQL proficient, Tableau preferred.","benefits":"Remote, growth environment, full benefits."},
            {"title":"Business Development Representative","company":"DataFlow Inc.","industry":"technology","location":"San Francisco, CA","remote":True,"job_type":JobType.full_time,"salary_min":60000,"salary_max":80000,"skills_required":["Outbound Sales","CRM","Prospecting","SaaS Sales","Communication"],"is_featured":False,"description":"Drive top-of-funnel pipeline through outbound prospecting and qualification for our enterprise sales team.","requirements":"1+ year SDR/BDR experience, Salesforce or HubSpot, coachable mindset.","benefits":"Uncapped commission, remote, career growth into AE."},
            {"title":"Account Executive – Enterprise","company":"DataFlow Inc.","industry":"technology","location":"San Francisco, CA","remote":True,"job_type":JobType.full_time,"salary_min":120000,"salary_max":180000,"skills_required":["Enterprise Sales","SaaS","Negotiation","Salesforce","Pipeline Management"],"is_featured":False,"description":"Close complex, multi-stakeholder enterprise deals for our data platform. ACV $200K–$2M.","requirements":"4+ years enterprise SaaS sales, consistent quota attainment required.","benefits":"Uncapped OTE, equity, President's Club trips."},
            {"title":"Customer Success Manager","company":"DataFlow Inc.","industry":"technology","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":80000,"salary_max":110000,"skills_required":["Customer Success","Onboarding","SaaS","Renewal Management","Stakeholder Management"],"is_featured":False,"description":"Own a portfolio of enterprise accounts, driving adoption, expansion, and renewal for our data platform.","requirements":"3+ years CSM in SaaS, strong executive communication, Gainsight preferred.","benefits":"Remote, variable comp on expansion, career growth."},
            {"title":"HR Business Partner","company":"Acme Technologies","industry":"technology","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":90000,"salary_max":120000,"skills_required":["HRBP","Employee Relations","Talent Development","Workday","Organizational Design"],"is_featured":False,"description":"Partner with engineering and product leaders to drive talent strategy, performance, and culture.","requirements":"5+ years HRBP, tech company preferred, Workday experience.","benefits":"Impactful role, equity, full benefits."},
            {"title":"Recruiter – Technical","company":"Acme Technologies","industry":"technology","location":"New York, NY","remote":True,"job_type":JobType.full_time,"salary_min":75000,"salary_max":100000,"skills_required":["Technical Recruiting","Sourcing","Greenhouse","LinkedIn Recruiter","Negotiation"],"is_featured":False,"description":"Source and close top engineering talent in a highly competitive market for our growing tech platform.","requirements":"3+ years technical recruiting, agency or in-house, strong sourcing skills.","benefits":"Remote-friendly, competitive comp, high-impact role."},
            {"title":"Operations Manager","company":"SwiftLogix","industry":"logistics","location":"Dallas, TX","remote":False,"job_type":JobType.full_time,"salary_min":80000,"salary_max":108000,"skills_required":["Operations Management","P&L","Process Improvement","Team Leadership","KPIs"],"is_featured":False,"description":"Manage daily operations for our Dallas fulfilment hub, leading 60 staff across multiple shifts.","requirements":"5+ years operations management, 3PL or distribution centre experience.","benefits":"Profit sharing, advancement path, full benefits."},
            {"title":"Project Manager – Construction","company":"GreenBridge Energy","industry":"engineering","location":"Denver, CO","remote":False,"job_type":JobType.full_time,"salary_min":95000,"salary_max":130000,"skills_required":["Project Management","MS Project","Construction Management","Budgeting","Stakeholder Management"],"is_featured":False,"description":"Lead construction of utility-scale solar and wind projects from NTP through commercial operation.","requirements":"5+ years construction PM, renewable energy preferred, PMP certification a plus.","benefits":"Project bonuses, travel, mission-driven work."},
            {"title":"Graphic Designer","company":"EduPath Learning","industry":"education","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":55000,"salary_max":75000,"skills_required":["Adobe Illustrator","Photoshop","UI Design","Motion Graphics","Brand Design"],"is_featured":False,"description":"Create visual assets for our online courses, marketing materials, and mobile learning app.","requirements":"3+ years graphic design, education or tech industry preferred.","benefits":"100% remote, creative role, meaningful mission."},
            {"title":"Cybersecurity Analyst","company":"Acme Technologies","industry":"technology","location":"New York, NY","remote":True,"job_type":JobType.full_time,"salary_min":95000,"salary_max":130000,"skills_required":["SIEM","Vulnerability Management","Incident Response","Python","Splunk"],"is_featured":False,"description":"Monitor, detect, and respond to security threats across our global platform infrastructure.","requirements":"3+ years SOC or security operations, SPLUNK or Sentinel experience.","benefits":"Cutting-edge tooling, remote-friendly, top compensation."},
            {"title":"Product Designer","company":"DataFlow Inc.","industry":"technology","location":"San Francisco, CA","remote":True,"job_type":JobType.full_time,"salary_min":110000,"salary_max":148000,"skills_required":["Figma","User Research","Interaction Design","Design Systems","Prototyping"],"is_featured":True,"description":"Shape the end-to-end experience of our analytics platform — from research through pixel-perfect delivery.","requirements":"4+ years product design, data-heavy product experience a strong plus.","benefits":"Equity, remote, top-tier design culture."},
            {"title":"Scrum Master","company":"Acme Technologies","industry":"technology","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":95000,"salary_max":125000,"skills_required":["Scrum","Agile","Jira","Facilitation","Team Coaching"],"is_featured":False,"description":"Facilitate agile ceremonies and remove impediments for two cross-functional engineering squads.","requirements":"CSM or PSM certified, 3+ years Scrum Master experience, tech background preferred.","benefits":"Strong culture, career path, full benefits."},
            {"title":"Tax Manager","company":"FinTech Partners","industry":"finance","location":"Austin, TX","remote":True,"job_type":JobType.full_time,"salary_min":110000,"salary_max":148000,"skills_required":["Tax Compliance","ASC 740","Federal Tax","CPA","Tax Provision"],"is_featured":False,"description":"Own federal and state tax compliance, provision, and planning for a high-growth fintech company.","requirements":"CPA, 6+ years tax with public accounting background, fintech or tech company experience.","benefits":"Remote, equity, strong growth trajectory."},
            {"title":"Nursing Home Administrator","company":"MetroHealth System","industry":"healthcare","location":"Cleveland, OH","remote":False,"job_type":JobType.full_time,"salary_min":85000,"salary_max":115000,"skills_required":["Long-Term Care","Regulatory Compliance","Staff Management","Budget Management","CMS"],"is_featured":False,"description":"Lead operations, staff, and regulatory compliance for our 120-bed skilled nursing facility.","requirements":"NHA license, 3+ years long-term care administration.","benefits":"Sign-on bonus, full benefits, community impact."},
            {"title":"Renewable Energy Analyst","company":"GreenBridge Energy","industry":"engineering","location":"Denver, CO","remote":True,"job_type":JobType.full_time,"salary_min":70000,"salary_max":95000,"skills_required":["Energy Modeling","PVsyst","Python","Financial Modeling","GIS"],"is_featured":False,"description":"Conduct energy yield analysis, resource assessment, and financial modelling for solar and wind projects.","requirements":"2+ years renewable energy analysis, PVsyst or HOMER proficiency.","benefits":"Mission-driven, remote-friendly, great team."},
            {"title":"Retail IT Support Specialist","company":"RetailNext","industry":"technology","location":"Atlanta, GA","remote":False,"job_type":JobType.full_time,"salary_min":48000,"salary_max":65000,"skills_required":["Help Desk","Windows","Networking","POS Support","Active Directory"],"is_featured":False,"description":"Provide on-site and remote IT support for our retail store network of 200+ locations.","requirements":"2+ years IT support, retail POS experience strongly preferred.","benefits":"Advancement opportunities, full benefits, growth company."},
            {"title":"Instructional Technology Specialist","company":"EduPath Learning","industry":"education","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":60000,"salary_max":82000,"skills_required":["LMS Administration","Canvas","Video Production","eLearning Tools","Training"],"is_featured":False,"description":"Support faculty and course developers in using edtech tools to create engaging online learning experiences.","requirements":"3+ years instructional technology, LMS administration required.","benefits":"Remote, education mission, professional development."},

            # ── Horizon AI ──────────────────────────────────────────────────
            {"title":"AI Research Scientist","company":"Horizon AI","industry":"technology","location":"San Francisco, CA","remote":True,"job_type":JobType.full_time,"salary_min":180000,"salary_max":250000,"skills_required":["Python","PyTorch","NLP","Reinforcement Learning","Research"],"is_featured":True,"description":"Conduct cutting-edge AI research and publish findings that push the boundaries of what's possible with large language models.","requirements":"PhD in Machine Learning or related field, publications at NeurIPS/ICML/ICLR preferred.","benefits":"Research freedom, top compensation, GPU cluster access, publication encouraged."},
            {"title":"Prompt Engineer","company":"Horizon AI","industry":"technology","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":110000,"salary_max":150000,"skills_required":["LLMs","Prompt Design","Python","NLP","Evaluation"],"is_featured":False,"description":"Design, test, and optimise prompts that power our AI products across reasoning, coding, and creative tasks.","requirements":"Strong Python, deep familiarity with GPT-4/Claude APIs, systematic evaluation mindset.","benefits":"Remote, frontier AI work, learning stipend."},
            {"title":"MLOps Platform Engineer","company":"Horizon AI","industry":"technology","location":"San Francisco, CA","remote":True,"job_type":JobType.full_time,"salary_min":145000,"salary_max":195000,"skills_required":["Kubernetes","MLflow","Python","Ray","Distributed Training"],"is_featured":False,"description":"Build the infrastructure that trains and serves billion-parameter models reliably and efficiently at scale.","requirements":"4+ years platform/infrastructure engineering, hands-on GPU cluster management.","benefits":"Equity, remote option, state-of-the-art tooling."},
            {"title":"AI Safety Researcher","company":"Horizon AI","industry":"technology","location":"San Francisco, CA","remote":False,"job_type":JobType.full_time,"salary_min":160000,"salary_max":220000,"skills_required":["AI Alignment","Python","Interpretability","Red Teaming","Research"],"is_featured":True,"description":"Work on alignment, interpretability, and robustness research to ensure our AI systems behave safely and predictably.","requirements":"Strong ML background, genuine interest in safety, research experience preferred.","benefits":"Mission-driven, top comp, direct impact on AI safety."},
            {"title":"Developer Relations Engineer","company":"Horizon AI","industry":"technology","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":120000,"salary_max":160000,"skills_required":["Python","API Design","Technical Writing","Public Speaking","Developer Community"],"is_featured":False,"description":"Represent Horizon AI to the developer community through talks, tutorials, SDK contributions, and direct support.","requirements":"Strong coding skills, public communication ability, prior DevRel or OSS contribution.","benefits":"Conference travel, remote, high-visibility role."},

            # ── Peak Wellness Group ──────────────────────────────────────────
            {"title":"Physical Therapist","company":"Peak Wellness Group","industry":"healthcare","location":"Miami, FL","remote":False,"job_type":JobType.full_time,"salary_min":68000,"salary_max":90000,"skills_required":["Manual Therapy","Exercise Prescription","EMR","Patient Assessment","Rehabilitation"],"is_featured":False,"description":"Provide outpatient physical therapy to a diverse caseload across sports, ortho, and post-surgical rehabilitation.","requirements":"DPT license, Florida state licensure, 1+ year clinical experience.","benefits":"Sign-on bonus, student loan assistance, flexible scheduling."},
            {"title":"Occupational Therapist","company":"Peak Wellness Group","industry":"healthcare","location":"Miami, FL","remote":False,"job_type":JobType.full_time,"salary_min":65000,"salary_max":88000,"skills_required":["Occupational Therapy","ADL Training","Cognitive Rehabilitation","Home Assessment","Documentation"],"is_featured":False,"description":"Help patients regain independence in daily living activities across our outpatient and home health programs.","requirements":"OTR/L license, 1+ year experience, home health experience a plus.","benefits":"Mileage reimbursement, flexible schedule, full benefits."},
            {"title":"Wellness Coordinator","company":"Peak Wellness Group","industry":"healthcare","location":"Miami, FL","remote":True,"job_type":JobType.full_time,"salary_min":50000,"salary_max":68000,"skills_required":["Health Coaching","Program Design","Nutrition","Fitness","Community Engagement"],"is_featured":False,"description":"Design and manage corporate wellness programs for 50+ employer clients, driving measurable health outcomes.","requirements":"Health coaching certification, 2+ years wellness program management.","benefits":"Remote, meaningful work, health perks."},
            {"title":"Telehealth Physician – Internal Medicine","company":"Peak Wellness Group","industry":"healthcare","location":"Remote","remote":True,"job_type":JobType.part_time,"salary_min":150000,"salary_max":220000,"skills_required":["Internal Medicine","Telemedicine","EMR","Diagnosis","Patient Communication"],"is_featured":False,"description":"See patients via telehealth across our virtual primary care platform. Flexible schedule, part-time commitment.","requirements":"MD/DO, board-certified Internal Medicine, active multi-state licenses preferred.","benefits":"High hourly rate, fully remote, malpractice covered."},

            # ── Vault Capital ────────────────────────────────────────────────
            {"title":"Private Equity Associate","company":"Vault Capital","industry":"finance","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":150000,"salary_max":220000,"skills_required":["LBO Modeling","Due Diligence","Financial Analysis","Excel","Deal Execution"],"is_featured":True,"description":"Join our mid-market PE fund to evaluate and execute investments in technology and business services companies.","requirements":"2+ years IB or PE experience, elite academic credentials, exceptional modelling skills.","benefits":"Carry participation, deal bonuses, elite learning environment."},
            {"title":"Venture Capital Analyst","company":"Vault Capital","industry":"finance","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":90000,"salary_max":130000,"skills_required":["Startup Evaluation","Market Research","Financial Modelling","Excel","Pitch Decks"],"is_featured":False,"description":"Source and evaluate early-stage investment opportunities across SaaS, AI, and fintech verticals.","requirements":"Top-tier undergrad or MBA, passion for startups, strong analytical skills.","benefits":"Carry potential, network access, steep learning curve."},
            {"title":"Portfolio Finance Manager","company":"Vault Capital","industry":"finance","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":105000,"salary_max":140000,"skills_required":["Portfolio Analytics","Financial Reporting","Accounting","Excel","Investor Relations"],"is_featured":False,"description":"Support portfolio company financial reporting, fund accounting, and LP communications for our $800M fund.","requirements":"CPA or CFA, 4+ years fund accounting or portfolio finance.","benefits":"Bonus, full benefits, prestigious fund brand."},
            {"title":"Fund Operations Analyst","company":"Vault Capital","industry":"finance","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":72000,"salary_max":98000,"skills_required":["Fund Administration","NAV Calculation","Compliance","Excel","Investor Reporting"],"is_featured":False,"description":"Support day-to-day fund operations including NAV, investor reporting, compliance, and capital calls.","requirements":"2+ years fund ops experience, Series 65 a plus.","benefits":"Bonus, career growth into senior ops or IR."},

            # ── TerraNova Builders ───────────────────────────────────────────
            {"title":"Civil Project Engineer","company":"TerraNova Builders","industry":"engineering","location":"Phoenix, AZ","remote":False,"job_type":JobType.full_time,"salary_min":75000,"salary_max":105000,"skills_required":["Civil Engineering","AutoCAD Civil 3D","Site Development","Grading","Permitting"],"is_featured":False,"description":"Manage civil engineering design and permitting for residential and commercial development projects across Arizona.","requirements":"BSCE, 3+ years site development, EIT or PE preferred.","benefits":"Project bonuses, professional license sponsorship, growth company."},
            {"title":"Construction Superintendent","company":"TerraNova Builders","industry":"engineering","location":"Phoenix, AZ","remote":False,"job_type":JobType.full_time,"salary_min":85000,"salary_max":118000,"skills_required":["Construction Management","Scheduling","Subcontractor Management","Safety","Blueprints"],"is_featured":False,"description":"Oversee day-to-day construction operations on commercial projects from groundbreaking to punch list.","requirements":"8+ years construction superintendent, OSHA 30 required.","benefits":"Truck allowance, performance bonus, stable backlog."},
            {"title":"Estimator – Commercial Construction","company":"TerraNova Builders","industry":"engineering","location":"Phoenix, AZ","remote":False,"job_type":JobType.full_time,"salary_min":80000,"salary_max":110000,"skills_required":["Cost Estimation","Bluebeam","Procore","Bid Preparation","Quantity Takeoff"],"is_featured":False,"description":"Prepare accurate cost estimates and bid packages for commercial general contracting projects up to $50M.","requirements":"5+ years commercial estimating, Bluebeam proficiency required.","benefits":"Bonus on won projects, full benefits, growing pipeline."},
            {"title":"BIM Coordinator","company":"TerraNova Builders","industry":"engineering","location":"Phoenix, AZ","remote":False,"job_type":JobType.full_time,"salary_min":68000,"salary_max":92000,"skills_required":["Revit","BIM 360","Navisworks","Clash Detection","MEP Coordination"],"is_featured":False,"description":"Develop and manage BIM models, coordinate MEP clash detection, and support VDC workflows on large construction projects.","requirements":"3+ years BIM coordination, Revit proficiency required.","benefits":"Tech-forward company, training, full benefits."},
            {"title":"Safety Manager – Construction","company":"TerraNova Builders","industry":"engineering","location":"Phoenix, AZ","remote":False,"job_type":JobType.full_time,"salary_min":78000,"salary_max":105000,"skills_required":["OSHA","Safety Training","Incident Investigation","HAZMAT","Site Audits"],"is_featured":False,"description":"Lead jobsite safety programs, conduct inspections, investigate incidents, and maintain our zero-incident culture.","requirements":"CSP or ASP certification, 5+ years construction safety, OSHA 500.","benefits":"Company vehicle, bonus, leadership role."},

            # ── BrightMinds Academy ──────────────────────────────────────────
            {"title":"High School Math Teacher","company":"BrightMinds Academy","industry":"education","location":"Boston, MA","remote":False,"job_type":JobType.full_time,"salary_min":52000,"salary_max":72000,"skills_required":["Mathematics","Curriculum Design","Classroom Management","Differentiated Instruction","Assessment"],"is_featured":False,"description":"Teach AP Calculus and Pre-Calculus to 9th–12th grade students in our college-preparatory private school.","requirements":"Teaching certification, math subject expertise, 2+ years classroom experience.","benefits":"Summers off, tuition discount for dependents, retirement plan."},
            {"title":"Academic Dean","company":"BrightMinds Academy","industry":"education","location":"Boston, MA","remote":False,"job_type":JobType.full_time,"salary_min":90000,"salary_max":120000,"skills_required":["Academic Leadership","Curriculum Oversight","Faculty Development","Student Affairs","Strategic Planning"],"is_featured":False,"description":"Lead academic programming, faculty development, and curriculum alignment across all departments of our K-12 school.","requirements":"Master's or EdD in Education Leadership, 5+ years academic administration.","benefits":"Leadership role, housing stipend option, full benefits."},
            {"title":"College Counselor","company":"BrightMinds Academy","industry":"education","location":"Boston, MA","remote":False,"job_type":JobType.full_time,"salary_min":58000,"salary_max":78000,"skills_required":["College Advising","Essay Coaching","Application Review","Student Counseling","Naviance"],"is_featured":False,"description":"Guide 11th and 12th grade students through the college application process, from college list building to final decisions.","requirements":"3+ years college counseling, former admission officer experience a plus.","benefits":"Summers flexible, professional development, rewarding work."},
            {"title":"STEM Curriculum Developer","company":"BrightMinds Academy","industry":"education","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":65000,"salary_max":88000,"skills_required":["STEM Education","Curriculum Design","Python","Project-Based Learning","Standards Alignment"],"is_featured":False,"description":"Design rigorous, engaging STEM curriculum for grades 6–12 that integrates coding, engineering, and scientific inquiry.","requirements":"STEM teaching background, 3+ years curriculum development.","benefits":"Remote, creative work, meaningful mission."},

            # ── Nexus Law Group ──────────────────────────────────────────────
            {"title":"Immigration Attorney","company":"Nexus Law Group","industry":"legal","location":"Washington, DC","remote":False,"job_type":JobType.full_time,"salary_min":95000,"salary_max":135000,"skills_required":["Immigration Law","H-1B","Green Card","PERM","Client Counseling"],"is_featured":False,"description":"Represent corporate clients on employment-based immigration matters including H-1B, PERM, and EB-1/EB-2 petitions.","requirements":"JD, DC or VA bar, 3+ years immigration law, corporate immigration focus.","benefits":"Billable bonus, hybrid schedule, supportive firm culture."},
            {"title":"Intellectual Property Paralegal","company":"Nexus Law Group","industry":"legal","location":"Washington, DC","remote":True,"job_type":JobType.full_time,"salary_min":55000,"salary_max":75000,"skills_required":["Patent Filing","Trademark","Docketing","USPTO","IP Research"],"is_featured":False,"description":"Support IP attorneys in patent prosecution, trademark filings, and docketing for a growing IP practice group.","requirements":"2+ years IP paralegal experience, USPTO portal proficiency.","benefits":"Remote option, professional development, growth firm."},
            {"title":"Legal Billing Specialist","company":"Nexus Law Group","industry":"legal","location":"Washington, DC","remote":True,"job_type":JobType.full_time,"salary_min":48000,"salary_max":65000,"skills_required":["Legal Billing","Aderant","Time Entry","Accounts Receivable","Billing Guidelines"],"is_featured":False,"description":"Process attorney time entries, prepare client invoices, and manage billing compliance across our litigation and transactional practices.","requirements":"2+ years legal billing, Aderant or Elite experience preferred.","benefits":"Remote, stable firm, full benefits."},
            {"title":"Data Privacy Counsel","company":"Nexus Law Group","industry":"legal","location":"Washington, DC","remote":True,"job_type":JobType.full_time,"salary_min":130000,"salary_max":180000,"skills_required":["GDPR","CCPA","Data Privacy","Privacy Impact Assessments","Contract Negotiation"],"is_featured":False,"description":"Advise tech and healthcare clients on data privacy compliance, incident response, and regulatory risk.","requirements":"JD, 4+ years data privacy law, CIPP/US or CIPP/E certification preferred.","benefits":"Hybrid, strong compensation, growing practice area."},

            # ── Urban Store Co. ──────────────────────────────────────────────
            {"title":"Category Manager","company":"Urban Store Co.","industry":"retail","location":"Los Angeles, CA","remote":False,"job_type":JobType.full_time,"salary_min":80000,"salary_max":108000,"skills_required":["Category Management","Vendor Negotiation","Merchandising","P&L Management","Planogram"],"is_featured":False,"description":"Own the strategy, assortment, and financial performance of a high-volume product category across 300+ stores.","requirements":"5+ years category management, strong P&L ownership, CPG or retail background.","benefits":"Performance bonus, company discount, career growth."},
            {"title":"Loss Prevention Manager","company":"Urban Store Co.","industry":"retail","location":"Los Angeles, CA","remote":False,"job_type":JobType.full_time,"salary_min":58000,"salary_max":78000,"skills_required":["Loss Prevention","CCTV","Investigations","Shrinkage Reduction","Compliance"],"is_featured":False,"description":"Develop and execute loss prevention strategies across our Southern California store network to minimise shrinkage.","requirements":"3+ years loss prevention management, CFI certification preferred.","benefits":"Company vehicle, bonus on shrinkage targets, full benefits."},
            {"title":"Retail Data Analyst","company":"Urban Store Co.","industry":"retail","location":"Los Angeles, CA","remote":True,"job_type":JobType.full_time,"salary_min":65000,"salary_max":88000,"skills_required":["SQL","Tableau","Retail Analytics","Python","Excel"],"is_featured":False,"description":"Analyse sales, inventory, and customer data to guide merchandising and store operations decisions.","requirements":"2+ years data analytics, retail domain preferred, strong SQL.","benefits":"Remote-friendly, growth company, competitive pay."},
            {"title":"Omnichannel Operations Manager","company":"Urban Store Co.","industry":"retail","location":"Los Angeles, CA","remote":False,"job_type":JobType.full_time,"salary_min":85000,"salary_max":115000,"skills_required":["Omnichannel Retail","BOPIS","Inventory Management","Process Improvement","Cross-functional Leadership"],"is_featured":False,"description":"Lead the integration of online and in-store operations, driving seamless click-and-collect and ship-from-store capabilities.","requirements":"5+ years retail operations, omnichannel programme experience required.","benefits":"High-impact role, bonus, career advancement."},
            {"title":"HR Generalist – Retail","company":"Urban Store Co.","industry":"retail","location":"Los Angeles, CA","remote":False,"job_type":JobType.full_time,"salary_min":55000,"salary_max":75000,"skills_required":["HR Generalist","Employee Relations","Onboarding","HRIS","Compliance"],"is_featured":False,"description":"Support HR operations for 2,000+ store associates across our California region, from onboarding to ER.","requirements":"3+ years HR generalist in retail or high-volume environment.","benefits":"Company discount, full benefits, diverse team."},

            # ── Alpha Logistics ──────────────────────────────────────────────
            {"title":"Global Trade Compliance Manager","company":"Alpha Logistics","industry":"logistics","location":"Chicago, IL","remote":False,"job_type":JobType.full_time,"salary_min":95000,"salary_max":130000,"skills_required":["Import/Export Compliance","Customs Brokerage","HTS Classification","ITAR","C-TPAT"],"is_featured":False,"description":"Manage global trade compliance across our 50-country logistics network, ensuring regulatory adherence and cost optimisation.","requirements":"7+ years trade compliance, CCS or LCB licence preferred.","benefits":"High-impact role, international exposure, competitive comp."},
            {"title":"Last Mile Delivery Manager","company":"Alpha Logistics","industry":"logistics","location":"Chicago, IL","remote":False,"job_type":JobType.full_time,"salary_min":72000,"salary_max":98000,"skills_required":["Last Mile Delivery","Route Optimisation","Driver Management","KPIs","Fleet Tracking"],"is_featured":False,"description":"Lead last-mile operations for our Chicago metro delivery network, managing 80+ drivers and 4 depots.","requirements":"5+ years delivery or distribution management, fleet experience required.","benefits":"Vehicle provided, performance bonus, advancement path."},
            {"title":"Logistics IT Systems Analyst","company":"Alpha Logistics","industry":"logistics","location":"Chicago, IL","remote":True,"job_type":JobType.full_time,"salary_min":75000,"salary_max":100000,"skills_required":["WMS","TMS","SQL","EDI","Business Analysis"],"is_featured":False,"description":"Support and improve our warehouse and transportation management systems across 25 distribution centres.","requirements":"3+ years logistics IT, WMS implementation experience, SQL proficient.","benefits":"Remote-friendly, system modernisation work, full benefits."},
            {"title":"Import Coordinator","company":"Alpha Logistics","industry":"logistics","location":"Chicago, IL","remote":False,"job_type":JobType.full_time,"salary_min":48000,"salary_max":65000,"skills_required":["Import Documentation","Customs Clearance","Ocean Freight","Vendor Communication","MS Office"],"is_featured":False,"description":"Coordinate import shipments from Asia and Europe, managing documentation, customs clearance, and delivery scheduling.","requirements":"2+ years import coordination, ocean freight experience required.","benefits":"Career growth, supportive team, full benefits."},
            {"title":"Cold Chain Logistics Specialist","company":"Alpha Logistics","industry":"logistics","location":"Chicago, IL","remote":False,"job_type":JobType.full_time,"salary_min":60000,"salary_max":82000,"skills_required":["Cold Chain","Temperature Control","Pharmaceutical Logistics","GDP","Risk Assessment"],"is_featured":False,"description":"Manage temperature-controlled logistics for pharmaceutical and food clients, ensuring chain-of-custody and GDP compliance.","requirements":"3+ years cold chain logistics, pharma sector preferred, GDP knowledge.","benefits":"Specialised field, full benefits, growth opportunities."},

            # ── PrimeCast Media ──────────────────────────────────────────────
            {"title":"Performance Marketing Manager","company":"PrimeCast Media","industry":"marketing","location":"New York, NY","remote":True,"job_type":JobType.full_time,"salary_min":85000,"salary_max":118000,"skills_required":["Google Ads","Meta Ads","Attribution","ROAS Optimisation","Analytics"],"is_featured":False,"description":"Own performance marketing channels for our portfolio of media brands, managing $5M+ in annual ad spend.","requirements":"4+ years performance marketing, DTC or media background, strong attribution expertise.","benefits":"Remote, performance bonus, high-impact portfolio."},
            {"title":"Brand Strategist","company":"PrimeCast Media","industry":"marketing","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":80000,"salary_max":110000,"skills_required":["Brand Strategy","Consumer Research","Positioning","Creative Briefs","Campaign Planning"],"is_featured":False,"description":"Define and evolve brand positioning for our flagship media properties reaching 20M monthly readers.","requirements":"5+ years brand strategy at agency or media company, strong research skills.","benefits":"Creative environment, media perks, career growth."},
            {"title":"Podcast Producer","company":"PrimeCast Media","industry":"marketing","location":"New York, NY","remote":True,"job_type":JobType.full_time,"salary_min":62000,"salary_max":85000,"skills_required":["Audio Production","Adobe Audition","Storytelling","Guest Booking","Show Notes"],"is_featured":False,"description":"Produce two weekly podcasts from concept to publish — booking guests, recording, editing, and writing show notes.","requirements":"3+ years podcast production, strong audio editing, editorial sensibility.","benefits":"Remote option, creative work, growing media company."},
            {"title":"Video Content Creator","company":"PrimeCast Media","industry":"marketing","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":55000,"salary_max":78000,"skills_required":["Video Production","Adobe Premiere","YouTube","Scripting","Lighting"],"is_featured":False,"description":"Produce high-quality video content for our YouTube channels and social platforms, end-to-end from script to publish.","requirements":"2+ years video production, strong editing skills, on-camera comfort a plus.","benefits":"Studio equipment provided, creative freedom, growing brand."},
            {"title":"Audience Development Manager","company":"PrimeCast Media","industry":"marketing","location":"New York, NY","remote":True,"job_type":JobType.full_time,"salary_min":72000,"salary_max":98000,"skills_required":["SEO","Newsletter Growth","Subscriber Acquisition","A/B Testing","Analytics"],"is_featured":False,"description":"Grow our subscriber and audience base across newsletters, search, and social using data-driven acquisition strategies.","requirements":"4+ years audience or newsletter growth, strong SEO and analytics background.","benefits":"Remote, performance bonus, high-growth media brand."},

            # ── SteelCraft Industries ────────────────────────────────────────
            {"title":"Welding Engineer","company":"SteelCraft Industries","industry":"manufacturing","location":"Pittsburgh, PA","remote":False,"job_type":JobType.full_time,"salary_min":78000,"salary_max":105000,"skills_required":["Welding Engineering","AWS Certification","WPS/PQR","Metallurgy","Quality Control"],"is_featured":False,"description":"Develop and qualify welding procedures, troubleshoot weld defects, and support production quality for our heavy fabrication facility.","requirements":"BS in Welding Engineering or Materials Science, CWI preferred, 3+ years industrial welding engineering.","benefits":"Technical depth, full benefits, stable company."},
            {"title":"Plant Manager","company":"SteelCraft Industries","industry":"manufacturing","location":"Pittsburgh, PA","remote":False,"job_type":JobType.full_time,"salary_min":110000,"salary_max":150000,"skills_required":["Plant Management","P&L","Lean Manufacturing","Safety","Team Leadership"],"is_featured":False,"description":"Lead operations of our 250,000 sq ft steel fabrication plant, overseeing 300 employees across three shifts.","requirements":"10+ years manufacturing leadership, P&L ownership, steel or heavy industry preferred.","benefits":"Profit sharing, executive perks, strong tenure."},
            {"title":"Supply Chain Coordinator","company":"SteelCraft Industries","industry":"manufacturing","location":"Pittsburgh, PA","remote":False,"job_type":JobType.full_time,"salary_min":52000,"salary_max":72000,"skills_required":["Purchasing","ERP","Vendor Management","Inventory","MRP"],"is_featured":False,"description":"Coordinate raw material procurement, vendor relationships, and inventory control for our high-volume steel fabrication operation.","requirements":"2+ years supply chain in manufacturing, ERP experience required.","benefits":"Stable industry, full benefits, growth potential."},
            {"title":"Maintenance Manager","company":"SteelCraft Industries","industry":"manufacturing","location":"Pittsburgh, PA","remote":False,"job_type":JobType.full_time,"salary_min":85000,"salary_max":115000,"skills_required":["Preventive Maintenance","PLC","Hydraulics","Team Leadership","CMMS"],"is_featured":False,"description":"Lead a 20-person maintenance team ensuring maximum equipment uptime across our heavy manufacturing facility.","requirements":"7+ years industrial maintenance, 3+ years supervisory, strong electrical and hydraulics knowledge.","benefits":"Overtime potential, full benefits, leadership path."},
            {"title":"EHS Manager","company":"SteelCraft Industries","industry":"manufacturing","location":"Pittsburgh, PA","remote":False,"job_type":JobType.full_time,"salary_min":80000,"salary_max":108000,"skills_required":["Environmental Health Safety","OSHA","ISO 14001","Incident Investigation","Training"],"is_featured":False,"description":"Lead environmental, health, and safety programmes for our steel fabrication facility, targeting zero-incident performance.","requirements":"5+ years EHS in heavy manufacturing, CSP preferred, ISO 14001 experience.","benefits":"High impact, full benefits, leadership visibility."},

            # ── Cross-company additional roles ───────────────────────────────
            {"title":"Principal Data Engineer","company":"DataFlow Inc.","industry":"technology","location":"San Francisco, CA","remote":True,"job_type":JobType.full_time,"salary_min":155000,"salary_max":200000,"skills_required":["Apache Spark","Kafka","dbt","Snowflake","Python"],"is_featured":False,"description":"Architect and lead the build-out of DataFlow's next-generation real-time streaming data platform.","requirements":"8+ years data engineering, Kafka and Spark expertise, proven tech leadership.","benefits":"Remote, equity, principal-level scope."},
            {"title":"Revenue Operations Manager","company":"FinTech Partners","industry":"finance","location":"Austin, TX","remote":True,"job_type":JobType.full_time,"salary_min":95000,"salary_max":130000,"skills_required":["Salesforce","RevOps","HubSpot","Pipeline Management","Analytics"],"is_featured":False,"description":"Align sales, marketing, and customer success operations to drive predictable revenue growth for our fintech platform.","requirements":"4+ years RevOps, Salesforce admin skills, SaaS background preferred.","benefits":"Remote, variable comp, high-growth environment."},
            {"title":"Infrastructure Security Architect","company":"Acme Technologies","industry":"technology","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":175000,"salary_max":230000,"skills_required":["Zero Trust","AWS Security","IAM","SASE","Security Architecture"],"is_featured":False,"description":"Design and lead the security architecture for our global multi-cloud infrastructure serving 50M+ users.","requirements":"10+ years security, CISSP required, deep cloud security expertise.","benefits":"Top compensation, equity, high-stakes impact."},
            {"title":"Clinical Data Manager","company":"NovaBio Labs","industry":"healthcare","location":"Boston, MA","remote":True,"job_type":JobType.full_time,"salary_min":85000,"salary_max":115000,"skills_required":["Clinical Data Management","EDC","CDISC","SAS","Medidata Rave"],"is_featured":False,"description":"Oversee data collection, cleaning, and integrity for Phase II/III oncology trials across multiple investigative sites.","requirements":"5+ years CDM, CCDM certification preferred, Medidata Rave expertise.","benefits":"Remote, mission-driven, strong comp."},
            {"title":"Renewable Energy Project Developer","company":"GreenBridge Energy","industry":"engineering","location":"Denver, CO","remote":False,"job_type":JobType.full_time,"salary_min":90000,"salary_max":125000,"skills_required":["Project Development","Land Acquisition","Permitting","PPA Negotiation","GIS"],"is_featured":False,"description":"Develop utility-scale solar and wind projects from site origination through notice-to-proceed, managing land, permitting, and offtake.","requirements":"4+ years renewable project development, PPA and interconnection experience.","benefits":"Carry potential, mission-driven, strong growth."},
            {"title":"Retail Operations Analyst","company":"RetailNext","industry":"retail","location":"Atlanta, GA","remote":True,"job_type":JobType.full_time,"salary_min":58000,"salary_max":80000,"skills_required":["Operations Analytics","Excel","SQL","Process Documentation","KPIs"],"is_featured":False,"description":"Analyse store operations data to identify efficiency opportunities and support national rollout of new operational standards.","requirements":"2+ years operations analysis, retail preferred, strong Excel and SQL.","benefits":"Remote-friendly, high-impact work, growth company."},
            {"title":"3PL Account Manager","company":"SwiftLogix","industry":"logistics","location":"Dallas, TX","remote":False,"job_type":JobType.full_time,"salary_min":65000,"salary_max":90000,"skills_required":["Account Management","3PL","Client Relations","Problem Solving","Logistics"],"is_featured":False,"description":"Manage key client relationships for our 3PL operation, ensuring SLA compliance and driving account growth.","requirements":"3+ years 3PL or freight account management, strong client communication skills.","benefits":"Bonus on retention, full benefits, growth path."},
            {"title":"Online Learning Experience Designer","company":"EduPath Learning","industry":"education","location":"Remote","remote":True,"job_type":JobType.full_time,"salary_min":68000,"salary_max":92000,"skills_required":["Learning Experience Design","Articulate Storyline","UX Design","Accessibility","Assessment Design"],"is_featured":False,"description":"Design visually compelling, pedagogically sound online learning experiences for our 500K+ learner platform.","requirements":"3+ years LXD or instructional design, Articulate Storyline proficiency required.","benefits":"100% remote, creative work, meaningful mission."},
            {"title":"Legal Technology Manager","company":"LexaCorp Legal","industry":"legal","location":"Chicago, IL","remote":True,"job_type":JobType.full_time,"salary_min":100000,"salary_max":138000,"skills_required":["Legal Tech","Clio","Document Automation","AI Tools","Change Management"],"is_featured":False,"description":"Lead adoption of AI and legal technology tools across our 120-attorney firm, driving efficiency and competitive advantage.","requirements":"5+ years legal technology management, attorney background a plus.","benefits":"Remote-friendly, cutting-edge tools, high-impact role."},
            {"title":"Media Partnerships Manager","company":"PrimeCast Media","industry":"marketing","location":"New York, NY","remote":False,"job_type":JobType.full_time,"salary_min":78000,"salary_max":105000,"skills_required":["Partnership Development","Sponsorship Sales","Negotiation","Media Planning","CRM"],"is_featured":False,"description":"Build and grow revenue-generating partnerships with brands, agencies, and platforms across our media portfolio.","requirements":"4+ years media partnerships or sponsorship sales, strong negotiation skills.","benefits":"Commission structure, media perks, growing company."},
        ]

        from slugify import slugify
        import uuid
        for jd in jobs_data:
            slug = f"{slugify(jd['title'])}-{uuid.uuid4().hex[:6]}"
            co_id = company_map.get(jd["company"])
            existing = await db.scalar(
                select(Job).where(Job.title == jd["title"], Job.company_id == co_id)
            ) if co_id else None
            if not existing:
                job = Job(
                    company_id=co_id or 1,
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
        # Clean up old generic slugs if they exist
        for old_slug in ("career-advice",):
            old = await db.scalar(select(BlogPost).where(BlogPost.slug == old_slug))
            if old:
                await db.delete(old)
                await db.flush()

        blog_posts = [
            {
                "title": "10 Resume Mistakes That Are Costing You Interviews",
                "slug": "resume-mistakes-interviews",
                "category": "Career Advice",
                "cover_emoji": "💼",
                "reading_time_minutes": 7,
                "tags": ["resume", "job search", "career tips"],
                "excerpt": "Discover the most common resume pitfalls and how to fix them to land more callbacks from top employers.",
                "days_ago": 9,
                "content": """<p class="lead">Your resume is your first impression — and most job seekers are making at least three of these ten critical mistakes without realizing it.</p>

<h2>1. Using a Generic Objective Statement</h2>
<p>Hiring managers read hundreds of resumes. An objective like "seeking a challenging role to grow my skills" tells them nothing. Replace it with a sharp, two-sentence <strong>professional summary</strong> that highlights your specific value: years of experience, top skills, and your biggest career win.</p>

<h2>2. Burying Your Accomplishments in Job Duties</h2>
<p>Don't list what your job was — show what you <em>achieved</em>. Compare these two bullets:</p>
<ul>
  <li>❌ "Responsible for managing social media accounts"</li>
  <li>✅ "Grew Instagram following 340% in 6 months, driving 22% increase in website traffic"</li>
</ul>
<p>Quantify everything you can. Numbers stand out and prove impact.</p>

<h2>3. Ignoring ATS Keywords</h2>
<p>Most large companies use Applicant Tracking Systems to filter resumes before a human sees them. If your resume doesn't include the exact keywords from the job description, it gets filtered out automatically. Mirror the language in the posting — don't paraphrase.</p>

<h2>4. Using a Functional Resume Format When You Shouldn't</h2>
<p>Functional resumes (skills-based, hiding employment gaps) raise red flags for most recruiters. Unless you're making a dramatic career switch, stick to a <strong>reverse-chronological format</strong>. It's what hiring managers expect and trust.</p>

<h2>5. One-Size-Fits-All Applications</h2>
<p>Sending the same resume to 50 companies is a losing strategy. Tailor your resume for each role — at minimum, adjust your summary and skills section to align with the specific job. It takes 10 extra minutes and dramatically increases your callback rate.</p>

<h2>6. Poor Formatting and Inconsistent Design</h2>
<p>Inconsistent fonts, cramped margins, and walls of text make your resume hard to scan. Recruiters spend an average of 7 seconds on initial screening. Use clean headers, consistent bullet points, and enough white space to guide the eye.</p>

<h2>7. Listing Outdated or Irrelevant Skills</h2>
<p>Listing "Microsoft Office" as a skill in 2025 wastes space and signals you're behind the times. Remove anything that's expected and obvious. Highlight tools and technologies that are genuinely relevant and current for your target role.</p>

<h2>8. Typos and Grammatical Errors</h2>
<p>A single typo can eliminate you from consideration. Always proofread at least three times, then have someone else review it. Use tools like Grammarly — but don't rely on them exclusively. Read your resume out loud to catch awkward phrasing.</p>

<h2>9. Wrong File Format</h2>
<p>Unless specifically requested otherwise, always send your resume as a <strong>PDF</strong>. Word documents can render differently on different computers, potentially destroying your carefully crafted formatting.</p>

<h2>10. Missing Contact Information or Broken Links</h2>
<p>Double-check that your email, phone number, LinkedIn URL, and any portfolio links actually work. Recruiters won't hunt for your contact information — they'll simply move to the next candidate.</p>

<h2>The Takeaway</h2>
<p>A strong resume isn't about looking impressive — it's about making it effortless for a hiring manager to see why you're the right fit. Fix these ten mistakes and you'll see a measurable difference in your interview callback rate within weeks.</p>""",
            },
            {
                "title": "The 15 Fastest-Growing Jobs in Tech for 2025",
                "slug": "tech-jobs-2025",
                "category": "Industry Trends",
                "cover_emoji": "📈",
                "reading_time_minutes": 9,
                "tags": ["tech jobs", "AI", "career growth", "2025"],
                "excerpt": "AI, cybersecurity, and cloud computing are reshaping the workforce. Here's where the opportunities lie.",
                "days_ago": 23,
                "content": """<p class="lead">The technology sector added over 2 million jobs last year alone. But not all tech roles are growing equally. These 15 positions are seeing explosive demand — and lucrative salaries to match.</p>

<h2>1. AI/ML Engineer</h2>
<p>Median salary: <strong>$165,000</strong> · Growth: 40% YoY<br>The backbone of every AI product. Companies are racing to hire engineers who can design, train, and deploy machine learning models at scale.</p>

<h2>2. Prompt Engineer</h2>
<p>Median salary: <strong>$130,000</strong> · Growth: New category<br>The art of communicating effectively with large language models has become a legitimate and highly valued engineering discipline.</p>

<h2>3. Cybersecurity Analyst</h2>
<p>Median salary: <strong>$120,000</strong> · Growth: 35% YoY<br>With ransomware attacks costing businesses $8B+ annually, demand for security professionals has never been higher.</p>

<h2>4. Cloud Architect</h2>
<p>Median salary: <strong>$155,000</strong> · Growth: 28% YoY<br>AWS, Azure, and GCP architects are among the most sought-after professionals as enterprise migration to the cloud accelerates.</p>

<h2>5. Data Engineer</h2>
<p>Median salary: <strong>$140,000</strong> · Growth: 32% YoY<br>Every AI initiative needs clean, structured data pipelines. Data engineers build and maintain the infrastructure that makes AI possible.</p>

<h2>6. DevOps / Platform Engineer</h2>
<p>Median salary: <strong>$135,000</strong> · Growth: 25% YoY<br>The shift from DevOps to "Platform Engineering" reflects the increasing complexity of modern software delivery pipelines.</p>

<h2>7. Full-Stack Developer</h2>
<p>Median salary: <strong>$125,000</strong> · Growth: 22% YoY<br>React, Next.js, and TypeScript continue to dominate. Developers comfortable across the entire stack remain in constant demand.</p>

<h2>8. AI Product Manager</h2>
<p>Median salary: <strong>$160,000</strong> · Growth: 45% YoY<br>PMs who can bridge the gap between ML capabilities and user needs are among the rarest — and best compensated — professionals in tech.</p>

<h2>9. Blockchain Developer</h2>
<p>Median salary: <strong>$130,000</strong> · Growth: 18% YoY<br>Beyond crypto, blockchain is finding real applications in supply chain, healthcare records, and financial settlements.</p>

<h2>10. UX Researcher</h2>
<p>Median salary: <strong>$115,000</strong> · Growth: 20% YoY<br>As products become more complex, companies are investing heavily in understanding how real users interact with their tools.</p>

<h2>11–15: Honorable Mentions</h2>
<ul>
  <li><strong>Robotics Engineer</strong> — $145K · Manufacturing automation boom</li>
  <li><strong>Quantum Computing Researcher</strong> — $175K · Early-stage but explosive</li>
  <li><strong>AR/VR Developer</strong> — $120K · Spatial computing going mainstream</li>
  <li><strong>Site Reliability Engineer (SRE)</strong> — $150K · Uptime is revenue</li>
  <li><strong>Technical Writer (AI Focus)</strong> — $95K · Documentation for AI tools surging</li>
</ul>

<h2>How to Position Yourself</h2>
<p>The common thread across all 15 roles? <strong>AI fluency</strong>. Even non-AI roles increasingly require familiarity with AI tools and workflows. Investing in learning Python, understanding ML fundamentals, and building projects with open-source AI frameworks will open doors across every category on this list.</p>""",
            },
            {
                "title": "How to Build a Winning Employer Brand in 2025",
                "slug": "employer-branding-2025",
                "category": "Hiring Guide",
                "cover_emoji": "🤝",
                "reading_time_minutes": 8,
                "tags": ["employer brand", "hiring", "talent acquisition", "culture"],
                "excerpt": "Top candidates have options. Learn how leading companies attract elite talent in a competitive market.",
                "days_ago": 37,
                "content": """<p class="lead">In a world where top engineers receive 10+ recruiter messages per week, your employer brand is the single biggest lever you can pull to attract and retain elite talent.</p>

<h2>What Is Employer Branding?</h2>
<p>Your employer brand is the perception candidates have of your company as a place to work. It includes your culture, values, reputation, compensation philosophy, and how you treat people throughout the hiring process.</p>

<h2>Why It Matters More Than Ever</h2>
<p>A LinkedIn study found that companies with strong employer brands see <strong>50% more qualified applicants</strong> and <strong>28% lower turnover</strong>. In the talent war, brand is a force multiplier — it makes every other recruiting effort more effective.</p>

<h2>Step 1: Audit Your Current Brand</h2>
<p>Start by listening. Review your Glassdoor ratings, read exit interview data, and survey current employees honestly. You can't improve what you haven't measured. Look for patterns: what do people love? What consistently frustrates them?</p>

<h2>Step 2: Define Your Employee Value Proposition (EVP)</h2>
<p>Your EVP is the answer to "Why would an exceptional person choose to work here?" It should be specific, authentic, and differentiated. Vague promises like "great culture and growth opportunities" mean nothing. Instead:</p>
<ul>
  <li>"We ship to production on day 3. Bureaucracy is our enemy."</li>
  <li>"Every engineer has a $5,000 annual learning budget with no approval required."</li>
  <li>"We've promoted 40% of our senior engineers internally in the last two years."</li>
</ul>

<h2>Step 3: Activate Your Employees as Brand Ambassadors</h2>
<p>Nothing is more credible than hearing from your actual team. Encourage employees to share their authentic experiences on LinkedIn. Create a simple content program: monthly team spotlights, behind-the-scenes engineering blog posts, and honest "a day in the life" videos.</p>

<h2>Step 4: Obsess Over the Candidate Experience</h2>
<p>Every touchpoint — from your careers page to your rejection emails — is a brand moment. Companies that ghost candidates or run 8-round interview processes destroy their reputation with the very people they're trying to attract.</p>
<p>Set a target: respond to every applicant within 5 business days. Give feedback after interviews. Make the process feel respectful of the candidate's time.</p>

<h2>Step 5: Be Honest About Your Culture</h2>
<p>The biggest mistake companies make is portraying a culture that doesn't exist. Candidates who join based on false promises churn within 6 months, costing you $15,000–$50,000 per failed hire. Authenticity builds long-term trust and attracts people who will genuinely thrive in your environment.</p>

<h2>Measuring Your Progress</h2>
<p>Track these metrics quarterly: offer acceptance rate, time-to-fill, Glassdoor score, employee Net Promoter Score (eNPS), and referral hire rate. A strong employer brand will show improvement across all five within 12 months of a focused effort.</p>""",
            },
            {
                "title": "The Ultimate Guide to Acing Your Technical Interview",
                "slug": "technical-interview-guide",
                "category": "Career Advice",
                "cover_emoji": "🎯",
                "reading_time_minutes": 10,
                "tags": ["interview", "tech interview", "coding", "preparation"],
                "excerpt": "From LeetCode prep to system design and behavioral questions — a complete roadmap to landing your next engineering role.",
                "days_ago": 14,
                "content": """<p class="lead">Technical interviews are a skill. Like any skill, they can be practiced, learned, and mastered. Here's a complete system for turning interview anxiety into confident execution.</p>

<h2>Phase 1: The 6-Week Preparation Framework</h2>
<p>Don't cram the night before. Serious preparation requires 6 weeks of consistent, structured practice:</p>
<ul>
  <li><strong>Weeks 1–2:</strong> Data structures foundations (arrays, hash maps, trees, graphs)</li>
  <li><strong>Weeks 3–4:</strong> Algorithm patterns (sliding window, two pointers, BFS/DFS, dynamic programming)</li>
  <li><strong>Week 5:</strong> System design fundamentals</li>
  <li><strong>Week 6:</strong> Mock interviews and company-specific prep</li>
</ul>

<h2>The Algorithm Interview</h2>
<p>Solve 75–100 LeetCode problems across all difficulty levels. More important than volume is <strong>pattern recognition</strong>. When you see a problem, identify the pattern first: Is this a sliding window? A two-pointer problem? BFS on a graph?</p>
<p>Before writing any code, always:</p>
<ol>
  <li>Clarify the problem — ask about edge cases, input constraints, expected output format</li>
  <li>Think out loud — describe your approach before coding</li>
  <li>Start with a brute force, then optimize</li>
  <li>Test your code with examples before declaring it complete</li>
</ol>

<h2>System Design: How to Structure Your Answer</h2>
<p>When asked "design Twitter" or "design a URL shortener," use this framework:</p>
<ol>
  <li><strong>Requirements gathering</strong> (5 min): functional vs. non-functional, scale estimates</li>
  <li><strong>High-level design</strong> (10 min): components, API design, data model</li>
  <li><strong>Deep dive</strong> (15 min): the interviewer will direct focus here</li>
  <li><strong>Trade-offs and bottlenecks</strong> (5 min): what would you improve with more time?</li>
</ol>

<h2>Behavioral Interviews: The STAR Method</h2>
<p>Every behavioral answer should follow STAR: <strong>S</strong>ituation, <strong>T</strong>ask, <strong>A</strong>ction, <strong>R</strong>esult. Prepare 8–10 stories from your career that can flex across different questions. Your best stories should demonstrate: leadership under pressure, resolving conflict, shipping under constraints, and learning from failure.</p>

<h2>The Questions You Must Ask</h2>
<p>Always ask at least two questions at the end. Great options:</p>
<ul>
  <li>"What does success look like in this role after 90 days?"</li>
  <li>"What's the biggest technical challenge the team is facing right now?"</li>
  <li>"How does the team handle disagreements on technical direction?"</li>
</ul>

<h2>Day-Of Execution</h2>
<p>Sleep 8 hours. Eat a real meal. Arrive 10 minutes early (virtual or in-person). Open with genuine curiosity about the team and the problem. Close by reiterating your enthusiasm and asking about next steps. Follow up with a thank-you email within 24 hours that references a specific part of the conversation.</p>""",
            },
            {
                "title": "Remote Work in 2025: Staying Productive and Connected",
                "slug": "remote-work-productivity-2025",
                "category": "Workplace",
                "cover_emoji": "🏠",
                "reading_time_minutes": 6,
                "tags": ["remote work", "productivity", "work from home", "async"],
                "excerpt": "Hybrid and remote setups are here to stay. Here's how top performers maintain focus, build relationships, and advance their careers from anywhere.",
                "days_ago": 5,
                "content": """<p class="lead">Five years after the great remote work experiment began, the data is in: remote workers can be just as productive — or more — than their in-office counterparts. But it requires intentional systems.</p>

<h2>Design Your Environment Deliberately</h2>
<p>Your home office setup directly impacts your output quality. The minimum viable setup: a dedicated workspace (even a corner of a room), an external monitor, a good microphone, and a comfortable chair. A poor audio setup alone will undermine your perceived professionalism in every meeting.</p>

<h2>Master Asynchronous Communication</h2>
<p>The best remote teams operate primarily async. This means writing clearly, documenting decisions, and not expecting instant responses. Tools like Notion, Linear, and Loom have replaced the hallway conversation. Learn to communicate your work and ideas in writing — it's a career-defining skill in distributed teams.</p>

<h2>Protect Deep Work Time</h2>
<p>The biggest advantage of remote work — and the hardest to maintain — is uninterrupted deep work time. Block 3–4 hours each morning for your most cognitively demanding tasks. Turn off Slack notifications. Close email. Guard this time as if it were a meeting with your CEO.</p>

<h2>Build Relationships Proactively</h2>
<p>Relationships don't form accidentally in remote environments. You have to be intentional. Schedule virtual coffee chats with colleagues. Participate actively in Slack channels. When you visit the office, make those interactions count. The people who advance in remote-first companies are visible, communicative, and genuinely connected to their teammates.</p>

<h2>Manage Your Energy, Not Just Your Time</h2>
<p>Working from home blurs the boundary between work and personal life. Establish firm start and end times. Take real lunch breaks away from your desk. Build in physical movement — even a 20-minute walk changes your afternoon energy level dramatically.</p>

<h2>Advance Your Career Remotely</h2>
<p>The biggest remote career mistake is becoming invisible. Speak up in meetings. Share your work and wins in team channels. Volunteer for high-visibility projects. Write internal documentation that others reference. Visibility and impact — not face time — are how remote workers get promoted.</p>""",
            },
            {
                "title": "How to Negotiate Your Salary Like a Pro",
                "slug": "salary-negotiation-guide",
                "category": "Career Advice",
                "cover_emoji": "💰",
                "reading_time_minutes": 8,
                "tags": ["salary", "negotiation", "compensation", "offer"],
                "excerpt": "Most people leave money on the table in every salary negotiation. Here's the exact playbook for getting what you're actually worth.",
                "days_ago": 31,
                "content": """<p class="lead">The average professional who negotiates their salary earns $5,000–$20,000 more per year than those who accept the first offer. Over a career, that difference compounds to hundreds of thousands of dollars.</p>

<h2>Rule #1: Never Give the First Number</h2>
<p>When asked "what are your salary expectations?", deflect with: <em>"I'd love to understand the full scope of the role before discussing compensation. What's the budgeted range for this position?"</em></p>
<p>If pressed, respond with a range where your target is at the low end. Never anchor low — you can always negotiate down, but you can rarely negotiate up from an early number.</p>

<h2>Do Your Research First</h2>
<p>Before any negotiation, know your market value precisely. Use multiple sources: Levels.fyi (for tech), LinkedIn Salary, Glassdoor, and recent conversations with peers in similar roles. Know the range for your specific title, location, years of experience, and company size.</p>

<h2>The Counter-Offer Formula</h2>
<p>When you receive an offer, don't respond immediately. Say: <em>"Thank you so much — I'm genuinely excited about this opportunity. Can I take 48 hours to review the full package?"</em></p>
<p>Then counter with 10–15% above the offer, supported by specific data: <em>"Based on my research and [X years] of [specific skill] experience, I was expecting something closer to $[number]. Is there flexibility to get to that level?"</em></p>

<h2>Negotiate the Full Package</h2>
<p>Base salary is just one component. Don't overlook:</p>
<ul>
  <li>Signing bonus (often easier to move than base)</li>
  <li>Equity / RSU vesting schedule</li>
  <li>Performance review timeline (ask for 6-month instead of annual)</li>
  <li>Remote work flexibility</li>
  <li>Learning & development budget</li>
  <li>Extra vacation days</li>
</ul>

<h2>The Silence Is Your Friend</h2>
<p>After making your counter-offer, stop talking. The first person to speak after a negotiation anchor almost always concedes. Sit in the silence. Let them respond. This is uncomfortable but enormously effective.</p>

<h2>What to Do When They Say No</h2>
<p>If they can't move on salary, ask: <em>"Is there anything else in the package we could adjust to get closer to my target total compensation?"</em> Then explore the signing bonus, equity, or review timeline. Almost every "no" on salary has a "yes" somewhere else in the package.</p>

<h2>The Follow-Up</h2>
<p>Get any final agreement in writing before you resign from your current role. Verbal commitments don't count. A professional, grateful email summarizing the agreed terms protects both parties and demonstrates your attention to detail from day one.</p>""",
            },
            {
                "title": "LinkedIn Profile Optimization: Get Found by Recruiters",
                "slug": "linkedin-profile-optimization",
                "category": "Job Search",
                "cover_emoji": "🔗",
                "reading_time_minutes": 7,
                "tags": ["linkedin", "profile", "networking", "recruiter"],
                "excerpt": "Recruiters are searching LinkedIn right now for someone with your skills. Make sure they find you — and like what they see.",
                "days_ago": 19,
                "content": """<p class="lead">Over 95% of recruiters use LinkedIn as their primary sourcing tool. If your profile isn't optimized, you're invisible to opportunities that could change your career.</p>

<h2>The LinkedIn Algorithm: What You Need to Know</h2>
<p>LinkedIn's recruiter search algorithm ranks profiles based on keyword relevance, completeness, and recent activity. Profiles with an "All-Star" completeness rating appear significantly higher in search results. Getting to All-Star is the first objective.</p>

<h2>Your Photo: First Impressions in 300ms</h2>
<p>Profiles with photos receive 21x more views than those without. Use a professional headshot with a clean background. Your face should fill 60% of the frame. Smile naturally. Avoid casual photos, group shots, or anything that looks like it was cropped from another image.</p>

<h2>Your Headline Is Your Ad Copy</h2>
<p>Most people use their job title as their headline. That's a missed opportunity. Your headline follows you everywhere on LinkedIn — comments, connection requests, search results. Make it descriptive and keyword-rich:</p>
<ul>
  <li>❌ "Software Engineer at Acme Corp"</li>
  <li>✅ "Full-Stack Engineer · React · Node.js · AWS · Building products used by 2M+ users"</li>
</ul>

<h2>The About Section: Your Elevator Pitch</h2>
<p>Write in first person. Open with a hook — your single most impressive achievement or your specific professional mission. Then cover: what you do, what you're best at, and what kind of opportunities you're interested in. End with a call to action: "Open to senior engineering roles at mission-driven companies. Let's connect."</p>

<h2>Experience: Accomplishments Over Duties</h2>
<p>Each role should have 3–5 bullet points that lead with action verbs and include measurable outcomes. Quantify wherever possible — percentages, dollar figures, user counts, time saved. Recruiters scan, not read — make your impact scannable.</p>

<h2>Skills and Endorsements</h2>
<p>Add your top 5 skills first — these get the most weight in search algorithms. Reach out to former colleagues for endorsements. Endorse others first; reciprocal endorsements often follow naturally.</p>

<h2>Stay Active</h2>
<p>The algorithm rewards active users. Post or comment at least twice a week. Share insights from your field, comment thoughtfully on others' posts, and publish the occasional long-form article. Activity signals to LinkedIn that you're engaged — and surfaces your profile to more recruiters.</p>""",
            },
            {
                "title": "AI Is Changing Every Job — Here's How to Stay Relevant",
                "slug": "ai-impact-on-jobs-2025",
                "category": "Industry Trends",
                "cover_emoji": "🤖",
                "reading_time_minutes": 9,
                "tags": ["AI", "future of work", "upskilling", "automation"],
                "excerpt": "Artificial intelligence isn't replacing workers — it's replacing workers who don't know how to use it. Here's how to future-proof your career.",
                "days_ago": 7,
                "content": """<p class="lead">The AI revolution isn't coming — it's here. In every industry, from marketing to medicine, professionals who learn to work alongside AI are becoming dramatically more productive. Those who don't are falling behind.</p>

<h2>What AI Actually Replaces (and What It Doesn't)</h2>
<p>AI excels at pattern recognition, data analysis, content generation, code completion, and repetitive decision-making. It struggles with creative problem-solving in novel contexts, interpersonal communication, ethical judgment, and physical dexterity.</p>
<p>The jobs most at risk are those that consist primarily of the former. The jobs most secure are those that require deep human judgment, creativity, and relationship-building — especially when augmented by AI tools.</p>

<h2>The Augmentation Advantage</h2>
<p>Research from MIT found that knowledge workers who adopted AI tools became 37% more productive. But the gains weren't distributed evenly — they went disproportionately to workers who used AI strategically rather than superficially.</p>
<p>Strategic AI use means: automating your low-value tasks completely, using AI as a thought partner and first-draft generator, and focusing your human attention on the 20% of work that requires genuine expertise and judgment.</p>

<h2>The Skills That AI Makes More Valuable</h2>
<p>Counterintuitively, the AI boom has increased demand for fundamentally human skills:</p>
<ul>
  <li><strong>Critical evaluation</strong> — knowing when AI output is wrong or incomplete</li>
  <li><strong>Complex reasoning</strong> — chaining together multiple problems that AI can't handle holistically</li>
  <li><strong>Stakeholder communication</strong> — translating AI capabilities into business outcomes</li>
  <li><strong>Domain expertise</strong> — AI is only as good as the expert guiding it</li>
</ul>

<h2>A 90-Day AI Upskilling Plan</h2>
<p><strong>Month 1:</strong> Pick three AI tools relevant to your work and spend 30 minutes a day learning them deeply. ChatGPT, Claude, Midjourney, GitHub Copilot — whatever your field needs.</p>
<p><strong>Month 2:</strong> Build something real. Create a workflow, a tool, or a project using AI that solves a genuine problem in your work. The act of building teaches you what guides and books can't.</p>
<p><strong>Month 3:</strong> Share what you've learned. Write a post, give a team presentation, or mentor a colleague. Teaching consolidates your learning and establishes you as an AI leader in your organization.</p>

<h2>The Long Game</h2>
<p>AI literacy is rapidly becoming as fundamental as computer literacy was in the 1990s. Professionals who invest in this skill now will have a compounding advantage for the next decade. Those who wait will find themselves competing against workers who are, effectively, more capable than they are.</p>
<p>The question isn't whether AI will change your job. It's whether you'll be the person using it — or the person replaced by someone who does.</p>""",
            },
            {
                "title": "Building a High-Performance Hiring Pipeline from Scratch",
                "slug": "high-performance-hiring-pipeline",
                "category": "Hiring Guide",
                "cover_emoji": "⚙️",
                "reading_time_minutes": 8,
                "tags": ["hiring", "recruiting", "HR", "talent pipeline"],
                "excerpt": "Slow, unpredictable hiring processes cost you the best candidates. Here's how to build a pipeline that consistently delivers A-players.",
                "days_ago": 44,
                "content": """<p class="lead">The average time-to-hire across industries is 36 days. The best candidates are off the market in 10. If your hiring process takes longer than three weeks, you are systematically losing to faster-moving companies.</p>

<h2>Diagnose Your Current Pipeline</h2>
<p>Before redesigning anything, map your current process and measure four metrics: time-to-hire, offer acceptance rate, quality-of-hire (90-day performance), and cost-per-hire. These four numbers will tell you exactly where your pipeline is broken.</p>

<h2>Write Job Descriptions That Actually Attract</h2>
<p>Most job descriptions are written for legal compliance, not candidate attraction. Every requirement you list reduces your applicant pool. Be ruthless: separate "must-haves" from "nice-to-haves" and cut the latter from the required section. Lead with why this role is an exceptional opportunity, not a list of duties.</p>
<p>A/B test your job descriptions. Small changes in title, requirements, and company description can change application volume by 30–50%.</p>

<h2>Design a 3-Round Interview Process</h2>
<p>The optimal interview process has three rounds — no more:</p>
<ol>
  <li><strong>Round 1 (30 min):</strong> Recruiter screen — culture fit, motivation, salary alignment</li>
  <li><strong>Round 2 (60–90 min):</strong> Technical or skills assessment with the hiring manager</li>
  <li><strong>Round 3 (90 min):</strong> Final round — team meet, deep dive on key competencies</li>
</ol>
<p>Each round should have a clear go/no-go decision with documented rationale. Ambiguity at any stage causes delays and loses candidates to faster competitors.</p>

<h2>Build Your Talent Pool Before You Need It</h2>
<p>Reactive hiring — posting a job when someone leaves — is expensive and slow. The best teams maintain a warm talent pool of 20–30 candidates they've already screened who could be hired quickly for anticipated roles.</p>
<p>Employee referrals are your highest-quality, lowest-cost source. Build a referral program with meaningful incentives ($2,000–$5,000 for successful hires is standard). Referred candidates hire 55% faster and stay 25% longer than those sourced externally.</p>

<h2>Make Offers Fast</h2>
<p>The single most impactful thing you can do: reduce decision-to-offer time to 24 hours. After a final round interview, debrief immediately. Make the decision that day. Send the offer letter that evening. Candidates who receive same-day or next-day offers are dramatically more likely to accept.</p>

<h2>Measure What Matters</h2>
<p>Track recruiter performance on speed and quality metrics, not just volume. The best recruiting teams report weekly on pipeline health, conversion rates at each stage, and offer acceptance rates. Data-driven hiring is consistently more effective than gut-driven hiring.</p>""",
            },
        ]

        for post_data in blog_posts:
            existing = await db.scalar(select(BlogPost).where(BlogPost.slug == post_data["slug"]))
            if not existing:
                db.add(BlogPost(
                    title=post_data["title"],
                    slug=post_data["slug"],
                    category=post_data["category"],
                    cover_emoji=post_data["cover_emoji"],
                    reading_time_minutes=post_data["reading_time_minutes"],
                    tags=post_data["tags"],
                    excerpt=post_data["excerpt"],
                    content=post_data["content"],
                    author_id=admin.id,
                    is_published=True,
                    published_at=datetime.utcnow() - timedelta(days=post_data["days_ago"]),
                ))
            else:
                # Update existing posts with richer content
                existing.content = post_data["content"]
                existing.cover_emoji = post_data.get("cover_emoji")
                existing.reading_time_minutes = post_data.get("reading_time_minutes", 5)
                existing.tags = post_data.get("tags", [])
        print("✅ Blog posts seeded")

        await db.commit()
        print("\n🎉 All seed data committed successfully!")
        print("\n── Demo credentials ──────────────────────────────────────────────")
        print("  Admin:     admin@taiq.us              / Admin@1234!")
        print("  Candidate: candidate@demo.com         / Candidate@1234!")
        print("  Employers (all): password             / Employer@1234!")
        print("    hr@acmetech.com · jobs@dataflow.io · recruit@metrohealth.org")
        print("    talent@fintechpartners.com · hr@cloudnative.io")
        print("    hiring@novabio.com · jobs@greenbridge.com · recruit@lexacorp.com")
        print("    hr@retailnext.com · talent@edupath.org · jobs@swiftlogix.com · hr@nimblemfg.com")
        print("    jobs@horizonai.io · hr@peakwellness.com · talent@vaultcapital.com")
        print("    jobs@terranova.build · hr@brightminds.edu · recruit@nexuslaw.com")
        print("    jobs@urbanstore.com · hr@alphalogistics.com · talent@primecast.com · jobs@steelcraft.io")
        print("──────────────────────────────────────────────────────────────────")


if __name__ == "__main__":
    asyncio.run(seed())
