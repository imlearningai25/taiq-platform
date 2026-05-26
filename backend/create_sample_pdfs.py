"""
Generate sample job-description PDFs for testing the AI file-upload parser.
Run inside the backend container:
  docker compose exec backend python create_sample_pdfs.py
Files are written to /app/sample_jobs/ (= ./backend/sample_jobs/ on the host).
"""
import os
from fpdf import FPDF

OUT_DIR = "/app/sample_jobs"
os.makedirs(OUT_DIR, exist_ok=True)


def clean(text: str) -> str:
    """Replace non-latin-1 characters with ASCII equivalents."""
    return (text
            .replace("–", "-").replace("—", "--")
            .replace("‘", "'").replace("’", "'")
            .replace("“", '"').replace("”", '"')
            .replace("•", "*").replace("…", "..."))


class JobPDF(FPDF):
    def __init__(self, company: str):
        super().__init__()
        self.company = company
        self.add_page()
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(True, margin=20)

    def header_block(self, title: str, company: str, location: str,
                     job_type: str, salary: str, remote: bool):
        self.set_fill_color(10, 40, 100)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 18)
        self.cell(0, 12, clean(title), new_x="LMARGIN", new_y="NEXT", fill=True, align="L")
        self.set_font("Helvetica", "", 11)
        self.set_fill_color(230, 235, 245)
        self.set_text_color(40, 40, 40)
        meta = f"{company}  |  {location}  |  {job_type}  |  {clean(salary)}"
        if remote:
            meta += "  |  Remote / Hybrid"
        self.cell(0, 8, meta, new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(4)

    def section(self, heading: str, body: str):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(10, 40, 100)
        self.cell(0, 8, heading, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(10, 40, 100)
        self.line(self.get_x(), self.get_y(), 190, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        for line in body.strip().split("\n"):
            line = clean(line.strip())
            if not line:
                self.ln(2)
                continue
            if line.startswith("-") or line.startswith("*"):
                line = "  - " + line.lstrip("-* ").strip()
            self.multi_cell(self.epw, 5.5, line)
        self.ln(4)


JOBS = [
    # ── 1 ─────────────────────────────────────────────────────────────────────
    {
        "filename": "senior_software_engineer.pdf",
        "title": "Senior Software Engineer – Platform Team",
        "company": "NovaTech Solutions",
        "location": "San Francisco, CA",
        "job_type": "Full Time",
        "salary": "$160,000 – $210,000 / year",
        "remote": True,
        "description": """\
NovaTech Solutions is building the next generation of cloud infrastructure
tools used by thousands of developers worldwide. We are looking for a
Senior Software Engineer to join our Platform team and help design, build,
and maintain the core services that power our SaaS product.

You will work closely with product managers, designers, and other engineers
to deliver high-quality, scalable features with a focus on reliability and
developer experience.""",
        "requirements": """\
- 5+ years of professional software engineering experience
- Strong proficiency in Python and/or Go
- Experience designing and operating distributed systems at scale
- Solid understanding of REST and gRPC APIs
- Familiarity with Kubernetes, Terraform, and AWS or GCP
- Experience with PostgreSQL and Redis
- Strong communication skills and ability to work across time zones""",
        "benefits": """\
- Competitive salary and equity package
- Fully remote-friendly with optional hub offices
- Unlimited PTO with a minimum 3-week expectation
- $3,000 annual learning & development budget
- Top-tier health, dental, and vision insurance
- Home-office setup stipend of $2,000""",
        "skills": ["Python", "Go", "Kubernetes", "PostgreSQL", "Redis", "AWS", "gRPC"],
        "industry": "Technology",
    },
    # ── 2 ─────────────────────────────────────────────────────────────────────
    {
        "filename": "registered_nurse_icu.pdf",
        "title": "Registered Nurse – ICU",
        "company": "Maplewood Medical Center",
        "location": "Chicago, IL",
        "job_type": "Full Time",
        "salary": "$80,000 – $105,000 / year",
        "remote": False,
        "description": """\
Maplewood Medical Center is a 450-bed acute-care hospital serving the
greater Chicago metropolitan area. We are seeking a compassionate,
detail-oriented Registered Nurse to join our Intensive Care Unit (ICU).

You will provide direct patient care to critically ill adults, collaborate
with the multidisciplinary care team, and mentor junior nursing staff in
evidence-based best practices.""",
        "requirements": """\
- Active RN license in the state of Illinois (or compact license)
- Bachelor of Science in Nursing (BSN) required; MSN preferred
- Minimum 2 years of ICU or critical-care experience
- ACLS, BLS, and CCRN certification (or willingness to obtain within 6 months)
- Proficiency with EMR systems (Epic preferred)
- Excellent critical-thinking and communication skills""",
        "benefits": """\
- Shift differentials for nights, weekends, and holidays
- Tuition reimbursement up to $7,500 per year
- Loan forgiveness eligibility (PSLF)
- Comprehensive medical, dental, and vision insurance
- 403(b) retirement plan with employer match
- Free on-site parking and subsidised cafeteria""",
        "skills": ["ICU", "ACLS", "BLS", "CCRN", "Epic EMR", "Critical Care", "Patient Assessment"],
        "industry": "Healthcare",
    },
    # ── 3 ─────────────────────────────────────────────────────────────────────
    {
        "filename": "financial_analyst.pdf",
        "title": "Financial Analyst – FP&A",
        "company": "Apex Capital Group",
        "location": "New York, NY",
        "job_type": "Full Time",
        "salary": "$95,000 – $130,000 / year",
        "remote": True,
        "description": """\
Apex Capital Group is a mid-market investment firm managing $4B in assets
across private equity, credit, and infrastructure strategies. We are looking
for a Financial Analyst to join our Financial Planning & Analysis (FP&A)
team and support portfolio performance reporting and strategic budgeting.

You will build and maintain financial models, prepare management reports,
and partner with portfolio company CFOs on operational performance tracking.""",
        "requirements": """\
- Bachelor's degree in Finance, Accounting, Economics, or related field
- 2–4 years of experience in investment banking, private equity, or corporate FP&A
- Advanced Excel and financial modelling skills
- Experience with SQL for data extraction and analysis
- CFA Level 1 or progress towards CFA designation preferred
- Strong written and verbal communication skills""",
        "benefits": """\
- Performance bonus up to 20% of base salary
- Hybrid work schedule (3 days in-office)
- Paid CFA exam fees and study materials
- Comprehensive health benefits from Day 1
- 401(k) with 4% employer match
- Quarterly team offsites""",
        "skills": ["Financial Modelling", "Excel", "SQL", "FP&A", "CFA", "PowerBI", "Budgeting"],
        "industry": "Finance",
    },
    # ── 4 ─────────────────────────────────────────────────────────────────────
    {
        "filename": "growth_marketing_manager.pdf",
        "title": "Growth Marketing Manager",
        "company": "BrightLeaf Commerce",
        "location": "Austin, TX",
        "job_type": "Full Time",
        "salary": "$110,000 – $140,000 / year",
        "remote": True,
        "description": """\
BrightLeaf Commerce is a fast-growing DTC e-commerce brand in the
sustainable home-goods space. We are hiring a Growth Marketing Manager
to own our paid acquisition, lifecycle email/SMS, and conversion
optimisation programmes.

Reporting to the VP of Marketing, you will develop and execute
multi-channel campaigns, run rigorous A/B tests, and turn data into
actionable growth strategies.""",
        "requirements": """\
- 4+ years in performance or growth marketing roles
- Proven track record managing Meta Ads and Google Ads at $1M+ monthly spend
- Hands-on experience with Klaviyo or a comparable ESP for email and SMS
- Strong analytical skills; comfort with Google Analytics 4 and Looker
- Experience with CRO tools such as Optimizely or VWO
- Excellent project management and cross-functional collaboration skills""",
        "benefits": """\
- Fully remote with flexible working hours
- Generous product discount and annual gifting budget
- $2,000 professional development budget
- Health, dental, and vision insurance
- 401(k) with employer match
- Paid parental leave (16 weeks)""",
        "skills": ["Meta Ads", "Google Ads", "Klaviyo", "SEO", "CRO", "Google Analytics", "A/B Testing"],
        "industry": "Marketing",
    },
    # ── 5 ─────────────────────────────────────────────────────────────────────
    {
        "filename": "mechanical_engineer.pdf",
        "title": "Mechanical Engineer – Product Development",
        "company": "Orion Dynamics Inc.",
        "location": "Detroit, MI",
        "job_type": "Full Time",
        "salary": "$90,000 – $120,000 / year",
        "remote": False,
        "description": """\
Orion Dynamics Inc. is a Tier-1 automotive supplier specialising in
precision-machined components and sub-assemblies. We are looking for a
Mechanical Engineer to join our Product Development team and lead the
design and validation of new powertrain components from concept through
production launch.

You will collaborate with cross-functional teams including manufacturing,
quality, and customer programmes to deliver components on time and within
cost targets.""",
        "requirements": """\
- Bachelor's degree in Mechanical Engineering (BSME required; MSME preferred)
- 3–6 years of experience in automotive or heavy-equipment product development
- Proficiency in SolidWorks and CATIA V5 for 3-D modelling and GD&T
- Familiarity with APQP, PPAP, FMEA, and DVP&R processes
- Experience with FEA tools such as ANSYS or Abaqus
- Knowledge of materials science (steels, aluminium alloys, composites)""",
        "benefits": """\
- Competitive base salary plus annual profit-sharing bonus
- On-site gym and wellness programme
- Comprehensive medical, dental, and vision coverage
- 401(k) with 5% employer match
- Tuition reimbursement up to $6,000 per year
- Relocation assistance available""",
        "skills": ["SolidWorks", "CATIA", "FEA", "APQP", "PPAP", "GD&T", "ANSYS"],
        "industry": "Engineering",
    },
]


def build_pdf(job: dict) -> str:
    pdf = JobPDF(job["company"])
    pdf.header_block(
        job["title"], job["company"], job["location"],
        job["job_type"], job["salary"], job["remote"],
    )
    pdf.section("About the Role", job["description"])
    pdf.section("Requirements", "\n".join(f"- {r}" for r in job["requirements"].strip().split("\n") if r.strip()))
    pdf.section("What We Offer", "\n".join(f"- {b}" for b in job["benefits"].strip().split("\n") if b.strip()))

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(10, 40, 100)
    pdf.cell(0, 8, "Skills", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(10, 40, 100)
    pdf.line(pdf.get_x(), pdf.get_y(), 190, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(pdf.epw, 5.5, "  |  ".join(job["skills"]))

    out_path = os.path.join(OUT_DIR, job["filename"])
    pdf.output(out_path)
    return out_path


if __name__ == "__main__":
    print(f"\n📄 Generating sample job PDFs → {OUT_DIR}\n")
    for j in JOBS:
        path = build_pdf(j)
        print(f"  ✅  {j['filename']}  ({j['industry']})")
    print(f"\n🎉 Done! {len(JOBS)} files written to ./backend/sample_jobs/\n")
