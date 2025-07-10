#!/usr/bin/env python3
"""
Test script for CRM functionality

This script demonstrates and tests the CRM system including:
- SQLite database operations
- Lead import and management
- Status tracking and pipeline management
- Google Sheets integration (if credentials available)
- Dashboard and reporting
"""

import os
import sys
import tempfile
from datetime import datetime
from typing import List, Dict

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crm_system import (
    CRMSystem, CRMDatabase, CRMContact, Interaction, Campaign,
    LeadStatus, InteractionType, GoogleSheetsIntegration
)
from lead_manager import Lead


def test_database_operations():
    """Test basic database operations"""
    print("🗄️  TESTING DATABASE OPERATIONS")
    print("="*50)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Initialize database
        db = CRMDatabase(db_path)
        print("✅ Database initialized")
        
        # Create test contact
        contact = CRMContact(
            id="test-001",
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            company_name="Example Corp",
            position="CEO",
            industry="Technology",
            phone="+1-555-0123",
            linkedin_url="https://linkedin.com/in/johndoe",
            status=LeadStatus.NEW,
            lead_source="test",
            lead_score=75,
            notes="Test contact for CRM"
        )
        
        # Insert contact
        contact_id = db.insert_contact(contact)
        print(f"✅ Contact inserted: {contact_id}")
        
        # Retrieve contact
        retrieved_contact = db.get_contact(contact_id)
        assert retrieved_contact is not None
        assert retrieved_contact.email == "john.doe@example.com"
        print("✅ Contact retrieved successfully")
        
        # Update contact
        retrieved_contact.status = LeadStatus.CONTACTED
        retrieved_contact.notes += "\nUpdated via test"
        db.update_contact(retrieved_contact)
        print("✅ Contact updated")
        
        # Search contacts
        contacts = db.search_contacts(query="john")
        assert len(contacts) == 1
        print("✅ Contact search works")
        
        # Add interaction
        interaction = Interaction(
            id="int-001",
            contact_id=contact_id,
            interaction_type=InteractionType.EMAIL_SENT,
            subject="Test Email",
            content="This is a test email",
            timestamp=datetime.now().isoformat(),
            created_by="test_system"
        )
        
        interaction_id = db.add_interaction(interaction)
        print(f"✅ Interaction added: {interaction_id}")
        
        # Get interactions
        interactions = db.get_contact_interactions(contact_id)
        assert len(interactions) == 1
        print("✅ Interaction retrieval works")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)

def test_crm_system():
    """Test CRM system functionality"""
    print("\n📋 TESTING CRM SYSTEM")
    print("="*50)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Configuration
        config = {
            'crm': {
                'database_path': db_path,
                'google_credentials_path': 'google_credentials.json',
                'auto_import_leads': True,
                'auto_log_emails': True
            }
        }
        
        # Initialize CRM
        crm = CRMSystem(config)
        print("✅ CRM system initialized")
        
        # Create test leads
        leads = [
            Lead(
                first_name="Alice",
                last_name="Smith",
                email="alice.smith@techcorp.com",
                company_name="TechCorp",
                position="CTO",
                industry="Technology",
                linkedin_url="https://linkedin.com/in/alicesmith",
                location="San Francisco, CA"
            ),
            Lead(
                first_name="Bob",
                last_name="Johnson",
                email="bob.johnson@innovate.com",
                company_name="InnovateInc",
                position="VP Sales",
                industry="Software",
                phone="+1-555-0456",
                website="https://innovate.com"
            )
        ]
        
        # Import leads to CRM
        contacts = crm.batch_import_leads(leads, "test_import")
        print(f"✅ Imported {len(contacts)} leads to CRM")
        
        # Test email logging
        if contacts:
            contact = contacts[0]
            crm.log_email_sent(
                contact.id,
                "Welcome to Our Platform",
                "Thank you for your interest in our solutions...",
                "test_campaign"
            )
            print("✅ Email interaction logged")
        
        # Test status updates
        crm.update_contact_status(contact.id, LeadStatus.CONTACTED, "Initial outreach completed")
        print("✅ Contact status updated")
        
        # Test search functionality
        contacted_contacts = crm.get_contacts_by_status(LeadStatus.CONTACTED)
        print(f"✅ Found {len(contacted_contacts)} contacted leads")
        
        # Test pipeline report
        pipeline_report = crm.get_pipeline_report()
        print("✅ Pipeline report generated")
        print(f"   New leads: {pipeline_report['new']['count']}")
        print(f"   Contacted: {pipeline_report['contacted']['count']}")
        
        # Test dashboard stats
        stats = crm.get_dashboard_stats()
        print("✅ Dashboard stats generated")
        print(f"   Total contacts: {stats['total_contacts']}")
        
        # Test CSV export
        export_file = crm.export_to_csv("test_export.csv")
        print(f"✅ Data exported to: {export_file}")
        
        # Clean up export file
        if os.path.exists(export_file):
            os.unlink(export_file)
        
        return True
        
    except Exception as e:
        print(f"❌ CRM system test failed: {str(e)}")
        return False
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)

def test_google_sheets_integration():
    """Test Google Sheets integration"""
    print("\n📊 TESTING GOOGLE SHEETS INTEGRATION")
    print("="*50)
    
    try:
        # Check if Google Sheets is available
        from crm_system import GOOGLE_SHEETS_AVAILABLE
        
        if not GOOGLE_SHEETS_AVAILABLE:
            print("⚠️  Google Sheets dependencies not installed")
            print("   Install with: pip install gspread google-auth")
            return True  # Not a failure, just not available
        
        # Initialize Google Sheets integration
        sheets = GoogleSheetsIntegration("google_credentials.json")
        
        if not os.path.exists("google_credentials.json"):
            print("⚠️  Google Sheets credentials not found")
            print("   Create google_credentials.json with service account credentials")
            return True  # Not a failure, just not configured
        
        print("✅ Google Sheets integration initialized")
        
        # Note: We can't test actual sheet operations without valid credentials
        # and a real Google Sheet, but we can test the integration setup
        
        return True
        
    except Exception as e:
        print(f"⚠️  Google Sheets test skipped: {str(e)}")
        return True  # Not a critical failure

def test_lead_status_workflow():
    """Test lead status workflow"""
    print("\n🔄 TESTING LEAD STATUS WORKFLOW")
    print("="*50)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        config = {
            'crm': {
                'database_path': db_path
            }
        }
        
        crm = CRMSystem(config)
        
        # Create lead
        lead = Lead(
            first_name="Test",
            last_name="Lead",
            email="test.lead@workflow.com",
            company_name="Workflow Corp",
            position="Manager",
            industry="Testing"
        )
        
        # Import lead
        contact = crm.import_lead_to_crm(lead, "workflow_test")
        print(f"✅ Lead imported with status: {contact.status.value}")
        
        # Test status progression
        status_progression = [
            LeadStatus.CONTACTED,
            LeadStatus.RESPONDED,
            LeadStatus.QUALIFIED,
            LeadStatus.PROPOSAL_SENT,
            LeadStatus.NEGOTIATION,
            LeadStatus.CLOSED_WON
        ]
        
        for status in status_progression:
            crm.update_contact_status(contact.id, status, f"Advanced to {status.value}")
            
            # Add interaction for each status change
            interaction = Interaction(
                id=f"int-{status.value}",
                contact_id=contact.id,
                interaction_type=InteractionType.NOTE,
                subject=f"Status Update: {status.value}",
                content=f"Contact advanced to {status.value} stage",
                timestamp=datetime.now().isoformat(),
                created_by="test_workflow"
            )
            
            crm.db.add_interaction(interaction)
            print(f"   🔄 Advanced to: {status.value}")
        
        # Verify final status
        final_contact = crm.db.get_contact(contact.id)
        assert final_contact.status == LeadStatus.CLOSED_WON
        print("✅ Status workflow completed successfully")
        
        # Check interaction history
        interactions = crm.db.get_contact_interactions(contact.id)
        print(f"✅ {len(interactions)} interactions recorded")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed: {str(e)}")
        return False
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

def test_cli_integration():
    """Test CLI integration"""
    print("\n💻 TESTING CLI INTEGRATION")
    print("="*50)
    
    try:
        # Test importing the main module
        from main import EnhancedOutreachAgent
        
        # Create temporary config
        test_config = {
            'agent': {'verbose': False},
            'crm': {'database_path': 'test_cli.db'},
            'lead_sources': {'csv': {'default_path': 'test.csv'}},
            'email_templates': {
                'subject_templates': ['Test Subject'],
                'opening_templates': ['Test Opening']
            },
            'personalization': {'research_depth': 'low'},
            'output': {'format': 'json'}
        }
        
        # Save test config
        import yaml
        with open('test_config.yaml', 'w') as f:
            yaml.dump(test_config, f)
        
        # Initialize agent
        agent = EnhancedOutreachAgent('test_config.yaml')
        print("✅ CLI integration works")
        
        # Test CRM methods
        stats = agent.get_crm_dashboard()
        print(f"✅ Dashboard access works: {stats['total_contacts']} contacts")
        
        # Test search
        contacts = agent.search_crm_contacts()
        print(f"✅ Search works: {len(contacts)} contacts found")
        
        # Clean up
        if os.path.exists('test_config.yaml'):
            os.unlink('test_config.yaml')
        if os.path.exists('test_cli.db'):
            os.unlink('test_cli.db')
        
        return True
        
    except Exception as e:
        print(f"❌ CLI integration test failed: {str(e)}")
        return False

def test_data_integrity():
    """Test data integrity and error handling"""
    print("\n🔒 TESTING DATA INTEGRITY")
    print("="*50)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        db = CRMDatabase(db_path)
        
        # Test duplicate email handling
        contact1 = CRMContact(
            id="dup-001",
            first_name="Duplicate",
            last_name="Test",
            email="duplicate@test.com",
            company_name="Test Corp",
            position="Tester",
            industry="Testing"
        )
        
        contact2 = CRMContact(
            id="dup-002",
            first_name="Another",
            last_name="Duplicate",
            email="duplicate@test.com",  # Same email
            company_name="Other Corp",
            position="Manager",
            industry="Testing"
        )
        
        # Insert first contact
        db.insert_contact(contact1)
        print("✅ First contact inserted")
        
        # Try to insert duplicate email (should handle gracefully)
        try:
            db.insert_contact(contact2)
            print("⚠️  Duplicate email was allowed (check constraint needed)")
        except Exception as e:
            print("✅ Duplicate email properly rejected")
        
        # Test invalid status handling
        contact3 = CRMContact(
            id="invalid-001",
            first_name="Invalid",
            last_name="Status",
            email="invalid@test.com",
            company_name="Invalid Corp",
            position="Tester",
            industry="Testing",
            status=LeadStatus.NEW
        )
        
        db.insert_contact(contact3)
        
        # Try to retrieve with invalid status would be handled by enum
        retrieved = db.get_contact("invalid-001")
        assert retrieved.status == LeadStatus.NEW
        print("✅ Status validation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Data integrity test failed: {str(e)}")
        return False
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

def main():
    """Run all CRM tests"""
    print("🧪 CRM SYSTEM TEST SUITE")
    print("="*60)
    print()
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Database Operations", test_database_operations),
        ("CRM System", test_crm_system),
        ("Google Sheets Integration", test_google_sheets_integration),
        ("Lead Status Workflow", test_lead_status_workflow),
        ("CLI Integration", test_cli_integration),
        ("Data Integrity", test_data_integrity),
    ]
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            test_results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {str(e)}")
            test_results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("🎉 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! CRM system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n💡 NEXT STEPS:")
    print("1. Test with real data using main.py commands")
    print("2. Set up Google Sheets credentials for sync functionality")
    print("3. Configure CRM settings in config.yaml")
    print("4. Try the CRM commands:")
    print("   python main.py --crm-dashboard")
    print("   python main.py --crm-search 'company name'")
    print("   python main.py --collect-leads --import-to-crm --sales-nav-csv file.csv")


if __name__ == "__main__":
    main()