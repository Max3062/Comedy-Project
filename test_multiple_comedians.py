#!/usr/bin/env python3
"""
Test the Google search follower extraction with multiple comedians
"""

from instagram_follower_extractor import InstagramFollowerExtractor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_multiple_comedians():
    """Test follower extraction with several comedians"""
    
    print("Testing Google Search Follower Extraction")
    print("="*50)
    
    extractor = InstagramFollowerExtractor()
    
    # Test with various comedians (mix of famous and less famous)
    test_comedians = [
        "Amy Schumer",
        "Jim Gaffigan", 
        "Sebastian Maniscalco",
        "Nikki Glaser",
        "Mark Normand"
    ]
    
    results = []
    
    for comedian in test_comedians:
        print(f"\nTesting: {comedian}")
        print("-" * 30)
        
        search_result = extractor.search_comedian_instagram(comedian)
        
        if search_result:
            instagram_url = search_result['instagram_url']
            follower_count = search_result.get('follower_count', 0)
            confidence = search_result.get('confidence_score', 0)
            
            print(f"✓ Instagram: {instagram_url}")
            print(f"✓ Followers: {follower_count:,}")
            print(f"✓ Confidence: {confidence:.2f}")
            
            results.append({
                'comedian': comedian,
                'instagram': instagram_url,
                'followers': follower_count,
                'success': follower_count > 0
            })
        else:
            print("✗ No Instagram found")
            results.append({
                'comedian': comedian,
                'instagram': None,
                'followers': 0,
                'success': False
            })
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    successful_extractions = sum(1 for r in results if r['success'])
    found_profiles = sum(1 for r in results if r['instagram'])
    
    print(f"Comedians tested: {len(test_comedians)}")
    print(f"Instagram profiles found: {found_profiles}/{len(test_comedians)}")
    print(f"Follower counts extracted: {successful_extractions}/{len(test_comedians)}")
    print(f"Success rate: {successful_extractions/len(test_comedians)*100:.1f}%")
    
    print("\nDetailed Results:")
    print("-" * 80)
    print(f"{'Comedian':<20} {'Followers':<15} {'Status':<15} {'Instagram'}")
    print("-" * 80)
    
    for result in results:
        status = "✓ Success" if result['success'] else ("✓ Profile" if result['instagram'] else "✗ Not found")
        followers_str = f"{result['followers']:,}" if result['followers'] > 0 else "N/A"
        instagram_str = result['instagram'] or "N/A"
        
        print(f"{result['comedian']:<20} {followers_str:<15} {status:<15} {instagram_str}")

if __name__ == "__main__":
    test_multiple_comedians()