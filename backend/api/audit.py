from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
from models import AuditLog
from services.audit_service import AuditService

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: int
    account_id: int
    action: str
    details: dict
    masked_credentials: bool
    created_at: str
    user_agent: str = None
    ip_address: str = None
    
    class Config:
        from_attributes = True


@router.get("/audit", response_model=List[AuditLogResponse])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    action: Optional[str] = None,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get audit logs with optional filtering"""
    
    query = db.query(AuditLog)
    
    # Apply filters
    if action:
        query = query.filter(AuditLog.action == action)
    
    if account_id:
        query = query.filter(AuditLog.account_id == account_id)
    
    # Order by most recent first
    query = query.order_by(AuditLog.created_at.desc())
    
    # Apply pagination
    logs = query.offset(skip).limit(limit).all()
    
    return logs


@router.get("/audit/actions")
async def get_audit_actions(db: Session = Depends(get_db)):
    """Get list of all audit actions for filtering"""
    
    from sqlalchemy import func
    
    actions = db.query(AuditLog.action).distinct().all()
    
    return {
        "actions": [action[0] for action in actions]
    }


@router.get("/audit/summary")
async def get_audit_summary(db: Session = Depends(get_db)):
    """Get audit log summary statistics"""
    
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Total logs
    total_logs = db.query(func.count(AuditLog.id)).scalar()
    
    # Logs by action
    action_counts = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).all()
    
    # Recent activity (last 24 hours)
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_logs = db.query(func.count(AuditLog.id)).filter(
        AuditLog.created_at >= recent_cutoff
    ).scalar()
    
    # Credential reveals
    credential_reveals = db.query(func.count(AuditLog.id)).filter(
        AuditLog.action == "credentials_revealed"
    ).scalar()
    
    return {
        "total_logs": total_logs,
        "recent_activity": recent_logs,
        "credential_reveals": credential_reveals,
        "actions": {action: count for action, count in action_counts}
    }


@router.get("/audit/{log_id}")
async def get_audit_log(log_id: int, db: Session = Depends(get_db)):
    """Get specific audit log details"""
    
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    return log


@router.get("/audit/{log_id}/reveal")
async def reveal_credentials(log_id: int, db: Session = Depends(get_db)):
    """Reveal masked credentials in audit log"""
    
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    if not log.masked_credentials:
        raise HTTPException(
            status_code=400,
            detail="This log entry does not contain masked credentials"
        )
    
    # Get unmasked details
    audit_service = AuditService()
    unmasked_details = await audit_service.reveal_credentials(log)
    
    # Log the reveal action
    await audit_service.log_action(
        db=db,
        account_id=log.account_id,
        action="credentials_revealed",
        details={
            "log_id": log.id,
            "original_action": log.action
        },
        masked_credentials=False
    )
    
    return {
        "log_id": log.id,
        "action": log.action,
        "details": unmasked_details,
        "created_at": log.created_at.isoformat()
    }


@router.delete("/audit/cleanup")
async def cleanup_old_logs(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Clean up audit logs older than specified days"""
    
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Count logs to be deleted
    logs_to_delete = db.query(AuditLog).filter(
        AuditLog.created_at < cutoff_date
    ).count()
    
    if logs_to_delete == 0:
        return {"message": "No logs to cleanup", "deleted_count": 0}
    
    # Delete old logs
    db.query(AuditLog).filter(AuditLog.created_at < cutoff_date).delete()
    db.commit()
    
    # Log the cleanup action
    audit_service = AuditService()
    await audit_service.log_action(
        db=db,
        account_id=None,
        action="audit_cleanup",
        details={
            "deleted_count": logs_to_delete,
            "cutoff_days": days,
            "cutoff_date": cutoff_date.isoformat()
        },
        masked_credentials=False
    )
    
    return {
        "message": f"Successfully cleaned up {logs_to_delete} old audit logs",
        "deleted_count": logs_to_delete,
        "cutoff_date": cutoff_date.isoformat()
    }