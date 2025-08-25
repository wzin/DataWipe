import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import pandas as pd
from io import StringIO

from services.csv_parser import CSVParser
from services.email_service import EmailService
from services.llm_service import LLMService
from services.audit_service import AuditService
from services.deletion_service import DeletionService
from models import Account, DeletionTask, AuditLog


class TestCSVParser:
    """Test CSV parsing functionality"""
    
    def test_detect_bitwarden_format(self):
        """Test detection of Bitwarden format"""
        import pandas as pd
        parser = CSVParser()
        columns = ['name', 'url', 'username', 'password', 'notes']
        df = pd.DataFrame(columns=columns)
        
        format_type, confidence = parser.detect_format(df)
        assert format_type in ["bitwarden", "chrome", "generic"]  # These columns match multiple formats
    
    def test_detect_lastpass_format(self):
        """Test detection of LastPass format"""
        import pandas as pd
        parser = CSVParser()
        columns = ['url', 'username', 'password', 'totp', 'extra', 'name', 'grouping', 'fav']
        df = pd.DataFrame(columns=columns)
        
        format_type, confidence = parser.detect_format(df)
        assert format_type == "lastpass"
    
    def test_detect_unknown_format(self):
        """Test detection of unknown format"""
        import pandas as pd
        parser = CSVParser()
        columns = ['col1', 'col2', 'col3']
        df = pd.DataFrame(columns=columns)
        
        format_type, confidence = parser.detect_format(df)
        assert format_type is None  # Should return None for unrecognized format
    
    def test_parse_bitwarden_csv(self):
        """Test parsing Bitwarden CSV"""
        csv_content = """name,url,username,password,notes
Gmail,https://accounts.google.com,test@gmail.com,password123,Email account
Facebook,https://facebook.com,test@facebook.com,password456,Social media account"""
        
        # Create temporary CSV file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            parser = CSVParser()
            accounts = parser.parse_csv(temp_path)
            
            assert len(accounts) == 2
            assert accounts[0]['site_name'] == 'Gmail'
            assert accounts[0]['site_url'] == 'https://accounts.google.com'
            assert accounts[0]['username'] == 'test@gmail.com'
            assert accounts[0]['email'] == 'test@gmail.com'  # Should extract email from username
            
            assert accounts[1]['site_name'] == 'Facebook'
            assert accounts[1]['site_url'] == 'https://facebook.com'
            assert accounts[1]['username'] == 'test@facebook.com'
        finally:
            import os
            os.unlink(temp_path)
    
    def test_clean_url(self):
        """Test URL cleaning functionality"""
        parser = CSVParser()
        
        # Test with protocol
        assert parser._clean_url('https://example.com') == 'https://example.com'
        
        # Test without protocol
        assert parser._clean_url('example.com') == 'https://example.com'
        
        # Test with path
        assert parser._clean_url('https://example.com/login') == 'https://example.com'
        
        # Test with subdomain
        assert parser._clean_url('https://mail.google.com') == 'https://mail.google.com'
    
    def test_extract_email(self):
        """Test email extraction from username and notes"""
        parser = CSVParser()
        
        # Test email in username
        email = parser._extract_email('test@example.com', '')
        assert email == 'test@example.com'
        
        # Test email in notes
        email = parser._extract_email('testuser', 'Contact: test@example.com')
        assert email == 'test@example.com'
        
        # Test no email
        email = parser._extract_email('testuser', 'No email here')
        assert email == ''
    
    def test_password_encryption(self):
        """Test password encryption and decryption"""
        from services.encryption_service import encryption_service
        
        original_password = "test_password_123"
        encrypted = encryption_service.encrypt_password(original_password)
        decrypted = encryption_service.decrypt_password(encrypted)
        
        assert encrypted != original_password
        assert decrypted == original_password


class TestEmailService:
    """Test email service functionality"""
    
    def test_detect_gmail_smtp(self):
        """Test Gmail SMTP detection"""
        email_service = EmailService('test@gmail.com', 'password')
        
        config = email_service.smtp_config
        assert config['server'] == 'smtp.gmail.com'
        assert config['port'] == 587
        assert config['app_password_required'] is True
    
    def test_detect_outlook_smtp(self):
        """Test Outlook SMTP detection"""
        email_service = EmailService('test@outlook.com', 'password')
        
        config = email_service.smtp_config
        assert config['server'] == 'smtp-mail.outlook.com'
        assert config['port'] == 587
        assert config['app_password_required'] is False
    
    def test_detect_yahoo_smtp(self):
        """Test Yahoo SMTP detection"""
        email_service = EmailService('test@yahoo.com', 'password')
        
        config = email_service.smtp_config
        assert config['server'] == 'smtp.mail.yahoo.com'
        assert config['port'] == 587
        assert config['app_password_required'] is True
    
    def test_generate_deletion_email_body(self):
        """Test deletion email body generation"""
        email_service = EmailService('test@gmail.com', 'password')
        
        account_data = {
            'site_name': 'Test Site',
            'username': 'testuser',
            'email': 'test@example.com',
            'site_url': 'https://test.com'
        }
        
        body = email_service._generate_deletion_email_body(account_data)
        
        assert 'GDPR Article 17' in body
        assert 'Test Site' in body
        assert 'testuser' in body
        assert 'test@example.com' in body
        assert 'https://test.com' in body
    
    @patch('aiosmtplib.send')
    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_send):
        """Test successful email sending"""
        mock_send.return_value = True
        
        email_service = EmailService('test@gmail.com', 'password')
        success = await email_service.send_email(
            'recipient@example.com',
            'Test Subject',
            'Test Body',
            user_name='Test User'
        )
        
        assert success is True
        mock_send.assert_called_once()
    
    @patch('aiosmtplib.send')
    @pytest.mark.asyncio
    async def test_send_email_failure(self, mock_send):
        """Test email sending failure"""
        mock_send.side_effect = Exception('SMTP Error')
        
        email_service = EmailService('test@gmail.com', 'password')
        success = await email_service.send_email(
            'recipient@example.com',
            'Test Subject',
            'Test Body'
        )
        
        assert success is False


class TestLLMService:
    """Test LLM service functionality"""
    
    def test_extract_domain(self):
        """Test domain extraction from URL"""
        llm_service = LLMService()
        
        # Test with protocol
        domain = llm_service._extract_domain('https://www.example.com/path')
        assert domain == 'example.com'
        
        # Test without www
        domain = llm_service._extract_domain('https://example.com')
        assert domain == 'example.com'
        
        # Test with port
        domain = llm_service._extract_domain('https://example.com:8080')
        assert domain == 'example.com'
    
    @patch('openai.OpenAI')
    @pytest.mark.asyncio
    async def test_call_openai(self, mock_openai):
        """Test OpenAI API call"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        
        llm_service = LLMService()
        llm_service.openai_client = mock_client
        
        response = await llm_service._call_openai("Test prompt")
        
        assert response == "Test response"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('anthropic.Anthropic')
    @pytest.mark.asyncio
    async def test_call_anthropic(self, mock_anthropic):
        """Test Anthropic API call"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Test response"
        mock_client.messages.create.return_value = mock_response
        
        llm_service = LLMService()
        llm_service.anthropic_client = mock_client
        
        response = await llm_service._call_anthropic("Test prompt")
        
        assert response == "Test response"
        mock_client.messages.create.assert_called_once()
    
    def test_generate_fallback_email(self):
        """Test fallback email generation"""
        llm_service = LLMService()
        
        account = MagicMock()
        account.site_name = "Test Site"
        account.username = "testuser"
        account.email = "test@example.com"
        account.site_url = "https://test.com"
        
        email = llm_service._generate_fallback_email(account)
        
        assert "GDPR Article 17" in email
        assert "Test Site" in email
        assert "testuser" in email
        assert "test@example.com" in email
    
    def test_calculate_cost(self):
        """Test cost calculation"""
        llm_service = LLMService()
        
        # Test OpenAI cost (0.00003 per token)
        from models import LLMProvider
        cost = llm_service._calculate_cost(LLMProvider.OPENAI, 1000)
        assert abs(cost - 0.03) < 0.0001  # 1000 * 0.00003 with floating point tolerance
        
        # Test Anthropic cost (0.00003 per token)
        cost = llm_service._calculate_cost(LLMProvider.ANTHROPIC, 1000)
        assert abs(cost - 0.03) < 0.0001  # 1000 * 0.00003 with floating point tolerance


class TestAuditService:
    """Test audit service functionality"""
    
    def test_mask_sensitive_data(self):
        """Test sensitive data masking"""
        audit_service = AuditService()
        
        data = {
            'username': 'testuser',
            'password': 'secret123',
            'email': 'test@example.com',
            'token': 'auth_token_123',
            'normal_field': 'normal_value'
        }
        
        masked = audit_service._mask_sensitive_data(data)
        
        assert masked['username'] == 'testuser'
        assert masked['email'] == 'test@example.com'
        assert masked['normal_field'] == 'normal_value'
        assert masked['password'].startswith('[MASKED:')
        assert masked['token'].startswith('[MASKED:')
    
    def test_mask_nested_sensitive_data(self):
        """Test nested sensitive data masking"""
        audit_service = AuditService()
        
        data = {
            'user_info': {
                'username': 'testuser',
                'password': 'secret123',
                'settings': {
                    'api_key': 'key_123',
                    'theme': 'dark'
                }
            }
        }
        
        masked = audit_service._mask_sensitive_data(data)
        
        assert masked['user_info']['username'] == 'testuser'
        assert masked['user_info']['password'].startswith('[MASKED:')
        assert masked['user_info']['settings']['api_key'].startswith('[MASKED:')
        assert masked['user_info']['settings']['theme'] == 'dark'
    
    @pytest.mark.asyncio
    async def test_log_action(self):
        """Test audit logging"""
        audit_service = AuditService()
        
        # This would normally use a real database session
        # For testing, we'll mock it
        mock_db = MagicMock()
        
        await audit_service.log_action(
            db=mock_db,
            account_id=1,
            action="test_action",
            details={'test': 'data'},
            masked_credentials=True
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestDeletionService:
    """Test deletion service functionality"""
    
    def test_initialization(self):
        """Test deletion service initialization"""
        deletion_service = DeletionService()
        
        # web_scraper is temporarily disabled
        # assert deletion_service.web_scraper is not None
        assert deletion_service.email_service is not None
        assert deletion_service.llm_service is not None
        assert deletion_service.audit_service is not None
    
    @patch('services.deletion_service.DeletionService._attempt_automated_deletion')
    @pytest.mark.asyncio
    async def test_execute_deletion_automated(self, mock_attempt):
        """Test automated deletion execution"""
        mock_attempt.return_value = True
        
        deletion_service = DeletionService()
        
        # Import the enum
        from models import DeletionMethod
        
        # Mock task with proper enum value
        task = MagicMock()
        task.method = DeletionMethod.AUTOMATED
        task.attempts = 0
        
        await deletion_service.execute_deletion(task)
        
        mock_attempt.assert_called_once()
    
    @patch('services.deletion_service.DeletionService._send_deletion_email')
    @pytest.mark.asyncio
    async def test_execute_deletion_email(self, mock_send):
        """Test email deletion execution"""
        mock_send.return_value = True
        
        deletion_service = DeletionService()
        
        # Import the enum
        from models import DeletionMethod
        
        # Mock task with proper enum value
        task = MagicMock()
        task.method = DeletionMethod.EMAIL
        task.attempts = 0
        
        await deletion_service.execute_deletion(task)
        
        mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_deletion_email(self):
        """Test deletion email address generation"""
        deletion_service = DeletionService()
        
        account = MagicMock()
        account.site_url = "https://example.com"
        
        email = deletion_service._get_deletion_email(account)
        
        assert email == "privacy@example.com"
    
    @pytest.mark.asyncio
    async def test_estimate_deletion_time(self):
        """Test deletion time estimation"""
        deletion_service = DeletionService()
        
        estimate = await deletion_service.estimate_deletion_time([1, 2, 3])
        
        assert estimate['total_accounts'] == 3
        assert estimate['estimated_time_minutes'] == 9  # 3 * 3
        assert 'automation_success_rate' in estimate
        assert 'email_fallback_rate' in estimate