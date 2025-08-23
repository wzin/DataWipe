import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os

from main import app
from database import Base, get_db
from models import User
from services.auth_service import AuthService

# Test database setup - use in-memory database for isolation
@pytest.fixture
def test_db():
    """Create a fresh test database for each test"""
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal
    
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create test client with fresh database"""
    return TestClient(app)


@pytest.fixture
def test_user(test_db):
    """Create a test user"""
    db = test_db()
    auth_service = AuthService()
    
    # First check if user exists and delete if needed
    existing = db.query(User).filter(
        (User.username == "testuser") | (User.email == "test@example.com")
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
    
    user = auth_service.create_user(
        db=db,
        username="testuser",
        email="test@example.com",
        password="Test123!@#",
        session_duration_hours=24
    )
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get auth headers for test user"""
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "Test123!@#"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestUserRegistration:
    def test_register_valid_user(self, client, test_db):
        """Test successful user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "ValidPass123!",
                "session_duration_hours": 12
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["session_duration_hours"] == 12
    
    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "another@example.com",
                "password": "ValidPass123!",
                "session_duration_hours": 24
            }
        )
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "anotheruser",
                "email": "test@example.com",
                "password": "ValidPass123!",
                "session_duration_hours": 24
            }
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_invalid_password(self, client, test_db):
        """Test registration with invalid password"""
        # Too short
        response = client.post(
            "/api/auth/register",
            json={
                "username": "user1",
                "email": "user1@example.com",
                "password": "Short1!",
                "session_duration_hours": 24
            }
        )
        assert response.status_code == 422
        
        # No uppercase
        response = client.post(
            "/api/auth/register",
            json={
                "username": "user2",
                "email": "user2@example.com",
                "password": "lowercase123!",
                "session_duration_hours": 24
            }
        )
        assert response.status_code == 422
        
        # No special character
        response = client.post(
            "/api/auth/register",
            json={
                "username": "user3",
                "email": "user3@example.com",
                "password": "NoSpecial123",
                "session_duration_hours": 24
            }
        )
        assert response.status_code == 422
    
    def test_register_invalid_email(self, client, test_db):
        """Test registration with invalid email"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "user4",
                "email": "invalid-email",
                "password": "ValidPass123!",
                "session_duration_hours": 24
            }
        )
        assert response.status_code == 422


class TestUserLogin:
    def test_login_valid_credentials(self, client, test_user):
        """Test login with valid credentials"""
        response = client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "Test123!@#"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"
    
    def test_login_invalid_username(self, client, test_user):
        """Test login with invalid username"""
        response = client.post(
            "/api/auth/login",
            data={"username": "wronguser", "password": "Test123!@#"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password"""
        response = client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "WrongPass123!"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_account_lockout(self, client, test_user):
        """Test account lockout after multiple failed attempts"""
        # Make 5 failed login attempts
        for _ in range(5):
            response = client.post(
                "/api/auth/login",
                data={"username": "testuser", "password": "WrongPassword"}
            )
            assert response.status_code in [401, 423]
        
        # 6th attempt should be locked
        response = client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "Test123!@#"}
        )
        assert response.status_code == 423
        assert "Account locked" in response.json()["detail"]


class TestAuthenticatedEndpoints:
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user information"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    def test_get_current_user_no_auth(self, client, test_db):
        """Test getting current user without authentication"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client, test_db):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_logout(self, client, auth_headers):
        """Test logout"""
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
    
    def test_refresh_token(self, client, auth_headers):
        """Test token refresh"""
        response = client.post("/api/auth/refresh", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


class TestPasswordManagement:
    def test_change_password(self, client, auth_headers):
        """Test changing password"""
        response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "Test123!@#",
                "new_password": "NewPass456!@#"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"
        
        # Try logging in with new password
        response = client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "NewPass456!@#"}
        )
        assert response.status_code == 200
    
    def test_change_password_wrong_current(self, client, auth_headers):
        """Test changing password with wrong current password"""
        response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "WrongPassword",
                "new_password": "NewPass456!@#"
            },
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Incorrect current password" in response.json()["detail"]
    
    def test_password_reset_request(self, client, test_user):
        """Test password reset request"""
        response = client.post(
            "/api/auth/password-reset-request",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 200
        assert "password reset link has been sent" in response.json()["message"]
    
    def test_password_reset_request_unknown_email(self, client, test_db):
        """Test password reset request with unknown email"""
        response = client.post(
            "/api/auth/password-reset-request",
            json={"email": "unknown@example.com"}
        )
        # Should still return 200 to prevent email enumeration
        assert response.status_code == 200
        assert "password reset link has been sent" in response.json()["message"]


class TestSessionManagement:
    def test_update_session_duration(self, client, auth_headers):
        """Test updating session duration"""
        response = client.put(
            "/api/auth/session-duration",
            json={"session_duration_hours": 8},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["session_duration_hours"] == 8
    
    def test_update_session_duration_invalid(self, client, auth_headers):
        """Test updating session duration with invalid value"""
        # Too high
        response = client.put(
            "/api/auth/session-duration",
            json={"session_duration_hours": 25},
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Too low
        response = client.put(
            "/api/auth/session-duration",
            json={"session_duration_hours": 0},
            headers=auth_headers
        )
        assert response.status_code == 422


class TestProtectedEndpoints:
    def test_accounts_endpoint_authenticated(self, client, auth_headers):
        """Test accessing accounts endpoint with authentication"""
        response = client.get("/api/accounts", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_accounts_endpoint_unauthenticated(self, client, test_db):
        """Test accessing accounts endpoint without authentication"""
        response = client.get("/api/accounts")
        assert response.status_code == 401
    
    def test_accounts_summary_authenticated(self, client, auth_headers):
        """Test accessing accounts summary with authentication"""
        response = client.get("/api/accounts/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_accounts" in data
        assert "by_status" in data
    
    def test_accounts_summary_unauthenticated(self, client, test_db):
        """Test accessing accounts summary without authentication"""
        response = client.get("/api/accounts/summary")
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])