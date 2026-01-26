"""MCP prompts for common proxy management workflows.

Prompts provide guided workflows for complex multi-step operations.
Each prompt accepts arguments and returns contextual instructions.
"""

import logging

from mcp.server.fastmcp import FastMCP

from reverse_proxy_mcp.mcp.client import get_client

logger = logging.getLogger(__name__)

# FastMCP instance will be imported from server.py
mcp: FastMCP = None  # type: ignore


def register_prompts(mcp_instance: FastMCP) -> None:
    """Register all MCP prompts with the FastMCP server instance.

    Args:
        mcp_instance: The FastMCP server instance to register prompts with
    """
    global mcp
    mcp = mcp_instance

    @mcp.prompt()
    def setup_new_domain(domain: str, backend_host: str, backend_port: int) -> str:
        """Guide user through creating backend + rule + certificate for a new domain.

        Args:
            domain: The domain name to configure (e.g., api.example.com)
            backend_host: Backend server hostname or IP address
            backend_port: Backend server port number

        Returns:
            Step-by-step instructions with tool calls
        """
        # Check if backend already exists
        try:
            client = get_client()
            backends = client.get("/backends", params={"limit": 1000})
            existing = [
                b
                for b in backends
                if b.get("host") == backend_host and b.get("port") == backend_port
            ]
        except Exception:
            existing = []

        prompt = f"""# Setting Up New Domain: {domain}

## Overview
You are configuring a new reverse proxy rule for domain '{domain}' pointing to backend {backend_host}:{backend_port}.

## Steps

### 1. Create or Verify Backend Server
"""
        if existing:
            backend_id = existing[0]["id"]
            backend_name = existing[0]["name"]
            prompt += f"""Backend already exists: '{backend_name}' (ID: {backend_id})
- Host: {backend_host}
- Port: {backend_port}

You can skip to step 2.
"""
        else:
            prompt += f"""Create a new backend server:

Tool: create_backend
Parameters:
- name: "{domain.replace('.', '-')}-backend"
- host: "{backend_host}"
- port: {backend_port}
- protocol: "http" (use "https" if backend requires SSL)
- description: "Backend server for {domain}"

Save the returned backend_id for the next step.
"""

        prompt += f"""
### 2. Create Proxy Rule

Tool: create_proxy_rule
Parameters:
- domain: "{domain}"
- backend_id: <backend_id from step 1>
- path_pattern: "/" (default, or specify custom path)
- certificate_id: null (skip SSL for now, or specify cert ID if available)
- rule_type: "reverse_proxy"

### 3. (Optional) Configure SSL Certificate

If you have an SSL certificate for {domain}:

Tool: create_certificate
Parameters:
- name: "{domain}-ssl"
- domain: "{domain}" (or "*.{domain.split('.')["-2"]}.{domain.split('.')["-1"]}" for wildcard)
- cert_pem: "<certificate PEM content>"
- key_pem: "<private key PEM content>"
- is_default: false
- description: "SSL certificate for {domain}"

Then update the proxy rule:

Tool: update_proxy_rule
Parameters:
- rule_id: <rule_id from step 2>
- certificate_id: <cert_id from create_certificate>

### 4. Reload Nginx Configuration

Tool: reload_nginx

This applies the new configuration without restarting the container.

### 5. Verify Configuration

Check health status:
Tool: get_health

Verify the proxy rule is active:
Tool: get_proxy_rule
Parameters:
- rule_id: <rule_id from step 2>

## Testing

Test the new domain with curl:
```
curl -H "Host: {domain}" http://localhost/
```

Or if SSL is configured:
```
curl -k https://{domain}/
```

## Next Steps

- Monitor metrics for the new domain using get_metrics
- Check audit logs to confirm changes were recorded
- Update DNS records to point {domain} to your reverse proxy IP
"""

        return prompt

    @mcp.prompt()
    def troubleshoot_proxy(domain: str) -> str:
        """Diagnose proxy issues for a specific domain.

        Args:
            domain: The domain experiencing issues

        Returns:
            Diagnostic steps and common fixes
        """
        # Fetch current configuration
        try:
            client = get_client()
            rules = client.get("/proxy-rules", params={"limit": 1000})
            matching_rules = [r for r in rules if r.get("domain") == domain]
            backends = client.get("/backends", params={"limit": 1000})
            health = client.get("/health")
        except Exception as e:
            logger.error(f"Failed to fetch troubleshooting data: {e}")
            matching_rules = []
            backends = []
            health = {}

        prompt = f"""# Troubleshooting Proxy for Domain: {domain}

## Current Configuration

"""
        if matching_rules:
            rule = matching_rules[0]
            backend_id = rule.get("backend_id")
            backend = next((b for b in backends if b["id"] == backend_id), None)

            prompt += f"""### Proxy Rule Found
- Rule ID: {rule.get('id')}
- Domain: {rule.get('domain')}
- Path Pattern: {rule.get('path_pattern')}
- Backend ID: {backend_id}
- Certificate: {rule.get('certificate_name') or 'None (HTTP only)'}
- Active: {rule.get('is_active')}

### Backend Server
"""
            if backend:
                prompt += f"""- Name: {backend.get('name')}
- Host: {backend.get('host')}
- Port: {backend.get('port')}
- Protocol: {backend.get('protocol')}
- Active: {backend.get('is_active')}
"""
            else:
                prompt += f"""⚠️  Backend ID {backend_id} not found - this is likely the issue!
"""
        else:
            prompt += f"""⚠️  No proxy rule found for domain '{domain}'

This is likely the root cause. You need to create a proxy rule first.
"""

        prompt += f"""
## Health Check Status

System Status: {health.get('status', 'unknown')}

## Diagnostic Steps

### 1. Verify Proxy Rule Exists and is Active

Tool: list_proxy_rules

Check if rule for '{domain}' exists and is_active=true.

### 2. Verify Backend Server is Reachable

Tool: get_backend
Parameters:
- backend_id: <backend_id from proxy rule>

Ensure:
- Backend is_active=true
- Host and port are correct
- Protocol matches backend server (http vs https)

### 3. Test Backend Connectivity

From the proxy container, test if backend is reachable:
```
curl -v {backend.get('protocol', 'http')}://{backend.get('host', 'BACKEND_HOST')}:{backend.get('port', 'PORT')}/
```

### 4. Check Nginx Configuration

Tool: get_config

Verify Nginx configuration was generated correctly.

Tool: reload_nginx

Force a reload to ensure latest config is active.

### 5. Review Recent Errors

Tool: get_metrics
Parameters:
- metric_type: "errors"
- limit: 50

Look for error patterns related to '{domain}'.

### 6. Check Audit Logs

Tool: get_audit_logs (admin only)

Review recent changes that might have affected this domain.

## Common Issues and Fixes

### Issue: 502 Bad Gateway
- **Cause**: Backend server is down or unreachable
- **Fix**: Verify backend server is running, check firewall rules

### Issue: 404 Not Found
- **Cause**: No proxy rule matches the domain or path
- **Fix**: Verify domain matches exactly (case-sensitive), check path_pattern

### Issue: SSL/TLS Errors
- **Cause**: Certificate mismatch or expired certificate
- **Fix**: Use list_certificates to find correct cert, update rule with certificate_id

### Issue: Timeout Errors
- **Cause**: Backend server too slow or unresponsive
- **Fix**: Increase timeout_seconds in config, check backend performance

### Issue: Connection Refused
- **Cause**: Backend server port is closed or wrong port number
- **Fix**: Verify backend port with netstat/ss, update backend configuration

## Additional Tools

- get_health: Check overall system health
- get_metrics: View request/response metrics for performance analysis
- get_certificate: Verify SSL certificate details and expiration
"""

        return prompt

    @mcp.prompt()
    def configure_ssl(domain: str, is_wildcard: bool = False) -> str:
        """Guide SSL certificate upload and assignment to domain.

        Args:
            domain: The domain to configure SSL for
            is_wildcard: Whether this is a wildcard certificate (*.example.com)

        Returns:
            Instructions for certificate generation and upload
        """
        cert_domain = f"*.{domain}" if is_wildcard else domain
        cert_name = f"{domain}-wildcard" if is_wildcard else f"{domain}-ssl"

        prompt = f"""# Configuring SSL Certificate for {domain}

## Certificate Type
{f'🌐 Wildcard Certificate (*.{domain})' if is_wildcard else f'🔒 Domain-Specific Certificate ({domain})'}

## Step 1: Generate or Obtain Certificate

### Option A: Let's Encrypt (Recommended for Production)

Install certbot and generate certificate:
```
certbot certonly --standalone -d {cert_domain}
```

Certificate files will be located at:
- Certificate: `/etc/letsencrypt/live/{domain}/fullchain.pem`
- Private Key: `/etc/letsencrypt/live/{domain}/privkey.pem`

### Option B: Self-Signed Certificate (Development Only)

Generate self-signed certificate:
```
openssl req -x509 -newkey rsa:4096 -nodes \\
  -keyout {domain}.key -out {domain}.crt \\
  -days 365 -subj "/CN={cert_domain}"
```

### Option C: Commercial Certificate

Obtain certificate from a certificate authority (DigiCert, Sectigo, etc.) and ensure you have:
- Certificate file (.crt or .pem)
- Private key file (.key or .pem)
- Intermediate certificates (if applicable, concatenate with main cert)

## Step 2: Read Certificate Content

```
cat {domain}.crt  # Copy certificate content
cat {domain}.key  # Copy private key content
```

## Step 3: Upload Certificate via MCP

Tool: create_certificate
Parameters:
- name: "{cert_name}"
- domain: "{cert_domain}"
- cert_pem: "<paste certificate PEM content>"
- key_pem: "<paste private key PEM content>"
- is_default: {"true" if is_wildcard else "false"} {"(wildcard certs often set as default)" if is_wildcard else ""}
- description: "SSL certificate for {domain}"

Save the returned cert_id for the next step.

## Step 4: Assign Certificate to Proxy Rule

First, find the proxy rule for {domain}:

Tool: list_proxy_rules

Look for rule matching domain "{domain}".

Then update the rule:

Tool: update_proxy_rule
Parameters:
- rule_id: <rule_id from list_proxy_rules>
- certificate_id: <cert_id from step 3>

## Step 5: Reload Nginx

Tool: reload_nginx

This applies the SSL configuration.

## Step 6: Verify SSL Configuration

Test SSL endpoint:
```
curl -v https://{domain}/
```

Check certificate details:
```
openssl s_client -connect {domain}:443 -servername {domain} < /dev/null
```

Verify certificate assignment:

Tool: get_proxy_rule
Parameters:
- rule_id: <rule_id from step 4>

Confirm certificate_name field matches "{cert_name}".

## Wildcard Certificate Notes
"""

        if is_wildcard:
            prompt += f"""
A wildcard certificate for *.{domain} will match:
- app.{domain}
- api.{domain}
- www.{domain}
- Any subdomain of {domain}

Setting is_default=true makes this certificate the fallback for any domain without a specific certificate assigned.

You can create multiple proxy rules for different subdomains and they will all use this wildcard certificate automatically.
"""
        else:
            prompt += f"""
This certificate only matches the exact domain: {domain}

If you need to support both {domain} and www.{domain}, you should either:
1. Generate a certificate with Subject Alternative Names (SAN) for both
2. Use a wildcard certificate for *.{domain.split('.', 1)[-1] if '.' in domain else domain}
"""

        prompt += """
## Security Best Practices

1. **Never commit private keys** to version control
2. **Rotate certificates** before expiration (set reminders 30 days before)
3. **Use strong key sizes**: Minimum 2048-bit RSA or 256-bit ECC
4. **Keep private keys secure**: Restrict file permissions (chmod 600)
5. **Enable HSTS headers** for production domains
6. **Monitor certificate expiration** using get_certificate tool

## Certificate Expiration Monitoring

Check certificate expiration dates:

Tool: list_certificates

Review expires_at field for all certificates and plan renewals.
"""

        return prompt

    @mcp.prompt()
    def rotate_certificate(cert_id: int) -> str:
        """Guide user through replacing an expiring certificate.

        Args:
            cert_id: The ID of the certificate to rotate

        Returns:
            Steps to upload new certificate, update rules, and verify
        """
        # Fetch current certificate details
        try:
            client = get_client()
            cert = client.get(f"/certificates/{cert_id}")
            cert_name = cert.get("name", "unknown")
            cert_domain = cert.get("domain", "unknown")
            is_default = cert.get("is_default", False)
        except Exception as e:
            logger.error(f"Failed to fetch certificate {cert_id}: {e}")
            cert_name = "unknown"
            cert_domain = "unknown"
            is_default = False

        prompt = f"""# Rotating SSL Certificate

## Certificate Information
- Certificate ID: {cert_id}
- Name: {cert_name}
- Domain: {cert_domain}
- Default Certificate: {is_default}

## Step 1: Generate New Certificate

Follow the same process used for the original certificate:

### Let's Encrypt (Recommended)
```
certbot certonly --standalone -d {cert_domain} --force-renewal
```

### Self-Signed (Development)
```
openssl req -x509 -newkey rsa:4096 -nodes \\
  -keyout {cert_domain}.key -out {cert_domain}.crt \\
  -days 365 -subj "/CN={cert_domain}"
```

## Step 2: Upload New Certificate

Tool: create_certificate
Parameters:
- name: "{cert_name}-new" (or keep same name with timestamp: "{cert_name}-2026")
- domain: "{cert_domain}"
- cert_pem: "<paste new certificate PEM content>"
- key_pem: "<paste new private key PEM content>"
- is_default: {str(is_default).lower()}
- description: "Rotated certificate for {cert_domain}"

Save the returned new_cert_id.

## Step 3: Update All Proxy Rules Using Old Certificate

First, find all rules using the old certificate:

Tool: list_proxy_rules

Look for rules with certificate_id={cert_id}.

For each rule, update to use new certificate:

Tool: update_proxy_rule
Parameters:
- rule_id: <rule_id from list>
- certificate_id: <new_cert_id from step 2>

## Step 4: Reload Nginx

Tool: reload_nginx

## Step 5: Verify New Certificate is Active

Test SSL connection:
```
curl -v https://{cert_domain}/
openssl s_client -connect {cert_domain}:443 -servername {cert_domain} < /dev/null | grep "Verify return code"
```

Check certificate details:

Tool: get_certificate
Parameters:
- cert_id: <new_cert_id>

## Step 6: Delete Old Certificate

Once verified the new certificate works:

Tool: delete_certificate
Parameters:
- cert_id: {cert_id}

## Certificate Rotation Checklist

- [ ] New certificate generated and tested locally
- [ ] New certificate uploaded via create_certificate
- [ ] All proxy rules updated to reference new certificate
- [ ] Nginx reloaded successfully
- [ ] SSL connection tested and verified
- [ ] Old certificate deleted
- [ ] Calendar reminder set for next rotation (90 days for Let's Encrypt, 1 year for commercial)

## Notes

- Zero-downtime rotation: The old certificate remains active until Nginx reload completes
- If rotation fails, rules still reference old certificate - safe to retry
- Always test new certificate before deleting old one
- Keep audit logs for compliance: All changes are automatically logged
"""

        return prompt

    @mcp.prompt()
    def create_user_account(username: str, role: str = "user") -> str:
        """Guide user through creating a new user account.

        Args:
            username: The username for the new account
            role: The role to assign (admin or user)

        Returns:
            User creation workflow with password handling
        """
        prompt = f"""# Creating New User Account: {username}

## User Role: {role.upper()}

{'⚠️  Admin Role: This user will have full access to all system features.' if role == 'admin' else '👤 User Role: This user will have read-only access to dashboards and metrics.'}

## Step 1: Generate Secure Password

Generate a strong random password:
```
openssl rand -base64 32
```

Or use a password manager to generate a secure password (minimum 12 characters).

## Step 2: Create User Account

Tool: create_user
Parameters:
- username: "{username}"
- password: "<generated password from step 1>"
- role: "{role}"
- full_name: "<optional full name>"

Save the returned user_id.

## Step 3: Verify User Creation

Tool: list_users

Confirm '{username}' appears in the user list with correct role.

## Step 4: (Optional) Test User Login

If testing immediately, you can verify the account works:

1. Save credentials securely in password manager
2. Share username and password with user via secure channel (NOT email or chat)
3. User should log in and change password on first login

## Permission Summary

### Admin Role ({role == 'admin' and '✓ SELECTED' or ''})
- Full CRUD access to backends, proxy rules, certificates
- User management capabilities
- Configuration changes
- Audit log access
- Cannot modify their own role (security protection)

### User Role ({role == 'user' and '✓ SELECTED' or ''})
- Read-only access to dashboards
- View metrics and monitoring data
- View certificate listings (no private keys)
- Cannot create, modify, or delete any resources
- Cannot access user management or audit logs

## Security Best Practices

1. **Password Complexity**: Minimum 12 characters, mixed case, numbers, symbols
2. **Secure Delivery**: Never send passwords via email or unsecured chat
3. **Force Password Change**: Instruct user to change password on first login
4. **Principle of Least Privilege**: Use 'user' role unless admin access required
5. **Regular Audits**: Review user list monthly, deactivate unused accounts

## Account Management

To deactivate user without deleting:
- Update user with is_active=false (feature to be implemented)

To delete user permanently:

Tool: delete_user (to be implemented)
Parameters:
- user_id: <user_id>

## Audit Logging

User creation is automatically logged in audit_logs table:
- Timestamp of creation
- Admin who created the account
- User role assigned
- IP address of admin

Review audit logs:

Tool: get_audit_logs (admin only)
"""

        return prompt

    @mcp.prompt()
    def configure_wildcard_domain(base_domain: str, subdomains: list[str]) -> str:
        """Guide user through setting up wildcard SSL with multiple subdomains.

        Args:
            base_domain: The base domain (e.g., example.com)
            subdomains: List of subdomains to configure (e.g., ["api", "www", "app"])

        Returns:
            Comprehensive setup instructions for wildcard configuration
        """
        subdomain_list = ", ".join(f"{sub}.{base_domain}" for sub in subdomains)

        prompt = f"""# Configuring Wildcard Domain: *.{base_domain}

## Subdomains to Configure
{subdomain_list}

## Overview

A wildcard certificate for *.{base_domain} will secure all subdomains with a single certificate.
You'll create separate proxy rules for each subdomain, all sharing the wildcard certificate.

## Step 1: Upload Wildcard Certificate

Tool: create_certificate
Parameters:
- name: "{base_domain}-wildcard"
- domain: "*.{base_domain}"
- cert_pem: "<wildcard certificate PEM content>"
- key_pem: "<private key PEM content>"
- is_default: true (recommended for wildcard certs)
- description: "Wildcard SSL certificate for *.{base_domain}"

Save the returned cert_id.

## Step 2: Create Backend Servers

For each subdomain, create a backend (or reuse existing):
"""

        for subdomain in subdomains:
            prompt += f"""
### {subdomain}.{base_domain}

Tool: create_backend
Parameters:
- name: "{subdomain}-{base_domain.replace('.', '-')}-backend"
- host: "<backend host for {subdomain}>"
- port: <backend port>
- protocol: "http"
- description: "Backend for {subdomain}.{base_domain}"

Save backend_id_{subdomain}.
"""

        prompt += """
## Step 3: Create Proxy Rules

For each subdomain, create a proxy rule referencing the wildcard certificate:
"""

        for subdomain in subdomains:
            prompt += f"""
### {subdomain}.{base_domain}

Tool: create_proxy_rule
Parameters:
- domain: "{subdomain}.{base_domain}"
- backend_id: <backend_id_{subdomain} from step 2>
- certificate_id: <cert_id from step 1>
- path_pattern: "/"
- rule_type: "reverse_proxy"
"""

        prompt += """
## Step 4: Reload Nginx

Tool: reload_nginx

## Step 5: Verify Configuration

Test each subdomain:
"""

        for subdomain in subdomains:
            prompt += f"""
```
curl -k https://{subdomain}.{base_domain}/
```
"""

        prompt += """
## Step 6: Update DNS Records

Add A or CNAME records for each subdomain pointing to your reverse proxy server:

"""
        for subdomain in subdomains:
            prompt += f"- {subdomain}.{base_domain} → <your-proxy-ip>\n"

        prompt += """
## Benefits of Wildcard Certificates

✅ Single certificate for unlimited subdomains
✅ Simplified certificate management
✅ Lower cost (one cert vs. multiple)
✅ Easy to add new subdomains (just create proxy rule)

## Limitations

⚠️  Does not cover the base domain itself (example.com)
⚠️  Does not cover nested subdomains (api.v2.example.com)
⚠️  If compromised, affects all subdomains

## Monitoring

Set up certificate expiration monitoring:

Tool: list_certificates

Check expires_at field and set reminder for renewal 30 days before expiration.
"""

        return prompt
