"""
Integration tests for DataWipe - end-to-end testing of key workflows
"""
import pytest
import asyncio
import tempfile
import csv
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app
from database import Base, get_db
from models import User, Account, DeletionTask, TaskStatus, AccountStatus, DeletionMethod
from services.auth_service import AuthService
from services.csv_parser import CSVParser
from services.encryption_service import encryption_service
from services.categorization_service import categorization_service
from services.email_service import EmailService
from services.deletion_service import DeletionService


# Test database setup
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def setup_db():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(setup_db):
    """Create test client"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user registration data"""
    return {
        "username": "integrationuser",
        "email": "integration@test.com",
        "password": "SecurePass123!",
        "session_duration_hours": 24
    }


@pytest.fixture
def csv_file_path():
    """Create temporary CSV file with test data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'url', 'username', 'password', 'notes'])
        writer.writerow(['Facebook', 'https://facebook.com', 'user@email.com', 'fbpass123', 'Social media'])
        writer.writerow(['Gmail', 'https://gmail.com', 'user@gmail.com', 'gmailpass456', 'Email account'])
        writer.writerow(['Amazon', 'https://amazon.com', 'shopper@email.com', 'amazonpass789', 'Shopping'])
        writer.writerow(['Netflix', 'https://netflix.com', 'viewer@email.com', 'netflixpass000', 'Streaming'])
        writer.writerow(['LinkedIn', 'https://linkedin.com', 'professional@email.com', 'linkedinpass111', 'Professional'])
        return f.name


class TestIntegration1_UserAccountLifecycle:
    """Test 1: Complete user account lifecycle - registration, login, settings, logout"""
    
    def test_complete_user_lifecycle(self, client, test_user_data):
        """Test complete user lifecycle from registration to logout"""
        
        # 1. Register new user
        register_response = client.post("/api/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        register_data = register_response.json()
        assert "access_token" in register_data
        assert register_data["user"]["username"] == test_user_data["username"]
        assert register_data["user"]["email"] == test_user_data["email"]
        
        access_token = register_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Get current user info
        user_response = client.get("/api/auth/me", headers=headers)
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert user_data["username"] == test_user_data["username"]
        assert user_data["is_active"] is True
        
        # 3. Update session duration
        session_response = client.put(
            "/api/auth/session",
            json={"session_duration_hours": 12},
            headers=headers
        )
        assert session_response.status_code == 200
        assert session_response.json()["session_duration_hours"] == 12
        
        # 4. Change password
        change_password_response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": test_user_data["password"],
                "new_password": "NewSecurePass456!"
            },
            headers=headers
        )
        assert change_password_response.status_code == 200
        
        # 5. Logout
        logout_response = client.post("/api/auth/logout", headers=headers)
        assert logout_response.status_code == 200
        
        # 6. Login with new password
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": test_user_data["username"],
                "password": "NewSecurePass456!"
            }
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
        
        # 7. Try to use old token (should fail)
        old_token_response = client.get("/api/auth/me", headers=headers)
        assert old_token_response.status_code == 401


class TestIntegration2_CSVImportAndCategorization:
    """Test 2: CSV import, parsing, categorization, and account management"""
    
    def test_csv_import_and_categorization_workflow(self, client, test_user_data, csv_file_path):
        """Test complete CSV import and categorization workflow"""
        
        # 1. Register and login
        register_response = client.post("/api/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        access_token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Upload CSV file
        with open(csv_file_path, 'rb') as f:
            upload_response = client.post(
                "/api/upload/csv",
                files={"file": ("accounts.csv", f, "text/csv")},
                headers=headers
            )
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["accounts_imported"] == 5
        assert upload_data["success"] is True
        
        # 3. Get imported accounts
        accounts_response = client.get("/api/accounts", headers=headers)
        assert accounts_response.status_code == 200
        accounts = accounts_response.json()
        assert len(accounts) == 5
        
        # 4. Verify categorization
        categories_found = set()
        for account in accounts:
            assert "category" in account
            assert "risk_level" in account
            assert "deletion_priority" in account
            categories_found.add(account["category"])
        
        # Should have multiple categories
        assert len(categories_found) >= 3
        assert "social_media" in categories_found  # Facebook, LinkedIn
        assert "email" in categories_found  # Gmail
        assert "shopping" in categories_found  # Amazon
        
        # 5. Get account summary
        summary_response = client.get("/api/accounts/summary", headers=headers)
        assert summary_response.status_code == 200
        summary = summary_response.json()
        assert summary["total_accounts"] == 5
        assert "by_status" in summary
        assert "by_category" in summary
        
        # 6. Update account status
        account_id = accounts[0]["id"]
        status_response = client.put(
            f"/api/accounts/{account_id}/status",
            json={"status": "pending"},
            headers=headers
        )
        assert status_response.status_code == 200
        
        # 7. Bulk categorize accounts
        bulk_response = client.post(
            "/api/accounts/categorize/bulk",
            json={"account_ids": [acc["id"] for acc in accounts[:3]]},
            headers=headers
        )
        assert bulk_response.status_code == 200
        assert bulk_response.json()["categorized"] == 3
        
        # 8. Delete an account
        delete_response = client.delete(
            f"/api/accounts/{account_id}",
            headers=headers
        )
        assert delete_response.status_code == 200
        
        # 9. Verify account was deleted
        accounts_after = client.get("/api/accounts", headers=headers).json()
        assert len(accounts_after) == 4


class TestIntegration3_DeletionWorkflow:
    """Test 3: Complete deletion workflow with tasks, retries, and audit logging"""
    
    @pytest.mark.asyncio
    async def test_deletion_workflow_with_retry(self, client, test_user_data):
        """Test complete deletion workflow including retry logic"""
        
        # 1. Setup user and accounts
        register_response = client.post("/api/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        access_token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Manually add accounts for deletion
        accounts_to_add = [
            {
                "site_name": "Test Site 1",
                "site_url": "https://testsite1.com",
                "username": "testuser1",
                "password": "pass123",
                "email": "test1@email.com"
            },
            {
                "site_name": "Test Site 2",
                "site_url": "https://testsite2.com",
                "username": "testuser2",
                "password": "pass456",
                "email": "test2@email.com"
            }
        ]
        
        added_accounts = []
        for account_data in accounts_to_add:
            add_response = client.post(
                "/api/accounts/manual",
                json=account_data,
                headers=headers
            )
            assert add_response.status_code == 200
            added_accounts.append(add_response.json())
        
        # 3. Start deletion process
        deletion_response = client.post(
            "/api/deletion/start",
            json={
                "account_ids": [acc["id"] for acc in added_accounts],
                "method": "automated"
            },
            headers=headers
        )
        assert deletion_response.status_code == 200
        deletion_data = deletion_response.json()
        assert deletion_data["tasks_created"] == 2
        
        # 4. Get deletion tasks
        tasks_response = client.get("/api/deletion/tasks", headers=headers)
        assert tasks_response.status_code == 200
        tasks = tasks_response.json()
        assert len(tasks) >= 2
        
        # 5. Simulate task failure and retry
        # Get database session to manipulate task status
        db = TestingSessionLocal()
        task = db.query(DeletionTask).first()
        if task:
            # Mark task as failed
            task.status = TaskStatus.FAILED
            task.last_error = "Network timeout"
            task.attempts = 1
            db.commit()
            
            # Retry the failed task
            retry_response = client.post(
                f"/api/deletion/retry/{task.id}",
                headers=headers
            )
            assert retry_response.status_code == 200
            retry_data = retry_response.json()
            assert retry_data["success"] is True
            assert "retry_after" in retry_data
        db.close()
        
        # 6. Get audit logs
        audit_response = client.get("/api/audit/logs", headers=headers)
        assert audit_response.status_code == 200
        audit_logs = audit_response.json()
        assert len(audit_logs) > 0
        
        # Check for specific audit actions
        actions_found = [log["action"] for log in audit_logs]
        assert "account_added" in actions_found or "manual_account_added" in actions_found
        assert "deletion_started" in actions_found or "deletion_task_created" in actions_found
        
        # 7. Get deletion status summary
        status_response = client.get("/api/deletion/status", headers=headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "total_tasks" in status_data
        assert "by_status" in status_data


class TestIntegration4_EmailConfiguration:
    """Test 4: Email configuration and GDPR template generation"""
    
    def test_email_configuration_workflow(self, client, test_user_data):
        """Test email configuration and template generation"""
        
        # 1. Register user
        register_response = client.post("/api/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        access_token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Configure email settings
        email_config = {
            "email": "user@gmail.com",
            "password": "app-specific-password",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587
        }
        
        config_response = client.post(
            "/api/settings/email",
            json=email_config,
            headers=headers
        )
        assert config_response.status_code == 200
        
        # 3. Get email settings (password should be masked)
        settings_response = client.get("/api/settings/email", headers=headers)
        assert settings_response.status_code == 200
        settings = settings_response.json()
        assert settings["email"] == email_config["email"]
        assert "password" not in settings or settings["password"] == "***"
        
        # 4. Add an account for deletion
        account_response = client.post(
            "/api/accounts/manual",
            json={
                "site_name": "TestService",
                "site_url": "https://testservice.com",
                "username": "testuser",
                "password": "testpass",
                "email": "test@testservice.com"
            },
            headers=headers
        )
        assert account_response.status_code == 200
        account_id = account_response.json()["id"]
        
        # 5. Generate GDPR deletion email template
        template_response = client.post(
            f"/api/deletion/email-template/{account_id}",
            headers=headers
        )
        assert template_response.status_code == 200
        template = template_response.json()
        
        assert "subject" in template
        assert "body" in template
        assert "GDPR" in template["body"] or "Article 17" in template["body"]
        assert "TestService" in template["body"]
        
        # 6. Get supported email providers
        providers_response = client.get("/api/settings/email/providers")
        assert providers_response.status_code == 200
        providers = providers_response.json()
        assert len(providers) > 0
        assert "gmail" in [p["name"].lower() for p in providers]


class TestIntegration5_SecurityAndValidation:
    """Test 5: Security features - password validation, account lockout, session management"""
    
    def test_security_features(self, client):
        """Test security features and validations"""
        
        # 1. Test password validation
        weak_passwords = [
            "short",  # Too short
            "NoNumbers!",  # No numbers
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoSpecialChars123",  # No special characters
        ]
        
        for weak_pass in weak_passwords:
            response = client.post(
                "/api/auth/register",
                json={
                    "username": "testuser",
                    "email": "test@test.com",
                    "password": weak_pass,
                    "session_duration_hours": 24
                }
            )
            assert response.status_code == 422  # Validation error
        
        # 2. Test account lockout
        # Register a user
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "lockouttest",
                "email": "lockout@test.com",
                "password": "ValidPass123!",
                "session_duration_hours": 24
            }
        )
        assert register_response.status_code == 200
        
        # Try to login with wrong password multiple times
        for i in range(6):  # More than lockout threshold
            login_response = client.post(
                "/api/auth/login",
                data={
                    "username": "lockouttest",
                    "password": "WrongPassword!"
                }
            )
            if i < 5:
                assert login_response.status_code == 401
            else:
                # Should be locked out
                assert login_response.status_code == 423
                assert "locked" in login_response.json()["detail"].lower()
        
        # 3. Test session duration limits
        response = client.post(
            "/api/auth/register",
            json={
                "username": "sessiontest",
                "email": "session@test.com",
                "password": "ValidPass123!",
                "session_duration_hours": 100  # Exceeds max
            }
        )
        assert response.status_code == 200
        # Should be capped at maximum (24 hours)
        assert response.json()["user"]["session_duration_hours"] <= 24
        
        # 4. Test duplicate username/email
        dup_response = client.post(
            "/api/auth/register",
            json={
                "username": "sessiontest",  # Duplicate
                "email": "another@test.com",
                "password": "ValidPass123!",
                "session_duration_hours": 24
            }
        )
        assert dup_response.status_code == 400
        assert "already registered" in dup_response.json()["detail"].lower()


class TestIntegration6_DataEncryption:
    """Test 6: Data encryption and decryption for stored passwords"""
    
    def test_password_encryption(self, client, test_user_data):
        """Test that passwords are properly encrypted and decrypted"""
        
        # 1. Register user
        register_response = client.post("/api/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        access_token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Add account with password
        test_password = "SuperSecret123!"
        account_response = client.post(
            "/api/accounts/manual",
            json={
                "site_name": "SecureService",
                "site_url": "https://secure.com",
                "username": "secureuser",
                "password": test_password,
                "email": "secure@test.com"
            },
            headers=headers
        )
        assert account_response.status_code == 200
        account_id = account_response.json()["id"]
        
        # 3. Get account details
        account_details = client.get(f"/api/accounts/{account_id}", headers=headers)
        assert account_details.status_code == 200
        account = account_details.json()
        
        # Password should be masked in response
        assert account.get("password") != test_password
        assert account.get("encrypted_password") != test_password
        
        # 4. Verify password is encrypted in database
        db = TestingSessionLocal()
        db_account = db.query(Account).filter(Account.id == account_id).first()
        assert db_account is not None
        assert db_account.encrypted_password != test_password
        assert len(db_account.encrypted_password) > len(test_password)
        
        # 5. Verify password can be decrypted correctly
        decrypted = encryption_service.decrypt_password(db_account.encrypted_password)
        assert decrypted == test_password
        db.close()


class TestIntegration7_ComprehensiveWorkflow:
    """Test 7: Comprehensive end-to-end workflow combining multiple features"""
    
    @pytest.mark.asyncio
    async def test_comprehensive_workflow(self, client, csv_file_path):
        """Test a complete realistic workflow"""
        
        # 1. User registration
        user_data = {
            "username": "comprehensiveuser",
            "email": "comprehensive@test.com",
            "password": "ComplexPass123!@#",
            "session_duration_hours": 12
        }
        register_response = client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 200
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Configure email
        email_response = client.post(
            "/api/settings/email",
            json={
                "email": "user@gmail.com",
                "password": "app-password",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587
            },
            headers=headers
        )
        assert email_response.status_code == 200
        
        # 3. Import accounts from CSV
        with open(csv_file_path, 'rb') as f:
            upload_response = client.post(
                "/api/upload/csv",
                files={"file": ("accounts.csv", f, "text/csv")},
                headers=headers
            )
        assert upload_response.status_code == 200
        
        # 4. Add manual account
        manual_response = client.post(
            "/api/accounts/manual",
            json={
                "site_name": "GitHub",
                "site_url": "https://github.com",
                "username": "developer",
                "password": "githubpass",
                "email": "dev@github.com"
            },
            headers=headers
        )
        assert manual_response.status_code == 200
        
        # 5. Get all accounts
        accounts = client.get("/api/accounts", headers=headers).json()
        assert len(accounts) == 6  # 5 from CSV + 1 manual
        
        # 6. Filter high-risk accounts
        high_risk = [acc for acc in accounts if acc.get("risk_level") in ["high", "critical"]]
        assert len(high_risk) > 0
        
        # 7. Start deletion for high-risk accounts
        deletion_response = client.post(
            "/api/deletion/start",
            json={
                "account_ids": [acc["id"] for acc in high_risk[:2]],
                "method": "email"
            },
            headers=headers
        )
        assert deletion_response.status_code == 200
        
        # 8. Get deletion progress
        progress_response = client.get("/api/deletion/tasks", headers=headers)
        assert progress_response.status_code == 200
        tasks = progress_response.json()
        assert len(tasks) >= 2
        
        # 9. Get audit trail
        audit_response = client.get("/api/audit/logs?limit=10", headers=headers)
        assert audit_response.status_code == 200
        logs = audit_response.json()
        assert len(logs) > 0
        
        # 10. Get final summary
        summary_response = client.get("/api/accounts/summary", headers=headers)
        assert summary_response.status_code == 200
        summary = summary_response.json()
        assert summary["total_accounts"] == 6
        
        # 11. Logout
        logout_response = client.post("/api/auth/logout", headers=headers)
        assert logout_response.status_code == 200
        
        # 12. Verify token is invalidated
        invalid_response = client.get("/api/accounts", headers=headers)
        assert invalid_response.status_code == 401


@pytest.mark.integration
def test_run_all_integrations():
    """Marker test to run all integration tests"""
    pass