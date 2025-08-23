from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import re

class CategorizationService:
    """Service for categorizing accounts by type and risk level"""
    
    # Category definitions with keywords and domains
    CATEGORIES = {
        'social_media': {
            'name': 'Social Media',
            'description': 'Social networking and communication platforms',
            'keywords': ['social', 'chat', 'message', 'friend', 'follow', 'post', 'share'],
            'domains': [
                'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
                'snapchat.com', 'tiktok.com', 'pinterest.com', 'reddit.com',
                'tumblr.com', 'discord.com', 'telegram.org', 'whatsapp.com',
                'youtube.com', 'twitch.tv', 'mastodon.social', 'threads.net'
            ],
            'risk_level': 'high',
            'data_sensitivity': 'high'
        },
        'finance': {
            'name': 'Finance & Banking',
            'description': 'Financial services, banking, and payment platforms',
            'keywords': ['bank', 'finance', 'payment', 'money', 'invest', 'crypto', 'wallet'],
            'domains': [
                'paypal.com', 'venmo.com', 'cashapp.com', 'zelle.com',
                'coinbase.com', 'binance.com', 'robinhood.com', 'etrade.com',
                'chase.com', 'bankofamerica.com', 'wellsfargo.com', 'citi.com',
                'stripe.com', 'square.com', 'wise.com', 'revolut.com'
            ],
            'risk_level': 'critical',
            'data_sensitivity': 'critical'
        },
        'shopping': {
            'name': 'Shopping & E-commerce',
            'description': 'Online shopping and marketplace platforms',
            'keywords': ['shop', 'buy', 'store', 'market', 'cart', 'order'],
            'domains': [
                'amazon.com', 'ebay.com', 'etsy.com', 'alibaba.com',
                'walmart.com', 'target.com', 'bestbuy.com', 'costco.com',
                'shopify.com', 'wish.com', 'aliexpress.com', 'wayfair.com',
                'ikea.com', 'homedepot.com', 'lowes.com', 'newegg.com'
            ],
            'risk_level': 'medium',
            'data_sensitivity': 'medium'
        },
        'entertainment': {
            'name': 'Entertainment & Streaming',
            'description': 'Video, music, and gaming platforms',
            'keywords': ['watch', 'stream', 'music', 'video', 'game', 'play', 'movie'],
            'domains': [
                'netflix.com', 'hulu.com', 'disney.com', 'hbomax.com',
                'spotify.com', 'apple.com/music', 'pandora.com', 'soundcloud.com',
                'steam.com', 'epicgames.com', 'xbox.com', 'playstation.com',
                'prime.amazon.com', 'peacocktv.com', 'paramount.com', 'crunchyroll.com'
            ],
            'risk_level': 'low',
            'data_sensitivity': 'low'
        },
        'productivity': {
            'name': 'Productivity & Work',
            'description': 'Work, productivity, and collaboration tools',
            'keywords': ['work', 'office', 'document', 'project', 'team', 'task'],
            'domains': [
                'slack.com', 'zoom.us', 'teams.microsoft.com', 'asana.com',
                'trello.com', 'notion.so', 'evernote.com', 'todoist.com',
                'dropbox.com', 'box.com', 'drive.google.com', 'onedrive.com',
                'jira.atlassian.com'
            ],
            'risk_level': 'medium',
            'data_sensitivity': 'high'
        },
        'email': {
            'name': 'Email Services',
            'description': 'Email providers and communication services',
            'keywords': ['mail', 'email', 'inbox', 'message'],
            'domains': [
                'gmail.com', 'outlook.com', 'yahoo.com', 'protonmail.com',
                'icloud.com', 'mail.com', 'aol.com', 'zoho.com',
                'fastmail.com', 'tutanota.com', 'gmx.com', 'yandex.com'
            ],
            'risk_level': 'high',
            'data_sensitivity': 'critical'
        },
        'travel': {
            'name': 'Travel & Transportation',
            'description': 'Travel booking, accommodation, and transportation',
            'keywords': ['travel', 'flight', 'hotel', 'book', 'trip', 'ride'],
            'domains': [
                'airbnb.com', 'booking.com', 'expedia.com', 'hotels.com',
                'uber.com', 'lyft.com', 'doordash.com', 'grubhub.com',
                'tripadvisor.com', 'kayak.com', 'priceline.com', 'vrbo.com',
                'united.com', 'delta.com', 'southwest.com', 'aa.com'
            ],
            'risk_level': 'medium',
            'data_sensitivity': 'medium'
        },
        'health': {
            'name': 'Health & Fitness',
            'description': 'Health, fitness, and medical services',
            'keywords': ['health', 'fitness', 'medical', 'doctor', 'workout', 'diet'],
            'domains': [
                'myfitnesspal.com', 'fitbit.com', 'strava.com', 'peloton.com',
                'headspace.com', 'calm.com', 'betterhelp.com', 'zocdoc.com',
                'cvs.com', 'walgreens.com', 'goodrx.com', 'webmd.com',
                'mychart.com', 'healthgrades.com', '23andme.com', 'ancestry.com'
            ],
            'risk_level': 'high',
            'data_sensitivity': 'critical'
        },
        'education': {
            'name': 'Education & Learning',
            'description': 'Educational platforms and learning resources',
            'keywords': ['learn', 'course', 'education', 'study', 'school', 'university'],
            'domains': [
                'coursera.org', 'udemy.com', 'edx.org', 'khanacademy.org',
                'duolingo.com', 'codecademy.com', 'udacity.com', 'skillshare.com',
                'linkedin.com/learning', 'pluralsight.com', 'masterclass.com',
                'chegg.com', 'quizlet.com', 'canvas.instructure.com'
            ],
            'risk_level': 'low',
            'data_sensitivity': 'medium'
        },
        'dating': {
            'name': 'Dating & Relationships',
            'description': 'Dating apps and relationship platforms',
            'keywords': ['date', 'dating', 'match', 'love', 'relationship', 'meet'],
            'domains': [
                'tinder.com', 'bumble.com', 'hinge.co', 'match.com',
                'okcupid.com', 'pof.com', 'eharmony.com', 'zoosk.com',
                'coffee-meets-bagel.com', 'happn.com', 'badoo.com', 'her.com'
            ],
            'risk_level': 'high',
            'data_sensitivity': 'high'
        },
        'news': {
            'name': 'News & Media',
            'description': 'News outlets and media platforms',
            'keywords': ['news', 'article', 'media', 'journal', 'magazine'],
            'domains': [
                'nytimes.com', 'wsj.com', 'washingtonpost.com', 'cnn.com',
                'bbc.com', 'theguardian.com', 'reuters.com', 'bloomberg.com',
                'medium.com', 'substack.com', 'flipboard.com', 'feedly.com'
            ],
            'risk_level': 'low',
            'data_sensitivity': 'low'
        },
        'developer': {
            'name': 'Developer Tools',
            'description': 'Development, coding, and technical platforms',
            'keywords': ['code', 'develop', 'api', 'host', 'deploy', 'database'],
            'domains': [
                'github.com', 'gitlab.com', 'bitbucket.org', 'stackoverflow.com',
                'aws.amazon.com', 'cloud.google.com', 'azure.microsoft.com',
                'heroku.com', 'vercel.com', 'netlify.com', 'digitalocean.com',
                'docker.com', 'npmjs.com', 'pypi.org', 'jetbrains.com'
            ],
            'risk_level': 'medium',
            'data_sensitivity': 'high'
        },
        'other': {
            'name': 'Other',
            'description': 'Uncategorized services',
            'keywords': [],
            'domains': [],
            'risk_level': 'medium',
            'data_sensitivity': 'medium'
        }
    }
    
    # Risk assessment factors
    RISK_FACTORS = {
        'has_payment_info': 3,
        'has_personal_data': 2,
        'has_private_messages': 2,
        'has_location_data': 2,
        'has_health_data': 3,
        'has_financial_data': 3,
        'has_biometric_data': 3,
        'is_identity_provider': 2,
        'shares_data_third_party': 1,
        'difficult_to_delete': 1
    }
    
    def categorize_account(self, site_name: str, site_url: str) -> Dict[str, any]:
        """
        Categorize an account based on site name and URL
        
        Returns:
            Dictionary with category, confidence, risk_level, and data_sensitivity
        """
        # Parse domain from URL
        domain = self._extract_domain(site_url)
        site_lower = site_name.lower() if site_name else ''
        
        # Check exact domain match first
        for category_id, category_data in self.CATEGORIES.items():
            if domain in category_data['domains']:
                return {
                    'category': category_id,
                    'category_name': category_data['name'],
                    'confidence': 1.0,
                    'risk_level': category_data['risk_level'],
                    'data_sensitivity': category_data['data_sensitivity']
                }
        
        # Check keywords in site name
        best_match = None
        best_score = 0
        
        for category_id, category_data in self.CATEGORIES.items():
            if category_id == 'other':
                continue
                
            score = 0
            for keyword in category_data['keywords']:
                if keyword in site_lower:
                    score += 1
                if keyword in domain:
                    score += 0.5
            
            if score > best_score:
                best_score = score
                best_match = category_id
        
        if best_match and best_score > 0:
            category_data = self.CATEGORIES[best_match]
            confidence = min(best_score / 3, 1.0)  # Normalize confidence
            return {
                'category': best_match,
                'category_name': category_data['name'],
                'confidence': confidence,
                'risk_level': category_data['risk_level'],
                'data_sensitivity': category_data['data_sensitivity']
            }
        
        # Default to 'other' category
        return {
            'category': 'other',
            'category_name': self.CATEGORIES['other']['name'],
            'confidence': 0.5,
            'risk_level': self.CATEGORIES['other']['risk_level'],
            'data_sensitivity': self.CATEGORIES['other']['data_sensitivity']
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            if not url:
                return ''
            
            # Handle invalid URLs that don't look like domains
            if not '.' in url and not url.startswith(('http://', 'https://')):
                return ''
            
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            if not domain:
                # If no netloc, try to extract from path
                domain = url.replace('https://', '').replace('http://', '').split('/')[0]
            
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Final validation - must have a dot for a valid domain
            if '.' not in domain:
                return ''
            
            return domain
        except:
            return ''
    
    def assess_deletion_priority(self, category: str, risk_level: str, 
                                last_used: Optional[str] = None,
                                has_breach: bool = False) -> Tuple[int, str]:
        """
        Assess deletion priority for an account
        
        Returns:
            Tuple of (priority_score, priority_label)
            Priority score: 1-10 (10 being highest priority)
            Priority label: 'critical', 'high', 'medium', 'low'
        """
        score = 5  # Base score
        
        # Adjust based on risk level
        risk_scores = {
            'critical': 3,
            'high': 2,
            'medium': 1,
            'low': 0
        }
        score += risk_scores.get(risk_level, 0)
        
        # Adjust based on category
        high_priority_categories = ['finance', 'health', 'email', 'social_media']
        low_priority_categories = ['news', 'entertainment', 'education']
        
        if category in high_priority_categories:
            score += 1
        elif category in low_priority_categories:
            score -= 1
        
        # Breach increases priority
        if has_breach:
            score += 2
        
        # Normalize score
        score = max(1, min(10, score))
        
        # Determine label
        if score >= 8:
            label = 'critical'
        elif score >= 6:
            label = 'high'
        elif score >= 4:
            label = 'medium'
        else:
            label = 'low'
        
        return score, label
    
    def get_category_stats(self, accounts: List[Dict]) -> Dict[str, any]:
        """
        Get statistics about account categories
        
        Args:
            accounts: List of account dictionaries
            
        Returns:
            Dictionary with category statistics
        """
        stats = {
            'total_accounts': len(accounts),
            'by_category': {},
            'by_risk_level': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            },
            'recommendations': []
        }
        
        # Count by category
        for account in accounts:
            category = account.get('category', 'other')
            if category not in stats['by_category']:
                stats['by_category'][category] = {
                    'count': 0,
                    'name': self.CATEGORIES[category]['name']
                }
            stats['by_category'][category]['count'] += 1
            
            # Count by risk level
            risk_level = account.get('risk_level', 'medium')
            stats['by_risk_level'][risk_level] += 1
        
        # Generate recommendations
        if stats['by_risk_level']['critical'] > 0:
            stats['recommendations'].append({
                'priority': 'critical',
                'message': f"You have {stats['by_risk_level']['critical']} critical risk accounts. Delete these immediately.",
                'action': 'filter_critical'
            })
        
        if stats['by_category'].get('finance', {}).get('count', 0) > 5:
            stats['recommendations'].append({
                'priority': 'high',
                'message': "You have many financial accounts. Consider consolidating.",
                'action': 'filter_finance'
            })
        
        if stats['by_category'].get('social_media', {}).get('count', 0) > 10:
            stats['recommendations'].append({
                'priority': 'medium',
                'message': "Large social media footprint detected. Review privacy settings.",
                'action': 'filter_social'
            })
        
        return stats
    
    def suggest_bulk_actions(self, accounts: List[Dict]) -> List[Dict]:
        """
        Suggest bulk deletion actions based on account patterns
        
        Returns:
            List of suggested bulk actions
        """
        suggestions = []
        
        # Group accounts by category
        by_category = {}
        for account in accounts:
            category = account.get('category', 'other')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(account)
        
        # Suggest deleting unused entertainment accounts
        if 'entertainment' in by_category and len(by_category['entertainment']) > 3:
            suggestions.append({
                'title': 'Clean up streaming services',
                'description': f"You have {len(by_category['entertainment'])} entertainment accounts. Consider deleting unused subscriptions.",
                'category': 'entertainment',
                'account_ids': [a['id'] for a in by_category['entertainment']],
                'priority': 'low'
            })
        
        # Suggest reviewing old social media
        if 'social_media' in by_category and len(by_category['social_media']) > 5:
            suggestions.append({
                'title': 'Reduce social media presence',
                'description': f"You have {len(by_category['social_media'])} social media accounts. Consider deleting inactive profiles.",
                'category': 'social_media',
                'account_ids': [a['id'] for a in by_category['social_media']],
                'priority': 'medium'
            })
        
        # Suggest securing financial accounts
        if 'finance' in by_category:
            suggestions.append({
                'title': 'Secure financial accounts',
                'description': f"Review and secure your {len(by_category['finance'])} financial accounts before deletion.",
                'category': 'finance',
                'account_ids': [a['id'] for a in by_category['finance']],
                'priority': 'high'
            })
        
        return suggestions


# Singleton instance
categorization_service = CategorizationService()