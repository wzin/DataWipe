# GDPR Account Deletion Assistant - Design Document

## Project Overview

The GDPR Account Deletion Assistant is a containerized application that helps users exercise their data deletion rights by automating account deletion across multiple online services. The system accepts password manager exports (Bitwarden/LastPass) and uses AI to discover accounts, automate deletions, and send GDPR deletion requests.

## Requirements Summary

### Input/Output
- **Input**: Bitwarden/LastPass CSV files (JSON support planned)
- **Output**: Account deletion automation with email fallback
- **Budget**: Maximum $5 per deletion operation

### Core Features
- CSV password manager import
- LLM-powered site discovery from URLs
- Semi-automated account deletion with user confirmation
- Email-based GDPR deletion requests as fallback
- Comprehensive audit logging with credential masking
- Web interface for management and monitoring

### Technical Stack
- **Backend**: Python with FastAPI
- **Frontend**: React
- **Database**: SQLite (PostgreSQL option available)
- **LLM**: OpenAI and Anthropic APIs
- **Containerization**: Docker
- **Web Automation**: Selenium/Playwright

## Architecture Overview

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │    │   FastAPI       │    │   SQLite DB     │
│   - File Upload │────│   - REST API    │────│   - Accounts    │
│   - Dashboard   │    │   - CSV Parser  │    │   - Tasks       │
│   - Progress    │    │   - LLM Service │    │   - Audit Logs  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   External      │
                       │   - OpenAI API  │
                       │   - Anthropic   │
                       │   - Email SMTP  │
                       │   - Web Sites   │
                       └─────────────────┘
```

## Database Schema

### Tables

#### accounts
- `id` (PRIMARY KEY)
- `user_id` (for multi-user support)
- `site_name` (VARCHAR)
- `site_url` (VARCHAR)
- `username` (VARCHAR, encrypted)
- `password_hash` (VARCHAR)
- `email` (VARCHAR)
- `status` (ENUM: discovered, pending, in_progress, completed, failed)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### deletion_tasks
- `id` (PRIMARY KEY)
- `account_id` (FOREIGN KEY)
- `method` (ENUM: automated, email)
- `status` (ENUM: pending, in_progress, completed, failed)
- `attempts` (INTEGER)
- `last_error` (TEXT)
- `deletion_url` (VARCHAR)
- `privacy_email` (VARCHAR)
- `created_at` (TIMESTAMP)
- `completed_at` (TIMESTAMP)

#### audit_logs
- `id` (PRIMARY KEY)
- `account_id` (FOREIGN KEY)
- `action` (VARCHAR)
- `details` (JSON)
- `masked_credentials` (BOOLEAN)
- `created_at` (TIMESTAMP)
- `user_agent` (VARCHAR)
- `ip_address` (VARCHAR)

#### llm_interactions
- `id` (PRIMARY KEY)
- `account_id` (FOREIGN KEY)
- `provider` (ENUM: openai, anthropic)
- `task_type` (ENUM: discovery, navigation, email_generation)
- `prompt` (TEXT)
- `response` (TEXT)
- `tokens_used` (INTEGER)
- `cost` (DECIMAL)
- `created_at` (TIMESTAMP)

## API Endpoints

### File Management
- `POST /api/upload` - Upload CSV file
- `GET /api/accounts` - List discovered accounts
- `POST /api/accounts/bulk-select` - Select accounts for deletion

### Account Management
- `GET /api/accounts/{id}` - Get account details
- `PUT /api/accounts/{id}` - Update account status
- `DELETE /api/accounts/{id}` - Remove account from system

### Deletion Operations
- `POST /api/deletion/start` - Start deletion process
- `GET /api/deletion/status` - Get deletion progress
- `POST /api/deletion/confirm` - Confirm deletion action
- `POST /api/deletion/email` - Send email deletion request

### Audit & Logging
- `GET /api/audit` - Get audit logs
- `GET /api/audit/{id}/reveal` - Reveal masked credentials
- `GET /api/stats` - Get deletion statistics

## LLM Integration Strategy

### Site Discovery
```python
# Example prompt for site discovery
prompt = """
Analyze these URLs from a password manager export:
- facebook.com/login
- accounts.google.com
- amazon.com/signin

For each site, provide:
1. Service name
2. Account deletion procedure
3. Privacy policy URL
4. Data deletion contact email
5. Automation difficulty (1-10)
"""
```

### UI Navigation
```python
# Example prompt for automated deletion
prompt = """
You are automating account deletion on {site_name}.
Current page HTML: {page_html}

Steps to delete account:
1. Navigate to account settings
2. Find delete/deactivate option
3. Confirm deletion
4. Handle any retention offers

Return next action as JSON: {"action": "click", "selector": "...", "text": "..."}
"""
```

### Email Generation
```python
# Example prompt for GDPR email
prompt = """
Generate a GDPR Article 17 deletion request email for {site_name}.
Include:
- Legal basis (GDPR Article 17)
- Account identifier: {username}
- Request complete data deletion
- 30-day compliance timeline
- Professional but firm tone
"""
```

## Security & Privacy

### Credential Handling
- Passwords encrypted at rest using AES-256
- Temporary storage during processing only
- Automatic cleanup after deletion completion
- Masked display in logs with reveal option

### Rate Limiting
- Human-like delays between requests (2-5 seconds)
- Randomized user agents and headers
- Session management to avoid detection
- Respect robots.txt and rate limits

### Audit Trail
- All actions logged with timestamps
- User confirmations tracked
- LLM interactions recorded
- Error handling and retry logic

## Error Handling & Fallbacks

### Automation Failures
1. **Page Structure Changed**: Use LLM to adapt to new UI
2. **Login Issues**: Skip 2FA accounts, log for manual review
3. **Site Unavailable**: Retry with exponential backoff
4. **Captcha/Protection**: Fall back to email method

### Email Fallbacks
1. **No Deletion Page**: Generate email request
2. **Complex Process**: Provide manual instructions
3. **No Contact Info**: Research and suggest alternatives
4. **Bounce/Error**: Log and notify user

## Implementation Phases

### Phase 1: Core Infrastructure
- Docker setup with Python/React
- Basic file upload and CSV parsing
- Database models and migrations
- Simple web interface

### Phase 2: LLM Integration
- OpenAI/Anthropic API integration
- Site discovery from CSV data
- Basic email generation
- Cost tracking and limits

### Phase 3: Web Automation
- Selenium/Playwright setup
- Account deletion automation
- Progress tracking and reporting
- Error handling and retries

### Phase 4: Production Features
- Comprehensive audit logging
- Security enhancements
- Performance optimizations
- User management and auth

## Monitoring & Metrics

### Key Metrics
- Accounts processed per hour
- Success rate by site
- LLM token usage and costs
- User satisfaction scores

### Alerting
- High failure rates
- Cost threshold exceeded
- System errors or downtime
- Security incidents

## Deployment

### Docker Configuration
```dockerfile
# Multi-stage build
FROM python:3.11-slim as backend
FROM node:18-alpine as frontend
FROM nginx:alpine as production
```

### Environment Variables
- `DATABASE_URL`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `SMTP_SERVER`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SECRET_KEY`

### Volume Mounts
- `/app/data` - SQLite database
- `/app/uploads` - Temporary CSV files
- `/app/logs` - Application logs

This design provides a comprehensive foundation for implementing the GDPR Account Deletion Assistant with robust security, scalability, and user experience considerations.