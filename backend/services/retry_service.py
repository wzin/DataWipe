"""
Retry service for handling failed deletion tasks with intelligent retry logic
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random

from models import DeletionTask, TaskStatus, Account, User
from services.deletion_service import DeletionService
from services.audit_service import AuditService
from services.email_service import EmailService


class RetryService:
    """Service for managing retry logic for failed deletion tasks"""
    
    # Retry configuration
    MAX_RETRY_ATTEMPTS = 5
    BASE_RETRY_DELAY = 60  # seconds
    MAX_RETRY_DELAY = 3600  # 1 hour max
    
    # Retry strategies by failure type
    RETRY_STRATEGIES = {
        'network_error': {
            'max_attempts': 5,
            'base_delay': 30,
            'backoff_multiplier': 2,
            'jitter': True
        },
        'rate_limit': {
            'max_attempts': 3,
            'base_delay': 300,  # 5 minutes
            'backoff_multiplier': 3,
            'jitter': False
        },
        'captcha_required': {
            'max_attempts': 2,
            'base_delay': 600,  # 10 minutes
            'backoff_multiplier': 1,
            'jitter': False
        },
        'auth_failed': {
            'max_attempts': 3,
            'base_delay': 60,
            'backoff_multiplier': 2,
            'jitter': True
        },
        'site_unavailable': {
            'max_attempts': 5,
            'base_delay': 120,
            'backoff_multiplier': 2,
            'jitter': True
        },
        'unknown': {
            'max_attempts': 3,
            'base_delay': 60,
            'backoff_multiplier': 2,
            'jitter': True
        }
    }
    
    def __init__(self):
        self.deletion_service = DeletionService()
        self.audit_service = AuditService()
        
    def classify_failure(self, error_message: str) -> str:
        """Classify the type of failure based on error message"""
        error_lower = error_message.lower() if error_message else ""
        
        if any(term in error_lower for term in ['network', 'connection', 'timeout', 'unreachable']):
            return 'network_error'
        elif any(term in error_lower for term in ['rate limit', 'too many requests', '429']):
            return 'rate_limit'
        elif any(term in error_lower for term in ['captcha', 'verification', 'robot']):
            return 'captcha_required'
        elif any(term in error_lower for term in ['auth', 'login', 'password', 'credential']):
            return 'auth_failed'
        elif any(term in error_lower for term in ['503', '500', 'unavailable', 'maintenance']):
            return 'site_unavailable'
        else:
            return 'unknown'
    
    def calculate_retry_delay(self, attempt: int, failure_type: str) -> int:
        """Calculate delay before next retry using exponential backoff"""
        strategy = self.RETRY_STRATEGIES.get(failure_type, self.RETRY_STRATEGIES['unknown'])
        
        # Exponential backoff
        delay = strategy['base_delay'] * (strategy['backoff_multiplier'] ** (attempt - 1))
        
        # Cap at maximum delay
        delay = min(delay, self.MAX_RETRY_DELAY)
        
        # Add jitter if configured
        if strategy.get('jitter', False):
            jitter = random.uniform(0.8, 1.2)
            delay = int(delay * jitter)
        
        return delay
    
    def should_retry(self, task: DeletionTask, failure_type: str) -> bool:
        """Determine if a task should be retried"""
        strategy = self.RETRY_STRATEGIES.get(failure_type, self.RETRY_STRATEGIES['unknown'])
        
        # Check attempt limit
        if task.attempts >= strategy['max_attempts']:
            return False
        
        # Check if task is too old (>30 days)
        if task.created_at < datetime.utcnow() - timedelta(days=30):
            return False
        
        # Don't retry if manually cancelled
        if hasattr(task, 'cancelled') and task.cancelled:
            return False
        
        # Check specific failure types that shouldn't be retried
        non_retryable = ['account_deleted', 'invalid_credentials', 'account_not_found']
        if any(term in (task.last_error or '').lower() for term in non_retryable):
            return False
        
        return True
    
    async def retry_failed_task(self, db: Session, task_id: int) -> Dict[str, Any]:
        """Retry a specific failed task"""
        # Get the task
        task = db.query(DeletionTask).filter(
            DeletionTask.id == task_id,
            DeletionTask.status == TaskStatus.FAILED
        ).first()
        
        if not task:
            return {
                'success': False,
                'error': 'Task not found or not in failed state'
            }
        
        # Classify failure and check if should retry
        failure_type = self.classify_failure(task.last_error)
        
        if not self.should_retry(task, failure_type):
            return {
                'success': False,
                'error': 'Task has exceeded retry limits or is not retryable',
                'failure_type': failure_type,
                'attempts': task.attempts
            }
        
        # Calculate delay
        delay = self.calculate_retry_delay(task.attempts + 1, failure_type)
        
        # Schedule retry
        task.status = TaskStatus.PENDING
        task.retry_after = datetime.utcnow() + timedelta(seconds=delay)
        task.retry_count = (task.retry_count or 0) + 1
        
        db.commit()
        
        # Log retry attempt
        await self.audit_service.log_action(
            db=db,
            user_id=task.account.user_id,
            account_id=task.account_id,
            action="task_retry_scheduled",
            details={
                'task_id': task_id,
                'failure_type': failure_type,
                'attempt': task.attempts + 1,
                'retry_delay': delay,
                'retry_after': task.retry_after.isoformat()
            }
        )
        
        # Execute retry after delay (async)
        asyncio.create_task(self._execute_delayed_retry(db, task_id, delay))
        
        return {
            'success': True,
            'task_id': task_id,
            'failure_type': failure_type,
            'retry_after': task.retry_after.isoformat(),
            'retry_delay_seconds': delay,
            'attempt': task.attempts + 1
        }
    
    async def _execute_delayed_retry(self, db: Session, task_id: int, delay: int):
        """Execute retry after delay"""
        await asyncio.sleep(delay)
        
        # Get fresh task from database
        task = db.query(DeletionTask).filter(DeletionTask.id == task_id).first()
        
        if task and task.status == TaskStatus.PENDING:
            # Execute deletion
            await self.deletion_service.execute_deletion(task)
    
    async def bulk_retry_failed_tasks(self, db: Session, user_id: int, 
                                     account_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Retry all failed tasks for a user or specific accounts"""
        # Get failed tasks
        query = db.query(DeletionTask).join(Account).filter(
            Account.user_id == user_id,
            DeletionTask.status == TaskStatus.FAILED
        )
        
        if account_ids:
            query = query.filter(DeletionTask.account_id.in_(account_ids))
        
        failed_tasks = query.all()
        
        if not failed_tasks:
            return {
                'success': True,
                'message': 'No failed tasks to retry',
                'retried': 0
            }
        
        retried = []
        skipped = []
        
        for task in failed_tasks:
            failure_type = self.classify_failure(task.last_error)
            
            if self.should_retry(task, failure_type):
                # Schedule retry
                delay = self.calculate_retry_delay(task.attempts + 1, failure_type)
                task.status = TaskStatus.PENDING
                task.retry_after = datetime.utcnow() + timedelta(seconds=delay)
                task.retry_count = (task.retry_count or 0) + 1
                
                retried.append({
                    'task_id': task.id,
                    'account': task.account.site_name,
                    'retry_after': task.retry_after.isoformat()
                })
                
                # Schedule async retry
                asyncio.create_task(self._execute_delayed_retry(db, task.id, delay))
            else:
                skipped.append({
                    'task_id': task.id,
                    'account': task.account.site_name,
                    'reason': 'Exceeded retry limits or non-retryable error'
                })
        
        db.commit()
        
        # Log bulk retry
        await self.audit_service.log_action(
            db=db,
            user_id=user_id,
            account_id=None,
            action="bulk_retry_scheduled",
            details={
                'total_tasks': len(failed_tasks),
                'retried': len(retried),
                'skipped': len(skipped)
            }
        )
        
        return {
            'success': True,
            'message': f'Scheduled {len(retried)} tasks for retry',
            'retried': retried,
            'skipped': skipped
        }
    
    async def get_retry_status(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get retry status for user's tasks"""
        # Get tasks with retry information
        tasks = db.query(DeletionTask).join(Account).filter(
            Account.user_id == user_id,
            DeletionTask.retry_count > 0
        ).all()
        
        # Categorize by status
        retrying = []
        succeeded_after_retry = []
        failed_after_retry = []
        
        for task in tasks:
            task_info = {
                'task_id': task.id,
                'account': task.account.site_name,
                'retry_count': task.retry_count,
                'attempts': task.attempts,
                'status': task.status.value
            }
            
            if task.status == TaskStatus.PENDING and task.retry_after:
                task_info['retry_after'] = task.retry_after.isoformat()
                retrying.append(task_info)
            elif task.status == TaskStatus.COMPLETED:
                succeeded_after_retry.append(task_info)
            elif task.status == TaskStatus.FAILED:
                task_info['last_error'] = task.last_error
                failed_after_retry.append(task_info)
        
        return {
            'total_retried_tasks': len(tasks),
            'currently_retrying': retrying,
            'succeeded_after_retry': succeeded_after_retry,
            'failed_after_retry': failed_after_retry,
            'success_rate': len(succeeded_after_retry) / len(tasks) if tasks else 0
        }
    
    async def configure_retry_strategy(self, failure_type: str, 
                                      config: Dict[str, Any]) -> bool:
        """Configure retry strategy for a specific failure type"""
        if failure_type not in self.RETRY_STRATEGIES:
            return False
        
        # Update strategy configuration
        self.RETRY_STRATEGIES[failure_type].update(config)
        return True
    
    def get_retry_strategies(self) -> Dict[str, Dict]:
        """Get current retry strategies configuration"""
        return self.RETRY_STRATEGIES.copy()
    
    async def cancel_retry(self, db: Session, task_id: int) -> bool:
        """Cancel a scheduled retry"""
        task = db.query(DeletionTask).filter(
            DeletionTask.id == task_id,
            DeletionTask.status == TaskStatus.PENDING
        ).first()
        
        if not task or not task.retry_after:
            return False
        
        # Mark as failed with cancellation note
        task.status = TaskStatus.FAILED
        task.last_error = "Retry cancelled by user"
        task.retry_after = None
        
        db.commit()
        
        # Log cancellation
        await self.audit_service.log_action(
            db=db,
            user_id=task.account.user_id,
            account_id=task.account_id,
            action="retry_cancelled",
            details={'task_id': task_id}
        )
        
        return True


# Singleton instance
retry_service = RetryService()