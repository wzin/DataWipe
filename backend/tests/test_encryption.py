import pytest
import os
from services.encryption_service import EncryptionService, encryption_service


class TestEncryptionService:
    
    def test_encrypt_decrypt_password(self):
        """Test encrypting and decrypting a password"""
        original_password = "MySecurePassword123!@#"
        
        # Encrypt the password
        encrypted = encryption_service.encrypt_password(original_password)
        
        # Verify it's encrypted (not the same as original)
        assert encrypted != original_password
        assert len(encrypted) > 0
        
        # Decrypt the password
        decrypted = encryption_service.decrypt_password(encrypted)
        
        # Verify it matches the original
        assert decrypted == original_password
    
    def test_encrypt_empty_password(self):
        """Test encrypting an empty password"""
        encrypted = encryption_service.encrypt_password("")
        assert encrypted == ""
        
        decrypted = encryption_service.decrypt_password("")
        assert decrypted == ""
    
    def test_decrypt_invalid_data(self):
        """Test decrypting invalid data"""
        result = encryption_service.decrypt_password("invalid_encrypted_data")
        assert result is None
    
    def test_encrypt_decrypt_unicode(self):
        """Test encrypting and decrypting Unicode characters"""
        original = "Password with émojis 🔐🔑 and spéciàl çhars"
        
        encrypted = encryption_service.encrypt_password(original)
        decrypted = encryption_service.decrypt_password(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_decrypt_long_password(self):
        """Test encrypting and decrypting a very long password"""
        original = "A" * 1000 + "B" * 1000 + "C" * 1000
        
        encrypted = encryption_service.encrypt_password(original)
        decrypted = encryption_service.decrypt_password(encrypted)
        
        assert decrypted == original
    
    def test_different_passwords_different_encryption(self):
        """Test that different passwords produce different encrypted values"""
        password1 = "Password1"
        password2 = "Password2"
        
        encrypted1 = encryption_service.encrypt_password(password1)
        encrypted2 = encryption_service.encrypt_password(password2)
        
        assert encrypted1 != encrypted2
    
    def test_same_password_different_encryption_each_time(self):
        """Test that the same password produces different encrypted values each time (due to IV)"""
        password = "SamePassword123"
        
        encrypted1 = encryption_service.encrypt_password(password)
        encrypted2 = encryption_service.encrypt_password(password)
        
        # Fernet uses a different IV each time, so encrypted values should differ
        assert encrypted1 != encrypted2
        
        # But both should decrypt to the same value
        assert encryption_service.decrypt_password(encrypted1) == password
        assert encryption_service.decrypt_password(encrypted2) == password
    
    def test_encrypt_decrypt_data(self):
        """Test generic data encryption and decryption"""
        original_data = "Some sensitive data that needs encryption"
        
        encrypted = encryption_service.encrypt_data(original_data)
        assert encrypted != original_data
        
        decrypted = encryption_service.decrypt_data(encrypted)
        assert decrypted == original_data
    
    def test_key_rotation(self):
        """Test rotating encryption keys"""
        # Create a new service with a specific key
        old_key = EncryptionService.generate_encryption_key()
        new_key = EncryptionService.generate_encryption_key()
        
        # Create service with old key
        old_service = EncryptionService()
        old_service.fernet = old_service._get_or_create_fernet()
        
        # Encrypt with old key
        original_data = "Sensitive data to rotate"
        encrypted_with_old = old_service.encrypt_data(original_data)
        
        # Rotate to new key
        rotated_data = encryption_service.rotate_encryption_key(
            old_key, new_key, encrypted_with_old
        )
        
        # Create service with new key and decrypt
        new_service = EncryptionService()
        os.environ["ENCRYPTION_KEY"] = new_key
        new_service.fernet = new_service._get_or_create_fernet()
        
        decrypted = new_service.decrypt_data(rotated_data)
        assert decrypted == original_data
    
    def test_generate_encryption_key(self):
        """Test generating new encryption keys"""
        key1 = EncryptionService.generate_encryption_key()
        key2 = EncryptionService.generate_encryption_key()
        
        # Keys should be different
        assert key1 != key2
        
        # Keys should be valid base64
        assert len(key1) == 44  # Fernet keys are 44 characters
        assert len(key2) == 44
    
    def test_encryption_with_environment_key(self, monkeypatch):
        """Test using encryption key from environment variable"""
        test_key = EncryptionService.generate_encryption_key()
        monkeypatch.setenv("ENCRYPTION_KEY", test_key)
        
        # Create new service that should use the env key
        service = EncryptionService()
        
        password = "TestPassword123"
        encrypted = service.encrypt_password(password)
        decrypted = service.decrypt_password(encrypted)
        
        assert decrypted == password


class TestEncryptionIntegration:
    
    def test_csv_parser_encryption_integration(self):
        """Test that CSV parser properly encrypts passwords"""
        from services.csv_parser import CSVParser
        from models import Account
        
        parser = CSVParser()
        
        # Create a mock account
        account = Account(
            user_id=1,
            site_name="Test Site",
            site_url="https://test.com",
            username="testuser",
            encrypted_password=encryption_service.encrypt_password("TestPassword123"),
            email="test@example.com"
        )
        
        # Get decrypted password
        decrypted = parser.get_decrypted_password(account)
        assert decrypted == "TestPassword123"
    
    def test_password_remains_encrypted_in_database(self):
        """Test that passwords are never stored in plain text"""
        password = "PlainTextPassword"
        encrypted = encryption_service.encrypt_password(password)
        
        # The encrypted password should never contain the original
        assert password not in encrypted
        assert "PlainText" not in encrypted
        assert len(encrypted) > len(password) * 2  # Encrypted is much longer


if __name__ == "__main__":
    pytest.main([__file__, "-v"])