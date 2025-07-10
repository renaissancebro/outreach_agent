"""
Lead Collection Tools Module

This module provides intelligent lead collection tools that can be used by the outreach agent
to gather leads from various sources. The agent can reason about which tool to use based on
the requirements and available data.

Tools Available:
1. PlaywrightScraper - For web scraping LinkedIn profiles, company websites, directories
2. SerpAPICollector - For search-based lead collection using Google search
3. SalesNavProcessor - Enhanced CSV processing for Sales Navigator exports
"""

import os
import csv
import json
import time
import asyncio
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import requests
from urllib.parse import urljoin, urlparse
import re

# Import statements for optional dependencies
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False

from lead_manager import Lead


@dataclass
class ToolCapability:
    """Represents what a tool can do"""
    name: str
    description: str
    input_types: List[str]  # e.g., ["url", "search_query", "csv_file"]
    output_format: str
    estimated_time: str
    cost_level: str  # "free", "low", "medium", "high"
    accuracy_level: str  # "low", "medium", "high"
    requirements: List[str]  # Dependencies needed


class LeadCollectionAgent:
    """
    Intelligent agent that can reason about which tool to use for lead collection
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.tools = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all available tools"""
        # Initialize Playwright scraper
        if PLAYWRIGHT_AVAILABLE:
            self.tools['playwright'] = PlaywrightScraper(self.config)
        
        # Initialize SerpAPI collector
        if SERPAPI_AVAILABLE and os.getenv('SERPAPI_KEY'):
            self.tools['serpapi'] = SerpAPICollector(self.config)
        
        # Initialize Sales Navigator processor (always available)
        self.tools['sales_nav'] = SalesNavProcessor(self.config)
    
    def get_tool_capabilities(self) -> List[ToolCapability]:
        """Get capabilities of all available tools"""
        capabilities = []
        
        if 'playwright' in self.tools:
            capabilities.append(ToolCapability(
                name="Playwright Web Scraper",
                description="Scrapes LinkedIn profiles, company websites, and directories",
                input_types=["linkedin_url", "company_url", "directory_url"],
                output_format="Lead objects with enriched data",
                estimated_time="2-5 seconds per profile",
                cost_level="free",
                accuracy_level="high",
                requirements=["playwright", "browser_installation"]
            ))
        
        if 'serpapi' in self.tools:
            capabilities.append(ToolCapability(
                name="SerpAPI Search Collector",
                description="Collects leads through Google search results",
                input_types=["search_query", "company_name", "industry_keywords"],
                output_format="Lead objects from search results",
                estimated_time="1-2 seconds per search",
                cost_level="low",
                accuracy_level="medium",
                requirements=["serpapi_key"]
            ))
        
        if 'sales_nav' in self.tools:
            capabilities.append(ToolCapability(
                name="Sales Navigator CSV Processor",
                description="Enhanced processing of Sales Navigator exports",
                input_types=["csv_file", "sales_nav_export"],
                output_format="Enriched Lead objects",
                estimated_time="Instant processing",
                cost_level="free",
                accuracy_level="high",
                requirements=["sales_navigator_access"]
            ))
        
        return capabilities
    
    def recommend_tool(self, request: Dict) -> Dict:
        """
        Intelligently recommend which tool to use based on the request
        
        Args:
            request: Dict containing:
                - task_type: "profile_scraping", "company_research", "bulk_collection", etc.
                - input_data: The data available (URLs, search terms, CSV files)
                - constraints: Time, cost, accuracy requirements
                - output_requirements: What format/details needed
        
        Returns:
            Dict with recommended tool and reasoning
        """
        task_type = request.get('task_type', '')
        input_data = request.get('input_data', {})
        constraints = request.get('constraints', {})
        
        recommendations = []
        
        # Analyze input data type
        if 'linkedin_urls' in input_data or 'company_urls' in input_data:
            if 'playwright' in self.tools:
                recommendations.append({
                    'tool': 'playwright',
                    'confidence': 0.9,
                    'reasoning': 'Direct URL access provides highest accuracy for profile/company data'
                })
        
        if 'search_queries' in input_data or 'company_names' in input_data:
            if 'serpapi' in self.tools:
                recommendations.append({
                    'tool': 'serpapi',
                    'confidence': 0.7,
                    'reasoning': 'Search-based collection good for discovering new prospects'
                })
        
        if 'csv_file' in input_data and 'sales_nav' in input_data.get('source', ''):
            if 'sales_nav' in self.tools:
                recommendations.append({
                    'tool': 'sales_nav',
                    'confidence': 0.95,
                    'reasoning': 'Optimized for Sales Navigator exports with enhanced data processing'
                })
        
        # Apply constraints
        if constraints.get('budget') == 'free' and recommendations:
            recommendations = [r for r in recommendations if r['tool'] != 'serpapi']
        
        if constraints.get('speed') == 'fast' and recommendations:
            # Prioritize tools with faster processing
            for r in recommendations:
                if r['tool'] == 'sales_nav':
                    r['confidence'] += 0.1
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        if recommendations:
            return {
                'recommended_tool': recommendations[0]['tool'],
                'confidence': recommendations[0]['confidence'],
                'reasoning': recommendations[0]['reasoning'],
                'alternatives': recommendations[1:] if len(recommendations) > 1 else []
            }
        else:
            return {
                'recommended_tool': None,
                'confidence': 0,
                'reasoning': 'No suitable tools available for this request',
                'alternatives': []
            }
    
    async def collect_leads(self, tool_name: str, parameters: Dict) -> List[Lead]:
        """
        Collect leads using the specified tool
        
        Args:
            tool_name: Name of the tool to use
            parameters: Tool-specific parameters
            
        Returns:
            List of Lead objects
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not available")
        
        tool = self.tools[tool_name]
        
        if tool_name == 'playwright':
            return await tool.scrape_leads(parameters)
        elif tool_name == 'serpapi':
            return await tool.search_leads(parameters)
        elif tool_name == 'sales_nav':
            return tool.process_sales_nav_csv(parameters)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")


class PlaywrightScraper:
    """
    Playwright-based web scraper for LinkedIn profiles and company websites
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.scraper_config = config.get('lead_collection_tools', {}).get('playwright', {})
        self.rate_limit = self.scraper_config.get('rate_limit_seconds', 2)
        self.timeout = self.scraper_config.get('timeout_seconds', 30)
        self.max_retries = self.scraper_config.get('max_retries', 3)
    
    async def scrape_leads(self, parameters: Dict) -> List[Lead]:
        """
        Scrape leads from various sources
        
        Args:
            parameters: Dict containing:
                - urls: List of URLs to scrape
                - source_type: "linkedin", "company_website", "directory"
                - max_leads: Maximum number of leads to collect
        
        Returns:
            List of Lead objects
        """
        urls = parameters.get('urls', [])
        source_type = parameters.get('source_type', 'linkedin')
        max_leads = parameters.get('max_leads', 100)
        
        leads = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set user agent to avoid detection
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            for i, url in enumerate(urls[:max_leads]):
                if i > 0:
                    await asyncio.sleep(self.rate_limit)
                
                try:
                    print(f"🔍 Scraping: {url}")
                    
                    if source_type == 'linkedin':
                        lead = await self._scrape_linkedin_profile(page, url)
                    elif source_type == 'company_website':
                        lead = await self._scrape_company_website(page, url)
                    elif source_type == 'directory':
                        lead = await self._scrape_directory_listing(page, url)
                    else:
                        print(f"⚠️ Unknown source type: {source_type}")
                        continue
                    
                    if lead:
                        leads.append(lead)
                        print(f"✅ Collected: {lead.first_name} {lead.last_name} at {lead.company_name}")
                    
                except Exception as e:
                    print(f"❌ Error scraping {url}: {str(e)}")
                    continue
            
            await browser.close()
        
        return leads
    
    async def _scrape_linkedin_profile(self, page: Page, url: str) -> Optional[Lead]:
        """Scrape a LinkedIn profile"""
        try:
            await page.goto(url, timeout=self.timeout * 1000)
            await page.wait_for_load_state('networkidle')
            
            # Extract profile information
            name_element = await page.query_selector('h1.text-heading-xlarge')
            name = await name_element.inner_text() if name_element else ""
            
            # Split name into first and last
            name_parts = name.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            # Extract current position and company
            position_element = await page.query_selector('.text-body-medium.break-words')
            position = await position_element.inner_text() if position_element else ""
            
            # Extract company from position text
            company_name = ""
            if " at " in position:
                company_name = position.split(" at ")[-1].strip()
            
            # Extract location
            location_element = await page.query_selector('.text-body-small.inline.t-black--light.break-words')
            location = await location_element.inner_text() if location_element else ""
            
            # Extract industry (if available)
            industry = ""
            
            # Create lead object
            lead = Lead(
                first_name=first_name,
                last_name=last_name,
                email="",  # Email not available from LinkedIn public profiles
                company_name=company_name,
                position=position,
                industry=industry,
                linkedin_url=url,
                location=location
            )
            
            return lead
            
        except Exception as e:
            print(f"Error scraping LinkedIn profile: {str(e)}")
            return None
    
    async def _scrape_company_website(self, page: Page, url: str) -> Optional[Lead]:
        """Scrape company website for contact information"""
        try:
            await page.goto(url, timeout=self.timeout * 1000)
            await page.wait_for_load_state('networkidle')
            
            # Look for contact/about pages
            contact_links = await page.query_selector_all('a[href*="contact"], a[href*="about"], a[href*="team"]')
            
            leads = []
            for link in contact_links[:3]:  # Check first 3 relevant pages
                href = await link.get_attribute('href')
                if href:
                    contact_url = urljoin(url, href)
                    await page.goto(contact_url)
                    
                    # Extract email addresses
                    emails = await self._extract_emails_from_page(page)
                    
                    # Extract names (basic extraction)
                    names = await self._extract_names_from_page(page)
                    
                    # Combine emails and names
                    for email in emails:
                        # Try to match with names or create basic lead
                        lead = Lead(
                            first_name="",
                            last_name="",
                            email=email,
                            company_name=urlparse(url).netloc.replace('www.', ''),
                            position="",
                            industry="",
                            website=url
                        )
                        leads.append(lead)
            
            return leads[0] if leads else None
            
        except Exception as e:
            print(f"Error scraping company website: {str(e)}")
            return None
    
    async def _scrape_directory_listing(self, page: Page, url: str) -> Optional[Lead]:
        """Scrape directory listing for business information"""
        try:
            await page.goto(url, timeout=self.timeout * 1000)
            await page.wait_for_load_state('networkidle')
            
            # Generic directory scraping logic
            # This would need to be customized for specific directories
            
            return None
            
        except Exception as e:
            print(f"Error scraping directory: {str(e)}")
            return None
    
    async def _extract_emails_from_page(self, page: Page) -> List[str]:
        """Extract email addresses from page content"""
        content = await page.content()
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        return list(set(emails))  # Remove duplicates
    
    async def _extract_names_from_page(self, page: Page) -> List[str]:
        """Extract potential names from page content"""
        # This is a basic implementation - could be enhanced with NLP
        names = []
        # Look for common name patterns in headings, etc.
        return names


class SerpAPICollector:
    """
    SerpAPI-based lead collector using Google search results
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.serpapi_config = config.get('lead_collection_tools', {}).get('serpapi', {})
        self.api_key = os.getenv('SERPAPI_KEY')
        self.rate_limit = self.serpapi_config.get('rate_limit_seconds', 1)
    
    async def search_leads(self, parameters: Dict) -> List[Lead]:
        """
        Search for leads using SerpAPI
        
        Args:
            parameters: Dict containing:
                - queries: List of search queries
                - max_results: Maximum results per query
                - filters: Additional search filters
        
        Returns:
            List of Lead objects
        """
        queries = parameters.get('queries', [])
        max_results = parameters.get('max_results', 10)
        filters = parameters.get('filters', {})
        
        leads = []
        
        for query in queries:
            try:
                print(f"🔍 Searching: {query}")
                
                # Construct search parameters
                search_params = {
                    "q": query,
                    "api_key": self.api_key,
                    "num": max_results,
                    "engine": "google"
                }
                
                # Add filters
                if filters.get('location'):
                    search_params['location'] = filters['location']
                if filters.get('date_range'):
                    search_params['tbs'] = filters['date_range']
                
                # Perform search
                search = GoogleSearch(search_params)
                results = search.get_dict()
                
                # Extract leads from results
                query_leads = self._extract_leads_from_search_results(results, query)
                leads.extend(query_leads)
                
                print(f"✅ Found {len(query_leads)} leads for query: {query}")
                
                # Rate limiting
                if len(queries) > 1:
                    await asyncio.sleep(self.rate_limit)
                
            except Exception as e:
                print(f"❌ Error searching '{query}': {str(e)}")
                continue
        
        return leads
    
    def _extract_leads_from_search_results(self, results: Dict, query: str) -> List[Lead]:
        """Extract lead information from search results"""
        leads = []
        
        organic_results = results.get('organic_results', [])
        
        for result in organic_results:
            try:
                title = result.get('title', '')
                link = result.get('link', '')
                snippet = result.get('snippet', '')
                
                # Extract potential lead information
                lead = self._create_lead_from_search_result(title, link, snippet, query)
                if lead:
                    leads.append(lead)
                    
            except Exception as e:
                print(f"Error processing search result: {str(e)}")
                continue
        
        return leads
    
    def _create_lead_from_search_result(self, title: str, link: str, snippet: str, query: str) -> Optional[Lead]:
        """Create a lead from search result data"""
        try:
            # Extract company name from title or URL
            company_name = ""
            if " | " in title:
                company_name = title.split(" | ")[-1].strip()
            elif " - " in title:
                company_name = title.split(" - ")[-1].strip()
            else:
                # Try to extract from URL
                domain = urlparse(link).netloc.replace('www.', '')
                company_name = domain.split('.')[0].title()
            
            # Extract potential name from title
            name_parts = title.split()
            first_name = ""
            last_name = ""
            
            # Basic name extraction (this could be improved)
            for i, part in enumerate(name_parts):
                if part.istitle() and len(part) > 2:
                    if not first_name:
                        first_name = part
                    elif not last_name:
                        last_name = part
                        break
            
            # Create lead
            lead = Lead(
                first_name=first_name,
                last_name=last_name,
                email="",  # Email not available from search results
                company_name=company_name,
                position="",
                industry="",
                website=link,
                notes=f"Found via search: {query}"
            )
            
            return lead
            
        except Exception as e:
            print(f"Error creating lead from search result: {str(e)}")
            return None


class SalesNavProcessor:
    """
    Enhanced processor for Sales Navigator CSV exports
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.processor_config = config.get('lead_collection_tools', {}).get('sales_nav', {})
    
    def process_sales_nav_csv(self, parameters: Dict) -> List[Lead]:
        """
        Process Sales Navigator CSV export with enhanced data extraction
        
        Args:
            parameters: Dict containing:
                - csv_file: Path to CSV file
                - enrich_data: Whether to enrich with additional data
                - clean_data: Whether to clean and normalize data
        
        Returns:
            List of Lead objects
        """
        csv_file = parameters.get('csv_file', '')
        enrich_data = parameters.get('enrich_data', True)
        clean_data = parameters.get('clean_data', True)
        
        if not csv_file or not os.path.exists(csv_file):
            raise ValueError(f"CSV file not found: {csv_file}")
        
        leads = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                # Try to detect if this is a Sales Navigator export
                sample = file.read(1024)
                file.seek(0)
                
                reader = csv.DictReader(file)
                
                for row in reader:
                    lead = self._process_sales_nav_row(row)
                    if lead:
                        if clean_data:
                            lead = self._clean_lead_data(lead)
                        if enrich_data:
                            lead = self._enrich_lead_data(lead)
                        leads.append(lead)
                
                print(f"✅ Processed {len(leads)} leads from Sales Navigator export")
                
        except Exception as e:
            print(f"❌ Error processing Sales Navigator CSV: {str(e)}")
            raise
        
        return leads
    
    def _process_sales_nav_row(self, row: Dict) -> Optional[Lead]:
        """Process a single row from Sales Navigator export"""
        try:
            # Map Sales Navigator columns to Lead fields
            # Sales Navigator exports can have different column names
            column_mapping = {
                'First Name': 'first_name',
                'Last Name': 'last_name',
                'Email': 'email',
                'Company': 'company_name',
                'Title': 'position',
                'Industry': 'industry',
                'Location': 'location',
                'Profile URL': 'linkedin_url',
                'Company URL': 'website',
                'Phone': 'phone',
                'Company Size': 'company_size',
                
                # Alternative column names
                'First': 'first_name',
                'Last': 'last_name',
                'Email Address': 'email',
                'Company Name': 'company_name',
                'Job Title': 'position',
                'Position': 'position',
                'Current Position': 'position',
                'LinkedIn URL': 'linkedin_url',
                'LinkedIn Profile': 'linkedin_url',
                'Company Website': 'website',
                'Phone Number': 'phone',
                'Geographic Location': 'location',
            }
            
            # Extract data using flexible column mapping
            lead_data = {}
            for csv_col, csv_val in row.items():
                if csv_col in column_mapping:
                    lead_field = column_mapping[csv_col]
                    lead_data[lead_field] = str(csv_val).strip() if csv_val else ""
            
            # Create lead with available data
            lead = Lead(
                first_name=lead_data.get('first_name', ''),
                last_name=lead_data.get('last_name', ''),
                email=lead_data.get('email', ''),
                company_name=lead_data.get('company_name', ''),
                position=lead_data.get('position', ''),
                industry=lead_data.get('industry', ''),
                linkedin_url=lead_data.get('linkedin_url', ''),
                phone=lead_data.get('phone', ''),
                website=lead_data.get('website', ''),
                company_size=lead_data.get('company_size', ''),
                location=lead_data.get('location', ''),
                notes="Imported from Sales Navigator"
            )
            
            return lead
            
        except Exception as e:
            print(f"Error processing row: {str(e)}")
            return None
    
    def _clean_lead_data(self, lead: Lead) -> Lead:
        """Clean and normalize lead data"""
        # Clean company name
        if lead.company_name:
            lead.company_name = lead.company_name.strip()
            # Remove common suffixes for normalization
            suffixes = [' Inc.', ' LLC', ' Corp.', ' Corporation', ' Ltd.', ' Limited']
            for suffix in suffixes:
                if lead.company_name.endswith(suffix):
                    lead.company_name = lead.company_name[:-len(suffix)].strip()
        
        # Clean position title
        if lead.position:
            lead.position = lead.position.strip()
        
        # Clean location
        if lead.location:
            lead.location = lead.location.strip()
        
        # Validate email format
        if lead.email:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, lead.email):
                lead.email = ""  # Clear invalid email
        
        return lead
    
    def _enrich_lead_data(self, lead: Lead) -> Lead:
        """Enrich lead with additional data"""
        # Extract domain from email for website
        if lead.email and not lead.website:
            domain = lead.email.split('@')[1]
            lead.website = f"https://{domain}"
        
        # Infer industry from company name (basic rules)
        if not lead.industry and lead.company_name:
            lead.industry = self._infer_industry(lead.company_name)
        
        return lead
    
    def _infer_industry(self, company_name: str) -> str:
        """Infer industry from company name"""
        company_lower = company_name.lower()
        
        industry_keywords = {
            'technology': ['tech', 'software', 'ai', 'artificial intelligence', 'data', 'cloud'],
            'healthcare': ['health', 'medical', 'pharma', 'biotech', 'hospital'],
            'finance': ['bank', 'financial', 'investment', 'capital', 'fund'],
            'retail': ['retail', 'commerce', 'shop', 'store', 'marketplace'],
            'manufacturing': ['manufacturing', 'industrial', 'factory', 'production'],
            'consulting': ['consulting', 'advisory', 'services', 'solutions'],
            'education': ['education', 'school', 'university', 'learning'],
            'real estate': ['real estate', 'property', 'construction', 'development']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in company_lower for keyword in keywords):
                return industry.title()
        
        return ""


# Utility functions for the agent
def get_available_tools() -> List[str]:
    """Get list of available tools"""
    tools = []
    
    if PLAYWRIGHT_AVAILABLE:
        tools.append('playwright')
    
    if SERPAPI_AVAILABLE and os.getenv('SERPAPI_KEY'):
        tools.append('serpapi')
    
    tools.append('sales_nav')  # Always available
    
    return tools


def validate_tool_requirements(tool_name: str) -> Dict:
    """Validate that all requirements for a tool are met"""
    requirements = {
        'playwright': {
            'available': PLAYWRIGHT_AVAILABLE,
            'missing': [] if PLAYWRIGHT_AVAILABLE else ['playwright package']
        },
        'serpapi': {
            'available': SERPAPI_AVAILABLE and bool(os.getenv('SERPAPI_KEY')),
            'missing': []
        },
        'sales_nav': {
            'available': True,
            'missing': []
        }
    }
    
    if tool_name == 'serpapi':
        if not SERPAPI_AVAILABLE:
            requirements['serpapi']['missing'].append('serpapi package')
        if not os.getenv('SERPAPI_KEY'):
            requirements['serpapi']['missing'].append('SERPAPI_KEY environment variable')
    
    return requirements.get(tool_name, {'available': False, 'missing': ['Unknown tool']})


# Example usage and testing
if __name__ == "__main__":
    # Example configuration
    config = {
        'lead_collection_tools': {
            'playwright': {
                'rate_limit_seconds': 2,
                'timeout_seconds': 30,
                'max_retries': 3
            },
            'serpapi': {
                'rate_limit_seconds': 1
            },
            'sales_nav': {
                'enable_enrichment': True
            }
        }
    }
    
    # Initialize agent
    agent = LeadCollectionAgent(config)
    
    # Get capabilities
    capabilities = agent.get_tool_capabilities()
    print("Available tools:")
    for cap in capabilities:
        print(f"- {cap.name}: {cap.description}")
    
    # Example recommendation
    request = {
        'task_type': 'profile_scraping',
        'input_data': {
            'linkedin_urls': ['https://linkedin.com/in/example'],
            'company_names': ['TechCorp']
        },
        'constraints': {
            'budget': 'free',
            'speed': 'medium'
        }
    }
    
    recommendation = agent.recommend_tool(request)
    print(f"\nRecommendation: {recommendation}")