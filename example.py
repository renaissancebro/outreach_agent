#!/usr/bin/env python3
"""
Example script demonstrating the Enhanced Outreach Agent functionality.
This script shows how to use the agent programmatically.
"""

import os
from main import EnhancedOutreachAgent
from lead_manager import Lead

def example_csv_campaign():
    """Example: Run a campaign using CSV leads"""
    print("=== Example 1: CSV Campaign ===")

    # Initialize the agent
    agent = EnhancedOutreachAgent()

    # Run a campaign with the sample CSV file
    emails = agent.run_csv_campaign(
        csv_path="leads.csv",
        enrich_with_snov=False,  # Set to True if you have Snov.io API key
        use_ai_research=True
    )

    print(f"Generated {len(emails)} emails")
    return emails

def example_template_only():
    """Example: Run a campaign using only templates (no AI research)"""
    print("\n=== Example 2: Template-Only Campaign ===")

    agent = EnhancedOutreachAgent()

    # Load leads
    leads = agent.process_csv_leads("leads.csv")

    # Generate emails using templates only
    emails = agent.generate_emails_for_leads(leads, use_ai_research=False)

    # Save results
    agent.save_results(emails)

    print(f"Generated {len(emails)} template-based emails")
    return emails

def example_custom_leads():
    """Example: Create custom leads programmatically"""
    print("\n=== Example 3: Custom Leads ===")

    agent = EnhancedOutreachAgent()

    # Create custom leads
    custom_leads = [
        Lead(
            first_name="Alice",
            last_name="Johnson",
            email="alice@startup.com",
            company_name="TechStartup",
            position="Founder",
            industry="SaaS",
            website="https://techstartup.com",
            location="San Francisco"
        ),
        Lead(
            first_name="Bob",
            last_name="Chen",
            email="bob@enterprise.com",
            company_name="EnterpriseCorp",
            position="CTO",
            industry="Enterprise Software",
            website="https://enterprisecorp.com",
            location="New York"
        )
    ]

    # Generate emails for custom leads
    emails = agent.generate_emails_for_leads(custom_leads, use_ai_research=True)

    # Save results
    agent.save_results(emails)

    print(f"Generated {len(emails)} emails for custom leads")
    return emails

def example_snov_search():
    """Example: Search for companies using Snov.io (requires API key)"""
    print("\n=== Example 4: Snov.io Search ===")

    # Check if Snov.io API key is available
    if not os.getenv('SNOV_API_KEY'):
        print("⚠️  SNOV_API_KEY not found. Skipping Snov.io example.")
        return []

    agent = EnhancedOutreachAgent()

    # Search for companies
    companies = agent.search_snov_leads("renewable energy", limit=3)

    print(f"Found {len(companies)} companies:")
    for company in companies:
        print(f"  - {company.get('name', 'Unknown')} ({company.get('industry', 'Unknown Industry')})")

    return companies

def example_configuration_modification():
    """Example: Modify configuration programmatically"""
    print("\n=== Example 5: Configuration Modification ===")

    # Load configuration
    agent = EnhancedOutreachAgent()

    # Modify configuration for this example
    agent.config['personalization']['tone'] = 'casual'
    agent.config['personalization']['max_email_length'] = 200

    # Create a simple lead
    lead = Lead(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        company_name="Example Corp",
        position="Manager",
        industry="Technology"
    )

    # Generate email with modified settings
    email = agent.email_generator.generate_email(lead, {
        'solution_benefit': 'awesome new tool',
        'pain_point': 'manual processes'
    })

    print("Generated email with casual tone:")
    print(f"Subject: {email['subject']}")
    print(f"Body: {email['body']}")

    return email

def main():
    """Run all examples"""
    print("🚀 Enhanced Outreach Agent Examples")
    print("=" * 50)

    try:
        # Example 1: CSV Campaign
        emails1 = example_csv_campaign()

        # Example 2: Template Only
        emails2 = example_template_only()

        # Example 3: Custom Leads
        emails3 = example_custom_leads()

        # Example 4: Snov.io Search (if API key available)
        companies = example_snov_search()

        # Example 5: Configuration Modification
        email5 = example_configuration_modification()

        print("\n" + "=" * 50)
        print("✅ All examples completed successfully!")
        print(f"📧 Total emails generated: {len(emails1) + len(emails2) + len(emails3)}")
        print(f"🏢 Companies found via Snov.io: {len(companies)}")

    except Exception as e:
        print(f"❌ Error running examples: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
