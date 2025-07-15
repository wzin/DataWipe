#!/usr/bin/env python3
"""
Simple Frontend Integration Test
This test verifies that the frontend can properly communicate with the backend API
"""

import requests
import time
import json

def test_frontend_backend_integration():
    """Test that frontend can communicate with backend through browser"""
    
    # Test from host machine (how browser will access it)
    print("Testing frontend-backend integration...")
    
    # Check if frontend serves the page
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        print(f"✅ Frontend accessible: {response.status_code}")
        
        # Check if the built app includes the correct API URL
        if "backend:8000" in response.text:
            print("⚠️  ISSUE FOUND: Frontend is configured to use 'backend:8000' which is not accessible from browser")
            print("   The browser needs to access the backend via 'localhost:8000' from the host machine")
            return False
        else:
            print("✅ Frontend configuration looks correct")
            
    except Exception as e:
        print(f"❌ Frontend not accessible: {e}")
        return False
    
    # Test backend API directly
    try:
        response = requests.get("http://localhost:8000/api/accounts", timeout=10)
        print(f"✅ Backend API accessible: {response.status_code}")
        
        if response.status_code == 200:
            accounts = response.json()
            print(f"✅ Backend returned {len(accounts)} accounts")
        else:
            print(f"❌ Backend API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Backend API not accessible: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_frontend_backend_integration()
    if success:
        print("\n🎉 Frontend-Backend integration test PASSED")
    else:
        print("\n❌ Frontend-Backend integration test FAILED")
        print("\nTo fix this issue:")
        print("1. The React app needs to be built with REACT_APP_API_URL=http://localhost:8000")
        print("2. Or use a reverse proxy to route API calls from the frontend")
    exit(0 if success else 1)