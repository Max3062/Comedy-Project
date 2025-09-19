#!/usr/bin/env python3
"""
Test script for the Comedy Cellar scraper
"""

from Lineup_scraper import ComedyCellarScraper
from datetime import date, datetime
import json

def test_api_request():
    """Test a single API request"""
    scraper = ComedyCellarScraper()
    
    # Test with a recent date that likely has data
    test_date = "2024-12-01"  # Saturday in December
    
    print(f"Testing API request for {test_date}...")
    
    response = scraper.make_api_request(test_date)
    
    if response:
        print("✓ API request successful!")
        print(f"Response keys: {list(response.keys())}")
        
        # Print the structure to understand the data format
        print("\nResponse structure:")
        print(json.dumps(response, indent=2)[:500] + "..." if len(str(response)) > 500 else json.dumps(response, indent=2))
        
        return True
    else:
        print("✗ API request failed!")
        return False

def test_date_scraping():
    """Test scraping a single date"""
    scraper = ComedyCellarScraper()
    
    # Test with a date that likely has shows
    test_date = date(2024, 12, 7)  # A Saturday
    
    print(f"\nTesting date scraping for {test_date}...")
    
    shows = scraper.scrape_date(test_date)
    
    print(f"Found {len(shows)} shows")
    
    for i, show in enumerate(shows):
        print(f"\nShow {i+1}:")
        print(f"  ID: {show.show_id}")
        print(f"  Time: {show.time}")
        print(f"  Venue: {show.venue}")
        print(f"  Comedians: {len(show.comedians)}")
        
        for j, comedian in enumerate(show.comedians[:3]):  # Show first 3 comedians
            print(f"    {j+1}. {comedian.name}")
        
        if len(show.comedians) > 3:
            print(f"    ... and {len(show.comedians) - 3} more")
    
    return shows

def test_csv_export():
    """Test CSV export functionality"""
    scraper = ComedyCellarScraper()
    
    # Create some test data
    test_date = date(2024, 12, 7)
    shows = scraper.scrape_date(test_date)
    
    if shows:
        print(f"\nTesting CSV export with {len(shows)} shows...")
        
        try:
            main_file = scraper.export_to_csv(shows, "test_export")
            print(f"✓ CSV export successful!")
            print(f"Main file: {main_file}")
            return True
        except Exception as e:
            print(f"✗ CSV export failed: {e}")
            return False
    else:
        print("No shows to export")
        return False

if __name__ == "__main__":
    print("Comedy Cellar Scraper Test Suite")
    print("=" * 40)
    
    # Run tests
    api_success = test_api_request()
    
    if api_success:
        shows = test_date_scraping()
        if shows:
            test_csv_export()
        else:
            print("No shows found for testing CSV export")
    
    print("\nTest completed!")