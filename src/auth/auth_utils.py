"""Authentication utilities for JWT token management and password hashing."""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import hashlib
import secrets
import logging
from .auth_config import get_auth_config

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get configuration
config = get_auth_config()


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.

    Args:
        data: Dictionary containing token payload
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.access_token_expire_minutes)

    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(to_encode, config.jwt_secret_key, algorithm=config.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token with longer expiration.

    Args:
        data: Dictionary containing token payload

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=config.refresh_token_expire_days)

    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(32)  # Unique token ID for tracking
    })

    encoded_jwt = jwt.encode(to_encode, config.jwt_secret_key, algorithm=config.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, config.jwt_secret_key, algorithms=[config.jwt_algorithm])
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify an access token and return its payload.

    Args:
        token: JWT access token to verify

    Returns:
        Token payload if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            logger.warning("Token is not an access token")
            return None
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a refresh token and return its payload.

    Args:
        token: JWT refresh token to verify

    Returns:
        Token payload if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            logger.warning("Token is not a refresh token")
            return None
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """Create a SHA256 hash of a token for secure storage.

    Args:
        token: Token string to hash

    Returns:
        SHA256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token.

    Args:
        length: Length of the token in bytes

    Returns:
        URL-safe token string
    """
    return secrets.token_urlsafe(length)


def create_token_pair(user_id: str, email: str, roles: list = None) -> Dict[str, str]:
    """Create both access and refresh tokens for a user.

    Args:
        user_id: User's unique identifier
        email: User's email address
        roles: Optional list of user roles

    Returns:
        Dictionary containing access_token and refresh_token
    """
    token_data = {
        "sub": user_id,
        "email": email,
        "roles": roles or []
    }

    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer"
    }