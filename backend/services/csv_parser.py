import csv
import pandas as pd
import json
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from urllib.parse import urlparse
import re

from models import Account, AccountStatus
from services.encryption_service import encryption_service


class CSVParser:
    """Enhanced parser for password manager CSV exports with auto-detection"""
    
    # Column mappings for different password manager formats
    FORMAT_MAPPINGS = {
        'bitwarden': {
            'columns': ['folder', 'favorite', 'type', 'name', 'notes', 'fields', 'reprompt', 'login_uri', 'login_username', 'login_password', 'login_totp'],
            'site_name': 'name',
            'site_url': 'login_uri',
            'username': 'login_username',
            'password': 'login_password',
            'notes': 'notes',
            'email': None  # Extract from username if email format
        },
        'lastpass': {
            'columns': ['url', 'username', 'password', 'totp', 'extra', 'name', 'grouping', 'fav'],
            'site_name': 'name',
            'site_url': 'url',
            'username': 'username',
            'password': 'password',
            'notes': 'extra',
            'email': None
        },
        '1password': {
            'columns': ['title', 'url', 'username', 'password', 'notes', 'type', 'category'],
            'site_name': 'title',
            'site_url': 'url',
            'username': 'username',
            'password': 'password',
            'notes': 'notes',
            'email': None
        },
        'chrome': {
            'columns': ['name', 'url', 'username', 'password'],
            'site_name': 'name',
            'site_url': 'url',
            'username': 'username',
            'password': 'password',
            'notes': None,
            'email': None
        },
        'firefox': {
            'columns': ['url', 'username', 'password', 'httpRealm', 'formActionOrigin', 'guid', 'timeCreated', 'timeLastUsed', 'timePasswordChanged'],
            'site_name': None,  # Extract from URL
            'site_url': 'url',
            'username': 'username',
            'password': 'password',
            'notes': None,
            'email': None
        },
        'keepass': {
            'columns': ['group', 'title', 'username', 'password', 'url', 'notes'],
            'site_name': 'title',
            'site_url': 'url',
            'username': 'username',
            'password': 'password',
            'notes': 'notes',
            'email': None
        },
        'dashlane': {
            'columns': ['username', 'username2', 'username3', 'title', 'password', 'note', 'url', 'category', 'otpSecret'],
            'site_name': 'title',
            'site_url': 'url',
            'username': 'username',
            'password': 'password',
            'notes': 'note',
            'email': 'username2'  # Dashlane often stores email in username2
        },
        'nordpass': {
            'columns': ['name', 'url', 'username', 'password', 'note', 'cardholdername', 'cardnumber', 'cvc', 'expirydate', 'zipcode', 'folder', 'full_name', 'phone_number', 'email', 'address1', 'address2', 'city', 'country', 'state'],
            'site_name': 'name',
            'site_url': 'url',
            'username': 'username',
            'password': 'password',
            'notes': 'note',
            'email': 'email'
        },
        'roboform': {
            'columns': ['name', 'url', 'login', 'pwd', 'note', 'folder', 'application', 'rfc_fieldname'],
            'site_name': 'name',
            'site_url': 'url',
            'username': 'login',
            'password': 'pwd',
            'notes': 'note',
            'email': None
        },
        'enpass': {
            'columns': ['title', 'url', 'username', 'password', 'notes', 'email'],
            'site_name': 'title',
            'site_url': 'url',
            'username': 'username',
            'password': 'password',
            'notes': 'notes',
            'email': 'email'
        }
    }
    
    def detect_format(self, df: pd.DataFrame) -> Tuple[str, float]:
        """
        Auto-detect CSV format based on column names
        Returns: (format_name, confidence_score)
        """
        columns_lower = [col.lower().strip() for col in df.columns]
        
        best_match = None
        best_score = 0
        
        for format_name, mapping in self.FORMAT_MAPPINGS.items():
            expected_columns = mapping['columns']
            
            # Calculate matching score
            matches = 0
            for expected_col in expected_columns:
                if expected_col and expected_col.lower() in columns_lower:
                    matches += 1
            
            # Calculate confidence score (0-1)
            if len(expected_columns) > 0:
                score = matches / len(expected_columns)
                
                # Bonus points for exact critical columns
                critical_cols = ['username', 'password', 'url']
                for col in critical_cols:
                    if mapping.get(col) and mapping[col].lower() in columns_lower:
                        score += 0.1
                
                if score > best_score:
                    best_score = score
                    best_match = format_name
        
        # If no good match, try generic detection
        if best_score < 0.5:
            if self._has_basic_columns(columns_lower):
                best_match = 'generic'
                best_score = 0.5
        
        return best_match, best_score
    
    def _has_basic_columns(self, columns: List[str]) -> bool:
        """Check if CSV has basic password manager columns"""
        required = ['password']
        identifiers = ['username', 'email', 'login', 'user']
        urls = ['url', 'website', 'site', 'domain']
        
        has_password = any(req in col for col in columns for req in required)
        has_identifier = any(ident in col for col in columns for ident in identifiers)
        has_url = any(url in col for col in columns for url in urls)
        
        return has_password and (has_identifier or has_url)
    
    def parse_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse CSV file with auto-detection and extract account information"""
        
        try:
            # Read CSV with different encodings
            df = None
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError("Could not read CSV file with any supported encoding")
            
            # Detect format
            format_name, confidence = self.detect_format(df)
            
            if format_name is None:
                raise ValueError(f"Could not detect CSV format. Please ensure it's from a supported password manager.")
            
            print(f"Detected format: {format_name} (confidence: {confidence:.2f})")
            
            # Parse based on detected format
            if format_name == 'generic':
                return self._parse_generic(df)
            else:
                return self._parse_with_mapping(df, self.FORMAT_MAPPINGS[format_name])
        
        except Exception as e:
            raise ValueError(f"Error parsing CSV file: {str(e)}")
    
    def _parse_with_mapping(self, df: pd.DataFrame, mapping: Dict) -> List[Dict[str, Any]]:
        """Parse CSV using specific format mapping"""
        accounts = []
        
        # Normalize column names
        df.columns = [col.lower().strip() for col in df.columns]
        
        for _, row in df.iterrows():
            try:
                # Extract fields based on mapping
                site_name = self._get_field(row, mapping['site_name'])
                site_url = self._get_field(row, mapping['site_url'])
                username = self._get_field(row, mapping['username'])
                password = self._get_field(row, mapping['password'])
                notes = self._get_field(row, mapping['notes'])
                email = self._get_field(row, mapping['email'])
                
                # Skip if missing critical fields
                if not password or (not username and not email):
                    continue
                
                # Clean and process fields
                if not site_name and site_url:
                    site_name = self._extract_site_name(site_url)
                
                if not site_url and site_name:
                    site_url = self._guess_url(site_name)
                
                site_url = self._clean_url(site_url)
                
                # Extract email if not explicitly provided
                if not email:
                    email = self._extract_email(username, notes)
                
                # Skip entries that look like secure notes or non-login items
                if self._is_non_login_item(site_name, site_url, password):
                    continue
                
                account = {
                    'site_name': site_name or 'Unknown',
                    'site_url': site_url or '',
                    'username': username or email or '',
                    'password': password,
                    'email': email or '',
                    'notes': notes or ''
                }
                
                accounts.append(account)
                
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue
        
        return accounts
    
    def _parse_generic(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Parse CSV with generic/unknown format"""
        accounts = []
        columns_lower = [col.lower() for col in df.columns]
        
        # Try to identify columns
        password_col = next((col for col in columns_lower if 'password' in col or 'pass' in col or 'pwd' in col), None)
        username_col = next((col for col in columns_lower if 'username' in col or 'user' in col or 'login' in col or 'email' in col), None)
        url_col = next((col for col in columns_lower if 'url' in col or 'website' in col or 'site' in col or 'domain' in col), None)
        name_col = next((col for col in columns_lower if 'name' in col or 'title' in col or 'description' in col), None)
        notes_col = next((col for col in columns_lower if 'note' in col or 'comment' in col or 'description' in col), None)
        
        if not password_col:
            raise ValueError("Could not identify password column")
        
        for _, row in df.iterrows():
            try:
                password = str(row[password_col]) if pd.notna(row[password_col]) else None
                if not password or password == 'nan':
                    continue
                
                username = str(row[username_col]) if username_col and pd.notna(row[username_col]) else ''
                site_url = str(row[url_col]) if url_col and pd.notna(row[url_col]) else ''
                site_name = str(row[name_col]) if name_col and pd.notna(row[name_col]) else ''
                notes = str(row[notes_col]) if notes_col and pd.notna(row[notes_col]) else ''
                
                # Clean and process
                if not site_name and site_url:
                    site_name = self._extract_site_name(site_url)
                elif not site_name and username:
                    # Try to guess from email domain
                    if '@' in username:
                        domain = username.split('@')[1]
                        site_name = domain.split('.')[0].capitalize()
                
                site_url = self._clean_url(site_url)
                email = self._extract_email(username, notes)
                
                account = {
                    'site_name': site_name or 'Unknown',
                    'site_url': site_url,
                    'username': username,
                    'password': password,
                    'email': email,
                    'notes': notes
                }
                
                accounts.append(account)
                
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue
        
        return accounts
    
    def _get_field(self, row, field_name: Optional[str]) -> str:
        """Safely get field from row"""
        if not field_name:
            return ''
        
        field_name = field_name.lower()
        if field_name in row.index:
            value = row[field_name]
            if pd.notna(value):
                return str(value).strip()
        return ''
    
    def _extract_site_name(self, url: str) -> str:
        """Extract site name from URL"""
        if not url:
            return 'Unknown'
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            
            # Remove www. and common TLDs
            domain = domain.replace('www.', '')
            
            # Get the main part of the domain
            parts = domain.split('.')
            if len(parts) > 1:
                return parts[0].capitalize()
            return domain.capitalize()
        except:
            return url.split('/')[0].capitalize()
    
    def _guess_url(self, site_name: str) -> str:
        """Guess URL from site name"""
        if not site_name:
            return ''
        
        # Common patterns
        site_lower = site_name.lower()
        
        # Remove spaces and special chars
        clean_name = re.sub(r'[^a-z0-9]', '', site_lower)
        
        # Common domains
        common_domains = {
            'google': 'https://accounts.google.com',
            'gmail': 'https://accounts.google.com',
            'facebook': 'https://www.facebook.com',
            'twitter': 'https://twitter.com',
            'instagram': 'https://www.instagram.com',
            'linkedin': 'https://www.linkedin.com',
            'amazon': 'https://www.amazon.com',
            'netflix': 'https://www.netflix.com',
            'spotify': 'https://www.spotify.com',
            'apple': 'https://appleid.apple.com',
            'microsoft': 'https://account.microsoft.com',
            'github': 'https://github.com',
            'reddit': 'https://www.reddit.com'
        }
        
        if clean_name in common_domains:
            return common_domains[clean_name]
        
        # Default pattern
        return f'https://www.{clean_name}.com'
    
    def _clean_url(self, url: str) -> str:
        """Clean and normalize URL"""
        if not url:
            return ""
        
        url = url.strip()
        
        # Handle special cases
        if url == 'nan' or url == 'None':
            return ""
        
        # Add protocol if missing
        if url and not url.startswith(('http://', 'https://', 'ftp://')):
            url = 'https://' + url
        
        try:
            parsed = urlparse(url)
            # Return base domain
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
            return url
        except Exception:
            return url
    
    def _extract_email(self, username: str, notes: str) -> str:
        """Extract email from username or notes"""
        # Check if username is an email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        if username and re.match(email_pattern, username):
            return username
        
        # Check notes for email
        if notes:
            email_match = re.search(email_pattern, notes)
            if email_match:
                return email_match.group()
        
        return ""
    
    def _is_non_login_item(self, site_name: str, site_url: str, password: str) -> bool:
        """Check if this is a non-login item (secure note, credit card, etc.)"""
        if not site_name and not site_url:
            return True
        
        # Check for common non-login patterns
        non_login_keywords = [
            'secure note', 'note', 'credit card', 'card', 'identity',
            'driver license', 'passport', 'social security', 'bank account',
            'wifi', 'router', 'server', 'database', 'ssh', 'ftp'
        ]
        
        combined = f"{site_name} {site_url}".lower()
        
        return any(keyword in combined for keyword in non_login_keywords)
    
    def save_account(self, db: Session, account_data: Dict[str, Any], user_id: int) -> Account:
        """Save account to database with encrypted password"""
        
        # Check if account already exists for this user
        existing = db.query(Account).filter(
            Account.user_id == user_id,
            Account.site_url == account_data['site_url'],
            Account.username == account_data['username']
        ).first()
        
        if existing:
            # Update existing account
            existing.site_name = account_data['site_name']
            existing.email = account_data.get('email', '')
            existing.encrypted_password = encryption_service.encrypt_password(account_data['password'])
            db.commit()
            return existing
        
        # Create new account with encrypted password
        account = Account(
            user_id=user_id,
            site_name=account_data['site_name'],
            site_url=account_data['site_url'],
            username=account_data['username'],
            encrypted_password=encryption_service.encrypt_password(account_data['password']),
            email=account_data.get('email', ''),
            status=AccountStatus.DISCOVERED
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        
        return account
    
    @staticmethod
    def get_decrypted_password(account: Account) -> str:
        """Get decrypted password for account"""
        return encryption_service.decrypt_password(account.encrypted_password)
    
    def get_supported_formats(self) -> Dict[str, Dict]:
        """Get information about supported formats"""
        return {
            format_name: {
                'name': format_name.replace('_', ' ').title(),
                'columns': mapping['columns'],
                'has_email_field': mapping.get('email') is not None
            }
            for format_name, mapping in self.FORMAT_MAPPINGS.items()
        }