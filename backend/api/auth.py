from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from database import get_db
from models import User
from schemas.auth import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    PasswordResetRequest, PasswordResetConfirm, PasswordChangeRequest,
    SessionUpdateRequest
)
from services.auth_service import AuthService
from services.audit_service import AuditService
from services.email_service import EmailService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Dependency to get the current authenticated user"""
    return AuthService.get_current_user(db, token)


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/auth/register", response_model=TokenResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        # Create user
        user = AuthService.create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            session_duration_hours=user_data.session_duration_hours
        )
        
        # Log registration
        audit_service = AuditService()
        await audit_service.log_action(
            db=db,
            user_id=user.id,
            account_id=None,
            action="user_registered",
            details={
                "username": user.username,
                "email": user.email
            },
            user_agent=request.headers.get("User-Agent"),
            ip_address=request.client.host
        )
        
        # Create access token
        access_token_expires = timedelta(hours=user.session_duration_hours)
        access_token = AuthService.create_access_token(
            data={"sub": user.id, "username": user.username},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            expires_in=user.session_duration_hours * 3600,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Login with username and password"""
    # Authenticate user
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        # Log failed login attempt
        audit_service = AuditService()
        await audit_service.log_action(
            db=db,
            user_id=None,
            account_id=None,
            action="login_failed",
            details={"username": form_data.username},
            user_agent=request.headers.get("User-Agent") if request else None,
            ip_address=request.client.host if request else None
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log successful login
    audit_service = AuditService()
    await audit_service.log_action(
        db=db,
        user_id=user.id,
        account_id=None,
        action="user_login",
        details={"username": user.username},
        user_agent=request.headers.get("User-Agent") if request else None,
        ip_address=request.client.host if request else None
    )
    
    # Create access token
    access_token_expires = timedelta(hours=user.session_duration_hours)
    access_token = AuthService.create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=user.session_duration_hours * 3600,
        user=UserResponse.from_orm(user)
    )


@router.post("/auth/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout the current user"""
    # Log logout
    audit_service = AuditService()
    await audit_service.log_action(
        db=db,
        user_id=current_user.id,
        account_id=None,
        action="user_logout",
        details={"username": current_user.username},
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host
    )
    
    return {"message": "Successfully logged out"}


@router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


@router.post("/auth/password-reset-request")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Request a password reset email"""
    # Create reset token
    reset_token = AuthService.create_password_reset_token(db, reset_request.email)
    
    if reset_token:
        # Send reset email
        email_service = EmailService()
        reset_url = f"http://localhost:3000/reset-password?token={reset_token}"
        
        try:
            await email_service.send_password_reset_email(
                email=reset_request.email,
                reset_url=reset_url
            )
        except Exception as e:
            # Log error but don't reveal if email exists
            print(f"Error sending password reset email: {e}")
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/auth/password-reset-confirm")
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    try:
        AuthService.reset_password(db, reset_confirm.token, reset_confirm.new_password)
        
        # Log password reset
        audit_service = AuditService()
        await audit_service.log_action(
            db=db,
            user_id=None,
            account_id=None,
            action="password_reset",
            details={"success": True},
            user_agent=request.headers.get("User-Agent"),
            ip_address=request.client.host
        )
        
        return {"message": "Password has been reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/auth/change-password")
async def change_password(
    password_change: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change the current user's password"""
    try:
        AuthService.change_password(
            db, 
            current_user, 
            password_change.current_password, 
            password_change.new_password
        )
        
        # Log password change
        audit_service = AuditService()
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            account_id=None,
            action="password_changed",
            details={"username": current_user.username},
            user_agent=request.headers.get("User-Agent"),
            ip_address=request.client.host
        )
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/auth/session-duration")
async def update_session_duration(
    session_update: SessionUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user's session duration preference"""
    user = AuthService.update_session_duration(
        db, 
        current_user, 
        session_update.session_duration_hours
    )
    
    return {
        "message": "Session duration updated",
        "session_duration_hours": user.session_duration_hours
    }


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Refresh the access token"""
    # Create new access token
    access_token_expires = timedelta(hours=current_user.session_duration_hours)
    access_token = AuthService.create_access_token(
        data={"sub": current_user.id, "username": current_user.username},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=current_user.session_duration_hours * 3600,
        user=UserResponse.from_orm(current_user)
    )