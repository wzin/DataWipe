from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from pathlib import Path

from database import get_db
from models import User
from services.csv_parser import CSVParser
from services.llm_service import LLMService
from services.audit_service import AuditService
from api.auth import get_current_active_user
from config import settings

router = APIRouter()


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload and process CSV file from password manager"""
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_path = Path(settings.upload_dir) / f"{file_id}_{file.filename}"
    
    try:
        # Save uploaded file
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Parse CSV file with format detection
        parser = CSVParser()
        
        # First detect the format
        import pandas as pd
        df = pd.read_csv(str(file_path))
        detected_format, confidence = parser.detect_format(df)
        
        # Parse the CSV
        accounts = parser.parse_csv(str(file_path))
        
        # Use LLM to discover and enrich account information
        llm_service = LLMService()
        enriched_accounts = await llm_service.discover_accounts(accounts)
        
        # Save accounts to database with user association
        saved_accounts = []
        skipped_accounts = []
        for account_data in enriched_accounts:
            try:
                account = parser.save_account(db, account_data, current_user.id)
                saved_accounts.append(account)
            except Exception as e:
                skipped_accounts.append({
                    'site_name': account_data.get('site_name', 'Unknown'),
                    'reason': str(e)
                })
        
        # Log the upload
        audit_service = AuditService()
        await audit_service.log_action(
            db=db,
            user_id=current_user.id,
            account_id=None,
            action="csv_uploaded",
            details={
                "filename": file.filename,
                "detected_format": detected_format,
                "format_confidence": confidence,
                "accounts_imported": len(saved_accounts),
                "accounts_skipped": len(skipped_accounts)
            }
        )
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return {
            "message": f"Successfully processed {len(saved_accounts)} accounts",
            "accounts_discovered": len(saved_accounts),
            "accounts_skipped": len(skipped_accounts),
            "detected_format": detected_format,
            "format_confidence": round(confidence, 2),
            "file_id": file_id,
            "skipped_details": skipped_accounts[:5] if skipped_accounts else []
        }
        
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            os.remove(file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/upload/formats")
async def get_supported_formats():
    """Get supported file formats and their expected structure"""
    parser = CSVParser()
    supported = parser.get_supported_formats()
    
    return {
        "supported_formats": ["csv"],
        "password_managers": list(supported.keys()),
        "format_details": supported,
        "auto_detection": True,
        "notes": {
            "auto_detection": "DataWipe automatically detects the format of your CSV file",
            "supported_managers": "Supports exports from Bitwarden, LastPass, 1Password, Chrome, Firefox, KeePass, Dashlane, NordPass, RoboForm, and Enpass",
            "generic_format": "Can also parse generic CSV files with password, username/email, and URL columns"
        }
    }