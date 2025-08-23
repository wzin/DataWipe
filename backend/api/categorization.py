from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel

from database import get_db
from models import User, Account
from services.categorization_service import categorization_service
from api.auth import get_current_active_user
from services.audit_service import AuditService

router = APIRouter()


class CategoryUpdateRequest(BaseModel):
    """Request to update account category"""
    category: str
    risk_level: Optional[str] = None
    deletion_priority: Optional[int] = None


class BulkCategorizeRequest(BaseModel):
    """Request to categorize multiple accounts"""
    account_ids: List[int]
    auto_categorize: bool = True


class CategoryStatsResponse(BaseModel):
    """Response with category statistics"""
    total_accounts: int
    by_category: Dict
    by_risk_level: Dict
    recommendations: List[Dict]


@router.post("/accounts/categorize/{account_id}")
async def categorize_single_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Auto-categorize a single account"""
    
    # Get the account
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    try:
        # Categorize the account
        category_info = categorization_service.categorize_account(
            account.site_name, 
            account.site_url
        )
        
        # Update account with category information
        account.category = category_info['category']
        account.category_confidence = category_info['confidence']
        account.risk_level = category_info['risk_level']
        account.data_sensitivity = category_info['data_sensitivity']
        
        # Assess deletion priority
        priority_score, _ = categorization_service.assess_deletion_priority(
            category_info['category'],
            category_info['risk_level']
        )
        account.deletion_priority = priority_score
        
        db.commit()
        db.refresh(account)
        
        # Log the action
        audit_service = AuditService()
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            account_id=account_id,
            action="account_categorized",
            details={
                "category": category_info['category'],
                "risk_level": category_info['risk_level']
            }
        )
        
        return {
            "account_id": account_id,
            "site_name": account.site_name,
            "category": account.category,
            "category_name": category_info['category_name'],
            "confidence": account.category_confidence,
            "risk_level": account.risk_level,
            "data_sensitivity": account.data_sensitivity,
            "deletion_priority": account.deletion_priority
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to categorize account: {str(e)}"
        )


@router.post("/accounts/categorize/bulk")
async def bulk_categorize_accounts(
    request: BulkCategorizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk categorize multiple accounts"""
    
    # Get all accounts
    accounts = db.query(Account).filter(
        Account.id.in_(request.account_ids),
        Account.user_id == current_user.id
    ).all()
    
    if not accounts:
        raise HTTPException(status_code=404, detail="No accounts found")
    
    categorized = []
    errors = []
    
    for account in accounts:
        try:
            # Categorize the account
            category_info = categorization_service.categorize_account(
                account.site_name,
                account.site_url
            )
            
            # Update account
            account.category = category_info['category']
            account.category_confidence = category_info['confidence']
            account.risk_level = category_info['risk_level']
            account.data_sensitivity = category_info['data_sensitivity']
            
            # Assess deletion priority
            priority_score, _ = categorization_service.assess_deletion_priority(
                category_info['category'],
                category_info['risk_level']
            )
            account.deletion_priority = priority_score
            
            categorized.append({
                "account_id": account.id,
                "site_name": account.site_name,
                "category": account.category,
                "risk_level": account.risk_level
            })
            
        except Exception as e:
            errors.append({
                "account_id": account.id,
                "error": str(e)
            })
    
    # Commit all changes
    db.commit()
    
    # Log the action
    audit_service = AuditService()
    await audit_service.log_action(
        db=db,
        user_id=current_user.id,
        account_id=None,
        action="bulk_categorization",
        details={
            "total_accounts": len(accounts),
            "successfully_categorized": len(categorized),
            "errors": len(errors)
        }
    )
    
    return {
        "message": f"Categorized {len(categorized)} accounts",
        "categorized": categorized,
        "errors": errors
    }


@router.put("/accounts/{account_id}/category")
async def update_account_category(
    account_id: int,
    update_request: CategoryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Manually update account category"""
    
    # Get the account
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Update category
    account.category = update_request.category
    account.category_confidence = 1.0  # Manual categorization has full confidence
    
    if update_request.risk_level:
        account.risk_level = update_request.risk_level
    
    if update_request.deletion_priority:
        account.deletion_priority = update_request.deletion_priority
    
    db.commit()
    db.refresh(account)
    
    return {
        "account_id": account_id,
        "site_name": account.site_name,
        "category": account.category,
        "risk_level": account.risk_level,
        "deletion_priority": account.deletion_priority,
        "message": "Category updated successfully"
    }


@router.get("/accounts/categories/stats", response_model=CategoryStatsResponse)
async def get_category_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get statistics about account categories"""
    
    # Get all user accounts
    accounts = db.query(Account).filter(
        Account.user_id == current_user.id
    ).all()
    
    # Convert to dictionaries for the service
    account_dicts = [
        {
            'id': acc.id,
            'category': acc.category,
            'risk_level': acc.risk_level,
            'site_name': acc.site_name
        }
        for acc in accounts
    ]
    
    # Get statistics
    stats = categorization_service.get_category_stats(account_dicts)
    
    return stats


@router.get("/accounts/categories/suggestions")
async def get_bulk_action_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get suggested bulk actions based on account patterns"""
    
    # Get all user accounts
    accounts = db.query(Account).filter(
        Account.user_id == current_user.id
    ).all()
    
    # Convert to dictionaries
    account_dicts = [
        {
            'id': acc.id,
            'category': acc.category,
            'risk_level': acc.risk_level,
            'site_name': acc.site_name
        }
        for acc in accounts
    ]
    
    # Get suggestions
    suggestions = categorization_service.suggest_bulk_actions(account_dicts)
    
    return {
        "suggestions": suggestions
    }


@router.get("/categories/list")
async def get_available_categories(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available categories with descriptions"""
    
    categories = []
    for category_id, category_data in categorization_service.CATEGORIES.items():
        categories.append({
            "id": category_id,
            "name": category_data['name'],
            "description": category_data['description'],
            "risk_level": category_data['risk_level'],
            "data_sensitivity": category_data['data_sensitivity']
        })
    
    return {
        "categories": categories
    }