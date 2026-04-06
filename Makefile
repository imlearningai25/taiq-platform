.PHONY: up down build logs seed migrate test shell-backend shell-db clean help

## ── Docker ───────────────────────────────────────────────────────────────────
up:            ## Start all services
	cp -n .env.example .env 2>/dev/null || true
	docker compose up -d --build
	@echo "✅  TaIQ is running at http://localhost"
	@echo "📖  API docs at           http://localhost/api/docs"

up-dev:        ## Start with live logs
	docker compose up --build

down:          ## Stop all services
	docker compose down

down-v:        ## Stop and remove volumes (wipes DB)
	docker compose down -v

build:         ## Re-build images
	docker compose build --no-cache

logs:          ## Tail logs
	docker compose logs -f

logs-backend:  ## Tail backend logs only
	docker compose logs -f backend

## ── Database ─────────────────────────────────────────────────────────────────
seed:          ## Populate demo data
	docker compose exec backend python seed.py

migrate:       ## Run Alembic migrations
	docker compose exec backend alembic upgrade head

migration:     ## Create a new migration (make migration msg="add X table")
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

## ── Backend ──────────────────────────────────────────────────────────────────
test:          ## Run backend test suite
	docker compose exec backend \
		sh -c "pip install -r requirements-test.txt -q && pytest -v"

shell-backend: ## Shell into backend container
	docker compose exec backend bash

shell-db:      ## psql into Postgres
	docker compose exec db psql -U staffing -d staffing_db

## ── Misc ─────────────────────────────────────────────────────────────────────
clean:         ## Remove containers, images, volumes
	docker compose down -v --rmi all

help:          ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n",$$1,$$2}'
