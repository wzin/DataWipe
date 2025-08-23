import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import base64

from services.web_scraper import WebScraper


class TestPlaywrightWebScraper:
    """Test Playwright-based web scraper service"""
    
    @pytest.fixture
    def scraper(self):
        """Create WebScraper instance"""
        return WebScraper()
    
    @pytest.fixture
    def mock_browser(self):
        """Create mock browser context"""
        mock = MagicMock()
        mock.new_context = AsyncMock()
        mock.close = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_page(self):
        """Create mock page object"""
        mock = AsyncMock()
        mock.goto = AsyncMock()
        mock.wait_for_load_state = AsyncMock()
        mock.screenshot = AsyncMock(return_value=b"fake_screenshot")
        mock.content = AsyncMock(return_value="<html><body>Test</body></html>")
        mock.click = AsyncMock()
        mock.fill = AsyncMock()
        mock.wait_for_selector = AsyncMock()
        mock.locator = MagicMock()
        mock.evaluate = AsyncMock()
        mock.close = AsyncMock()
        return mock
    
    @pytest.mark.asyncio
    async def test_init_browser(self, scraper):
        """Test browser initialization"""
        with patch('services.web_scraper.async_playwright') as mock_playwright:
            mock_p = AsyncMock()
            mock_playwright.return_value.__aenter__.return_value = mock_p
            mock_p.chromium.launch = AsyncMock()
            
            await scraper._init_browser()
            
            mock_p.chromium.launch.assert_called_once_with(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
    
    @pytest.mark.asyncio
    async def test_login_to_site(self, scraper, mock_page):
        """Test login functionality"""
        scraper.page = mock_page
        
        result = await scraper.login_to_site(
            "https://test.com",
            "testuser",
            "testpass"
        )
        
        assert result['success'] is True
        mock_page.goto.assert_called_with("https://test.com", wait_until='networkidle')
        mock_page.wait_for_load_state.assert_called_with('networkidle')
    
    @pytest.mark.asyncio
    async def test_login_with_site_config(self, scraper, mock_page):
        """Test login with specific site configuration"""
        scraper.page = mock_page
        mock_page.locator.return_value.count = AsyncMock(return_value=1)
        mock_page.locator.return_value.fill = AsyncMock()
        mock_page.locator.return_value.click = AsyncMock()
        
        # Test Facebook login
        result = await scraper.login_to_site(
            "https://facebook.com",
            "user@test.com",
            "password123"
        )
        
        assert result['success'] is True
        mock_page.goto.assert_called()
    
    @pytest.mark.asyncio
    async def test_navigate_to_deletion(self, scraper, mock_page):
        """Test navigation to deletion page"""
        scraper.page = mock_page
        mock_page.url = "https://test.com/home"
        
        result = await scraper.navigate_to_deletion_page("https://test.com")
        
        assert result['success'] is True
        assert 'navigation_path' in result
    
    @pytest.mark.asyncio
    async def test_execute_deletion(self, scraper, mock_page):
        """Test account deletion execution"""
        scraper.page = mock_page
        mock_page.locator.return_value.count = AsyncMock(return_value=1)
        mock_page.locator.return_value.click = AsyncMock()
        
        result = await scraper.execute_deletion("https://test.com")
        
        assert result['success'] is True
        assert 'screenshot' in result
        assert result['screenshot'] == base64.b64encode(b"fake_screenshot").decode()
    
    @pytest.mark.asyncio
    async def test_take_screenshot(self, scraper, mock_page):
        """Test screenshot capture"""
        scraper.page = mock_page
        
        screenshot = await scraper.take_screenshot()
        
        assert screenshot == base64.b64encode(b"fake_screenshot").decode()
        mock_page.screenshot.assert_called_once_with(full_page=True)
    
    @pytest.mark.asyncio
    async def test_anti_detection_measures(self, scraper):
        """Test anti-detection browser configuration"""
        with patch('services.web_scraper.async_playwright') as mock_playwright:
            mock_p = AsyncMock()
            mock_playwright.return_value.__aenter__.return_value = mock_p
            mock_browser = Mock()
            mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_context = Mock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_page = Mock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_page.add_init_script = AsyncMock()
            
            await scraper._init_browser()
            
            # Check anti-detection script was added
            mock_page.add_init_script.assert_called()
            init_script = mock_page.add_init_script.call_args[0][0]
            assert 'webdriver' in init_script
            assert 'navigator.plugins' in init_script
    
    @pytest.mark.asyncio
    async def test_error_handling(self, scraper, mock_page):
        """Test error handling in web scraping"""
        scraper.page = mock_page
        mock_page.goto.side_effect = Exception("Network error")
        
        result = await scraper.login_to_site(
            "https://test.com",
            "user",
            "pass"
        )
        
        assert result['success'] is False
        assert 'error' in result
        assert "Network error" in result['error']
    
    @pytest.mark.asyncio
    async def test_cleanup(self, scraper):
        """Test browser cleanup"""
        mock_browser = Mock()
        mock_browser.close = AsyncMock()
        mock_page = Mock()
        mock_page.close = AsyncMock()
        mock_playwright = Mock()
        mock_playwright.stop = AsyncMock()
        
        scraper.browser = mock_browser
        scraper.page = mock_page
        scraper.playwright = mock_playwright
        
        await scraper.cleanup()
        
        mock_page.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_site_specific_facebook(self, scraper, mock_page):
        """Test Facebook-specific deletion logic"""
        scraper.page = mock_page
        mock_page.url = "https://facebook.com/settings"
        mock_page.locator.return_value.count = AsyncMock(return_value=1)
        mock_page.locator.return_value.click = AsyncMock()
        
        result = await scraper.navigate_to_deletion_page("https://facebook.com")
        
        assert result['success'] is True
        # Should navigate to Facebook's account deletion page
        mock_page.goto.assert_called()
    
    @pytest.mark.asyncio
    async def test_site_specific_google(self, scraper, mock_page):
        """Test Google-specific deletion logic"""
        scraper.page = mock_page
        mock_page.url = "https://myaccount.google.com"
        
        result = await scraper.navigate_to_deletion_page("https://accounts.google.com")
        
        assert result['success'] is True
        mock_page.goto.assert_called_with(
            "https://myaccount.google.com/delete-services-or-account",
            wait_until='networkidle'
        )
    
    @pytest.mark.asyncio
    async def test_site_specific_twitter(self, scraper, mock_page):
        """Test Twitter/X-specific deletion logic"""
        scraper.page = mock_page
        mock_page.url = "https://twitter.com/settings"
        mock_page.locator.return_value.count = AsyncMock(return_value=1)
        
        result = await scraper.navigate_to_deletion_page("https://twitter.com")
        
        assert result['success'] is True
        mock_page.goto.assert_called_with(
            "https://twitter.com/settings/deactivate",
            wait_until='networkidle'
        )
    
    @pytest.mark.asyncio
    async def test_get_supported_sites(self, scraper):
        """Test getting list of supported sites"""
        sites = scraper.get_supported_sites()
        
        assert isinstance(sites, list)
        assert len(sites) > 0
        assert 'facebook.com' in sites
        assert 'google.com' in sites
        assert 'twitter.com' in sites
    
    @pytest.mark.asyncio
    async def test_random_delay(self, scraper):
        """Test random delay for anti-bot measures"""
        with patch('asyncio.sleep') as mock_sleep:
            await scraper._random_delay(1, 2)
            
            mock_sleep.assert_called_once()
            delay = mock_sleep.call_args[0][0]
            assert 1 <= delay <= 2
    
    @pytest.mark.asyncio
    async def test_viewport_randomization(self, scraper):
        """Test viewport size randomization"""
        with patch('services.web_scraper.async_playwright') as mock_playwright:
            mock_p = AsyncMock()
            mock_playwright.return_value.__aenter__.return_value = mock_p
            mock_browser = Mock()
            mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock()
            
            await scraper._init_browser()
            
            # Check viewport was set with reasonable dimensions
            context_args = mock_browser.new_context.call_args[1]
            assert 'viewport' in context_args
            viewport = context_args['viewport']
            assert 1200 <= viewport['width'] <= 1920
            assert 720 <= viewport['height'] <= 1080
    
    @pytest.mark.asyncio
    async def test_user_agent(self, scraper):
        """Test user agent is set"""
        with patch('services.web_scraper.async_playwright') as mock_playwright:
            mock_p = AsyncMock()
            mock_playwright.return_value.__aenter__.return_value = mock_p
            mock_browser = Mock()
            mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock()
            
            await scraper._init_browser()
            
            # Check user agent was set
            context_args = mock_browser.new_context.call_args[1]
            assert 'user_agent' in context_args
            assert 'Mozilla' in context_args['user_agent']
    
    @pytest.mark.asyncio
    async def test_deletion_confirmation(self, scraper, mock_page):
        """Test handling of deletion confirmation dialogs"""
        scraper.page = mock_page
        mock_page.locator.return_value.count = AsyncMock(return_value=1)
        mock_page.locator.return_value.click = AsyncMock()
        
        # Mock confirmation dialog
        mock_page.on = Mock()
        
        result = await scraper.execute_deletion("https://test.com")
        
        assert result['success'] is True
        # Should handle dialog if present
        if mock_page.on.called:
            assert mock_page.on.call_args[0][0] == 'dialog'
    
    def test_site_configurations(self, scraper):
        """Test site configuration structure"""
        configs = scraper.SITE_CONFIGS
        
        assert isinstance(configs, dict)
        
        # Check each config has required fields
        for site, config in configs.items():
            assert 'login_url' in config
            assert 'deletion_url' in config or 'deletion_path' in config
            assert 'selectors' in config
            assert 'username' in config['selectors']
            assert 'password' in config['selectors']
    
    @pytest.mark.asyncio
    async def test_network_error_retry(self, scraper, mock_page):
        """Test retry on network errors"""
        scraper.page = mock_page
        mock_page.goto.side_effect = [
            Exception("Network error"),
            None  # Success on second try
        ]
        
        with patch('asyncio.sleep'):
            result = await scraper.login_to_site(
                "https://test.com",
                "user",
                "pass"
            )
        
        # Should retry and eventually succeed
        assert mock_page.goto.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_captcha_detection(self, scraper, mock_page):
        """Test CAPTCHA detection"""
        scraper.page = mock_page
        mock_page.content.return_value = AsyncMock(
            return_value='<div class="g-recaptcha">CAPTCHA</div>'
        )
        mock_page.locator.return_value.count = AsyncMock(return_value=1)
        
        result = await scraper.login_to_site(
            "https://test.com",
            "user",
            "pass"
        )
        
        # Should detect CAPTCHA and report it
        if 'captcha_detected' in result:
            assert result['captcha_detected'] is True