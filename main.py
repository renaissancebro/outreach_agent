import os
import yaml
import argparse
from typing import List, Dict
from datetime import datetime
from crewai import Agent, Task, Crew
from dotenv import load_dotenv
from lead_manager import LeadManager, Lead
from email_generator import EmailGenerator

# Load environment variables
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


class EnhancedOutreachAgent:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the enhanced outreach agent with configuration"""
        self.config = self._load_config(config_path)
        self.lead_manager = LeadManager(self.config)
        self.email_generator = EmailGenerator(self.config)
        self.crew = self._setup_crew()

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
                "Research the provided company and contact information to gather insights for personalization. "
                "Focus on: recent news, company achievements, industry challenges, and how our solution could help. "
                "Return structured data including pain points, solution benefits, and company context."
            ),
            expected_output="JSON object with research findings including pain_points, solution_benefits, company_research, and industry_insights",
            agent=research_agent
        )

        # Outreach Task
        outreach_task = Task(
            description=(
                "Using the research provided and lead information, create a highly personalized outreach email. "
                "The email should be warm, relevant, and demonstrate understanding of the recipient's role and company. "
                "Include a compelling subject line and 2-3 paragraph message that feels personal and valuable."
            ),
            expected_output="Complete email with subject line and personalized body content",
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

    def generate_emails_for_leads(self, leads: List[Lead], use_ai_research: bool = True) -> List[Dict]:
        """Generate personalized emails for a list of leads"""
        print(f"\n🔧 Starting email generation for {len(leads)} leads...")
        print(f"🔧 AI Research enabled: {use_ai_research}")

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
                    # Create a research prompt with lead information
                    research_prompt = f"""
                    Research this company and contact for personalized outreach:
                    - Company: {lead.company_name}
                    - Contact: {lead.first_name} {lead.last_name} ({lead.position})
                    - Industry: {lead.industry}
                    - Website: {lead.website or 'Not provided'}
                    - Location: {lead.location or 'Not provided'}

                    Focus on recent news, achievements, challenges, and how our AI dashboard solution could help with regulatory compliance and industry insights.
                    """

                    print(f"   🔍 Research prompt created, running CrewAI...")

                    # Run the crew to get research and email
                    result = self.crew.kickoff()

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
                        'solution_benefit': 'AI-powered regulatory dashboard',
                        'pain_point': 'regulatory compliance tracking'
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

    def run_csv_campaign(self, csv_path: str = None, enrich_with_snov: bool = False, use_ai_research: bool = True):
        """Run a complete outreach campaign using CSV leads"""
        print(f"\n{'='*60}")
        print(f"🚀 STARTING CSV-BASED OUTREACH CAMPAIGN")
        print(f"{'='*60}")
        print(f"📁 CSV Path: {csv_path or 'leads.csv'}")
        print(f"🔍 Enrich with Snov.io: {enrich_with_snov}")
        print(f"🤖 AI Research: {use_ai_research}")
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

        print(f"\n{'='*60}")
        print(f"🎉 CAMPAIGN COMPLETED SUCCESSFULLY!")
        print(f"📊 Summary:")
        print(f"   📧 Emails generated: {len(emails)}")
        print(f"   👥 Leads processed: {len(leads)}")
        print(f"   🤖 AI Research used: {use_ai_research}")
        print(f"   🔍 Snov.io enrichment: {enrich_with_snov}")
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
        return emails


def main():
    """Main function to run the outreach agent"""
    parser = argparse.ArgumentParser(description="Enhanced Outreach Agent")
    parser.add_argument("--config", default="config.yaml", help="Path to configuration file")
    parser.add_argument("--csv", help="Path to CSV file with leads")
    parser.add_argument("--snov-query", help="Company search query for Snov.io")
    parser.add_argument("--enrich", action="store_true", help="Enrich leads with Snov.io data")
    parser.add_argument("--no-ai-research", action="store_true", help="Disable AI research, use templates only")
    parser.add_argument("--limit", type=int, default=10, help="Limit number of leads to process")

    args = parser.parse_args()

    try:
        # Initialize the agent
        agent = EnhancedOutreachAgent(args.config)

        if args.csv:
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


if __name__ == "__main__":
    exit(main())

