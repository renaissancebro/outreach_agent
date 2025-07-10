# Enhanced Outreach Agent

A powerful, configurable outreach agent that generates personalized cold emails using CrewAI, with support for CSV leads and Snov.io API integration.

## Features

- **YAML Configuration**: Easy-to-modify configuration file for all settings
- **Multiple Lead Sources**: Support for CSV files and Snov.io API
- **AI-Powered Research**: Uses CrewAI agents for company research and email generation
- **Template-Based Fallback**: Template system for when AI research is disabled
- **Lead Enrichment**: Automatically enrich leads with additional data from Snov.io
- **Rate Limiting**: Built-in rate limiting for API calls
- **Multiple Output Formats**: JSON, text, and markdown output options
- **Personalization Levels**: Low, medium, and high research depth options
- **🆕 Intelligent Lead Collection**: AI-powered tool selection for optimal lead gathering
- **🆕 Playwright Web Scraping**: Automated scraping of LinkedIn profiles and company websites
- **🆕 SerpAPI Integration**: Search-based lead collection using Google search results
- **🆕 Enhanced Sales Navigator Support**: Advanced CSV processing with data enrichment

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

| Feature | OpenAI | Snov.io | SerpAPI | Notes |
|---------|--------|---------|---------|-------|
| Basic CSV email generation | ✅ | ❌ | ❌ | Core functionality |
| AI research & personalization | ✅ | ❌ | ❌ | Enhanced emails |
| Lead enrichment | ✅ | ✅ | ❌ | Better lead data |
| Sales Navigator processing | ✅ | ✅ | ❌ | Enhanced CSV processing |
| Web scraping (Playwright) | ✅ | ❌ | ❌ | Free web scraping |
| Search-based lead collection | ✅ | ❌ | ✅ | Find new prospects |
| Company research | ✅ | ✅ | ✅ | Maximum capability |

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

**All APIs Together:**
- ✅ Maximum capability and accuracy
- ✅ Intelligent tool selection with all options
- ✅ Comprehensive lead collection pipeline
- ✅ Automated fallback between tools
- ✅ Enterprise-grade lead generation

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

**Test with sample data:**
```bash
python main.py --csv leads.csv --limit 1 --no-ai-research
```

### Getting Help

1. **Check logs**: Look in the `logs/` directory for error details
2. **Enable verbose mode**: Add `verbose: true` to your config
3. **Test incrementally**: Start with basic CSV, then add features
4. **Check API status**: Verify your API keys are active and have credits

## Contributing

To extend the agent:

1. **Add new lead sources**: Extend `LeadManager` class
2. **Add new email templates**: Modify `config.yaml` and `EmailGenerator`
3. **Add new personalization logic**: Extend the research and generation methods
4. **Add new output formats**: Extend the save methods in `EmailGenerator`

## License

This project is open source. Feel free to modify and distribute according to your needs.
