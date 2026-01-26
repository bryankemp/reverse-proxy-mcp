Reverse Proxy MCP Documentation
================================

Welcome to Reverse Proxy MCP, a containerized Nginx reverse proxy management system with REST API, MCP server, and Flutter WebUI.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started
   architecture
   api-reference
   mcp-reference
   user-guide
   development

Features
--------

- **Dynamic Configuration** - Hot-reload proxy rules without container restart
- **REST API** - Complete proxy management via hierarchical (v1) and matrix (v2) endpoints
- **MCP Integration** - AI/LLM compatibility via Model Context Protocol
- **Flutter WebUI** - Responsive management interface
- **Role-Based Access Control** - Admin and user roles with fine-grained permissions
- **Monitoring** - Real-time metrics and historical analytics
- **Audit Logging** - Complete change history and compliance tracking
- **SSL Management** - Wildcard certificates, default certificates, and expiry monitoring
- **Docker Ready** - Multi-container orchestration with docker-compose

Quick Start
-----------

Using Docker Compose:

.. code-block:: bash

   # Clone and start
   git clone https://github.com/bryankemp/reverse-proxy-mcp.git
   cd reverse-proxy-mcp
   cp .env.example .env
   docker compose up -d

   # Access WebUI at http://localhost
   # Login: admin / password

Architecture Overview
---------------------

.. code-block:: text

   ┌─────────────────────────────────────────────────────┐
   │                 Nginx Proxy (80/443)                │
   └─────────────────────────────────────────────────────┘
            ↑              ↑              ↑
      ┌─────────┐    ┌─────────┐   ┌──────────┐
      │   API   │    │   MCP   │   │  WebUI   │
      │ (8000)  │    │ (8000)  │   │  (80)    │
      └─────────┘    └─────────┘   └──────────┘
            ↓              ↓              ↓
   ┌─────────────────────────────────────────────────────┐
   │              SQLite Database                        │
   │   (users, backends, rules, certificates, logs)     │
   └─────────────────────────────────────────────────────┘

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
