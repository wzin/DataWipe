import asyncio
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json
import base64

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright.async_api import TimeoutError as PlaywrightTimeout

from models import Account, DeletionTask
from services.encryption_service import encryption_service
from services.site_configs import SITE_CONFIGS


class WebScraper:
    """Service for automated account deletion using Playwright"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.screenshots_dir = Path("/app/data/screenshots")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Browser settings
        self.headless = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
        self.slow_mo = int(os.getenv("BROWSER_SLOW_MO", "0"))  # Milliseconds between actions
        self.timeout = int(os.getenv("BROWSER_TIMEOUT", "30000"))  # Default 30 seconds
        
    async def initialize(self):
        """Initialize Playwright browser"""
        if not self.browser:
            playwright = await async_playwright().start()
            
            # Use Chromium for better compatibility
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )
            
            # Create context with common settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                ignore_https_errors=True,
                # Enable permissions
                permissions=['geolocation', 'notifications'],
                # Anti-detection measures
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            )
            
            # Add stealth scripts to avoid detection
            await self.context.add_init_script("""
                // Override navigator.webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                // Chrome specific
                window.chrome = {
                    runtime: {}
                };
                
                // Permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
    
    async def cleanup(self):
        """Clean up browser resources"""
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
    
    async def delete_account(self, account: Account, task: DeletionTask) -> Dict[str, Any]:
        """
        Attempt to delete an account using web automation
        
        Returns:
            Dict with success status, screenshots, and any error messages
        """
        await self.initialize()
        
        # Get site-specific configuration
        site_config = self._get_site_config(account.site_url)
        if not site_config:
            return {
                'success': False,
                'error': f'No deletion configuration available for {account.site_name}',
                'method': 'unknown'
            }
        
        page = await self.context.new_page()
        screenshots = []
        
        try:
            # Set timeout for this deletion attempt
            page.set_default_timeout(self.timeout)
            
            # Navigate to login page
            await page.goto(site_config.get('login_url', account.site_url))
            await page.wait_for_load_state('networkidle')
            
            # Take initial screenshot
            screenshot = await self._take_screenshot(page, account.id, 'login_page')
            screenshots.append(screenshot)
            
            # Perform login
            login_success = await self._perform_login(
                page, 
                account.username,
                encryption_service.decrypt_password(account.encrypted_password),
                site_config
            )
            
            if not login_success:
                return {
                    'success': False,
                    'error': 'Failed to login to account',
                    'screenshots': screenshots,
                    'method': 'automated'
                }
            
            # Take post-login screenshot
            screenshot = await self._take_screenshot(page, account.id, 'logged_in')
            screenshots.append(screenshot)
            
            # Navigate to deletion page
            deletion_result = await self._perform_deletion(page, site_config)
            
            # Take final screenshot
            screenshot = await self._take_screenshot(page, account.id, 'deletion_complete')
            screenshots.append(screenshot)
            
            return {
                'success': deletion_result['success'],
                'error': deletion_result.get('error'),
                'screenshots': screenshots,
                'method': 'automated',
                'confirmation': deletion_result.get('confirmation_text')
            }
            
        except PlaywrightTimeout as e:
            return {
                'success': False,
                'error': f'Operation timed out: {str(e)}',
                'screenshots': screenshots,
                'method': 'automated'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'screenshots': screenshots,
                'method': 'automated'
            }
        finally:
            await page.close()
    
    async def _perform_login(self, page: Page, username: str, password: str, config: Dict) -> bool:
        """Perform login using site-specific selectors"""
        try:
            # Wait for login form
            await page.wait_for_selector(
                config.get('username_selector', 'input[type="email"], input[type="text"]'),
                timeout=10000
            )
            
            # Fill username
            username_selector = config.get('username_selector', 'input[type="email"], input[type="text"]')
            await page.fill(username_selector, username)
            
            # Fill password
            password_selector = config.get('password_selector', 'input[type="password"]')
            await page.fill(password_selector, password)
            
            # Handle "remember me" checkbox if specified
            if config.get('uncheck_remember'):
                remember_selector = config.get('remember_selector', 'input[type="checkbox"]')
                try:
                    await page.uncheck(remember_selector, timeout=2000)
                except:
                    pass  # Ignore if not found
            
            # Click login button
            login_button = config.get('login_button_selector', 'button[type="submit"]')
            await page.click(login_button)
            
            # Wait for navigation or success indicator
            if config.get('login_success_url'):
                await page.wait_for_url(config['login_success_url'], timeout=15000)
            elif config.get('login_success_selector'):
                await page.wait_for_selector(config['login_success_selector'], timeout=15000)
            else:
                # Generic wait for navigation
                await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Check for 2FA/MFA
            if await self._check_for_2fa(page, config):
                # For now, we'll return False as we don't handle 2FA yet
                return False
            
            return True
            
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    async def _check_for_2fa(self, page: Page, config: Dict) -> bool:
        """Check if 2FA is required"""
        two_fa_indicators = config.get('2fa_indicators', [
            'input[type="tel"]',
            'input[name*="code"]',
            'input[name*="otp"]',
            'input[placeholder*="code"]',
            'text=/verification code/i',
            'text=/two.factor/i',
            'text=/2fa/i'
        ])
        
        for indicator in two_fa_indicators:
            try:
                if await page.locator(indicator).count() > 0:
                    return True
            except:
                continue
        
        return False
    
    async def _perform_deletion(self, page: Page, config: Dict) -> Dict[str, Any]:
        """Navigate to account deletion page and perform deletion"""
        try:
            # Navigate to account/settings page
            if config.get('account_settings_url'):
                await page.goto(config['account_settings_url'])
            else:
                # Try common patterns
                current_url = page.url
                base_url = '/'.join(current_url.split('/')[:3])
                for url_pattern in ['/settings', '/account', '/preferences', '/profile']:
                    try:
                        await page.goto(base_url + url_pattern)
                        await page.wait_for_load_state('networkidle', timeout=5000)
                        break
                    except:
                        continue
            
            # Look for deletion link/button
            deletion_texts = config.get('deletion_link_texts', [
                'Delete Account',
                'Close Account', 
                'Remove Account',
                'Deactivate Account',
                'Delete My Account',
                'Close My Account'
            ])
            
            deletion_link_found = False
            for text in deletion_texts:
                try:
                    # Try to find and click deletion link
                    await page.locator(f'text=/{text}/i').first.click(timeout=3000)
                    deletion_link_found = True
                    break
                except:
                    continue
            
            if not deletion_link_found:
                # Try with specific selectors if configured
                if config.get('deletion_link_selector'):
                    await page.click(config['deletion_link_selector'])
                else:
                    return {
                        'success': False,
                        'error': 'Could not find account deletion option'
                    }
            
            # Wait for deletion page to load
            await page.wait_for_load_state('networkidle')
            
            # Handle confirmation steps
            confirmation_steps = config.get('confirmation_steps', [])
            for step in confirmation_steps:
                if step['type'] == 'click':
                    await page.click(step['selector'])
                elif step['type'] == 'fill':
                    await page.fill(step['selector'], step['value'])
                elif step['type'] == 'check':
                    await page.check(step['selector'])
                elif step['type'] == 'select':
                    await page.select_option(step['selector'], step['value'])
                
                # Wait between steps
                await asyncio.sleep(1)
            
            # Final confirmation
            confirm_texts = config.get('confirm_button_texts', [
                'Delete Account',
                'Confirm Deletion',
                'Yes, Delete',
                'Delete',
                'Confirm',
                'Delete My Account'
            ])
            
            for text in confirm_texts:
                try:
                    await page.locator(f'button:has-text("{text}")').first.click(timeout=3000)
                    break
                except:
                    continue
            
            # Wait for confirmation
            await page.wait_for_load_state('networkidle')
            
            # Check for success message
            success_indicators = config.get('success_indicators', [
                'text=/account.*deleted/i',
                'text=/successfully.*removed/i',
                'text=/account.*closed/i',
                'text=/goodbye/i'
            ])
            
            for indicator in success_indicators:
                try:
                    element = await page.wait_for_selector(indicator, timeout=5000)
                    confirmation_text = await element.text_content()
                    return {
                        'success': True,
                        'confirmation_text': confirmation_text
                    }
                except:
                    continue
            
            # If no clear success indicator, assume success if we're logged out
            try:
                # Check if we're redirected to homepage or login
                if 'login' in page.url.lower() or page.url == config.get('homepage_url', ''):
                    return {
                        'success': True,
                        'confirmation_text': 'Account appears to be deleted (redirected to login/homepage)'
                    }
            except:
                pass
            
            return {
                'success': False,
                'error': 'Could not confirm account deletion'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Deletion process failed: {str(e)}'
            }
    
    async def _take_screenshot(self, page: Page, account_id: int, stage: str) -> str:
        """Take a screenshot and return the file path"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"account_{account_id}_{stage}_{timestamp}.png"
        filepath = self.screenshots_dir / filename
        
        await page.screenshot(path=str(filepath), full_page=True)
        
        return str(filepath)
    
    def _get_site_config(self, site_url: str) -> Optional[Dict]:
        """Get site-specific configuration for deletion"""
        # Extract domain from URL
        from urllib.parse import urlparse
        domain = urlparse(site_url).netloc.lower()
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Look for exact match or partial match
        for pattern, config in SITE_CONFIGS.items():
            if pattern in domain or domain in pattern:
                return config
        
        return None
    
    async def test_deletion_capability(self, site_url: str) -> Dict[str, Any]:
        """Test if we can automate deletion for a given site"""
        config = self._get_site_config(site_url)
        
        if not config:
            return {
                'supported': False,
                'reason': 'No configuration available for this site',
                'difficulty': 10
            }
        
        return {
            'supported': True,
            'difficulty': config.get('difficulty', 5),
            'method': 'automated',
            'requires_2fa': config.get('requires_2fa', False),
            'estimated_time': config.get('estimated_time', '2-5 minutes')
        }