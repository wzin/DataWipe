#!/usr/bin/env python3
"""
Simple test to reproduce the network error on accounts tab
"""
import requests
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import tempfile
import os

def test_accounts_page_network_error():
    """Test to reproduce the network error on accounts tab"""
    print("🔍 Testing accounts page for network errors...")
    
    # Setup Chrome in headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        # Navigate to accounts page
        print("📱 Navigating to accounts page...")
        driver.get("http://localhost:3000/accounts")
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check page source for any errors
        page_source = driver.page_source
        print(f"📄 Page source length: {len(page_source)} characters")
        
        # Check for network error messages
        error_patterns = [
            "network error",
            "Network Error", 
            "connection failed",
            "failed to fetch",
            "fetch error",
            "api error",
            "backend:8000"  # This would indicate wrong URL
        ]
        
        found_errors = []
        for pattern in error_patterns:
            if pattern.lower() in page_source.lower():
                found_errors.append(pattern)
        
        if found_errors:
            print(f"❌ NETWORK ERRORS FOUND: {found_errors}")
            
            # Save page source for debugging
            with open('/tmp/accounts_page_error.html', 'w') as f:
                f.write(page_source)
            print("💾 Page source saved to /tmp/accounts_page_error.html")
            
            # Take screenshot
            driver.save_screenshot('/tmp/accounts_page_error.png')
            print("📸 Screenshot saved to /tmp/accounts_page_error.png")
            
            return False
        else:
            print("✅ No network errors found in page source")
            
        # Check browser console for errors
        print("🔍 Checking browser console for errors...")
        logs = driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        
        if errors:
            print(f"❌ BROWSER CONSOLE ERRORS: {len(errors)} errors found")
            for error in errors:
                print(f"   - {error['message']}")
            
            # Check if these are critical errors or just minor issues
            critical_errors = [e for e in errors if 'api' in e['message'].lower() or 'network' in e['message'].lower() or 'fetch' in e['message'].lower()]
            
            if critical_errors:
                print(f"🚨 CRITICAL NETWORK ERRORS: {len(critical_errors)} found")
                for error in critical_errors:
                    print(f"   - {error['message']}")
                return False
            else:
                print("ℹ️  Only minor errors found (favicon, manifest), continuing...")
        else:
            print("✅ No browser console errors found")
            
        # Check for actual account content or loading states
        print("🔍 Checking for accounts content...")
        
        # Look for accounts, loading, or error indicators
        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.find_elements(By.XPATH, "//*[contains(text(), 'Loading') or contains(text(), 'No accounts') or contains(text(), 'Account') or contains(text(), 'error') or contains(text(), 'Error')]")
            )
            
            # Get visible text
            body_text = driver.find_element(By.TAG_NAME, "body").text
            print(f"📄 Page body text (first 500 chars): {body_text[:500]}")
            
            # Check for specific account-related content
            if "account" in body_text.lower() or "loading" in body_text.lower():
                print("✅ Accounts page appears to be functioning")
                return True
            else:
                print("⚠️ Accounts page content unclear")
                return False
                
        except TimeoutException:
            print("❌ Accounts page did not load expected content")
            return False
    
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = test_accounts_page_network_error()
    if success:
        print("\n🎉 TEST PASSED: No network errors found on accounts page")
    else:
        print("\n❌ TEST FAILED: Network errors or issues found")
        print("\nThis reproduces the issue you reported!")
    
    exit(0 if success else 1)