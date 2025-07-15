import asyncio
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import random
from urllib.parse import urlparse

from models import Account
from config import settings


class WebScraper:
    """Web scraping service for automated account deletion"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
    
    async def navigate_to_page(self, url: str) -> Optional[str]:
        """Navigate to a page and return HTML content"""
        
        try:
            driver = self._get_driver()
            driver.get(url)
            
            # Wait for page to load
            await asyncio.sleep(random.uniform(2, 4))
            
            # Get page content
            html_content = driver.page_source
            
            driver.quit()
            return html_content
            
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            if driver:
                driver.quit()
            return None
    
    async def execute_deletion(self, account: Account, analysis: Dict[str, Any], task_id: int) -> bool:
        """Execute automated account deletion"""
        
        try:
            driver = self._get_driver()
            
            # Navigate to deletion URL
            deletion_url = analysis.get('deletion_url') or f"{account.site_url}/settings"
            driver.get(deletion_url)
            
            # Wait for page load
            await asyncio.sleep(random.uniform(2, 4))
            
            # Step 1: Login if required
            login_success = await self._attempt_login(driver, account)
            if not login_success:
                driver.quit()
                return False
            
            # Step 2: Navigate to deletion page
            deletion_success = await self._navigate_to_deletion(driver, analysis)
            if not deletion_success:
                driver.quit()
                return False
            
            # Step 3: Execute deletion
            final_success = await self._execute_final_deletion(driver, analysis, account)
            
            driver.quit()
            return final_success
            
        except Exception as e:
            print(f"Error executing deletion for {account.site_name}: {e}")
            if driver:
                driver.quit()
            return False
    
    async def _attempt_login(self, driver: webdriver.Chrome, account: Account) -> bool:
        """Attempt to log into the account"""
        
        try:
            # Common login selectors
            username_selectors = [
                'input[name="username"]',
                'input[name="email"]',
                'input[type="email"]',
                'input[id="username"]',
                'input[id="email"]',
                '#username',
                '#email'
            ]
            
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[id="password"]',
                '#password'
            ]
            
            # Find username field
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not username_field:
                print("Could not find username field")
                return False
            
            # Find password field
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not password_field:
                print("Could not find password field")
                return False
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(account.username)
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Get decrypted password (implement in CSV parser)
            password = "dummy_password"  # This would be decrypted
            password_field.clear()
            password_field.send_keys(password)
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Find and click login button
            login_button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:contains("Log in")',
                'button:contains("Sign in")',
                '.login-button',
                '#login-button'
            ]
            
            for selector in login_button_selectors:
                try:
                    login_button = driver.find_element(By.CSS_SELECTOR, selector)
                    login_button.click()
                    break
                except:
                    continue
            
            # Wait for login to complete
            await asyncio.sleep(random.uniform(3, 5))
            
            # Check if login was successful
            # Look for common indicators of successful login
            success_indicators = [
                'dashboard',
                'account',
                'settings',
                'profile',
                'logout'
            ]
            
            page_content = driver.page_source.lower()
            login_success = any(indicator in page_content for indicator in success_indicators)
            
            # Also check if we're still on login page
            login_indicators = ['login', 'sign in', 'password', 'username']
            still_on_login = any(indicator in driver.current_url.lower() for indicator in login_indicators)
            
            return login_success and not still_on_login
            
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    async def _navigate_to_deletion(self, driver: webdriver.Chrome, analysis: Dict[str, Any]) -> bool:
        """Navigate to account deletion page"""
        
        try:
            # Try to find deletion page link
            deletion_links = [
                'a[href*="delete"]',
                'a[href*="close"]',
                'a[href*="deactivate"]',
                'a:contains("Delete Account")',
                'a:contains("Close Account")',
                'a:contains("Deactivate")'
            ]
            
            for selector in deletion_links:
                try:
                    link = driver.find_element(By.CSS_SELECTOR, selector)
                    link.click()
                    await asyncio.sleep(random.uniform(2, 4))
                    return True
                except:
                    continue
            
            # If no direct link found, try settings first
            settings_links = [
                'a[href*="settings"]',
                'a[href*="account"]',
                'a[href*="profile"]',
                'a:contains("Settings")',
                'a:contains("Account")',
                'a:contains("Profile")'
            ]
            
            for selector in settings_links:
                try:
                    link = driver.find_element(By.CSS_SELECTOR, selector)
                    link.click()
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    # Now look for deletion option
                    for del_selector in deletion_links:
                        try:
                            del_link = driver.find_element(By.CSS_SELECTOR, del_selector)
                            del_link.click()
                            await asyncio.sleep(random.uniform(2, 4))
                            return True
                        except:
                            continue
                    
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Navigation to deletion page failed: {e}")
            return False
    
    async def _execute_final_deletion(self, driver: webdriver.Chrome, analysis: Dict[str, Any], account: Account) -> bool:
        """Execute the final deletion steps"""
        
        try:
            # Look for deletion button
            deletion_buttons = [
                'button:contains("Delete Account")',
                'button:contains("Delete My Account")',
                'button:contains("Close Account")',
                'button:contains("Deactivate")',
                'input[value*="Delete"]',
                '.delete-button',
                '#delete-account'
            ]
            
            delete_button = None
            for selector in deletion_buttons:
                try:
                    delete_button = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not delete_button:
                print("Could not find delete button")
                return False
            
            # Click delete button
            delete_button.click()
            await asyncio.sleep(random.uniform(2, 4))
            
            # Handle confirmation dialog
            confirmation_handled = await self._handle_confirmation(driver, analysis)
            if not confirmation_handled:
                return False
            
            # Wait for deletion to complete
            await asyncio.sleep(random.uniform(3, 5))
            
            # Check for success indicators
            success_indicators = [
                'account deleted',
                'account closed',
                'successfully deleted',
                'account deactivated',
                'goodbye'
            ]
            
            page_content = driver.page_source.lower()
            deletion_success = any(indicator in page_content for indicator in success_indicators)
            
            return deletion_success
            
        except Exception as e:
            print(f"Final deletion failed: {e}")
            return False
    
    async def _handle_confirmation(self, driver: webdriver.Chrome, analysis: Dict[str, Any]) -> bool:
        """Handle confirmation dialogs"""
        
        try:
            # Wait for confirmation dialog
            await asyncio.sleep(random.uniform(1, 2))
            
            # Look for confirmation buttons
            confirm_buttons = [
                'button:contains("Yes")',
                'button:contains("Confirm")',
                'button:contains("Delete")',
                'button:contains("Continue")',
                'button:contains("OK")',
                '.confirm-button',
                '#confirm-delete'
            ]
            
            for selector in confirm_buttons:
                try:
                    confirm_button = driver.find_element(By.CSS_SELECTOR, selector)
                    confirm_button.click()
                    await asyncio.sleep(random.uniform(1, 2))
                    break
                except:
                    continue
            
            # Handle password confirmation if required
            password_fields = driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
            if password_fields:
                password_field = password_fields[0]
                password = "dummy_password"  # This would be decrypted
                password_field.send_keys(password)
                
                # Find submit button
                submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                submit_button.click()
                await asyncio.sleep(random.uniform(2, 3))
            
            return True
            
        except Exception as e:
            print(f"Confirmation handling failed: {e}")
            return False
    
    def _get_driver(self) -> webdriver.Chrome:
        """Get configured Chrome driver"""
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # Set binary location if specified
        if settings.chrome_bin:
            chrome_options.binary_location = settings.chrome_bin
        
        # Create driver
        driver = webdriver.Chrome(
            executable_path=settings.chromedriver_path,
            options=chrome_options
        )
        
        # Set timeouts
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        return driver
    
    async def test_site_accessibility(self, url: str) -> Dict[str, Any]:
        """Test if a site is accessible and analyze its structure"""
        
        try:
            driver = self._get_driver()
            start_time = time.time()
            
            driver.get(url)
            load_time = time.time() - start_time
            
            # Basic analysis
            title = driver.title
            has_login = bool(driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]'))
            has_captcha = bool(driver.find_elements(By.CSS_SELECTOR, '.captcha, .recaptcha'))
            
            # Check for common frameworks
            page_source = driver.page_source
            frameworks = []
            if 'react' in page_source.lower():
                frameworks.append('React')
            if 'angular' in page_source.lower():
                frameworks.append('Angular')
            if 'vue' in page_source.lower():
                frameworks.append('Vue')
            
            driver.quit()
            
            return {
                'accessible': True,
                'load_time': load_time,
                'title': title,
                'has_login': has_login,
                'has_captcha': has_captcha,
                'frameworks': frameworks,
                'automation_difficulty': 3 + (2 if has_captcha else 0)
            }
            
        except Exception as e:
            return {
                'accessible': False,
                'error': str(e),
                'automation_difficulty': 10
            }