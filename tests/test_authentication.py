"""Tests for authentication functionality."""

import pytest
import uuid
from datetime import datetime, timedelta
from jose import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.database import Base, DatabaseManager
from src.core.user_models import User
from src.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    create_token_pair,
    hash_token,
)
from src.auth.auth_config import get_auth_config


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 30
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_hashes_same_password(self):
        """Test that same password creates different hashes."""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token functions."""

    def test_create_access_token(self):
        """Test creating access token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50

    def test_verify_access_token_valid(self):
        """Test verifying valid access token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        payload = verify_access_token(token)

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"

    def test_verify_access_token_invalid(self):
        """Test verifying invalid access token."""
        invalid_token = "invalid.token.string"
        payload = verify_access_token(invalid_token)

        assert payload is None

    def test_verify_refresh_token_valid(self):
        """Test verifying valid refresh token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_refresh_token(data)
        payload = verify_refresh_token(token)

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "refresh"
        assert "jti" in payload  # Unique token ID

    def test_access_token_expiry(self):
        """Test access token expiration."""
        config = get_auth_config()
        data = {"sub": "user123", "email": "test@example.com"}

        # Create token with 1 second expiry
        token = create_access_token(data, expires_delta=timedelta(seconds=1))

        # Should be valid immediately
        payload = verify_access_token(token)
        assert payload is not None

        # Wait for expiration
        import time
        time.sleep(2)

        # Should be invalid after expiry
        payload = verify_access_token(token)
        assert payload is None

    def test_create_token_pair(self):
        """Test creating token pair."""
        user_id = "user123"
        email = "test@example.com"
        roles = ["user", "admin"]

        tokens = create_token_pair(user_id, email, roles)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

        # Verify both tokens
        access_payload = verify_access_token(tokens["access_token"])
        refresh_payload = verify_refresh_token(tokens["refresh_token"])

        assert access_payload["sub"] == user_id
        assert access_payload["email"] == email
        assert access_payload["roles"] == roles

        assert refresh_payload["sub"] == user_id
        assert refresh_payload["email"] == email
        assert refresh_payload["roles"] == roles

    def test_hash_token(self):
        """Test token hashing for storage."""
        token = "test.token.value"
        hash1 = hash_token(token)
        hash2 = hash_token(token)

        assert hash1 == hash2  # Same token produces same hash
        assert len(hash1) == 64  # SHA256 produces 64 char hex string
        assert hash1 != token


@pytest.fixture
def test_db():
    """Create a test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def test_client(test_db, monkeypatch):
    """Create a test client with test database."""
    from src.mcp.server import app

    def get_test_db():
        try:
            yield test_db
        finally:
            pass

    # Monkey patch the database dependency
    from src.core import database
    monkeypatch.setattr(database, "get_db", get_test_db)

    client = TestClient(app)
    return client


class TestAuthenticationAPI:
    """Test authentication API endpoints."""

    def test_register_success(self, test_client):
        """Test successful user registration."""
        response = test_client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePassword123!",
                "first_name": "John",
                "last_name": "Doe"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert "id" in data
        assert "created_at" in data

    def test_register_duplicate_email(self, test_client):
        """Test registration with duplicate email."""
        # Register first user
        test_client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user1",
                "password": "SecurePassword123!"
            }
        )

        # Try to register with same email
        response = test_client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user2",
                "password": "SecurePassword123!"
            }
        )

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_weak_password(self, test_client):
        """Test registration with weak password."""
        response = test_client.post(
            "/api/auth/register",
            json={
                "email": "weakpass@example.com",
                "username": "weakuser",
                "password": "weak"  # Too short
            }
        )

        assert response.status_code == 400
        error = response.json()["detail"]
        assert "Password" in str(error)

    def test_login_success(self, test_client, test_db):
        """Test successful login."""
        # Create a test user directly in database
        from src.core.user_models import User as UserModel

        user = UserModel(
            id=str(uuid.uuid4()),
            email="testuser@example.com",
            username="testuser",
            password_hash=hash_password("TestPassword123!"),
            status="active",
            email_verified=True
        )
        test_db.add(user)
        test_db.commit()

        # Login
        response = test_client.post(
            "/api/auth/login",
            data={
                "username": "testuser@example.com",
                "password": "TestPassword123!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_wrong_password(self, test_client, test_db):
        """Test login with wrong password."""
        # Create a test user
        from src.core.user_models import User as UserModel

        user = UserModel(
            id=str(uuid.uuid4()),
            email="wrongpass@example.com",
            username="wrongpassuser",
            password_hash=hash_password("CorrectPassword123!"),
            status="active"
        )
        test_db.add(user)
        test_db.commit()

        # Try login with wrong password
        response = test_client.post(
            "/api/auth/login",
            data={
                "username": "wrongpass@example.com",
                "password": "WrongPassword456!"
            }
        )

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, test_client):
        """Test login with non-existent user."""
        response = test_client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "AnyPassword123!"
            }
        )

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_refresh_token_valid(self, test_client, test_db):
        """Test refreshing token with valid refresh token."""
        from src.core.user_models import User as UserModel, AuthToken

        # Create user and login
        user = UserModel(
            id=str(uuid.uuid4()),
            email="refresh@example.com",
            username="refreshuser",
            password_hash=hash_password("TestPassword123!"),
            status="active"
        )
        test_db.add(user)
        test_db.commit()

        # Login to get tokens
        login_response = test_client.post(
            "/api/auth/login",
            data={
                "username": "refresh@example.com",
                "password": "TestPassword123!"
            }
        )
        tokens = login_response.json()

        # Refresh token
        response = test_client.post(
            "/api/auth/refresh",
            json={
                "refresh_token": tokens["refresh_token"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != tokens["access_token"]  # New access token

    def test_refresh_token_invalid(self, test_client):
        """Test refreshing with invalid refresh token."""
        response = test_client.post(
            "/api/auth/refresh",
            json={
                "refresh_token": "invalid.refresh.token"
            }
        )

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]


class TestAuthenticationMiddleware:
    """Test authentication middleware."""

    def test_protected_route_without_token(self, test_client):
        """Test accessing protected route without token."""
        # This would be a protected endpoint
        # response = test_client.get("/api/protected")
        # assert response.status_code == 401
        pass  # TODO: Add when protected endpoints are implemented

    def test_protected_route_with_valid_token(self, test_client, test_db):
        """Test accessing protected route with valid token."""
        # TODO: Add when protected endpoints are implemented
        pass

    def test_protected_route_with_expired_token(self, test_client):
        """Test accessing protected route with expired token."""
        # TODO: Add when protected endpoints are implemented
        pass