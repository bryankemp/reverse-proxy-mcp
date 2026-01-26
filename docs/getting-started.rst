Getting Started
===============

Installation
------------

Prerequisites
^^^^^^^^^^^^^

- Python 3.10 or higher
- Docker and Docker Compose (for containerized deployment)
- Git

Quick Install
^^^^^^^^^^^^^

Clone the repository::

    git clone https://gitlab.kempville.com/yourusername/reverse-proxy-mcp.git
    cd reverse-proxy-mcp

Install uv (fast Python package manager)::

    curl -LsSf https://astral.sh/uv/install.sh | sh

Install dependencies::

    uv sync --all-groups

Install pre-commit hooks::

    pre-commit install

Configuration
-------------

Create environment file::

    cp .env.example .env

Edit ``.env`` and set the following:

- ``ADMIN_EMAIL``: Admin username (default: admin)
- ``ADMIN_PASSWORD``: Admin password (default: password)
- ``SECRET_KEY``: JWT secret key (generate with ``openssl rand -hex 32``)
- ``DATABASE_URL``: SQLite database path (default: sqlite:///./data/reverse_proxy_mcp.db)

Running the Application
-----------------------

Local Development
^^^^^^^^^^^^^^^^^

Run the API server::

    uv run python -m reverse_proxy_mcp

Or with uvicorn::

    uv run uvicorn reverse_proxy_mcp.api.main:create_app --reload --port 8000

The API will be available at http://localhost:8000

Access the API documentation at http://localhost:8000/docs

Docker Compose
^^^^^^^^^^^^^^

Build and start all services::

    docker-compose up -d

Services:

- API: http://localhost:8000
- MCP Server: http://localhost:5000/mcp
- Web UI: http://localhost:8080
- Nginx Proxy: http://localhost:80, https://localhost:443

First Steps
-----------

1. Login to Web UI
^^^^^^^^^^^^^^^^^^

Navigate to http://localhost:8080 and login with:

- Username: ``admin``
- Password: ``password`` (you will be forced to change this)

2. Create Backend Server
^^^^^^^^^^^^^^^^^^^^^^^^^

Navigate to "Backend Servers" and create a new backend:

- Name: my-app
- Host/IP: 192.168.1.100
- Port: 8080
- Protocol: http

3. Create Proxy Rule
^^^^^^^^^^^^^^^^^^^^^

Navigate to "Proxy Rules" and create a new rule:

- Domain: app.example.com
- Backend: my-app
- Path Pattern: /
- SSL Enabled: Yes

4. Upload SSL Certificate (Optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Navigate to "SSL Certificates" and upload:

- Name: Example SSL
- Domain: \*.example.com
- Certificate file: cert.pem
- Key file: key.pem

5. Reload Nginx
^^^^^^^^^^^^^^^

Click "Reload Nginx" to apply changes.

Testing
-------

Run all tests::

    uv run pytest

Run with coverage::

    uv run pytest --cov=src --cov-report=html

Code Quality
------------

Format code::

    uv run black src tests

Lint code::

    uv run ruff check src tests

Type check::

    uv run mypy src

Next Steps
----------

- Read :doc:`architecture` to understand system design
- See :doc:`api-reference` for complete API documentation
- Check :doc:`mcp-reference` for MCP server integration
