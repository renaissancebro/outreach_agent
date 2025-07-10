# Outreach Agent Payment System Deployment Guide

## Overview

The Outreach Agent now includes a complete Stripe payment integration with tiered access control. This guide covers deploying the payment system for production use.

## Architecture

### Components

1. **CLI Application** (`main.py`) - Command-line interface with authentication
2. **FastAPI Server** (`api_server.py`) - REST API with payment endpoints
3. **Payment System** (`payment_system.py`) - Stripe integration and license management
4. **Authentication Middleware** (`auth_middleware.py`) - CLI and API authentication
5. **SQLite Database** (`payments.db`) - License and usage tracking

### Tiers

- **Free**: 50 emails/month, basic features, no AI research
- **Pro**: $49/month, 1,000 emails/month, AI research, CRM dashboard, API integrations
- **Enterprise**: $199/month, 10,000 emails/month, all features, priority support

## Setup Instructions

### 1. Install Dependencies

```bash
pip install stripe fastapi uvicorn email-validator
```

### 2. Configure Stripe

1. Create a Stripe account at https://stripe.com
2. Get your API keys from the Stripe dashboard
3. Set environment variables:

```bash
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."
```

### 3. Initialize Database

```bash
python -c "from payment_system import PaymentDatabase; PaymentDatabase()"
```

### 4. Start the API Server

```bash
python api_server.py
```

The server will start on `http://localhost:8000`

## API Endpoints

### Public Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /pricing` - Pricing information
- `GET /landing` - Landing page with checkout
- `POST /free/generate-sample` - Free sample email generation

### Authentication Required

- `GET /auth/validate` - Validate license key
- `POST /emails/generate` - Generate emails (requires license)
- `GET /crm/dashboard` - CRM dashboard (Pro/Enterprise)
- `GET /crm/contacts` - Search contacts (Pro/Enterprise)
- `POST /integrations/sheets/sync` - Google Sheets sync (Pro/Enterprise)

### Payment Endpoints

- `POST /payment/checkout` - Create Stripe checkout session
- `POST /payment/webhook` - Handle Stripe webhooks

## CLI Commands

### License Management

```bash
# Show current license info
python main.py --license-info

# Set license key
python main.py --set-license "OUTREACH-XXXX-XXXX-XXXX-XXXX"

# Remove license key
python main.py --remove-license
```

### Feature Access

All premium features are automatically gated based on license tier:

- AI research requires Pro/Enterprise license
- CRM dashboard requires Pro/Enterprise license
- API integrations require Pro/Enterprise license
- Google Sheets sync requires Pro/Enterprise license

## Stripe Configuration

### Products and Prices

You need to create these products in your Stripe dashboard:

1. **Outreach Agent Pro**
   - Price: $49/month
   - ID: `price_pro_monthly`

2. **Outreach Agent Enterprise**
   - Price: $199/month
   - ID: `price_enterprise_monthly`

### Webhooks

Configure webhook endpoint: `https://your-domain.com/payment/webhook`

Required events:
- `checkout.session.completed`
- `invoice.payment_succeeded`
- `customer.subscription.deleted`

## Production Deployment

### 1. Environment Variables

```bash
# Required
export STRIPE_SECRET_KEY="sk_live_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."
export OPENAI_API_KEY="sk-..."

# Optional
export SNOV_CLIENT_ID="..."
export SNOV_CLIENT_SECRET="..."
export SERPAPI_KEY="..."
```

### 2. Database Setup

For production, consider using PostgreSQL instead of SQLite:

```bash
# Update payment_system.py to use PostgreSQL
# pip install psycopg2-binary
```

### 3. Deploy with Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "api_server.py"]
```

### 4. Use a Process Manager

```bash
# Using gunicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_server:app

# Or using systemd
sudo systemctl enable outreach-agent
sudo systemctl start outreach-agent
```

## Testing

### 1. Test Payment Flow

```bash
# Test license creation
python -c "
from payment_system import PaymentDatabase, LicenseManager, SubscriptionTier
db = PaymentDatabase()
lm = LicenseManager(db)
license = lm.create_license_for_payment('test@example.com', SubscriptionTier.PRO)
print(f'License: {license.license_key}')
"

# Test CLI authentication
python main.py --set-license "OUTREACH-XXXX-XXXX-XXXX-XXXX"
python main.py --license-info
```

### 2. Test API Endpoints

```bash
# Test health
curl http://localhost:8000/health

# Test pricing
curl http://localhost:8000/pricing

# Test authentication
curl -H "Authorization: Bearer YOUR_LICENSE_KEY" http://localhost:8000/auth/validate
```

### 3. Test Stripe Integration

1. Use Stripe's test card: `4242 4242 4242 4242`
2. Test checkout flow via landing page
3. Verify webhook delivery in Stripe dashboard

## Monitoring

### 1. Usage Tracking

Monitor usage patterns:

```python
from payment_system import PaymentDatabase

db = PaymentDatabase()
stats = db.get_usage_stats("LICENSE_KEY")
print(f"Usage: {stats}")
```

### 2. Revenue Tracking

Track revenue and subscriptions via Stripe dashboard.

### 3. Error Monitoring

Set up error tracking for webhook failures and authentication issues.

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Webhook Signatures**: Always verify webhook signatures
3. **Rate Limiting**: Implement rate limiting on public endpoints
4. **HTTPS**: Use HTTPS in production
5. **Input Validation**: Validate all user inputs

## Troubleshooting

### Common Issues

1. **License validation fails**: Check database path consistency
2. **Webhook failures**: Verify webhook signature and endpoint URL
3. **Payment processing errors**: Check Stripe logs
4. **Authentication errors**: Verify license key format and expiration

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For deployment support:
- Check logs in `logs/` directory
- Monitor Stripe dashboard for payment issues
- Review API server logs for authentication problems

## Next Steps

1. Set up production Stripe account
2. Configure custom domain
3. Set up monitoring and alerting
4. Add additional payment methods
5. Implement team management features