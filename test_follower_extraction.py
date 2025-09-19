#!/usr/bin/env python3
"""
Test the updated follower count extraction functionality
"""

from instagram_follower_extractor import InstagramFollowerExtractor
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)

def test_follower_extraction():
    """Test follower count extraction with a fresh comedian"""
    
    print("Testing Updated Follower Count Extraction")
    print("="*50)
    
    extractor = InstagramFollowerExtractor()
    
    # Test with a comedian not in database
    test_comedian = "Kevin Hart"
    
    print(f"Testing follower extraction for: {test_comedian}")
    print("This will search for Instagram profile and attempt to extract followers...")
    print()
    
    # Search for Instagram profile
    search_result = extractor.search_comedian_instagram(test_comedian)
    
    if search_result:
        instagram_url = search_result['instagram_url']
        follower_count = search_result.get('follower_count', 0)
        
        print(f"✓ Found Instagram: {instagram_url}")
        print(f"✓ Follower count from search: {follower_count}")
        
        if follower_count > 0:
            print("🎉 Successfully extracted follower count from Google search!")
        else:
            print("⚠️  No follower count in search results, but found profile!")
    else:
        print("✗ No Instagram profile found")

if __name__ == "__main__":
    test_follower_extraction()