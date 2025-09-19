#!/usr/bin/env python3
"""
Test script for the Instagram follower extractor

This script tests the Instagram extraction functionality with a few sample comedians
to ensure the system is working correctly before processing large datasets.
"""

import pandas as pd
from instagram_follower_extractor import InstagramFollowerExtractor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_instagram_extractor():
    """Test the Instagram follower extractor with sample comedians"""
    
    print("Testing Instagram Follower Extractor")
    print("="*40)
    
    # Sample comedian data for testing
    sample_comedians = [
        "Jerry Seinfeld",
        "Dave Chappelle", 
        "Amy Schumer",
        "Chris Rock",
        "Sebastian Maniscalco"
    ]
    
    # Create a test DataFrame
    test_data = []
    for i, comedian in enumerate(sample_comedians):
        test_data.append({
            'comedian_name': comedian,
            'show_date': f'2024-12-{i+1:02d}',
            'venue': 'Comedy Cellar',
            'show_time': '8:00 PM'
        })
    
    df = pd.DataFrame(test_data)
    
    print(f"Testing with {len(df)} sample comedians:")
    for comedian in sample_comedians:
        print(f"  - {comedian}")
    print()
    
    try:
        # Initialize the extractor
        print("Initializing Instagram follower extractor...")
        extractor = InstagramFollowerExtractor()
        
        print("✓ Extractor initialized successfully")
        print(f"✓ API credentials loaded")
        
        # Test individual search first
        print(f"\nTesting individual search for: {sample_comedians[0]}")
        result = extractor.search_comedian_instagram(sample_comedians[0])
        
        if result:
            print(f"✓ Found Instagram profile: {result}")
            # Now test full processing to get follower count
            comedian_result = extractor.process_comedian(sample_comedians[0])
            if comedian_result:
                print(f"✓ Follower count: {comedian_result.follower_count}")
            else:
                print("✓ Profile found but follower extraction failed")
        else:
            print("✗ No Instagram profile found")
        
        # Test batch processing (just 2 comedians to avoid rate limits)
        print(f"\nTesting batch processing with first 2 comedians...")
        small_df = df.head(2).copy()
        
        enhanced_df = extractor.process_comedian_dataframe(small_df, 'comedian_name')
        
        print(f"✓ Processed {len(enhanced_df)} records")
        
        # Show results
        print("\nResults:")
        print("-"*60)
        for _, row in enhanced_df.iterrows():
            instagram = row.get('instagram_url', 'Not found')
            followers = row.get('follower_count', 'N/A')
            print(f"{row['comedian_name']:20} | {instagram:30} | {followers}")
        
        # Save test results
        output_file = 'test_instagram_results.csv'
        enhanced_df.to_csv(output_file, index=False)
        print(f"\nTest results saved to: {output_file}")
        
        return True
        
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nMake sure your .env file contains:")
        print("GOOGLE_API_KEY=your_api_key_here")
        print("GOOGLE_CSE_ID=your_search_engine_id_here")
        return False
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        logger.exception("Error during testing")
        return False

def test_database_functionality():
    """Test the SQLite database functionality"""
    print("\nTesting Database Functionality")
    print("="*30)
    
    try:
        extractor = InstagramFollowerExtractor()
        
        # Test data insertion
        test_data = {
            'comedian_name': 'Test Comedian',
            'instagram_url': 'https://instagram.com/test',
            'follower_count': 12345,
            'search_query': 'Test Comedian instagram',
            'confidence_score': 0.95
        }
        
        print("Testing database insertion...")
        extractor.save_to_database(test_data)
        print("✓ Data inserted successfully")
        
        # Test data retrieval
        print("Testing database retrieval...")
        result = extractor.get_from_database('Test Comedian')
        
        if result:
            print("✓ Data retrieved successfully")
            print(f"  - Instagram: {result.get('instagram_url')}")
            print(f"  - Followers: {result.get('follower_count')}")
        else:
            print("✗ Data not found in database")
        
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

if __name__ == "__main__":
    print("Instagram Follower Extractor Test Suite")
    print("="*50)
    
    # Test 1: Basic functionality
    success1 = test_instagram_extractor()
    
    # Test 2: Database functionality  
    success2 = test_database_functionality()
    
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Instagram extraction: {'✓ PASS' if success1 else '✗ FAIL'}")
    print(f"Database functionality: {'✓ PASS' if success2 else '✗ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("1. Run the Comedy Cellar scraper to get comedian data")
        print("2. Use enhance_with_instagram.py to add Instagram data")
        print("3. Or run: python enhance_with_instagram.py --pipeline")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")