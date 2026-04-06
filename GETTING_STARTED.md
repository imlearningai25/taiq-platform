# TaIQ — Getting Started Guide

## Prerequisites
| Tool | Min Version | Install |
|------|------------|---------|
| Docker Desktop | 4.x | https://www.docker.com/products/docker-desktop/ |
| Docker Compose | v2 (bundled) | Included with Docker Desktop |
| Git | any | https://git-scm.com |
| GNU Make | any | macOS: `brew install make` · Windows: use Git Bash |

> **Windows users:** Use Git Bash or WSL2 for all commands.

---

## Step 1 — Get the code

```bash
# Unzip the package
unzip taiq-platform.zip
cd taiq-platform
```

---

## Step 2 — Configure environment

```bash
# Copy the example env file (edit secrets before going to production)
cp .env.example .env
```

The defaults work out of the box for local development. Key values in `.env`:

| Variable | Default | Notes |
|----------|---------|-------|
| `APP_NAME` | TaIQ | Displayed in API docs |
| `POSTGRES_USER` | taiq | DB username |
| `POSTGRES_PASSWORD` | taiq_secret | **Change in production** |
| `POSTGRES_DB` | taiq_db | DB name |
| `SECRET_KEY` | change-me-... | **Change in production** |

---

## Step 3 — Start all services

```bash
make up
# or without Make:
docker compose up -d --build
```

This command:
- Builds the Python backend image (multi-stage, ~400MB)
- Pulls PostgreSQL 16, Redis 7, and Nginx images
- Creates the `taiq_net` Docker network
- Starts 5 containers: `taiq_db`, `taiq_redis`, `taiq_backend` (×2 replicas), `taiq_frontend`, `taiq_nginx`
- Waits for the database health check to pass before starting the backend

**First build takes 2–4 minutes** (downloads images + installs Python packages).
Subsequent starts take under 10 seconds.

---

## Step 4 — Load demo data

```bash
make seed
# or:
docker compose exec backend python seed.py
```

This inserts:
- 10 industry categories
- 5 employer companies + accounts  
- 6 sample job listings (featured + regular)
- 6 testimonials
- 3 blog posts
- Admin, candidate, and employer demo users

---

## Step 5 — Open in your browser

| URL | What you'll see |
|-----|----------------|
| **http://localhost:8090** | TaIQ homepage |
| **http://localhost:8090/api/docs** | Interactive Swagger API docs |
| **http://localhost:8090/api/redoc** | ReDoc API reference |
| **http://localhost:8090/api/health** | `{"status":"ok"}` health check |

---

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@taiq.us | Admin@1234! |
| Candidate | candidate@demo.com | Candidate@1234! |
| Employer | hr@acmetech.com | Employer@1234! |

---

## Common Commands

```bash
make up            # Start all services
make down          # Stop all services
make down-v        # Stop + wipe database volume
make logs          # Tail all service logs
make logs-backend  # Tail backend logs only
make seed          # Load demo data
make migrate       # Run Alembic DB migrations
make test          # Run pytest test suite
make shell-backend # Open bash inside backend container
make shell-db      # Open psql inside database container
make clean         # Remove all containers, images, volumes
```

---

## Project Structure (key files)

```
taiq-platform/
├── docker-compose.yml          ← All services wired together
├── .env                        ← Your local config (git-ignored)
├── .env.example                ← Template
├── Makefile                    ← Developer shortcuts
├── nginx/nginx.conf            ← Reverse proxy + rate limiting
├── backend/
│   ├── app/main.py             ← FastAPI entrypoint
│   ├── app/api/                ← API route handlers
│   ├── app/models/models.py    ← Database models
│   ├── seed.py                 ← Demo data loader
│   └── requirements.txt
└── frontend/
    ├── index.html              ← Main website
    ├── privacy-policy.html
    ├── terms-of-service.html
    ├── cookie-policy.html
    └── accessibility.html
```

---

## Troubleshooting

**Port 80 already in use?**
```bash
# Find what's using port 80
sudo lsof -i :80
# Change the port in docker-compose.yml:
# ports: - "8080:80"   ← use 8080 instead
```

**Database won't start?**
```bash
docker compose logs db
# If volume is corrupt:
make down-v && make up
```

**Backend crashes on startup?**
```bash
make logs-backend
# Usually a missing env variable — check your .env file
```

**Permission denied on make?**
```bash
chmod +x ./docker-compose.yml  # not needed — use: docker compose up -d --build
```

---

## Production Checklist

- [ ] Set `SECRET_KEY` to a 64-character random string: `openssl rand -hex 32`
- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Set `ENVIRONMENT=production`
- [ ] Add SSL certificate to `nginx/ssl/` and update `nginx.conf`
- [ ] Disable `create_all` in `backend/app/main.py` and use Alembic only
- [ ] Set up automated PostgreSQL backups
- [ ] Configure a firewall — only expose ports 80 and 443 publicly

---

*Built with FastAPI · PostgreSQL · Redis · Docker · Nginx*
