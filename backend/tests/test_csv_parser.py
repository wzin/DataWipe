import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from services.csv_parser import CSVParser
from models import Account, AccountStatus


class TestCSVParser:
    """Test suite for CSV parser with format auto-detection"""
    
    @pytest.fixture
    def parser(self):
        """Create CSVParser instance"""
        return CSVParser()
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock(spec=Session)
    
    def create_temp_csv(self, data, columns):
        """Helper to create temporary CSV file"""
        df = pd.DataFrame(data, columns=columns)
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        df.to_csv(temp_file.name, index=False)
        temp_file.close()
        return temp_file.name
    
    def test_detect_bitwarden_format(self, parser):
        """Test detection of Bitwarden format"""
        columns = ['folder', 'favorite', 'type', 'name', 'notes', 'fields', 
                   'reprompt', 'login_uri', 'login_username', 'login_password', 'login_totp']
        data = [['Personal', '0', 'login', 'Google', '', '', '0', 
                'https://accounts.google.com', 'user@gmail.com', 'password123', '']]
        
        temp_file = self.create_temp_csv(data, columns)
        try:
            df = pd.read_csv(temp_file)
            format_name, confidence = parser.detect_format(df)
            
            assert format_name == 'bitwarden'
            assert confidence > 0.8
        finally:
            os.unlink(temp_file)
    
    def test_detect_lastpass_format(self, parser):
        """Test detection of LastPass format"""
        columns = ['url', 'username', 'password', 'totp', 'extra', 'name', 'grouping', 'fav']
        data = [['https://facebook.com', 'user@email.com', 'pass123', '', 
                'notes here', 'Facebook', 'Social', '0']]
        
        temp_file = self.create_temp_csv(data, columns)
        try:
            df = pd.read_csv(temp_file)
            format_name, confidence = parser.detect_format(df)
            
            assert format_name == 'lastpass'
            assert confidence > 0.8
        finally:
            os.unlink(temp_file)
    
    def test_detect_1password_format(self, parser):
        """Test detection of 1Password format"""
        columns = ['title', 'url', 'username', 'password', 'notes', 'type', 'category']
        data = [['Twitter', 'https://twitter.com', '@username', 'securepass', 
                'My Twitter account', 'Login', 'Social']]
        
        temp_file = self.create_temp_csv(data, columns)
        try:
            df = pd.read_csv(temp_file)
            format_name, confidence = parser.detect_format(df)
            
            assert format_name == '1password'
            assert confidence > 0.8
        finally:
            os.unlink(temp_file)
    
    def test_detect_chrome_format(self, parser):
        """Test detection of Chrome passwords format"""
        columns = ['name', 'url', 'username', 'password']
        data = [['amazon.com', 'https://www.amazon.com', 'shopper@email.com', 'amazonpass']]
        
        temp_file = self.create_temp_csv(data, columns)
        try:
            df = pd.read_csv(temp_file)
            format_name, confidence = parser.detect_format(df)
            
            assert format_name == 'chrome'
            assert confidence > 0.8
        finally:
            os.unlink(temp_file)
    
    def test_detect_keepass_format(self, parser):
        """Test detection of KeePass format"""
        columns = ['group', 'title', 'username', 'password', 'url', 'notes']
        data = [['Internet', 'LinkedIn', 'professional@email.com', 'linkedpass',
                'https://linkedin.com', 'Professional network']]
        
        temp_file = self.create_temp_csv(data, columns)
        try:
            df = pd.read_csv(temp_file)
            format_name, confidence = parser.detect_format(df)
            
            assert format_name == 'keepass'
            assert confidence > 0.8
        finally:
            os.unlink(temp_file)
    
    def test_detect_generic_format(self, parser):
        """Test detection of generic/unknown format"""
        columns = ['website', 'user', 'pass', 'description']
        data = [['github.com', 'developer', 'gitpass', 'Code repository']]
        
        temp_file = self.create_temp_csv(data, columns)
        try:
            df = pd.read_csv(temp_file)
            format_name, confidence = parser.detect_format(df)
            
            assert format_name == 'generic'
            assert confidence == 0.5
        finally:
            os.unlink(temp_file)
    
    def test_parse_bitwarden_csv(self, parser):
        """Test parsing Bitwarden CSV export"""
        columns = ['folder', 'favorite', 'type', 'name', 'notes', 'fields', 
                   'reprompt', 'login_uri', 'login_username', 'login_password', 'login_totp']
        data = [
            ['Personal', '0', 'login', 'Google', 'Main account', '', '0', 
             'https://accounts.google.com', 'user@gmail.com', 'password123', ''],
            ['Work', '1', 'login', 'Slack', '', '', '0',
             'https://slack.com', 'worker@company.com', 'slackpass', ''],
            ['', '0', 'note', 'Secure Note', 'This is a note', '', '0', '', '', '', '']
        ]
        
        temp_file = self.create_temp_csv(data, columns)
        try:
            accounts = parser.parse_csv(temp_file)
            
            assert len(accounts) == 2  # Should skip the secure note
            assert accounts[0]['site_name'] == 'Google'
            assert accounts[0]['site_url'] == 'https://accounts.google.com'
            assert accounts[0]['username'] == 'user@gmail.com'
            assert accounts[0]['password'] == 'password123'
            assert accounts[0]['email'] == 'user@gmail.com'
            
            assert accounts[1]['site_name'] == 'Slack'
            assert accounts[1]['username'] == 'worker@company.com'
        finally:
            os.unlink(temp_file)
    
    def test_parse_chrome_csv(self, parser):
        """Test parsing Chrome passwords CSV"""
        columns = ['name', 'url', 'username', 'password']
        data = [
            ['amazon.com', 'https://www.amazon.com', 'shopper@email.com', 'amazonpass'],
            ['netflix.com', 'https://www.netflix.com', 'viewer@email.com', 'netflixpass'],
            ['', '', '', '']  # Empty row
        ]
        
        temp_file = self.create_temp_csv(data, columns)
        try:
            accounts = parser.parse_csv(temp_file)
            
            assert len(accounts) == 2  # Should skip empty row
            assert accounts[0]['site_name'] == 'amazon.com'
            assert accounts[0]['site_url'] == 'https://www.amazon.com'
            assert accounts[0]['username'] == 'shopper@email.com'
            assert accounts[0]['email'] == 'shopper@email.com'
            
            assert accounts[1]['site_name'] == 'netflix.com'
            assert accounts[1]['username'] == 'viewer@email.com'
        finally:
            os.unlink(temp_file)
    
    def test_parse_generic_csv(self, parser):
        """Test parsing generic/unknown CSV format"""
        columns = ['website', 'user_name', 'password_field', 'notes']
        data = [
            ['github.com', 'developer', 'gitpass', 'Version control'],
            ['stackoverflow.com', 'coder@email.com', 'stackpass', 'Q&A site']
        ]
        
        temp_file = self.create_temp_csv(data, columns)
        try:
            accounts = parser.parse_csv(temp_file)
            
            assert len(accounts) == 2
            assert accounts[0]['site_name'] == 'Github'
            assert accounts[0]['site_url'] == 'https://github.com'
            assert accounts[0]['username'] == 'developer'
            assert accounts[0]['password'] == 'gitpass'
            
            assert accounts[1]['site_name'] == 'Stackoverflow'
            assert accounts[1]['email'] == 'coder@email.com'
        finally:
            os.unlink(temp_file)
    
    def test_extract_email_from_username(self, parser):
        """Test email extraction from username field"""
        email = parser._extract_email('user@example.com', '')
        assert email == 'user@example.com'
        
        email = parser._extract_email('username', 'Contact: admin@site.com')
        assert email == 'admin@site.com'
        
        email = parser._extract_email('user123', 'No email here')
        assert email == ''
    
    def test_extract_site_name_from_url(self, parser):
        """Test site name extraction from URL"""
        assert parser._extract_site_name('https://www.google.com') == 'Google'
        assert parser._extract_site_name('http://facebook.com/profile') == 'Facebook'
        assert parser._extract_site_name('netflix.com') == 'Netflix'
        assert parser._extract_site_name('') == 'Unknown'
    
    def test_clean_url(self, parser):
        """Test URL cleaning and normalization"""
        assert parser._clean_url('google.com') == 'https://google.com'
        assert parser._clean_url('http://example.com/path') == 'http://example.com'
        assert parser._clean_url('https://www.site.com/page?param=1') == 'https://www.site.com'
        assert parser._clean_url('nan') == ''
        assert parser._clean_url('') == ''
    
    def test_skip_non_login_items(self, parser):
        """Test skipping non-login items like credit cards and secure notes"""
        assert parser._is_non_login_item('Credit Card', '', 'password') == True
        assert parser._is_non_login_item('Secure Note', '', 'password') == True
        assert parser._is_non_login_item('', 'ssh://server.com', 'password') == True
        assert parser._is_non_login_item('Google', 'https://google.com', 'password') == False
    
    @patch('services.csv_parser.encryption_service')
    def test_save_account_new(self, mock_encryption, parser, mock_db):
        """Test saving new account to database"""
        mock_encryption.encrypt_password.return_value = 'encrypted_pass'
        
        account_data = {
            'site_name': 'TestSite',
            'site_url': 'https://testsite.com',
            'username': 'testuser',
            'password': 'testpass',
            'email': 'test@email.com'
        }
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = parser.save_account(mock_db, account_data, user_id=1)
        
        mock_encryption.encrypt_password.assert_called_once_with('testpass')
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        mock_db.refresh.assert_called_once()
    
    @patch('services.csv_parser.encryption_service')
    def test_save_account_existing(self, mock_encryption, parser, mock_db):
        """Test updating existing account"""
        mock_encryption.encrypt_password.return_value = 'encrypted_pass'
        
        existing_account = Mock(spec=Account)
        mock_db.query.return_value.filter.return_value.first.return_value = existing_account
        
        account_data = {
            'site_name': 'UpdatedSite',
            'site_url': 'https://testsite.com',
            'username': 'testuser',
            'password': 'newpass',
            'email': 'new@email.com'
        }
        
        result = parser.save_account(mock_db, account_data, user_id=1)
        
        assert existing_account.site_name == 'UpdatedSite'
        assert existing_account.email == 'new@email.com'
        mock_encryption.encrypt_password.assert_called_once_with('newpass')
        mock_db.commit.assert_called()
    
    def test_handle_different_encodings(self, parser):
        """Test handling different file encodings"""
        # Create CSV with UTF-8 BOM
        columns = ['name', 'url', 'username', 'password']
        data = [['Café', 'https://café.com', 'user', 'pass']]
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', 
                                                encoding='utf-8-sig', delete=False)
        df = pd.DataFrame(data, columns=columns)
        df.to_csv(temp_file.name, index=False)
        temp_file.close()
        
        try:
            accounts = parser.parse_csv(temp_file.name)
            assert len(accounts) == 1
            assert accounts[0]['site_name'] == 'Café'
        finally:
            os.unlink(temp_file.name)
    
    def test_guess_url_from_site_name(self, parser):
        """Test URL guessing from site name"""
        assert parser._guess_url('Google') == 'https://accounts.google.com'
        assert parser._guess_url('Facebook') == 'https://www.facebook.com'
        assert parser._guess_url('UnknownSite') == 'https://www.unknownsite.com'
        assert parser._guess_url('') == ''
    
    def test_get_supported_formats(self, parser):
        """Test getting list of supported formats"""
        formats = parser.get_supported_formats()
        
        assert 'bitwarden' in formats
        assert 'lastpass' in formats
        assert '1password' in formats
        assert 'chrome' in formats
        assert 'keepass' in formats
        
        assert formats['bitwarden']['name'] == 'Bitwarden'
        assert isinstance(formats['bitwarden']['columns'], list)
    
    def test_parse_nordpass_with_extra_fields(self, parser):
        """Test parsing NordPass CSV with credit card fields"""
        columns = ['name', 'url', 'username', 'password', 'note', 'cardholdername', 
                   'cardnumber', 'cvc', 'expirydate', 'zipcode', 'folder', 
                   'full_name', 'phone_number', 'email', 'address1', 'address2', 
                   'city', 'country', 'state']
        
        data = [
            ['GitHub', 'https://github.com', 'dev', 'pass123', 'Work account',
             '', '', '', '', '', 'Work', '', '', 'dev@company.com', '', '', '', '', ''],
            ['Visa Card', '', '', '', 'Primary card', 'John Doe', '4111111111111111',
             '123', '12/25', '12345', 'Finance', '', '', '', '', '', '', '', '']
        ]
        
        temp_file = self.create_temp_csv(data, columns)
        try:
            accounts = parser.parse_csv(temp_file)
            
            assert len(accounts) == 1  # Should skip credit card
            assert accounts[0]['site_name'] == 'GitHub'
            assert accounts[0]['email'] == 'dev@company.com'
        finally:
            os.unlink(temp_file)
    
    def test_invalid_csv_file(self, parser):
        """Test handling invalid CSV file"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write("This is not a valid CSV\n")
        temp_file.write("Just random text\n")
        temp_file.close()
        
        try:
            with pytest.raises(ValueError, match="Could not detect CSV format"):
                parser.parse_csv(temp_file.name)
        finally:
            os.unlink(temp_file.name)
    
    def test_empty_csv_file(self, parser):
        """Test handling empty CSV file"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.close()
        
        try:
            with pytest.raises(ValueError):
                parser.parse_csv(temp_file.name)
        finally:
            os.unlink(temp_file.name)