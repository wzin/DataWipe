# End-to-End Test Suite

This directory contains comprehensive end-to-end tests for the GDPR Account Deletion Assistant application.

## Test Coverage

### 1. Application Accessibility Tests ✅
- Frontend load time and accessibility
- Backend health check
- API root endpoint validation

### 2. Backend API Endpoints Tests ✅
- `/api/accounts` - Account listing
- `/api/settings/email/providers` - Email provider configuration
- `/api/upload/formats` - Supported file formats

### 3. CSV Upload Functionality Tests ✅
- File upload validation
- CSV parsing and account creation
- Error handling for invalid files

### 4. Account Management Workflow Tests ✅
- Account retrieval
- Account status updates
- Account update verification

### 5. Deletion Process Workflow Tests ✅
- Deletion task creation
- Deletion task tracking
- Multi-account deletion handling

### 6. Email Configuration Tests ✅
- Email settings validation
- Invalid credential rejection
- Provider-specific configuration

### 7. Error Handling Tests ✅
- 404 error responses
- JSON validation
- File upload validation
- Malformed request handling

### 8. Security Features Tests ✅
- CORS headers verification
- Rate limiting functionality
- Input validation

## Running Tests

### Automated Test Suite
```bash
# Run all tests
python tests/test_e2e.py

# Or use the test runner
./run_e2e_tests.sh
```

### Manual Testing
```bash
# Start the application
docker compose up -d

# Run individual test functions
python -c "from tests.test_e2e import E2ETestSuite; suite = E2ETestSuite(); suite.test_csv_upload_functionality()"
```

## Test Results

The test suite generates:
- **Console output** with real-time test results
- **JSON report** with detailed test data
- **Summary statistics** including success rate

### Sample Output
```
🧪 Starting End-to-End Test Suite for GDPR Account Deletion Assistant
======================================================================

=== Test 1: Application Accessibility ===
✅ Frontend Load: PASS
✅ Backend Health: PASS
✅ API Root: PASS

📊 TEST SUMMARY REPORT
======================================================================
📋 Total Tests: 18
✅ Passed: 17
❌ Failed: 0
⚠️  Warnings: 1
🎯 Success Rate: 94.4%
```

## Test Data

The test suite uses realistic test data:
- **CSV files** with sample account data
- **Email configurations** with various providers
- **Account status** transitions
- **Error scenarios** for edge case testing

## Extending Tests

To add new tests:

1. **Add test method** to `E2ETestSuite` class
2. **Call from** `run_all_tests()` method
3. **Use logging** with `self.log_test()`
4. **Handle exceptions** gracefully

Example:
```python
def test_new_feature(self):
    """Test new feature functionality"""
    print("\n=== Test: New Feature ===")
    try:
        # Test implementation
        response = self.session.get(f"{self.base_url}/api/new-endpoint")
        if response.status_code == 200:
            self.log_test("New Feature", "PASS")
        else:
            self.log_test("New Feature", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        self.log_test("New Feature", "FAIL", str(e))
```

## Dependencies

- `requests` - HTTP client for API testing
- `json` - JSON data handling
- `tempfile` - Temporary file creation
- `time` - Test timing and timestamps

## Continuous Integration

The test suite is designed to be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run E2E Tests
  run: |
    docker compose up -d
    sleep 10
    python tests/test_e2e.py
    docker compose down
```

## Troubleshooting

### Common Issues

1. **Services not accessible**
   - Check Docker containers are running
   - Verify ports 3000 and 8000 are available
   - Check firewall settings

2. **Database errors**
   - Ensure database is initialized
   - Check volume permissions
   - Verify database schema

3. **Test failures**
   - Review detailed JSON report
   - Check application logs
   - Verify test data integrity

### Debug Mode
```bash
# Enable verbose logging
PYTHONPATH=. python -v tests/test_e2e.py

# Check container logs
docker compose logs -f backend
docker compose logs -f frontend
```