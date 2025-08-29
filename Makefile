# ==============================================================================
# Makefile for Django Site Template
#
# Provides a unified interface for common development tasks, abstracting away
# the underlying Docker Compose commands for a better Developer Experience (DX).
#
# Inspired by the self-documenting Makefile pattern.
# ==============================================================================

# Default target executed when 'make' is run without arguments
.DEFAULT_GOAL := help

# ==============================================================================
# Sudo Configuration
#
# Allows running Docker commands with sudo when needed (e.g., in CI environments).
# Usage: make up SUDO=true
# ==============================================================================
SUDO_PREFIX := 
ifeq ($(SUDO),true)
    SUDO_PREFIX := sudo
endif

DOCKER_CMD := $(SUDO_PREFIX) docker

# Define the project name based on the directory name for dynamic container naming
PROJECT_NAME := $(shell basename $(CURDIR))

# Define project names for different environments
DEV_PROJECT_NAME := $(PROJECT_NAME)-dev
PROD_PROJECT_NAME := $(PROJECT_NAME)-prod
TEST_PROJECT_NAME := $(PROJECT_NAME)-test

# ==============================================================================
# HELP
# ==============================================================================

.PHONY: help
help: ## Show this help message
	@echo "Usage: make [target] [VAR=value]"
	@echo "Options:"
	@echo "  \033[36m%-15s\033[0m %s" "SUDO=true" "Run docker commands with sudo (e.g., make up SUDO=true)"
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $1, $2}' $(MAKEFILE_LIST)

# ==============================================================================
# Environment Setup
# ==============================================================================

.PHONY: setup
setup: ## Initialize project: install dependencies, create .env file and pull required Docker images.
	@echo "Installing python dependencies with Poetry..."
	@poetry install --no-root
	@echo "Creating environment file..."
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..." ; \
		cp .env.example .env; \
	else \
		echo ".env already exists. Skipping creation."; \
	fi
	@echo "✅ Environment file created (.env)"
	@echo "💡 You can customize .env for your specific needs:"
	@echo "   📝 Change database settings as needed"
	@echo "   📝 Adjust DEBUG and SECRET_KEY for development"
	@echo ""
	@echo "Pulling PostgreSQL image for development and tests..."
	$(DOCKER_CMD) pull postgres:16-alpine

# ==============================================================================
# Development Environment Commands
# ==============================================================================

.PHONY: up
up: ## Start all development containers in detached mode
	@echo "Starting up development services..."
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) up -d --build

.PHONY: down
down: ## Stop and remove all development containers
	@echo "Shutting down development services..."
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) down --remove-orphans

.PHONY: rebuild
rebuild: ## Rebuild the web service without cache and restart it
	@echo "Rebuilding web service with --no-cache..."
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) build --no-cache web
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) up -d web

.PHONY: up-prod
up-prod: ## Start all production-like containers
	@echo "Starting up production-like services..."
	$(DOCKER_CMD) compose -f docker-compose.yml --project-name $(PROD_PROJECT_NAME) up -d --build --pull always --remove-orphans

.PHONY: down-prod
down-prod: ## Stop and remove all production-like containers
	@echo "Shutting down production-like services..."
	$(DOCKER_CMD) compose -f docker-compose.yml --project-name $(PROD_PROJECT_NAME) down --remove-orphans

.PHONY: logs
logs: ## View the logs for the development web service
	@echo "Following logs for the dev web service..."
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) logs -f web

.PHONY: shell
shell: ## Open a shell inside the running development web container
	@echo "Opening shell in dev web container..."
	@$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) exec web /bin/bash || \
		(echo "Failed to open shell. Is the container running? Try 'make up'" && exit 1)


# ==============================================================================
# Django Management Commands
# ==============================================================================

.PHONY: makemigrations
makemigrations: ## Create new migration files. Usage: make makemigrations m="Your migration message"
	@if [ -n "$(m)" ]; then \
		echo "Creating migration with message: $(m)..."; \
		$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) exec web poetry run python manage.py makemigrations --name "$(m)"; \
	else \
		echo "Creating migration..."; \
		$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) exec web poetry run python manage.py makemigrations; \
	fi

.PHONY: migrate
migrate: ## Run database migrations against the development database
	@echo "Running database migrations for dev environment..."
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) exec web poetry run python manage.py migrate

.PHONY: superuser
superuser: ## Create a Django superuser
	@echo "Creating superuser..."
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) exec web poetry run python manage.py createsuperuser


# ==============================================================================
# CODE QUALITY 
# ==============================================================================

.PHONY: format
format: ## Format code with black and ruff --fix
	@echo "Formatting code with black and ruff..."
	poetry run black .
	poetry run ruff check . --fix

.PHONY: lint
lint: ## Lint code with black check and ruff
	@echo "Linting code with black check and ruff..."
	poetry run black --check .
	poetry run ruff check .

# ==============================================================================
# TESTING
# ==============================================================================

.PHONY: test
test: unit-test build-test db-test e2e-test ## Run the full test suite

.PHONY: unit-test
unit-test: ## Run the fast, database-independent unit tests locally
	@echo "Running unit tests..."
	@poetry run python -m pytest tests/unit -s

.PHONY: db-test
db-test: ## Run the slower, database-dependent tests locally
	@echo "Running database tests..."
	@poetry run python -m pytest tests/db -s

.PHONY: e2e-test
e2e-test: ## Run end-to-end tests against a live application stack
	@echo "Running end-to-end tests..."
	@poetry run python -m pytest tests/e2e -s

.PHONY: test-docker
test-docker: ## Run all tests in Docker containers with isolated test database
	@echo "Running tests in Docker containers..."
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.test.override.yml --project-name $(TEST_PROJECT_NAME) up --build --abort-on-container-exit --remove-orphans
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.test.override.yml --project-name $(TEST_PROJECT_NAME) down --remove-orphans

.PHONY: build-test
build-test: ## Build Docker image for testing without leaving artifacts
	@echo "Building Docker image for testing (clean build)..."
	@TEMP_IMAGE_TAG=$(date +%s)-build-test; \
	$(DOCKER_CMD) build --target production --tag temp-build-test:$TEMP_IMAGE_TAG . && \
	echo "Build successful. Cleaning up temporary image..." && \
	$(DOCKER_CMD) rmi temp-build-test:$TEMP_IMAGE_TAG || true




