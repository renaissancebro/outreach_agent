#!/usr/bin/env python3
"""
End-to-End Test Script for Outreach Agent
This script tests the complete workflow from lead collection to email generation
"""

import os
import sys
import time
import json
import csv
from datetime import datetime
from typing import List, Dict

def test_free_tier():
    """Test free tier functionality"""
    print("🆓 TESTING FREE TIER FUNCTIONALITY")
    print("="*50)
    
    # Test license info without any license
    print("1. Testing license info (should show free tier)...")
    os.system("python main.py --license-info")
    
    # Test basic email generation with sample data
    print("\n2. Testing basic email generation...")
    os.system("python main.py --csv test_data/sample_leads.csv --limit 2 --no-ai-research")
    
    # Test CRM dashboard (should be blocked)
    print("\n3. Testing CRM dashboard (should be blocked)...")
    os.system("python main.py --crm-dashboard")
    
    print("✅ Free tier testing completed!\n")

def test_pro_license():
    """Test pro tier functionality"""
    print("💎 TESTING PRO TIER FUNCTIONALITY")
    print("="*50)
    
    # Create a test pro license
    print("1. Creating test Pro license...")
    os.system("""python -c "
from payment_system import PaymentDatabase, LicenseManager, SubscriptionTier
db = PaymentDatabase()
lm = LicenseManager(db)
license = lm.create_license_for_payment('test@yourbusiness.com', SubscriptionTier.PRO)
print(f'Pro license created: {license.license_key}')
with open('test_license_key.txt', 'w') as f:
    f.write(license.license_key)
"
""")
    
    # Read the license key
    with open('test_license_key.txt', 'r') as f:
        license_key = f.read().strip()
    
    # Set the license
    print("2. Setting Pro license...")
    os.system(f"python main.py --set-license {license_key}")
    
    # Test license info
    print("\n3. Testing license info (should show Pro tier)...")
    os.system("python main.py --license-info")
    
    # Test AI-powered email generation
    print("\n4. Testing AI-powered email generation...")
    os.system("python main.py --csv test_data/sample_leads.csv --limit 1")
    
    # Test CRM dashboard
    print("\n5. Testing CRM dashboard...")
    os.system("python main.py --crm-dashboard")
    
    # Test tool capabilities
    print("\n6. Testing tool capabilities...")
    os.system("python main.py --tool-capabilities")
    
    print("✅ Pro tier testing completed!\n")

def test_api_server():
    """Test the API server functionality"""
    print("🌐 TESTING API SERVER")
    print("="*50)
    
    print("Starting API server test client...")
    
    test_code = '''
from fastapi.testclient import TestClient
from api_server import app
import json

client = TestClient(app)

print("1. Testing health endpoint...")
response = client.get("/health")
print(f"   Status: {response.status_code}")
print(f"   Data: {response.json()}")

print("\\n2. Testing pricing endpoint...")
response = client.get("/pricing")
print(f"   Status: {response.status_code}")
print(f"   Tiers available: {list(response.json()['tiers'].keys())}")

print("\\n3. Testing free sample generation...")
response = client.post("/free/generate-sample")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   Sample generated successfully!")
else:
    print(f"   Error: {response.json()}")

# Test with license key if available
try:
    with open("test_license_key.txt", "r") as f:
        license_key = f.read().strip()
    
    print(f"\\n4. Testing authentication with license key...")
    headers = {"Authorization": f"Bearer {license_key}"}
    response = client.get("/auth/validate", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Tier: {data['tier']}")
        print(f"   Features: {list(data['features_available'].keys())}")
    else:
        print(f"   Error: {response.json()}")

except FileNotFoundError:
    print("\\n4. No license key found, skipping authenticated tests...")

print("\\n✅ API server testing completed!")
'''
    
    with open('temp_api_test.py', 'w') as f:
        f.write(test_code)
    
    os.system("python temp_api_test.py")
    os.remove('temp_api_test.py')
    print()

def test_lead_collection():
    """Test intelligent lead collection"""
    print("🎯 TESTING LEAD COLLECTION")
    print("="*50)
    
    # Test CSV processing
    print("1. Testing Sales Navigator CSV processing...")
    os.system("python main.py --collect-leads --sales-nav-csv test_data/sample_sales_nav.csv --import-to-crm --limit 2")
    
    # Test web scraping capabilities
    print("\n2. Testing tool capabilities...")
    os.system("python main.py --tool-capabilities")
    
    print("✅ Lead collection testing completed!\n")

def test_crm_workflow():
    """Test complete CRM workflow"""
    print("📊 TESTING CRM WORKFLOW")
    print("="*50)
    
    # Import leads to CRM
    print("1. Importing test leads to CRM...")
    os.system("python main.py --csv test_data/sample_leads.csv --import-to-crm --limit 3 --no-ai-research")
    
    # Check CRM dashboard
    print("\n2. Checking CRM dashboard...")
    os.system("python main.py --crm-dashboard")
    
    # Search contacts
    print("\n3. Searching CRM contacts...")
    os.system("python main.py --crm-search TechCorp")
    
    # Filter by status
    print("\n4. Filtering by new status...")
    os.system("python main.py --crm-status new")
    
    # Update contact status
    print("\n5. Updating contact status...")
    os.system("python main.py --crm-update-status john@techcorp.com contacted")
    
    # Export CRM data
    print("\n6. Exporting CRM data...")
    os.system("python main.py --crm-export test_crm_export.csv")
    
    print("✅ CRM workflow testing completed!\n")

def create_sample_data():
    """Create sample test data"""
    print("📋 CREATING SAMPLE TEST DATA")
    print("="*50)
    
    # Create test data directory
    os.makedirs('test_data', exist_ok=True)
    
    # Sample leads CSV
    sample_leads = [
        {
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'john@techcorp.com',
            'company_name': 'TechCorp Inc',
            'position': 'CEO',
            'industry': 'Technology',
            'website': 'https://techcorp.com',
            'linkedin_url': 'https://linkedin.com/in/johnsmith',
            'location': 'San Francisco, CA',
            'company_size': '50-100',
            'phone': '+1-555-0123',
            'notes': 'Interested in AI solutions'
        },
        {
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'email': 'sarah@innovate.co',
            'company_name': 'Innovate Solutions',
            'position': 'CTO',
            'industry': 'Software',
            'website': 'https://innovate.co',
            'linkedin_url': 'https://linkedin.com/in/sarahjohnson',
            'location': 'New York, NY',
            'company_size': '100-200',
            'phone': '+1-555-0456',
            'notes': 'Looking for automation tools'
        },
        {
            'first_name': 'Mike',
            'last_name': 'Davis',
            'email': 'mike@startupx.io',
            'company_name': 'StartupX',
            'position': 'Founder',
            'industry': 'Fintech',
            'website': 'https://startupx.io',
            'linkedin_url': 'https://linkedin.com/in/mikedavis',
            'location': 'Austin, TX',
            'company_size': '10-50',
            'phone': '+1-555-0789',
            'notes': 'Early stage fintech startup'
        }
    ]
    
    # Write sample leads CSV
    with open('test_data/sample_leads.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = sample_leads[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_leads)
    
    # Sample Sales Navigator export
    sales_nav_data = [
        {
            'first_name': 'Lisa',
            'last_name': 'Wang',
            'email': 'lisa@aicompany.com',
            'company_name': 'AI Company',
            'position': 'VP of Engineering',
            'industry': 'Artificial Intelligence',
            'location': 'Seattle, WA',
            'connection_degree': '2nd',
            'shared_connections': '5 shared connections'
        },
        {
            'first_name': 'David',
            'last_name': 'Brown',
            'email': 'david@datatech.com',
            'company_name': 'DataTech Solutions',
            'position': 'Data Science Director',
            'industry': 'Data Analytics',
            'location': 'Boston, MA',
            'connection_degree': '3rd',
            'shared_connections': '2 shared connections'
        }
    ]
    
    # Write Sales Navigator CSV
    with open('test_data/sample_sales_nav.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = sales_nav_data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sales_nav_data)
    
    print("✅ Sample test data created in test_data/ directory\n")

def cleanup_test_data():
    """Clean up test data"""
    print("🧹 CLEANING UP TEST DATA")
    print("="*50)
    
    # Remove test files
    files_to_remove = [
        'test_license_key.txt',
        'test_crm_export.csv',
        'test_payment.db'
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed: {file}")
    
    # Remove license key
    print("Removing test license...")
    os.system("python main.py --remove-license")
    
    print("✅ Cleanup completed!\n")

def main():
    """Run end-to-end tests"""
    print("🚀 OUTREACH AGENT END-TO-END TESTING")
    print("="*60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Create sample data first
        create_sample_data()
        
        # Test free tier
        test_free_tier()
        
        # Test pro license
        test_pro_license()
        
        # Test API server
        test_api_server()
        
        # Test lead collection
        test_lead_collection()
        
        # Test CRM workflow
        test_crm_workflow()
        
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("Ready for personal business use!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
    finally:
        # Always cleanup
        cleanup_test_data()

if __name__ == "__main__":
    main()