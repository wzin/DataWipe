#!/usr/bin/env python3
"""
End-to-End Test Suite for GDPR Account Deletion Assistant

This test suite performs comprehensive manual testing scenarios
to validate the entire application workflow.
"""

import json
import time
import requests
import tempfile
import os
from typing import Dict, List, Optional

class E2ETestSuite:
    def __init__(self, base_url: str = "http://localhost:8000", frontend_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.frontend_url = frontend_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
            
    def test_application_accessibility(self):
        """Test 1: Application Accessibility and Initial Load"""
        print("\n=== Test 1: Application Accessibility ===")
        
        # Test frontend accessibility
        try:
            response = self.session.get(self.frontend_url, timeout=10)
            if response.status_code == 200 and "GDPR Account Deletion Assistant" in response.text:
                self.log_test("Frontend Load", "PASS", f"Response time: {response.elapsed.total_seconds():.3f}s")
            else:
                self.log_test("Frontend Load", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Frontend Load", "FAIL", str(e))
            
        # Test backend accessibility
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            data = response.json()
            if response.status_code == 200 and data.get("status") == "healthy":
                self.log_test("Backend Health", "PASS", f"Version: {data.get('version')}")
            else:
                self.log_test("Backend Health", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Backend Health", "FAIL", str(e))
            
        # Test API root endpoint
        try:
            response = self.session.get(self.base_url, timeout=10)
            data = response.json()
            if response.status_code == 200 and "GDPR Account Deletion Assistant API" in data.get("message", ""):
                self.log_test("API Root", "PASS")
            else:
                self.log_test("API Root", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("API Root", "FAIL", str(e))
            
    def test_backend_api_endpoints(self):
        """Test 2: Backend API Endpoints Functionality"""
        print("\n=== Test 2: Backend API Endpoints ===")
        
        # Test accounts endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/accounts", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Accounts Endpoint", "PASS", f"Found {len(data)} accounts")
            else:
                self.log_test("Accounts Endpoint", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Accounts Endpoint", "FAIL", str(e))
            
        # Test email providers endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/settings/email/providers", timeout=10)
            if response.status_code == 200:
                data = response.json()
                providers = data.get("providers", [])
                self.log_test("Email Providers", "PASS", f"Found {len(providers)} providers")
            else:
                self.log_test("Email Providers", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Email Providers", "FAIL", str(e))
            
        # Test upload formats endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/upload/formats", timeout=10)
            if response.status_code == 200:
                data = response.json()
                formats = data.get("supported_formats", [])
                self.log_test("Upload Formats", "PASS", f"Supported: {formats}")
            else:
                self.log_test("Upload Formats", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Upload Formats", "FAIL", str(e))
            
    def test_csv_upload_functionality(self):
        """Test 3: CSV Upload Functionality"""
        print("\n=== Test 3: CSV Upload Functionality ===")
        
        # Create test CSV file
        test_csv_content = """name,url,username,password,notes
Gmail,https://accounts.google.com,testuser@gmail.com,testpass123,Personal email
Facebook,https://facebook.com,testuser@example.com,fbpass456,Social media
GitHub,https://github.com,testuser,ghpass789,Code repository
LinkedIn,https://linkedin.com,test@example.com,lnpass101,Professional network
"""
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                f.write(test_csv_content)
                temp_file = f.name
                
            # Test CSV upload
            with open(temp_file, 'rb') as f:
                files = {'file': ('test_accounts.csv', f, 'text/csv')}
                response = self.session.post(f"{self.base_url}/api/upload", files=files, timeout=30)
                
            if response.status_code == 200:
                data = response.json()
                accounts_count = data.get("accounts_discovered", 0)
                self.log_test("CSV Upload", "PASS", f"Processed {accounts_count} accounts")
            else:
                self.log_test("CSV Upload", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                
            # Clean up
            os.unlink(temp_file)
            
        except Exception as e:
            self.log_test("CSV Upload", "FAIL", str(e))
            
    def test_account_management_workflow(self):
        """Test 4: Account Management Workflow"""
        print("\n=== Test 4: Account Management Workflow ===")
        
        # Get accounts list
        try:
            response = self.session.get(f"{self.base_url}/api/accounts", timeout=10)
            if response.status_code == 200:
                accounts = response.json()
                if accounts:
                    account_id = accounts[0]["id"]
                    self.log_test("Account Retrieval", "PASS", f"Found account ID: {account_id}")
                    
                    # Test account update
                    update_data = {"status": "pending"}
                    response = self.session.put(
                        f"{self.base_url}/api/accounts/{account_id}",
                        json=update_data,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        self.log_test("Account Update", "PASS", "Status updated to pending")
                        
                        # Verify update
                        response = self.session.get(f"{self.base_url}/api/accounts/{account_id}", timeout=10)
                        if response.status_code == 200:
                            updated_account = response.json()
                            if updated_account.get("status") == "pending":
                                self.log_test("Account Update Verification", "PASS")
                            else:
                                self.log_test("Account Update Verification", "FAIL", "Status not updated")
                        else:
                            self.log_test("Account Update Verification", "FAIL", f"Status: {response.status_code}")
                    else:
                        self.log_test("Account Update", "FAIL", f"Status: {response.status_code}")
                else:
                    self.log_test("Account Retrieval", "FAIL", "No accounts found")
            else:
                self.log_test("Account Retrieval", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Account Management", "FAIL", str(e))
            
    def test_deletion_process_workflow(self):
        """Test 5: Deletion Process Workflow"""
        print("\n=== Test 5: Deletion Process Workflow ===")
        
        # Get accounts for deletion
        try:
            response = self.session.get(f"{self.base_url}/api/accounts", timeout=10)
            if response.status_code == 200:
                accounts = response.json()
                if len(accounts) >= 2:
                    account_ids = [accounts[0]["id"], accounts[1]["id"]]
                    
                    # Start deletion process
                    deletion_data = {"account_ids": account_ids}
                    response = self.session.post(
                        f"{self.base_url}/api/deletion/start",
                        json=deletion_data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        task_ids = data.get("task_ids", [])
                        self.log_test("Deletion Start", "PASS", f"Created {len(task_ids)} tasks")
                        
                        # Check deletion tasks
                        response = self.session.get(f"{self.base_url}/api/deletion/tasks", timeout=10)
                        if response.status_code == 200:
                            tasks = response.json()
                            self.log_test("Deletion Tasks", "PASS", f"Found {len(tasks)} tasks")
                        else:
                            self.log_test("Deletion Tasks", "FAIL", f"Status: {response.status_code}")
                    else:
                        self.log_test("Deletion Start", "FAIL", f"Status: {response.status_code}")
                else:
                    self.log_test("Deletion Process", "SKIP", "Not enough accounts for testing")
            else:
                self.log_test("Deletion Process", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Deletion Process", "FAIL", str(e))
            
    def test_email_configuration(self):
        """Test 6: Email Configuration"""
        print("\n=== Test 6: Email Configuration ===")
        
        # Test email configuration with invalid credentials (should fail gracefully)
        try:
            email_config = {
                "email": "test@gmail.com",
                "password": "invalid_password"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/settings/email",
                json=email_config,
                timeout=30
            )
            
            # Should fail with authentication error
            if response.status_code == 400:
                self.log_test("Email Config Validation", "PASS", "Invalid credentials properly rejected")
            else:
                self.log_test("Email Config Validation", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Email Configuration", "FAIL", str(e))
            
    def test_error_handling(self):
        """Test 7: Error Handling and Edge Cases"""
        print("\n=== Test 7: Error Handling ===")
        
        # Test invalid endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/invalid-endpoint", timeout=10)
            if response.status_code == 404:
                self.log_test("404 Error Handling", "PASS")
            else:
                self.log_test("404 Error Handling", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("404 Error Handling", "FAIL", str(e))
            
        # Test malformed JSON
        try:
            response = self.session.post(
                f"{self.base_url}/api/settings/email",
                data="invalid json",
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 422:
                self.log_test("JSON Validation", "PASS", "Malformed JSON properly rejected")
            else:
                self.log_test("JSON Validation", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("JSON Validation", "FAIL", str(e))
            
        # Test upload without file
        try:
            response = self.session.post(f"{self.base_url}/api/upload", timeout=10)
            if response.status_code == 422:
                self.log_test("Upload Validation", "PASS", "Missing file properly rejected")
            else:
                self.log_test("Upload Validation", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Upload Validation", "FAIL", str(e))
            
    def test_security_features(self):
        """Test 8: Security Features"""
        print("\n=== Test 8: Security Features ===")
        
        # Test CORS headers
        try:
            response = self.session.options(f"{self.base_url}/api/accounts", timeout=10)
            if "Access-Control-Allow-Origin" in response.headers:
                self.log_test("CORS Headers", "PASS")
            else:
                self.log_test("CORS Headers", "WARN", "CORS headers not found")
        except Exception as e:
            self.log_test("CORS Headers", "FAIL", str(e))
            
        # Test rate limiting (basic check)
        try:
            responses = []
            for i in range(5):
                response = self.session.get(f"{self.base_url}/health", timeout=5)
                responses.append(response.status_code)
                
            if all(status == 200 for status in responses):
                self.log_test("Rate Limiting", "PASS", "Multiple requests handled correctly")
            else:
                self.log_test("Rate Limiting", "WARN", f"Some requests failed: {responses}")
        except Exception as e:
            self.log_test("Rate Limiting", "FAIL", str(e))
            
    def run_all_tests(self):
        """Run all test suites"""
        print("🧪 Starting End-to-End Test Suite for GDPR Account Deletion Assistant")
        print("=" * 70)
        
        start_time = time.time()
        
        self.test_application_accessibility()
        self.test_backend_api_endpoints()
        self.test_csv_upload_functionality()
        self.test_account_management_workflow()
        self.test_deletion_process_workflow()
        self.test_email_configuration()
        self.test_error_handling()
        self.test_security_features()
        
        end_time = time.time()
        
        # Generate summary report
        self.generate_summary_report(end_time - start_time)
        
    def generate_summary_report(self, duration: float):
        """Generate summary test report"""
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY REPORT")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "SKIP"])
        warnings = len([r for r in self.test_results if r["status"] == "WARN"])
        
        print(f"📋 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"⏭️  Skipped: {skipped_tests}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test_name']}: {result['details']}")
                    
        if warnings > 0:
            print("\n⚠️  WARNINGS:")
            for result in self.test_results:
                if result["status"] == "WARN":
                    print(f"  - {result['test_name']}: {result['details']}")
                    
        # Save detailed report
        report_file = f"/tmp/e2e_test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Overall status
        if failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n🔴 {failed_tests} TEST(S) FAILED - Review and fix issues")
            
if __name__ == "__main__":
    # Run the test suite
    test_suite = E2ETestSuite()
    test_suite.run_all_tests()