#!/usr/bin/env python3
"""
Test script to validate outreach agent setup and API connections
"""

import os
from dotenv import load_dotenv
from lead_manager import LeadManager
import yaml

def test_environment_setup():
    """Test environment variables and configuration"""
    print("🔍 Testing environment setup...")
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ['OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Set (length: {len(value)})")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    # Check Snov.io credentials (either OAuth or API key)
    snov_client_id = os.getenv('SNOV_CLIENT_ID')
    snov_client_secret = os.getenv('SNOV_CLIENT_SECRET')
    snov_api_key = os.getenv('SNOV_API_KEY')
    
    if snov_client_id and snov_client_secret:
        print(f"✅ SNOV_CLIENT_ID: Set (length: {len(snov_client_id)})")
        print(f"✅ SNOV_CLIENT_SECRET: Set (length: {len(snov_client_secret)})")
        print("✅ Snov.io OAuth credentials configured")
    elif snov_api_key:
        print(f"✅ SNOV_API_KEY: Set (length: {len(snov_api_key)})")
        print("✅ Snov.io API key configured")
    else:
        print("❌ Snov.io credentials: Not set")
        print("⚠️  Set either SNOV_CLIENT_ID+SNOV_CLIENT_SECRET or SNOV_API_KEY")
        missing_vars.append('SNOV_CREDENTIALS')
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {missing_vars}")
        print("Please set these in your .env file or environment")
        return False
    
    return True

def test_config_file():
    """Test configuration file loading"""
    print("\n🔍 Testing configuration file...")
    
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        print("✅ Configuration file loaded successfully")
        
        # Check key sections
        sections = ['agent', 'lead_sources', 'email_templates', 'output']
        for section in sections:
            if section in config:
                print(f"✅ {section}: Found")
            else:
                print(f"⚠️  {section}: Missing")
        
        return True
    except Exception as e:
        print(f"❌ Error loading config file: {e}")
        return False

def test_snov_connection():
    """Test Snov.io API connection"""
    print("\n🔍 Testing Snov.io API connection...")
    
    try:
        # Load config
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        # Create lead manager
        lead_manager = LeadManager(config)
        
        # Test connection
        return lead_manager.verify_snov_connection()
    except Exception as e:
        print(f"❌ Error testing Snov.io connection: {e}")
        return False

def test_csv_leads():
    """Test CSV lead loading"""
    print("\n🔍 Testing CSV lead loading...")
    
    try:
        # Load config
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        # Create lead manager
        lead_manager = LeadManager(config)
        
        # Load leads
        leads = lead_manager.load_csv_leads('leads.csv')
        
        if leads:
            print(f"✅ Successfully loaded {len(leads)} leads from CSV")
            print(f"📋 Sample lead: {leads[0].first_name} {leads[0].last_name} at {leads[0].company_name}")
            return True
        else:
            print("❌ No leads found in CSV file")
            return False
    except Exception as e:
        print(f"❌ Error loading CSV leads: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 OUTREACH AGENT SETUP VALIDATION")
    print("=" * 50)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Configuration File", test_config_file),
        ("CSV Lead Loading", test_csv_leads),
        ("Snov.io Connection", test_snov_connection)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Your outreach agent is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)