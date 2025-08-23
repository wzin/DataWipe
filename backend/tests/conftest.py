import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app
from database import Base, get_db
from models import User


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function"""
    # Create an in-memory SQLite database
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a test session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with the test database"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db):
    """Create a test user"""
    from services.auth_service import AuthService
    
    auth_service = AuthService()
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=auth_service.get_password_hash("TestPassword123!")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers for test user"""
    from services.auth_service import AuthService
    
    auth_service = AuthService()
    access_token = auth_service.create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_account(test_db, test_user):
    """Create a test account"""
    from models import Account, AccountStatus
    from services.encryption_service import encryption_service
    
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
    test_db.add(account)
    test_db.commit()
    test_db.refresh(account)
    return account
