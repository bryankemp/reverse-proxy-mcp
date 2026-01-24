.PHONY: help install lint test format clean serve dev setup

help:
	@echo "Nginx Manager - Development Commands"
	@echo "===================================="
	@echo "make setup         - Create venv and install dependencies"
	@echo "make install       - Install dependencies"
	@echo "make lint          - Run linting checks (black, ruff, mypy)"
	@echo "make format        - Format code with black and ruff"
	@echo "make test          - Run all tests"
	@echo "make test-unit     - Run unit tests only"
	@echo "make test-coverage - Run tests with coverage report"
	@echo "make dev           - Run API server in development mode"
	@echo "make clean         - Remove cache and build artifacts"
	@echo "make db-init       - Initialize database"

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install -e ".[dev]"
	pre-commit install

install:
	pip install -e ".[dev]"

lint:
	black --check src tests
	ruff check src tests
	mypy src

format:
	black src tests
	ruff check --fix src tests

test:
	pytest --cov=src --cov-report=term-missing --cov-report=html

test-unit:
	pytest -m unit --cov=src --cov-report=term-missing

test-integration:
	pytest -m integration --cov=src --cov-report=term-missing

test-coverage:
	pytest --cov=src --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

dev:
	python -m nginx_manager

serve:
	uvicorn nginx_manager.api.main:create_app --reload --port 8000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	rm -rf dist build *.egg-info

db-init:
	python -c "from nginx_manager.core import create_all_tables; create_all_tables()"

pre-commit-run:
	pre-commit run --all-files
