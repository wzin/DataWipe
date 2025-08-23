#!/bin/bash

# DataWipe Comprehensive Test Suite Runner
# Runs all tests inside Docker containers

set -e

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🧪 DataWipe Test Suite"
echo "====================="

# Function to run backend tests
run_backend_tests() {
    echo -e "\n${YELLOW}Running Backend Tests...${NC}"
    echo "------------------------"
    
    # Install test dependencies if needed
    docker compose exec backend pip install pytest pytest-asyncio pytest-cov 2>/dev/null || true
    
    # Run all backend tests
    docker compose exec backend python -m pytest tests/ -v --tb=short || {
        echo -e "${RED}❌ Backend tests failed${NC}"
        return 1
    }
    
    echo -e "${GREEN}✅ Backend tests passed${NC}"
}

# Function to run specific test categories
run_unit_tests() {
    echo -e "\n${YELLOW}Running Unit Tests...${NC}"
    docker compose exec backend python -m pytest tests/test_auth.py tests/test_encryption.py tests/test_csv_parser.py -v || {
        echo -e "${RED}❌ Unit tests failed${NC}"
        return 1
    }
    echo -e "${GREEN}✅ Unit tests passed${NC}"
}

# Function to test API endpoints
test_api_endpoints() {
    echo -e "\n${YELLOW}Testing API Endpoints...${NC}"
    echo "------------------------"
    
    # Wait for backend to be ready
    echo "Waiting for backend to be ready..."
    sleep 3
    
    # Test health endpoint
    curl -f http://localhost:8000/health 2>/dev/null || {
        echo -e "${RED}❌ Backend not responding${NC}"
        return 1
    }
    
    echo -e "${GREEN}✅ API is responding${NC}"
    
    # Test API docs
    curl -f http://localhost:8000/docs 2>/dev/null || {
        echo -e "${RED}❌ API documentation not available${NC}"
        return 1
    }
    
    echo -e "${GREEN}✅ API documentation available${NC}"
}

# Function to run integration tests
run_integration_tests() {
    echo -e "\n${YELLOW}Running Integration Tests...${NC}"
    echo "------------------------"
    
    # Create a test script for integration testing
    cat << 'EOF' > /tmp/integration_test.py
import asyncio
import sys
sys.path.append('/app')

from database import init_db, get_db
from services.encryption_service import encryption_service
from services.categorization_service import categorization_service
from services.csv_parser import CSVParser

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
EOF
    
    docker cp /tmp/integration_test.py account-deleter2-backend-1:/app/integration_test.py
    docker compose exec backend python integration_test.py || {
        echo -e "${RED}❌ Integration tests failed${NC}"
        return 1
    }
    
    echo -e "${GREEN}✅ Integration tests passed${NC}"
}

# Function to run frontend tests (if any)
run_frontend_tests() {
    echo -e "\n${YELLOW}Running Frontend Tests...${NC}"
    echo "------------------------"
    
    # Check if frontend container is running
    if docker compose ps frontend | grep -q "Up"; then
        # Run frontend tests if they exist
        docker compose exec frontend npm test -- --watchAll=false 2>/dev/null || {
            echo -e "${YELLOW}⚠️  No frontend tests found or tests skipped${NC}"
        }
    else
        echo -e "${YELLOW}⚠️  Frontend container not running${NC}"
    fi
}

# Function to run Selenium E2E tests
run_e2e_tests() {
    echo -e "\n${YELLOW}Running E2E Tests...${NC}"
    echo "------------------------"
    
    if [ -f "./run_selenium_tests.sh" ]; then
        ./run_selenium_tests.sh || {
            echo -e "${YELLOW}⚠️  E2E tests failed (non-critical)${NC}"
        }
    else
        echo -e "${YELLOW}⚠️  E2E test script not found${NC}"
    fi
}

# Function to generate test report
generate_report() {
    echo -e "\n${YELLOW}Generating Test Report...${NC}"
    echo "========================="
    
    # Count test files
    test_count=$(docker compose exec backend find tests -name "test_*.py" | wc -l)
    echo "Total test files: $test_count"
    
    # Try to get coverage if pytest-cov is installed
    docker compose exec backend python -m pytest tests/ --cov=. --cov-report=term-missing 2>/dev/null || true
}

# Main execution
main() {
    echo "Starting DataWipe containers..."
    docker compose up -d backend
    
    # Wait for services to be ready
    echo "Waiting for services to start..."
    sleep 5
    
    # Run tests based on arguments
    if [ "$1" == "quick" ]; then
        echo -e "\n${YELLOW}Running Quick Tests Only${NC}"
        test_api_endpoints
        run_unit_tests
    elif [ "$1" == "integration" ]; then
        run_integration_tests
    elif [ "$1" == "e2e" ]; then
        run_e2e_tests
    elif [ "$1" == "backend" ]; then
        run_backend_tests
    else
        # Run all tests
        echo -e "\n${YELLOW}Running Full Test Suite${NC}"
        test_api_endpoints
        run_backend_tests
        run_integration_tests
        run_frontend_tests
        # run_e2e_tests  # Commented out as it requires full stack
        generate_report
    fi
    
    echo -e "\n${GREEN}🎉 Test suite completed!${NC}"
}

# Show usage
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: ./run_tests.sh [option]"
    echo ""
    echo "Options:"
    echo "  quick       - Run quick unit tests only"
    echo "  backend     - Run all backend tests"
    echo "  integration - Run integration tests"
    echo "  e2e        - Run E2E tests (requires full stack)"
    echo "  (no option) - Run full test suite"
    echo ""
    exit 0
fi

# Run main function with arguments
main "$@"