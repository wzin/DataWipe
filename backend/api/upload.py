from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from pathlib import Path

from database import get_db
from services.csv_parser import CSVParser
from services.llm_service import LLMService
from config import settings

router = APIRouter()


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
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
        
        # Parse CSV file
        parser = CSVParser()
        accounts = parser.parse_csv(str(file_path))
        
        # Use LLM to discover and enrich account information
        llm_service = LLMService()
        enriched_accounts = await llm_service.discover_accounts(accounts)
        
        # Save accounts to database
        saved_accounts = []
        for account_data in enriched_accounts:
            account = parser.save_account(db, account_data)
            saved_accounts.append(account)
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return {
            "message": f"Successfully processed {len(saved_accounts)} accounts",
            "accounts_discovered": len(saved_accounts),
            "file_id": file_id
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
    return {
        "supported_formats": ["csv"],
        "expected_columns": {
            "bitwarden": ["name", "url", "username", "password", "notes"],
            "lastpass": ["name", "url", "username", "password", "extra"]
        },
        "sample_data": {
            "bitwarden": {
                "name": "Gmail",
                "url": "https://accounts.google.com",
                "username": "user@gmail.com",
                "password": "mypassword",
                "notes": "Personal email account"
            },
            "lastpass": {
                "name": "Facebook",
                "url": "https://facebook.com",
                "username": "user@example.com",
                "password": "mypassword",
                "extra": "Social media account"
            }
        }
    }