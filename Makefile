.PHONY: help install lint test format clean serve dev setup

help:
	@echo "Reverse Proxy MCP - Development Commands"
	@echo "=========================================="
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
	curl -LsSf https://astral.sh/uv/install.sh | sh
	uv sync --all-groups
	pre-commit install

install:
	uv sync --all-groups

lint:
	uv run black --check src tests
	uv run ruff check src tests
	uv run mypy src

format:
	uv run black src tests
	uv run ruff check --fix src tests

test:
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html

test-unit:
	uv run pytest -m unit --cov=src --cov-report=term-missing

test-integration:
	uv run pytest -m integration --cov=src --cov-report=term-missing

test-coverage:
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

dev:
	uv run python -m reverse_proxy_mcp

serve:
	uv run uvicorn reverse_proxy_mcp.api.main:create_app --reload --port 8000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	rm -rf dist build *.egg-info .uv-cache

db-init:
	uv run python -c "from reverse_proxy_mcp.core import create_all_tables; create_all_tables()"

pre-commit-run:
	pre-commit run --all-files
