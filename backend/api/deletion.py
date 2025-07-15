from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from database import get_db
from models import Account, DeletionTask, TaskStatus, DeletionMethod
from services.deletion_service import DeletionService
from services.audit_service import AuditService

router = APIRouter()


class StartDeletionRequest(BaseModel):
    account_ids: List[int]


class ConfirmDeletionRequest(BaseModel):
    task_id: int


class DeletionTaskResponse(BaseModel):
    id: int
    account_id: int
    method: str
    status: str
    attempts: int
    last_error: str = None
    created_at: str
    completed_at: str = None
    
    class Config:
        from_attributes = True


@router.post("/deletion/start")
async def start_deletion(
    request: StartDeletionRequest,
    db: Session = Depends(get_db)
):
    """Start deletion process for selected accounts"""
    
    # Validate account IDs
    accounts = db.query(Account).filter(Account.id.in_(request.account_ids)).all()
    if len(accounts) != len(request.account_ids):
        raise HTTPException(
            status_code=400,
            detail="Some account IDs are invalid"
        )
    
    deletion_service = DeletionService()
    audit_service = AuditService()
    
    created_tasks = []
    
    for account in accounts:
        # Create deletion task
        task = DeletionTask(
            account_id=account.id,
            method=DeletionMethod.AUTOMATED,  # Start with automated, fallback to email
            status=TaskStatus.PENDING
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Log task creation
        await audit_service.log_action(
            db=db,
            account_id=account.id,
            action="deletion_task_created",
            details={
                "task_id": task.id,
                "method": task.method.value,
                "site_name": account.site_name
            }
        )
        
        created_tasks.append(task)
    
    # Start background processing
    await deletion_service.process_tasks(created_tasks)
    
    return {
        "message": f"Started deletion process for {len(created_tasks)} accounts",
        "task_ids": [task.id for task in created_tasks]
    }


@router.get("/deletion/tasks")
async def get_deletion_tasks(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """Get deletion tasks with optional filtering"""
    
    query = db.query(DeletionTask)
    
    if status:
        query = query.filter(DeletionTask.status == status)
    
    tasks = query.offset(skip).limit(limit).all()
    
    return tasks


@router.get("/deletion/status/{task_id}")
async def get_deletion_status(task_id: int, db: Session = Depends(get_db)):
    """Get status of specific deletion task"""
    
    task = db.query(DeletionTask).filter(DeletionTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task.id,
        "status": task.status.value,
        "method": task.method.value,
        "attempts": task.attempts,
        "last_error": task.last_error,
        "account": {
            "id": task.account.id,
            "site_name": task.account.site_name,
            "site_url": task.account.site_url,
            "username": task.account.username
        }
    }


@router.post("/deletion/confirm/{task_id}")
async def confirm_deletion(task_id: int, db: Session = Depends(get_db)):
    """Confirm a deletion action that requires user approval"""
    
    task = db.query(DeletionTask).filter(DeletionTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != TaskStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="Task is not in pending state"
        )
    
    # Update task status
    task.status = TaskStatus.IN_PROGRESS
    db.commit()
    
    # Log confirmation
    audit_service = AuditService()
    await audit_service.log_action(
        db=db,
        account_id=task.account_id,
        action="deletion_confirmed",
        details={
            "task_id": task.id,
            "method": task.method.value
        }
    )
    
    # Continue with deletion process
    deletion_service = DeletionService()
    await deletion_service.execute_deletion(task)
    
    return {"message": "Deletion confirmed and will proceed"}


@router.post("/deletion/email/{account_id}")
async def send_email_deletion(account_id: int, db: Session = Depends(get_db)):
    """Send email deletion request for account"""
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Create email deletion task
    task = DeletionTask(
        account_id=account_id,
        method=DeletionMethod.EMAIL,
        status=TaskStatus.PENDING
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Send email
    deletion_service = DeletionService()
    result = await deletion_service.send_deletion_email(task)
    
    # Log email sent
    audit_service = AuditService()
    await audit_service.log_action(
        db=db,
        account_id=account_id,
        action="deletion_email_sent",
        details={
            "task_id": task.id,
            "privacy_email": task.privacy_email,
            "success": result.get("success", False)
        }
    )
    
    return {
        "message": "Deletion email sent successfully",
        "task_id": task.id,
        "privacy_email": task.privacy_email
    }


@router.post("/deletion/retry/{task_id}")
async def retry_deletion(task_id: int, db: Session = Depends(get_db)):
    """Retry a failed deletion task"""
    
    task = db.query(DeletionTask).filter(DeletionTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != TaskStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail="Task is not in failed state"
        )
    
    # Reset task for retry
    task.status = TaskStatus.PENDING
    task.attempts += 1
    task.last_error = None
    db.commit()
    
    # Log retry
    audit_service = AuditService()
    await audit_service.log_action(
        db=db,
        account_id=task.account_id,
        action="deletion_retry",
        details={
            "task_id": task.id,
            "attempt": task.attempts
        }
    )
    
    # Process task
    deletion_service = DeletionService()
    await deletion_service.execute_deletion(task)
    
    return {"message": "Deletion task retried"}


@router.delete("/deletion/cancel/{task_id}")
async def cancel_deletion(task_id: int, db: Session = Depends(get_db)):
    """Cancel a pending deletion task"""
    
    task = db.query(DeletionTask).filter(DeletionTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=400,
            detail="Task cannot be cancelled in current state"
        )
    
    # Cancel task
    db.delete(task)
    db.commit()
    
    # Log cancellation
    audit_service = AuditService()
    await audit_service.log_action(
        db=db,
        account_id=task.account_id,
        action="deletion_cancelled",
        details={
            "task_id": task.id,
            "method": task.method.value
        }
    )
    
    return {"message": "Deletion task cancelled"}