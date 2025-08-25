import asyncio
import sys
import pytest
sys.path.append('/app')

from database import init_db, get_db
from services.encryption_service import encryption_service
from services.categorization_service import categorization_service
from services.csv_parser import CSVParser

@pytest.mark.asyncio
async def test_integration():
    print("Testing database connection...")
    init_db()
    print("✓ Database connected")
    
    print("Testing encryption service...")
    encrypted = encryption_service.encrypt_password("test123")
    decrypted = encryption_service.decrypt_password(encrypted)
    assert decrypted == "test123"
    print("✓ Encryption working")
    
    print("Testing categorization service...")
    result = categorization_service.categorize_account("Facebook", "https://facebook.com")
    assert result['category'] == 'social_media'
    print("✓ Categorization working")
    
    print("Testing CSV parser...")
    parser = CSVParser()
    formats = parser.get_supported_formats()
    assert len(formats) >= 10
    print(f"✓ CSV parser supports {len(formats)} formats")
    
    print("\n✅ All integration tests passed!")

if __name__ == "__main__":
    asyncio.run(test_integration())
