import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import time
import random

from models import DeletionTask, Account, TaskStatus, DeletionMethod
from services.web_scraper import WebScraper
from services.email_service import EmailService
from services.llm_service import LLMService
from services.audit_service import AuditService
from config import settings


class DeletionService:
    """Service for managing account deletion processes"""
    
    def __init__(self):
        self.web_scraper = WebScraper()
        self.email_service = EmailService()
        self.llm_service = LLMService()
        self.audit_service = AuditService()
    
    async def process_tasks(self, tasks: List[DeletionTask]):
        """Process multiple deletion tasks"""
        
        for task in tasks:
            try:
                await self.execute_deletion(task)
                
                # Add human-like delay between tasks
                delay = random.uniform(2, 5)
                await asyncio.sleep(delay)
                
            except Exception as e:
                print(f"Error processing task {task.id}: {e}")
                await self._mark_task_failed(task, str(e))
    
    async def execute_deletion(self, task: DeletionTask):
        """Execute a single deletion task"""
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.attempts += 1
        
        # Get database session (in real implementation, this would be injected)
        # For now, we'll simulate the process
        
        try:
            if task.method == DeletionMethod.AUTOMATED:
                success = await self._attempt_automated_deletion(task)
                if not success:
                    # Fallback to email
                    await self._fallback_to_email(task)
            else:
                # Email deletion
                await self._send_deletion_email(task)
            
        except Exception as e:
            await self._mark_task_failed(task, str(e))
    
    async def _attempt_automated_deletion(self, task: DeletionTask) -> bool:
        """Attempt automated deletion using web scraping"""
        
        account = task.account
        
        try:
            # Step 1: Use LLM to get site information
            site_info = await self.llm_service.discover_accounts([{
                'site_name': account.site_name,
                'site_url': account.site_url,
                'username': account.username
            }])
            
            if not site_info or not site_info[0].get('deletion_url'):
                return False
            
            # Step 2: Navigate to deletion page
            deletion_url = site_info[0]['deletion_url']
            page_content = await self.web_scraper.navigate_to_page(deletion_url)
            
            if not page_content:
                return False
            
            # Step 3: Analyze page with LLM
            analysis = await self.llm_service.analyze_deletion_page(
                page_content, account.site_name
            )
            
            if analysis.get('difficulty', 10) > 8:
                return False  # Too difficult for automation
            
            # Step 4: Attempt automated deletion
            success = await self.web_scraper.execute_deletion(
                account, analysis, task.id
            )
            
            if success:
                await self._mark_task_completed(task)
                return True
            else:
                return False
            
        except Exception as e:
            print(f"Automated deletion failed for {account.site_name}: {e}")
            return False
    
    async def _fallback_to_email(self, task: DeletionTask):
        """Fallback to email deletion"""
        
        # Update task method
        task.method = DeletionMethod.EMAIL
        
        # Send email
        await self._send_deletion_email(task)
    
    async def _send_deletion_email(self, task: DeletionTask):
        """Send email deletion request"""
        
        account = task.account
        
        try:
            # Generate email content
            email_content = await self.llm_service.generate_deletion_email(account)
            
            # Extract subject and body
            lines = email_content.split('\n')
            subject = lines[0].replace('Subject: ', '') if lines[0].startswith('Subject: ') else 'GDPR Data Deletion Request'
            body = '\n'.join(lines[1:]).strip()
            
            # Determine recipient
            recipient = self._get_deletion_email(account)
            
            if not recipient:
                raise Exception("No deletion email address found")
            
            # Send email
            success = await self.email_service.send_email(
                to=recipient,
                subject=subject,
                body=body,
                account_id=account.id
            )
            
            if success:
                task.privacy_email = recipient
                await self._mark_task_completed(task)
            else:
                raise Exception("Failed to send deletion email")
            
        except Exception as e:
            await self._mark_task_failed(task, str(e))
    
    def _get_deletion_email(self, account: Account) -> Optional[str]:
        """Get deletion email address for account"""
        
        # Common privacy email patterns
        domain = account.site_url.replace('https://', '').replace('http://', '').split('/')[0]
        
        privacy_emails = [
            f"privacy@{domain}",
            f"data-protection@{domain}",
            f"gdpr@{domain}",
            f"legal@{domain}",
            f"support@{domain}"
        ]
        
        # For now, return the first one
        # In production, this would be enhanced with LLM discovery
        return privacy_emails[0]
    
    async def _mark_task_completed(self, task: DeletionTask):
        """Mark task as completed"""
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        
        # Update account status
        task.account.status = 'completed'
        
        # Log completion
        # await self.audit_service.log_action(...)
    
    async def _mark_task_failed(self, task: DeletionTask, error_message: str):
        """Mark task as failed"""
        
        task.status = TaskStatus.FAILED
        task.last_error = error_message
        
        # Update account status
        task.account.status = 'failed'
        
        # Log failure
        # await self.audit_service.log_action(...)
    
    async def get_task_status(self, task_id: int) -> Dict[str, Any]:
        """Get detailed status of a deletion task"""
        
        # This would query the database for the task
        # For now, return mock data
        return {
            "task_id": task_id,
            "status": "in_progress",
            "progress": 50,
            "current_step": "Analyzing deletion page",
            "estimated_completion": "2 minutes"
        }
    
    async def cancel_task(self, task_id: int) -> bool:
        """Cancel a running deletion task"""
        
        # This would stop the task if it's running
        # For now, return success
        return True
    
    async def retry_failed_task(self, task: DeletionTask) -> bool:
        """Retry a failed deletion task"""
        
        if task.attempts >= 3:
            return False  # Max attempts reached
        
        # Reset task
        task.status = TaskStatus.PENDING
        task.last_error = None
        
        # Execute task
        await self.execute_deletion(task)
        
        return True
    
    async def estimate_deletion_time(self, account_ids: List[int]) -> Dict[str, Any]:
        """Estimate time required for deletion tasks"""
        
        # This would analyze the accounts and provide estimates
        # For now, return mock estimates
        return {
            "total_accounts": len(account_ids),
            "estimated_time_minutes": len(account_ids) * 3,
            "automation_success_rate": 0.7,
            "email_fallback_rate": 0.3
        }
    
    async def get_deletion_statistics(self) -> Dict[str, Any]:
        """Get deletion statistics"""
        
        # This would query the database for statistics
        # For now, return mock data
        return {
            "total_deletions": 150,
            "successful_deletions": 135,
            "failed_deletions": 15,
            "success_rate": 0.9,
            "average_time_per_deletion": 3.5,
            "most_common_failures": [
                "Site structure changed",
                "Captcha protection",
                "2FA required"
            ]
        }