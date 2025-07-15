FROM python:3.11-slim

# Install system dependencies for Chrome and Selenium
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Add Google Chrome repository
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

# Install Google Chrome
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && wget -N http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && rm chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver

# Set display port to avoid crash
ENV DISPLAY=:99

# Install Python dependencies
RUN pip install --no-cache-dir \
    selenium \
    pytest \
    pytest-html \
    requests \
    python-dotenv \
    webdriver-manager

# Create test user (non-root for security)
RUN useradd -m -s /bin/bash testuser
USER testuser

# Set working directory
WORKDIR /app/tests

# Copy test files
COPY --chown=testuser:testuser . .

# Run tests by default
CMD ["python", "-m", "pytest", "test_selenium_e2e.py", "-v", "--html=report.html", "--self-contained-html"]