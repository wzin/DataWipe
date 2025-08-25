import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Set test database before any imports
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from main import app
from database import Base, get_db
from models import User

# Import all models to ensure they're registered with Base
from models import (
    User, Account, DeletionTask, AuditLog, UserSettings,
    LLMInteraction, SiteMetadata
)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function"""
    # Create an in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a test session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="function")
def client():
    """Create a test client with the test database"""
    # Create an in-memory SQLite database for the test
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Override the get_db dependency
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Cleanup
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_user(client):
    """Create a test user"""
    from services.auth_service import AuthService
    
    # Get the db session from the overridden dependency
    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    
    auth_service = AuthService()
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=auth_service.get_password_hash("TestPassword123!")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Close the generator
    try:
        next(db_gen)
    except StopIteration:
        pass
    
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    from services.auth_service import AuthService
    
    auth_service = AuthService()
    access_token = auth_service.create_access_token(data={
        "sub": test_user.id,
        "username": test_user.username
    })
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_account(client, test_user):
    """Create a test account"""
    from models import Account, AccountStatus
    from services.encryption_service import encryption_service
    
    # Get the db session from the overridden dependency
    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    
    account = Account(
        user_id=test_user.id,
        site_name="Test Site",
        site_url="https://test.com",
        username="testuser",
        encrypted_password=encryption_service.encrypt_password("password123"),
        email="test@test.com",
        status=AccountStatus.DISCOVERED,
        category="other",
        risk_level="medium"
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    
    # Close the generator
    try:
        next(db_gen)
    except StopIteration:
        pass
    
    return account


@pytest.fixture
def sample_account(client, test_user):
    """Alias for test_account for backward compatibility"""
    from models import Account, AccountStatus
    from services.encryption_service import encryption_service
    
    # Get the db session from the overridden dependency
    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    
    account = Account(
        user_id=test_user.id,
        site_name="Test Site",
        site_url="https://test.com",
        username="testuser",
        encrypted_password=encryption_service.encrypt_password("password123"),
        email="test@test.com",
        status=AccountStatus.DISCOVERED,
        category="other",
        risk_level="medium"
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    
    # Close the generator
    try:
        next(db_gen)
    except StopIteration:
        pass
    
    return account


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return {
        "site_name": "Test Site",
        "site_url": "https://test.com",
        "username": "testuser",
        "password": "password123",
        "email": "test@test.com"
    }


@pytest.fixture
def test_user_data():
    """Test user registration data"""
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "ValidPass123!",
        "session_duration_hours": 24
    }