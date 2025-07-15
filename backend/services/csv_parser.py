import csv
import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from urllib.parse import urlparse
import hashlib
from cryptography.fernet import Fernet
import base64
import os

from models import Account, AccountStatus
from config import settings


class CSVParser:
    """Parser for password manager CSV exports"""
    
    def __init__(self):
        self.cipher_suite = self._get_cipher_suite()
    
    def _get_cipher_suite(self):
        """Get or create encryption cipher"""
        key = base64.urlsafe_b64encode(settings.secret_key.encode()[:32].ljust(32, b'0'))
        return Fernet(key)
    
    def parse_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse CSV file and extract account information"""
        
        try:
            df = pd.read_csv(file_path)
            
            # Detect CSV format (Bitwarden or LastPass)
            csv_format = self._detect_format(df.columns.tolist())
            
            if csv_format == "bitwarden":
                return self._parse_bitwarden(df)
            elif csv_format == "lastpass":
                return self._parse_lastpass(df)
            else:
                raise ValueError(f"Unsupported CSV format. Expected columns: {self._get_expected_columns()}")
        
        except Exception as e:
            raise ValueError(f"Error parsing CSV file: {str(e)}")
    
    def _detect_format(self, columns: List[str]) -> str:
        """Detect CSV format based on column names"""
        
        bitwarden_columns = {'name', 'url', 'username', 'password'}
        lastpass_columns = {'name', 'url', 'username', 'password', 'extra'}
        
        columns_set = set(col.lower() for col in columns)
        
        if bitwarden_columns.issubset(columns_set):
            return "bitwarden"
        elif lastpass_columns.issubset(columns_set):
            return "lastpass"
        else:
            return "unknown"
    
    def _parse_bitwarden(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Parse Bitwarden CSV export"""
        
        accounts = []
        
        for _, row in df.iterrows():
            # Skip empty rows or folders
            if pd.isna(row.get('url')) or not row.get('url'):
                continue
            
            account = {
                'site_name': row.get('name', '').strip(),
                'site_url': self._clean_url(row.get('url', '')),
                'username': row.get('username', '').strip(),
                'password': row.get('password', '').strip(),
                'notes': row.get('notes', '').strip()
            }
            
            # Skip if missing essential fields
            if not account['site_url'] or not account['username']:
                continue
            
            # Extract email if available
            account['email'] = self._extract_email(account['username'], account['notes'])
            
            accounts.append(account)
        
        return accounts
    
    def _parse_lastpass(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Parse LastPass CSV export"""
        
        accounts = []
        
        for _, row in df.iterrows():
            # Skip empty rows
            if pd.isna(row.get('url')) or not row.get('url'):
                continue
            
            account = {
                'site_name': row.get('name', '').strip(),
                'site_url': self._clean_url(row.get('url', '')),
                'username': row.get('username', '').strip(),
                'password': row.get('password', '').strip(),
                'notes': row.get('extra', '').strip()
            }
            
            # Skip if missing essential fields
            if not account['site_url'] or not account['username']:
                continue
            
            # Extract email if available
            account['email'] = self._extract_email(account['username'], account['notes'])
            
            accounts.append(account)
        
        return accounts
    
    def _clean_url(self, url: str) -> str:
        """Clean and normalize URL"""
        if not url:
            return ""
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            parsed = urlparse(url)
            # Return base domain
            return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            return url
    
    def _extract_email(self, username: str, notes: str) -> str:
        """Extract email from username or notes"""
        import re
        
        # Check if username is an email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        if re.match(email_pattern, username):
            return username
        
        # Check notes for email
        if notes:
            email_match = re.search(email_pattern, notes)
            if email_match:
                return email_match.group()
        
        return ""
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt password for storage"""
        return self.cipher_suite.encrypt(password.encode()).decode()
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt password for use"""
        return self.cipher_suite.decrypt(encrypted_password.encode()).decode()
    
    def save_account(self, db: Session, account_data: Dict[str, Any]) -> Account:
        """Save account to database"""
        
        # Check if account already exists
        existing = db.query(Account).filter(
            Account.site_url == account_data['site_url'],
            Account.username == account_data['username']
        ).first()
        
        if existing:
            # Update existing account
            existing.site_name = account_data['site_name']
            existing.email = account_data.get('email', '')
            existing.password_hash = self._encrypt_password(account_data['password'])
            existing.updated_at = pd.Timestamp.now()
            db.commit()
            return existing
        
        # Create new account
        account = Account(
            site_name=account_data['site_name'],
            site_url=account_data['site_url'],
            username=account_data['username'],
            password_hash=self._encrypt_password(account_data['password']),
            email=account_data.get('email', ''),
            status=AccountStatus.DISCOVERED
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        
        return account
    
    def get_password(self, account: Account) -> str:
        """Get decrypted password for account"""
        return self._decrypt_password(account.password_hash)
    
    def _get_expected_columns(self) -> Dict[str, List[str]]:
        """Get expected column names for different formats"""
        return {
            "bitwarden": ["name", "url", "username", "password", "notes"],
            "lastpass": ["name", "url", "username", "password", "extra"]
        }