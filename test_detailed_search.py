#!/usr/bin/env python3
"""
Test with detailed Google search results display
"""

from instagram_follower_extractor import InstagramFollowerExtractor
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_with_search_results():
    """Test showing the actual Google search results"""
    
    print("Testing with Detailed Google Search Results")
    print("="*60)
    
    extractor = InstagramFollowerExtractor()
    
    # Test with one comedian to see detailed results
    test_comedian = "Jim Gaffigan"
    
    print(f"Testing: {test_comedian}")
    print("="*40)
    
    # Let's manually call the search to see raw results
    search_queries = [
        f"{test_comedian} comedian instagram",
        f"{test_comedian} stand up comedy instagram",
        f"{test_comedian} instagram profile"
    ]
    
    for i, query in enumerate(search_queries, 1):
        print(f"\n{i}. Search Query: '{query}'")
        print("-" * 50)
        
        try:
            import requests
            params = {
                'key': extractor.google_api_key,
                'cx': extractor.google_cse_id,
                'q': query,
                'num': 5  # Get top 5 results for display
            }
            
            response = requests.get(extractor.base_search_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'items' in data:
                for j, item in enumerate(data['items'], 1):
                    title = item.get('title', 'No title')
                    link = item.get('link', 'No link')
                    snippet = item.get('snippet', 'No snippet')
                    
                    print(f"\n  Result {j}:")
                    print(f"    Title: {title}")
                    print(f"    Link: {link}")
                    print(f"    Snippet: {snippet}")
                    
                    # Check if this contains Instagram info
                    full_text = f"{title} {snippet}".lower()
                    if 'instagram' in full_text:
                        print(f"    🔍 Contains Instagram mention")
                        
                        # Check for follower patterns
                        import re
                        follower_patterns = [
                            r'(\d+(?:\.\d+)?)\s*([kmb])\s*followers',
                            r'(\d{1,3}(?:,\d{3})*)\s*followers',
                            r'followers[\s:]*(\d+(?:\.\d+)?)\s*([kmb])',
                        ]
                        
                        for pattern in follower_patterns:
                            matches = re.findall(pattern, full_text)
                            if matches:
                                print(f"    📊 Found follower pattern: {matches}")
                                break
            else:
                print("    No search results found")
                
        except Exception as e:
            print(f"    Error: {e}")
    
    print("\n" + "="*60)
    print("NOW TESTING THE EXTRACTOR'S INTERPRETATION")
    print("="*60)
    
    # Now test our extractor's interpretation
    search_result = extractor.search_comedian_instagram(test_comedian)
    
    if search_result:
        print(f"\nExtractor Results:")
        print(f"  Instagram URL: {search_result['instagram_url']}")
        print(f"  Follower Count: {search_result.get('follower_count', 0):,}")
        print(f"  Confidence Score: {search_result.get('confidence_score', 0):.2f}")
        print(f"  Search Snippet: {search_result.get('search_snippet', 'N/A')}")
    else:
        print("\nExtractor found no results")

def test_multiple_with_details():
    """Test multiple comedians with basic details"""
    
    print("\n" + "="*60)
    print("TESTING MULTIPLE COMEDIANS WITH DETAILS")
    print("="*60)
    
    extractor = InstagramFollowerExtractor()
    
    comedians = ["Amy Schumer", "Sebastian Maniscalco", "Nikki Glaser"]
    
    for comedian in comedians:
        print(f"\nTesting: {comedian}")
        print("-" * 30)
        
        search_result = extractor.search_comedian_instagram(comedian)
        
        if search_result:
            print(f"✓ Found: {search_result['instagram_url']}")
            print(f"  Followers: {search_result.get('follower_count', 0):,}")
            print(f"  Confidence: {search_result.get('confidence_score', 0):.2f}")
            
            # Show a snippet of the search result that led to this
            snippet = search_result.get('search_snippet', '')
            if snippet:
                snippet_preview = snippet[:100] + "..." if len(snippet) > 100 else snippet
                print(f"  From snippet: '{snippet_preview}'")
        else:
            print("✗ No Instagram found")

if __name__ == "__main__":
    test_with_search_results()
    test_multiple_with_details()