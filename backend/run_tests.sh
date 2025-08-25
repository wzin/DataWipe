#!/bin/bash
# Script to run tests with proper database configuration

# Set test environment
export DATABASE_URL="sqlite:///./test.db"
export ENVIRONMENT="testing"

# Remove old test database
rm -f test.db

# Run tests
python -m pytest tests/ "$@"

# Cleanup
rm -f test.db