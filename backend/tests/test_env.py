"""
This module must be imported FIRST in conftest.py to set up test environment
"""
import os
import sys

# Set test database URL before any other imports
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["ENVIRONMENT"] = "testing"

# Ensure test settings are used
print("Test environment configured with DATABASE_URL=sqlite:///./test.db")