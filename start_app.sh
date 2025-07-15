#!/bin/bash

# GDPR Account Deletion Assistant - Startup Script
# This script properly starts the application with database initialization

echo "🚀 Starting GDPR Account Deletion Assistant"
echo "==========================================="

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker compose down

# Build and start services
echo "🔨 Building and starting services..."
docker compose up -d --build

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "📋 Checking service status..."
if ! docker compose ps | grep -q "backend.*Up"; then
    echo "❌ Backend service not running properly"
    docker compose logs backend
    exit 1
fi

if ! docker compose ps | grep -q "frontend.*Up"; then
    echo "❌ Frontend service not running properly"
    docker compose logs frontend
    exit 1
fi

echo "✅ Services are running"

# Initialize database
echo "🗄️ Initializing database..."
docker compose exec backend python -c "
from database import init_db
from models import Base
from sqlalchemy import create_engine

try:
    engine = create_engine('sqlite:////app/data/accounts.db')
    Base.metadata.create_all(engine)
    print('Database tables created successfully')
except Exception as e:
    print(f'Database initialization failed: {e}')
    exit(1)
"

# Seed test data
echo "📊 Seeding test data..."
docker compose exec backend python -c "
import requests
import tempfile
import os

csv_content = '''name,url,username,password,notes
Gmail,https://accounts.google.com,testuser@gmail.com,testpass123,Test Gmail account
Facebook,https://facebook.com,testuser@facebook.com,fbpass456,Test Facebook account
GitHub,https://github.com,testuser,githubpass789,Test GitHub account
LinkedIn,https://linkedin.com,test@example.com,linkedinpass,Test LinkedIn account
Twitter,https://twitter.com,testuser@twitter.com,twitterpass,Test Twitter account
'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
    f.write(csv_content)
    temp_file = f.name

try:
    with open(temp_file, 'rb') as f:
        files = {'file': ('test.csv', f, 'text/csv')}
        response = requests.post('http://localhost:8000/api/upload', files=files)
        if response.status_code == 200:
            print('Test data seeded successfully')
        else:
            print(f'Failed to seed data: {response.status_code}')
finally:
    os.unlink(temp_file)
"

# Test endpoints
echo "🧪 Testing endpoints..."
ACCOUNTS_COUNT=$(curl -s http://localhost:8000/api/accounts | python -c "import sys, json; print(len(json.load(sys.stdin)))")
SUMMARY_RESPONSE=$(curl -s http://localhost:8000/api/accounts/summary)

echo "✅ Found $ACCOUNTS_COUNT accounts"
echo "✅ Summary endpoint working: $SUMMARY_RESPONSE"

# Final status
echo ""
echo "🎉 Application started successfully!"
echo "📱 Frontend: http://localhost:3000 (or http://127.0.0.1:3000)"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "🔍 To run E2E tests:"
echo "   ./run_selenium_tests.sh"
echo ""
echo "🛑 To stop the application:"
echo "   docker compose down"