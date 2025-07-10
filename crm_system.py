"""
CRM System for Outreach Agent

This module provides comprehensive CRM functionality including:
- Lead management with SQLite database
- Contact tracking and interaction history
- Campaign management and analytics
- Google Sheets integration for data sync
- Pipeline management with stages
- Reporting and dashboard functionality
"""

import os
import sqlite3
import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Google Sheets imports (optional)
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False

from lead_manager import Lead


class LeadStatus(Enum):
    """Lead status options"""
    NEW = "new"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    DORMANT = "dormant"


class InteractionType(Enum):
    """Types of interactions"""
    EMAIL_SENT = "email_sent"
    EMAIL_RECEIVED = "email_received"
    PHONE_CALL = "phone_call"
    MEETING = "meeting"
    NOTE = "note"
    PROPOSAL = "proposal"
    FOLLOW_UP = "follow_up"
    SOCIAL_MEDIA = "social_media"


@dataclass
class CRMContact:
    """Enhanced contact with CRM fields"""
    id: str
    first_name: str
    last_name: str
    email: str
    company_name: str
    position: str
    industry: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    
    # CRM specific fields
    status: LeadStatus = LeadStatus.NEW
    lead_source: str = "unknown"
    assigned_to: Optional[str] = None
    lead_score: int = 0
    estimated_value: Optional[float] = None
    expected_close_date: Optional[str] = None
    
    # Timestamps
    created_at: str = None
    updated_at: str = None
    last_contacted: Optional[str] = None
    
    # Notes and tags
    notes: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
        if self.tags is None:
            self.tags = []


@dataclass
class Interaction:
    """Contact interaction record"""
    id: str
    contact_id: str
    interaction_type: InteractionType
    subject: str
    content: str
    timestamp: str
    created_by: str = "system"
    metadata: Dict = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Campaign:
    """Campaign tracking"""
    id: str
    name: str
    description: str
    status: str = "active"  # active, paused, completed
    start_date: str = None
    end_date: Optional[str] = None
    created_at: str = None
    
    # Campaign metrics
    total_contacts: int = 0
    emails_sent: int = 0
    responses_received: int = 0
    meetings_scheduled: int = 0
    deals_closed: int = 0
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.start_date is None:
            self.start_date = datetime.now().isoformat()


class CRMDatabase:
    """SQLite database manager for CRM"""
    
    def __init__(self, db_path: str = "crm.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Contacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                company_name TEXT,
                position TEXT,
                industry TEXT,
                phone TEXT,
                linkedin_url TEXT,
                website TEXT,
                company_size TEXT,
                location TEXT,
                status TEXT DEFAULT 'new',
                lead_source TEXT DEFAULT 'unknown',
                assigned_to TEXT,
                lead_score INTEGER DEFAULT 0,
                estimated_value REAL,
                expected_close_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_contacted TEXT,
                notes TEXT,
                tags TEXT
            )
        """)
        
        # Interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id TEXT PRIMARY KEY,
                contact_id TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                subject TEXT NOT NULL,
                content TEXT,
                timestamp TEXT NOT NULL,
                created_by TEXT DEFAULT 'system',
                metadata TEXT,
                FOREIGN KEY (contact_id) REFERENCES contacts (id)
            )
        """)
        
        # Campaigns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                start_date TEXT,
                end_date TEXT,
                created_at TEXT NOT NULL,
                total_contacts INTEGER DEFAULT 0,
                emails_sent INTEGER DEFAULT 0,
                responses_received INTEGER DEFAULT 0,
                meetings_scheduled INTEGER DEFAULT 0,
                deals_closed INTEGER DEFAULT 0
            )
        """)
        
        # Campaign contacts junction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_contacts (
                campaign_id TEXT NOT NULL,
                contact_id TEXT NOT NULL,
                added_at TEXT NOT NULL,
                PRIMARY KEY (campaign_id, contact_id),
                FOREIGN KEY (campaign_id) REFERENCES campaigns (id),
                FOREIGN KEY (contact_id) REFERENCES contacts (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a query and return results as dictionaries"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.commit()
            return results
        finally:
            conn.close()
    
    def insert_contact(self, contact: CRMContact) -> str:
        """Insert a new contact"""
        contact.updated_at = datetime.now().isoformat()
        
        query = """
            INSERT INTO contacts (
                id, first_name, last_name, email, company_name, position, industry,
                phone, linkedin_url, website, company_size, location, status,
                lead_source, assigned_to, lead_score, estimated_value, expected_close_date,
                created_at, updated_at, last_contacted, notes, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            contact.id, contact.first_name, contact.last_name, contact.email,
            contact.company_name, contact.position, contact.industry,
            contact.phone, contact.linkedin_url, contact.website,
            contact.company_size, contact.location, contact.status.value,
            contact.lead_source, contact.assigned_to, contact.lead_score,
            contact.estimated_value, contact.expected_close_date,
            contact.created_at, contact.updated_at, contact.last_contacted,
            contact.notes, json.dumps(contact.tags)
        )
        
        self.execute_query(query, params)
        return contact.id
    
    def update_contact(self, contact: CRMContact) -> bool:
        """Update an existing contact"""
        contact.updated_at = datetime.now().isoformat()
        
        query = """
            UPDATE contacts SET
                first_name = ?, last_name = ?, email = ?, company_name = ?, position = ?,
                industry = ?, phone = ?, linkedin_url = ?, website = ?, company_size = ?,
                location = ?, status = ?, lead_source = ?, assigned_to = ?, lead_score = ?,
                estimated_value = ?, expected_close_date = ?, updated_at = ?,
                last_contacted = ?, notes = ?, tags = ?
            WHERE id = ?
        """
        
        params = (
            contact.first_name, contact.last_name, contact.email, contact.company_name,
            contact.position, contact.industry, contact.phone, contact.linkedin_url,
            contact.website, contact.company_size, contact.location, contact.status.value,
            contact.lead_source, contact.assigned_to, contact.lead_score,
            contact.estimated_value, contact.expected_close_date, contact.updated_at,
            contact.last_contacted, contact.notes, json.dumps(contact.tags),
            contact.id
        )
        
        self.execute_query(query, params)
        return True
    
    def get_contact(self, contact_id: str) -> Optional[CRMContact]:
        """Get a contact by ID"""
        query = "SELECT * FROM contacts WHERE id = ?"
        results = self.execute_query(query, (contact_id,))
        
        if results:
            row = results[0]
            return self._row_to_contact(row)
        return None
    
    def get_contact_by_email(self, email: str) -> Optional[CRMContact]:
        """Get a contact by email"""
        query = "SELECT * FROM contacts WHERE email = ?"
        results = self.execute_query(query, (email,))
        
        if results:
            row = results[0]
            return self._row_to_contact(row)
        return None
    
    def _row_to_contact(self, row: Dict) -> CRMContact:
        """Convert database row to CRMContact"""
        tags = json.loads(row['tags']) if row['tags'] else []
        
        return CRMContact(
            id=row['id'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            email=row['email'],
            company_name=row['company_name'],
            position=row['position'],
            industry=row['industry'],
            phone=row['phone'],
            linkedin_url=row['linkedin_url'],
            website=row['website'],
            company_size=row['company_size'],
            location=row['location'],
            status=LeadStatus(row['status']),
            lead_source=row['lead_source'],
            assigned_to=row['assigned_to'],
            lead_score=row['lead_score'],
            estimated_value=row['estimated_value'],
            expected_close_date=row['expected_close_date'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            last_contacted=row['last_contacted'],
            notes=row['notes'],
            tags=tags
        )
    
    def search_contacts(self, query: str = None, status: LeadStatus = None, 
                       limit: int = 100) -> List[CRMContact]:
        """Search contacts with filters"""
        sql_query = "SELECT * FROM contacts WHERE 1=1"
        params = []
        
        if query:
            sql_query += " AND (first_name LIKE ? OR last_name LIKE ? OR company_name LIKE ? OR email LIKE ?)"
            search_term = f"%{query}%"
            params.extend([search_term, search_term, search_term, search_term])
        
        if status:
            sql_query += " AND status = ?"
            params.append(status.value)
        
        sql_query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        
        results = self.execute_query(sql_query, tuple(params))
        return [self._row_to_contact(row) for row in results]
    
    def add_interaction(self, interaction: Interaction) -> str:
        """Add an interaction record"""
        query = """
            INSERT INTO interactions (
                id, contact_id, interaction_type, subject, content, timestamp, created_by, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            interaction.id, interaction.contact_id, interaction.interaction_type.value,
            interaction.subject, interaction.content, interaction.timestamp,
            interaction.created_by, json.dumps(interaction.metadata)
        )
        
        self.execute_query(query, params)
        
        # Update last_contacted for the contact
        self.execute_query(
            "UPDATE contacts SET last_contacted = ? WHERE id = ?",
            (interaction.timestamp, interaction.contact_id)
        )
        
        return interaction.id
    
    def get_contact_interactions(self, contact_id: str) -> List[Interaction]:
        """Get all interactions for a contact"""
        query = """
            SELECT * FROM interactions 
            WHERE contact_id = ? 
            ORDER BY timestamp DESC
        """
        results = self.execute_query(query, (contact_id,))
        
        interactions = []
        for row in results:
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            interaction = Interaction(
                id=row['id'],
                contact_id=row['contact_id'],
                interaction_type=InteractionType(row['interaction_type']),
                subject=row['subject'],
                content=row['content'],
                timestamp=row['timestamp'],
                created_by=row['created_by'],
                metadata=metadata
            )
            interactions.append(interaction)
        
        return interactions


class GoogleSheetsIntegration:
    """Google Sheets integration for CRM data"""
    
    def __init__(self, credentials_path: str = "google_credentials.json"):
        self.credentials_path = credentials_path
        self.client = None
        self.sheet = None
        
        if GOOGLE_SHEETS_AVAILABLE:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Sheets client"""
        try:
            if os.path.exists(self.credentials_path):
                scope = [
                    "https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive.file",
                    "https://www.googleapis.com/auth/drive"
                ]
                
                credentials = Credentials.from_service_account_file(
                    self.credentials_path, scopes=scope
                )
                self.client = gspread.authorize(credentials)
                print("✅ Google Sheets client initialized")
            else:
                print("⚠️  Google Sheets credentials not found")
        except Exception as e:
            print(f"❌ Error initializing Google Sheets: {str(e)}")
    
    def connect_to_sheet(self, sheet_id: str, worksheet_name: str = "Sheet1"):
        """Connect to a specific Google Sheet"""
        try:
            if not self.client:
                raise Exception("Google Sheets client not initialized")
            
            spreadsheet = self.client.open_by_key(sheet_id)
            self.sheet = spreadsheet.worksheet(worksheet_name)
            print(f"✅ Connected to Google Sheet: {worksheet_name}")
            return True
        except Exception as e:
            print(f"❌ Error connecting to Google Sheet: {str(e)}")
            return False
    
    def sync_contacts_to_sheet(self, contacts: List[CRMContact]):
        """Sync contacts to Google Sheet"""
        try:
            if not self.sheet:
                raise Exception("Not connected to Google Sheet")
            
            # Clear existing data
            self.sheet.clear()
            
            # Prepare headers
            headers = [
                "ID", "First Name", "Last Name", "Email", "Company", "Position", 
                "Industry", "Phone", "LinkedIn", "Website", "Company Size", 
                "Location", "Status", "Lead Source", "Assigned To", "Lead Score",
                "Estimated Value", "Expected Close", "Created", "Updated", 
                "Last Contacted", "Notes", "Tags"
            ]
            
            # Prepare data rows
            rows = [headers]
            for contact in contacts:
                row = [
                    contact.id, contact.first_name, contact.last_name, contact.email,
                    contact.company_name, contact.position, contact.industry,
                    contact.phone or "", contact.linkedin_url or "", contact.website or "",
                    contact.company_size or "", contact.location or "",
                    contact.status.value, contact.lead_source, contact.assigned_to or "",
                    contact.lead_score, contact.estimated_value or "",
                    contact.expected_close_date or "", contact.created_at,
                    contact.updated_at, contact.last_contacted or "",
                    contact.notes or "", ", ".join(contact.tags)
                ]
                rows.append(row)
            
            # Update sheet
            self.sheet.update("A1", rows)
            print(f"✅ Synced {len(contacts)} contacts to Google Sheet")
            return True
            
        except Exception as e:
            print(f"❌ Error syncing to Google Sheet: {str(e)}")
            return False
    
    def import_contacts_from_sheet(self) -> List[CRMContact]:
        """Import contacts from Google Sheet"""
        try:
            if not self.sheet:
                raise Exception("Not connected to Google Sheet")
            
            # Get all values
            values = self.sheet.get_all_values()
            
            if len(values) < 2:
                print("⚠️  No data found in Google Sheet")
                return []
            
            headers = values[0]
            contacts = []
            
            for row in values[1:]:
                if len(row) < len(headers):
                    row.extend([""] * (len(headers) - len(row)))
                
                contact_data = dict(zip(headers, row))
                
                # Convert to CRMContact
                contact = CRMContact(
                    id=contact_data.get("ID") or str(uuid.uuid4()),
                    first_name=contact_data.get("First Name", ""),
                    last_name=contact_data.get("Last Name", ""),
                    email=contact_data.get("Email", ""),
                    company_name=contact_data.get("Company", ""),
                    position=contact_data.get("Position", ""),
                    industry=contact_data.get("Industry", ""),
                    phone=contact_data.get("Phone") or None,
                    linkedin_url=contact_data.get("LinkedIn") or None,
                    website=contact_data.get("Website") or None,
                    company_size=contact_data.get("Company Size") or None,
                    location=contact_data.get("Location") or None,
                    status=LeadStatus(contact_data.get("Status", "new")),
                    lead_source=contact_data.get("Lead Source", "google_sheets"),
                    assigned_to=contact_data.get("Assigned To") or None,
                    lead_score=int(contact_data.get("Lead Score", 0) or 0),
                    estimated_value=float(contact_data.get("Estimated Value", 0) or 0) or None,
                    expected_close_date=contact_data.get("Expected Close") or None,
                    created_at=contact_data.get("Created") or datetime.now().isoformat(),
                    updated_at=contact_data.get("Updated") or datetime.now().isoformat(),
                    last_contacted=contact_data.get("Last Contacted") or None,
                    notes=contact_data.get("Notes", ""),
                    tags=contact_data.get("Tags", "").split(", ") if contact_data.get("Tags") else []
                )
                
                contacts.append(contact)
            
            print(f"✅ Imported {len(contacts)} contacts from Google Sheet")
            return contacts
            
        except Exception as e:
            print(f"❌ Error importing from Google Sheet: {str(e)}")
            return []


class CRMSystem:
    """Main CRM system class"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.crm_config = config.get('crm', {})
        
        # Initialize database
        db_path = self.crm_config.get('database_path', 'crm.db')
        self.db = CRMDatabase(db_path)
        
        # Initialize Google Sheets integration
        self.sheets = GoogleSheetsIntegration(
            self.crm_config.get('google_credentials_path', 'google_credentials.json')
        )
        
        print("✅ CRM System initialized")
    
    def import_lead_to_crm(self, lead: Lead, source: str = "lead_collection") -> CRMContact:
        """Convert a Lead to CRMContact and add to database"""
        # Check if contact already exists
        existing_contact = self.db.get_contact_by_email(lead.email)
        
        if existing_contact:
            print(f"📋 Contact already exists: {lead.email}")
            return existing_contact
        
        # Create new CRM contact
        contact = CRMContact(
            id=str(uuid.uuid4()),
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            company_name=lead.company_name,
            position=lead.position,
            industry=lead.industry,
            phone=lead.phone,
            linkedin_url=lead.linkedin_url,
            website=lead.website,
            company_size=lead.company_size,
            location=lead.location,
            status=LeadStatus.NEW,
            lead_source=source,
            notes=lead.notes or ""
        )
        
        # Add to database
        self.db.insert_contact(contact)
        print(f"✅ Added new contact: {contact.first_name} {contact.last_name}")
        
        return contact
    
    def batch_import_leads(self, leads: List[Lead], source: str = "batch_import") -> List[CRMContact]:
        """Import multiple leads to CRM"""
        contacts = []
        
        for lead in leads:
            try:
                contact = self.import_lead_to_crm(lead, source)
                contacts.append(contact)
            except Exception as e:
                print(f"❌ Error importing lead {lead.email}: {str(e)}")
                continue
        
        print(f"✅ Batch import completed: {len(contacts)} contacts processed")
        return contacts
    
    def log_email_sent(self, contact_id: str, subject: str, content: str, 
                      campaign_id: str = None):
        """Log that an email was sent"""
        interaction = Interaction(
            id=str(uuid.uuid4()),
            contact_id=contact_id,
            interaction_type=InteractionType.EMAIL_SENT,
            subject=subject,
            content=content,
            timestamp=datetime.now().isoformat(),
            created_by="outreach_agent",
            metadata={
                "campaign_id": campaign_id,
                "email_length": len(content)
            }
        )
        
        self.db.add_interaction(interaction)
        print(f"📧 Logged email sent to contact {contact_id}")
    
    def update_contact_status(self, contact_id: str, status: LeadStatus, 
                            notes: str = None):
        """Update contact status"""
        contact = self.db.get_contact(contact_id)
        if not contact:
            print(f"❌ Contact not found: {contact_id}")
            return False
        
        contact.status = status
        if notes:
            contact.notes = contact.notes + "\n" + notes if contact.notes else notes
        
        self.db.update_contact(contact)
        print(f"✅ Updated contact status: {contact.email} -> {status.value}")
        return True
    
    def get_contacts_by_status(self, status: LeadStatus) -> List[CRMContact]:
        """Get contacts by status"""
        return self.db.search_contacts(status=status)
    
    def get_pipeline_report(self) -> Dict:
        """Generate pipeline report"""
        report = {}
        
        for status in LeadStatus:
            contacts = self.get_contacts_by_status(status)
            report[status.value] = {
                "count": len(contacts),
                "contacts": [f"{c.first_name} {c.last_name} ({c.company_name})" for c in contacts]
            }
        
        return report
    
    def sync_to_google_sheets(self, sheet_id: str, worksheet_name: str = "CRM Data"):
        """Sync all contacts to Google Sheets"""
        if not GOOGLE_SHEETS_AVAILABLE:
            print("❌ Google Sheets integration not available")
            return False
        
        try:
            # Connect to sheet
            if not self.sheets.connect_to_sheet(sheet_id, worksheet_name):
                return False
            
            # Get all contacts
            contacts = self.db.search_contacts(limit=10000)
            
            # Sync to sheet
            return self.sheets.sync_contacts_to_sheet(contacts)
            
        except Exception as e:
            print(f"❌ Error syncing to Google Sheets: {str(e)}")
            return False
    
    def import_from_google_sheets(self, sheet_id: str, worksheet_name: str = "CRM Data"):
        """Import contacts from Google Sheets"""
        if not GOOGLE_SHEETS_AVAILABLE:
            print("❌ Google Sheets integration not available")
            return []
        
        try:
            # Connect to sheet
            if not self.sheets.connect_to_sheet(sheet_id, worksheet_name):
                return []
            
            # Import contacts
            contacts = self.sheets.import_contacts_from_sheet()
            
            # Add to database
            for contact in contacts:
                try:
                    existing = self.db.get_contact_by_email(contact.email)
                    if existing:
                        self.db.update_contact(contact)
                    else:
                        self.db.insert_contact(contact)
                except Exception as e:
                    print(f"❌ Error importing contact {contact.email}: {str(e)}")
            
            return contacts
            
        except Exception as e:
            print(f"❌ Error importing from Google Sheets: {str(e)}")
            return []
    
    def export_to_csv(self, filename: str = None) -> str:
        """Export contacts to CSV"""
        if not filename:
            filename = f"crm_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        contacts = self.db.search_contacts(limit=10000)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'id', 'first_name', 'last_name', 'email', 'company_name', 'position',
                'industry', 'phone', 'linkedin_url', 'website', 'company_size',
                'location', 'status', 'lead_source', 'assigned_to', 'lead_score',
                'estimated_value', 'expected_close_date', 'created_at', 'updated_at',
                'last_contacted', 'notes', 'tags'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for contact in contacts:
                row = asdict(contact)
                row['status'] = contact.status.value
                row['tags'] = ', '.join(contact.tags) if contact.tags else ''
                writer.writerow(row)
        
        print(f"✅ Exported {len(contacts)} contacts to {filename}")
        return filename
    
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        total_contacts = len(self.db.search_contacts(limit=10000))
        
        # Get recent activity
        recent_contacts = self.db.search_contacts(limit=10)
        
        # Pipeline stats
        pipeline = self.get_pipeline_report()
        
        stats = {
            "total_contacts": total_contacts,
            "recent_contacts": len(recent_contacts),
            "pipeline_summary": {
                "new_leads": pipeline.get("new", {}).get("count", 0),
                "contacted": pipeline.get("contacted", {}).get("count", 0),
                "qualified": pipeline.get("qualified", {}).get("count", 0),
                "closed_won": pipeline.get("closed_won", {}).get("count", 0),
                "closed_lost": pipeline.get("closed_lost", {}).get("count", 0)
            },
            "conversion_rates": {
                "contact_to_response": 0,  # Would need interaction data
                "response_to_qualified": 0,
                "qualified_to_closed": 0
            }
        }
        
        return stats


def convert_lead_to_crm_contact(lead: Lead, source: str = "lead_collection") -> CRMContact:
    """Utility function to convert Lead to CRMContact"""
    return CRMContact(
        id=str(uuid.uuid4()),
        first_name=lead.first_name,
        last_name=lead.last_name,
        email=lead.email,
        company_name=lead.company_name,
        position=lead.position,
        industry=lead.industry,
        phone=lead.phone,
        linkedin_url=lead.linkedin_url,
        website=lead.website,
        company_size=lead.company_size,
        location=lead.location,
        status=LeadStatus.NEW,
        lead_source=source,
        notes=lead.notes or ""
    )


# Example usage and testing
if __name__ == "__main__":
    # Example configuration
    config = {
        'crm': {
            'database_path': 'test_crm.db',
            'google_credentials_path': 'google_credentials.json'
        }
    }
    
    # Initialize CRM
    crm = CRMSystem(config)
    
    # Example lead data
    from lead_manager import Lead
    
    sample_lead = Lead(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        company_name="Example Corp",
        position="CEO",
        industry="Technology",
        phone="+1-555-0123",
        linkedin_url="https://linkedin.com/in/johndoe",
        website="https://example.com",
        location="San Francisco, CA",
        notes="Interested in AI solutions"
    )
    
    # Import lead to CRM
    contact = crm.import_lead_to_crm(sample_lead, "demo")
    
    # Log an email sent
    crm.log_email_sent(
        contact.id,
        "Introduction to Our AI Solutions",
        "Hi John, I wanted to introduce you to our AI solutions...",
        "demo_campaign"
    )
    
    # Update status
    crm.update_contact_status(contact.id, LeadStatus.CONTACTED, "Initial outreach sent")
    
    # Get dashboard stats
    stats = crm.get_dashboard_stats()
    print(f"Dashboard stats: {stats}")
    
    # Export to CSV
    crm.export_to_csv("demo_export.csv")
    
    print("✅ CRM demo completed!")