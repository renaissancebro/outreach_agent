"""
Stripe Payment Integration for Outreach Agent

This module provides:
- Tiered access control system (Free, Pro, Enterprise)
- Stripe payment processing with webhooks
- License key generation and management
- Usage tracking and rate limiting
- API authentication for CLI and web access
"""

import os
import stripe
import sqlite3
import secrets
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SubscriptionTier(Enum):
    """Subscription tiers with access levels"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class FeatureAccess(Enum):
    """Feature access levels"""
    BLOCKED = "blocked"
    LIMITED = "limited"
    UNLIMITED = "unlimited"


@dataclass
class TierLimits:
    """Limits for each subscription tier"""
    tier: SubscriptionTier
    monthly_emails: int
    monthly_api_calls: int
    ai_research: bool
    crm_dashboard: bool
    snov_io_access: bool
    sheets_access: bool
    playwright_access: bool
    serpapi_access: bool
    lead_collection: bool
    priority_support: bool
    team_seats: int
    
    # Rate limits (per hour)
    emails_per_hour: int
    api_calls_per_hour: int


# Define tier configurations
TIER_CONFIGS = {
    SubscriptionTier.FREE: TierLimits(
        tier=SubscriptionTier.FREE,
        monthly_emails=50,
        monthly_api_calls=100,
        ai_research=False,  # 🔒 LOCKED
        crm_dashboard=False,  # 🔒 LOCKED
        snov_io_access=False,  # 🔒 LOCKED
        sheets_access=False,  # 🔒 LOCKED
        playwright_access=True,  # Basic web scraping allowed
        serpapi_access=False,  # 🔒 LOCKED
        lead_collection=True,  # Basic CSV processing only
        priority_support=False,
        team_seats=1,
        emails_per_hour=10,
        api_calls_per_hour=20
    ),
    SubscriptionTier.PRO: TierLimits(
        tier=SubscriptionTier.PRO,
        monthly_emails=1000,
        monthly_api_calls=5000,
        ai_research=True,  # ✅ UNLOCKED
        crm_dashboard=True,  # ✅ UNLOCKED
        snov_io_access=True,  # ✅ UNLOCKED
        sheets_access=True,  # ✅ UNLOCKED
        playwright_access=True,
        serpapi_access=True,  # ✅ UNLOCKED
        lead_collection=True,
        priority_support=True,
        team_seats=5,
        emails_per_hour=100,
        api_calls_per_hour=500
    ),
    SubscriptionTier.ENTERPRISE: TierLimits(
        tier=SubscriptionTier.ENTERPRISE,
        monthly_emails=10000,
        monthly_api_calls=50000,
        ai_research=True,
        crm_dashboard=True,
        snov_io_access=True,
        sheets_access=True,
        playwright_access=True,
        serpapi_access=True,
        lead_collection=True,
        priority_support=True,
        team_seats=50,
        emails_per_hour=1000,
        api_calls_per_hour=5000
    )
}


@dataclass
class License:
    """License key with associated subscription"""
    license_key: str
    user_email: str
    tier: SubscriptionTier
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    created_at: str
    expires_at: Optional[str]
    is_active: bool
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UsageRecord:
    """Usage tracking record"""
    id: str
    license_key: str
    feature: str
    timestamp: str
    count: int = 1
    metadata: Dict = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.metadata is None:
            self.metadata = {}


class PaymentDatabase:
    """SQLite database for payment and license management"""
    
    def __init__(self, db_path: str = "payments.db"):
        # Use a consistent database path for the payment system
        if db_path == "payments.db":
            # Create database in current directory for consistency
            db_path = os.path.join(os.getcwd(), "payments.db")
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize payment database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Licenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                license_key TEXT PRIMARY KEY,
                user_email TEXT NOT NULL,
                tier TEXT NOT NULL,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                is_active BOOLEAN DEFAULT 1,
                metadata TEXT
            )
        """)
        
        # Usage tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_records (
                id TEXT PRIMARY KEY,
                license_key TEXT NOT NULL,
                feature TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                metadata TEXT,
                FOREIGN KEY (license_key) REFERENCES licenses (license_key)
            )
        """)
        
        # Payment events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_events (
                id TEXT PRIMARY KEY,
                stripe_event_id TEXT UNIQUE,
                event_type TEXT NOT NULL,
                customer_id TEXT,
                subscription_id TEXT,
                amount INTEGER,
                currency TEXT,
                timestamp TEXT NOT NULL,
                processed BOOLEAN DEFAULT 0,
                metadata TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_license(self, license: License) -> str:
        """Create a new license"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO licenses (
                license_key, user_email, tier, stripe_customer_id, stripe_subscription_id,
                created_at, expires_at, is_active, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            license.license_key, license.user_email, license.tier.value,
            license.stripe_customer_id, license.stripe_subscription_id,
            license.created_at, license.expires_at, license.is_active,
            json.dumps(license.metadata)
        ))
        
        conn.commit()
        conn.close()
        return license.license_key
    
    def get_license(self, license_key: str) -> Optional[License]:
        """Get license by key"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return License(
                license_key=row['license_key'],
                user_email=row['user_email'],
                tier=SubscriptionTier(row['tier']),
                stripe_customer_id=row['stripe_customer_id'],
                stripe_subscription_id=row['stripe_subscription_id'],
                created_at=row['created_at'],
                expires_at=row['expires_at'],
                is_active=bool(row['is_active']),
                metadata=json.loads(row['metadata'] or '{}')
            )
        return None
    
    def update_license_status(self, license_key: str, is_active: bool):
        """Update license active status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE licenses SET is_active = ? WHERE license_key = ?",
            (is_active, license_key)
        )
        
        conn.commit()
        conn.close()
    
    def record_usage(self, usage: UsageRecord):
        """Record usage for billing and rate limiting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO usage_records (id, license_key, feature, timestamp, count, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            usage.id, usage.license_key, usage.feature, usage.timestamp,
            usage.count, json.dumps(usage.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    def get_usage_stats(self, license_key: str, feature: str = None, 
                       start_date: str = None, end_date: str = None) -> Dict:
        """Get usage statistics for a license"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT feature, SUM(count) as total FROM usage_records WHERE license_key = ?"
        params = [license_key]
        
        if feature:
            query += " AND feature = ?"
            params.append(feature)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " GROUP BY feature"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return {row[0]: row[1] for row in results}


class LicenseManager:
    """Manages license generation and validation"""
    
    def __init__(self, db: PaymentDatabase):
        self.db = db
    
    def generate_license_key(self) -> str:
        """Generate a unique license key"""
        # Format: OUTREACH-XXXX-XXXX-XXXX-XXXX
        parts = []
        for _ in range(4):
            part = secrets.token_hex(2).upper()
            parts.append(part)
        
        return f"OUTREACH-{'-'.join(parts)}"
    
    def create_license_for_payment(self, user_email: str, tier: SubscriptionTier,
                                 stripe_customer_id: str = None,
                                 stripe_subscription_id: str = None) -> License:
        """Create a new license for a paid user"""
        license_key = self.generate_license_key()
        
        # Calculate expiration based on tier
        expires_at = None
        if tier != SubscriptionTier.ENTERPRISE:  # Enterprise has no expiration
            expires_at = (datetime.now() + timedelta(days=30)).isoformat()
        
        license = License(
            license_key=license_key,
            user_email=user_email,
            tier=tier,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            created_at=datetime.now().isoformat(),
            expires_at=expires_at,
            is_active=True,
            metadata={"created_via": "stripe_payment"}
        )
        
        self.db.create_license(license)
        logger.info(f"Created license {license_key} for {user_email} ({tier.value})")
        
        return license
    
    def validate_license(self, license_key: str) -> Tuple[bool, Optional[License], str]:
        """Validate a license key and return status"""
        if not license_key:
            return False, None, "No license key provided"
        
        license = self.db.get_license(license_key)
        if not license:
            return False, None, "Invalid license key"
        
        if not license.is_active:
            return False, license, "License is inactive"
        
        # Check expiration
        if license.expires_at:
            expires = datetime.fromisoformat(license.expires_at)
            if datetime.now() > expires:
                return False, license, "License has expired"
        
        return True, license, "Valid license"
    
    def check_feature_access(self, license_key: str, feature: str) -> Tuple[bool, str]:
        """Check if a license has access to a specific feature"""
        is_valid, license, message = self.validate_license(license_key)
        
        if not is_valid:
            return False, message
        
        tier_config = TIER_CONFIGS[license.tier]
        
        # Check feature-specific access
        feature_access = {
            "ai_research": tier_config.ai_research,
            "crm_dashboard": tier_config.crm_dashboard,
            "snov_io": tier_config.snov_io_access,
            "sheets_sync": tier_config.sheets_access,
            "playwright": tier_config.playwright_access,
            "serpapi": tier_config.serpapi_access,
            "lead_collection": tier_config.lead_collection
        }
        
        if feature not in feature_access:
            return False, f"Unknown feature: {feature}"
        
        if not feature_access[feature]:
            return False, f"Feature '{feature}' not available in {license.tier.value} tier"
        
        return True, "Access granted"
    
    def check_rate_limits(self, license_key: str, feature: str) -> Tuple[bool, str]:
        """Check if user has exceeded rate limits"""
        is_valid, license, message = self.validate_license(license_key)
        
        if not is_valid:
            return False, message
        
        tier_config = TIER_CONFIGS[license.tier]
        
        # Check hourly limits
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        current_hour_usage = self.db.get_usage_stats(
            license_key, feature, one_hour_ago
        )
        
        hourly_usage = current_hour_usage.get(feature, 0)
        
        if feature == "email_generation":
            if hourly_usage >= tier_config.emails_per_hour:
                return False, f"Hourly email limit reached ({tier_config.emails_per_hour})"
        else:
            if hourly_usage >= tier_config.api_calls_per_hour:
                return False, f"Hourly API limit reached ({tier_config.api_calls_per_hour})"
        
        # Check monthly limits
        month_ago = (datetime.now() - timedelta(days=30)).isoformat()
        monthly_usage = self.db.get_usage_stats(
            license_key, feature, month_ago
        )
        
        monthly_total = monthly_usage.get(feature, 0)
        
        if feature == "email_generation":
            if monthly_total >= tier_config.monthly_emails:
                return False, f"Monthly email limit reached ({tier_config.monthly_emails})"
        else:
            if monthly_total >= tier_config.monthly_api_calls:
                return False, f"Monthly API limit reached ({tier_config.monthly_api_calls})"
        
        return True, "Within limits"
    
    def record_feature_usage(self, license_key: str, feature: str, count: int = 1, 
                           metadata: Dict = None):
        """Record usage of a feature"""
        usage = UsageRecord(
            id=str(uuid.uuid4()),
            license_key=license_key,
            feature=feature,
            timestamp=datetime.now().isoformat(),
            count=count,
            metadata=metadata or {}
        )
        
        self.db.record_usage(usage)


class StripePaymentProcessor:
    """Handles Stripe payment processing and webhooks"""
    
    def __init__(self, stripe_secret_key: str, webhook_secret: str, license_manager: LicenseManager):
        stripe.api_key = stripe_secret_key
        self.webhook_secret = webhook_secret
        self.license_manager = license_manager
        self.db = license_manager.db
    
    def create_checkout_session(self, tier: SubscriptionTier, success_url: str, 
                              cancel_url: str, customer_email: str = None) -> Dict:
        """Create a Stripe checkout session"""
        
        # Define pricing for each tier
        price_mapping = {
            SubscriptionTier.PRO: {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "Outreach Agent Pro",
                        "description": "AI research, CRM dashboard, API integrations"
                    },
                    "unit_amount": 4900,  # $49/month
                    "recurring": {"interval": "month"}
                }
            },
            SubscriptionTier.ENTERPRISE: {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "Outreach Agent Enterprise",
                        "description": "Unlimited access, priority support, team features"
                    },
                    "unit_amount": 19900,  # $199/month
                    "recurring": {"interval": "month"}
                }
            }
        }
        
        if tier not in price_mapping:
            raise ValueError(f"No pricing configured for tier: {tier}")
        
        session_params = {
            "line_items": [price_mapping[tier]],
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {
                "tier": tier.value,
                "customer_email": customer_email or ""
            }
        }
        
        if customer_email:
            session_params["customer_email"] = customer_email
        
        session = stripe.checkout.Session.create(**session_params)
        
        logger.info(f"Created checkout session {session.id} for {tier.value}")
        return {
            "session_id": session.id,
            "checkout_url": session.url
        }
    
    def handle_webhook(self, payload: str, signature: str) -> Dict:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
        except ValueError:
            logger.error("Invalid payload in webhook")
            return {"status": "error", "message": "Invalid payload"}
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature in webhook")
            return {"status": "error", "message": "Invalid signature"}
        
        logger.info(f"Received webhook event: {event['type']}")
        
        # Handle different event types
        if event["type"] == "checkout.session.completed":
            return self._handle_checkout_completed(event["data"]["object"])
        elif event["type"] == "invoice.payment_succeeded":
            return self._handle_payment_succeeded(event["data"]["object"])
        elif event["type"] == "customer.subscription.deleted":
            return self._handle_subscription_cancelled(event["data"]["object"])
        else:
            logger.info(f"Unhandled event type: {event['type']}")
            return {"status": "ignored", "message": f"Event type {event['type']} not handled"}
    
    def _handle_checkout_completed(self, session) -> Dict:
        """Handle completed checkout session"""
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        customer_email = session.get("customer_email")
        tier_str = session.get("metadata", {}).get("tier")
        
        if not tier_str:
            logger.error("No tier information in checkout session")
            return {"status": "error", "message": "Missing tier information"}
        
        try:
            tier = SubscriptionTier(tier_str)
        except ValueError:
            logger.error(f"Invalid tier: {tier_str}")
            return {"status": "error", "message": "Invalid tier"}
        
        # Create license
        license = self.license_manager.create_license_for_payment(
            user_email=customer_email,
            tier=tier,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id
        )
        
        logger.info(f"Created license {license.license_key} for completed checkout")
        
        # TODO: Send license key via email
        # self._send_license_email(customer_email, license.license_key)
        
        return {
            "status": "success",
            "message": "License created",
            "license_key": license.license_key
        }
    
    def _handle_payment_succeeded(self, invoice) -> Dict:
        """Handle successful recurring payment"""
        subscription_id = invoice.get("subscription")
        
        # Reactivate license if it was suspended
        # This would require looking up license by subscription_id
        # For now, just log the event
        logger.info(f"Payment succeeded for subscription {subscription_id}")
        
        return {"status": "success", "message": "Payment processed"}
    
    def _handle_subscription_cancelled(self, subscription) -> Dict:
        """Handle cancelled subscription"""
        subscription_id = subscription.get("id")
        
        # Deactivate associated license
        # This would require looking up license by subscription_id
        # For now, just log the event
        logger.info(f"Subscription cancelled: {subscription_id}")
        
        return {"status": "success", "message": "Subscription cancelled"}


# Pricing configuration
PRICING_CONFIG = {
    SubscriptionTier.FREE: {
        "name": "Free",
        "price": 0,
        "period": "forever",
        "features": [
            "50 emails/month",
            "Basic CSV processing",
            "Template-based emails",
            "Playwright web scraping",
            "1 team seat"
        ],
        "limitations": [
            "No AI research",
            "No CRM dashboard",
            "No API integrations",
            "No Google Sheets sync"
        ]
    },
    SubscriptionTier.PRO: {
        "name": "Pro",
        "price": 49,
        "period": "month",
        "stripe_price_id": "price_pro_monthly",  # Replace with actual Stripe price ID
        "features": [
            "1,000 emails/month",
            "AI-powered research",
            "Full CRM dashboard",
            "Snov.io integration", 
            "Google Sheets sync",
            "SerpAPI access",
            "Priority support",
            "5 team seats"
        ],
        "limitations": []
    },
    SubscriptionTier.ENTERPRISE: {
        "name": "Enterprise",
        "price": 199,
        "period": "month",
        "stripe_price_id": "price_enterprise_monthly",  # Replace with actual Stripe price ID
        "features": [
            "10,000 emails/month",
            "All Pro features",
            "Advanced analytics",
            "Custom integrations",
            "Dedicated support",
            "50 team seats",
            "SLA guarantee"
        ],
        "limitations": []
    }
}


def get_tier_config(tier: SubscriptionTier) -> TierLimits:
    """Get configuration for a subscription tier"""
    return TIER_CONFIGS[tier]


def get_pricing_info(tier: SubscriptionTier) -> Dict:
    """Get pricing information for a tier"""
    return PRICING_CONFIG[tier]


# Example usage
if __name__ == "__main__":
    # Initialize system
    db = PaymentDatabase("test_payments.db")
    license_manager = LicenseManager(db)
    
    # Create test license
    test_license = license_manager.create_license_for_payment(
        user_email="test@example.com",
        tier=SubscriptionTier.PRO
    )
    
    print(f"Created test license: {test_license.license_key}")
    
    # Test validation
    is_valid, license, message = license_manager.validate_license(test_license.license_key)
    print(f"License validation: {is_valid} - {message}")
    
    # Test feature access
    can_access, access_message = license_manager.check_feature_access(
        test_license.license_key, "ai_research"
    )
    print(f"AI Research access: {can_access} - {access_message}")
    
    # Test rate limits
    within_limits, limit_message = license_manager.check_rate_limits(
        test_license.license_key, "email_generation"
    )
    print(f"Rate limits: {within_limits} - {limit_message}")
    
    # Record usage
    license_manager.record_feature_usage(
        test_license.license_key, "email_generation", 1
    )
    print("Recorded usage")
    
    # Clean up
    import os
    os.unlink("test_payments.db")