import imaplib
import email
from email.header import decode_header
import re
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from models import DeletionTask, Account, TaskStatus
from services.encryption_service import encryption_service


class IMAPMonitor:
    """Service for monitoring email responses to deletion requests via IMAP"""
    
    def __init__(self, user_email: str, user_password: str):
        self.user_email = user_email
        self.user_password = user_password
        self.imap_config = self._detect_imap_settings(user_email)
        self.connection = None
    
    def _detect_imap_settings(self, email: str) -> Dict[str, Any]:
        """Auto-detect IMAP settings based on email provider"""
        
        domain = email.split('@')[1].lower() if '@' in email else ''
        
        imap_configs = {
            'gmail.com': {
                'server': 'imap.gmail.com',
                'port': 993,
                'use_ssl': True,
                'folder': '[Gmail]/All Mail'  # Gmail specific
            },
            'outlook.com': {
                'server': 'outlook.office365.com',
                'port': 993,
                'use_ssl': True,
                'folder': 'INBOX'
            },
            'hotmail.com': {
                'server': 'outlook.office365.com',
                'port': 993,
                'use_ssl': True,
                'folder': 'INBOX'
            },
            'yahoo.com': {
                'server': 'imap.mail.yahoo.com',
                'port': 993,
                'use_ssl': True,
                'folder': 'INBOX'
            },
            'icloud.com': {
                'server': 'imap.mail.me.com',
                'port': 993,
                'use_ssl': True,
                'folder': 'INBOX'
            }
        }
        
        return imap_configs.get(domain, {
            'server': f'imap.{domain}',
            'port': 993,
            'use_ssl': True,
            'folder': 'INBOX'
        })
    
    async def connect(self) -> bool:
        """Connect to IMAP server"""
        try:
            if self.imap_config['use_ssl']:
                self.connection = imaplib.IMAP4_SSL(
                    self.imap_config['server'],
                    self.imap_config['port']
                )
            else:
                self.connection = imaplib.IMAP4(
                    self.imap_config['server'],
                    self.imap_config['port']
                )
            
            # Login
            self.connection.login(self.user_email, self.user_password)
            
            # Select folder
            self.connection.select(self.imap_config['folder'])
            
            return True
            
        except Exception as e:
            print(f"IMAP connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from IMAP server"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except:
                pass
            self.connection = None
    
    async def check_deletion_responses(self, tasks: List[DeletionTask]) -> List[Dict[str, Any]]:
        """Check for responses to deletion requests"""
        
        if not await self.connect():
            return []
        
        responses = []
        
        try:
            for task in tasks:
                if task.status != TaskStatus.PENDING:
                    continue
                
                account = task.account
                
                # Search for emails from the service
                search_criteria = self._build_search_criteria(account)
                
                # Search for emails
                status, message_ids = self.connection.search(None, search_criteria)
                
                if status == 'OK' and message_ids[0]:
                    for msg_id in message_ids[0].split():
                        # Fetch email
                        status, msg_data = self.connection.fetch(msg_id, '(RFC822)')
                        
                        if status == 'OK':
                            email_body = msg_data[0][1]
                            response_data = await self._parse_deletion_response(
                                email_body, account, task
                            )
                            
                            if response_data:
                                responses.append(response_data)
        
        finally:
            await self.disconnect()
        
        return responses
    
    def _build_search_criteria(self, account: Account) -> str:
        """Build IMAP search criteria for finding responses"""
        
        # Extract domain from site URL
        from urllib.parse import urlparse
        domain = urlparse(account.site_url).netloc.lower().replace('www.', '')
        
        # Search for emails from the service domain
        # received in the last 30 days
        date_filter = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
        
        # Build search string
        search_parts = []
        
        # From domain
        if '@' in domain:
            search_parts.append(f'FROM "{domain}"')
        else:
            search_parts.append(f'FROM "@{domain}"')
        
        # Date filter
        search_parts.append(f'SINCE {date_filter}')
        
        # Subject filters (looking for deletion-related keywords)
        keywords = ['deletion', 'delete', 'removed', 'closed', 'deactivated', 'gdpr', 'erasure']
        
        # IMAP OR syntax for multiple keywords
        if len(keywords) > 1:
            or_criteria = ' OR '.join([f'SUBJECT "{kw}"' for kw in keywords])
            search_parts.append(f'({or_criteria})')
        else:
            search_parts.append(f'SUBJECT "{keywords[0]}"')
        
        return ' '.join(search_parts)
    
    async def _parse_deletion_response(self, email_body: bytes, account: Account, 
                                      task: DeletionTask) -> Optional[Dict[str, Any]]:
        """Parse email to determine if it's a deletion response"""
        
        try:
            # Parse email
            msg = email.message_from_bytes(email_body)
            
            # Get subject
            subject = decode_header(msg['Subject'])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            
            # Get sender
            sender = msg['From']
            
            # Get date
            date = msg['Date']
            
            # Get body
            body = self._get_email_body(msg)
            
            # Analyze content for deletion confirmation
            analysis = self._analyze_deletion_response(subject, body)
            
            if analysis['is_deletion_response']:
                return {
                    'task_id': task.id,
                    'account_id': account.id,
                    'sender': sender,
                    'subject': subject,
                    'date': date,
                    'body_preview': body[:500] if body else '',
                    'status': analysis['status'],
                    'requires_action': analysis['requires_action'],
                    'confirmation_link': analysis.get('confirmation_link'),
                    'deletion_confirmed': analysis.get('deletion_confirmed', False)
                }
            
            return None
            
        except Exception as e:
            print(f"Error parsing email: {e}")
            return None
    
    def _get_email_body(self, msg) -> str:
        """Extract email body from message"""
        
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        pass
                elif content_type == "text/html" and not body:
                    try:
                        # Basic HTML to text conversion
                        html_body = part.get_payload(decode=True).decode()
                        # Remove HTML tags (basic)
                        body = re.sub('<[^<]+?>', '', html_body)
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode()
            except:
                pass
        
        return body
    
    def _analyze_deletion_response(self, subject: str, body: str) -> Dict[str, Any]:
        """Analyze email content to determine deletion status"""
        
        subject_lower = subject.lower() if subject else ""
        body_lower = body.lower() if body else ""
        combined = f"{subject_lower} {body_lower}"
        
        # Patterns indicating deletion response
        deletion_keywords = [
            'deletion', 'delete', 'removed', 'closed', 'deactivated',
            'gdpr', 'erasure', 'account', 'data protection'
        ]
        
        is_deletion_response = any(keyword in combined for keyword in deletion_keywords)
        
        # Patterns for confirmation
        confirmation_patterns = [
            r'account.*has been.*deleted',
            r'account.*has been.*closed',
            r'account.*has been.*removed',
            r'deletion.*complete',
            r'successfully.*deleted',
            r'permanently.*deleted',
            r'account.*deactivated'
        ]
        
        deletion_confirmed = any(re.search(pattern, combined) for pattern in confirmation_patterns)
        
        # Patterns for action required
        action_patterns = [
            r'click.*confirm',
            r'confirm.*deletion',
            r'verify.*email',
            r'click.*link',
            r'action.*required'
        ]
        
        requires_action = any(re.search(pattern, combined) for pattern in action_patterns)
        
        # Extract confirmation links
        confirmation_link = None
        link_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        links = re.findall(link_pattern, body)
        
        for link in links:
            if any(keyword in link.lower() for keyword in ['confirm', 'delete', 'verify', 'complete']):
                confirmation_link = link
                break
        
        # Determine status
        if deletion_confirmed:
            status = 'confirmed'
        elif requires_action:
            status = 'action_required'
        elif is_deletion_response:
            status = 'acknowledged'
        else:
            status = 'unknown'
        
        return {
            'is_deletion_response': is_deletion_response,
            'status': status,
            'deletion_confirmed': deletion_confirmed,
            'requires_action': requires_action,
            'confirmation_link': confirmation_link
        }
    
    async def monitor_inbox(self, interval_seconds: int = 300) -> None:
        """Continuously monitor inbox for deletion responses"""
        
        while True:
            try:
                # Check for new emails
                await self._check_new_emails()
                
                # Wait before next check
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def _check_new_emails(self) -> List[Dict[str, Any]]:
        """Check for new deletion-related emails"""
        
        if not await self.connect():
            return []
        
        new_emails = []
        
        try:
            # Search for unseen emails from the last 7 days
            date_filter = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
            search_criteria = f'(UNSEEN SINCE {date_filter})'
            
            status, message_ids = self.connection.search(None, search_criteria)
            
            if status == 'OK' and message_ids[0]:
                for msg_id in message_ids[0].split():
                    # Fetch email
                    status, msg_data = self.connection.fetch(msg_id, '(RFC822)')
                    
                    if status == 'OK':
                        email_body = msg_data[0][1]
                        msg = email.message_from_bytes(email_body)
                        
                        # Get basic info
                        subject = decode_header(msg['Subject'])[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode()
                        
                        sender = msg['From']
                        body = self._get_email_body(msg)
                        
                        # Check if it's deletion-related
                        analysis = self._analyze_deletion_response(subject, body)
                        
                        if analysis['is_deletion_response']:
                            new_emails.append({
                                'sender': sender,
                                'subject': subject,
                                'body_preview': body[:500] if body else '',
                                'analysis': analysis,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            # Mark as seen
                            self.connection.store(msg_id, '+FLAGS', '\\Seen')
        
        finally:
            await self.disconnect()
        
        return new_emails
    
    async def test_imap_connection(self) -> Dict[str, Any]:
        """Test IMAP connection and configuration"""
        
        try:
            if await self.connect():
                # Get folder list
                status, folders = self.connection.list()
                folder_list = []
                
                if status == 'OK':
                    for folder in folders:
                        if isinstance(folder, bytes):
                            folder = folder.decode()
                        folder_list.append(folder.split('"')[-2] if '"' in folder else folder)
                
                # Get message count in current folder
                status, messages = self.connection.search(None, 'ALL')
                message_count = len(messages[0].split()) if status == 'OK' and messages[0] else 0
                
                await self.disconnect()
                
                return {
                    'success': True,
                    'server': self.imap_config['server'],
                    'port': self.imap_config['port'],
                    'folders': folder_list[:10],  # First 10 folders
                    'current_folder': self.imap_config['folder'],
                    'message_count': message_count
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to connect to IMAP server'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'server': self.imap_config['server'],
                'port': self.imap_config['port']
            }