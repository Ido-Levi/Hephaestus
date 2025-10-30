"""Authentication module for Hephaestus."""

from .auth_utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_access_token,
    verify_refresh_token,
    hash_token,
    generate_secure_token,
    create_token_pair,
)
from .auth_config import AuthConfig, get_auth_config

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_access_token",
    "verify_refresh_token",
    "hash_token",
    "generate_secure_token",
    "create_token_pair",
    "AuthConfig",
    "get_auth_config",
]