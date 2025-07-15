from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./data/accounts.db"
    
    # LLM APIs
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Security
    secret_key: str = "your-secret-key-change-this"
    
    # Rate limiting
    max_requests_per_hour: int = 100
    delay_between_requests: int = 3
    
    # Budget control
    max_cost_per_deletion: float = 5.00
    daily_budget_limit: float = 100.00
    
    # Directories
    upload_dir: str = "/app/uploads"
    data_dir: str = "/app/data"
    logs_dir: str = "/app/logs"
    
    # Chrome settings
    chrome_bin: str = "/usr/bin/chromium"
    chromedriver_path: str = "/usr/bin/chromedriver"
    
    # Environment
    environment: str = "production"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Aliases for backward compatibility
DATABASE_URL = settings.database_url
OPENAI_API_KEY = settings.openai_api_key
ANTHROPIC_API_KEY = settings.anthropic_api_key
SMTP_SERVER = settings.smtp_server
SMTP_PORT = settings.smtp_port
SMTP_USERNAME = settings.smtp_username
SMTP_PASSWORD = settings.smtp_password
SECRET_KEY = settings.secret_key
UPLOAD_DIR = settings.upload_dir
DATA_DIR = settings.data_dir
LOGS_DIR = settings.logs_dir