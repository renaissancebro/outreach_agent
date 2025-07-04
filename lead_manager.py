import csv
import json
import time
import requests
from typing import List, Dict, Optional
import os
from dataclasses import dataclass
from datetime import datetime


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

    def _rate_limit(self):
        """Implement rate limiting for API calls"""
        if self.rate_limits.get('snov_api_calls_per_minute'):
            min_interval = 60 / self.rate_limits['snov_api_calls_per_minute']
            time_since_last = time.time() - self.last_api_call
            if time_since_last < min_interval:
                time.sleep(min_interval - time_since_last)
        self.last_api_call = time.time()

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

        api_key = os.getenv('SNOV_API_KEY') or self.snov_config.get('api_key', '').replace('${SNOV_API_KEY}', '')
        if not api_key:
            raise ValueError("SNOV_API_KEY not found in environment variables")

        url = f"{self.snov_config['base_url']}{self.snov_config['endpoints']['search_companies']}"
        params = {
            'accessToken': api_key,
            'search': query,
            'limit': limit
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling Snov.io API: {str(e)}")

    def get_snov_company_info(self, company_id: str) -> Dict:
        """Get detailed company information from Snov.io"""
        self._rate_limit()

        api_key = os.getenv('SNOV_API_KEY') or self.snov_config.get('api_key', '').replace('${SNOV_API_KEY}', '')
        if not api_key:
            raise ValueError("SNOV_API_KEY not found in environment variables")

        url = f"{self.snov_config['base_url']}{self.snov_config['endpoints']['get_company_info']}"
        params = {
            'accessToken': api_key,
            'id': company_id
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('data', {})
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling Snov.io API: {str(e)}")

    def get_snov_emails(self, first_name: str, last_name: str, domain: str) -> List[str]:
        """Get email addresses for a person using Snov.io"""
        self._rate_limit()

        api_key = os.getenv('SNOV_API_KEY') or self.snov_config.get('api_key', '').replace('${SNOV_API_KEY}', '')
        if not api_key:
            raise ValueError("SNOV_API_KEY not found in environment variables")

        url = f"{self.snov_config['base_url']}{self.snov_config['endpoints']['get_emails']}"
        params = {
            'accessToken': api_key,
            'firstName': first_name,
            'lastName': last_name,
            'domain': domain
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            emails = []
            for email_data in data.get('data', []):
                if email_data.get('email'):
                    emails.append(email_data['email'])
            return emails
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling Snov.io API: {str(e)}")

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
