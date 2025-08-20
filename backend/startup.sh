#!/bin/bash

# Install missing dependencies that weren't in the Docker image
pip install python-jose[cryptography] playwright passlib[bcrypt] aiosmtplib

# Install Playwright browsers (if needed)
# playwright install chromium

# Start the application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload