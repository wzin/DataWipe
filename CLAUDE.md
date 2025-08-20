# DataWipe Project Guide for Claude Code Agent

## Project Overview
DataWipe is a GDPR-compliant account deletion assistant that helps users bulk delete unwanted online accounts. Users upload passwords from password managers, select accounts to delete, and the app automates the deletion process via web scraping or email requests.

## Quick Start Commands
```bash
# Start the application
./start_app.sh

# Run tests
./run_selenium_tests.sh

# Access points
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Project Structure
```
account-deleter2/
├── backend/                 # FastAPI backend (Python)
│   ├── api/                # API endpoints
│   ├── services/           # Business logic services
│   ├── models.py          # SQLAlchemy models
│   ├── database.py        # Database configuration
│   └── main.py            # FastAPI app entry
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/        # Page components
│   │   └── services/     # API client services
├── tests/                # Test suites
├── USER_STORIES.md       # Complete user requirements
└── IMPLEMENTATION_GAPS.md # What needs to be built
```

## Current Implementation Status

### ✅ Working Features
- **Authentication system** - JWT-based with session management
- **Password encryption** - AES-256 encryption for stored passwords
- **CSV upload with auto-detection** - Supports 10+ password managers
- **Email integration** - SMTP sending and IMAP monitoring
- **Web scraping** - Playwright automation for 15+ sites
- Account listing and filtering
- Bulk selection of accounts
- Audit logging with user tracking
- Docker containerization with volume mounts

## Development Guidelines

### Before Making Changes
1. **Always read existing code first** - Use Read tool on related files
2. **Check USER_STORIES.md** - Ensure alignment with requirements
3. **Update IMPLEMENTATION_GAPS.md** - Mark completed features
4. **Write tests** - Every new feature needs tests

### Code Conventions
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Pydantic
- **Frontend**: React 18, Tailwind CSS, Lucide icons
- **Testing**: Pytest (backend), Selenium (E2E)
- **Database**: SQLite (dev), PostgreSQL (prod-ready)

### Security Requirements
- All passwords must be encrypted with AES-256
- Use environment variables for secrets
- Implement proper session management
- Add CSRF protection
- Validate all inputs

### Testing Strategy
```bash
# Backend unit tests
cd backend && python -m pytest tests/ -v

# Frontend tests
cd frontend && npm test

# E2E tests
./run_selenium_tests.sh
```

### Common Tasks

#### Adding a New API Endpoint
1. Create endpoint in `backend/api/[module].py`
2. Add Pydantic models for request/response
3. Implement service logic in `backend/services/`
4. Add tests in `backend/tests/`
5. Update frontend API service
6. Update API documentation

#### Adding a Database Model
1. Define model in `backend/models.py`
2. Create migration (if using Alembic)
3. Update related API endpoints
4. Add model tests

#### Implementing a Service
1. Create service class in `backend/services/`
2. Implement business logic methods
3. Add error handling
4. Write comprehensive tests
5. Integrate with API endpoints

## Environment Variables
```bash
# Required for production
DATABASE_URL=sqlite:////app/data/accounts.db
SECRET_KEY=<generate-secure-key>
ENCRYPTION_KEY=<generate-32-byte-key>

# Email configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=user@gmail.com
SMTP_PASSWORD=<app-password>
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993

# Optional integrations
OPENAI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
HIBP_API_KEY=<key>
```

## Current Implementation Priorities

### Phase 1: Security & Core ✅ COMPLETED
- [x] Authentication system with JWT
- [x] Password encryption service (AES-256)
- [x] Playwright web scraping (15+ sites)
- [x] SMTP/IMAP email service
- [x] CSV format detection (10+ formats)

### Phase 2: Essential Features
- [ ] Manual account entry
- [ ] Account categorization
- [ ] Email monitoring
- [ ] Review/confirm workflow
- [ ] Compliance reports

### Phase 3: Enhancements
- [ ] Risk assessment
- [ ] Breach detection (HIBP)
- [ ] Multiple email accounts
- [ ] Dry run mode
- [ ] Analytics dashboard

## Debugging Tips
```bash
# Check Docker logs
docker compose logs backend -f
docker compose logs frontend -f

# Database inspection
docker compose exec backend python
>>> from database import engine
>>> from models import *
>>> # Query data

# Reset database
rm -rf data/accounts.db
./start_app.sh
```

## Important Files to Review
- `USER_STORIES.md` - All feature requirements
- `IMPLEMENTATION_GAPS.md` - What's missing
- `backend/models.py` - Data structure
- `backend/api/` - Current endpoints
- `frontend/src/pages/` - UI components

## Questions to Ask User
When implementing features, ask about:
1. UI/UX preferences
2. Error handling strategies
3. Performance requirements
4. Security trade-offs
5. Third-party service preferences

## Testing Checklist
- [ ] Unit tests for new functions
- [ ] Integration tests for API endpoints
- [ ] E2E tests for user workflows
- [ ] Security tests for auth/encryption
- [ ] Performance tests for batch operations

## Common Issues & Solutions
1. **Network Error on Accounts Page**: Check CORS and API routes
2. **Docker not starting**: Ensure ports 3000/8000 are free
3. **Database errors**: Reset with `rm -rf data/accounts.db`
4. **Import errors**: Check Python path and dependencies

## Notes for Future Sessions
- User wants comprehensive testing for every feature
- Prioritize security (encryption, auth) before features
- Update documentation after each implementation
- Ask questions when design decisions needed
- Focus on P0 features first, then P1, P2, P3

## Recent Changes Log
- Created USER_STORIES.md with 40+ user stories
- Created IMPLEMENTATION_GAPS.md analyzing missing features
- ✅ Completed Phase 1: All P0 features implemented
  - JWT authentication with configurable sessions
  - AES-256 password encryption
  - Playwright web automation for 15+ sites
  - SMTP/IMAP email integration
  - CSV auto-detection for 10+ password managers
- Next: Phase 2 (P1 features) - Manual entry, categorization, etc.
