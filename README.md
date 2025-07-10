# Enhanced Outreach Agent with CRM & Payment System

A comprehensive sales automation SaaS platform that combines AI-powered outreach with full CRM functionality and tiered subscription access. Generate personalized cold emails, manage your sales pipeline, and track every interaction - all in one integrated system with flexible pricing tiers.

## Features

### 🤖 **AI-Powered Email Generation**
- **Intelligent Research**: CrewAI agents research companies and create personalized emails
- **Template Fallback**: Professional templates when AI research is disabled
- **Multiple Personalization Levels**: Low, medium, and high research depth
- **Smart Content**: Industry-specific pain points and solution positioning

### 📊 **Comprehensive CRM System** 
- **SQLite Database**: Robust contact management with full relationship tracking
- **Pipeline Management**: Status-based lead progression (new → contacted → qualified → closed)
- **Interaction History**: Complete record of all emails, calls, and touchpoints
- **Dashboard Analytics**: Real-time pipeline metrics and conversion tracking
- **Lead Scoring**: Configurable point system for lead qualification
- **Team Collaboration**: Share data with Google Sheets integration

### 🔍 **Intelligent Lead Collection**
- **AI Tool Selection**: Automatically chooses the best collection method for your data
- **Playwright Web Scraping**: Extract contacts from LinkedIn profiles and company websites
- **SerpAPI Integration**: Find prospects through Google search results
- **Sales Navigator Enhanced**: Advanced CSV processing with data enrichment
- **Snov.io Enrichment**: Automatically enhance leads with company data and email discovery

### 🔗 **Integrations & Automation**
- **Google Sheets Sync**: Bi-directional data sync for team collaboration  
- **Multi-format Output**: JSON, text, and markdown email exports
- **Rate Limiting**: Built-in protection against API limits and blocking
- **YAML Configuration**: Easy-to-modify settings for all features
- **Automated Workflows**: Seamless lead-to-email-to-CRM pipeline

### 💳 **Payment System & SaaS Features**
- **Tiered Subscription Model**: Free, Pro ($49/month), Enterprise ($199/month)
- **Stripe Integration**: Secure payment processing with webhooks
- **License Key Management**: Automated license generation and validation
- **Feature Access Control**: Tiered access to AI research, CRM, and integrations
- **Usage Tracking**: Monitor emails, API calls, and feature usage
- **REST API**: Full-featured API for integrations and custom applications
- **Landing Page**: Built-in checkout flow and pricing display

## 🚀 Subscription Tiers

### Free Tier
- ✅ **50 emails/month**
- ✅ **Basic CSV processing**
- ✅ **Template-based emails**
- ✅ **Playwright web scraping**
- ✅ **1 team seat**
- ❌ No AI research
- ❌ No CRM dashboard
- ❌ No API integrations

### Pro Tier - $49/month
- ✅ **1,000 emails/month**
- ✅ **AI-powered research**
- ✅ **Full CRM dashboard**
- ✅ **Snov.io integration**
- ✅ **Google Sheets sync**
- ✅ **SerpAPI access**
- ✅ **Priority support**
- ✅ **5 team seats**

### Enterprise Tier - $199/month
- ✅ **10,000 emails/month**
- ✅ **All Pro features**
- ✅ **Advanced analytics**
- ✅ **Custom integrations**
- ✅ **Dedicated support**
- ✅ **50 team seats**
- ✅ **SLA guarantee**

## Installation

1. **Clone and navigate to the project:**

   ```bash
   cd agents/outreach-agent
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   **For web scraping capabilities, also install:**
   ```bash
   pip install playwright serpapi
   playwright install
   ```

   **For Google Sheets integration (optional):**
   ```bash
   pip install gspread google-auth
   ```

3. **Set up environment variables:**
   Create a `.env` file with your API keys:
   ```bash
   # Required for AI email generation
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Optional: Snov.io for lead enrichment (choose ONE method)
   # Method 1: OAuth (Recommended)
   SNOV_CLIENT_ID=your_snov_client_id_here
   SNOV_CLIENT_SECRET=your_snov_client_secret_here
   
   # Method 2: API Key (Alternative)
   # SNOV_API_KEY=your_snov_api_key_here
   
   # Optional: SerpAPI for search-based lead collection
   SERPAPI_KEY=your_serpapi_key_here
   ```

4. **Validate your setup:**
   Run the validation script to ensure everything is configured correctly:
   ```bash
   python test_setup.py
   ```

## API Keys Setup

### Required API Keys

#### OpenAI API Key (Required)
- **Purpose**: Powers the AI research and email generation
- **How to get**: 
  1. Go to [OpenAI API](https://platform.openai.com/api-keys)
  2. Create an account or sign in
  3. Generate a new API key
  4. Add billing information (pay-per-use)
- **Cost**: ~$0.002 per email generated
- **Environment Variable**: `OPENAI_API_KEY`

### Optional API Keys

#### Snov.io API (Optional - for lead enrichment)
- **Purpose**: Enriches leads with additional company data and finds email addresses
- **How to get**:
  1. Go to [Snov.io](https://snov.io)
  2. Create an account
  3. Choose OAuth (recommended) or API Key method
  4. **For OAuth**: Go to API settings and create OAuth app
  5. **For API Key**: Go to API settings and generate key
- **Cost**: Free tier available, paid plans start at $30/month
- **Environment Variables**: 
  - OAuth: `SNOV_CLIENT_ID` and `SNOV_CLIENT_SECRET`
  - API Key: `SNOV_API_KEY`

#### SerpAPI (Optional - for search-based lead collection)
- **Purpose**: Performs Google searches to find companies and contacts
- **How to get**:
  1. Go to [SerpAPI](https://serpapi.com)
  2. Create an account
  3. Get your API key from the dashboard
- **Cost**: Free tier (100 searches/month), paid plans start at $50/month
- **Environment Variable**: `SERPAPI_KEY`

### Feature Availability by API Key

| Feature | OpenAI | Snov.io | SerpAPI | Google Sheets | Notes |
|---------|--------|---------|---------|---------------|-------|
| **🔥 CRM contact management** | ✅ | ❌ | ❌ | ❌ | **Always available** |
| **🔥 Pipeline tracking** | ✅ | ❌ | ❌ | ❌ | **Status management** |
| **🔥 Interaction history** | ✅ | ❌ | ❌ | ❌ | **Email logging** |
| **🔥 Team collaboration sync** | ✅ | ❌ | ❌ | ✅ | **Google Sheets** |
| Basic CSV email generation | ✅ | ❌ | ❌ | ❌ | Core functionality |
| AI research & personalization | ✅ | ❌ | ❌ | ❌ | Enhanced emails |
| Lead enrichment | ✅ | ✅ | ❌ | ❌ | Better lead data |
| Sales Navigator processing | ✅ | ✅ | ❌ | ❌ | Enhanced CSV processing |
| Web scraping (Playwright) | ✅ | ❌ | ❌ | ❌ | Free web scraping |
| Search-based lead collection | ✅ | ❌ | ✅ | ❌ | Find new prospects |
| Company research | ✅ | ✅ | ✅ | ❌ | Maximum capability |

### Testing API Keys

After setting up your keys, test them:

```bash
# Test all configured APIs
python test_setup.py

# Test lead collection tools specifically
python test_lead_collection.py

# Show available tools based on your keys
python main.py --tool-capabilities
```

### ✅ What Will Work With Real API Keys

**With OpenAI API Key Only:**
- ✅ **Complete CRM system with pipeline tracking**
- ✅ **Automatic email interaction logging** 
- ✅ **Contact management and search**
- ✅ **Dashboard analytics and reporting**
- ✅ Basic CSV email generation
- ✅ AI-powered research and personalization
- ✅ Playwright web scraping (free)
- ✅ Sales Navigator CSV processing
- ✅ Template-based email generation
- ✅ All core functionality

**Adding Snov.io API:**
- ✅ Lead enrichment with company data
- ✅ Email address discovery
- ✅ Company information lookup
- ✅ Enhanced Sales Navigator processing
- ✅ Lead data validation and cleaning

**Adding SerpAPI Key:**
- ✅ Search-based lead collection
- ✅ Company discovery through Google search
- ✅ Industry-specific prospect finding
- ✅ Automated lead generation from search queries

**Adding Google Sheets Credentials:**
- ✅ **Team collaboration with shared CRM data**
- ✅ **Bi-directional Google Sheets sync**
- ✅ **Real-time team pipeline visibility**
- ✅ **Distributed sales team management**

**All APIs Together:**
- ✅ **Complete sales automation platform**
- ✅ **Enterprise-grade CRM with team collaboration**
- ✅ Maximum lead collection capability and accuracy
- ✅ Intelligent tool selection with all options
- ✅ Comprehensive lead-to-close pipeline
- ✅ Automated fallback between tools

### 🔧 Quick Start for Real Usage

1. **Get OpenAI API key** (required, ~$0.002/email)
2. **Add to .env file**:
   ```bash
   OPENAI_API_KEY=sk-your-actual-key-here
   ```
3. **Test basic functionality**:
   ```bash
   python main.py --csv your_leads.csv --limit 5
   ```
4. **Add optional APIs** as needed for enhanced features
5. **Scale up** once you're comfortable with the system

### 🔗 Google Sheets Integration Setup

To enable Google Sheets sync for team collaboration:

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing one

2. **Enable Google Sheets API**:
   - In the Console, go to "APIs & Services" > "Library"
   - Search for "Google Sheets API" and enable it
   - Also enable "Google Drive API"

3. **Create Service Account**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Give it a name like "outreach-agent-sheets"
   - Download the JSON key file

4. **Configure the System**:
   - Save the JSON file as `google_credentials.json` in your project directory
   - The system will automatically detect and use it

5. **Share Your Sheet**:
   - Create a Google Sheet for your CRM data
   - Share it with the service account email (found in the JSON file)
   - Give it "Editor" permissions
   - Copy the Sheet ID from the URL

6. **Test the Integration**:
   ```bash
   python main.py --crm-import-to-sheets "your_sheet_id_here"
   ```

## 🚀 Complete Workflow Example

Here's how to use the system for a complete sales campaign:

### **Step 1: Collect Leads**
```bash
# Method 1: Sales Navigator export
python main.py --collect-leads --sales-nav-csv prospects.csv --import-to-crm

# Method 2: LinkedIn profile scraping  
python main.py --collect-leads --linkedin-urls https://linkedin.com/in/ceo1 https://linkedin.com/in/cto2 --import-to-crm

# Method 3: Search-based collection
python main.py --collect-leads --search-queries "AI startups San Francisco" --import-to-crm
```

### **Step 2: Generate Personalized Emails**
```bash
# AI-powered research and email generation (automatically logs to CRM)
python main.py --csv prospects.csv --limit 20

# Or use existing CRM contacts
python main.py --crm-status new --limit 10
```

### **Step 3: Track Pipeline Progress**
```bash
# View dashboard
python main.py --crm-dashboard

# Update lead status as responses come in
python main.py --crm-update-status john@techcorp.com responded
python main.py --crm-update-status jane@startup.com qualified

# Search and filter contacts
python main.py --crm-search "TechCorp"
python main.py --crm-status qualified
```

### **Step 4: Team Collaboration**
```bash
# Export to Google Sheets for team access
python main.py --crm-import-to-sheets "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

# Export for analysis
python main.py --crm-export monthly_report.csv
```

### **Step 5: Follow-up Campaigns**
```bash
# Generate follow-up emails for contacted leads
python main.py --crm-status contacted --generate-followup

# Or target qualified leads with proposals
python main.py --crm-status qualified --template proposal
```

**🎯 Result**: Complete sales automation from lead collection → personalized outreach → pipeline tracking → team collaboration → closed deals!

## Configuration

The agent uses `config.yaml` for all settings. Key configuration sections:

### Agent Settings

```yaml
agent:
  role: "Outreach Specialist"
  goal: "Write personalized cold outreach emails"
  backstory: "You are a skilled marketing agent..."
  verbose: true
  allow_delegation: false
```

### Email Templates

```yaml
email_templates:
  subject_templates:
    - "Quick question about {company_name} and {pain_point}"
    - "How {company_name} can leverage {solution_benefit}"
  opening_templates:
    - "Hi {first_name}, I noticed {company_name} is doing interesting work in {industry}."
```

### Lead Sources

```yaml
lead_sources:
  csv:
    default_path: "leads.csv"
    required_columns:
      - "first_name"
      - "last_name"
      - "email"
      - "company_name"
      - "position"
      - "industry"
  snov_io:
    api_key: "${SNOV_API_KEY}"
    base_url: "https://api.snov.io"
```

### Personalization Settings

```yaml
personalization:
  research_depth: "medium" # low, medium, high
  include_company_research: true
  max_email_length: 300
  tone: "professional_friendly" # formal, professional_friendly, casual
```

### CRM Configuration

```yaml
crm:
  # SQLite database path
  database_path: "crm.db"
  
  # Google Sheets integration (optional)
  google_credentials_path: "google_credentials.json"
  
  # Auto-import settings
  auto_import_leads: true
  auto_log_emails: true
  
  # Lead scoring rules
  lead_scoring:
    has_linkedin: 5
    has_phone: 3
    company_size_large: 10
    industry_match: 15
    
  # Pipeline automation
  pipeline:
    auto_advance_stages: false
    follow_up_days: 7
```

## 💳 Payment System & License Management

### Getting Started with Payments

The system operates on a freemium model with automatic feature gating:

1. **Free Tier**: Start immediately with basic features
2. **Pro Tier**: Unlock AI research, CRM dashboard, and integrations
3. **Enterprise Tier**: Full access with priority support

### License Management Commands

```bash
# Check current license status
python main.py --license-info

# Set a license key (obtained after payment)
python main.py --set-license "OUTREACH-XXXX-XXXX-XXXX-XXXX"

# Remove stored license key
python main.py --remove-license
```

### SaaS API Server

Start the full-featured API server with payment integration:

```bash
# Start the API server
python api_server.py

# Access the landing page
open http://localhost:8000/landing

# View API documentation
open http://localhost:8000/docs
```

### Key API Endpoints

- **Landing Page**: `GET /landing` - Pricing and checkout
- **Pricing Info**: `GET /pricing` - Subscription tier details
- **Free Sample**: `POST /free/generate-sample` - Try without signup
- **Authentication**: `GET /auth/validate` - Validate license key
- **Payment**: `POST /payment/checkout` - Create Stripe checkout
- **Webhooks**: `POST /payment/webhook` - Handle Stripe events

### Feature Access Control

Features are automatically gated based on your subscription tier:

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Basic email generation | ✅ | ✅ | ✅ |
| AI-powered research | ❌ | ✅ | ✅ |
| CRM dashboard | ❌ | ✅ | ✅ |
| Google Sheets sync | ❌ | ✅ | ✅ |
| API integrations | ❌ | ✅ | ✅ |
| Priority support | ❌ | ✅ | ✅ |
| Team seats | 1 | 5 | 50 |

### Usage Tracking

Monitor your usage and limits:

```bash
# View license information and usage stats
python main.py --license-info

# Example output:
# 📊 USAGE THIS MONTH
# Emails: 45 / 1000
# API Calls: 230 / 5000
```

## CRM System Overview

### 📊 **Database Schema**

The CRM uses SQLite with a comprehensive schema designed for sales pipeline management:

**Contacts Table:**
- Personal info (name, email, phone, LinkedIn)
- Company details (name, position, industry, size, location)
- CRM fields (status, lead source, score, assigned to)
- Sales data (estimated value, expected close date)
- Timestamps (created, updated, last contacted)
- Notes and tags for custom organization

**Interactions Table:**
- Complete activity history (emails, calls, meetings, notes)
- Timestamps and content for each interaction
- Metadata tracking (campaign IDs, email length, etc.)
- Created by tracking for team environments

**Campaigns Table:**
- Campaign management and tracking
- Performance metrics (emails sent, responses, conversions)
- Date ranges and status tracking

### 🔄 **Lead Status Progression**

The system tracks leads through a complete sales pipeline:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  New Lead   │ -> │  Contacted  │ -> │  Responded  │ -> │  Qualified  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                  │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│ Closed Won  │ <- │ Negotiation │ <- │Proposal Sent│ <-----------┘
└─────────────┘    └─────────────┘    └─────────────┘
       │                                        │
       │           ┌─────────────┐              │
       └---------> │Closed Lost  │ <------------┘
                   └─────────────┘
```

### 📈 **Analytics & Reporting**

**Dashboard Metrics:**
- Total contacts and recent activity
- Pipeline distribution by status
- Conversion rates at each stage
- Average time in each status
- Top performing campaigns

**Export Capabilities:**
- CSV export for analysis
- Google Sheets for team collaboration
- JSON format for integrations
- Filtered exports by status/date range

## Usage

### Quick Start

1. **Set up your API keys** in a `.env` file
2. **Run the validation script**: `python test_setup.py`
3. **Start generating emails**: `python main.py --csv leads.csv`

### Basic Usage

**Run with CSV leads:**

```bash
python main.py --csv leads.csv
```

**Run with Snov.io search:**

```bash
python main.py --snov-query "renewable energy companies"
```

**Enrich CSV leads with Snov.io data:**

```bash
python main.py --csv leads.csv --enrich
```

**Use template-based generation only (no AI research):**

```bash
python main.py --csv leads.csv --no-ai-research
```

**Run as a Flask API server:**

```bash
python main.py --server --port 5000
```

### 🆕 Intelligent Lead Collection

The agent can automatically choose the best tool for your lead collection needs:

**Show available tools and capabilities:**

```bash
python main.py --tool-capabilities
```

**Intelligently process Sales Navigator export:**

```bash
python main.py --collect-leads --sales-nav-csv your_export.csv
```

**Scrape LinkedIn profiles (requires Playwright setup):**

```bash
python main.py --collect-leads --linkedin-urls https://linkedin.com/in/profile1 https://linkedin.com/in/profile2
```

**Search-based lead collection (requires SerpAPI key):**

```bash
python main.py --collect-leads --search-queries "tech startups San Francisco" "AI companies"
```

**Scrape company websites:**

```bash
python main.py --collect-leads --company-urls https://company1.com https://company2.com
```

**Control tool selection with constraints:**

```bash
python main.py --collect-leads --sales-nav-csv export.csv --budget free --priority accuracy
```

### 📊 **CRM & Pipeline Management**

Complete sales pipeline management with automated tracking:

**📈 View pipeline dashboard:**
```bash
python main.py --crm-dashboard
```
*Shows total contacts, pipeline summary, and conversion metrics*

**🔍 Search and filter contacts:**
```bash
# Search by name, company, or email
python main.py --crm-search "TechCorp"
python main.py --crm-search "john@company.com"

# Filter by lead status
python main.py --crm-status new          # New leads
python main.py --crm-status contacted    # Recently contacted
python main.py --crm-status qualified    # Qualified prospects
python main.py --crm-status closed_won   # Successful deals
```

**🔄 Manage contact status:**
```bash
# Update lead status as you progress through sales cycle
python main.py --crm-update-status john@company.com contacted
python main.py --crm-update-status jane@startup.com qualified
python main.py --crm-update-status ceo@bigcorp.com closed_won
```

**📤 Export and sync data:**
```bash
# Export CRM data to CSV
python main.py --crm-export contacts_export.csv

# Sync with Google Sheets for team collaboration
python main.py --crm-import-to-sheets "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

# Import contacts from shared Google Sheet
python main.py --crm-import-from-sheets "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
```

**🤖 Automated CRM integration:**
```bash
# Automatically import leads to CRM during collection
python main.py --collect-leads --sales-nav-csv file.csv --import-to-crm

# All generated emails are automatically logged in CRM
python main.py --csv leads.csv  # Emails tracked automatically
```

**📊 Pipeline Status Flow:**
```
New Lead → Contacted → Responded → Qualified → Proposal Sent → Negotiation → Closed Won/Lost
```
*Each status change is automatically timestamped and tracked*

### How the Intelligent Agent Works

The system includes an AI agent that analyzes your input and automatically selects the optimal tool:

1. **Analyzes your input**: URLs, search queries, CSV files, etc.
2. **Considers constraints**: Budget (free/paid), priority (speed/accuracy), available API keys
3. **Recommends best tool**: With confidence score and reasoning
4. **Fallback handling**: Tries alternatives if the primary tool fails
5. **Collects leads**: Using the selected tool with optimized parameters
6. **Generates emails**: Feeds collected leads into email generation

**Example Decision Process:**
- Input: LinkedIn URLs → Recommends: Playwright (free, high accuracy)
- Input: Company names → Recommends: SerpAPI (if key available) or Snov.io
- Input: Sales Nav CSV → Recommends: Enhanced CSV processor (always available)
- Budget: Free → Avoids paid API tools when possible
- Priority: Speed → Prefers faster tools over more accurate ones

### Advanced Usage

**Custom configuration file:**

```bash
python main.py --config custom_config.yaml --csv leads.csv
```

**Limit number of leads:**

```bash
python main.py --snov-query "tech companies" --limit 5
```

## CSV Format

Your CSV file should include these required columns:

```csv
first_name,last_name,email,company_name,position,industry,linkedin_url,phone,website,company_size,location,notes
John,Smith,john@company.com,TechCorp,CEO,Technology,https://linkedin.com/in/john,,https://techcorp.com,50-100,San Francisco,Interested in AI
```

## Snov.io Integration

The agent includes robust Snov.io integration with:

- **Company Search**: Search for companies using the Snov.io API
- **Company Information**: Get detailed company information
- **Email Discovery**: Find email addresses for contacts
- **Lead Enrichment**: Automatically enrich existing lead data
- **Connection Verification**: Built-in API connection testing

### Setting up Snov.io

Choose one of two authentication methods:

#### Method 1: OAuth Client Credentials (Recommended)
1. **Get your Snov.io OAuth credentials** from [snov.io](https://snov.io)
2. **Add them to your `.env` file**:
   ```bash
   SNOV_CLIENT_ID=your_client_id_here
   SNOV_CLIENT_SECRET=your_client_secret_here
   ```

#### Method 2: API Key (Alternative)
1. **Get a Snov.io API key** from [snov.io](https://snov.io)
2. **Add it to your `.env` file**:
   ```bash
   SNOV_API_KEY=your_snov_api_key_here
   ```

#### Testing and Usage
3. **Test the connection**:
   ```bash
   python test_setup.py
   ```
4. **Use Snov.io features**:
   - `--enrich`: Enrich CSV leads with Snov.io data
   - `--snov-query`: Search for companies directly

## Output

Generated emails are saved in the `output/` directory (configurable) in your chosen format:

- **JSON**: Structured data with metadata
- **Text**: Human-readable format
- **Markdown**: Formatted for easy reading

Example output structure:

```json
{
  "to": "john.smith@techcorp.com",
  "to_name": "John Smith",
  "subject": "Quick question about TechCorp and regulatory compliance",
  "body": "Hi John, I noticed TechCorp is doing interesting work in Technology...",
  "company": "TechCorp Inc",
  "position": "CEO",
  "industry": "Technology",
  "metadata": {
    "generated_at": "2024-01-15 10:30:00",
    "personalization_level": "medium",
    "tone": "professional_friendly"
  }
}
```

## Customization

### Adding New Email Templates

Edit `config.yaml` to add new templates:

```yaml
email_templates:
  subject_templates:
    - "Your new subject template with {company_name}"
  opening_templates:
    - "Your new opening template for {first_name}"
```

### Modifying Personalization Logic

Edit `email_generator.py` to customize how emails are generated based on research depth and tone.

### Adding New Lead Sources

Extend `lead_manager.py` to support additional lead sources like:

- LinkedIn Sales Navigator exports
- HubSpot CRM exports
- Custom API integrations

## Rate Limiting

The agent includes built-in rate limiting:

- Snov.io API calls: Configurable calls per minute
- Email generation: Configurable delay between emails

Adjust in `config.yaml`:

```yaml
rate_limits:
  snov_api_calls_per_minute: 60
  delay_between_emails: 2 # seconds
```

## Error Handling

The agent includes robust error handling:

- Graceful fallback from AI research to templates
- API rate limit compliance
- CSV validation and error reporting
- Detailed logging for debugging

## Examples

### Example 1: Basic CSV Campaign

```bash
# Generate emails for all leads in leads.csv
python main.py --csv leads.csv
```

### Example 2: Enriched Campaign

```bash
# Enrich leads with Snov.io data, then generate emails
python main.py --csv leads.csv --enrich
```

### Example 3: Snov.io Search Campaign

```bash
# Search for renewable energy companies and generate emails
python main.py --snov-query "renewable energy" --limit 10
```

### Example 4: Template-Only Campaign

```bash
# Use templates only (faster, no API costs)
python main.py --csv leads.csv --no-ai-research
```

## Troubleshooting

### Common Issues

#### API Key Issues
1. **Missing OpenAI API Key**: Ensure `OPENAI_API_KEY` is set in `.env`
2. **Invalid API Keys**: Run `python test_setup.py` to verify all keys
3. **Snov.io Authentication**: Choose either OAuth or API key method, not both
4. **SerpAPI Limits**: Check your monthly search quota

#### Lead Collection Issues
1. **No tools available**: Install optional dependencies: `pip install playwright serpapi`
2. **Playwright browser issues**: Run `playwright install` to download browsers
3. **LinkedIn scraping blocked**: Use rate limiting, avoid too many requests
4. **CSV format errors**: Check required columns match your file structure

#### CRM Issues
1. **Database locked**: Close any other applications accessing the CRM database
2. **Google Sheets sync failed**: Check service account credentials and sheet permissions
3. **Contact not found**: Verify email address is exact (case sensitive)
4. **Pipeline status invalid**: Use valid statuses: `new`, `contacted`, `responded`, `qualified`, `proposal_sent`, `negotiation`, `closed_won`, `closed_lost`
5. **CRM data missing**: Check if `auto_import_leads` is enabled in config.yaml

#### Performance Issues
1. **Slow email generation**: Reduce `research_depth` in config
2. **Rate limit errors**: Increase delays in `config.yaml`
3. **Memory issues**: Process leads in smaller batches using `--limit`

### Debug Mode
Set `verbose: true` in the agent configuration for detailed logging:

```yaml
agent:
  verbose: true
```

### Testing Your Setup

**Test API connections:**
```bash
python test_setup.py
```

**Test lead collection tools:**
```bash
python test_lead_collection.py
```

**Test CRM functionality:**
```bash
python test_crm.py
```

**Test CRM commands:**
```bash
# Test dashboard
python main.py --crm-dashboard

# Test with sample data
python main.py --csv leads.csv --limit 1 --no-ai-research --import-to-crm

# Check CRM after import
python main.py --crm-dashboard
```

### Getting Help

1. **Check logs**: Look in the `logs/` directory for error details
2. **Enable verbose mode**: Add `verbose: true` to your config
3. **Test incrementally**: Start with basic CSV, then add features
4. **Check API status**: Verify your API keys are active and have credits

## 🚀 Production Deployment

### Quick Production Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install stripe fastapi uvicorn email-validator
   ```

2. **Set production environment variables**:
   ```bash
   export STRIPE_SECRET_KEY="sk_live_..."
   export STRIPE_WEBHOOK_SECRET="whsec_..."
   export OPENAI_API_KEY="sk-..."
   ```

3. **Start the production server**:
   ```bash
   # Using gunicorn for production
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_server:app --bind 0.0.0.0:8000
   
   # Or simple uvicorn
   python api_server.py
   ```

4. **Configure Stripe webhooks**:
   - Webhook URL: `https://your-domain.com/payment/webhook`
   - Events: `checkout.session.completed`, `invoice.payment_succeeded`, `customer.subscription.deleted`

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install stripe fastapi uvicorn email-validator

COPY . .

EXPOSE 8000
CMD ["python", "api_server.py"]
```

### Environment Variables

```bash
# Required for payment system
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Required for AI features
OPENAI_API_KEY=sk-...

# Optional integrations
SNOV_CLIENT_ID=...
SNOV_CLIENT_SECRET=...
SERPAPI_KEY=...
```

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Contributing

To extend the agent:

1. **Add new lead sources**: Extend `LeadManager` class
2. **Add new email templates**: Modify `config.yaml` and `EmailGenerator`
3. **Add new personalization logic**: Extend the research and generation methods
4. **Add new output formats**: Extend the save methods in `EmailGenerator`

## License

This project is open source. Feel free to modify and distribute according to your needs.
