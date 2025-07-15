#!/bin/bash
# Selenium E2E Test Runner for GDPR Account Deletion Assistant
# This script runs comprehensive browser-based tests to catch frontend-backend integration issues

set -e

echo "🧪 GDPR Account Deletion Assistant - Selenium E2E Tests"
echo "======================================================"

# First, let's fix the frontend configuration and restart
echo "🔧 Fixing frontend configuration..."
docker compose up -d --build frontend

echo "⏳ Waiting for services to stabilize..."
sleep 15

# Initialize database tables
echo "🗄️ Initializing database..."
docker compose exec backend python -c "
from database import init_db
from models import Base
from sqlalchemy import create_engine

# Create database and tables
engine = create_engine('sqlite:////app/data/accounts.db')
Base.metadata.create_all(engine)
print('Database tables created')
"

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

# Test API connectivity from within containers
echo "🔗 Testing API connectivity..."
docker compose exec backend python -c "
import requests
try:
    response = requests.get('http://localhost:8000/health')
    if response.status_code == 200:
        print('✅ Backend health check passed')
    else:
        print(f'❌ Backend health check failed: {response.status_code}')
        exit(1)
except Exception as e:
    print(f'❌ Backend health check failed: {e}')
    exit(1)
"

echo "✅ Backend is healthy"

# Run quick API test to populate some data
echo "📊 Seeding test data..."
docker compose exec backend python -c "
import requests
import tempfile
import os

# Create test CSV
csv_content = '''name,url,username,password,notes
Test Gmail,https://accounts.google.com,test@gmail.com,pass123,Test account
Test GitHub,https://github.com,testuser,pass456,Test repository
'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
    f.write(csv_content)
    temp_file = f.name

try:
    with open(temp_file, 'rb') as f:
        files = {'file': ('test.csv', f, 'text/csv')}
        response = requests.post('http://localhost:8000/api/upload', files=files)
        print(f'Data seeded: {response.status_code}')
finally:
    os.unlink(temp_file)
"

# Build and run Selenium tests
echo "🚀 Building Selenium test container..."
docker compose build e2e-tests

echo "🧪 Running Selenium E2E tests..."
docker compose --profile testing run --rm e2e-tests

# Copy test results out of container
echo "📄 Copying test results..."
docker compose --profile testing run --rm -v "$(pwd)/tests/selenium:/host" e2e-tests bash -c "
if [ -f selenium_report.html ]; then
    cp selenium_report.html /host/
    echo 'Test report copied to tests/selenium/selenium_report.html'
else
    echo 'No test report found'
fi
"

echo "✅ Selenium tests completed!"
echo "📊 Check tests/selenium/selenium_report.html for detailed results"

# Clean up test containers
echo "🧹 Cleaning up test containers..."
docker compose --profile testing down