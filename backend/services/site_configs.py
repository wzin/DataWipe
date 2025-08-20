"""
Site-specific configurations for automated account deletion.
Each configuration includes selectors and steps for different services.
"""

SITE_CONFIGS = {
    # Google/Gmail
    "google.com": {
        "login_url": "https://accounts.google.com/signin",
        "account_settings_url": "https://myaccount.google.com/data-and-privacy",
        "username_selector": 'input[type="email"]',
        "password_selector": 'input[type="password"]',
        "login_button_selector": '#passwordNext',
        "deletion_link_texts": ["Delete your Google Account"],
        "deletion_link_selector": 'a[href*="deleteaccount"]',
        "confirmation_steps": [
            {"type": "check", "selector": 'input[type="checkbox"][name="confirm"]'},
            {"type": "fill", "selector": 'input[name="password"]', "value": "{password}"}
        ],
        "confirm_button_texts": ["Delete Account"],
        "success_indicators": ["text=/account.*deleted/i"],
        "difficulty": 7,
        "requires_2fa": True,
        "estimated_time": "5-10 minutes"
    },
    
    # Facebook
    "facebook.com": {
        "login_url": "https://www.facebook.com/",
        "account_settings_url": "https://www.facebook.com/settings",
        "username_selector": 'input[name="email"]',
        "password_selector": 'input[name="pass"]',
        "login_button_selector": 'button[name="login"]',
        "deletion_link_texts": ["Deactivation and Deletion", "Delete Account"],
        "confirmation_steps": [
            {"type": "click", "selector": 'input[value="delete_account"]'},
            {"type": "click", "selector": 'button:has-text("Continue to Account Deletion")'},
            {"type": "fill", "selector": 'input[type="password"]', "value": "{password}"}
        ],
        "confirm_button_texts": ["Delete Account"],
        "success_indicators": ["text=/account.*scheduled.*deletion/i"],
        "difficulty": 6,
        "requires_2fa": False,
        "estimated_time": "3-5 minutes"
    },
    
    # Twitter/X
    "twitter.com": {
        "login_url": "https://twitter.com/login",
        "account_settings_url": "https://twitter.com/settings/account",
        "username_selector": 'input[name="text"]',
        "password_selector": 'input[name="password"]',
        "login_button_selector": 'div[data-testid="LoginForm_Login_Button"]',
        "deletion_link_texts": ["Deactivate your account"],
        "confirmation_steps": [
            {"type": "click", "selector": 'button:has-text("Deactivate")'},
            {"type": "fill", "selector": 'input[type="password"]', "value": "{password}"}
        ],
        "confirm_button_texts": ["Deactivate"],
        "success_indicators": ["text=/account.*deactivated/i"],
        "difficulty": 5,
        "requires_2fa": False,
        "estimated_time": "2-3 minutes"
    },
    
    "x.com": {  # Same as Twitter
        "login_url": "https://x.com/login",
        "account_settings_url": "https://x.com/settings/account",
        "username_selector": 'input[name="text"]',
        "password_selector": 'input[name="password"]',
        "login_button_selector": 'div[data-testid="LoginForm_Login_Button"]',
        "deletion_link_texts": ["Deactivate your account"],
        "confirmation_steps": [
            {"type": "click", "selector": 'button:has-text("Deactivate")'},
            {"type": "fill", "selector": 'input[type="password"]', "value": "{password}"}
        ],
        "confirm_button_texts": ["Deactivate"],
        "success_indicators": ["text=/account.*deactivated/i"],
        "difficulty": 5,
        "requires_2fa": False,
        "estimated_time": "2-3 minutes"
    },
    
    # Instagram
    "instagram.com": {
        "login_url": "https://www.instagram.com/accounts/login/",
        "account_settings_url": "https://www.instagram.com/accounts/remove/request/permanent/",
        "username_selector": 'input[name="username"]',
        "password_selector": 'input[name="password"]',
        "login_button_selector": 'button[type="submit"]',
        "deletion_link_texts": ["Delete Your Account"],
        "confirmation_steps": [
            {"type": "select", "selector": 'select', "value": "Prefer not to say"},
            {"type": "fill", "selector": 'input[type="password"]', "value": "{password}"}
        ],
        "confirm_button_texts": ["Permanently delete my account"],
        "success_indicators": ["text=/account.*deleted/i"],
        "difficulty": 5,
        "requires_2fa": False,
        "estimated_time": "2-3 minutes"
    },
    
    # LinkedIn
    "linkedin.com": {
        "login_url": "https://www.linkedin.com/login",
        "account_settings_url": "https://www.linkedin.com/mypreferences/d/accounts",
        "username_selector": 'input[id="username"]',
        "password_selector": 'input[id="password"]',
        "login_button_selector": 'button[type="submit"]',
        "deletion_link_texts": ["Close account"],
        "confirmation_steps": [
            {"type": "click", "selector": 'input[value="other"]'},
            {"type": "click", "selector": 'button:has-text("Continue")'},
            {"type": "fill", "selector": 'input[type="password"]', "value": "{password}"}
        ],
        "confirm_button_texts": ["Done"],
        "success_indicators": ["text=/account.*closed/i"],
        "difficulty": 4,
        "requires_2fa": False,
        "estimated_time": "2-3 minutes"
    },
    
    # Reddit
    "reddit.com": {
        "login_url": "https://www.reddit.com/login",
        "account_settings_url": "https://www.reddit.com/settings/account",
        "username_selector": 'input[name="username"]',
        "password_selector": 'input[name="password"]',
        "login_button_selector": 'button[type="submit"]',
        "deletion_link_texts": ["Delete account"],
        "confirmation_steps": [
            {"type": "fill", "selector": 'input[name="username"]', "value": "{username}"},
            {"type": "fill", "selector": 'input[name="password"]', "value": "{password}"},
            {"type": "check", "selector": 'input[type="checkbox"]'}
        ],
        "confirm_button_texts": ["Delete"],
        "success_indicators": ["text=/account.*deleted/i"],
        "difficulty": 3,
        "requires_2fa": False,
        "estimated_time": "2-3 minutes"
    },
    
    # Amazon
    "amazon.com": {
        "login_url": "https://www.amazon.com/ap/signin",
        "account_settings_url": "https://www.amazon.com/gp/privacycentral/dsar/preview.html",
        "username_selector": 'input[type="email"]',
        "password_selector": 'input[type="password"]',
        "login_button_selector": 'input[id="signInSubmit"]',
        "deletion_link_texts": ["Close Your Amazon Account"],
        "confirmation_steps": [
            {"type": "check", "selector": 'input[type="checkbox"][name="confirm"]'},
            {"type": "click", "selector": 'button:has-text("Close my account")'}
        ],
        "confirm_button_texts": ["Close my account"],
        "success_indicators": ["text=/account.*closed/i"],
        "difficulty": 6,
        "requires_2fa": False,
        "estimated_time": "3-5 minutes"
    },
    
    # Microsoft
    "microsoft.com": {
        "login_url": "https://login.microsoftonline.com/",
        "account_settings_url": "https://account.microsoft.com/privacy",
        "username_selector": 'input[type="email"]',
        "password_selector": 'input[type="password"]',
        "login_button_selector": 'input[type="submit"]',
        "deletion_link_texts": ["Close account"],
        "confirmation_steps": [
            {"type": "click", "selector": 'button:has-text("Next")'},
            {"type": "check", "selector": 'input[type="checkbox"]'},
            {"type": "click", "selector": 'button:has-text("Mark account for closure")'}
        ],
        "confirm_button_texts": ["Done"],
        "success_indicators": ["text=/account.*closed/i"],
        "difficulty": 6,
        "requires_2fa": True,
        "estimated_time": "5-7 minutes"
    },
    
    # Apple
    "apple.com": {
        "login_url": "https://appleid.apple.com/sign-in",
        "account_settings_url": "https://privacy.apple.com/",
        "username_selector": 'input[type="text"][can-field="accountName"]',
        "password_selector": 'input[type="password"]',
        "login_button_selector": 'button[id="sign-in"]',
        "deletion_link_texts": ["Delete your account"],
        "confirmation_steps": [
            {"type": "select", "selector": 'select', "value": "Other"},
            {"type": "click", "selector": 'button:has-text("Continue")'},
            {"type": "check", "selector": 'input[type="checkbox"]'}
        ],
        "confirm_button_texts": ["Delete account"],
        "success_indicators": ["text=/account.*deleted/i"],
        "difficulty": 7,
        "requires_2fa": True,
        "estimated_time": "5-10 minutes"
    },
    
    # Yahoo
    "yahoo.com": {
        "login_url": "https://login.yahoo.com/",
        "account_settings_url": "https://login.yahoo.com/account/delete-user",
        "username_selector": 'input[name="username"]',
        "password_selector": 'input[name="password"]',
        "login_button_selector": 'input[type="submit"]',
        "deletion_link_texts": ["Delete account"],
        "confirmation_steps": [
            {"type": "fill", "selector": 'input[type="password"]', "value": "{password}"},
            {"type": "click", "selector": 'button:has-text("Yes, delete this account")'}
        ],
        "confirm_button_texts": ["Yes, delete this account"],
        "success_indicators": ["text=/account.*deleted/i"],
        "difficulty": 4,
        "requires_2fa": False,
        "estimated_time": "2-3 minutes"
    },
    
    # Pinterest
    "pinterest.com": {
        "login_url": "https://www.pinterest.com/login/",
        "account_settings_url": "https://www.pinterest.com/settings/account-settings/",
        "username_selector": 'input[type="email"]',
        "password_selector": 'input[type="password"]',
        "login_button_selector": 'button[type="submit"]',
        "deletion_link_texts": ["Delete account"],
        "confirmation_steps": [
            {"type": "click", "selector": 'button:has-text("Continue")'},
            {"type": "fill", "selector": 'input[type="password"]', "value": "{password}"},
            {"type": "click", "selector": 'button:has-text("Delete account")'}
        ],
        "confirm_button_texts": ["Delete account"],
        "success_indicators": ["text=/account.*deleted/i"],
        "difficulty": 3,
        "requires_2fa": False,
        "estimated_time": "2-3 minutes"
    },
    
    # Spotify
    "spotify.com": {
        "login_url": "https://accounts.spotify.com/login",
        "account_settings_url": "https://www.spotify.com/account/privacy/",
        "username_selector": 'input[id="login-username"]',
        "password_selector": 'input[id="login-password"]',
        "login_button_selector": 'button[id="login-button"]',
        "deletion_link_texts": ["Close account"],
        "confirmation_steps": [
            {"type": "click", "selector": 'button:has-text("Close Account")'}
        ],
        "confirm_button_texts": ["Close Account"],
        "success_indicators": ["text=/account.*closed/i"],
        "difficulty": 3,
        "requires_2fa": False,
        "estimated_time": "2-3 minutes"
    },
    
    # Netflix
    "netflix.com": {
        "login_url": "https://www.netflix.com/login",
        "account_settings_url": "https://www.netflix.com/account",
        "username_selector": 'input[name="userLoginId"]',
        "password_selector": 'input[name="password"]',
        "login_button_selector": 'button[type="submit"]',
        "deletion_link_texts": ["Cancel Membership"],
        "confirmation_steps": [
            {"type": "click", "selector": 'button:has-text("Finish Cancellation")'}
        ],
        "confirm_button_texts": ["Finish Cancellation"],
        "success_indicators": ["text=/membership.*cancelled/i"],
        "difficulty": 2,
        "requires_2fa": False,
        "estimated_time": "1-2 minutes"
    }
}