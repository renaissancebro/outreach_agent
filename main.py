import os
import yaml
import argparse
import csv
import json
from typing import List, Dict
from datetime import datetime
from crewai import Agent, Task, Crew
from dotenv import load_dotenv
from lead_manager import LeadManager, Lead
from email_generator import EmailGenerator
from lead_collection_tools import LeadCollectionAgent
from crm_system import CRMSystem, LeadStatus, InteractionType
from flask import Flask, request, jsonify
from auth_middleware import (
    require_ai_research, require_crm_dashboard, require_snov_io, 
    require_sheets_sync, require_serpapi, show_license_info,
    set_license_key, remove_license_key
)

# Load environment variables
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


class EnhancedOutreachAgent:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the enhanced outreach agent with configuration"""
        self.config = self._load_config(config_path)
        self.lead_manager = LeadManager(self.config)
        self.email_generator = EmailGenerator(self.config)
        self.lead_collection_agent = LeadCollectionAgent(self.config)
        self.crm = CRMSystem(self.config)
        self.crew = self._setup_crew()
        self.campaign_log = []

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration: {e}")

    def _setup_crew(self) -> Crew:
        """Setup CrewAI agents and tasks"""
        agent_config = self.config.get('agent', {})

        # Research Agent for company/industry insights
        research_agent = Agent(
            role="Market Research Specialist",
            goal="Research companies and industries to provide context for personalized outreach",
            backstory="You are an expert at gathering and analyzing company information, industry trends, and market insights to help create highly targeted outreach campaigns.",
            verbose=agent_config.get('verbose', True),
            allow_delegation=False
        )

        # Outreach Agent for email generation
        outreach_agent = Agent(
            role=agent_config.get('role', 'Outreach Specialist'),
            goal=agent_config.get('goal', 'Write personalized cold outreach emails'),
            backstory=agent_config.get('backstory', 'You are a skilled marketing agent who crafts targeted, warm messages that actually get responses.'),
            verbose=agent_config.get('verbose', True),
            allow_delegation=False
        )

        # Research Task
        research_task = Task(
            description=(
                "Research the provided company and contact information to identify market intelligence opportunities. "
                "Focus on: recent industry developments, compliance changes, competitor activities, policy shifts, and emerging trends. "
                "Identify specific areas where AlphaRed's AI agents could surface critical intelligence before competitors notice. "
                "Return structured data including market gaps, intelligence opportunities, company context, and competitive landscape."
            ),
            expected_output="JSON object with research findings including market_gaps, intelligence_opportunities, company_research, and competitive_landscape",
            agent=research_agent
        )

        # Outreach Task
        outreach_task = Task(
            description=(
                "Using the research provided and lead information, create a compelling outreach email that positions AlphaRed as the solution for staying ahead of market changes. "
                "Emphasize speed, clarity, and competitive advantage through early intelligence. "
                "Highlight how AlphaRed's AI agents can surface niche market intelligence (compliance changes, competitor moves, policy shifts) before others notice. "
                "Include a compelling subject line and 2-3 paragraph message that conveys urgency and strategic value."
            ),
            expected_output="Complete email with subject line and personalized body content focused on AlphaRed's market intelligence capabilities",
            agent=outreach_agent,
            context=[research_task]
        )

        return Crew(
            agents=[research_agent, outreach_agent],
            tasks=[research_task, outreach_task],
            verbose=agent_config.get('verbose', True)
        )

    def process_csv_leads(self, csv_path: str = None, enrich_with_snov: bool = False) -> List[Lead]:
        """Process leads from CSV file"""
        print(f"\n📊 Loading leads from CSV: {csv_path or 'leads.csv'}")
        print(f"🔧 Enrich with Snov.io: {enrich_with_snov}")

        try:
            leads = self.lead_manager.load_csv_leads(csv_path)
            print(f"✅ Successfully loaded {len(leads)} leads from CSV")

            # Print first few leads as preview
            if leads:
                print(f"📋 Sample leads:")
                for i, lead in enumerate(leads[:3]):
                    print(f"   {i+1}. {lead.first_name} {lead.last_name} - {lead.position} at {lead.company_name}")
                if len(leads) > 3:
                    print(f"   ... and {len(leads) - 3} more leads")

        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return []

        if enrich_with_snov:
            print(f"\n🔍 Enriching leads with Snov.io data...")
            print(f"⚠️  Note: Snov.io integration requires API credentials")
            enriched_leads = []
            for i, lead in enumerate(leads):
                print(f"   [{i+1}/{len(leads)}] Enriching: {lead.first_name} {lead.last_name}")
                try:
                    enriched_lead = self.lead_manager.enrich_lead_with_snov(lead)
                    enriched_leads.append(enriched_lead)
                    print(f"   ✅ Enrichment completed")
                except Exception as e:
                    print(f"   ⚠️  Enrichment failed: {e}")
                    enriched_leads.append(lead)  # Keep original lead
            leads = enriched_leads
            print(f"✅ Lead enrichment completed")

        return leads

    def search_snov_leads(self, company_query: str, limit: int = 10) -> List[Dict]:
        """Search for leads using Snov.io API"""
        print(f"🔍 Searching Snov.io for companies: {company_query}")
        companies = self.lead_manager.search_snov_companies(company_query, limit)
        print(f"✅ Found {len(companies)} companies")
        return companies
    
    def collect_leads_intelligently(self, request_params: Dict) -> List[Lead]:
        """
        Intelligently collect leads using the best available tool
        
        Args:
            request_params: Dict containing:
                - task_type: Type of lead collection task
                - input_data: Available input data (URLs, queries, files)
                - constraints: Budget, time, accuracy requirements
                - max_leads: Maximum number of leads to collect
        
        Returns:
            List of Lead objects
        """
        print(f"\n🤖 INTELLIGENT LEAD COLLECTION")
        print(f"{'='*50}")
        
        # Get tool recommendation from the agent
        recommendation = self.lead_collection_agent.recommend_tool(request_params)
        
        print(f"🎯 Recommended Tool: {recommendation['recommended_tool']}")
        print(f"🔍 Confidence: {recommendation['confidence']:.2f}")
        print(f"💭 Reasoning: {recommendation['reasoning']}")
        
        if recommendation['alternatives']:
            print(f"🔄 Alternatives: {[alt['tool'] for alt in recommendation['alternatives']]}")
        
        recommended_tool = recommendation['recommended_tool']
        
        if not recommended_tool:
            print(f"❌ No suitable tool available for this request")
            return []
        
        # Extract parameters for the chosen tool
        tool_params = self._prepare_tool_parameters(recommended_tool, request_params)
        
        # Collect leads using the recommended tool
        print(f"\n🔧 Collecting leads using {recommended_tool}...")
        try:
            import asyncio
            leads = asyncio.run(self.lead_collection_agent.collect_leads(recommended_tool, tool_params))
            print(f"✅ Successfully collected {len(leads)} leads using {recommended_tool}")
            return leads
        except Exception as e:
            print(f"❌ Error collecting leads with {recommended_tool}: {str(e)}")
            
            # Try alternative tools if available
            if recommendation['alternatives']:
                print(f"🔄 Trying alternative tools...")
                for alt in recommendation['alternatives']:
                    try:
                        alt_params = self._prepare_tool_parameters(alt['tool'], request_params)
                        leads = asyncio.run(self.lead_collection_agent.collect_leads(alt['tool'], alt_params))
                        print(f"✅ Successfully collected {len(leads)} leads using {alt['tool']}")
                        return leads
                    except Exception as e2:
                        print(f"❌ Alternative {alt['tool']} also failed: {str(e2)}")
                        continue
            
            return []
    
    def _prepare_tool_parameters(self, tool_name: str, request_params: Dict) -> Dict:
        """Prepare parameters for the specific tool"""
        input_data = request_params.get('input_data', {})
        max_leads = request_params.get('max_leads', 50)
        
        if tool_name == 'playwright':
            return {
                'urls': input_data.get('linkedin_urls', []) + input_data.get('company_urls', []),
                'source_type': 'linkedin' if input_data.get('linkedin_urls') else 'company_website',
                'max_leads': max_leads
            }
        elif tool_name == 'serpapi':
            return {
                'queries': input_data.get('search_queries', []) + input_data.get('company_names', []),
                'max_results': min(max_leads, 10),  # SerpAPI typically returns 10 results per query
                'filters': input_data.get('filters', {})
            }
        elif tool_name == 'sales_nav':
            return {
                'csv_file': input_data.get('csv_file', ''),
                'enrich_data': input_data.get('enrich_data', True),
                'clean_data': input_data.get('clean_data', True)
            }
        else:
            return {}
    
    def get_tool_capabilities(self):
        """Get capabilities of all available lead collection tools"""
        capabilities = self.lead_collection_agent.get_tool_capabilities()
        
        print(f"\n🛠️  AVAILABLE LEAD COLLECTION TOOLS")
        print(f"{'='*50}")
        
        for i, cap in enumerate(capabilities, 1):
            print(f"{i}. {cap.name}")
            print(f"   📝 Description: {cap.description}")
            print(f"   📥 Input Types: {', '.join(cap.input_types)}")
            print(f"   ⏱️  Time: {cap.estimated_time}")
            print(f"   💰 Cost: {cap.cost_level}")
            print(f"   🎯 Accuracy: {cap.accuracy_level}")
            print(f"   📋 Requirements: {', '.join(cap.requirements)}")
            print()
        
        return capabilities
    
    def import_leads_to_crm(self, leads: List[Lead], source: str = "lead_collection") -> List:
        """Import leads to CRM system"""
        print(f"\n📋 IMPORTING LEADS TO CRM")
        print(f"{'='*50}")
        
        contacts = self.crm.batch_import_leads(leads, source)
        
        print(f"✅ Imported {len(contacts)} leads to CRM")
        return contacts
    
    @require_crm_dashboard
    def get_crm_dashboard(self) -> Dict:
        """Get CRM dashboard statistics"""
        return self.crm.get_dashboard_stats()
    
    def update_contact_status(self, email: str, status: str, notes: str = None) -> bool:
        """Update contact status in CRM"""
        contact = self.crm.db.get_contact_by_email(email)
        if not contact:
            print(f"❌ Contact not found: {email}")
            return False
        
        try:
            status_enum = LeadStatus(status)
            return self.crm.update_contact_status(contact.id, status_enum, notes)
        except ValueError:
            print(f"❌ Invalid status: {status}")
            return False
    
    def search_crm_contacts(self, query: str = None, status: str = None) -> List:
        """Search CRM contacts"""
        status_enum = None
        if status:
            try:
                status_enum = LeadStatus(status)
            except ValueError:
                print(f"❌ Invalid status: {status}")
                return []
        
        contacts = self.crm.db.search_contacts(query=query, status=status_enum)
        return contacts
    
    def export_crm_data(self, format: str = "csv", filename: str = None) -> str:
        """Export CRM data"""
        if format == "csv":
            return self.crm.export_to_csv(filename)
        else:
            print(f"❌ Unsupported export format: {format}")
            return None
    
    @require_sheets_sync
    def sync_crm_to_google_sheets(self, sheet_id: str, worksheet_name: str = "CRM Data") -> bool:
        """Sync CRM data to Google Sheets"""
        return self.crm.sync_to_google_sheets(sheet_id, worksheet_name)
    
    @require_sheets_sync
    def import_crm_from_google_sheets(self, sheet_id: str, worksheet_name: str = "CRM Data") -> List:
        """Import CRM data from Google Sheets"""
        return self.crm.import_from_google_sheets(sheet_id, worksheet_name)

    def generate_emails_for_leads(self, leads: List[Lead], use_ai_research: bool = True) -> List[Dict]:
        """Generate personalized emails for a list of leads"""
        print(f"\n🔧 Starting email generation for {len(leads)} leads...")
        print(f"🔧 AI Research enabled: {use_ai_research}")

        # Check AI research access if requested
        if use_ai_research:
            from auth_middleware import require_license
            auth_check = require_license("ai_research", allow_prompt=True)
            test_func = lambda: True
            result = auth_check(test_func)()
            if result is None:
                print("🔄 Falling back to template-based generation...")
                use_ai_research = False

        emails = []

        for i, lead in enumerate(leads):
            print(f"\n📧 [{i+1}/{len(leads)}] Processing: {lead.first_name} {lead.last_name} at {lead.company_name}")
            print(f"   📋 Lead details: {lead.position} in {lead.industry}")
            if lead.website:
                print(f"   🌐 Website: {lead.website}")
            if lead.location:
                print(f"   📍 Location: {lead.location}")

            context = {}

            if use_ai_research:
                print(f"   🤖 Starting AI research for {lead.company_name}...")
                # Use CrewAI for research and email generation
                try:
                    # Create lead information for the crew
                    lead_info = f"""
                    Research this company and contact for personalized outreach:
                    - Company: {lead.company_name}
                    - Contact: {lead.first_name} {lead.last_name} ({lead.position})
                    - Industry: {lead.industry}
                    - Website: {lead.website or 'Not provided'}
                    - Location: {lead.location or 'Not provided'}

                    Focus on recent news, achievements, challenges, and how our AI dashboard solution could help with regulatory compliance and industry insights.
                    """

                    print(f"   🔍 Lead info prepared, running CrewAI...")

                    # Run the crew to get research and email with lead-specific inputs
                    result = self.crew.kickoff(inputs={"lead_info": lead_info})

                    print(f"   ✅ AI research completed successfully")
                    print(f"   📄 AI Result length: {len(str(result))} characters")

                    # Parse the result to extract email content
                    # This is a simplified approach - you might want to enhance the parsing
                    context = {
                        'ai_research': result,
                        'solution_benefit': 'AI-powered regulatory dashboard',
                        'pain_point': 'regulatory compliance tracking'
                    }

                except Exception as e:
                    print(f"   ⚠️  AI research failed for {lead.first_name} {lead.last_name}: {e}")
                    print(f"   🔄 Falling back to template-based generation...")
                    # Fallback to template-based generation
                    context = {
                        'solution_benefit': 'AI agents that surface critical market intelligence before competitors notice',
                        'pain_point': 'missing crucial market shifts and being blindsided by changes',
                        'emotional_hook': 'never miss a shift that could make or break your business',
                        'value_prop': 'get signal, not noise - actionable intelligence when it matters most',
                        'urgency': 'stay ahead of the curve with real-time market intelligence'
                    }
            else:
                print(f"   📝 Using template-based generation (no AI research)...")
                # Use template-based generation
                context = {
                    'solution_benefit': 'AI-powered regulatory dashboard',
                    'pain_point': 'regulatory compliance tracking'
                }

            print(f"   🎯 Context prepared: {list(context.keys())}")

            # Generate email using the email generator
            print(f"   ✍️  Generating email with EmailGenerator...")
            email_data = self.email_generator.generate_email(lead, context)

            print(f"   ✅ Email generated successfully!")
            print(f"   📧 Subject: {email_data['subject']}")
            print(f"   📝 Body length: {len(email_data['body'])} characters")

            # Import lead to CRM and log email interaction
            try:
                contact = self.crm.import_lead_to_crm(lead, "email_campaign")
                self.crm.log_email_sent(
                    contact.id,
                    email_data['subject'],
                    email_data['body']
                )
                print(f"   📋 Logged in CRM: {contact.email}")
            except Exception as e:
                print(f"   ⚠️  CRM logging failed: {str(e)}")

            # Log the email generation
            self.campaign_log.append({
                'full_name': f"{lead.first_name} {lead.last_name}",
                'company': lead.company_name,
                'method': 'AI Research' if use_ai_research else 'Template',
                'timestamp': datetime.now().isoformat()
            })

            emails.append(email_data)

            # Rate limiting delay
            delay = self.config.get('rate_limits', {}).get('delay_between_emails', 2)
            if delay > 0 and i < len(leads) - 1:
                print(f"   ⏳ Waiting {delay} seconds before next email...")
                import time
                time.sleep(delay)

        print(f"\n🎉 Email generation completed! Generated {len(emails)} emails.")
        return emails

    def save_results(self, emails: List[Dict], leads: List[Lead] = None):
        """Save generated emails and optionally enriched leads"""
        print(f"\n💾 Saving results...")
        print(f"📧 Emails to save: {len(emails)}")
        print(f"👥 Leads to save: {len(leads) if leads else 0}")

        # Save emails
        if self.config.get('output', {}).get('save_to_file', True):
            print(f"📁 Saving emails to file...")
            try:
                output_path = self.email_generator.save_emails(emails)
                print(f"✅ Emails saved successfully to: {output_path}")
            except Exception as e:
                print(f"❌ Error saving emails: {e}")

        # Save enriched leads if provided
        if leads and self.config.get('output', {}).get('save_enriched_leads', False):
            print(f"📁 Saving enriched leads to CSV...")
            try:
                enriched_path = f"enriched_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                self.lead_manager.save_leads_to_csv(leads, enriched_path)
                print(f"✅ Enriched leads saved to: {enriched_path}")
            except Exception as e:
                print(f"❌ Error saving enriched leads: {e}")

        print(f"💾 Save operations completed!")

        # Save campaign log
        self._save_campaign_log()

    def run_csv_campaign(self, csv_path: str = None, enrich_with_snov: bool = False, use_ai_research: bool = True):
        """Run a complete outreach campaign using CSV leads"""
        start_time = datetime.now()

        print(f"\n{'='*60}")
        print(f"🚀 STARTING CSV-BASED OUTREACH CAMPAIGN")
        print(f"{'='*60}")
        print(f"📁 CSV Path: {csv_path or 'leads.csv'}")
        print(f"🔍 Enrich with Snov.io: {enrich_with_snov}")
        print(f"🤖 AI Research: {use_ai_research}")
        print(f"⏰ Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        # Load and optionally enrich leads
        print(f"\n📊 STEP 1: Loading and processing leads...")
        leads = self.process_csv_leads(csv_path, enrich_with_snov)

        if not leads:
            print(f"❌ No leads loaded. Campaign aborted.")
            return []

        # Generate emails
        print(f"\n📧 STEP 2: Generating personalized emails...")
        emails = self.generate_emails_for_leads(leads, use_ai_research)

        # Save results
        print(f"\n💾 STEP 3: Saving campaign results...")
        self.save_results(emails, leads if enrich_with_snov else None)

        # Calculate metrics
        end_time = datetime.now()
        duration = end_time - start_time
        fallback_count = sum(1 for log in self.campaign_log[-len(leads):] if log['method'] == 'Template')
        ai_count = sum(1 for log in self.campaign_log[-len(leads):] if log['method'] == 'AI Research')

        # Print summary block
        print(f"\n{'='*60}")
        print(f"🎉 CAMPAIGN COMPLETED SUCCESSFULLY!")
        print(f"{'='*60}")
        print(f"📊 CAMPAIGN SUMMARY")
        print(f"{'='*60}")
        print(f"👥 Total Leads Processed: {len(leads)}")
        print(f"📧 Emails Generated: {len(emails)}")
        print(f"🤖 AI Research Used: {ai_count}")
        print(f"📝 Template Fallbacks: {fallback_count}")
        print(f"⏰ Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Duration: {duration}")
        print(f"🔍 Snov.io Enrichment: {'✅ Yes' if enrich_with_snov else '❌ No'}")
        print(f"{'='*60}")

        return emails

    def run_snov_campaign(self, company_query: str, limit: int = 10, use_ai_research: bool = True):
        """Run a complete outreach campaign using Snov.io leads"""
        print("🚀 Starting Snov.io-based outreach campaign...")

        # Search for companies
        companies = self.search_snov_leads(company_query, limit)

        # Convert to leads (simplified - you'd need to implement full lead creation from Snov.io data)
        leads = []
        for company in companies:
            # This is a simplified example - you'd need to implement proper lead creation
            # based on your Snov.io data structure
            lead = Lead(
                first_name="[First Name]",
                last_name="[Last Name]",
                email="[Email]",
                company_name=company.get('name', 'Unknown Company'),
                position="[Position]",
                industry=company.get('industry', 'Unknown Industry')
            )
            leads.append(lead)

        # Generate emails
        emails = self.generate_emails_for_leads(leads, use_ai_research)

        # Save results
        self.save_results(emails)

        print(f"🎉 Campaign completed! Generated {len(emails)} personalized emails.")

        # Save campaign log
        self._save_campaign_log()

        return emails

    def _save_campaign_log(self):
        """Save campaign log to CSV and JSON files"""
        if not self.campaign_log:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)

        # Save as CSV
        csv_path = f"logs/campaign_log_{timestamp}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['full_name', 'company', 'method', 'timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.campaign_log)

        # Save as JSON
        json_path = f"logs/campaign_log_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.campaign_log, jsonfile, indent=2)

        print(f"📊 Campaign log saved: {csv_path} and {json_path}")


def main():
    """Main function to run the outreach agent"""
    parser = argparse.ArgumentParser(description="Enhanced Outreach Agent")
    parser.add_argument("--config", default="config.yaml", help="Path to configuration file")
    parser.add_argument("--csv", help="Path to CSV file with leads")
    parser.add_argument("--snov-query", help="Company search query for Snov.io")
    parser.add_argument("--enrich", action="store_true", help="Enrich leads with Snov.io data")
    parser.add_argument("--no-ai-research", action="store_true", help="Disable AI research, use templates only")
    parser.add_argument("--limit", type=int, default=10, help="Limit number of leads to process")
    parser.add_argument("--server", action="store_true", help="Run as Flask server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Server port (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    # Lead collection tool options
    parser.add_argument("--collect-leads", action="store_true", help="Use intelligent lead collection")
    parser.add_argument("--linkedin-urls", nargs="+", help="LinkedIn profile URLs to scrape")
    parser.add_argument("--company-urls", nargs="+", help="Company website URLs to scrape")
    parser.add_argument("--search-queries", nargs="+", help="Search queries for SerpAPI")
    parser.add_argument("--sales-nav-csv", help="Sales Navigator CSV export file")
    parser.add_argument("--tool-capabilities", action="store_true", help="Show available tool capabilities")
    parser.add_argument("--budget", choices=["free", "low", "medium", "high"], default="free", help="Budget constraint for tool selection")
    parser.add_argument("--priority", choices=["speed", "accuracy", "cost"], default="accuracy", help="Priority for tool selection")
    
    # CRM options
    parser.add_argument("--crm-dashboard", action="store_true", help="Show CRM dashboard")
    parser.add_argument("--crm-search", help="Search CRM contacts")
    parser.add_argument("--crm-status", choices=["new", "contacted", "responded", "qualified", "proposal_sent", "negotiation", "closed_won", "closed_lost", "dormant"], help="Filter by contact status")
    parser.add_argument("--crm-export", help="Export CRM data to file")
    parser.add_argument("--crm-import-to-sheets", help="Google Sheets ID to sync CRM data to")
    parser.add_argument("--crm-import-from-sheets", help="Google Sheets ID to import CRM data from")
    parser.add_argument("--crm-update-status", nargs=2, metavar=("EMAIL", "STATUS"), help="Update contact status: email new_status")
    parser.add_argument("--import-to-crm", action="store_true", help="Import collected leads to CRM")
    
    # License management options
    parser.add_argument("--license-info", action="store_true", help="Show license information")
    parser.add_argument("--set-license", help="Set license key")
    parser.add_argument("--remove-license", action="store_true", help="Remove stored license key")

    args = parser.parse_args()

    try:
        if args.server:
            # Run as Flask server
            run_server(host=args.host, port=args.port, debug=args.debug)
            return 0

        # Handle license management commands first
        if args.license_info:
            show_license_info()
            return 0
        
        if args.set_license:
            success = set_license_key(args.set_license)
            return 0 if success else 1
        
        if args.remove_license:
            remove_license_key()
            return 0

        # Initialize the agent
        agent = EnhancedOutreachAgent(args.config)
        
        if args.tool_capabilities:
            # Show tool capabilities and exit
            agent.get_tool_capabilities()
            return 0
        
        # CRM-specific commands
        if args.crm_dashboard:
            # Show CRM dashboard
            stats = agent.get_crm_dashboard()
            print(f"\n📊 CRM DASHBOARD")
            print(f"{'='*50}")
            print(f"📈 Total Contacts: {stats['total_contacts']}")
            print(f"📋 Recent Activity: {stats['recent_contacts']} contacts")
            print(f"\n🔄 PIPELINE SUMMARY:")
            pipeline = stats['pipeline_summary']
            print(f"   🆕 New Leads: {pipeline['new_leads']}")
            print(f"   📧 Contacted: {pipeline['contacted']}")
            print(f"   ✅ Qualified: {pipeline['qualified']}")
            print(f"   🎉 Closed Won: {pipeline['closed_won']}")
            print(f"   ❌ Closed Lost: {pipeline['closed_lost']}")
            return 0
        
        if args.crm_search or args.crm_status:
            # Search CRM contacts
            contacts = agent.search_crm_contacts(query=args.crm_search, status=args.crm_status)
            print(f"\n🔍 CRM SEARCH RESULTS")
            print(f"{'='*50}")
            print(f"Found {len(contacts)} contacts:")
            
            for contact in contacts[:20]:  # Limit to first 20
                print(f"   📧 {contact.first_name} {contact.last_name} ({contact.email})")
                print(f"      🏢 {contact.company_name} - {contact.position}")
                print(f"      📊 Status: {contact.status.value} | Score: {contact.lead_score}")
                print()
            
            if len(contacts) > 20:
                print(f"   ... and {len(contacts) - 20} more contacts")
            return 0
        
        if args.crm_export:
            # Export CRM data
            filename = agent.export_crm_data("csv", args.crm_export)
            print(f"✅ CRM data exported to: {filename}")
            return 0
        
        if args.crm_import_to_sheets:
            # Sync to Google Sheets
            success = agent.sync_crm_to_google_sheets(args.crm_import_to_sheets)
            if success:
                print(f"✅ CRM data synced to Google Sheets")
            else:
                print(f"❌ Failed to sync to Google Sheets")
            return 0
        
        if args.crm_import_from_sheets:
            # Import from Google Sheets
            contacts = agent.import_crm_from_google_sheets(args.crm_import_from_sheets)
            print(f"✅ Imported {len(contacts)} contacts from Google Sheets")
            return 0
        
        if args.crm_update_status:
            # Update contact status
            email, status = args.crm_update_status
            success = agent.update_contact_status(email, status)
            if success:
                print(f"✅ Updated status for {email} to {status}")
            else:
                print(f"❌ Failed to update status for {email}")
            return 0
        
        if args.collect_leads:
            # Use intelligent lead collection
            request_params = {
                'task_type': 'lead_collection',
                'input_data': {
                    'linkedin_urls': args.linkedin_urls or [],
                    'company_urls': args.company_urls or [],
                    'search_queries': args.search_queries or [],
                    'csv_file': args.sales_nav_csv or '',
                    'source': 'sales_nav' if args.sales_nav_csv else 'web'
                },
                'constraints': {
                    'budget': args.budget,
                    'priority': args.priority
                },
                'max_leads': args.limit
            }
            
            # Collect leads intelligently
            leads = agent.collect_leads_intelligently(request_params)
            
            if leads:
                # Import to CRM if requested
                if args.import_to_crm:
                    agent.import_leads_to_crm(leads, "intelligent_collection")
                
                # Generate emails for collected leads
                emails = agent.generate_emails_for_leads(leads, not args.no_ai_research)
                agent.save_results(emails, leads)
            else:
                print("❌ No leads collected")
                return 1
        
        elif args.csv:
            # Run CSV-based campaign
            agent.run_csv_campaign(
                csv_path=args.csv,
                enrich_with_snov=args.enrich,
                use_ai_research=not args.no_ai_research
            )
        elif args.snov_query:
            # Run Snov.io-based campaign
            agent.run_snov_campaign(
                company_query=args.snov_query,
                limit=args.limit,
                use_ai_research=not args.no_ai_research
            )
        else:
            # Run example campaign
            print("📝 Running example campaign with sample data...")
            agent.run_csv_campaign(use_ai_research=not args.no_ai_research)

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


# Flask server for HTTP API
app = Flask(__name__)
outreach_agent = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'outreach-agent',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/campaign', methods=['POST'])
def run_campaign():
    """Run an outreach campaign via HTTP POST"""
    global outreach_agent

    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        # Extract parameters
        csv_path = data.get('csv_path', 'leads.csv')
        use_ai = data.get('use_ai', True)
        enrich = data.get('enrich', False)
        limit = data.get('limit', 10)

        # Initialize agent if not already done
        if outreach_agent is None:
            outreach_agent = EnhancedOutreachAgent()

        # Run the campaign
        print(f"🚀 Starting campaign via HTTP API...")
        print(f"📁 CSV Path: {csv_path}")
        print(f"🤖 AI Research: {use_ai}")
        print(f"🔍 Enrich: {enrich}")
        print(f"📊 Limit: {limit}")

        emails = outreach_agent.run_csv_campaign(
            csv_path=csv_path,
            enrich_with_snov=enrich,
            use_ai_research=use_ai
        )

        return jsonify({
            'success': True,
            'message': 'Campaign completed successfully',
            'emails_generated': len(emails),
            'campaign_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/campaign/status', methods=['GET'])
def campaign_status():
    """Get campaign status and recent logs"""
    global outreach_agent

    try:
        if outreach_agent is None:
            return jsonify({
                'status': 'not_initialized',
                'message': 'No campaigns have been run yet'
            })

        return jsonify({
            'status': 'ready',
            'last_campaign_logs': outreach_agent.campaign_log[-10:] if outreach_agent.campaign_log else [],
            'total_campaigns_logged': len(outreach_agent.campaign_log)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask server"""
    print(f"🌐 Starting Flask server on {host}:{port}")
    print(f"📋 Available endpoints:")
    print(f"   GET  /health - Health check")
    print(f"   POST /campaign - Run outreach campaign")
    print(f"   GET  /campaign/status - Get campaign status")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    exit(main())

