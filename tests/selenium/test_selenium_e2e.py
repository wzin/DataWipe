#!/usr/bin/env python3
"""
Selenium-based End-to-End Tests for GDPR Account Deletion Assistant

This test suite uses Selenium WebDriver to test the actual browser interactions
and catch frontend-backend integration issues that API tests might miss.
"""

import pytest
import time
import json
import tempfile
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import requests

class TestSeleniumE2E:
    """Selenium-based E2E tests for GDPR Account Deletion Assistant"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Setup Chrome WebDriver with headless configuration"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    @pytest.fixture(scope="class")
    def base_url(self):
        """Base URL for the application"""
        return "http://frontend:3000"
    
    @pytest.fixture(scope="class")
    def api_url(self):
        """API URL for direct API calls"""
        return "http://backend:8000"
    
    @pytest.fixture(scope="class")
    def wait_for_services(self, api_url):
        """Wait for backend and frontend services to be ready"""
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{api_url}/health", timeout=5)
                if response.status_code == 200:
                    time.sleep(5)  # Additional wait for frontend
                    return
            except:
                pass
            time.sleep(2)
        pytest.fail("Services not ready after 60 seconds")
    
    def test_01_frontend_loads(self, driver, base_url, wait_for_services):
        """Test that frontend loads correctly"""
        driver.get(base_url)
        
        # Check page title
        assert "GDPR Account Deletion Assistant" in driver.title
        
        # Check for React app root
        root_element = driver.find_element(By.ID, "root")
        assert root_element is not None
        
        # Wait for app to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check that no JavaScript errors occurred
        logs = driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        assert len(errors) == 0, f"JavaScript errors found: {errors}"
    
    def test_02_navigation_menu(self, driver, base_url):
        """Test navigation menu functionality"""
        driver.get(base_url)
        
        # Wait for navigation to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "nav"))
        )
        
        # Test navigation links
        nav_links = [
            ("Dashboard", "/"),
            ("Upload", "/upload"),
            ("Accounts", "/accounts"),
            ("Deletion", "/deletion"),
            ("Audit", "/audit"),
            ("Settings", "/settings")
        ]
        
        for link_text, expected_path in nav_links:
            try:
                # Find and click navigation link
                link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, link_text))
                )
                link.click()
                
                # Wait for page to load
                time.sleep(2)
                
                # Check URL changed
                current_url = driver.current_url
                assert expected_path in current_url, f"Navigation to {link_text} failed"
                
            except TimeoutException:
                pytest.fail(f"Navigation link '{link_text}' not found or not clickable")
    
    def test_03_accounts_page_loads(self, driver, base_url):
        """Test that accounts page loads without network errors"""
        driver.get(f"{base_url}/accounts")
        
        # Wait for accounts page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        
        # Check for network error messages
        try:
            error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'network error') or contains(text(), 'Network Error') or contains(text(), 'connection') or contains(text(), 'failed to fetch')]")
            assert len(error_elements) == 0, f"Network error found on accounts page: {[elem.text for elem in error_elements]}"
        except NoSuchElementException:
            pass  # No error elements found, which is good
        
        # Check for loading states or account content
        try:
            # Look for either loading indicator or account content
            WebDriverWait(driver, 10).until(
                lambda d: d.find_elements(By.XPATH, "//*[contains(text(), 'Loading') or contains(text(), 'No accounts') or contains(text(), 'Account')]")
            )
        except TimeoutException:
            # Take screenshot for debugging
            driver.save_screenshot('/tmp/accounts_page_error.png')
            page_source = driver.page_source
            pytest.fail(f"Accounts page did not load properly. Page source length: {len(page_source)}")
    
    def test_04_upload_page_functionality(self, driver, base_url):
        """Test CSV upload functionality through browser"""
        driver.get(f"{base_url}/upload")
        
        # Wait for upload page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        
        # Create test CSV file
        test_csv_content = """name,url,username,password,notes
Test Gmail,https://accounts.google.com,selenium@gmail.com,testpass123,Selenium test
Test Facebook,https://facebook.com,selenium@facebook.com,fbpass456,Selenium test
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(test_csv_content)
            temp_file = f.name
        
        try:
            # Find file input (might be hidden in dropzone)
            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            
            # Upload file
            file_input.send_keys(temp_file)
            
            # Wait for upload to process
            time.sleep(3)
            
            # Check for success message or redirect
            try:
                success_indicators = WebDriverWait(driver, 10).until(
                    lambda d: d.find_elements(By.XPATH, "//*[contains(text(), 'success') or contains(text(), 'uploaded') or contains(text(), 'processed')]")
                )
                assert len(success_indicators) > 0, "No success indicators found after upload"
            except TimeoutException:
                # Check for error messages
                error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'error') or contains(text(), 'failed')]")
                if error_elements:
                    pytest.fail(f"Upload failed with errors: {[elem.text for elem in error_elements]}")
                else:
                    pytest.fail("Upload did not show success or error message")
        
        finally:
            # Clean up temp file
            os.unlink(temp_file)
    
    def test_05_settings_page_email_config(self, driver, base_url):
        """Test email configuration page"""
        driver.get(f"{base_url}/settings")
        
        # Wait for settings page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        
        # Check for email configuration form
        try:
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email']"))
            )
            assert email_input is not None, "Email input field not found"
            
            # Check for password field
            password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
            assert password_input is not None, "Password input field not found"
            
            # Check for provider selection or information
            provider_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Gmail') or contains(text(), 'Outlook') or contains(text(), 'Yahoo')]")
            assert len(provider_elements) > 0, "Email provider information not found"
            
        except TimeoutException:
            pytest.fail("Email configuration form not found on settings page")
    
    def test_06_deletion_page_functionality(self, driver, base_url):
        """Test deletion page functionality"""
        driver.get(f"{base_url}/deletion")
        
        # Wait for deletion page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        
        # Check for deletion-related content
        try:
            deletion_content = WebDriverWait(driver, 10).until(
                lambda d: d.find_elements(By.XPATH, "//*[contains(text(), 'deletion') or contains(text(), 'Delete') or contains(text(), 'task')]")
            )
            assert len(deletion_content) > 0, "Deletion page content not found"
        except TimeoutException:
            pytest.fail("Deletion page did not load properly")
    
    def test_07_audit_page_functionality(self, driver, base_url):
        """Test audit page functionality"""
        driver.get(f"{base_url}/audit")
        
        # Wait for audit page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        
        # Check for audit-related content
        try:
            audit_content = WebDriverWait(driver, 10).until(
                lambda d: d.find_elements(By.XPATH, "//*[contains(text(), 'audit') or contains(text(), 'Audit') or contains(text(), 'log')]")
            )
            assert len(audit_content) > 0, "Audit page content not found"
        except TimeoutException:
            pytest.fail("Audit page did not load properly")
    
    def test_08_frontend_backend_integration(self, driver, base_url, api_url):
        """Test frontend-backend integration by checking API calls"""
        driver.get(f"{base_url}/accounts")
        
        # Enable network logging
        driver.execute_cdp_cmd('Network.enable', {})
        
        # Wait for page to load and make API calls
        time.sleep(5)
        
        # Check network logs for API calls
        logs = driver.get_log('performance')
        network_logs = [json.loads(log['message']) for log in logs if log['level'] == 'INFO']
        
        # Look for API requests
        api_requests = []
        for log in network_logs:
            if 'message' in log and 'params' in log['message']:
                if 'request' in log['message']['params']:
                    url = log['message']['params']['request']['url']
                    if '/api/' in url:
                        api_requests.append(url)
        
        # Check that API calls were made
        assert len(api_requests) > 0, f"No API requests found. Network logs: {len(network_logs)}"
        
        # Check for failed requests
        failed_requests = []
        for log in network_logs:
            if 'message' in log and 'params' in log['message']:
                if 'response' in log['message']['params']:
                    response = log['message']['params']['response']
                    if response.get('status', 200) >= 400:
                        failed_requests.append(response)
        
        assert len(failed_requests) == 0, f"Failed API requests found: {failed_requests}"
    
    def test_09_responsive_design(self, driver, base_url):
        """Test responsive design on different screen sizes"""
        test_sizes = [
            (1920, 1080),  # Desktop
            (1024, 768),   # Tablet
            (375, 667),    # Mobile
        ]
        
        for width, height in test_sizes:
            driver.set_window_size(width, height)
            driver.get(base_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check that navigation is present (might be collapsed on mobile)
            nav_elements = driver.find_elements(By.TAG_NAME, "nav")
            assert len(nav_elements) > 0, f"Navigation not found at {width}x{height}"
            
            # Check for responsive behavior
            body = driver.find_element(By.TAG_NAME, "body")
            assert body.size['width'] <= width, f"Content overflow at {width}x{height}"
    
    def test_10_accessibility_basics(self, driver, base_url):
        """Test basic accessibility features"""
        driver.get(base_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check for basic accessibility elements
        # Page should have a title
        assert driver.title, "Page title is empty"
        
        # Check for proper heading hierarchy
        h1_elements = driver.find_elements(By.TAG_NAME, "h1")
        assert len(h1_elements) > 0, "No h1 elements found"
        
        # Check for alt text on images
        images = driver.find_elements(By.TAG_NAME, "img")
        for img in images:
            alt_text = img.get_attribute("alt")
            assert alt_text is not None, f"Image missing alt text: {img.get_attribute('src')}"
        
        # Check for form labels
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for input_elem in inputs:
            input_type = input_elem.get_attribute("type")
            if input_type not in ["hidden", "submit", "button"]:
                # Check for label or aria-label
                label_id = input_elem.get_attribute("id")
                if label_id:
                    labels = driver.find_elements(By.CSS_SELECTOR, f"label[for='{label_id}']")
                    aria_label = input_elem.get_attribute("aria-label")
                    assert len(labels) > 0 or aria_label, f"Input field missing label: {input_elem.get_attribute('name')}"
    
    def test_11_error_handling_ui(self, driver, base_url):
        """Test error handling in the UI"""
        driver.get(f"{base_url}/upload")
        
        # Wait for upload page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        
        # Try to upload an invalid file
        invalid_content = "This is not a valid CSV file"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(invalid_content)
            temp_file = f.name
        
        try:
            # Find file input
            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            
            # Upload invalid file
            file_input.send_keys(temp_file)
            
            # Wait for error handling
            time.sleep(3)
            
            # Check for error message
            error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'error') or contains(text(), 'invalid') or contains(text(), 'failed')]")
            assert len(error_elements) > 0, "No error message shown for invalid file"
            
        finally:
            os.unlink(temp_file)
    
    def test_12_performance_basic(self, driver, base_url):
        """Test basic performance metrics"""
        start_time = time.time()
        driver.get(base_url)
        
        # Wait for page to be fully loaded
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        load_time = time.time() - start_time
        
        # Page should load within reasonable time
        assert load_time < 10, f"Page took too long to load: {load_time:.2f} seconds"
        
        # Check for performance timing
        performance_timing = driver.execute_script("return window.performance.timing")
        if performance_timing:
            navigation_start = performance_timing['navigationStart']
            load_complete = performance_timing['loadEventEnd']
            total_time = load_complete - navigation_start
            
            assert total_time < 5000, f"Page load time too high: {total_time}ms"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--html=selenium_report.html", "--self-contained-html"])