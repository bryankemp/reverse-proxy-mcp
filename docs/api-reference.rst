API Reference
=============

Authentication
--------------

All API endpoints (except ``/monitoring/health``) require authentication via JWT bearer token.

Login
^^^^^

``POST /api/v1/auth/login``

Request Body::

    {
      "username": "admin",
      "password": "password"
    }

Response::

    {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "token_type": "bearer",
      "expires_in": 86400,
      "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@nginx-manager.local",
        "role": "admin",
        "is_active": true,
        "must_change_password": false
      },
      "requires_password_change": false
    }

Logout
^^^^^^

``POST /api/v1/auth/logout``

Headers::

    Authorization: Bearer <token>

Change Password
^^^^^^^^^^^^^^^

``POST /api/v1/auth/change-password``

Headers::

    Authorization: Bearer <token>

Request Body::

    {
      "old_password": "current_password",  // Optional if must_change_password=true
      "new_password": "new_secure_password"
    }

Backend Servers
---------------

List Backends
^^^^^^^^^^^^^

``GET /api/v1/backends``

Query Parameters:
  - ``limit``: Maximum results (default: 50)
  - ``offset``: Pagination offset (default: 0)

Response::

    [
      {
        "id": 1,
        "name": "app-server",
        "ip": "192.168.1.100",
        "port": 8080,
        "protocol": "http",
        "service_description": "Main application server",
        "is_active": true,
        "created_by": 1,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ]

Get Backend
^^^^^^^^^^^

``GET /api/v1/backends/{id}``

Create Backend
^^^^^^^^^^^^^^

``POST /api/v1/backends`` (Admin only)

Request Body::

    {
      "name": "app-server",
      "ip": "192.168.1.100",
      "port": 8080,
      "protocol": "http",
      "service_description": "Main application server"
    }

Update Backend
^^^^^^^^^^^^^^

``PUT /api/v1/backends/{id}`` (Admin only)

Request Body (all fields optional)::

    {
      "name": "updated-name",
      "ip": "192.168.1.101",
      "port": 9090,
      "protocol": "https",
      "is_active": false
    }

Delete Backend
^^^^^^^^^^^^^^

``DELETE /api/v1/backends/{id}`` (Admin only)

Proxy Rules
-----------

List Rules
^^^^^^^^^^

``GET /api/v1/proxy-rules``

Query Parameters:
  - ``limit``: Maximum results (default: 50)
  - ``offset``: Pagination offset (default: 0)

Create Rule
^^^^^^^^^^^

``POST /api/v1/proxy-rules`` (Admin only)

Request Body::

    {
      "frontend_domain": "api.example.com",
      "backend_id": 1,
      "certificate_id": null,
      "access_control": "public",
      "enable_hsts": true,
      "force_https": true,
      "ssl_enabled": true,
      "rate_limit": "100r/s",
      "ip_whitelist": "[\"192.168.1.0/24\"]"
    }

Update Rule
^^^^^^^^^^^

``PUT /api/v1/proxy-rules/{id}`` (Admin only)

Delete Rule
^^^^^^^^^^^

``DELETE /api/v1/proxy-rules/{id}`` (Admin only)

SSL Certificates
----------------

List Certificates
^^^^^^^^^^^^^^^^^

``GET /api/v1/certificates``

Get Certificate Dropdown
^^^^^^^^^^^^^^^^^^^^^^^^^

``GET /api/v1/certificates/dropdown``

Returns simplified list for UI dropdowns.

Upload Certificate
^^^^^^^^^^^^^^^^^^

``POST /api/v1/certificates`` (Admin only)

Multipart form with:
  - ``name``: Certificate name
  - ``domain``: Domain pattern (e.g., ``*.example.com``)
  - ``is_default``: Boolean (default: false)
  - ``cert_file``: PEM certificate file
  - ``key_file``: PEM private key file

Set Default Certificate
^^^^^^^^^^^^^^^^^^^^^^^

``PUT /api/v1/certificates/{id}/set-default`` (Admin only)

Delete Certificate
^^^^^^^^^^^^^^^^^^

``DELETE /api/v1/certificates/{id}`` (Admin only)

Check Expiry Status
^^^^^^^^^^^^^^^^^^^

``GET /api/v1/certificates/{domain}/expiry-status``

List Expiring Certificates
^^^^^^^^^^^^^^^^^^^^^^^^^^^

``GET /api/v1/certificates/expiring/list``

Query Parameters:
  - ``days``: Days threshold (default: 30)

User Management
---------------

List Users
^^^^^^^^^^

``GET /api/v1/users`` (Admin only)

Get User
^^^^^^^^

``GET /api/v1/users/{id}`` (Admin only)

Create User
^^^^^^^^^^^

``POST /api/v1/users`` (Admin only)

Request Body::

    {
      "username": "newuser",
      "email": "user@example.com",
      "password": "secure_password",
      "role": "user",
      "full_name": "New User"
    }

Update User
^^^^^^^^^^^

``PUT /api/v1/users/{id}`` (Admin only)

Request Body (all fields optional)::

    {
      "email": "updated@example.com",
      "role": "admin",
      "is_active": false
    }

Delete User
^^^^^^^^^^^

``DELETE /api/v1/users/{id}`` (Admin only)

Configuration
-------------

Get All Config
^^^^^^^^^^^^^^

``GET /api/v1/config`` (Admin only)

Set Config Value
^^^^^^^^^^^^^^^^

``PUT /api/v1/config/{key}`` (Admin only)

Query Parameters:
  - ``value``: Configuration value

Get Nginx Config
^^^^^^^^^^^^^^^^

``GET /api/v1/config/nginx`` (Admin only)

Returns current generated nginx configuration.

Reload Nginx
^^^^^^^^^^^^

``POST /api/v1/config/reload`` (Admin only)

Regenerates configuration from database and reloads Nginx.

Audit Logs
----------

List All Logs
^^^^^^^^^^^^^

``GET /api/v1/config/logs/all`` (Admin only)

Query Parameters:
  - ``limit``: Maximum results (default: 100)

Cleanup Old Logs
^^^^^^^^^^^^^^^^

``POST /api/v1/config/logs/cleanup`` (Admin only)

Query Parameters:
  - ``days_retention``: Days to keep (default: 90)

Monitoring
----------

Health Check
^^^^^^^^^^^^

``GET /api/v1/monitoring/health``

No authentication required.

Response::

    {
      "status": "healthy",
      "version": "1.0.0",
      "database": "connected",
      "nginx": "active",
      "active_backends": 5,
      "active_rules": 12,
      "timestamp": "2024-01-01T00:00:00Z"
    }

Get Metrics
^^^^^^^^^^^

``GET /api/v1/monitoring/metrics``

Query Parameters:
  - ``backend_id``: Optional backend filter
  - ``hours``: Lookback period (default: 24)
  - ``limit``: Maximum results (default: 100)

Metrics Summary
^^^^^^^^^^^^^^^

``GET /api/v1/monitoring/metrics/summary``

Query Parameters:
  - ``hours``: Lookback period (default: 24)

Response::

    {
      "total_requests": 10000,
      "avg_response_time_ms": 125.5,
      "avg_error_rate": 0.05,
      "status_2xx": 9500,
      "status_3xx": 400,
      "status_4xx": 80,
      "status_5xx": 20,
      "period_hours": 24
    }

Backend Metrics
^^^^^^^^^^^^^^^

``GET /api/v1/monitoring/metrics/backends/{id}``

Query Parameters:
  - ``hours``: Lookback period (default: 24)

Cleanup Metrics
^^^^^^^^^^^^^^^

``POST /api/v1/monitoring/metrics/cleanup`` (User access)

Query Parameters:
  - ``days_retention``: Days to keep (default: 30)

Error Responses
---------------

All endpoints return consistent error format::

    {
      "detail": "Error message describing the issue"
    }

Common HTTP Status Codes:
  - ``200 OK``: Successful request
  - ``201 Created``: Resource created successfully
  - ``204 No Content``: Successful deletion
  - ``400 Bad Request``: Invalid request data
  - ``401 Unauthorized``: Missing or invalid token
  - ``403 Forbidden``: Insufficient permissions
  - ``404 Not Found``: Resource not found
  - ``409 Conflict``: Resource already exists
  - ``500 Internal Server Error``: Server error

Interactive Documentation
--------------------------

Access interactive API documentation at ``http://localhost:8000/docs``

Features:
  - Try API endpoints directly from browser
  - Schema validation
  - Example requests and responses
  - OAuth2 authentication flow
