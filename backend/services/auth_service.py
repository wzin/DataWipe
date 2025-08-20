from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import secrets
import os

from models import User
from schemas.auth import TokenData

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


class AuthService:
    """Service for handling authentication and authorization"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> TokenData:
        """Verify and decode a JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("sub")
            username: str = payload.get("username")
            
            if user_id is None:
                raise credentials_exception
            
            token_data = TokenData(
                user_id=user_id,
                username=username,
                exp=payload.get("exp")
            )
            return token_data
            
        except JWTError:
            raise credentials_exception
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password"""
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return None
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            minutes_left = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is locked. Try again in {minutes_left} minutes."
            )
        
        # Verify password
        if not AuthService.verify_password(password, user.hashed_password):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            
            # Lock account if max attempts reached
            if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Account locked due to too many failed login attempts. Try again in {LOCKOUT_DURATION_MINUTES} minutes."
                )
            
            db.commit()
            return None
        
        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str, 
                   session_duration_hours: int = 24, is_superuser: bool = False) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Create new user
        hashed_password = AuthService.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            session_duration_hours=session_duration_hours,
            is_superuser=is_superuser
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> User:
        """Get the current user from a JWT token"""
        token_data = AuthService.verify_token(token)
        
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return user
    
    @staticmethod
    def create_password_reset_token(db: Session, email: str) -> str:
        """Create a password reset token for a user"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Don't reveal if email exists or not
            return None
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        
        db.commit()
        
        return reset_token
    
    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        """Reset a user's password using a reset token"""
        user = db.query(User).filter(
            User.reset_token == token,
            User.reset_token_expires > datetime.utcnow()
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Update password and clear reset token
        user.hashed_password = AuthService.get_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        user.failed_login_attempts = 0
        user.locked_until = None
        
        db.commit()
        
        return True
    
    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str) -> bool:
        """Change a user's password"""
        if not AuthService.verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        user.hashed_password = AuthService.get_password_hash(new_password)
        db.commit()
        
        return True
    
    @staticmethod
    def update_session_duration(db: Session, user: User, hours: int) -> User:
        """Update user's session duration preference"""
        user.session_duration_hours = hours
        db.commit()
        db.refresh(user)
        
        return user