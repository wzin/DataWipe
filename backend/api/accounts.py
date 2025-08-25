from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from database import get_db
from models import Account, AccountStatus, User
from services.audit_service import AuditService
from api.auth import get_current_active_user

router = APIRouter()


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    site_name: str
    site_url: str
    username: str
    email: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


class AccountUpdate(BaseModel):
    status: Optional[AccountStatus] = None


class BulkSelectRequest(BaseModel):
    account_ids: List[int]
    action: str  # "select" or "deselect"


@router.get("/accounts", response_model=List[AccountResponse])
async def get_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[AccountStatus] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of accounts with optional filtering"""
    
    query = db.query(Account).filter(Account.user_id == current_user.id)
    
    # Apply filters
    if status:
        query = query.filter(Account.status == status)
    
    if search:
        query = query.filter(
            Account.site_name.ilike(f"%{search}%") |
            Account.username.ilike(f"%{search}%") |
            Account.email.ilike(f"%{search}%")
        )
    
    # Apply pagination
    accounts = query.offset(skip).limit(limit).all()
    
    return accounts


@router.get("/accounts/summary")
async def get_accounts_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get summary statistics for accounts"""
    
    from sqlalchemy import func
    
    summary = db.query(
        Account.status,
        func.count(Account.id).label('count')
    ).filter(Account.user_id == current_user.id).group_by(Account.status).all()
    
    # Convert to dict
    status_counts = {status.value: 0 for status in AccountStatus}
    for status, count in summary:
        status_counts[status.value] = count
    
    return {
        "total_accounts": sum(status_counts.values()),
        "by_status": status_counts
    }


@router.get("/accounts/{account_id:int}", response_model=AccountResponse)
async def get_account(
    account_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific account details"""
    
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return account


@router.put("/accounts/{account_id:int}")
async def update_account(
    account_id: int,
    account_update: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update account information"""
    
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Update fields
    if account_update.status:
        old_status = account.status
        account.status = account_update.status
        
        # Log the status change
        audit_service = AuditService()
        await audit_service.log_action(
            db=db,
            account_id=account_id,
            action="status_changed",
            details={
                "old_status": old_status.value,
                "new_status": account_update.status.value
            }
        )
    
    db.commit()
    db.refresh(account)
    
    return {"message": "Account updated successfully"}


@router.delete("/accounts/{account_id:int}")
async def delete_account(
    account_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove account from system (not from the actual service)"""
    
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Log the deletion
    audit_service = AuditService()
    await audit_service.log_action(
        db=db,
        account_id=account_id,
        action="account_removed",
        details={
            "site_name": account.site_name,
            "username": account.username
        }
    )
    
    db.delete(account)
    db.commit()
    
    return {"message": "Account removed from system"}


@router.post("/accounts/bulk-select")
async def bulk_select_accounts(
    request: BulkSelectRequest,
    db: Session = Depends(get_db)
):
    """Select or deselect multiple accounts for deletion"""
    
    # Validate account IDs exist
    accounts = db.query(Account).filter(Account.id.in_(request.account_ids)).all()
    if len(accounts) != len(request.account_ids):
        raise HTTPException(
            status_code=400,
            detail="Some account IDs are invalid"
        )
    
    # Update status based on action
    new_status = AccountStatus.PENDING if request.action == "select" else AccountStatus.DISCOVERED
    
    for account in accounts:
        account.status = new_status
    
    db.commit()
    
    # Log bulk action
    audit_service = AuditService()
    await audit_service.log_action(
        db=db,
        account_id=None,
        action="bulk_select",
        details={
            "action": request.action,
            "account_count": len(request.account_ids),
            "account_ids": request.account_ids
        }
    )
    
    return {
        "message": f"Successfully {request.action}ed {len(accounts)} accounts",
        "updated_count": len(accounts)
    }