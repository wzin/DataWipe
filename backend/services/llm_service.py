import openai
import anthropic
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import json
import re
from datetime import datetime
import asyncio

from models import LLMInteraction, LLMProvider, LLMTaskType, Account, SiteMetadata
from config import settings


class LLMService:
    """Service for LLM interactions"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        if settings.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        
        if settings.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    
    async def discover_accounts(self, accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use LLM to discover and enrich account information"""
        
        # Group accounts by domain for batch processing
        domains = {}
        for account in accounts:
            domain = self._extract_domain(account['site_url'])
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(account)
        
        enriched_accounts = []
        
        for domain, domain_accounts in domains.items():
            try:
                # Get site metadata
                site_info = await self._discover_site_info(domain, domain_accounts[0])
                
                # Enrich each account with site info
                for account in domain_accounts:
                    account.update(site_info)
                    enriched_accounts.append(account)
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error processing domain {domain}: {e}")
                # Add accounts without enrichment
                enriched_accounts.extend(domain_accounts)
        
        return enriched_accounts
    
    async def _discover_site_info(self, domain: str, sample_account: Dict[str, Any]) -> Dict[str, Any]:
        """Discover site information using LLM"""
        
        prompt = f"""
        Analyze this website and provide account deletion information:
        
        Domain: {domain}
        Site Name: {sample_account.get('site_name', 'Unknown')}
        Site URL: {sample_account.get('site_url', '')}
        
        Please provide:
        1. Official site name
        2. Account deletion procedure difficulty (1-10 scale)
        3. Privacy policy URL (if known)
        4. Data deletion contact email (if known)
        5. Account deletion URL (if known)
        6. Brief deletion instructions
        
        Format your response as JSON:
        {{
            "site_name": "Official Site Name",
            "deletion_difficulty": 5,
            "privacy_policy_url": "https://example.com/privacy",
            "deletion_contact_email": "privacy@example.com",
            "deletion_url": "https://example.com/account/delete",
            "deletion_instructions": "Go to Settings > Account > Delete Account"
        }}
        """
        
        try:
            response = await self._call_llm(prompt, LLMTaskType.DISCOVERY)
            site_info = json.loads(response)
            
            # Validate and clean response
            return {
                'site_name': site_info.get('site_name', sample_account.get('site_name', 'Unknown')),
                'deletion_difficulty': min(10, max(1, site_info.get('deletion_difficulty', 5))),
                'privacy_policy_url': site_info.get('privacy_policy_url', ''),
                'deletion_contact_email': site_info.get('deletion_contact_email', ''),
                'deletion_url': site_info.get('deletion_url', ''),
                'deletion_instructions': site_info.get('deletion_instructions', '')
            }
        
        except Exception as e:
            print(f"Error discovering site info for {domain}: {e}")
            return {
                'deletion_difficulty': 5,
                'privacy_policy_url': '',
                'deletion_contact_email': '',
                'deletion_url': '',
                'deletion_instructions': ''
            }
    
    async def generate_deletion_email(self, account: Account, site_metadata: Optional[SiteMetadata] = None) -> str:
        """Generate GDPR deletion email"""
        
        prompt = f"""
        Generate a professional GDPR Article 17 deletion request email for:
        
        Site: {account.site_name}
        Username: {account.username}
        Email: {account.email}
        Site URL: {account.site_url}
        
        Requirements:
        1. Reference GDPR Article 17 (Right to Erasure)
        2. Request complete deletion of all personal data
        3. Include account identifier
        4. Specify 30-day compliance timeline
        5. Professional but firm tone
        6. Request confirmation of deletion
        
        Format as a complete email with subject line.
        """
        
        try:
            response = await self._call_llm(prompt, LLMTaskType.EMAIL_GENERATION, account_id=account.id)
            return response
        
        except Exception as e:
            print(f"Error generating deletion email: {e}")
            return self._generate_fallback_email(account)
    
    async def analyze_deletion_page(self, html_content: str, site_name: str) -> Dict[str, Any]:
        """Analyze deletion page HTML and provide navigation instructions"""
        
        prompt = f"""
        Analyze this HTML content from {site_name} and provide account deletion navigation instructions:
        
        HTML Content (truncated):
        {html_content[:3000]}...
        
        Provide:
        1. Step-by-step deletion instructions
        2. CSS selectors for key elements
        3. Expected confirmation texts
        4. Difficulty assessment (1-10)
        5. Any warnings or important notes
        
        Format as JSON:
        {{
            "instructions": ["Step 1", "Step 2", "Step 3"],
            "selectors": {{
                "delete_button": "selector",
                "confirm_button": "selector",
                "password_field": "selector"
            }},
            "confirmation_texts": ["Are you sure?", "This will delete your account"],
            "difficulty": 5,
            "warnings": ["Account deletion is permanent", "Download data first"]
        }}
        """
        
        try:
            response = await self._call_llm(prompt, LLMTaskType.NAVIGATION)
            return json.loads(response)
        
        except Exception as e:
            print(f"Error analyzing deletion page: {e}")
            return {
                "instructions": ["Navigate to account settings", "Look for delete account option"],
                "selectors": {},
                "confirmation_texts": [],
                "difficulty": 8,
                "warnings": ["Automated deletion not supported"]
            }
    
    async def _call_llm(self, prompt: str, task_type: LLMTaskType, account_id: Optional[int] = None) -> str:
        """Call LLM with cost tracking"""
        
        provider = LLMProvider.OPENAI if self.openai_client else LLMProvider.ANTHROPIC
        
        try:
            if provider == LLMProvider.OPENAI:
                response = await self._call_openai(prompt)
            else:
                response = await self._call_anthropic(prompt)
            
            # Log interaction (implement cost tracking)
            # await self._log_interaction(provider, task_type, prompt, response, account_id)
            
            return response
        
        except Exception as e:
            print(f"LLM call failed: {e}")
            raise
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant specializing in GDPR compliance and account deletion procedures."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.1
        )
        
        return response.choices[0].message.content
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        
        response = self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0.1,
            system="You are a helpful assistant specializing in GDPR compliance and account deletion procedures.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        import re
        
        # Remove protocol
        domain = re.sub(r'^https?://', '', url)
        # Remove www
        domain = re.sub(r'^www\.', '', domain)
        # Remove path
        domain = domain.split('/')[0]
        # Remove port
        domain = domain.split(':')[0]
        
        return domain
    
    def _generate_fallback_email(self, account: Account) -> str:
        """Generate fallback deletion email"""
        
        return f"""Subject: GDPR Article 17 Data Deletion Request

Dear {account.site_name} Privacy Team,

I am writing to request the complete deletion of my personal data from your platform in accordance with Article 17 of the EU General Data Protection Regulation (GDPR) - the Right to Erasure.

Account Details:
- Username: {account.username}
- Email: {account.email}
- Site: {account.site_url}

I request that you:
1. Delete all personal data associated with this account
2. Remove all records of my activity on your platform
3. Ensure no backups contain my personal information
4. Confirm completion of this deletion within 30 days

Please provide written confirmation once the deletion has been completed.

Thank you for your prompt attention to this matter.

Best regards,
[Your Name]

Note: This request is made under GDPR Article 17 and is legally binding for organizations processing EU residents' data.
"""
    
    async def _log_interaction(self, provider: LLMProvider, task_type: LLMTaskType, 
                             prompt: str, response: str, account_id: Optional[int] = None):
        """Log LLM interaction with cost tracking"""
        
        # Calculate approximate cost based on tokens
        tokens_used = len(prompt.split()) + len(response.split())
        cost = self._calculate_cost(provider, tokens_used)
        
        # This would be implemented with proper database session
        # For now, just log to console
        print(f"LLM Interaction: {provider.value} - {task_type.value} - {tokens_used} tokens - ${cost:.4f}")
    
    def _calculate_cost(self, provider: LLMProvider, tokens: int) -> float:
        """Calculate approximate cost for LLM usage"""
        
        # Approximate pricing (update with actual rates)
        if provider == LLMProvider.OPENAI:
            return tokens * 0.00003  # $0.03 per 1K tokens
        elif provider == LLMProvider.ANTHROPIC:
            return tokens * 0.00003  # Similar pricing
        
        return 0.0