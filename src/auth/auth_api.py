"""Authentication API endpoints for Hephaestus."""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
import uuid
import logging

from src.core.database import get_db, DatabaseManager
from src.core.user_models import User, AuthToken, UserSession, LoginAttempt, AuditLog
from . import (
    hash_password,
    verify_password,
    create_token_pair,
    verify_refresh_token,
    hash_token,
    generate_secure_token,
)
from .auth_config import get_auth_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
config = get_auth_config()


# Request/Response models
class UserRegisterRequest(BaseModel):
    """User registration request model."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLoginRequest(BaseModel):
    """User login request model."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""

    refresh_token: str


class UserResponse(BaseModel):
    """User response model."""

    id: str
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: datetime
    email_verified: bool
    status: str


# Helper functions
def get_db_manager() -> DatabaseManager:
    """Get database manager instance."""
    return DatabaseManager()


def validate_password(password: str) -> bool:
    """Validate password meets requirements.

    Args:
        password: Password to validate

    Returns:
        True if password meets requirements

    Raises:
        HTTPException: If password doesn't meet requirements
    """
    errors = []

    if len(password) < config.min_password_length:
        errors.append(f"Password must be at least {config.min_password_length} characters")

    if config.require_uppercase and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if config.require_lowercase and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if config.require_digit and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    if config.require_special and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password validation failed", "errors": errors}
        )

    return True


def record_login_attempt(
    db: Session,
    email: str,
    ip_address: str,
    user_agent: str,
    success: bool,
    failure_reason: Optional[str] = None
):
    """Record a login attempt for security auditing."""
    attempt = LoginAttempt(
        email=email,
        ip_address=ip_address,
        user_agent=user_agent,
        attempt_type="password",
        success=success,
        failure_reason=failure_reason
    )
    db.add(attempt)
    db.commit()


def check_login_attempts(db: Session, email: str) -> bool:
    """Check if user has exceeded login attempt limit.

    Returns:
        True if login is allowed, False if account is locked
    """
    if not config.max_login_attempts:
        return True

    # Get recent failed attempts
    cutoff_time = datetime.utcnow() - timedelta(minutes=config.lockout_duration_minutes)
    recent_attempts = db.query(LoginAttempt).filter(
        LoginAttempt.email == email,
        LoginAttempt.success == False,
        LoginAttempt.attempted_at >= cutoff_time
    ).count()

    return recent_attempts < config.max_login_attempts


def create_audit_log(
    db: Session,
    user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    status_result: str = "success",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    error_message: Optional[str] = None
):
    """Create an audit log entry."""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status_result,
        ip_address=ip_address,
        user_agent=user_agent,
        error_message=error_message
    )
    db.add(audit)
    db.commit()


# API Endpoints
@router.post("/register", response_model=UserResponse)
async def register(request: UserRegisterRequest):
    """Register a new user account."""
    db_manager = get_db_manager()

    # Validate password
    validate_password(request.password)

    with db_manager.get_session() as db:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if username already exists
        existing_user = db.query(User).filter(User.username == request.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            email=request.email,
            username=request.username,
            password_hash=hash_password(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
            status="active",
            email_verified=not config.enable_email_verification  # Auto-verify if verification disabled
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # Create audit log
        create_audit_log(
            db=db,
            user_id=user.id,
            action="register",
            resource_type="user",
            resource_id=user.id,
            status_result="success"
        )

        logger.info(f"New user registered: {user.email}")

        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            created_at=user.created_at,
            email_verified=user.email_verified,
            status=user.status
        )


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with email and password."""
    db_manager = get_db_manager()

    with db_manager.get_session() as db:
        # Check login attempts
        if not check_login_attempts(db, form_data.username):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account locked due to too many failed login attempts. Try again in {config.lockout_duration_minutes} minutes."
            )

        # Find user by email (username field contains email)
        user = db.query(User).filter(User.email == form_data.username).first()

        if not user or not verify_password(form_data.password, user.password_hash):
            # Record failed attempt
            record_login_attempt(
                db=db,
                email=form_data.username,
                ip_address="",  # TODO: Get from request
                user_agent="",  # TODO: Get from request
                success=False,
                failure_reason="Invalid credentials"
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check user status
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user.status}"
            )

        # Record successful attempt
        record_login_attempt(
            db=db,
            email=form_data.username,
            ip_address="",  # TODO: Get from request
            user_agent="",  # TODO: Get from request
            success=True
        )

        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()

        # Create tokens
        tokens = create_token_pair(
            user_id=user.id,
            email=user.email,
            roles=[]  # TODO: Load user roles
        )

        # Store refresh token
        refresh_token_record = AuthToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=hash_token(tokens["refresh_token"]),
            token_type="refresh",
            expires_at=datetime.utcnow() + timedelta(days=config.refresh_token_expire_days)
        )
        db.add(refresh_token_record)

        # Create session
        session = UserSession(
            id=str(uuid.uuid4()),
            user_id=user.id,
            session_token_hash=generate_secure_token(),
            ip_address="",  # TODO: Get from request
            user_agent="",  # TODO: Get from request
            expires_at=datetime.utcnow() + timedelta(minutes=config.session_timeout_minutes)
        )
        db.add(session)

        # Create audit log
        create_audit_log(
            db=db,
            user_id=user.id,
            action="login",
            resource_type="user",
            resource_id=user.id,
            status_result="success"
        )

        db.commit()

        logger.info(f"User logged in: {user.email}")

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=config.access_token_expire_minutes * 60
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    db_manager = get_db_manager()

    # Verify refresh token
    payload = verify_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    with db_manager.get_session() as db:
        # Check if refresh token exists and is valid
        token_hash = hash_token(request.refresh_token)
        stored_token = db.query(AuthToken).filter(
            AuthToken.token_hash == token_hash,
            AuthToken.token_type == "refresh"
        ).first()

        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found"
            )

        if stored_token.revoked_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )

        if stored_token.expires_at and stored_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )

        # Get user
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user or user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Update token last used
        stored_token.last_used_at = datetime.utcnow()

        # Create new tokens
        tokens = create_token_pair(
            user_id=user.id,
            email=user.email,
            roles=[]  # TODO: Load user roles
        )

        # Optionally revoke old refresh token and store new one
        if not config.allow_multiple_sessions:
            stored_token.revoked_at = datetime.utcnow()

        # Store new refresh token
        new_refresh_token = AuthToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=hash_token(tokens["refresh_token"]),
            token_type="refresh",
            expires_at=datetime.utcnow() + timedelta(days=config.refresh_token_expire_days)
        )
        db.add(new_refresh_token)

        db.commit()

        logger.info(f"Token refreshed for user: {user.email}")

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=config.access_token_expire_minutes * 60
        )


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Logout and invalidate tokens."""
    # TODO: Implement token blacklisting or session termination
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user information."""
    # TODO: Implement get current user from token
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not yet implemented"
    )