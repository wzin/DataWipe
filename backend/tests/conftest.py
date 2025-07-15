import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app
from database import Base, get_db
from models import Account, UserSettings, DeletionTask, AuditLog


@pytest.fixture(scope="session")
def test_db():
    """Create test database"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Create engine and tables
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestSessionLocal
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def db_session(test_db):
    """Create database session for tests"""
    session = test_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Create test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_account(db_session):
    """Create sample account for testing"""
    account = Account(
        site_name="Test Site",
        site_url="https://test.com",
        username="testuser",
        password_hash="encrypted_password",
        email="test@example.com",
        status="discovered"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def sample_user_settings(db_session):
    """Create sample user settings for testing"""
    settings = UserSettings(
        user_id="test_user",
        email="test@gmail.com",
        email_password="encrypted_password",
        name="Test User"
    )
    db_session.add(settings)
    db_session.commit()
    db_session.refresh(settings)
    return settings


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing"""
    return """name,url,username,password,notes
Gmail,https://accounts.google.com,test@gmail.com,password123,Email account
Facebook,https://facebook.com,test@facebook.com,password456,Social media
Amazon,https://amazon.com,test@amazon.com,password789,Shopping account"""


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return {
        "site_name": "Test Site",
        "deletion_difficulty": 5,
        "privacy_policy_url": "https://test.com/privacy",
        "deletion_contact_email": "privacy@test.com",
        "deletion_url": "https://test.com/delete",
        "deletion_instructions": "Go to settings and delete account"
    }