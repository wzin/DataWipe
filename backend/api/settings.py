from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from database import get_db
from models import UserSettings
from services.email_service import EmailService

router = APIRouter()


class EmailSettingsRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    
    
class EmailSettingsResponse(BaseModel):
    email: str
    name: Optional[str]
    provider: str
    configured: bool
    app_password_required: bool


@router.post("/settings/email")
async def configure_email(
    request: EmailSettingsRequest,
    db: Session = Depends(get_db)
):
    """Configure user's email settings"""
    
    # Test email configuration
    email_service = EmailService(request.email, request.password)
    test_result = await email_service.test_email_configuration()
    
    if not test_result['success']:
        raise HTTPException(
            status_code=400,
            detail=f"Email configuration failed: {test_result['error']}"
        )
    
    # Save email settings (encrypted)
    user_settings = db.query(UserSettings).filter(
        UserSettings.user_id == "default"  # For now, single user
    ).first()
    
    if not user_settings:
        user_settings = UserSettings(
            user_id="default",
            email=request.email,
            email_password=request.password,  # This should be encrypted
            name=request.name
        )
        db.add(user_settings)
    else:
        user_settings.email = request.email
        user_settings.email_password = request.password  # This should be encrypted
        user_settings.name = request.name
    
    db.commit()
    
    return {
        "message": "Email configuration saved successfully",
        "email": request.email,
        "provider": test_result['provider'],
        "app_password_required": test_result['app_password_required']
    }


@router.get("/settings/email", response_model=EmailSettingsResponse)
async def get_email_settings(db: Session = Depends(get_db)):
    """Get current email settings"""
    
    user_settings = db.query(UserSettings).filter(
        UserSettings.user_id == "default"
    ).first()
    
    if not user_settings or not user_settings.email:
        raise HTTPException(
            status_code=404,
            detail="Email settings not configured"
        )
    
    # Test current configuration
    email_service = EmailService(user_settings.email, user_settings.email_password)
    test_result = await email_service.test_email_configuration()
    
    return EmailSettingsResponse(
        email=user_settings.email,
        name=user_settings.name,
        provider=user_settings.email.split('@')[1],
        configured=test_result['success'],
        app_password_required=test_result.get('app_password_required', False)
    )


@router.post("/settings/email/test")
async def test_email_settings(
    request: EmailSettingsRequest,
    db: Session = Depends(get_db)
):
    """Test email settings without saving"""
    
    email_service = EmailService(request.email, request.password)
    test_result = await email_service.test_email_configuration()
    
    if not test_result['success']:
        raise HTTPException(
            status_code=400,
            detail=f"Email test failed: {test_result['error']}"
        )
    
    return {
        "message": "Email configuration is working",
        "provider": test_result['provider'],
        "smtp_server": test_result['smtp_server'],
        "smtp_port": test_result['smtp_port'],
        "app_password_required": test_result['app_password_required']
    }


@router.delete("/settings/email")
async def delete_email_settings(db: Session = Depends(get_db)):
    """Delete email settings"""
    
    user_settings = db.query(UserSettings).filter(
        UserSettings.user_id == "default"
    ).first()
    
    if user_settings:
        user_settings.email = None
        user_settings.email_password = None
        user_settings.name = None
        db.commit()
    
    return {"message": "Email settings deleted successfully"}


@router.get("/settings/email/providers")
async def get_supported_email_providers():
    """Get list of supported email providers with setup instructions"""
    
    return {
        "providers": [
            {
                "name": "Gmail",
                "domain": "gmail.com",
                "app_password_required": True,
                "setup_instructions": [
                    "Enable 2-factor authentication",
                    "Go to Google Account settings",
                    "Select Security > 2-Step Verification > App passwords",
                    "Generate app password for 'Mail'",
                    "Use the generated password, not your regular password"
                ],
                "help_url": "https://support.google.com/accounts/answer/185833"
            },
            {
                "name": "Outlook/Hotmail",
                "domain": "outlook.com",
                "app_password_required": False,
                "setup_instructions": [
                    "Use your regular email and password",
                    "If using 2FA, you may need an app password"
                ],
                "help_url": "https://support.microsoft.com/en-us/office/pop-imap-and-smtp-settings-for-outlook-com-d088b986-291d-42b8-9564-9c414e2aa040"
            },
            {
                "name": "Yahoo Mail",
                "domain": "yahoo.com",
                "app_password_required": True,
                "setup_instructions": [
                    "Enable 2-factor authentication",
                    "Go to Account Security settings",
                    "Generate app password",
                    "Use the generated password"
                ],
                "help_url": "https://help.yahoo.com/kb/generate-third-party-passwords-sln15241.html"
            }
        ]
    }