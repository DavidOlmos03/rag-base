.PHONY: help install dev-up dev-down prod-up prod-down logs init-db migrate test lint format clean

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "RAG Base Service - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install dependencies with Poetry
	poetry install

install-dev: ## Install dependencies including dev tools
	poetry install --with dev

# Docker Development
dev-up: ## Start development environment
	docker-compose -f docker-compose.dev.yml up -d

dev-build: ## Build and start development environment
	docker-compose -f docker-compose.dev.yml up -d --build

dev-down: ## Stop development environment
	docker-compose -f docker-compose.dev.yml down

dev-down-v: ## Stop development environment and remove volumes
	docker-compose -f docker-compose.dev.yml down -v

dev-restart: ## Restart development environment
	docker-compose -f docker-compose.dev.yml restart

dev-logs: ## View development logs (all services)
	docker-compose -f docker-compose.dev.yml logs -f

dev-logs-api: ## View API logs only
	docker-compose -f docker-compose.dev.yml logs -f api

# Docker Production
prod-up: ## Start production environment
	docker-compose -f docker-compose.prod.yml up -d

prod-build: ## Build and start production environment
	docker-compose -f docker-compose.prod.yml up -d --build

prod-down: ## Stop production environment
	docker-compose -f docker-compose.prod.yml down

prod-logs: ## View production logs
	docker-compose -f docker-compose.prod.yml logs -f

# Database
init-db: ## Initialize database with tables and seed data
	docker exec -it ragbase-api-dev poetry run python scripts/init_db.py

migrate: ## Run database migrations
	docker exec -it ragbase-api-dev poetry run alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	docker exec -it ragbase-api-dev poetry run alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	docker exec -it ragbase-api-dev poetry run alembic downgrade -1

db-shell: ## Access PostgreSQL shell
	docker exec -it ragbase-postgres-dev psql -U raguser -d ragbase

# Ollama
ollama-pull-llama3: ## Pull Llama3 model for Ollama
	docker exec -it ragbase-ollama-dev ollama pull llama3

ollama-pull-mistral: ## Pull Mistral model for Ollama
	docker exec -it ragbase-ollama-dev ollama pull mistral

ollama-list: ## List installed Ollama models
	docker exec -it ragbase-ollama-dev ollama list

# Testing
test: ## Run all tests
	poetry run pytest

test-unit: ## Run unit tests only
	poetry run pytest tests/unit

test-integration: ## Run integration tests only
	poetry run pytest tests/integration

test-cov: ## Run tests with coverage report
	poetry run pytest --cov=app --cov-report=html --cov-report=term

# Code Quality
format: ## Format code with Black
	poetry run black app tests

lint: ## Lint code with Ruff
	poetry run ruff check app tests

lint-fix: ## Lint and fix code with Ruff
	poetry run ruff check app tests --fix

type-check: ## Type check with MyPy
	poetry run mypy app

check-all: format lint type-check ## Run all code quality checks

# Local Development
run-local: ## Run API locally (requires services running)
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

shell: ## Access API container shell
	docker exec -it ragbase-api-dev bash

# Cleanup
clean: ## Clean up cache and build files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov .coverage

clean-all: clean dev-down-v ## Clean everything including Docker volumes

# Info
status: ## Show status of all services
	docker-compose -f docker-compose.dev.yml ps

services: ## List all running containers
	docker ps --filter "name=ragbase"

# Quick Setup
quickstart: dev-up init-db ollama-pull-llama3 ## Quick setup: start services, init DB, pull Llama3
	@echo ""
	@echo "✅ RAG Base Service is ready!"
	@echo ""
	@echo "📚 API Documentation: http://localhost:8000/api/v1/docs"
	@echo "🏥 Health Check: http://localhost:8000/api/v1/health"
	@echo "🗄️  PGAdmin: http://localhost:5050"
	@echo "📊 Redis Commander: http://localhost:8081"
	@echo ""
	@echo "Test credentials: test@example.com / testpassword123"
	@echo ""
