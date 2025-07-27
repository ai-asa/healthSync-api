.PHONY: help install clean test test-unit test-integration test-coverage lint format type-check security-check run-dev docker-build docker-run db-up db-down db-migrate

# Default target
help:
	@echo "Available commands:"
	@echo "  make install          - Install all dependencies"
	@echo "  make clean            - Clean up generated files"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-coverage    - Run tests with coverage report"
	@echo "  make lint             - Run linting (ruff)"
	@echo "  make format           - Format code (black + isort)"
	@echo "  make type-check       - Run type checking (mypy)"
	@echo "  make security-check   - Run security checks"
	@echo "  make run-dev          - Run development server"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-run       - Run with Docker Compose"
	@echo "  make db-up            - Start MySQL container"
	@echo "  make db-down          - Stop MySQL container"
	@echo "  make db-migrate       - Run database migrations"

# Environment setup
install:
	uv pip install -r requirements-dev.txt
	pre-commit install

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov coverage.xml .pytest_cache
	rm -rf .mypy_cache .ruff_cache

# Testing
test:
	pytest

test-unit:
	pytest tests/unit -v -m "not integration"

test-integration:
	docker-compose up -d mysql
	pytest tests/integration -v -m "integration"
	docker-compose down

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term

test-performance:
	pytest tests/performance -v -m "performance"

# Code quality
lint:
	ruff check src tests

format:
	black src tests
	isort src tests

type-check:
	mypy src

security-check:
	bandit -r src
	safety check

# Development
run-dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Docker
docker-build:
	docker build -t healthsync-api:latest .

docker-run:
	docker-compose up --build

# Database
db-up:
	docker-compose up -d mysql

db-down:
	docker-compose down

db-migrate:
	alembic upgrade head

db-rollback:
	alembic downgrade -1

# CI/CD helpers
ci-test:
	@make lint
	@make type-check
	@make test-coverage

pre-commit:
	@make format
	@make lint
	@make type-check