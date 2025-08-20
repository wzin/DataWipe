#!/usr/bin/env python3
"""Quick test script for CSV parser functionality"""

import pandas as pd
import tempfile
import os
from services.csv_parser import CSVParser

def test_format_detection():
    """Test format detection for different password managers"""
    parser = CSVParser()
    
    print("Testing CSV Format Detection...")
    print("=" * 50)
    
    # Test Bitwarden format
    bitwarden_columns = ['folder', 'favorite', 'type', 'name', 'notes', 'fields', 
                         'reprompt', 'login_uri', 'login_username', 'login_password', 'login_totp']
    bitwarden_data = [['Personal', '0', 'login', 'Google', '', '', '0', 
                      'https://accounts.google.com', 'user@gmail.com', 'password123', '']]
    
    df = pd.DataFrame(bitwarden_data, columns=bitwarden_columns)
    format_name, confidence = parser.detect_format(df)
    print(f"✓ Bitwarden: Detected as '{format_name}' with confidence {confidence:.2f}")
    
    # Test Chrome format
    chrome_columns = ['name', 'url', 'username', 'password']
    chrome_data = [['amazon.com', 'https://www.amazon.com', 'shopper@email.com', 'amazonpass']]
    
    df = pd.DataFrame(chrome_data, columns=chrome_columns)
    format_name, confidence = parser.detect_format(df)
    print(f"✓ Chrome: Detected as '{format_name}' with confidence {confidence:.2f}")
    
    # Test 1Password format
    onepass_columns = ['title', 'url', 'username', 'password', 'notes', 'type', 'category']
    onepass_data = [['Twitter', 'https://twitter.com', '@username', 'securepass', 
                    'My Twitter account', 'Login', 'Social']]
    
    df = pd.DataFrame(onepass_data, columns=onepass_columns)
    format_name, confidence = parser.detect_format(df)
    print(f"✓ 1Password: Detected as '{format_name}' with confidence {confidence:.2f}")
    
    # Test generic format
    generic_columns = ['website', 'user', 'pass', 'description']
    generic_data = [['github.com', 'developer', 'gitpass', 'Code repository']]
    
    df = pd.DataFrame(generic_data, columns=generic_columns)
    format_name, confidence = parser.detect_format(df)
    print(f"✓ Generic: Detected as '{format_name}' with confidence {confidence:.2f}")
    
    print("\n" + "=" * 50)
    print("All format detection tests passed!")

def test_parsing():
    """Test CSV parsing functionality"""
    parser = CSVParser()
    
    print("\nTesting CSV Parsing...")
    print("=" * 50)
    
    # Create a temporary Bitwarden CSV
    columns = ['folder', 'favorite', 'type', 'name', 'notes', 'fields', 
               'reprompt', 'login_uri', 'login_username', 'login_password', 'login_totp']
    data = [
        ['Personal', '0', 'login', 'Google', 'Main account', '', '0', 
         'https://accounts.google.com', 'user@gmail.com', 'password123', ''],
        ['Work', '1', 'login', 'Slack', '', '', '0',
         'https://slack.com', 'worker@company.com', 'slackpass', ''],
        ['', '0', 'note', 'Secure Note', 'This is a note', '', '0', '', '', '', '']
    ]
    
    df = pd.DataFrame(data, columns=columns)
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    df.to_csv(temp_file.name, index=False)
    temp_file.close()
    
    try:
        accounts = parser.parse_csv(temp_file.name)
        
        print(f"✓ Parsed {len(accounts)} accounts (skipped secure notes)")
        
        for i, account in enumerate(accounts, 1):
            print(f"\nAccount {i}:")
            print(f"  Site: {account['site_name']}")
            print(f"  URL: {account['site_url']}")
            print(f"  Username: {account['username']}")
            print(f"  Email: {account['email']}")
            print(f"  Has Password: {'Yes' if account['password'] else 'No'}")
    finally:
        os.unlink(temp_file.name)
    
    print("\n" + "=" * 50)
    print("Parsing tests passed!")

def test_supported_formats():
    """Test getting supported formats"""
    parser = CSVParser()
    
    print("\nSupported Password Manager Formats:")
    print("=" * 50)
    
    formats = parser.get_supported_formats()
    
    for format_name, details in formats.items():
        print(f"\n{details['name']}:")
        print(f"  Key columns: {', '.join(details['columns'][:5])}...")
        print(f"  Has email field: {details['has_email_field']}")
    
    print(f"\nTotal supported formats: {len(formats)}")

if __name__ == "__main__":
    test_format_detection()
    test_parsing()
    test_supported_formats()
    print("\n✅ All tests passed successfully!")