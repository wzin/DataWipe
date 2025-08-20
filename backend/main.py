from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import os
from pathlib import Path

from database import init_db, get_db
from models import Account, DeletionTask, AuditLog
from services.csv_parser import CSVParser
from services.llm_service import LLMService
from services.deletion_service import DeletionService
from services.email_service import EmailService
from api import accounts, deletion, audit, upload, settings, auth, accounts_manual
from config import settings as app_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting GDPR Account Deletion Assistant...")
    init_db()
    print("Database initialized")
    
    # Create upload directories
    Path(app_settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(app_settings.data_dir).mkdir(parents=True, exist_ok=True)
    Path(app_settings.logs_dir).mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="GDPR Account Deletion Assistant",
    description="AI-powered tool for automated account deletion and GDPR compliance",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# API Routes
app.include_router(auth.router, prefix="/api", tags=["auth"])  # Auth routes don't require authentication
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(accounts.router, prefix="/api", tags=["accounts"])
app.include_router(accounts_manual.router, prefix="/api", tags=["manual_accounts"])
app.include_router(deletion.router, prefix="/api", tags=["deletion"])
app.include_router(audit.router, prefix="/api", tags=["audit"])
app.include_router(settings.router, prefix="/api", tags=["settings"])


@app.get("/")
async def root():
    return {"message": "GDPR Account Deletion Assistant API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/stats")
async def get_stats(db = Depends(get_db)):
    """Get system statistics"""
    from sqlalchemy import func
    
    total_accounts = db.query(func.count(Account.id)).scalar()
    completed_deletions = db.query(func.count(DeletionTask.id)).filter(
        DeletionTask.status == "completed"
    ).scalar()
    
    return {
        "total_accounts": total_accounts,
        "completed_deletions": completed_deletions,
        "pending_deletions": db.query(func.count(DeletionTask.id)).filter(
            DeletionTask.status == "pending"
        ).scalar(),
        "failed_deletions": db.query(func.count(DeletionTask.id)).filter(
            DeletionTask.status == "failed"
        ).scalar()
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )