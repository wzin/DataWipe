import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

# Import after setting env
from fastapi.testclient import TestClient
from database import Base, engine, SessionLocal, get_db
from main import app
from models import User

# Create tables
Base.metadata.create_all(bind=engine)

# Override get_db
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create client
client = TestClient(app)

# Test registration
response = client.post(
    "/api/auth/register",
    json={
        "username": "newuser",
        "email": "newuser@example.com", 
        "password": "ValidPass123!",
        "session_duration_hours": 12
    }
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("SUCCESS!")
    print(f"Response: {response.json()}")
else:
    print(f"Error: {response.text}")

# Cleanup
Base.metadata.drop_all(bind=engine)
os.unlink("test.db")
