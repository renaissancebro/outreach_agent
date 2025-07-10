"""
FastAPI Server for Outreach Agent SaaS

This module provides:
- REST API endpoints for all outreach functionality
- Authentication and authorization middleware
- Stripe payment integration endpoints
- Rate limiting and usage tracking
- License key validation
- Tiered access control
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Header, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional, Any
import os
import json
import asyncio
from datetime import datetime
import logging
import stripe
from contextlib import asynccontextmanager

# Local imports
from payment_system import (
    PaymentDatabase, LicenseManager, StripePaymentProcessor,
    SubscriptionTier, get_tier_config, get_pricing_info,
    TIER_CONFIGS, PRICING_CONFIG
)
from main import EnhancedOutreachAgent
from lead_manager import Lead
from crm_system import CRMContact, LeadStatus

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize payment system
payment_db = PaymentDatabase()
license_manager = LicenseManager(payment_db)

# Initialize Stripe
stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
stripe_processor = None

if stripe_secret_key and stripe_webhook_secret:
    stripe_processor = StripePaymentProcessor(
        stripe_secret_key, stripe_webhook_secret, license_manager
    )
    logger.info("Stripe integration initialized")
else:
    logger.warning("Stripe credentials not found - payment features disabled")

# Security
security = HTTPBearer()

# Pydantic models
class EmailGenerationRequest(BaseModel):
    leads: List[Dict[str, Any]]
    use_ai_research: bool = True
    template_override: Optional[str] = None

class LeadCollectionRequest(BaseModel):
    tool_type: str  # "playwright", "serpapi", "sales_nav"
    parameters: Dict[str, Any]
    import_to_crm: bool = True

class CRMUpdateRequest(BaseModel):
    email: str
    status: str
    notes: Optional[str] = None

class PaymentRequest(BaseModel):
    tier: str
    success_url: str
    cancel_url: str
    customer_email: Optional[EmailStr] = None

class LicenseValidationResponse(BaseModel):
    valid: bool
    license_key: str
    tier: str
    features_available: Dict[str, bool]
    usage_stats: Dict[str, int]
    rate_limits: Dict[str, int]

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    usage_consumed: Optional[int] = None

# Global outreach agent instance
outreach_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global outreach_agent
    
    # Startup
    logger.info("Starting Outreach Agent API server...")
    try:
        outreach_agent = EnhancedOutreachAgent()
        logger.info("Outreach agent initialized")
    except Exception as e:
        logger.error(f"Failed to initialize outreach agent: {e}")
        outreach_agent = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down Outreach Agent API server...")

# Initialize FastAPI app
app = FastAPI(
    title="Outreach Agent API",
    description="AI-powered outreach automation with CRM",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication dependency
async def authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Authenticate request and return license key"""
    license_key = credentials.credentials
    
    is_valid, license, message = license_manager.validate_license(license_key)
    if not is_valid:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {message}")
    
    return license_key

# Feature access dependency
def require_feature(feature_name: str):
    """Dependency to check feature access"""
    async def check_feature_access(license_key: str = Depends(authenticate)):
        can_access, message = license_manager.check_feature_access(license_key, feature_name)
        if not can_access:
            raise HTTPException(status_code=403, detail=f"Feature access denied: {message}")
        return license_key
    return check_feature_access

# Rate limiting dependency
def rate_limit(feature_name: str):
    """Dependency to check and enforce rate limits"""
    async def check_rate_limits(license_key: str = Depends(authenticate)):
        within_limits, message = license_manager.check_rate_limits(license_key, feature_name)
        if not within_limits:
            raise HTTPException(status_code=429, detail=f"Rate limit exceeded: {message}")
        
        # Record usage
        license_manager.record_feature_usage(license_key, feature_name)
        return license_key
    return check_rate_limits

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Outreach Agent API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_ready": outreach_agent is not None,
        "stripe_enabled": stripe_processor is not None
    }

# Authentication endpoints

@app.get("/auth/validate", response_model=LicenseValidationResponse)
async def validate_license_endpoint(license_key: str = Depends(authenticate)):
    """Validate license and return user information"""
    is_valid, license, message = license_manager.validate_license(license_key)
    
    if not is_valid:
        raise HTTPException(status_code=401, detail=message)
    
    tier_config = get_tier_config(license.tier)
    
    # Get usage stats
    usage_stats = payment_db.get_usage_stats(license_key)
    
    # Get available features
    features_available = {
        "ai_research": tier_config.ai_research,
        "crm_dashboard": tier_config.crm_dashboard,
        "snov_io": tier_config.snov_io_access,
        "sheets_sync": tier_config.sheets_access,
        "playwright": tier_config.playwright_access,
        "serpapi": tier_config.serpapi_access,
        "lead_collection": tier_config.lead_collection
    }
    
    return LicenseValidationResponse(
        valid=True,
        license_key=license_key,
        tier=license.tier.value,
        features_available=features_available,
        usage_stats=usage_stats,
        rate_limits={
            "emails_per_hour": tier_config.emails_per_hour,
            "api_calls_per_hour": tier_config.api_calls_per_hour,
            "monthly_emails": tier_config.monthly_emails,
            "monthly_api_calls": tier_config.monthly_api_calls
        }
    )

# Email generation endpoints

@app.post("/emails/generate", response_model=ApiResponse)
async def generate_emails(
    request: EmailGenerationRequest,
    license_key: str = Depends(rate_limit("email_generation"))
):
    """Generate personalized emails for leads"""
    if not outreach_agent:
        raise HTTPException(status_code=503, detail="Outreach agent not available")
    
    # Check AI research access
    if request.use_ai_research:
        can_access, message = license_manager.check_feature_access(license_key, "ai_research")
        if not can_access:
            # Fallback to template-based generation
            request.use_ai_research = False
            logger.info(f"AI research disabled for license {license_key}: {message}")
    
    try:
        # Convert dict leads to Lead objects
        leads = [Lead(**lead_data) for lead_data in request.leads]
        
        # Generate emails
        emails = outreach_agent.generate_emails_for_leads(leads, request.use_ai_research)
        
        return ApiResponse(
            success=True,
            data=emails,
            usage_consumed=len(leads)
        )
    
    except Exception as e:
        logger.error(f"Email generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email generation failed: {str(e)}")

# Lead collection endpoints

@app.get("/tools/capabilities")
async def get_tool_capabilities(license_key: str = Depends(authenticate)):
    """Get available lead collection tools for user's tier"""
    if not outreach_agent:
        raise HTTPException(status_code=503, detail="Outreach agent not available")
    
    # Get all capabilities
    all_capabilities = outreach_agent.get_tool_capabilities()
    
    # Filter based on user's tier
    is_valid, license, _ = license_manager.validate_license(license_key)
    tier_config = get_tier_config(license.tier)
    
    available_capabilities = []
    for cap in all_capabilities:
        # Check if user has access to this tool
        if cap.name == "Playwright Web Scraper" and tier_config.playwright_access:
            available_capabilities.append(cap)
        elif cap.name == "SerpAPI Search Collector" and tier_config.serpapi_access:
            available_capabilities.append(cap)
        elif cap.name == "Sales Navigator CSV Processor":
            available_capabilities.append(cap)  # Always available
    
    return ApiResponse(
        success=True,
        data=[cap.__dict__ for cap in available_capabilities]
    )

@app.post("/leads/collect", response_model=ApiResponse)
async def collect_leads(
    request: LeadCollectionRequest,
    license_key: str = Depends(rate_limit("lead_collection"))
):
    """Collect leads using intelligent tool selection"""
    if not outreach_agent:
        raise HTTPException(status_code=503, detail="Outreach agent not available")
    
    # Check tool access
    tool_feature_map = {
        "playwright": "playwright",
        "serpapi": "serpapi",
        "sales_nav": "lead_collection"
    }
    
    required_feature = tool_feature_map.get(request.tool_type)
    if required_feature:
        can_access, message = license_manager.check_feature_access(license_key, required_feature)
        if not can_access:
            raise HTTPException(status_code=403, detail=f"Tool access denied: {message}")
    
    try:
        # Prepare parameters for intelligent collection
        request_params = {
            'task_type': 'lead_collection',
            'input_data': request.parameters,
            'constraints': {'budget': 'free'},  # Will be overridden based on tier
            'max_leads': request.parameters.get('max_leads', 50)
        }
        
        # Collect leads
        leads = outreach_agent.collect_leads_intelligently(request_params)
        
        # Import to CRM if requested
        if request.import_to_crm and leads:
            outreach_agent.import_leads_to_crm(leads, f"api_collection_{license_key[:8]}")
        
        return ApiResponse(
            success=True,
            data=[lead.__dict__ for lead in leads],
            usage_consumed=len(leads)
        )
    
    except Exception as e:
        logger.error(f"Lead collection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Lead collection failed: {str(e)}")

# CRM endpoints

@app.get("/crm/dashboard", response_model=ApiResponse)
async def get_crm_dashboard(license_key: str = Depends(require_feature("crm_dashboard"))):
    """Get CRM dashboard statistics"""
    if not outreach_agent:
        raise HTTPException(status_code=503, detail="Outreach agent not available")
    
    try:
        stats = outreach_agent.get_crm_dashboard()
        return ApiResponse(success=True, data=stats)
    
    except Exception as e:
        logger.error(f"CRM dashboard failed: {e}")
        raise HTTPException(status_code=500, detail=f"CRM dashboard failed: {str(e)}")

@app.get("/crm/contacts", response_model=ApiResponse)
async def search_contacts(
    query: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    license_key: str = Depends(require_feature("crm_dashboard"))
):
    """Search CRM contacts"""
    if not outreach_agent:
        raise HTTPException(status_code=503, detail="Outreach agent not available")
    
    try:
        contacts = outreach_agent.search_crm_contacts(query=query, status=status)
        
        # Convert to serializable format
        contacts_data = []
        for contact in contacts[:limit]:
            contact_dict = contact.__dict__.copy()
            contact_dict['status'] = contact.status.value
            contacts_data.append(contact_dict)
        
        return ApiResponse(success=True, data=contacts_data)
    
    except Exception as e:
        logger.error(f"Contact search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Contact search failed: {str(e)}")

@app.put("/crm/contacts/status", response_model=ApiResponse)
async def update_contact_status(
    request: CRMUpdateRequest,
    license_key: str = Depends(require_feature("crm_dashboard"))
):
    """Update contact status in CRM"""
    if not outreach_agent:
        raise HTTPException(status_code=503, detail="Outreach agent not available")
    
    try:
        success = outreach_agent.update_contact_status(request.email, request.status, request.notes)
        
        if not success:
            raise HTTPException(status_code=404, detail="Contact not found or status invalid")
        
        return ApiResponse(success=True, data={"updated": True})
    
    except Exception as e:
        logger.error(f"Status update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status update failed: {str(e)}")

@app.get("/crm/export", response_model=ApiResponse)
async def export_crm_data(license_key: str = Depends(require_feature("crm_dashboard"))):
    """Export CRM data to CSV"""
    if not outreach_agent:
        raise HTTPException(status_code=503, detail="Outreach agent not available")
    
    try:
        filename = outreach_agent.export_crm_data("csv")
        return ApiResponse(success=True, data={"filename": filename})
    
    except Exception as e:
        logger.error(f"CRM export failed: {e}")
        raise HTTPException(status_code=500, detail=f"CRM export failed: {str(e)}")

# Google Sheets integration

@app.post("/integrations/sheets/sync", response_model=ApiResponse)
async def sync_to_sheets(
    sheet_id: str,
    worksheet_name: str = "CRM Data",
    license_key: str = Depends(require_feature("sheets_sync"))
):
    """Sync CRM data to Google Sheets"""
    if not outreach_agent:
        raise HTTPException(status_code=503, detail="Outreach agent not available")
    
    try:
        success = outreach_agent.sync_crm_to_google_sheets(sheet_id, worksheet_name)
        
        if not success:
            raise HTTPException(status_code=500, detail="Google Sheets sync failed")
        
        return ApiResponse(success=True, data={"synced": True})
    
    except Exception as e:
        logger.error(f"Sheets sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sheets sync failed: {str(e)}")

# Payment endpoints

@app.get("/pricing")
async def get_pricing():
    """Get pricing information for all tiers"""
    return {
        "tiers": {tier.value: get_pricing_info(tier) for tier in SubscriptionTier},
        "currency": "USD"
    }

@app.post("/payment/checkout", response_model=ApiResponse)
async def create_checkout_session(request: PaymentRequest):
    """Create Stripe checkout session"""
    if not stripe_processor:
        raise HTTPException(status_code=503, detail="Payment processing not available")
    
    try:
        tier = SubscriptionTier(request.tier)
        
        if tier == SubscriptionTier.FREE:
            raise HTTPException(status_code=400, detail="Free tier doesn't require payment")
        
        checkout_data = stripe_processor.create_checkout_session(
            tier=tier,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            customer_email=request.customer_email
        )
        
        return ApiResponse(success=True, data=checkout_data)
    
    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Checkout creation failed: {str(e)}")

@app.post("/payment/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    if not stripe_processor:
        raise HTTPException(status_code=503, detail="Payment processing not available")
    
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")
    
    try:
        result = stripe_processor.handle_webhook(payload.decode(), signature)
        return result
    
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

# Free tier endpoints (no authentication required)

@app.post("/free/generate-sample", response_model=ApiResponse)
async def generate_sample_email():
    """Generate a sample email (no authentication required)"""
    if not outreach_agent:
        raise HTTPException(status_code=503, detail="Outreach agent not available")
    
    # Create sample lead
    sample_lead = Lead(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        company_name="Example Corp",
        position="CEO",
        industry="Technology"
    )
    
    try:
        # Generate template-based email (no AI research)
        emails = outreach_agent.generate_emails_for_leads([sample_lead], use_ai_research=False)
        
        return ApiResponse(
            success=True,
            data=emails[0] if emails else None,
            usage_consumed=0  # Free sample
        )
    
    except Exception as e:
        logger.error(f"Sample email generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sample generation failed: {str(e)}")

# Landing page

@app.get("/landing", response_class=HTMLResponse)
async def landing_page():
    """Simple landing page with pricing and call-to-action"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Outreach Agent - AI-Powered Sales Automation</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; }}
            .hero {{ text-align: center; margin-bottom: 60px; }}
            .hero h1 {{ font-size: 3em; color: #333; margin-bottom: 20px; }}
            .hero p {{ font-size: 1.2em; color: #666; }}
            .pricing {{ display: flex; justify-content: space-around; gap: 30px; margin: 40px 0; }}
            .plan {{ border: 2px solid #ddd; border-radius: 10px; padding: 30px; text-align: center; flex: 1; }}
            .plan.featured {{ border-color: #007bff; background: #f8f9ff; }}
            .plan h3 {{ font-size: 1.5em; margin-bottom: 20px; }}
            .plan .price {{ font-size: 2em; color: #007bff; margin-bottom: 20px; }}
            .plan ul {{ text-align: left; margin: 20px 0; }}
            .plan button {{ background: #007bff; color: white; border: none; padding: 15px 30px; border-radius: 5px; cursor: pointer; font-size: 1.1em; }}
            .plan button:hover {{ background: #0056b3; }}
            .features {{ margin: 40px 0; }}
            .features h2 {{ text-align: center; margin-bottom: 30px; }}
            .feature-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }}
            .feature {{ padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="hero">
                <h1>🤖 Outreach Agent</h1>
                <p>AI-powered sales automation with comprehensive CRM</p>
                <p>Generate personalized emails, collect leads, and manage your entire sales pipeline</p>
                <button onclick="generateSample()" style="background: #28a745; color: white; border: none; padding: 15px 30px; border-radius: 5px; cursor: pointer; font-size: 1.1em; margin: 20px;">
                    Try Free Sample Email
                </button>
            </div>
            
            <div class="pricing">
                <div class="plan">
                    <h3>Free</h3>
                    <div class="price">$0<small>/forever</small></div>
                    <ul>
                        <li>50 emails/month</li>
                        <li>Basic CSV processing</li>
                        <li>Template emails</li>
                        <li>Web scraping</li>
                        <li>1 team seat</li>
                    </ul>
                    <button onclick="alert('Free tier - no payment required! Get started with the CLI.')">Get Started</button>
                </div>
                
                <div class="plan featured">
                    <h3>Pro</h3>
                    <div class="price">$49<small>/month</small></div>
                    <ul>
                        <li>1,000 emails/month</li>
                        <li>🔥 AI-powered research</li>
                        <li>🔥 Full CRM dashboard</li>
                        <li>🔥 API integrations</li>
                        <li>🔥 Google Sheets sync</li>
                        <li>Priority support</li>
                        <li>5 team seats</li>
                    </ul>
                    <button onclick="startCheckout('pro')">Start Pro Trial</button>
                </div>
                
                <div class="plan">
                    <h3>Enterprise</h3>
                    <div class="price">$199<small>/month</small></div>
                    <ul>
                        <li>10,000 emails/month</li>
                        <li>All Pro features</li>
                        <li>Advanced analytics</li>
                        <li>Custom integrations</li>
                        <li>Dedicated support</li>
                        <li>50 team seats</li>
                    </ul>
                    <button onclick="startCheckout('enterprise')">Contact Sales</button>
                </div>
            </div>
            
            <div class="features">
                <h2>🚀 Key Features</h2>
                <div class="feature-grid">
                    <div class="feature">
                        <h3>🤖 AI-Powered Research</h3>
                        <p>CrewAI agents research companies and generate personalized emails with industry-specific insights</p>
                    </div>
                    <div class="feature">
                        <h3>📊 Complete CRM</h3>
                        <p>Track your entire sales pipeline from lead collection to closed deals with interaction history</p>
                    </div>
                    <div class="feature">
                        <h3>🔍 Smart Lead Collection</h3>
                        <p>AI chooses the best tool for lead collection - LinkedIn scraping, search APIs, or CSV processing</p>
                    </div>
                    <div class="feature">
                        <h3>🔗 Team Collaboration</h3>
                        <p>Google Sheets integration for real-time team pipeline visibility and data sharing</p>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 60px; padding: 40px; background: #f8f9fa; border-radius: 10px;">
                <h2>Ready to automate your outreach?</h2>
                <p>Join hundreds of sales teams using Outreach Agent to generate more leads and close more deals</p>
                <button onclick="startCheckout('pro')" style="background: #007bff; color: white; border: none; padding: 20px 40px; border-radius: 5px; cursor: pointer; font-size: 1.2em;">
                    Start Your Free Trial
                </button>
            </div>
        </div>
        
        <script>
        async function generateSample() {{
            try {{
                const response = await fetch('/free/generate-sample', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }}
                }});
                const result = await response.json();
                
                if (result.success) {{
                    alert('Sample Email Generated:\\n\\nSubject: ' + result.data.subject + '\\n\\n' + result.data.body);
                }} else {{
                    alert('Error generating sample: ' + result.error);
                }}
            }} catch (error) {{
                alert('Error: ' + error.message);
            }}
        }}
        
        async function startCheckout(tier) {{
            if (tier === 'enterprise') {{
                alert('Contact us for Enterprise pricing: sales@outreachagent.com');
                return;
            }}
            
            try {{
                const response = await fetch('/payment/checkout', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        tier: tier,
                        success_url: window.location.origin + '/success',
                        cancel_url: window.location.origin + '/landing'
                    }})
                }});
                
                const result = await response.json();
                
                if (result.success) {{
                    window.location.href = result.data.checkout_url;
                }} else {{
                    alert('Error starting checkout: ' + result.error);
                }}
            }} catch (error) {{
                alert('Error: ' + error.message);
            }}
        }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/success", response_class=HTMLResponse)
async def success_page():
    """Payment success page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Successful - Outreach Agent</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; }
            .success { color: #28a745; font-size: 3em; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">✅</div>
            <h1>Payment Successful!</h1>
            <p>Thank you for subscribing to Outreach Agent Pro!</p>
            <p>Your license key has been sent to your email address.</p>
            <p>You can now use all Pro features including AI research, CRM dashboard, and API integrations.</p>
            <p><strong>Next steps:</strong></p>
            <ol style="text-align: left; max-width: 400px; margin: 20px auto;">
                <li>Check your email for the license key</li>
                <li>Set up the CLI tool with your license</li>
                <li>Start your first campaign</li>
            </ol>
            <p>Need help? Contact support at: support@outreachagent.com</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return {
        "success": False,
        "error": exc.detail,
        "status_code": exc.status_code
    }

if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )