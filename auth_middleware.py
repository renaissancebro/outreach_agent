"""
Authentication Middleware for CLI and API

This module provides:
- CLI license key validation
- Feature access control for CLI commands
- Authentication decorators for functions
- License key storage and management
- Usage tracking integration
"""

import os
import json
import functools
from typing import Callable, Any, Tuple, Optional
from datetime import datetime

from payment_system import (
    PaymentDatabase, LicenseManager, SubscriptionTier,
    get_tier_config, TIER_CONFIGS
)

# Global license manager instance
_license_manager = None
_current_license_key = None

def get_license_manager() -> LicenseManager:
    """Get or create license manager instance"""
    global _license_manager
    if _license_manager is None:
        db = PaymentDatabase()
        _license_manager = LicenseManager(db)
    return _license_manager

def get_license_file_path() -> str:
    """Get path to license file"""
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, ".outreach_agent_license")

def save_license_key(license_key: str) -> None:
    """Save license key to local file"""
    license_file = get_license_file_path()
    
    license_data = {
        "license_key": license_key,
        "saved_at": datetime.now().isoformat()
    }
    
    try:
        with open(license_file, 'w') as f:
            json.dump(license_data, f)
        print(f"✅ License key saved to {license_file}")
    except Exception as e:
        print(f"❌ Error saving license key: {e}")

def load_license_key() -> Optional[str]:
    """Load license key from local file or environment"""
    global _current_license_key
    
    # Try environment variable first
    env_license = os.getenv("OUTREACH_AGENT_LICENSE")
    if env_license:
        _current_license_key = env_license
        return env_license
    
    # Try license file
    license_file = get_license_file_path()
    if os.path.exists(license_file):
        try:
            with open(license_file, 'r') as f:
                license_data = json.load(f)
                _current_license_key = license_data.get("license_key")
                return _current_license_key
        except Exception as e:
            print(f"⚠️  Error loading license file: {e}")
    
    return None

def prompt_for_license() -> Optional[str]:
    """Prompt user to enter license key"""
    print("\n🔑 LICENSE KEY REQUIRED")
    print("="*50)
    print("This feature requires a valid license key.")
    print("Get your license key at: https://outreach-agent.com/pricing")
    print()
    
    license_key = input("Enter your license key (or 'skip' to continue with free tier): ").strip()
    
    if license_key.lower() == 'skip':
        return None
    
    if license_key:
        # Validate the license key
        license_manager = get_license_manager()
        is_valid, license, message = license_manager.validate_license(license_key)
        
        if is_valid:
            save_license_key(license_key)
            print(f"✅ License key validated! You have {license.tier.value} access.")
            return license_key
        else:
            print(f"❌ Invalid license key: {message}")
            return None
    
    return None

def get_current_license() -> Tuple[Optional[str], Optional[str]]:
    """Get current license key and tier"""
    license_key = load_license_key()
    
    if not license_key:
        return None, "free"
    
    license_manager = get_license_manager()
    is_valid, license, message = license_manager.validate_license(license_key)
    
    if is_valid:
        return license_key, license.tier.value
    else:
        print(f"⚠️  License validation failed: {message}")
        return None, "free"

def require_license(feature_name: str, allow_prompt: bool = True):
    """Decorator to require valid license for a function"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            license_key = load_license_key()
            
            # If no license key and prompting allowed, prompt user
            if not license_key and allow_prompt:
                license_key = prompt_for_license()
            
            # If still no license key, check if feature is available in free tier
            if not license_key:
                free_config = TIER_CONFIGS[SubscriptionTier.FREE]
                feature_available = getattr(free_config, feature_name, False)
                
                if not feature_available:
                    print(f"\n🔒 FEATURE LOCKED")
                    print(f"{'='*50}")
                    print(f"The '{feature_name}' feature requires a Pro or Enterprise license.")
                    print(f"Current tier: FREE")
                    print(f"Upgrade at: https://outreach-agent.com/pricing")
                    print(f"{'='*50}")
                    return None
                else:
                    # Feature is available in free tier, continue
                    return func(*args, **kwargs)
            
            # Validate license and check feature access
            license_manager = get_license_manager()
            
            # Check if license is valid
            is_valid, license, message = license_manager.validate_license(license_key)
            if not is_valid:
                print(f"❌ License validation failed: {message}")
                if allow_prompt:
                    new_license = prompt_for_license()
                    if new_license:
                        return wrapper(*args, **kwargs)  # Retry with new license
                return None
            
            # Check feature access
            can_access, access_message = license_manager.check_feature_access(license_key, feature_name)
            if not can_access:
                print(f"\n🔒 FEATURE ACCESS DENIED")
                print(f"{'='*50}")
                print(f"Feature: {feature_name}")
                print(f"Current tier: {license.tier.value}")
                print(f"Reason: {access_message}")
                print(f"Upgrade at: https://outreach-agent.com/pricing")
                print(f"{'='*50}")
                return None
            
            # Check rate limits
            within_limits, limit_message = license_manager.check_rate_limits(license_key, feature_name)
            if not within_limits:
                print(f"\n⚠️  RATE LIMIT EXCEEDED")
                print(f"{'='*50}")
                print(f"Feature: {feature_name}")
                print(f"Limit: {limit_message}")
                print(f"Try again later or upgrade your plan.")
                print(f"{'='*50}")
                return None
            
            # Record usage
            license_manager.record_feature_usage(license_key, feature_name)
            
            # Execute the original function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_tier(min_tier: SubscriptionTier):
    """Decorator to require minimum subscription tier"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            license_key = load_license_key()
            
            if not license_key:
                license_key = prompt_for_license()
            
            if not license_key:
                print(f"\n🔒 TIER REQUIREMENT NOT MET")
                print(f"{'='*50}")
                print(f"This feature requires {min_tier.value} tier or higher.")
                print(f"Current tier: FREE")
                print(f"Upgrade at: https://outreach-agent.com/pricing")
                print(f"{'='*50}")
                return None
            
            license_manager = get_license_manager()
            is_valid, license, message = license_manager.validate_license(license_key)
            
            if not is_valid:
                print(f"❌ License validation failed: {message}")
                return None
            
            # Check tier hierarchy
            tier_hierarchy = {
                SubscriptionTier.FREE: 0,
                SubscriptionTier.PRO: 1,
                SubscriptionTier.ENTERPRISE: 2
            }
            
            user_tier_level = tier_hierarchy.get(license.tier, 0)
            required_tier_level = tier_hierarchy.get(min_tier, 999)
            
            if user_tier_level < required_tier_level:
                print(f"\n🔒 INSUFFICIENT TIER")
                print(f"{'='*50}")
                print(f"Required: {min_tier.value} or higher")
                print(f"Current: {license.tier.value}")
                print(f"Upgrade at: https://outreach-agent.com/pricing")
                print(f"{'='*50}")
                return None
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def check_usage_limits(license_key: str, feature: str) -> Tuple[bool, str]:
    """Check if user is within usage limits"""
    license_manager = get_license_manager()
    return license_manager.check_rate_limits(license_key, feature)

def get_usage_stats(license_key: str) -> dict:
    """Get usage statistics for a license"""
    license_manager = get_license_manager()
    return license_manager.db.get_usage_stats(license_key)

def show_license_info():
    """Show current license information"""
    license_key = load_license_key()
    
    if not license_key:
        print("\n📋 LICENSE STATUS")
        print("="*50)
        print("Status: FREE TIER")
        print("License Key: None")
        print("Features: Limited")
        print("\nUpgrade to Pro for:")
        print("  • AI-powered research")
        print("  • CRM dashboard")
        print("  • API integrations")
        print("  • Google Sheets sync")
        print("\nGet Pro: https://outreach-agent.com/pricing")
        print("="*50)
        return
    
    license_manager = get_license_manager()
    is_valid, license, message = license_manager.validate_license(license_key)
    
    if not is_valid:
        print(f"\n❌ INVALID LICENSE")
        print("="*50)
        print(f"License Key: {license_key[:20]}...")
        print(f"Status: {message}")
        print("="*50)
        return
    
    tier_config = get_tier_config(license.tier)
    usage_stats = get_usage_stats(license_key)
    
    print(f"\n✅ LICENSE INFORMATION")
    print("="*50)
    print(f"Status: ACTIVE")
    print(f"Tier: {license.tier.value.upper()}")
    print(f"Email: {license.user_email}")
    print(f"License Key: {license_key[:20]}...")
    print(f"Created: {license.created_at[:10]}")
    if license.expires_at:
        print(f"Expires: {license.expires_at[:10]}")
    print(f"\n📊 USAGE THIS MONTH")
    print(f"Emails: {usage_stats.get('email_generation', 0)} / {tier_config.monthly_emails}")
    print(f"API Calls: {usage_stats.get('api_calls', 0)} / {tier_config.monthly_api_calls}")
    print(f"\n🎯 AVAILABLE FEATURES")
    print(f"AI Research: {'✅' if tier_config.ai_research else '❌'}")
    print(f"CRM Dashboard: {'✅' if tier_config.crm_dashboard else '❌'}")
    print(f"Snov.io Integration: {'✅' if tier_config.snov_io_access else '❌'}")
    print(f"Google Sheets Sync: {'✅' if tier_config.sheets_access else '❌'}")
    print(f"SerpAPI Access: {'✅' if tier_config.serpapi_access else '❌'}")
    print(f"Team Seats: {tier_config.team_seats}")
    print("="*50)

# CLI command decorators for specific features
def require_ai_research(func):
    """Require AI research access"""
    return require_license("ai_research")(func)

def require_crm_dashboard(func):
    """Require CRM dashboard access"""
    return require_license("crm_dashboard")(func)

def require_snov_io(func):
    """Require Snov.io access"""
    return require_license("snov_io")(func)

def require_sheets_sync(func):
    """Require Google Sheets sync access"""
    return require_license("sheets_sync")(func)

def require_serpapi(func):
    """Require SerpAPI access"""
    return require_license("serpapi")(func)

def require_pro_tier(func):
    """Require Pro tier or higher"""
    return require_tier(SubscriptionTier.PRO)(func)

def require_enterprise_tier(func):
    """Require Enterprise tier"""
    return require_tier(SubscriptionTier.ENTERPRISE)(func)

# License management commands
def set_license_key(license_key: str) -> bool:
    """Set and validate license key"""
    license_manager = get_license_manager()
    is_valid, license, message = license_manager.validate_license(license_key)
    
    if is_valid:
        save_license_key(license_key)
        print(f"✅ License key set successfully!")
        print(f"Tier: {license.tier.value}")
        print(f"Email: {license.user_email}")
        return True
    else:
        print(f"❌ Invalid license key: {message}")
        return False

def remove_license_key():
    """Remove stored license key"""
    license_file = get_license_file_path()
    
    if os.path.exists(license_file):
        try:
            os.remove(license_file)
            print("✅ License key removed")
        except Exception as e:
            print(f"❌ Error removing license key: {e}")
    else:
        print("ℹ️  No license key file found")

# Example usage
if __name__ == "__main__":
    # Test the authentication system
    print("Testing authentication system...")
    
    # Show current license info
    show_license_info()
    
    # Test feature that requires Pro tier
    @require_ai_research
    def test_ai_feature():
        print("✅ AI Research feature accessed!")
        return "AI result"
    
    # Test the decorated function
    result = test_ai_feature()
    print(f"Result: {result}")