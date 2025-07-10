#!/usr/bin/env python3
"""
Test script for lead collection tools

This script demonstrates how to use the intelligent lead collection system
with different tools and data sources.
"""

import os
import sys
import asyncio
from typing import List, Dict
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lead_collection_tools import (
    LeadCollectionAgent, 
    get_available_tools, 
    validate_tool_requirements,
    Lead
)

# Load environment variables
load_dotenv()

def test_tool_availability():
    """Test which tools are available"""
    print("🔍 TESTING TOOL AVAILABILITY")
    print("="*50)
    
    available_tools = get_available_tools()
    print(f"Available tools: {available_tools}")
    
    for tool in ['playwright', 'serpapi', 'sales_nav']:
        requirements = validate_tool_requirements(tool)
        status = "✅" if requirements['available'] else "❌"
        print(f"{status} {tool}: {'Available' if requirements['available'] else 'Not available'}")
        
        if requirements['missing']:
            print(f"   Missing: {', '.join(requirements['missing'])}")
    
    print()

def test_agent_initialization():
    """Test agent initialization"""
    print("🤖 TESTING AGENT INITIALIZATION")
    print("="*50)
    
    # Load configuration
    config = {
        'lead_collection_tools': {
            'playwright': {
                'rate_limit_seconds': 2,
                'timeout_seconds': 30,
                'max_retries': 3
            },
            'serpapi': {
                'rate_limit_seconds': 1
            },
            'sales_nav': {
                'enable_enrichment': True
            }
        }
    }
    
    try:
        agent = LeadCollectionAgent(config)
        print("✅ Agent initialized successfully")
        
        # Get capabilities
        capabilities = agent.get_tool_capabilities()
        print(f"✅ Found {len(capabilities)} tool capabilities")
        
        for cap in capabilities:
            print(f"   - {cap.name}: {cap.description}")
        
        return agent
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {str(e)}")
        return None

def test_tool_recommendations():
    """Test tool recommendation system"""
    print("🎯 TESTING TOOL RECOMMENDATIONS")
    print("="*50)
    
    config = {
        'lead_collection_tools': {
            'playwright': {'rate_limit_seconds': 2},
            'serpapi': {'rate_limit_seconds': 1},
            'sales_nav': {'enable_enrichment': True}
        }
    }
    
    agent = LeadCollectionAgent(config)
    
    # Test different scenarios
    test_scenarios = [
        {
            'name': 'LinkedIn Profile Scraping',
            'request': {
                'task_type': 'profile_scraping',
                'input_data': {
                    'linkedin_urls': ['https://linkedin.com/in/example1', 'https://linkedin.com/in/example2']
                },
                'constraints': {'budget': 'free'}
            }
        },
        {
            'name': 'Company Search',
            'request': {
                'task_type': 'company_research',
                'input_data': {
                    'search_queries': ['tech startups San Francisco', 'AI companies']
                },
                'constraints': {'budget': 'low', 'speed': 'fast'}
            }
        },
        {
            'name': 'Sales Navigator CSV',
            'request': {
                'task_type': 'bulk_collection',
                'input_data': {
                    'csv_file': 'sales_nav_export.csv',
                    'source': 'sales_nav'
                },
                'constraints': {'budget': 'free', 'accuracy': 'high'}
            }
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        recommendation = agent.recommend_tool(scenario['request'])
        print(f"   🎯 Recommended: {recommendation['recommended_tool']}")
        print(f"   🔍 Confidence: {recommendation['confidence']:.2f}")
        print(f"   💭 Reasoning: {recommendation['reasoning']}")
        
        if recommendation['alternatives']:
            print(f"   🔄 Alternatives: {[alt['tool'] for alt in recommendation['alternatives']]}")
    
    print()

def test_sales_nav_processing():
    """Test Sales Navigator CSV processing"""
    print("📊 TESTING SALES NAVIGATOR PROCESSING")
    print("="*50)
    
    # Create a sample CSV file for testing
    sample_csv_content = """First Name,Last Name,Email,Company,Title,Industry,Location,LinkedIn URL
John,Smith,john.smith@techcorp.com,TechCorp,CEO,Technology,San Francisco,https://linkedin.com/in/johnsmith
Jane,Doe,jane.doe@innovate.com,InnovateInc,CTO,Software,New York,https://linkedin.com/in/janedoe
"""
    
    test_csv_path = 'test_sales_nav.csv'
    
    try:
        # Write sample CSV
        with open(test_csv_path, 'w') as f:
            f.write(sample_csv_content)
        
        config = {
            'lead_collection_tools': {
                'sales_nav': {
                    'enable_enrichment': True,
                    'clean_data': True
                }
            }
        }
        
        agent = LeadCollectionAgent(config)
        
        # Test processing
        parameters = {
            'csv_file': test_csv_path,
            'enrich_data': True,
            'clean_data': True
        }
        
        leads = agent.tools['sales_nav'].process_sales_nav_csv(parameters)
        
        print(f"✅ Processed {len(leads)} leads from CSV")
        
        for i, lead in enumerate(leads):
            print(f"   {i+1}. {lead.first_name} {lead.last_name} - {lead.position} at {lead.company_name}")
            print(f"      📧 {lead.email}")
            print(f"      🔗 {lead.linkedin_url}")
        
        # Clean up
        os.remove(test_csv_path)
        
    except Exception as e:
        print(f"❌ Sales Navigator processing failed: {str(e)}")
        # Clean up on error
        if os.path.exists(test_csv_path):
            os.remove(test_csv_path)

async def test_playwright_scraping():
    """Test Playwright scraping (if available)"""
    print("🎭 TESTING PLAYWRIGHT SCRAPING")
    print("="*50)
    
    try:
        from playwright.async_api import async_playwright
        
        config = {
            'lead_collection_tools': {
                'playwright': {
                    'rate_limit_seconds': 2,
                    'timeout_seconds': 30,
                    'max_retries': 3
                }
            }
        }
        
        agent = LeadCollectionAgent(config)
        
        if 'playwright' not in agent.tools:
            print("❌ Playwright tool not available")
            return
        
        # Test with a simple example (using a public site)
        # Note: LinkedIn scraping requires proper authentication
        parameters = {
            'urls': ['https://example.com'],  # Safe test URL
            'source_type': 'company_website',
            'max_leads': 1
        }
        
        leads = await agent.tools['playwright'].scrape_leads(parameters)
        
        print(f"✅ Playwright scraping test completed")
        print(f"   Results: {len(leads)} leads collected")
        
    except ImportError:
        print("⚠️  Playwright not installed, skipping test")
    except Exception as e:
        print(f"❌ Playwright scraping failed: {str(e)}")

async def test_serpapi_search():
    """Test SerpAPI search (if available)"""
    print("🔍 TESTING SERPAPI SEARCH")
    print("="*50)
    
    if not os.getenv('SERPAPI_KEY'):
        print("⚠️  SERPAPI_KEY not set, skipping test")
        return
    
    try:
        from serpapi import GoogleSearch
        
        config = {
            'lead_collection_tools': {
                'serpapi': {
                    'rate_limit_seconds': 1
                }
            }
        }
        
        agent = LeadCollectionAgent(config)
        
        if 'serpapi' not in agent.tools:
            print("❌ SerpAPI tool not available")
            return
        
        # Test search
        parameters = {
            'queries': ['tech companies San Francisco'],
            'max_results': 3,
            'filters': {'location': 'San Francisco'}
        }
        
        leads = await agent.tools['serpapi'].search_leads(parameters)
        
        print(f"✅ SerpAPI search test completed")
        print(f"   Results: {len(leads)} leads collected")
        
        for i, lead in enumerate(leads):
            print(f"   {i+1}. {lead.company_name}")
            print(f"      🌐 {lead.website}")
        
    except ImportError:
        print("⚠️  SerpAPI not installed, skipping test")
    except Exception as e:
        print(f"❌ SerpAPI search failed: {str(e)}")

async def test_full_integration():
    """Test full integration with intelligent tool selection"""
    print("🚀 TESTING FULL INTEGRATION")
    print("="*50)
    
    config = {
        'lead_collection_tools': {
            'playwright': {
                'rate_limit_seconds': 2,
                'timeout_seconds': 30,
                'max_retries': 3
            },
            'serpapi': {
                'rate_limit_seconds': 1
            },
            'sales_nav': {
                'enable_enrichment': True,
                'clean_data': True
            }
        }
    }
    
    agent = LeadCollectionAgent(config)
    
    # Test intelligent collection with different inputs
    test_requests = [
        {
            'name': 'CSV Processing',
            'request': {
                'task_type': 'bulk_collection',
                'input_data': {
                    'csv_file': 'leads.csv',
                    'source': 'sales_nav'
                },
                'constraints': {'budget': 'free'},
                'max_leads': 5
            }
        }
    ]
    
    for test_case in test_requests:
        print(f"\n📋 Testing: {test_case['name']}")
        
        # Get recommendation
        recommendation = agent.recommend_tool(test_case['request'])
        print(f"   🎯 Recommended: {recommendation['recommended_tool']}")
        print(f"   🔍 Confidence: {recommendation['confidence']:.2f}")
        print(f"   💭 Reasoning: {recommendation['reasoning']}")
        
        # Note: We don't actually collect leads here to avoid API calls
        # In a real scenario, you would call:
        # leads = await agent.collect_leads(recommendation['recommended_tool'], parameters)
    
    print("\n✅ Full integration test completed")

def main():
    """Run all tests"""
    print("🧪 LEAD COLLECTION TOOLS TEST SUITE")
    print("="*60)
    print()
    
    # Test 1: Tool availability
    test_tool_availability()
    
    # Test 2: Agent initialization
    agent = test_agent_initialization()
    if not agent:
        print("❌ Cannot continue tests without agent")
        return
    
    print()
    
    # Test 3: Tool recommendations
    test_tool_recommendations()
    
    # Test 4: Sales Navigator processing
    test_sales_nav_processing()
    
    print()
    
    # Test 5: Async tests
    print("🔄 RUNNING ASYNC TESTS")
    print("="*50)
    
    async def run_async_tests():
        await test_playwright_scraping()
        print()
        await test_serpapi_search()
        print()
        await test_full_integration()
    
    asyncio.run(run_async_tests())
    
    print("\n🎉 ALL TESTS COMPLETED!")
    print("="*60)
    
    # Print summary
    print("\n📋 SUMMARY")
    print("="*30)
    print("✅ Tool availability check completed")
    print("✅ Agent initialization test completed")
    print("✅ Tool recommendation system tested")
    print("✅ Sales Navigator processing tested")
    print("✅ Async tool tests completed")
    print("✅ Full integration test completed")
    
    print("\n💡 NEXT STEPS:")
    print("1. Install missing dependencies if needed:")
    print("   pip install playwright serpapi")
    print("   playwright install")
    print("2. Set up API keys in .env file")
    print("3. Test with real data using main.py")
    print("   python main.py --tool-capabilities")
    print("   python main.py --collect-leads --sales-nav-csv your_file.csv")

if __name__ == "__main__":
    main()