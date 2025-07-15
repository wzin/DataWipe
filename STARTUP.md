# GDPR Account Deletion Assistant - Startup Guide

## Quick Start

### Method 1: Use the startup script (Recommended)
```bash
./start_app.sh
```

### Method 2: Manual startup
```bash
# 1. Stop and clean up
docker compose down

# 2. Build and start services
docker compose up -d --build

# 3. Wait for services to start
sleep 10

# 4. Initialize database
docker compose exec backend python -c "
from database import init_db
from models import Base
from sqlalchemy import create_engine
engine = create_engine('sqlite:////app/data/accounts.db')
Base.metadata.create_all(engine)
print('Database initialized')
"

# 5. (Optional) Seed test data
docker compose exec backend python -c "
import requests, tempfile, os
csv_content = '''name,url,username,password,notes
Gmail,https://accounts.google.com,test@gmail.com,pass123,Test account
GitHub,https://github.com,testuser,pass456,Test account'''
with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
    f.write(csv_content)
    temp_file = f.name
try:
    with open(temp_file, 'rb') as f:
        files = {'file': ('test.csv', f, 'text/csv')}
        response = requests.post('http://localhost:8000/api/upload', files=files)
        print('Test data seeded')
finally:
    os.unlink(temp_file)
"
```

## Access URLs

- **Frontend**: http://localhost:3000 (or http://127.0.0.1:3000)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Common Issues

### "Network Error" on Accounts Page
- **Fixed**: This was caused by API route ordering issues and CORS configuration
- **Solution**: The startup script ensures proper database initialization and CORS supports both localhost and 127.0.0.1

### Delete/Accounts Not Working After Restart
- **Cause**: Database tables not initialized after rebuild
- **Solution**: Always run database initialization after rebuilding

### CORS Error "Access-Control-Allow-Origin header is present"
- **Cause**: Browser accessing frontend via 127.0.0.1 instead of localhost
- **Fixed**: CORS now supports both `http://localhost:3000` and `http://127.0.0.1:3000`
- **Solution**: Use either URL, both work now

### Database Issues
- **Reset database**: `rm -rf data/accounts.db` then restart
- **Check tables**: `docker compose exec backend python -c "from models import Base; from sqlalchemy import create_engine; engine = create_engine('sqlite:////app/data/accounts.db'); print([table.name for table in Base.metadata.tables.values()])"`

## Testing

### Run E2E Tests
```bash
./run_selenium_tests.sh
```

### Test Specific Functionality
```bash
# Test accounts page
python test_network_error.py

# Test API endpoints
curl http://localhost:8000/api/accounts/summary
curl http://localhost:8000/api/accounts
```

## Stop Application
```bash
docker compose down
```

## Troubleshooting

1. **Services not starting**: Check logs with `docker compose logs backend` or `docker compose logs frontend`
2. **Database errors**: Ensure database is initialized after each rebuild
3. **Port conflicts**: Make sure ports 3000 and 8000 are available
4. **Build issues**: Clean build with `docker compose down && docker compose up -d --build`