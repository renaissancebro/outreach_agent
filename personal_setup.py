#!/usr/bin/env python3
"""
Personal Business Setup Script
Sets up Outreach Agent for your personal business use
"""

import os
import yaml
import json
from datetime import datetime
from payment_system import PaymentDatabase, LicenseManager, SubscriptionTier

def setup_personal_license():
    """Set up a personal Pro license for business use"""
    print("💎 SETTING UP PERSONAL PRO LICENSE")
    print("="*50)
    
    # Get user email
    email = input("Enter your business email: ").strip()
    if not email:
        email = "your-business@example.com"
    
    # Create Pro license
    db = PaymentDatabase()
    lm = LicenseManager(db)
    license = lm.create_license_for_payment(email, SubscriptionTier.PRO)
    
    print(f"✅ Personal Pro license created: {license.license_key}")
    
    # Set the license
    os.system(f"python main.py --set-license {license.license_key}")
    
    # Save license key for reference
    with open('personal_license.txt', 'w') as f:
        f.write(f"Personal Pro License: {license.license_key}\n")
        f.write(f"Email: {email}\n")
        f.write(f"Created: {datetime.now().isoformat()}\n")
    
    print("💾 License saved to personal_license.txt")
    return license.license_key

def create_personal_config():
    """Create a personal configuration for your business"""
    print("\n🔧 CREATING PERSONAL BUSINESS CONFIG")
    print("="*50)
    
    # Get business information
    business_name = input("Enter your business name: ").strip() or "Your Business"
    industry = input("Enter your industry: ").strip() or "Technology"
    solution = input("Enter your main solution/product: ").strip() or "Your Solution"
    
    # Create personalized config
    personal_config = {
        'agent': {
            'role': 'Business Development Specialist',
            'goal': f'Generate personalized outreach emails for {business_name}',
            'backstory': f'You are an expert at creating compelling outreach for {business_name}, a {industry} company that provides {solution}.',
            'verbose': True,
            'allow_delegation': False
        },
        'personalization': {
            'research_depth': 'high',
            'include_company_research': True,
            'max_email_length': 350,
            'tone': 'professional_friendly',
            'business_name': business_name,
            'industry': industry,
            'solution': solution
        },
        'email_templates': {
            'subject_templates': [
                f"Quick question about {{company_name}} and {solution.lower()}",
                f"How {business_name} can help {{company_name}} with {{pain_point}}",
                f"{{first_name}}, thought you'd be interested in this {industry.lower()} solution",
                f"5-minute chat about {{company_name}}'s {{industry}} challenges?"
            ],
            'opening_templates': [
                f"Hi {{first_name}}, I'm reaching out from {business_name} because I noticed {{company_name}} is doing interesting work in {{industry}}.",
                f"Hello {{first_name}}, I came across {{company_name}} and was impressed by your {{industry}} initiatives.",
                f"Hi {{first_name}}, as someone working in {{industry}}, I thought you might be interested in how {business_name} helps companies like {{company_name}}."
            ],
            'value_propositions': [
                f"{business_name} specializes in {solution} for {industry} companies",
                f"We've helped similar companies reduce costs by 30% through {solution}",
                f"Our {solution} platform has generated significant ROI for {industry} leaders"
            ]
        },
        'output': {
            'format': 'json',
            'save_to_file': True,
            'output_directory': 'personal_campaigns',
            'save_enriched_leads': True
        },
        'crm': {
            'database_path': 'personal_crm.db',
            'auto_import_leads': True,
            'auto_log_emails': True,
            'lead_scoring': {
                'has_linkedin': 5,
                'has_phone': 3,
                'company_size_large': 10,
                'industry_match': 15,
                'website_exists': 5
            }
        },
        'rate_limits': {
            'delay_between_emails': 1,
            'emails_per_hour': 50,
            'api_calls_per_minute': 30
        }
    }
    
    # Save personal config
    with open('personal_config.yaml', 'w') as f:
        yaml.dump(personal_config, f, default_flow_style=False, indent=2)
    
    print(f"✅ Personal config created: personal_config.yaml")
    print(f"   Business: {business_name}")
    print(f"   Industry: {industry}")
    print(f"   Solution: {solution}")
    
    return personal_config

def create_personal_leads_template():
    """Create a template for personal lead collection"""
    print("\n📋 CREATING PERSONAL LEADS TEMPLATE")
    print("="*50)
    
    # Create personal leads directory
    os.makedirs('personal_leads', exist_ok=True)
    os.makedirs('personal_campaigns', exist_ok=True)
    
    # Sample personal leads template
    template_leads = [
        {
            'first_name': 'Example',
            'last_name': 'Prospect',
            'email': 'prospect@targetcompany.com',
            'company_name': 'Target Company',
            'position': 'CEO',
            'industry': 'Technology',
            'website': 'https://targetcompany.com',
            'linkedin_url': 'https://linkedin.com/in/prospect',
            'location': 'San Francisco, CA',
            'company_size': '50-100',
            'phone': '+1-555-0123',
            'notes': 'Replace with your actual prospects'
        }
    ]
    
    # Save template
    import csv
    with open('personal_leads/template.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = template_leads[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(template_leads)
    
    print("✅ Personal leads template created: personal_leads/template.csv")
    print("   Edit this file with your actual prospects")

def setup_api_keys():
    """Guide user through API key setup"""
    print("\n🔑 API KEYS SETUP GUIDE")
    print("="*50)
    
    print("For optimal functionality, set up these API keys:")
    print()
    
    # Check existing keys
    openai_key = os.getenv("OPENAI_API_KEY")
    snov_client_id = os.getenv("SNOV_CLIENT_ID")
    serpapi_key = os.getenv("SERPAPI_KEY")
    
    print(f"OpenAI API Key: {'✅ Set' if openai_key else '❌ Not set (REQUIRED)'}")
    print(f"Snov.io Client ID: {'✅ Set' if snov_client_id else '⚠️  Not set (Optional)'}")
    print(f"SerpAPI Key: {'✅ Set' if serpapi_key else '⚠️  Not set (Optional)'}")
    
    if not openai_key:
        print("\n⚠️  IMPORTANT: OpenAI API key is required for AI-powered emails")
        print("Get your key at: https://platform.openai.com/api-keys")
        print("Add to your .env file: OPENAI_API_KEY=sk-your-key-here")
    
    # Create .env template if it doesn't exist
    if not os.path.exists('.env'):
        env_template = """# Required for AI-powered email generation
OPENAI_API_KEY=sk-your-openai-key-here

# Optional: Snov.io for lead enrichment
SNOV_CLIENT_ID=your-snov-client-id
SNOV_CLIENT_SECRET=your-snov-client-secret

# Optional: SerpAPI for search-based lead collection
SERPAPI_KEY=your-serpapi-key

# Optional: For production Stripe integration
# STRIPE_SECRET_KEY=sk_live_your-stripe-key
# STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret
"""
        with open('.env', 'w') as f:
            f.write(env_template)
        print("\n✅ Created .env template file - add your API keys there")

def create_personal_scripts():
    """Create convenient scripts for personal use"""
    print("\n📜 CREATING PERSONAL SCRIPTS")
    print("="*50)
    
    # Quick campaign script
    campaign_script = """#!/bin/bash
# Personal Campaign Runner
echo "🚀 Starting Personal Outreach Campaign"
echo "Using personal configuration and Pro license"

# Run campaign with personal config
python main.py --config personal_config.yaml --csv personal_leads/prospects.csv --limit 10

echo "✅ Campaign completed! Check personal_campaigns/ for results"
"""
    
    with open('run_personal_campaign.sh', 'w') as f:
        f.write(campaign_script)
    os.chmod('run_personal_campaign.sh', 0o755)
    
    # CRM management script
    crm_script = """#!/bin/bash
# Personal CRM Manager
echo "📊 Personal CRM Dashboard"

echo "=== CRM Statistics ==="
python main.py --config personal_config.yaml --crm-dashboard

echo ""
echo "=== Recent Contacts ==="
python main.py --config personal_config.yaml --crm-status new

echo ""
echo "=== All Contacts ==="
python main.py --config personal_config.yaml --crm-search ""
"""
    
    with open('personal_crm.sh', 'w') as f:
        f.write(crm_script)
    os.chmod('personal_crm.sh', 0o755)
    
    # Lead collection script
    collect_script = """#!/bin/bash
# Personal Lead Collection
echo "🎯 Personal Lead Collection Tools"

echo "Available tools:"
python main.py --config personal_config.yaml --tool-capabilities

echo ""
echo "To collect leads from Sales Navigator export:"
echo "python main.py --config personal_config.yaml --collect-leads --sales-nav-csv your_export.csv --import-to-crm"

echo ""
echo "To scrape LinkedIn profiles:"
echo "python main.py --config personal_config.yaml --collect-leads --linkedin-urls https://linkedin.com/in/profile1 --import-to-crm"
"""
    
    with open('collect_personal_leads.sh', 'w') as f:
        f.write(collect_script)
    os.chmod('collect_personal_leads.sh', 0o755)
    
    print("✅ Personal scripts created:")
    print("   ./run_personal_campaign.sh - Run outreach campaigns")
    print("   ./personal_crm.sh - Manage your CRM")
    print("   ./collect_personal_leads.sh - Collect new leads")

def show_usage_guide():
    """Show how to use the personal setup"""
    print("\n📖 PERSONAL USAGE GUIDE")
    print("="*50)
    
    print("Your personal Outreach Agent is ready! Here's how to use it:")
    print()
    
    print("1. 📝 PREPARE YOUR LEADS:")
    print("   - Edit personal_leads/template.csv with your actual prospects")
    print("   - Or export from Sales Navigator and use lead collection tools")
    print()
    
    print("2. 🚀 RUN CAMPAIGNS:")
    print("   ./run_personal_campaign.sh")
    print("   # Or manually:")
    print("   python main.py --config personal_config.yaml --csv personal_leads/prospects.csv")
    print()
    
    print("3. 📊 MANAGE CRM:")
    print("   ./personal_crm.sh")
    print("   # Update contact status:")
    print("   python main.py --config personal_config.yaml --crm-update-status email@company.com contacted")
    print()
    
    print("4. 🎯 COLLECT MORE LEADS:")
    print("   ./collect_personal_leads.sh")
    print("   # Or use intelligent collection:")
    print("   python main.py --config personal_config.yaml --collect-leads --search-queries 'your target companies'")
    print()
    
    print("5. 📈 TRACK PROGRESS:")
    print("   python main.py --license-info  # Check usage stats")
    print("   python main.py --config personal_config.yaml --crm-dashboard")
    print()
    
    print("💡 PRO TIPS:")
    print("   - All emails are automatically logged in your personal CRM")
    print("   - Use --limit to test with small batches first")
    print("   - Check personal_campaigns/ for generated emails")
    print("   - Your Pro license includes all premium features!")

def main():
    """Set up personal business channel"""
    print("🏢 OUTREACH AGENT PERSONAL BUSINESS SETUP")
    print("="*60)
    print("Setting up your personal outreach automation system...")
    print("="*60)
    
    try:
        # Setup personal license
        license_key = setup_personal_license()
        
        # Create personal configuration
        create_personal_config()
        
        # Create leads template
        create_personal_leads_template()
        
        # Setup API keys guide
        setup_api_keys()
        
        # Create convenience scripts
        create_personal_scripts()
        
        # Show usage guide
        show_usage_guide()
        
        print("\n🎉 PERSONAL SETUP COMPLETED!")
        print("="*60)
        print(f"Your Pro license: {license_key}")
        print("Ready to start generating outreach for your business!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("Please check the error and try again.")

if __name__ == "__main__":
    main()