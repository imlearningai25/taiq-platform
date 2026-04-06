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
        print("\n── Demo credentials ─────────────────────────────────────────")
        print("  Admin:     admin@taiq.us     / Admin@1234!")
        print("  Candidate: candidate@demo.com          / Candidate@1234!")
        print("  Employer:  hr@acmetech.com             / Employer@1234!")
        print("─────────────────────────────────────────────────────────────")


if __name__ == "__main__":
    asyncio.run(seed())
