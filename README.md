# DataWipe 🗑️

A comprehensive web application that helps users manage and delete their accounts across various online services in compliance with GDPR regulations.

## 🚀 Features

### Core Features
- **🔐 User Authentication**: JWT-based auth with configurable sessions (1-24h)
- **🔒 Password Encryption**: AES-256 encryption for all stored passwords
- **📁 CSV Import with Auto-Detection**: Supports 10+ password managers
  - Bitwarden, LastPass, 1Password, Chrome, Firefox, KeePass, Dashlane, NordPass, RoboForm, Enpass
- **➕ Manual Account Entry**: Add individual accounts with auto-categorization
- **🏷️ Smart Categorization**: Auto-categorize accounts by type and risk level
  - 13 categories: Social Media, Finance, Shopping, Entertainment, etc.
  - Risk assessment: Critical, High, Medium, Low
- **🤖 Web Automation**: Playwright-based deletion for 15+ popular sites
- **📧 Email Integration**: GDPR-compliant deletion requests
  - SMTP auto-detection for major providers
  - IMAP monitoring for responses
  - Follow-up and complaint templates
- **📊 Audit Trail**: Complete activity logging and compliance tracking
- **📱 Responsive Design**: Works on desktop, tablet, and mobile
- **📖 API Documentation**: Complete OpenAPI/Swagger documentation

## 🏗️ Architecture

- **Frontend**: React.js with modern UI components
- **Backend**: FastAPI (Python) with async support
- **Database**: SQLite (easily configurable to PostgreSQL)
- **Containerization**: Docker & Docker Compose
- **Testing**: Selenium E2E tests + API tests

## 📋 Prerequisites

- Docker and Docker Compose
- Git
- Port 3000 and 8000 available on your system

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
git clone <repository-url>
cd account-deleter2
./start_app.sh
```

### Option 2: Manual Setup
```bash
# Clone the repository
git clone <repository-url>
cd account-deleter2

# Start the application
docker compose down
docker compose up -d --build

# Wait for services to start
sleep 10

# Initialize database
docker compose exec backend python -c "
from database import init_db
from models import Base
from sqlalchemy import create_engine
engine = create_engine('sqlite:////app/data/accounts.db')
Base.metadata.create_all(engine)
print('Database initialized')
"
```

## 🌐 Access Points

- **Frontend**: http://localhost:3000 (or http://127.0.0.1:3000)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
account-deleter2/
├── backend/                 # FastAPI backend
│   ├── api/                # API endpoints
│   │   ├── accounts.py     # Account management
│   │   ├── audit.py        # Audit logging
│   │   ├── deletion.py     # Deletion tasks
│   │   └── upload.py       # File upload
│   ├── models.py           # Database models
│   ├── database.py         # Database configuration
│   ├── main.py             # FastAPI app
│   └── requirements-minimal.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Page components
│   │   └── services/       # API services
│   ├── public/
│   └── package.json
├── tests/                  # Test suites
│   ├── selenium/           # E2E browser tests
│   └── test_e2e.py         # API E2E tests
├── docker-compose.yml      # Docker services
├── start_app.sh           # Startup script
└── README.md
```

## 🧪 Testing

### Comprehensive Test Suite
DataWipe includes a complete test suite that runs inside Docker containers.

#### Run All Tests
```bash
# Run complete test suite
./run_tests.sh

# Run specific test categories
./run_tests.sh quick       # Quick unit tests only
./run_tests.sh backend     # All backend tests
./run_tests.sh integration # Integration tests
./run_tests.sh e2e        # End-to-end tests
```

#### Test Coverage
- **Unit Tests**: Authentication, encryption, CSV parsing, categorization
- **Integration Tests**: Database, services, API endpoints
- **E2E Tests**: Full user workflows with Selenium
- **API Tests**: All REST endpoints with auth

#### Manual Testing
```bash
# Test API health
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs

# Run specific test file in Docker
docker compose exec backend python -m pytest tests/test_auth.py -v
```

## 📊 API Endpoints

### Accounts
- `GET /api/accounts` - List all accounts
- `GET /api/accounts/summary` - Get account statistics
- `GET /api/accounts/{id}` - Get specific account
- `PUT /api/accounts/{id}` - Update account
- `DELETE /api/accounts/{id}` - Delete account

### Upload
- `POST /api/upload` - Upload CSV file

### Deletion
- `POST /api/deletion/tasks` - Create deletion task
- `GET /api/deletion/tasks` - List deletion tasks
- `GET /api/deletion/tasks/{id}` - Get specific task

### Audit
- `GET /api/audit` - List audit logs
- `GET /api/audit/summary` - Get audit statistics
- `GET /api/audit/actions` - List available actions

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=sqlite:////app/data/accounts.db

# API Keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Security
SECRET_KEY=your_secret_key_here
ENVIRONMENT=development
```

### Database Configuration
The application uses SQLite by default. To use PostgreSQL:

1. Update `DATABASE_URL` in environment variables
2. Install PostgreSQL dependencies in `requirements-minimal.txt`
3. Update `docker-compose.yml` to include PostgreSQL service

## 🛠️ Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-minimal.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

## 🚨 Troubleshooting

### Common Issues

1. **"Network Error" on Accounts Page**
   - **Fixed**: API route ordering and CORS issues resolved
   - **Solution**: Use the startup script for proper initialization

2. **CORS Error "Access-Control-Allow-Origin"**
   - **Fixed**: CORS supports both localhost and 127.0.0.1
   - **Solution**: Access frontend via either URL

3. **Database Issues**
   - **Reset**: `rm -rf data/accounts.db` then restart
   - **Check**: Ensure database initialization after rebuilds

### Debug Commands
```bash
# Check service status
docker compose ps

# View logs
docker compose logs backend
docker compose logs frontend

# Test API connectivity
curl http://localhost:8000/api/accounts/summary

# Reset application
docker compose down
./start_app.sh
```

## 📈 Performance & Monitoring

- **Database**: SQLite for development, PostgreSQL recommended for production
- **Caching**: Built-in FastAPI caching for API responses
- **Logging**: Comprehensive audit trail and error logging
- **Monitoring**: Health check endpoints available

## 🔒 Security

- **CORS**: Properly configured for local development
- **Input Validation**: Pydantic models for request validation
- **SQL Injection**: Protected via SQLAlchemy ORM
- **File Upload**: Secure CSV processing with validation
- **Secrets**: Environment variable configuration

## 📝 License

This project is private and proprietary.

## 🤝 Contributing

This is a private repository. For contributions or questions, please contact the project maintainer.

## 📞 Support

For technical support or questions about DataWipe, please check the troubleshooting section or review the comprehensive test suite results.

---

**Note**: This application is designed for GDPR compliance and personal data management. Always ensure proper data handling and privacy practices when using this tool.
