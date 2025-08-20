import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional

class EncryptionService:
    """Service for encrypting and decrypting sensitive data like account passwords"""
    
    def __init__(self):
        self.fernet = self._get_or_create_fernet()
    
    def _get_or_create_fernet(self) -> Fernet:
        """Get or create Fernet encryption instance"""
        # Get encryption key from environment or generate one
        encryption_key = os.getenv("ENCRYPTION_KEY")
        
        if not encryption_key:
            # Generate a new key if none exists (for development)
            # In production, this should be set as an environment variable
            encryption_key = Fernet.generate_key().decode()
            print(f"WARNING: Generated new encryption key. Set ENCRYPTION_KEY={encryption_key} in production")
        
        # Ensure the key is properly formatted
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        # Validate the key format
        try:
            fernet = Fernet(encryption_key)
        except Exception as e:
            # If the key is invalid, generate a new one from a password
            salt = b'stable_salt_for_key_derivation'  # In production, use a random salt stored securely
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(encryption_key[:32]))
            fernet = Fernet(key)
        
        return fernet
    
    def encrypt_password(self, password: str) -> str:
        """Encrypt a password and return base64 encoded encrypted data"""
        if not password:
            return ""
        
        try:
            # Encrypt the password
            encrypted = self.fernet.encrypt(password.encode())
            # Return as base64 string for database storage
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            print(f"Encryption error: {e}")
            raise ValueError("Failed to encrypt password")
    
    def decrypt_password(self, encrypted_password: str) -> Optional[str]:
        """Decrypt a password from base64 encoded encrypted data"""
        if not encrypted_password:
            return ""
        
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode())
            # Decrypt the password
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            # Return None if decryption fails (e.g., wrong key or corrupted data)
            return None
    
    def encrypt_data(self, data: str) -> str:
        """Generic method to encrypt any string data"""
        if not data:
            return ""
        
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            print(f"Encryption error: {e}")
            raise ValueError("Failed to encrypt data")
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Generic method to decrypt any string data"""
        if not encrypted_data:
            return ""
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return None
    
    def rotate_encryption_key(self, old_key: str, new_key: str, data: str) -> str:
        """Rotate encryption key by decrypting with old key and encrypting with new key"""
        # Create Fernet instances for both keys
        old_fernet = Fernet(old_key.encode() if isinstance(old_key, str) else old_key)
        new_fernet = Fernet(new_key.encode() if isinstance(new_key, str) else new_key)
        
        try:
            # Decrypt with old key
            encrypted_bytes = base64.urlsafe_b64decode(data.encode())
            decrypted = old_fernet.decrypt(encrypted_bytes)
            
            # Encrypt with new key
            encrypted = new_fernet.encrypt(decrypted)
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            print(f"Key rotation error: {e}")
            raise ValueError("Failed to rotate encryption key")
    
    @staticmethod
    def generate_encryption_key() -> str:
        """Generate a new encryption key"""
        return Fernet.generate_key().decode()


# Singleton instance
encryption_service = EncryptionService()