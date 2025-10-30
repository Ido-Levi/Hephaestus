"""User management database models for Hephaestus."""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    Boolean,
    ForeignKey,
    CheckConstraint,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from src.core.database import Base


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    display_name = Column(String)
    avatar_url = Column(Text)
    bio = Column(Text)
    status = Column(
        String,
        CheckConstraint("status IN ('active', 'inactive', 'suspended', 'deleted')"),
        default="active",
        nullable=False,
    )
    email_verified = Column(Boolean, default=False)
    phone_number = Column(String)
    phone_verified = Column(Boolean, default=False)
    timezone = Column(String, default="UTC")
    language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    deleted_at = Column(DateTime)  # Soft delete support

    # Relationships
    roles = relationship("UserRole", back_populates="user", foreign_keys="[UserRole.user_id]", cascade="all, delete-orphan")
    teams = relationship("TeamMember", back_populates="user", foreign_keys="[TeamMember.user_id]")
    owned_teams = relationship("Team", back_populates="owner")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    tokens = relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    # Note: User relationships with Agent, Task, Memory are not implemented yet
    # created_agents = relationship("Agent", foreign_keys="Agent.created_by_user_id", backref="creator")
    # created_tasks = relationship("Task", foreign_keys="Task.created_by_user_id", backref="task_creator")
    # assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to_user_id", backref="task_assignee")
    # created_memories = relationship("Memory", foreign_keys="Memory.created_by_user_id", backref="memory_creator")

    __table_args__ = (
        Index("idx_users_status", "status"),
        Index("idx_users_created_at", "created_at"),
    )


class Role(Base):
    """Role model for role-based access control."""

    __tablename__ = "roles"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text)
    is_system = Column(Boolean, default=False)  # System roles cannot be deleted
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("UserRole", back_populates="role")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")


class UserRole(Base):
    """Many-to-many relationship between users and roles."""

    __tablename__ = "user_roles"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(String, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    granted_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"))
    expires_at = Column(DateTime)  # Optional role expiration

    # Relationships
    user = relationship("User", back_populates="roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="users")
    grantor = relationship("User", foreign_keys=[granted_by])

    __table_args__ = (
        Index("idx_user_roles_user", "user_id"),
        Index("idx_user_roles_role", "role_id"),
        Index("idx_user_roles_expires", "expires_at"),
    )


class Permission(Base):
    """Granular permissions that can be assigned to roles."""

    __tablename__ = "permissions"

    id = Column(String, primary_key=True)
    resource = Column(String, nullable=False)  # e.g., 'agents', 'tasks', 'memories'
    action = Column(String, nullable=False)  # e.g., 'create', 'read', 'update', 'delete'
    description = Column(Text)
    is_system = Column(Boolean, default=False)

    # Relationships
    roles = relationship("RolePermission", back_populates="permission")

    __table_args__ = (
        UniqueConstraint("resource", "action", name="unique_permission"),
        Index("idx_permissions_resource", "resource"),
    )


class RolePermission(Base):
    """Links roles to their permissions."""

    __tablename__ = "role_permissions"

    role_id = Column(String, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(String, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")

    __table_args__ = (Index("idx_role_permissions_role", "role_id"),)


class Team(Base):
    """Teams for collaborative features."""

    __tablename__ = "teams"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    settings = Column(JSON)  # Team-specific settings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="owned_teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_teams_owner", "owner_id"),
        Index("idx_teams_active", "is_active"),
    )


class TeamMember(Base):
    """Team membership tracking."""

    __tablename__ = "team_members"

    team_id = Column(String, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(
        String,
        CheckConstraint("role IN ('owner', 'admin', 'member', 'viewer')"),
        default="member",
        nullable=False,
    )
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    invited_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"))

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="teams", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])

    __table_args__ = (
        Index("idx_team_members_team", "team_id"),
        Index("idx_team_members_user", "user_id"),
    )


class AuthToken(Base):
    """JWT refresh tokens and API keys."""

    __tablename__ = "auth_tokens"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String, unique=True, nullable=False, index=True)  # Hashed token for security
    token_type = Column(
        String,
        CheckConstraint("token_type IN ('refresh', 'api_key', 'password_reset', 'email_verification')"),
        nullable=False,
    )
    client_info = Column(JSON)  # User agent, IP, etc.
    expires_at = Column(DateTime)
    revoked_at = Column(DateTime)
    last_used_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="tokens")

    __table_args__ = (
        Index("idx_auth_tokens_user", "user_id"),
        Index("idx_auth_tokens_expires", "expires_at"),
        Index("idx_auth_tokens_type", "token_type"),
    )


class UserSession(Base):
    """Active user sessions tracking."""

    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token_hash = Column(String, unique=True, nullable=False, index=True)
    ip_address = Column(String)
    user_agent = Column(Text)
    device_info = Column(JSON)
    location_info = Column(JSON)  # Country, city from IP
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    terminated_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("idx_sessions_user", "user_id"),
        Index("idx_sessions_expires", "expires_at"),
    )


class AuditLog(Base):
    """Comprehensive audit trail for security and compliance."""

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String, nullable=False)  # 'login', 'logout', 'create_agent', etc.
    resource_type = Column(String)  # 'user', 'agent', 'task', etc.
    resource_id = Column(String)
    changes = Column(JSON)  # Before/after values for updates
    ip_address = Column(String)
    user_agent = Column(Text)
    status = Column(
        String,
        CheckConstraint("status IN ('success', 'failure', 'error')"),
        nullable=False,
    )
    error_message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_timestamp", "timestamp"),
    )


class UserPreferences(Base):
    """User-specific settings and preferences."""

    __tablename__ = "user_preferences"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    theme = Column(String, default="light")
    notification_settings = Column(JSON)
    dashboard_layout = Column(JSON)
    default_agent_settings = Column(JSON)
    ui_preferences = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="preferences")


class LoginAttempt(Base):
    """Track failed login attempts for security."""

    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String)
    ip_address = Column(String)
    user_agent = Column(Text)
    attempt_type = Column(
        String,
        CheckConstraint("attempt_type IN ('password', 'token', 'oauth')"),
        nullable=False,
    )
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String)
    attempted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_attempts_email", "email"),
        Index("idx_attempts_ip", "ip_address"),
        Index("idx_attempts_time", "attempted_at"),
    )