"""Proxy rule endpoints."""

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from nginx_manager.api.dependencies import require_admin, require_user
from nginx_manager.core import get_db
from nginx_manager.core.nginx import NginxConfigGenerator
from nginx_manager.models.database import ProxyRule, User
from nginx_manager.models.schemas import (
    ProxyRuleCreate,
    ProxyRuleResponse,
    ProxyRuleUpdate,
)

router = APIRouter(prefix="/proxy-rules", tags=["proxy-rules"])


@router.get("", response_model=List[ProxyRuleResponse])
def list_proxy_rules(
    db: Session = Depends(get_db), current_user: User = Depends(require_user)
) -> List[ProxyRuleResponse]:
    """List all proxy rules."""
    return db.query(ProxyRule).filter(ProxyRule.is_active).all()


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
    # Check if rule with same domain exists
    existing = (
        db.query(ProxyRule).filter(ProxyRule.frontend_domain == rule.frontend_domain).first()
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
        created_by=current_user.id,
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
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

    # Check if new domain conflicts
    if rule_update.frontend_domain and rule_update.frontend_domain != db_rule.frontend_domain:
        existing = (
            db.query(ProxyRule)
            .filter(ProxyRule.frontend_domain == rule_update.frontend_domain)
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

    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proxy_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Delete proxy rule (soft delete, admin only)."""
    db_rule = db.query(ProxyRule).filter(ProxyRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    db_rule.is_active = False
    db.commit()


@router.post("/reload")
def reload_nginx(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> dict:
    """Hot reload Nginx configuration (admin only)."""
    try:
        generator = NginxConfigGenerator(config_path="/etc/nginx/nginx.conf")
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
        )
