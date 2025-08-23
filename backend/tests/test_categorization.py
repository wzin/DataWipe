import pytest
from services.categorization_service import categorization_service


class TestCategorizationService:
    """Test suite for account categorization service"""
    
    def test_categorize_social_media(self):
        """Test categorization of social media accounts"""
        result = categorization_service.categorize_account("Facebook", "https://facebook.com")
        assert result['category'] == 'social_media'
        assert result['confidence'] == 1.0
        assert result['risk_level'] == 'high'
        assert result['data_sensitivity'] == 'high'
        
        result = categorization_service.categorize_account("Twitter", "https://twitter.com")
        assert result['category'] == 'social_media'
        
        result = categorization_service.categorize_account("My Instagram", "https://instagram.com")
        assert result['category'] == 'social_media'
    
    def test_categorize_finance(self):
        """Test categorization of financial accounts"""
        result = categorization_service.categorize_account("PayPal", "https://paypal.com")
        assert result['category'] == 'finance'
        assert result['risk_level'] == 'critical'
        assert result['data_sensitivity'] == 'critical'
        
        result = categorization_service.categorize_account("Chase Bank", "https://chase.com")
        assert result['category'] == 'finance'
        
        result = categorization_service.categorize_account("Coinbase", "https://coinbase.com")
        assert result['category'] == 'finance'
    
    def test_categorize_shopping(self):
        """Test categorization of shopping accounts"""
        result = categorization_service.categorize_account("Amazon", "https://amazon.com")
        assert result['category'] == 'shopping'
        assert result['risk_level'] == 'medium'
        
        result = categorization_service.categorize_account("eBay", "https://ebay.com")
        assert result['category'] == 'shopping'
    
    def test_categorize_entertainment(self):
        """Test categorization of entertainment accounts"""
        result = categorization_service.categorize_account("Netflix", "https://netflix.com")
        assert result['category'] == 'entertainment'
        assert result['risk_level'] == 'low'
        
        result = categorization_service.categorize_account("Spotify", "https://spotify.com")
        assert result['category'] == 'entertainment'
    
    def test_categorize_productivity(self):
        """Test categorization of productivity accounts"""
        result = categorization_service.categorize_account("Slack", "https://slack.com")
        assert result['category'] == 'productivity'
        assert result['risk_level'] == 'medium'
        assert result['data_sensitivity'] == 'high'
        
        result = categorization_service.categorize_account("GitHub", "https://github.com")
        assert result['category'] == 'developer'  # GitHub is in developer category
    
    def test_categorize_email(self):
        """Test categorization of email accounts"""
        result = categorization_service.categorize_account("Gmail", "https://gmail.com")
        assert result['category'] == 'email'
        assert result['risk_level'] == 'high'
        assert result['data_sensitivity'] == 'critical'
        
        result = categorization_service.categorize_account("Outlook", "https://outlook.com")
        assert result['category'] == 'email'
    
    def test_categorize_travel(self):
        """Test categorization of travel accounts"""
        result = categorization_service.categorize_account("Airbnb", "https://airbnb.com")
        assert result['category'] == 'travel'
        assert result['risk_level'] == 'medium'
        
        result = categorization_service.categorize_account("Uber", "https://uber.com")
        assert result['category'] == 'travel'
    
    def test_categorize_health(self):
        """Test categorization of health accounts"""
        result = categorization_service.categorize_account("MyFitnessPal", "https://myfitnesspal.com")
        assert result['category'] == 'health'
        assert result['risk_level'] == 'high'
        assert result['data_sensitivity'] == 'critical'
        
        result = categorization_service.categorize_account("23andMe", "https://23andme.com")
        assert result['category'] == 'health'
    
    def test_categorize_education(self):
        """Test categorization of education accounts"""
        result = categorization_service.categorize_account("Coursera", "https://coursera.org")
        assert result['category'] == 'education'
        assert result['risk_level'] == 'low'
        
        result = categorization_service.categorize_account("Duolingo", "https://duolingo.com")
        assert result['category'] == 'education'
    
    def test_categorize_dating(self):
        """Test categorization of dating accounts"""
        result = categorization_service.categorize_account("Tinder", "https://tinder.com")
        assert result['category'] == 'dating'
        assert result['risk_level'] == 'high'
        assert result['data_sensitivity'] == 'high'
        
        result = categorization_service.categorize_account("Bumble", "https://bumble.com")
        assert result['category'] == 'dating'
    
    def test_categorize_news(self):
        """Test categorization of news accounts"""
        result = categorization_service.categorize_account("New York Times", "https://nytimes.com")
        assert result['category'] == 'news'
        assert result['risk_level'] == 'low'
        
        result = categorization_service.categorize_account("Medium", "https://medium.com")
        assert result['category'] == 'news'
    
    def test_categorize_developer(self):
        """Test categorization of developer accounts"""
        result = categorization_service.categorize_account("GitHub", "https://github.com")
        assert result['category'] == 'developer'
        assert result['risk_level'] == 'medium'
        assert result['data_sensitivity'] == 'high'
        
        result = categorization_service.categorize_account("Stack Overflow", "https://stackoverflow.com")
        assert result['category'] == 'developer'
    
    def test_categorize_unknown(self):
        """Test categorization of unknown accounts"""
        result = categorization_service.categorize_account("Random Site", "https://randomsite123.com")
        assert result['category'] == 'other'
        assert result['confidence'] == 0.5
        assert result['risk_level'] == 'medium'
    
    def test_categorize_by_keywords(self):
        """Test categorization by keywords in site name"""
        result = categorization_service.categorize_account("My Social Network", "https://example.com")
        assert result['category'] == 'social_media'
        assert result['confidence'] < 1.0  # Less confident since not exact match
        
        result = categorization_service.categorize_account("Shop Online", "https://example.com")
        assert result['category'] == 'shopping'
        
        result = categorization_service.categorize_account("Bank Account", "https://example.com")
        assert result['category'] == 'finance'
    
    def test_domain_extraction(self):
        """Test domain extraction from URLs"""
        assert categorization_service._extract_domain("https://www.facebook.com") == "facebook.com"
        assert categorization_service._extract_domain("http://google.com/path") == "google.com"
        assert categorization_service._extract_domain("netflix.com") == "netflix.com"
        assert categorization_service._extract_domain("https://WWW.AMAZON.COM") == "amazon.com"
        assert categorization_service._extract_domain("invalid-url") == ""
    
    def test_deletion_priority_assessment(self):
        """Test deletion priority assessment"""
        # Critical risk should have high priority
        score, label = categorization_service.assess_deletion_priority('finance', 'critical')
        assert score >= 8
        assert label == 'critical'
        
        # Low risk entertainment should have low priority
        score, label = categorization_service.assess_deletion_priority('entertainment', 'low')
        assert score <= 4
        assert label in ['low', 'medium']
        
        # High risk social media should have high priority
        score, label = categorization_service.assess_deletion_priority('social_media', 'high')
        assert score >= 6
        assert label in ['high', 'critical']
        
        # Breach increases priority
        score_no_breach, _ = categorization_service.assess_deletion_priority('shopping', 'medium')
        score_breach, _ = categorization_service.assess_deletion_priority('shopping', 'medium', has_breach=True)
        assert score_breach > score_no_breach
    
    def test_category_stats(self):
        """Test category statistics generation"""
        accounts = [
            {'id': 1, 'category': 'social_media', 'risk_level': 'high'},
            {'id': 2, 'category': 'social_media', 'risk_level': 'high'},
            {'id': 3, 'category': 'finance', 'risk_level': 'critical'},
            {'id': 4, 'category': 'shopping', 'risk_level': 'medium'},
            {'id': 5, 'category': 'entertainment', 'risk_level': 'low'},
        ]
        
        stats = categorization_service.get_category_stats(accounts)
        
        assert stats['total_accounts'] == 5
        assert stats['by_category']['social_media']['count'] == 2
        assert stats['by_category']['finance']['count'] == 1
        assert stats['by_risk_level']['critical'] == 1
        assert stats['by_risk_level']['high'] == 2
        assert stats['by_risk_level']['medium'] == 1
        assert stats['by_risk_level']['low'] == 1
        
        # Should have recommendations for critical accounts
        assert any('critical' in rec['priority'] for rec in stats['recommendations'])
    
    def test_bulk_action_suggestions(self):
        """Test bulk action suggestions"""
        accounts = [
            {'id': 1, 'category': 'entertainment'},
            {'id': 2, 'category': 'entertainment'},
            {'id': 3, 'category': 'entertainment'},
            {'id': 4, 'category': 'entertainment'},
            {'id': 5, 'category': 'social_media'},
            {'id': 6, 'category': 'social_media'},
            {'id': 7, 'category': 'social_media'},
            {'id': 8, 'category': 'social_media'},
            {'id': 9, 'category': 'social_media'},
            {'id': 10, 'category': 'social_media'},
            {'id': 11, 'category': 'finance'},
            {'id': 12, 'category': 'finance'},
        ]
        
        suggestions = categorization_service.suggest_bulk_actions(accounts)
        
        # Should suggest cleaning up entertainment accounts
        entertainment_suggestion = next((s for s in suggestions if s['category'] == 'entertainment'), None)
        assert entertainment_suggestion is not None
        assert len(entertainment_suggestion['account_ids']) == 4
        
        # Should suggest reducing social media presence
        social_suggestion = next((s for s in suggestions if s['category'] == 'social_media'), None)
        assert social_suggestion is not None
        assert len(social_suggestion['account_ids']) == 6
        
        # Should suggest securing financial accounts
        finance_suggestion = next((s for s in suggestions if s['category'] == 'finance'), None)
        assert finance_suggestion is not None
        assert finance_suggestion['priority'] == 'high'
    
    def test_all_categories_defined(self):
        """Test that all categories have proper definitions"""
        for category_id, category_data in categorization_service.CATEGORIES.items():
            assert 'name' in category_data
            assert 'description' in category_data
            assert 'keywords' in category_data
            assert 'domains' in category_data
            assert 'risk_level' in category_data
            assert 'data_sensitivity' in category_data
            
            # Check risk levels are valid
            assert category_data['risk_level'] in ['critical', 'high', 'medium', 'low']
            assert category_data['data_sensitivity'] in ['critical', 'high', 'medium', 'low']
    
    def test_case_insensitive_categorization(self):
        """Test that categorization is case-insensitive"""
        result1 = categorization_service.categorize_account("FACEBOOK", "HTTPS://FACEBOOK.COM")
        result2 = categorization_service.categorize_account("facebook", "https://facebook.com")
        result3 = categorization_service.categorize_account("FaceBook", "https://FaceBook.com")
        
        assert result1['category'] == result2['category'] == result3['category']
        assert result1['confidence'] == result2['confidence'] == result3['confidence']