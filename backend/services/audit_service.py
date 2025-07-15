from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import json
from cryptography.fernet import Fernet
import base64

from models import AuditLog
from config import settings


class AuditService:
    """Service for audit logging and security"""
    
    def __init__(self):
        self.cipher_suite = self._get_cipher_suite()
    
    def _get_cipher_suite(self):
        """Get or create encryption cipher"""
        key = base64.urlsafe_b64encode(settings.secret_key.encode()[:32].ljust(32, b'0'))
        return Fernet(key)
    
    async def log_action(self, db: Session, account_id: Optional[int], action: str, 
                        details: Dict[str, Any], masked_credentials: bool = True,
                        user_agent: str = None, ip_address: str = None):
        """Log an audit action"""
        
        # Mask sensitive information in details
        if masked_credentials:
            details = self._mask_sensitive_data(details)
        
        log_entry = AuditLog(
            account_id=account_id,
            action=action,
            details=details,
            masked_credentials=masked_credentials,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        return log_entry
    
    def _mask_sensitive_data(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive information in log details"""
        
        masked_details = {}
        sensitive_keys = ['password', 'token', 'key', 'secret', 'credential']
        
        for key, value in details.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                if isinstance(value, str) and len(value) > 0:
                    # Encrypt sensitive data
                    encrypted_value = self.cipher_suite.encrypt(value.encode()).decode()
                    masked_details[key] = f"[MASKED:{encrypted_value}]"
                else:
                    masked_details[key] = "[MASKED]"
            elif isinstance(value, dict):
                masked_details[key] = self._mask_sensitive_data(value)
            else:
                masked_details[key] = value
        
        return masked_details
    
    async def reveal_credentials(self, log_entry: AuditLog) -> Dict[str, Any]:
        """Reveal masked credentials in audit log"""
        
        if not log_entry.masked_credentials:
            return log_entry.details
        
        unmasked_details = {}
        
        for key, value in log_entry.details.items():
            if isinstance(value, str) and value.startswith("[MASKED:") and value.endswith("]"):
                # Extract encrypted value
                encrypted_value = value[8:-1]  # Remove [MASKED: and ]
                try:
                    decrypted_value = self.cipher_suite.decrypt(encrypted_value.encode()).decode()
                    unmasked_details[key] = decrypted_value
                except Exception:
                    unmasked_details[key] = "[DECRYPTION_FAILED]"
            elif isinstance(value, dict):
                unmasked_details[key] = await self._reveal_nested_credentials(value)
            else:
                unmasked_details[key] = value
        
        return unmasked_details
    
    async def _reveal_nested_credentials(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Reveal credentials in nested dictionary"""
        
        unmasked_details = {}
        
        for key, value in details.items():
            if isinstance(value, str) and value.startswith("[MASKED:") and value.endswith("]"):
                encrypted_value = value[8:-1]
                try:
                    decrypted_value = self.cipher_suite.decrypt(encrypted_value.encode()).decode()
                    unmasked_details[key] = decrypted_value
                except Exception:
                    unmasked_details[key] = "[DECRYPTION_FAILED]"
            elif isinstance(value, dict):
                unmasked_details[key] = await self._reveal_nested_credentials(value)
            else:
                unmasked_details[key] = value
        
        return unmasked_details
    
    async def log_deletion_attempt(self, db: Session, account_id: int, 
                                 site_name: str, method: str, success: bool,
                                 error_message: str = None, details: Dict[str, Any] = None):
        """Log account deletion attempt"""
        
        log_details = {
            "site_name": site_name,
            "method": method,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if error_message:
            log_details["error_message"] = error_message
        
        if details:
            log_details.update(details)
        
        await self.log_action(
            db=db,
            account_id=account_id,
            action="deletion_attempt",
            details=log_details,
            masked_credentials=True
        )
    
    async def log_email_sent(self, db: Session, account_id: int, 
                           recipient: str, subject: str, success: bool,
                           error_message: str = None):
        """Log email sent for deletion request"""
        
        log_details = {
            "recipient": recipient,
            "subject": subject,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if error_message:
            log_details["error_message"] = error_message
        
        await self.log_action(
            db=db,
            account_id=account_id,
            action="deletion_email_sent",
            details=log_details,
            masked_credentials=False
        )
    
    async def log_llm_interaction(self, db: Session, account_id: Optional[int],
                                provider: str, task_type: str, tokens_used: int,
                                cost: float, success: bool):
        """Log LLM interaction with cost tracking"""
        
        log_details = {
            "provider": provider,
            "task_type": task_type,
            "tokens_used": tokens_used,
            "cost": cost,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.log_action(
            db=db,
            account_id=account_id,
            action="llm_interaction",
            details=log_details,
            masked_credentials=False
        )
    
    async def log_security_event(self, db: Session, event_type: str, 
                               details: Dict[str, Any], severity: str = "info"):
        """Log security-related events"""
        
        log_details = {
            "event_type": event_type,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }
        log_details.update(details)
        
        await self.log_action(
            db=db,
            account_id=None,
            action="security_event",
            details=log_details,
            masked_credentials=True
        )
    
    async def get_audit_trail(self, db: Session, account_id: int) -> list:
        """Get complete audit trail for an account"""
        
        logs = db.query(AuditLog).filter(
            AuditLog.account_id == account_id
        ).order_by(AuditLog.created_at.desc()).all()
        
        return logs
    
    async def generate_audit_report(self, db: Session, start_date: datetime, 
                                  end_date: datetime) -> Dict[str, Any]:
        """Generate audit report for date range"""
        
        logs = db.query(AuditLog).filter(
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        ).all()
        
        # Aggregate statistics
        from collections import defaultdict
        
        stats = {
            "total_actions": len(logs),
            "actions_by_type": defaultdict(int),
            "accounts_affected": set(),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
        
        for log in logs:
            stats["actions_by_type"][log.action] += 1
            if log.account_id:
                stats["accounts_affected"].add(log.account_id)
        
        stats["accounts_affected"] = len(stats["accounts_affected"])
        stats["actions_by_type"] = dict(stats["actions_by_type"])
        
        return stats