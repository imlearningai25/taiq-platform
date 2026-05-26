# TaIQ — Full-Stack Staffing Platform

A professional, production-ready staffing & recruitment platform inspired by Randstad USA, built with:

- **Backend:** FastAPI (Python 3.12) + SQLAlchemy async ORM
- **Database:** PostgreSQL 16 with Alembic migrations
- **Cache:** Redis 7
- **Frontend:** Vanilla HTML/CSS/JS (zero-dependency, blazing-fast)
- **Reverse Proxy:** Nginx (load-balanced, rate-limited)
- **Containerization:** Docker + Docker Compose (horizontally scalable)

---

## ✨ Features

### For Job Seekers
- Browse & search thousands of jobs by keyword, location, type, salary
- Filter by industry, remote status, job type
- One-click apply with cover letter
- Track application status in real-time
- Build a rich candidate profile with skills & experience

### For Employers
- Post unlimited job listings
- Manage applicants through a hiring pipeline
- Company profile with verification badge
- Analytics dashboard (views, applications, conversion rates)

### Platform
- JWT-based authentication (register/login)
- AI-powered job matching (architecture-ready)
- Responsive, mobile-first frontend
- RESTful API with OpenAPI/Swagger docs
- Role-based access control (candidate / employer / admin)
- Horizontal scaling via Docker Compose replicas

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop 4.x+ (includes Compose v2)
- GNU Make (optional but recommended)

### 1 — Clone & configure
```bash
git clone <repo-url> taiq
cd taiq
cp .env.example .env        # edit secrets before production!
```

### 2 — Start everything
```bash
make up
# or without make:
docker compose up -d --build
```

### 3 — Seed demo data
```bash
make seed
# or:
docker compose exec backend python seed.py
```

### 4 — Open in browser
| URL | Description |
|-----|-------------|
| http://localhost:8090 | Frontend website |
| http://localhost:8090/api/docs | Swagger UI |
| http://localhost:8090/api/redoc | ReDoc |
| http://localhost:8090/api/health | Health check |

### Demo credentials
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@taiq.us | Admin@1234! |
| Candidate | candidate@demo.com | Candidate@1234! |
| Employer | hr@acmetech.com | Employer@1234! |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Client Browser                    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP :80
              ┌────────▼────────┐
              │   Nginx Proxy   │  ← Rate limiting, gzip,
              │  (nginx:alpine) │    SSL termination
              └────┬───────┬───┘
                   │       │
         /api/*    │       │  /*
          ┌────────▼──┐  ┌─▼────────────┐
          │  Backend  │  │   Frontend   │
          │ (×2 reps) │  │  (nginx SPA) │
          │  FastAPI  │  └──────────────┘
          └─────┬─────┘
                │
      ┌─────────▼──────────┐
      │   PostgreSQL 16    │  ← Persistent volume
      └────────────────────┘
                │
      ┌─────────▼──────────┐
      │     Redis 7        │  ← Session cache
      └────────────────────┘
```

---

## 📁 Project Structure

```
taiq/
├── docker-compose.yml          # Orchestration
├── .env.example                # Environment template
├── Makefile                    # Developer shortcuts
├── nginx/
│   └── nginx.conf              # Reverse proxy + rate limiting
├── docker/
│   └── init.sql                # DB bootstrap seed
├── backend/
│   ├── Dockerfile              # Multi-stage Python build
│   ├── requirements.txt        # Production deps
│   ├── requirements-test.txt   # Test deps
│   ├── alembic.ini             # Migration config
│   ├── alembic/
│   │   └── env.py              # Async migration env
│   ├── seed.py                 # Demo data seeder
│   └── app/
│       ├── main.py             # FastAPI app entrypoint
│       ├── core/
│       │   ├── config.py       # Pydantic settings
│       │   ├── database.py     # Async SQLAlchemy engine
│       │   └── security.py     # JWT + bcrypt helpers
│       ├── models/
│       │   └── models.py       # SQLAlchemy ORM models
│       ├── schemas/
│       │   └── schemas.py      # Pydantic I/O schemas
│       └── api/
│           ├── auth.py         # Register / Login
│           ├── jobs.py         # Job search & detail
│           ├── applications.py # Apply, track, withdraw
│           ├── companies.py    # Company profiles
│           ├── employer.py     # Post & manage jobs, employer applications
│           ├── parse_job.py    # AI-powered job file parser (CSV/PDF/DOCX)
│           ├── profile.py      # Candidate profile, saved jobs, resume upload
│           ├── notifications.py# In-app notifications
│           ├── admin.py        # Admin panel: users, sites settings, audit log
│           └── public.py       # Stats, industries, blog
└── frontend/
    ├── Dockerfile              # Nginx static server
    ├── nginx-frontend.conf     # SPA routing
    └── index.html              # Complete single-page app
```

---

## 🔧 Developer Commands

```bash
make up            # Start all services (builds if needed)
make down          # Stop all services
make down-v        # Stop + wipe database
make logs          # Tail all logs
make seed          # Insert demo data
make migrate       # Run pending Alembic migrations
make migration msg="add salary_currency column"   # New migration
make test          # Run pytest suite
make shell-backend # Bash inside backend container
make shell-db      # psql inside Postgres container
make clean         # Remove everything (containers + images + volumes)
```

---

## 🔌 API Reference

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Obtain JWT |

### Jobs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/jobs` | Search / list jobs |
| GET | `/api/v1/jobs/featured` | Featured jobs |
| GET | `/api/v1/jobs/{id}` | Job detail |

### Applications (requires auth)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/applications` | Apply to job |
| GET | `/api/v1/applications/my` | My applications |
| DELETE | `/api/v1/applications/{id}` | Withdraw |

### Profile / Me (requires auth)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/me` | Get own profile + company |
| PATCH | `/api/v1/me` | Update name / phone |
| PUT | `/api/v1/me/profile` | Update candidate professional profile |
| POST | `/api/v1/me/change-password` | Change password |
| POST | `/api/v1/me/resume` | Upload resume (PDF/DOC/DOCX, max 10 MB) |
| DELETE | `/api/v1/me/resume` | Delete uploaded resume |
| GET | `/api/v1/me/saved` | List saved jobs |
| POST | `/api/v1/me/saved/{job_id}` | Save a job |
| DELETE | `/api/v1/me/saved/{job_id}` | Unsave a job |
| GET | `/api/v1/me/activities` | Own activity log |
| GET | `/api/v1/me/notifications` | List notifications (last 50) |
| PATCH | `/api/v1/me/notifications/{id}/read` | Mark one notification read |
| PATCH | `/api/v1/me/notifications/read-all` | Mark all notifications read |

### Employer (requires employer role)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/employer/jobs` | Post a job |
| GET | `/api/v1/employer/jobs` | My job postings |
| DELETE | `/api/v1/employer/jobs/{id}` | Deactivate posting |
| GET | `/api/v1/employer/jobs/company` | Get own company profile |
| PUT | `/api/v1/employer/jobs/company` | Update own company profile |
| GET | `/api/v1/employer/applications` | Applications to my jobs |
| PATCH | `/api/v1/employer/applications/{id}/status` | Update application status |
| POST | `/api/v1/employer/parse-job-file` | AI-parse CSV/PDF/DOCX into job fields |

### Companies
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/companies` | List / search companies |
| POST | `/api/v1/companies` | Create company profile |
| GET | `/api/v1/companies/{id}` | Company detail |
| PUT | `/api/v1/companies/{id}` | Update company (owner or admin) |

### Admin (requires admin role)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/site-settings` | Read site mode + construction content |
| PUT | `/api/v1/admin/site-settings` | Update site mode / construction content |
| GET | `/api/v1/admin/overview` | Platform stats (users, jobs, applications) |
| GET | `/api/v1/admin/users` | List users (filterable by role / search) |
| GET | `/api/v1/admin/users/count` | Total + verified user counts |
| PATCH | `/api/v1/admin/users/{id}/toggle-verify` | Toggle email-verified flag |
| GET | `/api/v1/admin/users/{id}/activities` | Activity log for a user |
| GET | `/api/v1/admin/jobs` | All jobs platform-wide |
| GET | `/api/v1/admin/applications` | All applications platform-wide |
| GET | `/api/v1/admin/companies` | All companies (with job counts) |
| PUT | `/api/v1/admin/companies/{id}` | Edit any company |
| PATCH | `/api/v1/admin/companies/{id}/verify` | Toggle company verified badge |
| DELETE | `/api/v1/admin/companies/{id}` | Delete company |
| GET | `/api/v1/admin/activities` | Platform-wide audit log |

### Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/public/stats` | Platform stats |
| GET | `/api/v1/public/industries` | Industry list |
| GET | `/api/v1/public/testimonials` | Testimonials |
| GET | `/api/v1/public/blog` | Blog posts |

Full interactive docs: **http://localhost:8090/api/docs**

---

## ⚙️ Scaling

### Scale backend horizontally
```bash
docker compose up -d --scale backend=4
```

### Production checklist
- [ ] Replace `SECRET_KEY` with a 64-char random string
- [ ] Set `ENVIRONMENT=production`
- [ ] Add SSL certificate to `nginx/ssl/`
- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Configure Redis password in `.env` + `nginx.conf`
- [ ] Enable Alembic migrations (disable `create_all` in `main.py`)
- [ ] Set up daily PostgreSQL backups
- [ ] Add monitoring (Prometheus + Grafana or Datadog)

---

## 🧪 Running Tests

```bash
make test
# or locally (with virtualenv):
pip install -r requirements.txt -r requirements-test.txt
pytest -v
```

---

## 📄 License

MIT License — free to use and modify for commercial and personal projects.
