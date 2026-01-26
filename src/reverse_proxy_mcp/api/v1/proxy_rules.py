"""Proxy rule endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from reverse_proxy_mcp.api.dependencies import require_admin, require_user
from reverse_proxy_mcp.core import get_db
from reverse_proxy_mcp.core.nginx import NginxConfigGenerator
from reverse_proxy_mcp.models.database import ProxyRule, User
from reverse_proxy_mcp.models.schemas import (
    ProxyRuleCreate,
    ProxyRuleResponse,
    ProxyRuleUpdate,
)

router = APIRouter(prefix="/proxy-rules", tags=["proxy-rules"])


@router.get("", response_model=list[ProxyRuleResponse])
def list_proxy_rules(
    db: Session = Depends(get_db), current_user: User = Depends(require_user)
) -> list[ProxyRuleResponse]:
    """List all proxy rules (including inactive)."""
    return db.query(ProxyRule).all()


@router.get("/{rule_id}", response_model=ProxyRuleResponse)
def get_proxy_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> ProxyRuleResponse:
    """Get specific proxy rule."""
    rule = db.query(ProxyRule).filter(ProxyRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return rule


@router.post("", response_model=ProxyRuleResponse, status_code=status.HTTP_201_CREATED)
def create_proxy_rule(
    rule: ProxyRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ProxyRuleResponse:
    """Create new proxy rule (admin only)."""
    # Check if active rule with same domain exists
    existing = (
        db.query(ProxyRule)
        .filter(ProxyRule.frontend_domain == rule.frontend_domain, ProxyRule.is_active)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Domain already has a rule"
        )

    db_rule = ProxyRule(
        frontend_domain=rule.frontend_domain,
        backend_id=rule.backend_id,
        access_control=rule.access_control,
        ip_whitelist=rule.ip_whitelist,
        # Security settings
        enable_hsts=rule.enable_hsts,
        hsts_max_age=rule.hsts_max_age,
        enable_security_headers=rule.enable_security_headers,
        custom_headers=rule.custom_headers,
        rate_limit=rule.rate_limit,
        ssl_enabled=rule.ssl_enabled,
        force_https=rule.force_https,
        created_by=current_user.id,
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)

    # Auto-reload Nginx after rule creation
    try:
        generator = NginxConfigGenerator()
        success, message = generator.apply_config(db)
        if not success:
            import logging

            logging.error(f"Nginx reload failed: {message}")
    except Exception as e:
        import logging

        logging.error(f"Nginx reload exception: {e}")

    return db_rule


@router.put("/{rule_id}", response_model=ProxyRuleResponse)
def update_proxy_rule(
    rule_id: int,
    rule_update: ProxyRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ProxyRuleResponse:
    """Update proxy rule (admin only)."""
    db_rule = db.query(ProxyRule).filter(ProxyRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    # Check if new domain conflicts with active rules
    if rule_update.frontend_domain and rule_update.frontend_domain != db_rule.frontend_domain:
        existing = (
            db.query(ProxyRule)
            .filter(
                ProxyRule.frontend_domain == rule_update.frontend_domain,
                ProxyRule.is_active,
                ProxyRule.id != rule_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Domain already has a rule"
            )

    if rule_update.frontend_domain:
        db_rule.frontend_domain = rule_update.frontend_domain
    if rule_update.backend_id:
        db_rule.backend_id = rule_update.backend_id
    if rule_update.access_control:
        db_rule.access_control = rule_update.access_control
    if rule_update.ip_whitelist is not None:
        db_rule.ip_whitelist = rule_update.ip_whitelist
    if rule_update.is_active is not None:
        db_rule.is_active = rule_update.is_active

    # Security settings
    if rule_update.enable_hsts is not None:
        db_rule.enable_hsts = rule_update.enable_hsts
    if rule_update.hsts_max_age is not None:
        db_rule.hsts_max_age = rule_update.hsts_max_age
    if rule_update.enable_security_headers is not None:
        db_rule.enable_security_headers = rule_update.enable_security_headers
    if rule_update.custom_headers is not None:
        db_rule.custom_headers = rule_update.custom_headers
    if rule_update.rate_limit is not None:
        db_rule.rate_limit = rule_update.rate_limit
    if rule_update.ssl_enabled is not None:
        db_rule.ssl_enabled = rule_update.ssl_enabled
    if rule_update.force_https is not None:
        db_rule.force_https = rule_update.force_https

    db.commit()
    db.refresh(db_rule)

    # Auto-reload Nginx after rule update
    try:
        generator = NginxConfigGenerator()
        success, message = generator.apply_config(db)
        if not success:
            import logging

            logging.error(f"Nginx reload failed: {message}")
    except Exception as e:
        import logging

        logging.error(f"Nginx reload exception: {e}")

    return db_rule


@router.post("/{rule_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_proxy_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Deactivate proxy rule (marks as inactive, admin only)."""
    db_rule = db.query(ProxyRule).filter(ProxyRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    # Soft delete - mark as inactive
    db_rule.is_active = False
    db.commit()

    # Auto-reload Nginx after rule deletion
    try:
        generator = NginxConfigGenerator()
        success, message = generator.apply_config(db)
        if not success:
            import logging

            logging.error(f"Nginx reload failed: {message}")
    except Exception as e:
        import logging

        logging.error(f"Nginx reload exception: {e}")


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proxy_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Permanently delete proxy rule (hard delete, admin only)."""
    db_rule = db.query(ProxyRule).filter(ProxyRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    # Hard delete from database
    db.delete(db_rule)
    db.commit()

    # Auto-reload Nginx after permanent deletion
    try:
        generator = NginxConfigGenerator()
        success, message = generator.apply_config(db)
        if not success:
            import logging

            logging.error(f"Nginx reload failed: {message}")
    except Exception as e:
        import logging

        logging.error(f"Nginx reload exception: {e}")


@router.post("/reload")
def reload_nginx(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> dict:
    """Hot reload Nginx configuration (admin only)."""
    try:
        generator = NginxConfigGenerator()
        success, message = generator.apply_config(db)

        if success:
            return {"status": "success", "message": message}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message,
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reload error: {str(e)}",
        ) from e
