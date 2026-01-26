User Guide
==========

Overview
--------

Reverse Proxy MCP provides three interfaces for managing your Nginx reverse proxy:

1. **Flutter WebUI** - Graphical interface at http://localhost:8080
2. **REST API** - Programmatic access at http://localhost:8000
3. **MCP Server** - AI/LLM integration at http://localhost:5000/mcp

This guide covers common workflows using the WebUI and REST API.

Getting Started
---------------

First Login
^^^^^^^^^^^

1. Navigate to http://localhost:8080
2. Enter default credentials:
   - Username: ``admin``
   - Password: ``admin``
3. You will be prompted to change your password immediately
4. Enter a secure new password

Initial Configuration
^^^^^^^^^^^^^^^^^^^^^

After logging in, you'll see the Dashboard with:

- Active backends count
- Active proxy rules count
- SSL certificates count
- Recent metrics summary

Backend Server Management
--------------------------

Adding a Backend Server
^^^^^^^^^^^^^^^^^^^^^^^

A backend server is a service that Nginx will proxy requests to.

**Via WebUI:**

1. Navigate to **Backends** from the sidebar
2. Click **Add Backend** button
3. Fill in the form:
   - Name: Unique identifier (e.g., ``app-server-1``)
   - IP Address: Server IP (e.g., ``192.168.1.100``)
   - Port: Service port (e.g., ``8080``)
   - Protocol: ``http`` or ``https``
   - Description: Optional notes
4. Click **Create**

**Via REST API:**

.. code-block:: bash

    curl -X POST http://localhost:8000/api/v1/backends \
      -H "Authorization: Bearer <your_token>" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "app-server-1",
        "ip": "192.168.1.100",
        "port": 8080,
        "protocol": "http",
        "service_description": "Main application server"
      }'

Editing a Backend
^^^^^^^^^^^^^^^^^

**Via WebUI:**

1. Go to **Backends** screen
2. Click the **Edit** icon for the backend
3. Update fields as needed
4. Click **Save**

**Via REST API:**

.. code-block:: bash

    curl -X PUT http://localhost:8000/api/v1/backends/1 \
      -H "Authorization: Bearer <your_token>" \
      -H "Content-Type: application/json" \
      -d '{
        "port": 9090,
        "is_active": false
      }'

Deleting a Backend
^^^^^^^^^^^^^^^^^^

**Warning:** Cannot delete a backend that is referenced by active proxy rules.

**Via WebUI:**

1. Navigate to **Backends**
2. Click the **Delete** icon
3. Confirm deletion

**Via REST API:**

.. code-block:: bash

    curl -X DELETE http://localhost:8000/api/v1/backends/1 \
      -H "Authorization: Bearer <your_token>"

Proxy Rule Management
---------------------

Creating a Proxy Rule
^^^^^^^^^^^^^^^^^^^^^

A proxy rule maps a frontend domain to a backend server.

**Via WebUI:**

1. Navigate to **Proxy Rules**
2. Click **Add Rule** button
3. Fill in the form:
   - Domain: Frontend domain (e.g., ``api.example.com``)
   - Backend: Select from dropdown
   - Certificate: Optional SSL certificate
   - Access Control: ``public``, ``private``, or ``whitelist``
   - Enable HSTS: Recommended for production
   - Force HTTPS: Redirect HTTP to HTTPS
   - SSL Enabled: Enable SSL/TLS
   - Rate Limit: e.g., ``100r/s`` (requests per second)
   - IP Whitelist: JSON array (e.g., ``["192.168.1.0/24"]``)
4. Click **Create**

**Via REST API:**

.. code-block:: bash

    curl -X POST http://localhost:8000/api/v1/proxy-rules \
      -H "Authorization: Bearer <your_token>" \
      -H "Content-Type: application/json" \
      -d '{
        "frontend_domain": "api.example.com",
        "backend_id": 1,
        "access_control": "public",
        "ssl_enabled": true,
        "force_https": true
      }'

Updating a Proxy Rule
^^^^^^^^^^^^^^^^^^^^^

**Via WebUI:**

1. Go to **Proxy Rules**
2. Click **Edit** for the rule
3. Modify fields
4. Click **Save**

Deleting a Proxy Rule
^^^^^^^^^^^^^^^^^^^^^

**Via WebUI:**

1. Navigate to **Proxy Rules**
2. Click **Delete** icon
3. Confirm deletion

SSL Certificate Management
--------------------------

Uploading a Certificate
^^^^^^^^^^^^^^^^^^^^^^^

**Via WebUI:**

1. Navigate to **SSL Certificates**
2. Click **Upload Certificate**
3. Fill in the form:
   - Name: Certificate identifier
   - Domain: Domain pattern (e.g., ``*.example.com`` for wildcard)
   - Certificate File: Select PEM file
   - Key File: Select PEM private key file
   - Set as Default: Check if this should be the default certificate
4. Click **Upload**

**Via REST API:**

.. code-block:: bash

    curl -X POST http://localhost:8000/api/v1/certificates \
      -H "Authorization: Bearer <your_token>" \
      -F "name=example-cert" \
      -F "domain=*.example.com" \
      -F "is_default=false" \
      -F "cert_file=@/path/to/cert.pem" \
      -F "key_file=@/path/to/key.pem"

Setting Default Certificate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The default certificate is used for domains without a specific certificate assigned.

**Via WebUI:**

1. Go to **SSL Certificates**
2. Click the three-dot menu for the certificate
3. Select **Set as Default**

**Via REST API:**

.. code-block:: bash

    curl -X PUT http://localhost:8000/api/v1/certificates/1/set-default \
      -H "Authorization: Bearer <your_token>"

Monitoring Expiring Certificates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Via WebUI:**

The Certificates screen shows expiry status with visual indicators:
  - Green: More than 30 days until expiry
  - Yellow: 7-30 days until expiry
  - Red: Less than 7 days until expiry

**Via REST API:**

.. code-block:: bash

    # List certificates expiring in next 30 days
    curl -X GET "http://localhost:8000/api/v1/certificates/expiring/list?days=30" \
      -H "Authorization: Bearer <your_token>"

User Management
---------------

Creating Users (Admin Only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Via WebUI:**

1. Navigate to **Users**
2. Click **Add User**
3. Fill in the form:
   - Username: Unique login name
   - Email: User email address
   - Password: Initial password (user will be forced to change it)
   - Full Name: Display name
   - Role: ``admin`` or ``user``
4. Click **Create**

**Via REST API:**

.. code-block:: bash

    curl -X POST http://localhost:8000/api/v1/users \
      -H "Authorization: Bearer <your_token>" \
      -H "Content-Type: application/json" \
      -d '{
        "username": "newuser",
        "email": "user@example.com",
        "password": "temp_password",
        "role": "user",
        "full_name": "John Doe"
      }'

**Note:** New users are automatically flagged with ``must_change_password=true`` and will be forced to change their password on first login.

Changing User Role (Admin Only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Via WebUI:**

1. Go to **Users** screen
2. Click **Edit** for the user
3. Change **Role** dropdown to ``admin`` or ``user``
4. Click **Save**

**Important:** You cannot change your own role to prevent accidental lockout.

Deactivating Users (Admin Only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Via WebUI:**

1. Go to **Users** screen
2. Click **Edit** for the user
3. Uncheck **Active** toggle
4. Click **Save**

Deactivated users cannot log in but their data is preserved.

Changing Your Password
^^^^^^^^^^^^^^^^^^^^^^^

**Via WebUI:**

1. Click your username in the top-right
2. Select **Change Password**
3. Enter old password and new password
4. Click **Change**

**Via REST API:**

.. code-block:: bash

    curl -X POST http://localhost:8000/api/v1/auth/change-password \
      -H "Authorization: Bearer <your_token>" \
      -H "Content-Type: application/json" \
      -d '{
        "old_password": "current_password",
        "new_password": "new_secure_password"
      }'

Configuration Management
------------------------

Viewing Configuration
^^^^^^^^^^^^^^^^^^^^^

**Via WebUI:**

1. Navigate to **Configuration**
2. View all global settings

**Via REST API:**

.. code-block:: bash

    curl -X GET http://localhost:8000/api/v1/config \
      -H "Authorization: Bearer <your_token>"

Updating Configuration
^^^^^^^^^^^^^^^^^^^^^^

**Via REST API:**

.. code-block:: bash

    curl -X PUT "http://localhost:8000/api/v1/config/max_connections?value=1024" \
      -H "Authorization: Bearer <your_token>"

Reloading Nginx Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After making changes to backends, proxy rules, or certificates, reload Nginx:

**Via WebUI:**

1. Navigate to **Configuration**
2. Click **Reload Nginx** button
3. Verify reload was successful

**Via REST API:**

.. code-block:: bash

    curl -X POST http://localhost:8000/api/v1/config/reload \
      -H "Authorization: Bearer <your_token>"

**Note:** Configuration is automatically validated before reload. Invalid configurations will not be applied, and the previous working configuration will remain active.

Monitoring & Metrics
--------------------

Viewing Dashboard
^^^^^^^^^^^^^^^^^

The dashboard shows:
  - System health status
  - Active resources count
  - Recent request metrics
  - Error rates by status code
  - Top backends by request volume

Metrics Summary
^^^^^^^^^^^^^^^

**Via REST API:**

.. code-block:: bash

    # Get last 24 hours
    curl -X GET http://localhost:8000/api/v1/monitoring/metrics/summary \
      -H "Authorization: Bearer <your_token>"
    
    # Get last 7 days
    curl -X GET "http://localhost:8000/api/v1/monitoring/metrics/summary?hours=168" \
      -H "Authorization: Bearer <your_token>"

Backend-Specific Metrics
^^^^^^^^^^^^^^^^^^^^^^^^^

**Via REST API:**

.. code-block:: bash

    curl -X GET http://localhost:8000/api/v1/monitoring/metrics/backends/1 \
      -H "Authorization: Bearer <your_token>"

Audit Logs
----------

Viewing Audit Logs (Admin Only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Audit logs track all configuration changes made by admins.

**Via WebUI:**

1. Navigate to **Audit Logs** (admin only)
2. View logs with:
   - Action performed (create, update, delete)
   - Resource type (backend, proxy_rule, certificate, user)
   - User who made the change
   - Timestamp
   - Before/after values

**Via REST API:**

.. code-block:: bash

    # Get last 100 logs
    curl -X GET http://localhost:8000/api/v1/config/logs/all \
      -H "Authorization: Bearer <your_token>"

Cleaning Up Old Logs
^^^^^^^^^^^^^^^^^^^^^

**Via REST API:**

.. code-block:: bash

    # Keep only last 90 days
    curl -X POST "http://localhost:8000/api/v1/config/logs/cleanup?days_retention=90" \
      -H "Authorization: Bearer <your_token>"

Common Workflows
----------------

Setting Up a New Domain
^^^^^^^^^^^^^^^^^^^^^^^

1. **Create Backend Server** (if not exists)
   - Name: ``api-backend``
   - IP: ``192.168.1.100``
   - Port: ``3000``

2. **Upload SSL Certificate** (optional but recommended)
   - Generate certificate (see SSL Setup below)
   - Upload via Certificates screen

3. **Create Proxy Rule**
   - Domain: ``api.example.com``
   - Backend: Select ``api-backend``
   - Certificate: Select uploaded certificate
   - Enable SSL, Force HTTPS, Enable HSTS

4. **Reload Nginx**
   - Click **Reload Nginx** in Configuration screen
   - Verify success message

5. **Test Configuration**

   .. code-block:: bash

       # Test HTTP redirect (should redirect to HTTPS)
       curl -I http://api.example.com
       
       # Test HTTPS (should return 200 or backend response)
       curl -I https://api.example.com

Rotating an SSL Certificate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Upload New Certificate**
   - Use same domain pattern
   - Upload new PEM files

2. **Update Proxy Rules**
   - Edit rules using old certificate
   - Select new certificate

3. **Reload Nginx**
   - Click **Reload Nginx**

4. **Delete Old Certificate**
   - Verify no rules are using it
   - Delete from Certificates screen

Setting Up Wildcard Domain
^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Obtain Wildcard Certificate**
   - Use Let's Encrypt DNS challenge
   - Or purchase commercial wildcard certificate
   - Domain: ``*.example.com``

2. **Upload Wildcard Certificate**
   - Name: ``example-wildcard``
   - Domain: ``*.example.com``

3. **Create Backends for Each Subdomain**
   - ``api-backend`` → ``192.168.1.100:3000``
   - ``app-backend`` → ``192.168.1.101:8080``
   - ``admin-backend`` → ``192.168.1.102:4000``

4. **Create Proxy Rules**
   - ``api.example.com`` → ``api-backend`` (use wildcard cert)
   - ``app.example.com`` → ``app-backend`` (use wildcard cert)
   - ``admin.example.com`` → ``admin-backend`` (use wildcard cert)

5. **Reload Nginx**

Troubleshooting
---------------

502 Bad Gateway
^^^^^^^^^^^^^^^

**Cause:** Backend server is unreachable or not responding.

**Steps to diagnose:**

1. Check backend is active:
   - Navigate to Backends
   - Verify ``is_active`` is checked

2. Test backend connectivity:

   .. code-block:: bash

       # Test if backend is reachable
       curl http://<backend_ip>:<backend_port>

3. Check backend server logs for errors

4. Verify Nginx configuration:
   - Navigate to **Configuration** → **View Nginx Config**
   - Check ``upstream`` block for correct IP/port

**Fix:**

- Update backend IP/port if incorrect
- Restart backend service if it's down
- Reload Nginx after making changes

404 Not Found
^^^^^^^^^^^^^

**Cause:** No proxy rule matches the requested domain.

**Steps to diagnose:**

1. Check proxy rules:
   - Navigate to **Proxy Rules**
   - Search for the domain

2. Verify domain matches exactly (case-sensitive)

3. Check DNS resolution:

   .. code-block:: bash

       # Verify DNS points to proxy server
       dig api.example.com

**Fix:**

- Create proxy rule for the domain
- Update DNS if pointing to wrong IP
- Reload Nginx

SSL Certificate Errors
^^^^^^^^^^^^^^^^^^^^^^^

**Cause:** Certificate expired, mismatched domain, or not trusted.

**Steps to diagnose:**

1. Check certificate expiry:
   - Navigate to **SSL Certificates**
   - Look for red/yellow expiry indicators

2. Test SSL connection:

   .. code-block:: bash

       # Check certificate details
       openssl s_client -connect api.example.com:443 -servername api.example.com

3. Verify domain matches certificate:
   - Certificate domain must match frontend domain
   - Wildcard certificates match ``*.example.com`` pattern

**Fix:**

- Upload new certificate if expired
- Update proxy rule to use correct certificate
- Reload Nginx

Connection Timeout
^^^^^^^^^^^^^^^^^^

**Cause:** Backend server is slow or unresponsive.

**Steps to diagnose:**

1. Check backend response time:

   .. code-block:: bash

       # Measure backend response time
       time curl http://<backend_ip>:<backend_port>

2. Review metrics for backend:
   - Navigate to **Monitoring**
   - Check avg response time for the backend

3. Check backend server resource usage (CPU, memory)

**Fix:**

- Increase timeout in configuration:

  .. code-block:: bash

      curl -X PUT "http://localhost:8000/api/v1/config/timeout_seconds?value=60" \
        -H "Authorization: Bearer <your_token>"

- Optimize backend performance
- Scale backend horizontally (add more backend servers)
- Reload Nginx after config change

Unauthorized (403) Errors
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause:** User role does not permit the action.

**Scenarios:**

- Regular users cannot create/edit/delete resources
- Regular users cannot access admin screens (users, config, audit logs)
- Users cannot modify their own role

**Fix:**

- Contact admin to grant admin role if needed
- Use read-only views available to regular users

Database Locked Errors
^^^^^^^^^^^^^^^^^^^^^^^

**Cause:** SQLite database is locked due to concurrent writes.

**Fix:**

- Wait a few seconds and retry
- If persistent, restart the API server:

  .. code-block:: bash

      docker-compose restart api

Role-Based Access
-----------------

Admin Role
^^^^^^^^^^

**Permissions:**
  - Full CRUD on all resources
  - Access to all WebUI screens
  - Can view audit logs
  - Can reload Nginx
  - Can manage users (except cannot change own role)

**Screens visible:**
  - Dashboard
  - Backends (read/write)
  - Proxy Rules (read/write)
  - SSL Certificates (read/write)
  - Users (admin only)
  - Configuration (admin only)
  - Audit Logs (admin only)
  - Monitoring

User Role
^^^^^^^^^

**Permissions:**
  - Read-only access to dashboards and metrics
  - Cannot create, edit, or delete resources
  - Cannot access admin screens
  - Can change own password
  - Can view certificate listings (read-only)

**Screens visible:**
  - Dashboard (read-only)
  - Backends (read-only, no edit/delete buttons)
  - Proxy Rules (read-only)
  - SSL Certificates (read-only)
  - Monitoring

**Screens hidden:**
  - Users
  - Configuration
  - Audit Logs

Best Practices
--------------

Security
^^^^^^^^

1. **Change default admin password immediately** on first login
2. **Use strong passwords**: 12+ characters, mix of upper/lower/numbers/symbols
3. **Enable HTTPS** for all production domains (set ``force_https=true``)
4. **Enable HSTS** for production (set ``enable_hsts=true``)
5. **Use wildcard certificates** for multiple subdomains under one domain
6. **Rotate certificates** before expiry (monitor expiring certificates)
7. **Use IP whitelisting** for admin or sensitive domains
8. **Review audit logs** regularly for unauthorized changes

Configuration
^^^^^^^^^^^^^

1. **Test backend connectivity** before creating proxy rules
2. **Always reload Nginx** after making changes
3. **Monitor metrics** to detect performance issues early
4. **Set rate limits** to prevent abuse (e.g., ``100r/s``)
5. **Use descriptive names** for backends and certificates
6. **Deactivate unused backends** instead of deleting them
7. **Backup database regularly** (copy ``./data/reverse_proxy_mcp.db``)

Operations
^^^^^^^^^^

1. **Check health endpoint** to verify system is operational:

   .. code-block:: bash

       curl http://localhost:8000/api/v1/monitoring/health

2. **Monitor metrics** to track request volume and error rates
3. **Clean up old metrics** to reduce database size:

   .. code-block:: bash

       # Keep last 30 days
       curl -X POST "http://localhost:8000/api/v1/monitoring/metrics/cleanup?days_retention=30" \
         -H "Authorization: Bearer <your_token>"

4. **Clean up audit logs** periodically (e.g., keep 90 days):

   .. code-block:: bash

       curl -X POST "http://localhost:8000/api/v1/config/logs/cleanup?days_retention=90" \
         -H "Authorization: Bearer <your_token>"

SSL Certificate Setup
---------------------

Let's Encrypt (Recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Using certbot:**

.. code-block:: bash

    # Install certbot
    sudo apt-get install certbot
    
    # Generate certificate (HTTP-01 challenge)
    sudo certbot certonly --standalone -d api.example.com
    
    # Certificate files will be in:
    # /etc/letsencrypt/live/api.example.com/fullchain.pem
    # /etc/letsencrypt/live/api.example.com/privkey.pem
    
    # Upload to Reverse Proxy MCP via WebUI or API

**Wildcard certificates (DNS-01 challenge):**

.. code-block:: bash

    # Requires DNS plugin (e.g., Cloudflare)
    sudo certbot certonly \
      --dns-cloudflare \
      --dns-cloudflare-credentials ~/.secrets/cloudflare.ini \
      -d "*.example.com"

Self-Signed Certificate (Testing Only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**For development/testing:**

.. code-block:: bash

    # Generate self-signed certificate
    openssl req -x509 -newkey rsa:4096 -nodes \
      -keyout key.pem \
      -out cert.pem \
      -days 365 \
      -subj "/CN=*.example.com"
    
    # Upload via WebUI or API

**Warning:** Self-signed certificates will trigger browser warnings. Only use for testing.

Commercial Certificate
^^^^^^^^^^^^^^^^^^^^^^

1. Purchase certificate from provider (DigiCert, GlobalSign, etc.)
2. Download PEM files (certificate and private key)
3. Upload via WebUI or API

Advanced Features
-----------------

Rate Limiting
^^^^^^^^^^^^^

Set per-rule rate limits to prevent abuse:

- ``10r/s`` - 10 requests per second
- ``100r/m`` - 100 requests per minute
- ``1000r/h`` - 1000 requests per hour

IP Whitelisting
^^^^^^^^^^^^^^^

Restrict access to specific IP ranges:

.. code-block:: json

    ["192.168.1.0/24", "10.0.0.0/8"]

Only clients from these ranges can access the domain.

Access Control Levels
^^^^^^^^^^^^^^^^^^^^^

- ``public`` - No restrictions
- ``private`` - Requires authentication (future implementation)
- ``whitelist`` - IP-based restriction

HSTS Configuration
^^^^^^^^^^^^^^^^^^

HTTP Strict Transport Security tells browsers to always use HTTPS.

**Best practice:**
  - Enable for production domains
  - Set ``max-age=31536000`` (1 year)
  - Include subdomains with ``includeSubDomains`` directive

Backup & Restore
----------------

Database Backup
^^^^^^^^^^^^^^^

.. code-block:: bash

    # Stop containers
    docker-compose down
    
    # Backup database
    cp ./data/reverse_proxy_mcp.db ./backups/reverse_proxy_mcp_$(date +%Y%m%d).db
    
    # Restart
    docker-compose up -d

Database Restore
^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Stop containers
    docker-compose down
    
    # Restore from backup
    cp ./backups/reverse_proxy_mcp_20240101.db ./data/reverse_proxy_mcp.db
    
    # Restart
    docker-compose up -d

MCP Integration (AI/LLM)
------------------------

The MCP server provides 22 tools for AI assistants to manage the reverse proxy.

Example MCP Tool Usage
^^^^^^^^^^^^^^^^^^^^^^

**Using Claude Desktop or other MCP clients:**

1. Configure MCP client to connect to ``http://localhost:5000/mcp``
2. Use natural language to manage proxy:
   - "Create a backend server for my app on 192.168.1.100:8080"
   - "Set up SSL for api.example.com using the wildcard certificate"
   - "Show me metrics for the last 24 hours"

Available MCP Prompts
^^^^^^^^^^^^^^^^^^^^^

- ``setup_new_domain`` - Complete workflow for adding new domain
- ``troubleshoot_proxy`` - Diagnose proxy issues for a domain
- ``configure_ssl`` - SSL certificate setup guidance
- ``rotate_certificate`` - Zero-downtime certificate rotation
- ``create_user_account`` - Secure user creation workflow

See ``docs/mcp-reference.rst`` for complete MCP documentation.
