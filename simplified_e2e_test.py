#!/usr/bin/env python3
"""
Simplified E2E test suite to verify the core functionality works
"""
import time
import tempfile
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

class SimplifiedE2ETest:
    def __init__(self):
        self.driver = None
        self.base_url = "http://localhost:3000"
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
    
    def test_01_homepage_loads(self):
        """Test that homepage loads correctly"""
        print("1. Testing homepage load...")
        self.driver.get(self.base_url)
        
        # Check page title
        assert "GDPR Account Deletion Assistant" in self.driver.title
        
        # Check for React app root
        root_element = self.driver.find_element(By.ID, "root")
        assert root_element is not None
        
        print("   ✅ Homepage loads successfully")
        return True
    
    def test_02_navigation_works(self):
        """Test navigation between pages"""
        print("2. Testing navigation...")
        
        nav_links = ["Dashboard", "Upload", "Accounts", "Deletion", "Audit Log", "Settings"]
        
        for link_text in nav_links:
            try:
                self.driver.get(self.base_url)
                
                # Wait for navigation to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "nav"))
                )
                
                # Find and click navigation link
                link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, link_text))
                )
                link.click()
                
                # Wait for page to load
                time.sleep(2)
                
                # Check that page loaded (has main content)
                main_content = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
                assert main_content is not None
                
                print(f"   ✅ {link_text} page loads successfully")
                
            except Exception as e:
                print(f"   ❌ {link_text} page failed: {e}")
                return False
        
        return True
    
    def test_03_accounts_page_data(self):
        """Test that accounts page shows data correctly"""
        print("3. Testing accounts page data...")
        
        self.driver.get(f"{self.base_url}/accounts")
        
        # Wait for accounts page to load
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        
        # Check page content
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        
        # Should show accounts-related content
        assert "Accounts" in body_text
        assert "STATUS" in body_text or "ACTIONS" in body_text
        
        # Check for account entries (should have some test data)
        account_indicators = ["Gmail", "Facebook", "GitHub", "LinkedIn", "testuser"]
        found_accounts = [acc for acc in account_indicators if acc in body_text]
        
        assert len(found_accounts) > 0, f"No account data found. Body text: {body_text[:500]}"
        
        print(f"   ✅ Accounts page shows {len(found_accounts)} account indicators")
        return True
    
    def test_04_no_critical_errors(self):
        """Test that there are no critical console errors"""
        print("4. Testing for critical console errors...")
        
        # Visit main pages and check for errors
        pages = ["/", "/accounts", "/upload", "/settings"]
        
        for page in pages:
            self.driver.get(f"{self.base_url}{page}")
            time.sleep(2)
            
            # Check browser console for critical errors
            logs = self.driver.get_log('browser')
            critical_errors = [
                log for log in logs 
                if log['level'] == 'SEVERE' and 
                any(term in log['message'].lower() for term in ['api', 'network', 'fetch', 'backend'])
            ]
            
            if critical_errors:
                print(f"   ❌ Critical errors found on {page}:")
                for error in critical_errors:
                    print(f"      - {error['message']}")
                return False
        
        print("   ✅ No critical console errors found")
        return True
    
    def test_05_responsive_layout(self):
        """Test basic responsive layout"""
        print("5. Testing responsive layout...")
        
        # Test different screen sizes
        sizes = [(1920, 1080), (768, 1024), (375, 667)]
        
        for width, height in sizes:
            self.driver.set_window_size(width, height)
            self.driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check that navigation exists
            nav_elements = self.driver.find_elements(By.TAG_NAME, "nav")
            assert len(nav_elements) > 0, f"Navigation not found at {width}x{height}"
            
            print(f"   ✅ Layout works at {width}x{height}")
        
        return True
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Running Simplified E2E Test Suite")
        print("=" * 50)
        
        tests = [
            self.test_01_homepage_loads,
            self.test_02_navigation_works,
            self.test_03_accounts_page_data,
            self.test_04_no_critical_errors,
            self.test_05_responsive_layout
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    print(f"   ❌ Test failed")
            except Exception as e:
                print(f"   ❌ Test failed with exception: {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! The application is working correctly.")
            return True
        else:
            print(f"❌ {total - passed} tests failed. Check the output above for details.")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    test_suite = SimplifiedE2ETest()
    
    try:
        success = test_suite.run_all_tests()
        exit(0 if success else 1)
    finally:
        test_suite.cleanup()