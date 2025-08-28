.DEFAULT_GOAL := help

PROJECT_NAME := $(shell basename $(CURDIR))
TEST_PROJECT_NAME := $(PROJECT_NAME)-test

# ==============================================================================
# Variables
# ==============================================================================

# Sudo Configuration - Allows running Docker commands with sudo when needed
SUDO_PREFIX :=
ifeq ($(SUDO),true)
	SUDO_PREFIX := sudo
endif

DOCKER_CMD := $(SUDO_PREFIX) docker

# ==============================================================================
# Docker Commands
# ==============================================================================

DEV_COMPOSE := DJANGO_ENV=development PROJECT_NAME=$(PROJECT_NAME) COMPOSE_PROJECT_NAME=$(PROJECT_NAME)-dev $(DOCKER_CMD) compose --project-name $(PROJECT_NAME)-dev
PROD_COMPOSE := DJANGO_ENV=production PROJECT_NAME=$(PROJECT_NAME) COMPOSE_PROJECT_NAME=$(PROJECT_NAME)-prod $(DOCKER_CMD) compose -f docker-compose.yml --project-name $(PROJECT_NAME)-prod
TEST_COMPOSE := DJANGO_ENV=test PROJECT_NAME=$(PROJECT_NAME) COMPOSE_PROJECT_NAME=$(PROJECT_NAME)-test $(DOCKER_CMD) compose --project-name $(PROJECT_NAME)-test

# ==============================================================================
# Help
# ==============================================================================

.PHONY: all
all: help ## Default target

.PHONY: help
help: ## Show this help message
	@echo "Usage: make [target] [VAR=value]"
	@echo ""
	@echo "Options:"
	@echo "  \033[36m%-25s\033[0m %s" "SUDO=true" "Run docker commands with sudo (e.g., make up SUDO=true)"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "; OFS=" "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ==============================================================================
# Environment Setup
# ==============================================================================

.PHONY: setup
setup: ## Install dependencies and create .env file if it doesn't exist
	@echo "Installing python dependencies with Poetry..."
	@poetry install
	@if [ ! -f .env ]; then \
		echo "Creating .env file from .env.example..."; \
		cp .env.example .env; \
	fi
	@echo "Setup complete."

# ==============================================================================
# Development Environment Commands
# ==============================================================================

.PHONY: up
up: ## Build images and start dev containers
	@echo "Building images and starting DEV containers..."
	@$(DEV_COMPOSE) up --build -d

.PHONY: down
down: ## Stop dev containers
	@echo "Stopping DEV containers..."
	@$(DEV_COMPOSE) down --remove-orphans

.PHONY: up-prod
up-prod: ## Build images and start prod-like containers
	@echo "Starting up PROD-like containers..."
	@$(PROD_COMPOSE) up -d --build

.PHONY: down-prod
down-prod: ## Stop prod-like containers
	@echo "Shutting down PROD-like containers..."
	@$(PROD_COMPOSE) down --remove-orphans

.PHONY: rebuild
rebuild: ## Rebuild services, pulling base images, without cache, and restart
	@echo "Rebuilding all DEV services with --no-cache and --pull..."
	@$(DEV_COMPOSE) up -d --build --no-cache --pull always

.PHONY: clean
clean: ## Remove all generated files and stop all containers
	@echo "Cleaning up project..."
	@$(DEV_COMPOSE) down -v --remove-orphans
	@$(PROD_COMPOSE) down -v --remove-orphans
	@echo "Cleanup complete."

.PHONY: logs
logs: ## Show and follow dev container logs
	@echo "Showing DEV logs..."
	@$(DEV_COMPOSE) logs -f

.PHONY: shell
shell: ## Start a shell inside the dev 'web' container
	@$(DEV_COMPOSE) ps --status=running --services | grep -q '^web$$' || { echo "Error: web container is not running. Please run 'make up' first." >&2; exit 1; }
	@echo "Connecting to DEV 'web' container shell..."
	@$(DEV_COMPOSE) exec web /bin/bash

# ==============================================================================
# Django Management Commands
# ==============================================================================

.PHONY: makemigrations
makemigrations: ## [DEV] Create new migration files
	@$(DEV_COMPOSE) exec web poetry run python manage.py makemigrations

.PHONY: migrate
migrate: ## [DEV] Run database migrations
	@echo "Running DEV database migrations..."
	@$(DEV_COMPOSE) exec web poetry run python manage.py migrate

.PHONY: superuser
superuser: ## [DEV] Create a Django superuser
	@echo "Creating DEV superuser..."
	@$(DEV_COMPOSE) exec web poetry run python manage.py createsuperuser

.PHONY: migrate-prod
migrate-prod: ## [PROD] Run database migrations in production-like environment
	@echo "Running PROD-like database migrations..."
	@$(PROD_COMPOSE) exec web python manage.py migrate

.PHONY: superuser-prod
superuser-prod: ## [PROD] Create a Django superuser in production-like environment
	@echo "Creating PROD-like superuser..."
	@$(PROD_COMPOSE) exec web python manage.py createsuperuser

# ==============================================================================
#  Code Quality
# ==============================================================================

.PHONY: format
format: ## Format code with Black and fix Ruff issues
	@echo "Formatting code with Black and Ruff..."
	@poetry run black .
	@poetry run ruff check . --fix

.PHONY: lint
lint: ## Check code format and lint issues
	@echo "Checking code format with Black..."
	@poetry run black --check .
	@echo "Checking code with Ruff..."
	@poetry run ruff check .

# ==============================================================================
#  Testing
# ==============================================================================

.PHONY: test
test: unit-test ## Run the full test suite

.PHONY: unit-test
unit-test: ## Run unit tests
	@echo "Running unit tests..."
	@DJANGO_ENV=test poetry run pytest tests/unit

.PHONY: db-test
db-test: ## Run the slower, database-dependent tests locally
	@echo "Running database tests..."
	@DJANGO_ENV=test poetry run python -m pytest tests/db
	
.PHONY: build-test
build-test: ## Build Docker image and run smoke tests in clean environment
	@echo "Building Docker image and running smoke tests..."
	@$(DOCKER_CMD) build --target builder -t $(TEST_PROJECT_NAME):test . || (echo "Docker build failed"; exit 1)
	@echo "Running smoke tests in Docker container..."
	@$(DOCKER_CMD) run --rm \
		-e DJANGO_ENV=test \
		-v $(CURDIR)/tests:/app/tests \
		-v $(CURDIR)/apps:/app/apps \
		-v $(CURDIR)/config:/app/config \
		-v $(CURDIR)/manage.py:/app/manage.py \
		-v $(CURDIR)/pyproject.toml:/app/pyproject.toml \
		$(TEST_PROJECT_NAME):test \
		sh -c "poetry run python -m pytest tests/unit/" || (echo "Smoke tests failed"; exit 1)
	@echo "Cleaning up test image..."
	@$(DOCKER_CMD) rmi $(TEST_PROJECT_NAME):test || true

.PHONY: e2e-test
e2e-test: ## Run end-to-end tests against a live application stack
	@echo "Running end-to-end tests..."
	@DJANGO_ENV=test poetry run python -m pytest tests/e2e




