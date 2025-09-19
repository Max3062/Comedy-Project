#!/usr/bin/env python3
"""
Debug test for Jim Gaffigan specifically
"""

from instagram_follower_extractor import InstagramFollowerExtractor
import logging

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)

def debug_jim_gaffigan():
    """Debug Jim Gaffigan extraction specifically"""
    
    print("Debugging Jim Gaffigan Instagram Detection")
    print("="*50)
    
    extractor = InstagramFollowerExtractor()
    
    # Test username validation directly
    test_usernames = [
        "jimgaffigan",
        "leannemorgancomedy", 
        "sebastiancomedy",
        "jimgaffiganofficial"
    ]
    
    comedian_name = "Jim Gaffigan"
    
    print(f"Testing username validation for: {comedian_name}")
    print("-" * 30)
    
    for username in test_usernames:
        is_valid = extractor._validate_instagram_profile(username, comedian_name)
        print(f"Username: {username:<20} Valid: {is_valid}")
    
    print("\n" + "="*50)
    print("FULL SEARCH PROCESS")
    print("="*50)
    
    # Now run the full search
    result = extractor.search_comedian_instagram(comedian_name)
    
    if result:
        print(f"\nFinal Result:")
        print(f"  URL: {result['instagram_url']}")
        print(f"  Followers: {result.get('follower_count', 0):,}")
        print(f"  Confidence: {result.get('confidence_score', 0):.2f}")

if __name__ == "__main__":
    debug_jim_gaffigan()