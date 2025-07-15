#!/bin/bash
"""
End-to-End Test Runner for GDPR Account Deletion Assistant
Usage: ./run_e2e_tests.sh [backend_url] [frontend_url]
"""

set -e

# Default URLs
BACKEND_URL=${1:-"http://localhost:8000"}
FRONTEND_URL=${2:-"http://localhost:3000"}

echo "🧪 GDPR Account Deletion Assistant - E2E Test Runner"
echo "=================================================="
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""

# Check if containers are running
echo "📋 Checking Docker containers..."
if ! docker ps | grep -q "account-deleter2-backend"; then
    echo "❌ Backend container not running. Starting containers..."
    docker compose up -d
    echo "⏳ Waiting for services to start..."
    sleep 10
fi

# Check if services are accessible
echo "🔍 Verifying service accessibility..."
if ! curl -s "$BACKEND_URL/health" > /dev/null; then
    echo "❌ Backend not accessible at $BACKEND_URL"
    exit 1
fi

if ! curl -s "$FRONTEND_URL" > /dev/null; then
    echo "❌ Frontend not accessible at $FRONTEND_URL"
    exit 1
fi

echo "✅ Services are accessible"
echo ""

# Run the test suite
echo "🚀 Running E2E Test Suite..."
echo "=================================================="
python tests/test_e2e.py

echo ""
echo "📊 Test run completed. Check the detailed report for full results."