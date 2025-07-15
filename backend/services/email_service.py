import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime
import aiosmtplib
import ssl

from config import settings


class EmailService:
    """Service for sending deletion request emails using user's email account"""
    
    def __init__(self, user_email: str = None, user_password: str = None):
        # Use user's email configuration if provided, otherwise fall back to system config
        self.user_email = user_email or settings.smtp_username
        self.user_password = user_password or settings.smtp_password
        
        # Auto-detect SMTP settings based on email provider
        self.smtp_config = self._detect_smtp_settings(self.user_email)
    
    def _detect_smtp_settings(self, email: str) -> Dict[str, Any]:
        """Auto-detect SMTP settings based on email provider"""
        
        domain = email.split('@')[1].lower() if '@' in email else ''
        
        smtp_configs = {
            'gmail.com': {
                'server': 'smtp.gmail.com',
                'port': 587,
                'use_tls': True,
                'auth_required': True,
                'app_password_required': True
            },
            'outlook.com': {
                'server': 'smtp-mail.outlook.com',
                'port': 587,
                'use_tls': True,
                'auth_required': True,
                'app_password_required': False
            },
            'hotmail.com': {
                'server': 'smtp-mail.outlook.com',
                'port': 587,
                'use_tls': True,
                'auth_required': True,
                'app_password_required': False
            },
            'yahoo.com': {
                'server': 'smtp.mail.yahoo.com',
                'port': 587,
                'use_tls': True,
                'auth_required': True,
                'app_password_required': True
            },
            'protonmail.com': {
                'server': '127.0.0.1',  # Requires Bridge
                'port': 1025,
                'use_tls': True,
                'auth_required': True,
                'app_password_required': False
            }
        }
        
        return smtp_configs.get(domain, {
            'server': settings.smtp_server,
            'port': settings.smtp_port,
            'use_tls': True,
            'auth_required': True,
            'app_password_required': False
        })
    
    async def send_email(self, to: str, subject: str, body: str, 
                        account_id: Optional[int] = None, user_name: str = None) -> bool:
        """Send email deletion request from user's email account"""
        
        try:
            # Create message
            message = MIMEMultipart()
            message['From'] = f"{user_name} <{self.user_email}>" if user_name else self.user_email
            message['To'] = to
            message['Subject'] = subject
            message['Reply-To'] = self.user_email
            
            # Add body with user's signature
            full_body = body
            if user_name:
                full_body = full_body.replace('[User Name]', user_name)
            else:
                full_body = full_body.replace('[User Name]', self.user_email.split('@')[0])
            
            message.attach(MIMEText(full_body, 'plain'))
            
            # Send email
            success = await self._send_async_email(message, to)
            
            # Log email sending (would integrate with audit service)
            await self._log_email_sent(to, subject, success, account_id)
            
            return success
            
        except Exception as e:
            print(f"Error sending email to {to}: {e}")
            await self._log_email_sent(to, subject, False, account_id, str(e))
            return False
    
    async def _send_async_email(self, message: MIMEMultipart, to: str) -> bool:
        """Send email asynchronously using user's email account"""
        
        try:
            # Send email using aiosmtplib with user's SMTP settings
            await aiosmtplib.send(
                message,
                hostname=self.smtp_config['server'],
                port=self.smtp_config['port'],
                start_tls=self.smtp_config['use_tls'],
                username=self.user_email,
                password=self.user_password,
                use_tls=False
            )
            
            return True
            
        except Exception as e:
            print(f"SMTP error: {e}")
            return False
    
    async def send_deletion_request(self, account_data: Dict[str, Any], 
                                  privacy_email: str) -> Dict[str, Any]:
        """Send standardized GDPR deletion request"""
        
        subject = f"GDPR Article 17 Data Deletion Request - {account_data['username']}"
        
        body = self._generate_deletion_email_body(account_data)
        
        success = await self.send_email(privacy_email, subject, body, account_data.get('id'))
        
        return {
            'success': success,
            'recipient': privacy_email,
            'subject': subject,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _generate_deletion_email_body(self, account_data: Dict[str, Any]) -> str:
        """Generate standardized deletion email body"""
        
        return f"""Dear {account_data['site_name']} Data Protection Team,

I am writing to request the complete deletion of my personal data from your platform in accordance with Article 17 of the EU General Data Protection Regulation (GDPR) - the Right to Erasure.

ACCOUNT INFORMATION:
- Username: {account_data['username']}
- Email: {account_data.get('email', 'N/A')}
- Site: {account_data['site_url']}
- Account created: {account_data.get('created_date', 'Unknown')}

DELETION REQUEST:
Under GDPR Article 17, I request that you:

1. DELETE all personal data associated with this account, including but not limited to:
   - Profile information and settings
   - Activity logs and usage data
   - Communications and messages
   - Any derived or inferred data profiles
   - Backup copies and archived data

2. REMOVE all records of my activity on your platform

3. ENSURE that no personal data remains in your systems, including:
   - Primary databases
   - Backup systems
   - Log files
   - Analytics systems
   - Third-party integrations

4. CONFIRM in writing that the deletion has been completed within 30 days of receipt of this request

LEGAL BASIS:
This request is made under:
- GDPR Article 17 (Right to Erasure)
- GDPR Article 12 (Transparent information and communication)

If you process EU residents' data, you are legally obligated to comply with this request within one month of receipt, as specified in GDPR Article 12(3).

CONFIRMATION REQUIRED:
Please confirm in writing:
1. Receipt of this deletion request
2. Completion of the deletion process
3. Any data that cannot be deleted and the legal basis for retention

If you cannot comply with this request, please provide detailed reasons and legal justification within 30 days.

CONTACT INFORMATION:
If you require additional information to process this request, please contact me at this email address.

Thank you for your prompt attention to this matter.

Regards,
[User Name]

---
This is an automated request generated by GDPR Account Deletion Assistant.
Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

IMPORTANT: This request is legally binding under GDPR for organizations processing EU residents' data.
"""
    
    async def send_follow_up_email(self, original_request: Dict[str, Any], 
                                 days_elapsed: int) -> bool:
        """Send follow-up email for unanswered deletion requests"""
        
        subject = f"FOLLOW-UP: GDPR Deletion Request - {original_request['username']} (Day {days_elapsed})"
        
        body = f"""Dear {original_request['site_name']} Data Protection Team,

This is a follow-up to my GDPR Article 17 data deletion request sent {days_elapsed} days ago.

ORIGINAL REQUEST DETAILS:
- Username: {original_request['username']}
- Email: {original_request.get('email', 'N/A')}
- Request sent: {original_request.get('sent_date', 'Unknown')}
- Site: {original_request['site_url']}

COMPLIANCE REMINDER:
Under GDPR Article 12(3), organizations must respond to data subject requests within one month of receipt. As {days_elapsed} days have passed, your response is {"overdue" if days_elapsed > 30 else "approaching the deadline"}.

REQUIRED ACTIONS:
1. Confirm receipt of the original deletion request
2. Provide status update on the deletion process
3. Complete the deletion if not already done
4. Provide written confirmation of completion

LEGAL CONSEQUENCES:
Failure to respond to valid GDPR requests can result in:
- Fines up to €20 million or 4% of annual global turnover
- Regulatory action by data protection authorities
- Potential legal proceedings

Please respond within 48 hours to avoid potential compliance issues.

If you have already processed this request, please confirm completion in writing.

Regards,
[User Name]

---
This is an automated follow-up generated by GDPR Account Deletion Assistant.
Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        success = await self.send_email(
            original_request['privacy_email'],
            subject,
            body,
            original_request.get('account_id')
        )
        
        return success
    
    async def test_email_configuration(self) -> Dict[str, Any]:
        """Test user's email configuration"""
        
        try:
            # Test connection
            context = ssl.create_default_context()
            
            server = smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'])
            server.ehlo()
            if self.smtp_config['use_tls']:
                server.starttls(context=context)
            server.login(self.user_email, self.user_password)
            server.quit()
            
            return {
                'success': True,
                'message': 'Email configuration is working',
                'smtp_server': self.smtp_config['server'],
                'smtp_port': self.smtp_config['port'],
                'username': self.user_email,
                'provider': self.user_email.split('@')[1],
                'app_password_required': self.smtp_config.get('app_password_required', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'smtp_server': self.smtp_config['server'],
                'smtp_port': self.smtp_config['port'],
                'provider': self.user_email.split('@')[1] if '@' in self.user_email else 'unknown',
                'app_password_required': self.smtp_config.get('app_password_required', False)
            }
    
    async def _log_email_sent(self, to: str, subject: str, success: bool, 
                            account_id: Optional[int] = None, error: str = None):
        """Log email sending for audit purposes"""
        
        log_data = {
            'recipient': to,
            'subject': subject,
            'success': success,
            'timestamp': datetime.utcnow().isoformat(),
            'account_id': account_id
        }
        
        if error:
            log_data['error'] = error
        
        # In production, this would integrate with the audit service
        print(f"Email log: {log_data}")
    
    async def get_email_templates(self) -> Dict[str, str]:
        """Get available email templates"""
        
        return {
            'gdpr_deletion': 'GDPR Article 17 Deletion Request',
            'follow_up': 'Follow-up for unanswered deletion request',
            'confirmation': 'Confirmation of deletion request',
            'complaint': 'Complaint to data protection authority'
        }
    
    async def generate_complaint_email(self, account_data: Dict[str, Any], 
                                     days_without_response: int) -> str:
        """Generate email template for complaint to data protection authority"""
        
        return f"""Subject: GDPR Compliance Complaint - Unresponsive Data Controller

Dear Data Protection Authority,

I am filing a complaint regarding a data controller's failure to respond to a valid GDPR deletion request.

COMPLAINT DETAILS:
- Data Controller: {account_data['site_name']}
- Website: {account_data['site_url']}
- My username: {account_data['username']}
- Request sent: {days_without_response} days ago
- Article violated: GDPR Article 17 (Right to Erasure) and Article 12 (Response time)

BACKGROUND:
I submitted a valid request for deletion of my personal data under GDPR Article 17 to {account_data['site_name']} {days_without_response} days ago. Despite the legal requirement to respond within one month, I have received no acknowledgment or response.

REQUESTED ACTION:
I request that your authority:
1. Investigate this non-compliance
2. Compel the data controller to respond and comply
3. Consider appropriate enforcement action

EVIDENCE:
I can provide copies of the original deletion request and any correspondence.

Thank you for your attention to this matter.

Regards,
[Your Name]
[Your Address]
[Your Contact Information]

---
Generated by GDPR Account Deletion Assistant
Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""