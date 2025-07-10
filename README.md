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
   OPENAI_API_KEY=your_openai_api_key_here
   SNOV_API_KEY=your_snov_api_key_here  # Optional
   SERPAPI_KEY=your_serpapi_key_here    # Optional - for search-based collection
   ```

4. **Validate your setup:**
   Run the validation script to ensure everything is configured correctly:
   ```bash
   python test_setup.py
   ```

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

**Show available tools and capabilities:**

```bash
python main.py --tool-capabilities
```

**Intelligently process Sales Navigator export:**

```bash
python main.py --collect-leads --sales-nav-csv your_export.csv
```

**Scrape LinkedIn profiles (requires Playwright):**

```bash
python main.py --collect-leads --linkedin-urls https://linkedin.com/in/profile1 https://linkedin.com/in/profile2
```

**Search-based lead collection (requires SerpAPI):**

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

**Common Issues:**

1. **Missing API Key**: Ensure `OPENAI_API_KEY` is set in `.env`
2. **CSV Format Error**: Check that required columns are present
3. **Rate Limit Errors**: Increase delays in `config.yaml`
4. **Snov.io API Errors**: Verify your API key and check rate limits

**Debug Mode:**
Set `verbose: true` in the agent configuration for detailed logging.

## Contributing

To extend the agent:

1. **Add new lead sources**: Extend `LeadManager` class
2. **Add new email templates**: Modify `config.yaml` and `EmailGenerator`
3. **Add new personalization logic**: Extend the research and generation methods
4. **Add new output formats**: Extend the save methods in `EmailGenerator`

## License

This project is open source. Feel free to modify and distribute according to your needs.
