from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum, Numeric, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
import json

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Session management
    session_duration_hours = Column(Integer, default=24)
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # Password reset
    reset_token = Column(String)
    reset_token_expires = Column(DateTime)
    
    # Relationships
    accounts = relationship("Account", back_populates="user")
    user_settings = relationship("UserSettings", back_populates="user", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="user")


class AccountStatus(PyEnum):
    DISCOVERED = "discovered"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class DeletionMethod(PyEnum):
    AUTOMATED = "automated"
    EMAIL = "email"


class TaskStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class LLMProvider(PyEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMTaskType(PyEnum):
    DISCOVERY = "discovery"
    NAVIGATION = "navigation"
    EMAIL_GENERATION = "email_generation"


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    site_name = Column(String, nullable=False)
    site_url = Column(String, nullable=False)
    username = Column(String, nullable=False)
    encrypted_password = Column(Text, nullable=False)  # Encrypted password using AES
    email = Column(String)
    status = Column(Enum(AccountStatus), default=AccountStatus.DISCOVERED)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    deletion_tasks = relationship("DeletionTask", back_populates="account")
    audit_logs = relationship("AuditLog", back_populates="account")
    llm_interactions = relationship("LLMInteraction", back_populates="account")


class DeletionTask(Base):
    __tablename__ = "deletion_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    method = Column(Enum(DeletionMethod), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    attempts = Column(Integer, default=0)
    last_error = Column(Text)
    deletion_url = Column(String)
    privacy_email = Column(String)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    
    # Relationships
    account = relationship("Account", back_populates="deletion_tasks")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))
    action = Column(String, nullable=False)
    details = Column(JSON)
    masked_credentials = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    user_agent = Column(String)
    ip_address = Column(String)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    account = relationship("Account", back_populates="audit_logs")


class LLMInteraction(Base):
    __tablename__ = "llm_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    provider = Column(Enum(LLMProvider), nullable=False)
    task_type = Column(Enum(LLMTaskType), nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    cost = Column(Numeric(10, 4), default=0.0000)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="llm_interactions")


class SiteMetadata(Base):
    __tablename__ = "site_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    site_name = Column(String, unique=True, nullable=False)
    site_url = Column(String, nullable=False)
    deletion_url = Column(String)
    privacy_email = Column(String)
    deletion_instructions = Column(Text)
    automation_difficulty = Column(Integer, default=5)  # 1-10 scale
    last_updated = Column(DateTime, default=func.now())
    success_rate = Column(Numeric(5, 2), default=0.0)  # Percentage
    
    # Metadata for automation
    login_selectors = Column(JSON)  # CSS selectors for login form
    deletion_selectors = Column(JSON)  # CSS selectors for deletion process
    confirmation_texts = Column(JSON)  # Expected confirmation texts


class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Email settings
    email = Column(String)
    email_password = Column(String)  # Encrypted
    name = Column(String)
    
    # Preferences
    auto_confirm_deletions = Column(Boolean, default=False)
    email_notifications = Column(Boolean, default=True)
    max_cost_per_deletion = Column(Numeric(10, 2), default=5.00)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_settings")