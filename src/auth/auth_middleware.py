"""Authentication middleware and dependencies for protected routes."""

from typing import Optional, List
from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import logging

from src.core.database import get_db, DatabaseManager
from src.core.user_models import User, Role, Permission, UserRole, RolePermission, AuthToken
from . import verify_access_token

logger = logging.getLogger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class CurrentUser:
    """Container for current authenticated user information."""

    def __init__(
        self,
        id: str,
        email: str,
        username: str,
        roles: List[str] = None,
        permissions: List[str] = None
    ):
        self.id = id
        self.email = email
        self.username = username
        self.roles = roles or []
        self.permissions = permissions or []

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return role_name in self.roles

    def has_permission(self, resource: str, action: str) -> bool:
        """Check if user has a specific permission."""
        permission = f"{resource}:{action}"
        return permission in self.permissions

    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)

    def has_all_roles(self, roles: List[str]) -> bool:
        """Check if user has all specified roles."""
        return all(role in self.roles for role in roles)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """Get the current authenticated user from JWT token.

    Args:
        token: JWT access token from Authorization header

    Returns:
        CurrentUser object with user information

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Verify token
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    db_manager = DatabaseManager()
    with db_manager.get_session() as db:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User account is {user.status}"
            )

        # Load user roles and permissions
        roles = []
        permissions = set()

        user_roles = db.query(UserRole).filter(
            UserRole.user_id == user.id
        ).all()

        for user_role in user_roles:
            # Skip expired roles
            if user_role.expires_at and user_role.expires_at < datetime.utcnow():
                continue

            role = db.query(Role).filter(Role.id == user_role.role_id).first()
            if role:
                roles.append(role.name)

                # Load role permissions
                role_permissions = db.query(RolePermission).filter(
                    RolePermission.role_id == role.id
                ).all()

                for role_perm in role_permissions:
                    perm = db.query(Permission).filter(
                        Permission.id == role_perm.permission_id
                    ).first()
                    if perm:
                        permissions.add(f"{perm.resource}:{perm.action}")

        return CurrentUser(
            id=user.id,
            email=user.email,
            username=user.username,
            roles=roles,
            permissions=list(permissions)
        )


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Ensure the current user is active.

    This is an alias for get_current_user since we already check
    status in that function, but kept for semantic clarity.
    """
    return current_user


class RequireRole:
    """Dependency for requiring specific roles."""

    def __init__(self, *roles: str):
        """Initialize with required roles.

        Args:
            *roles: One or more role names that are required
        """
        self.roles = roles

    async def __call__(
        self,
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        """Check if user has required roles.

        Args:
            current_user: Current authenticated user

        Returns:
            CurrentUser if authorized

        Raises:
            HTTPException: If user doesn't have required roles
        """
        if not current_user.has_any_role(list(self.roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of these roles: {', '.join(self.roles)}"
            )
        return current_user


class RequirePermission:
    """Dependency for requiring specific permissions."""

    def __init__(self, resource: str, action: str):
        """Initialize with required permission.

        Args:
            resource: Resource name (e.g., 'agents', 'tasks')
            action: Action name (e.g., 'create', 'read', 'update', 'delete')
        """
        self.resource = resource
        self.action = action

    async def __call__(
        self,
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        """Check if user has required permission.

        Args:
            current_user: Current authenticated user

        Returns:
            CurrentUser if authorized

        Raises:
            HTTPException: If user doesn't have required permission
        """
        if not current_user.has_permission(self.resource, self.action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires permission: {self.resource}:{self.action}"
            )
        return current_user


async def optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[CurrentUser]:
    """Get current user if authenticated, None otherwise.

    Useful for endpoints that have different behavior for
    authenticated vs anonymous users.
    """
    if not token:
        return None

    try:
        return await get_current_user(token)
    except HTTPException:
        return None


# Convenience dependencies for common permissions
require_admin = RequireRole("admin")
require_user = RequireRole("user", "admin")  # Regular user or admin


# Agent permissions
require_agent_create = RequirePermission("agents", "create")
require_agent_read = RequirePermission("agents", "read")
require_agent_update = RequirePermission("agents", "update")
require_agent_delete = RequirePermission("agents", "delete")

# Task permissions
require_task_create = RequirePermission("tasks", "create")
require_task_read = RequirePermission("tasks", "read")
require_task_update = RequirePermission("tasks", "update")
require_task_delete = RequirePermission("tasks", "delete")

# Memory permissions
require_memory_create = RequirePermission("memories", "create")
require_memory_read = RequirePermission("memories", "read")
require_memory_update = RequirePermission("memories", "update")
require_memory_delete = RequirePermission("memories", "delete")