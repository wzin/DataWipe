from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from typing import Optional
from urllib.parse import urlparse

from database import get_db
from models import User, Account, AccountStatus
from services.encryption_service import encryption_service
from api.auth import get_current_active_user
from services.audit_service import AuditService

router = APIRouter()


class ManualAccountCreate(BaseModel):
    """Schema for manually creating an account"""
    site_name: str
    site_url: str
    username: str
    password: str
    email: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('site_url')
    def validate_url(cls, v):
        """Ensure URL is valid and has protocol"""
        if not v:
            raise ValueError("Site URL is required")
        
        # Add protocol if missing
        if not v.startswith(('http://', 'https://')):
            v = f'https://{v}'
        
        # Validate URL structure
        try:
            result = urlparse(v)
            if not result.netloc:
                raise ValueError("Invalid URL format")
        except:
            raise ValueError("Invalid URL format")
        
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """Ensure password is not empty"""
        if not v or len(v.strip()) == 0:
            raise ValueError("Password cannot be empty")
        return v
    
    @validator('email')
    def validate_email(cls, v):
        """Basic email validation"""
        if v and '@' not in v:
            raise ValueError("Invalid email format")
        return v


class ManualAccountResponse(BaseModel):
    """Response after creating account"""
    id: int
    site_name: str
    site_url: str
    username: str
    email: Optional[str]
    status: str
    message: str


@router.post("/manual", response_model=ManualAccountResponse)
async def create_manual_account(
    account_data: ManualAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Manually add a single account"""
    
    try:
        # Check if account already exists for this user
        existing = db.query(Account).filter(
            Account.user_id == current_user.id,
            Account.site_url == account_data.site_url,
            Account.username == account_data.username
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Account already exists for {account_data.site_name}"
            )
        
        # Create new account with encrypted password
        new_account = Account(
            user_id=current_user.id,
            site_name=account_data.site_name,
            site_url=account_data.site_url,
            username=account_data.username,
            encrypted_password=encryption_service.encrypt_password(account_data.password),
            email=account_data.email or "",
            status=AccountStatus.DISCOVERED
        )
        
        # Add notes if provided
        if account_data.notes:
            new_account.notes = account_data.notes
        
        db.add(new_account)
        db.commit()
        db.refresh(new_account)
        
        # Log the action
        audit_service = AuditService()
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            account_id=new_account.id,
            action="manual_account_added",
            details={
                "site_name": account_data.site_name,
                "site_url": account_data.site_url
            }
        )
        
        return ManualAccountResponse(
            id=new_account.id,
            site_name=new_account.site_name,
            site_url=new_account.site_url,
            username=new_account.username,
            email=new_account.email,
            status=new_account.status.value,
            message="Account added successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add account: {str(e)}"
        )


@router.put("/{account_id}/manual", response_model=ManualAccountResponse)
async def update_manual_account(
    account_id: int,
    account_data: ManualAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a manually added account"""
    
    # Get the account
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )
    
    try:
        # Update account fields
        account.site_name = account_data.site_name
        account.site_url = account_data.site_url
        account.username = account_data.username
        account.encrypted_password = encryption_service.encrypt_password(account_data.password)
        account.email = account_data.email or ""
        
        if account_data.notes:
            account.notes = account_data.notes
        
        db.commit()
        db.refresh(account)
        
        # Log the action
        audit_service = AuditService()
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            account_id=account.id,
            action="manual_account_updated",
            details={
                "site_name": account_data.site_name
            }
        )
        
        return ManualAccountResponse(
            id=account.id,
            site_name=account.site_name,
            site_url=account.site_url,
            username=account.username,
            email=account.email,
            status=account.status.value,
            message="Account updated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update account: {str(e)}"
        )


@router.get("/check-duplicate")
async def check_duplicate_account(
    site_url: str,
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Check if an account already exists"""
    
    # Normalize URL
    if not site_url.startswith(('http://', 'https://')):
        site_url = f'https://{site_url}'
    
    existing = db.query(Account).filter(
        Account.user_id == current_user.id,
        Account.site_url == site_url,
        Account.username == username
    ).first()
    
    return {
        "is_duplicate": existing is not None,
        "account_id": existing.id if existing else None,
        "site_name": existing.site_name if existing else None
    }


@router.get("/suggestions")
async def get_site_suggestions(
    query: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get site suggestions based on partial input"""
    
    # Common sites database
    common_sites = [
        {"name": "Google", "url": "https://accounts.google.com", "category": "tech"},
        {"name": "Facebook", "url": "https://www.facebook.com", "category": "social"},
        {"name": "Twitter/X", "url": "https://twitter.com", "category": "social"},
        {"name": "Instagram", "url": "https://www.instagram.com", "category": "social"},
        {"name": "LinkedIn", "url": "https://www.linkedin.com", "category": "professional"},
        {"name": "Amazon", "url": "https://www.amazon.com", "category": "shopping"},
        {"name": "Netflix", "url": "https://www.netflix.com", "category": "entertainment"},
        {"name": "Spotify", "url": "https://www.spotify.com", "category": "entertainment"},
        {"name": "GitHub", "url": "https://github.com", "category": "tech"},
        {"name": "Microsoft", "url": "https://account.microsoft.com", "category": "tech"},
        {"name": "Apple", "url": "https://appleid.apple.com", "category": "tech"},
        {"name": "Reddit", "url": "https://www.reddit.com", "category": "social"},
        {"name": "Discord", "url": "https://discord.com", "category": "social"},
        {"name": "TikTok", "url": "https://www.tiktok.com", "category": "social"},
        {"name": "Snapchat", "url": "https://www.snapchat.com", "category": "social"},
        {"name": "Pinterest", "url": "https://www.pinterest.com", "category": "social"},
        {"name": "Tumblr", "url": "https://www.tumblr.com", "category": "social"},
        {"name": "PayPal", "url": "https://www.paypal.com", "category": "finance"},
        {"name": "eBay", "url": "https://www.ebay.com", "category": "shopping"},
        {"name": "Etsy", "url": "https://www.etsy.com", "category": "shopping"},
        {"name": "Uber", "url": "https://www.uber.com", "category": "transport"},
        {"name": "Airbnb", "url": "https://www.airbnb.com", "category": "travel"},
        {"name": "Booking.com", "url": "https://www.booking.com", "category": "travel"},
        {"name": "Dropbox", "url": "https://www.dropbox.com", "category": "storage"},
        {"name": "Slack", "url": "https://slack.com", "category": "professional"},
        {"name": "Zoom", "url": "https://zoom.us", "category": "communication"},
        {"name": "Adobe", "url": "https://account.adobe.com", "category": "creative"},
        {"name": "Canva", "url": "https://www.canva.com", "category": "creative"},
        {"name": "Notion", "url": "https://www.notion.so", "category": "productivity"},
        {"name": "Evernote", "url": "https://evernote.com", "category": "productivity"}
    ]
    
    # Filter suggestions based on query
    query_lower = query.lower()
    suggestions = [
        site for site in common_sites
        if query_lower in site["name"].lower() or query_lower in site["url"].lower()
    ]
    
    # Limit to 10 suggestions
    return suggestions[:10]