import csv
import json
import time
import requests
from typing import List, Dict, Optional
import os
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Lead:
    first_name: str
    last_name: str
    email: str
    company_name: str
    position: str
    industry: str
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class LeadManager:
    def __init__(self, config: Dict):
        self.config = config
        self.snov_config = config.get('lead_sources', {}).get('snov_io', {})
        self.csv_config = config.get('lead_sources', {}).get('csv', {})
        self.rate_limits = config.get('rate_limits', {})
        self.last_api_call = 0
        self.access_token = None
        self.token_expires_at = None

    def _rate_limit(self):
        """Implement rate limiting for API calls"""
        if self.rate_limits.get('snov_api_calls_per_minute'):
            min_interval = 60 / self.rate_limits['snov_api_calls_per_minute']
            time_since_last = time.time() - self.last_api_call
            if time_since_last < min_interval:
                time.sleep(min_interval - time_since_last)
        self.last_api_call = time.time()

    def _get_oauth_token(self) -> str:
        """Get OAuth access token using client credentials"""
        client_id = os.getenv('SNOV_CLIENT_ID')
        client_secret = os.getenv('SNOV_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise ValueError("SNOV_CLIENT_ID and SNOV_CLIENT_SECRET must be set for OAuth authentication")
        
        # Check if we have a valid token
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        # Get new token
        base_url = self.snov_config.get('base_url', 'https://api.snov.io')
        url = f"{base_url}/v1/oauth/access_token"
        
        payload = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        try:
            print("🔑 Getting OAuth access token...")
            response = requests.post(url, data=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'access_token' not in data:
                raise Exception(f"No access_token in response: {data}")
            
            self.access_token = data['access_token']
            # Set expiration time (default 1 hour if not provided)
            expires_in = data.get('expires_in', 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # 1 minute buffer
            
            print("✅ OAuth token obtained successfully")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get OAuth token: {str(e)}")
        except Exception as e:
            raise Exception(f"OAuth token error: {str(e)}")

    def _get_api_credentials(self) -> Dict:
        """Get API credentials (either API key or OAuth token)"""
        # Try OAuth first (client credentials)
        if os.getenv('SNOV_CLIENT_ID') and os.getenv('SNOV_CLIENT_SECRET'):
            token = self._get_oauth_token()
            return {'type': 'oauth', 'token': token}
        
        # Fallback to API key
        api_key = os.getenv('SNOV_API_KEY') or self.snov_config.get('api_key', '').replace('${SNOV_API_KEY}', '')
        if api_key:
            return {'type': 'api_key', 'key': api_key}
        
        raise ValueError("No valid Snov.io credentials found. Set either SNOV_CLIENT_ID+SNOV_CLIENT_SECRET or SNOV_API_KEY")

    def load_csv_leads(self, file_path: Optional[str] = None) -> List[Lead]:
        """Load leads from CSV file"""
        if not file_path:
            file_path = self.csv_config.get('default_path', 'leads.csv')

        leads = []
        required_columns = self.csv_config.get('required_columns', [])

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                # Validate required columns
                missing_columns = [col for col in required_columns if col not in reader.fieldnames]
                if missing_columns:
                    raise ValueError(f"Missing required columns: {missing_columns}")

                for row in reader:
                    lead = Lead(
                        first_name=row.get('first_name', '').strip(),
                        last_name=row.get('last_name', '').strip(),
                        email=row.get('email', '').strip(),
                        company_name=row.get('company_name', '').strip(),
                        position=row.get('position', '').strip(),
                        industry=row.get('industry', '').strip(),
                        linkedin_url=row.get('linkedin_url', '').strip() or None,
                        phone=row.get('phone', '').strip() or None,
                        website=row.get('website', '').strip() or None,
                        company_size=row.get('company_size', '').strip() or None,
                        location=row.get('location', '').strip() or None,
                        notes=row.get('notes', '').strip() or None
                    )
                    leads.append(lead)

        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading CSV file: {str(e)}")

        return leads

    def search_snov_companies(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for companies using Snov.io API"""
        self._rate_limit()

        credentials = self._get_api_credentials()
        base_url = self.snov_config.get('base_url', 'https://api.snov.io')
        endpoint = self.snov_config.get('endpoints', {}).get('search_companies', '/v1/get-domain-search')
        url = f"{base_url}{endpoint}"
        
        # Set up parameters based on auth type
        if credentials['type'] == 'oauth':
            headers = {'Authorization': f'Bearer {credentials["token"]}'}
            params = {'domain': query, 'limit': limit}
        else:
            headers = {}
            params = {'accessToken': credentials['key'], 'domain': query, 'limit': limit}

        try:
            print(f"🔍 Searching Snov.io for: {query}")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'success' in data and not data['success']:
                raise Exception(f"Snov.io API error: {data.get('message', 'Unknown error')}")
            
            return data.get('data', [])
        except requests.exceptions.Timeout:
            raise Exception("Snov.io API timeout - please try again")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling Snov.io API: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error with Snov.io API: {str(e)}")

    def get_snov_company_info(self, company_id: str) -> Dict:
        """Get detailed company information from Snov.io"""
        self._rate_limit()

        credentials = self._get_api_credentials()
        base_url = self.snov_config.get('base_url', 'https://api.snov.io')
        endpoint = self.snov_config.get('endpoints', {}).get('get_company_info', '/v1/get-company-info')
        url = f"{base_url}{endpoint}"
        
        # Set up parameters based on auth type
        if credentials['type'] == 'oauth':
            headers = {'Authorization': f'Bearer {credentials["token"]}'}
            params = {'id': company_id}
        else:
            headers = {}
            params = {'accessToken': credentials['key'], 'id': company_id}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('data', {})
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling Snov.io API: {str(e)}")

    def get_snov_emails(self, first_name: str, last_name: str, domain: str) -> List[str]:
        """Get email addresses for a person using Snov.io"""
        self._rate_limit()

        credentials = self._get_api_credentials()
        base_url = self.snov_config.get('base_url', 'https://api.snov.io')
        endpoint = self.snov_config.get('endpoints', {}).get('get_emails', '/v1/get-emails-from-names')
        url = f"{base_url}{endpoint}"
        
        # Set up parameters based on auth type
        if credentials['type'] == 'oauth':
            headers = {'Authorization': f'Bearer {credentials["token"]}'}
            params = {'firstName': first_name, 'lastName': last_name, 'domain': domain}
        else:
            headers = {}
            params = {'accessToken': credentials['key'], 'firstName': first_name, 'lastName': last_name, 'domain': domain}

        try:
            print(f"🔍 Finding emails for: {first_name} {last_name} @ {domain}")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'success' in data and not data['success']:
                print(f"⚠️  Snov.io API warning: {data.get('message', 'Unknown error')}")
                return []
            
            emails = []
            for email_data in data.get('data', []):
                if email_data.get('email'):
                    emails.append(email_data['email'])
            
            print(f"✅ Found {len(emails)} emails")
            return emails
        except requests.exceptions.Timeout:
            print("⚠️  Snov.io API timeout for email search")
            return []
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Error calling Snov.io API: {str(e)}")
            return []
        except Exception as e:
            print(f"⚠️  Unexpected error with Snov.io API: {str(e)}")
            return []

    def enrich_lead_with_snov(self, lead: Lead) -> Lead:
        """Enrich lead data using Snov.io API"""
        try:
            # Search for company
            companies = self.search_snov_companies(lead.company_name, limit=1)
            if companies:
                company_info = self.get_snov_company_info(companies[0]['id'])

                # Update lead with enriched data
                if not lead.website and company_info.get('website'):
                    lead.website = company_info['website']
                if not lead.company_size and company_info.get('size'):
                    lead.company_size = company_info['size']
                if not lead.location and company_info.get('location'):
                    lead.location = company_info['location']

                # Try to get email if not provided
                if not lead.email and lead.website:
                    domain = lead.website.replace('https://', '').replace('http://', '').split('/')[0]
                    emails = self.get_snov_emails(lead.first_name, lead.last_name, domain)
                    if emails:
                        lead.email = emails[0]

        except Exception as e:
            print(f"Warning: Could not enrich lead {lead.first_name} {lead.last_name}: {str(e)}")

        return lead

    def verify_snov_connection(self) -> bool:
        """Verify Snov.io API connection and credentials"""
        try:
            credentials = self._get_api_credentials()
            base_url = self.snov_config.get('base_url', 'https://api.snov.io')
            url = f"{base_url}/v1/get-balance"
            
            # Set up parameters based on auth type
            if credentials['type'] == 'oauth':
                headers = {'Authorization': f'Bearer {credentials["token"]}'}
                params = {}
                print("🔍 Verifying Snov.io API connection (OAuth)...")
            else:
                headers = {}
                params = {'accessToken': credentials['key']}
                print("🔍 Verifying Snov.io API connection (API Key)...")
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'success' in data and not data['success']:
                print(f"❌ Snov.io API error: {data.get('message', 'Unknown error')}")
                return False
            
            print("✅ Snov.io API connection verified successfully")
            if 'data' in data:
                balance = data['data'].get('balance', 'Unknown')
                print(f"📊 Account balance: {balance}")
            
            return True
        except Exception as e:
            print(f"❌ Failed to verify Snov.io connection: {str(e)}")
            return False

    def save_leads_to_csv(self, leads: List[Lead], file_path: str):
        """Save leads to CSV file"""
        fieldnames = [
            'first_name', 'last_name', 'email', 'company_name', 'position',
            'industry', 'linkedin_url', 'phone', 'website', 'company_size',
            'location', 'notes'
        ]

        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            for lead in leads:
                writer.writerow({
                    'first_name': lead.first_name,
                    'last_name': lead.last_name,
                    'email': lead.email,
                    'company_name': lead.company_name,
                    'position': lead.position,
                    'industry': lead.industry,
                    'linkedin_url': lead.linkedin_url,
                    'phone': lead.phone,
                    'website': lead.website,
                    'company_size': lead.company_size,
                    'location': lead.location,
                    'notes': lead.notes
                })
