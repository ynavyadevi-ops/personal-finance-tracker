"""FastAPI router implementing dedicated administrative portal management endpoints."""

import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.api.dependencies import require_admin
from src.core.exceptions import NotFoundError, ValidationError
from src.core.logging import logger
from src.core.security import hash_password
from src.db.models.audit import AuditLog
from src.db.models.settings import SystemSettings
from src.db.models.user import User, UserRole
from src.db.session import get_db
from src.schemas.common import GenericResponse
from src.schemas.user import (
    AdminOverviewMetrics,
    AdminResetPasswordResponse,
    AdminUserRead,
    AdminUserStatusUpdate,
    SystemSettingsRead,
    SystemSettingsUpdate,
)

router = APIRouter(prefix="/admin", tags=["Admin Portal"])


@router.get(
    "/overview",
    response_model=GenericResponse[AdminOverviewMetrics],
    summary="Platform operational overview and user metrics",
)
def get_admin_overview(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GenericResponse[AdminOverviewMetrics]:
    """Retrieve high-level user statistics, system health, and platform registration status."""
    total_users = db.scalar(select(func.count(User.id))) or 0
    active_users = db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0
    disabled_users = db.scalar(select(func.count(User.id)).where(User.is_active.is_(False))) or 0

    thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
    recent_users = (
        db.scalar(select(func.count(User.id)).where(User.created_at >= thirty_days_ago)) or 0
    )

    setting = db.execute(
        select(SystemSettings).where(SystemSettings.key == "registration_enabled")
    ).scalar_one_or_none()
    reg_enabled = setting.value.lower() == "true" if setting else True

    metrics = AdminOverviewMetrics(
        total_users=total_users,
        active_users=active_users,
        disabled_users=disabled_users,
        recent_registrations_30d=recent_users,
        db_connected=True,
        registration_enabled=reg_enabled,
    )
    return GenericResponse(success=True, data=metrics)


@router.get(
    "/users",
    response_model=GenericResponse[list[AdminUserRead]],
    summary="List and filter users for administrative management",
)
def list_users(
    search: str | None = Query(None, description="Search by user email or name"),
    role: UserRole | None = Query(None, description="Filter by user role"),
    active_only: bool | None = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GenericResponse[list[AdminUserRead]]:
    """List registered users with administrative metadata. Strictly excludes financial accounts and balances."""
    stmt = select(User)

    if search:
        search_term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            (func.lower(User.email).like(search_term)) | (func.lower(User.name).like(search_term))
        )

    if role:
        stmt = stmt.where(User.role == role)

    if active_only is not None:
        stmt = stmt.where(User.is_active.is_(active_only))

    stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    users = db.execute(stmt).scalars().all()

    data = [AdminUserRead.model_validate(u) for u in users]
    return GenericResponse(
        success=True, data=data, meta={"page": page, "page_size": page_size, "count": len(data)}
    )


@router.patch(
    "/users/{user_id}/status",
    response_model=GenericResponse[AdminUserRead],
    summary="Enable or disable user access",
)
def update_user_status(
    user_id: str,
    payload: AdminUserStatusUpdate,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GenericResponse[AdminUserRead]:
    """Enable or disable access for a target user account."""
    target_user = db.get(User, user_id)
    if not target_user:
        raise NotFoundError(f"User with ID '{user_id}' was not found.")

    if target_user.id == current_admin.id and not payload.is_active:
        raise ValidationError("Administrators cannot disable their own active account.")

    old_status = target_user.is_active
    target_user.is_active = payload.is_active

    audit = AuditLog(
        user_id=current_admin.id,
        action="USER_STATUS_CHANGE",
        entity_name="USER",
        entity_id=target_user.id,
        old_values=json.dumps({"is_active": old_status}),
        new_values=json.dumps({"is_active": payload.is_active}),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(audit)
    db.commit()
    db.refresh(target_user)

    logger.info(
        f"Admin {current_admin.id} changed status of user {target_user.id} to is_active={payload.is_active}"
    )
    return GenericResponse(success=True, data=AdminUserRead.model_validate(target_user))


@router.post(
    "/users/{user_id}/reset-password",
    response_model=GenericResponse[AdminResetPasswordResponse],
    summary="Initiate secure password reset with temporary credentials",
)
def reset_user_password(
    user_id: str,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GenericResponse[AdminResetPasswordResponse]:
    """Generate high-entropy temporary password and flag must_change_password=True for target user."""
    target_user = db.get(User, user_id)
    if not target_user:
        raise NotFoundError(f"User with ID '{user_id}' was not found.")

    # Generate temporary password meeting complexity requirements
    rand_suffix = secrets.token_urlsafe(10)
    temporary_password = f"Temp!{rand_suffix}1A"

    target_user.hashed_password = hash_password(temporary_password)
    target_user.must_change_password = True

    audit = AuditLog(
        user_id=current_admin.id,
        action="ADMIN_PASSWORD_RESET",
        entity_name="USER",
        entity_id=target_user.id,
        new_values=json.dumps({"must_change_password": True}),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(audit)
    db.commit()

    logger.info(f"Admin {current_admin.id} initiated password reset for user {target_user.id}")
    return GenericResponse(
        success=True,
        data=AdminResetPasswordResponse(
            user_id=target_user.id,
            email=target_user.email or "unknown",
            temporary_password=temporary_password,
            must_change_password=True,
            message="Temporary password generated. The user will be required to change it upon first login.",
        ),
    )


@router.get(
    "/audit-logs",
    response_model=GenericResponse[list[dict[str, Any]]],
    summary="Retrieve administrative audit logs",
)
def get_administrative_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GenericResponse[list[dict[str, Any]]]:
    """Retrieve security and administrative audit log history."""
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    entries = db.execute(stmt).scalars().all()

    logs = [
        {
            "id": e.id,
            "user_id": e.user_id,
            "action": e.action,
            "entity_name": e.entity_name,
            "entity_id": e.entity_id,
            "old_values": e.old_values,
            "new_values": e.new_values,
            "ip_address": e.ip_address,
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]
    return GenericResponse(success=True, data=logs, meta={"count": len(logs)})


@router.get(
    "/settings",
    response_model=GenericResponse[list[SystemSettingsRead]],
    summary="Retrieve platform system settings",
)
def get_system_settings(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GenericResponse[list[SystemSettingsRead]]:
    """Retrieve all platform system settings."""
    stmt = select(SystemSettings).order_by(SystemSettings.key)
    settings_list = db.execute(stmt).scalars().all()
    data = [SystemSettingsRead.model_validate(s) for s in settings_list]
    return GenericResponse(success=True, data=data)


@router.patch(
    "/settings",
    response_model=GenericResponse[dict[str, str]],
    summary="Update platform system settings",
)
def update_system_settings(
    payload: SystemSettingsUpdate,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GenericResponse[dict[str, str]]:
    """Update platform-wide settings (e.g. toggle public user registration)."""
    setting = db.execute(
        select(SystemSettings).where(SystemSettings.key == "registration_enabled")
    ).scalar_one_or_none()

    new_val = "true" if payload.registration_enabled else "false"
    old_val = setting.value if setting else "true"

    if not setting:
        setting = SystemSettings(
            key="registration_enabled",
            value=new_val,
            description="Whether public user registration is permitted",
        )
        db.add(setting)
    else:
        setting.value = new_val

    audit = AuditLog(
        user_id=current_admin.id,
        action="SYSTEM_SETTINGS_UPDATE",
        entity_name="SYSTEM_SETTINGS",
        entity_id="registration_enabled",
        old_values=json.dumps({"registration_enabled": old_val}),
        new_values=json.dumps({"registration_enabled": new_val}),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(audit)
    db.commit()

    logger.info(f"Admin {current_admin.id} updated registration_enabled to {new_val}")
    return GenericResponse(
        success=True,
        data={"registration_enabled": new_val},
    )
