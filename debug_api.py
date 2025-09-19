#!/usr/bin/env python3
"""
Debug script to understand the API response structure
"""

from Lineup_scraper import ComedyCellarScraper
import json
import re

def debug_api_response():
    """Debug the API response structure"""
    scraper = ComedyCellarScraper()
    
    # Test with several dates
    test_dates = ["2024-12-01", "2024-11-30", "2024-11-29", "2023-12-01", "2023-06-15"]
    
    for test_date in test_dates:
        print(f"\n{'='*50}")
        print(f"Testing {test_date}")
        print('='*50)
        
        response = scraper.make_api_request(test_date)
        
        if response:
            print("✓ Got response")
            print(f"Keys: {list(response.keys())}")
            
            # Check the show structure
            if 'show' in response:
                show = response['show']
                print(f"Show keys: {list(show.keys())}")
                
                if 'html' in show and show['html']:
                    html = show['html']
                    print(f"HTML length: {len(html)}")
                    
                    # Extract show information from HTML using regex
                    # Look for show times and venues
                    time_pattern = r'<span class="bold">([^<]+)<span class="hide-mobile">'
                    venue_pattern = r'<span class="title">([^<]+)</span>'
                    
                    times = re.findall(time_pattern, html)
                    venues = re.findall(venue_pattern, html)
                    
                    print(f"Found {len(times)} show times: {times}")
                    print(f"Found {len(venues)} venues: {venues}")
                    
                    # Look for comedian names
                    name_pattern = r'<span class="name">([^<]+)</span>'
                    names = re.findall(name_pattern, html)
                    print(f"Found {len(names)} comedian names: {names[:5]}...")  # Show first 5
                
                if 'date' in show:
                    print(f"Date: {show['date']}")
            
            # Check if there's dates data
            if 'dates' in response:
                dates_data = response['dates']
                print(f"Dates data keys: {list(dates_data.keys())}")
        else:
            print("✗ No response")

if __name__ == "__main__":
    debug_api_response()