import pytest
from fastapi.testclient import TestClient
import json
import io
from unittest.mock import patch, MagicMock

from models import Account, UserSettings, DeletionTask


class TestUploadAPI:
    """Test upload API endpoints"""
    
    def test_upload_csv_success(self, client, mock_llm_response):
        """Test successful CSV upload"""
        csv_content = """name,url,username,password,notes
Gmail,https://accounts.google.com,test@gmail.com,password123,Email account"""
        
        files = {
            'file': ('test.csv', io.StringIO(csv_content), 'text/csv')
        }
        
        with patch('services.llm_service.LLMService.discover_accounts') as mock_discover:
            mock_discover.return_value = [mock_llm_response]
            
            response = client.post("/api/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert "accounts_discovered" in data
            assert data["accounts_discovered"] == 1
    
    def test_upload_invalid_file_type(self, client):
        """Test upload with invalid file type"""
        files = {
            'file': ('test.txt', io.StringIO('invalid content'), 'text/plain')
        }
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 400
        assert "Only CSV files are supported" in response.json()["detail"]
    
    def test_get_supported_formats(self, client):
        """Test get supported formats endpoint"""
        response = client.get("/api/upload/formats")
        
        assert response.status_code == 200
        data = response.json()
        assert "supported_formats" in data
        assert "csv" in data["supported_formats"]
        assert "expected_columns" in data


class TestAccountsAPI:
    """Test accounts API endpoints"""
    
    def test_get_accounts_empty(self, client):
        """Test getting accounts when none exist"""
        response = client.get("/api/accounts")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_accounts_with_data(self, client, sample_account):
        """Test getting accounts with existing data"""
        response = client.get("/api/accounts")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["site_name"] == "Test Site"
        assert data[0]["username"] == "testuser"
    
    def test_get_account_by_id(self, client, sample_account):
        """Test getting specific account by ID"""
        response = client.get(f"/api/accounts/{sample_account.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["site_name"] == "Test Site"
        assert data["username"] == "testuser"
    
    def test_get_account_not_found(self, client):
        """Test getting non-existent account"""
        response = client.get("/api/accounts/999")
        
        assert response.status_code == 404
        assert "Account not found" in response.json()["detail"]
    
    def test_update_account_status(self, client, sample_account):
        """Test updating account status"""
        response = client.put(
            f"/api/accounts/{sample_account.id}",
            json={"status": "pending"}
        )
        
        assert response.status_code == 200
        
        # Verify status was updated
        response = client.get(f"/api/accounts/{sample_account.id}")
        assert response.json()["status"] == "pending"
    
    def test_bulk_select_accounts(self, client, sample_account):
        """Test bulk selecting accounts"""
        response = client.post(
            "/api/accounts/bulk-select",
            json={"account_ids": [sample_account.id], "action": "select"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully selected" in data["message"]
    
    def test_delete_account(self, client, sample_account):
        """Test deleting account"""
        response = client.delete(f"/api/accounts/{sample_account.id}")
        
        assert response.status_code == 200
        
        # Verify account was deleted
        response = client.get(f"/api/accounts/{sample_account.id}")
        assert response.status_code == 404
    
    def test_get_accounts_summary(self, client, sample_account):
        """Test getting accounts summary"""
        response = client.get("/api/accounts/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_accounts" in data
        assert "by_status" in data
        assert data["total_accounts"] == 1


class TestSettingsAPI:
    """Test settings API endpoints"""
    
    def test_get_email_settings_not_configured(self, client):
        """Test getting email settings when not configured"""
        response = client.get("/api/settings/email")
        
        assert response.status_code == 404
        assert "Email settings not configured" in response.json()["detail"]
    
    @patch('services.email_service.EmailService.test_email_configuration')
    def test_configure_email_success(self, mock_test, client):
        """Test successful email configuration"""
        mock_test.return_value = {
            'success': True,
            'provider': 'gmail.com',
            'app_password_required': True
        }
        
        response = client.post(
            "/api/settings/email",
            json={
                "email": "test@gmail.com",
                "password": "app_password",
                "name": "Test User"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@gmail.com"
        assert data["provider"] == "gmail.com"
    
    @patch('services.email_service.EmailService.test_email_configuration')
    def test_configure_email_invalid(self, mock_test, client):
        """Test email configuration with invalid credentials"""
        mock_test.return_value = {
            'success': False,
            'error': 'Authentication failed'
        }
        
        response = client.post(
            "/api/settings/email",
            json={
                "email": "test@gmail.com",
                "password": "wrong_password"
            }
        )
        
        assert response.status_code == 400
        assert "Email configuration failed" in response.json()["detail"]
    
    def test_get_supported_email_providers(self, client):
        """Test getting supported email providers"""
        response = client.get("/api/settings/email/providers")
        
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert len(data["providers"]) > 0
        
        # Check Gmail provider
        gmail_provider = next(p for p in data["providers"] if p["domain"] == "gmail.com")
        assert gmail_provider["app_password_required"] is True


class TestDeletionAPI:
    """Test deletion API endpoints"""
    
    def test_start_deletion_no_accounts(self, client):
        """Test starting deletion with no accounts"""
        response = client.post(
            "/api/deletion/start",
            json={"account_ids": [999]}
        )
        
        assert response.status_code == 400
        assert "Some account IDs are invalid" in response.json()["detail"]
    
    @patch('services.deletion_service.DeletionService.process_tasks')
    def test_start_deletion_success(self, mock_process, client, sample_account):
        """Test successful deletion start"""
        mock_process.return_value = True
        
        response = client.post(
            "/api/deletion/start",
            json={"account_ids": [sample_account.id]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Started deletion process" in data["message"]
        assert len(data["task_ids"]) == 1
    
    def test_get_deletion_tasks(self, client):
        """Test getting deletion tasks"""
        response = client.get("/api/deletion/tasks")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAuditAPI:
    """Test audit API endpoints"""
    
    def test_get_audit_logs(self, client):
        """Test getting audit logs"""
        response = client.get("/api/audit")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_audit_actions(self, client):
        """Test getting audit actions"""
        response = client.get("/api/audit/actions")
        
        assert response.status_code == 200
        data = response.json()
        assert "actions" in data
        assert isinstance(data["actions"], list)
    
    def test_get_audit_summary(self, client):
        """Test getting audit summary"""
        response = client.get("/api/audit/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_logs" in data
        assert "recent_activity" in data
        assert "actions" in data


class TestHealthAPI:
    """Test health and stats endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_get_stats(self, client):
        """Test getting system stats"""
        response = client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_accounts" in data
        assert "completed_deletions" in data
        assert "pending_deletions" in data
        assert "failed_deletions" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "GDPR Account Deletion Assistant" in data["message"]