#!/usr/bin/env python3
"""
Instagram Follower Extractor for Comedy Cellar Comedians

This module uses Google Search API to find comedian Instagram profiles
and extracts their follower counts. It maintains a database of comedians
and their social media metrics.

Author: Data Science Team
Date: 2025
"""

import os
import requests
import json
import csv
import time
import logging
import re
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import sqlite3
from datetime import datetime
import urllib.parse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_follower_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ComedianInstagram:
    """Data class for comedian Instagram information"""
    name: str
    instagram_username: str
    instagram_url: str
    follower_count: int
    followers_text: str
    last_updated: str
    search_attempts: int = 0
    verified: bool = False

class InstagramFollowerExtractor:
    """
    Extracts Instagram follower counts for comedians using Google Search API
    """
    
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_cse_id = os.getenv('GOOGLE_CSE_ID')
        
        if not self.google_api_key or not self.google_cse_id:
            raise ValueError("Google API key and CSE ID must be set in .env file")
        
        self.base_search_url = "https://www.googleapis.com/customsearch/v1"
        self.rate_limit_delay = 1.0  # Google allows 100 queries/day for free
        self.max_retries = 3
        self.database_path = "comedian_instagram_data.db"
        
        # Initialize database
        self._init_database()
        
        logger.info("Instagram Follower Extractor initialized")
    
    def _init_database(self):
        """Initialize SQLite database for storing comedian data"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comedians (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                instagram_username TEXT,
                instagram_url TEXT,
                follower_count INTEGER,
                followers_text TEXT,
                last_updated TEXT,
                search_attempts INTEGER DEFAULT 0,
                verified BOOLEAN DEFAULT FALSE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def search_comedian_instagram(self, comedian_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for comedian's Instagram profile using Google Search API
        
        Args:
            comedian_name: Name of the comedian
            
        Returns:
            Dictionary with instagram_url and follower_count if found, None otherwise
        """
        try:
            # Multiple search queries to increase chances of finding the profile
            search_queries = [
                f"{comedian_name} comedian instagram",
                f"{comedian_name} stand up comedy instagram",
                f"{comedian_name} instagram profile",
                f'"{comedian_name}" instagram comedian'
            ]
            
            for query in search_queries:
                logger.info(f"Searching for: {query}")
                
                params = {
                    'key': self.google_api_key,
                    'cx': self.google_cse_id,
                    'q': query,
                    'num': 10  # Get top 10 results
                }
                
                response = requests.get(self.base_search_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Look for Instagram URLs and follower counts in the results
                result = self._extract_instagram_data(data, comedian_name)
                
                if result:
                    logger.info(f"Found Instagram for {comedian_name}: {result['instagram_url']}")
                    if result.get('follower_count', 0) > 0:
                        logger.info(f"Found follower count from search: {result['follower_count']}")
                    return result
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
            
            logger.warning(f"No Instagram found for {comedian_name}")
            return None
            
        except requests.RequestException as e:
            logger.error(f"Search request failed for {comedian_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error searching for {comedian_name}: {e}")
            return None
    
    def _extract_instagram_data(self, search_data: Dict, comedian_name: str) -> Optional[Dict[str, Any]]:
        """
        Extract Instagram URL and follower count from Google search results
        Uses og:description metadata for reliable follower count extraction
        
        Args:
            search_data: Google search API response
            comedian_name: Name of the comedian for validation
            
        Returns:
            Dictionary with instagram_url and follower_count if found
        """
        if 'items' not in search_data:
            return None
        
        best_result = None
        
        for item in search_data['items']:
            link = item.get('link', '')
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            
            # Focus on Instagram URLs only for most reliable results
            if 'instagram.com' not in link:
                continue
            
            # Extract username from URL
            username = self._extract_username_from_url(link)
            if not username:
                continue
                
            # Create basic result
            instagram_url = f"https://www.instagram.com/{username}/"
            result = {
                'instagram_url': instagram_url,
                'follower_count': 0,
                'search_snippet': snippet,
                'confidence_score': self._calculate_confidence(comedian_name, username, f"{title} {snippet}")
            }
            
            # Try to extract follower count from og:description (most reliable)
            follower_count = self._extract_followers_from_og_description(item)
            
            if follower_count > 0:
                logger.info(f"Found follower count in search results: {follower_count}")
                result['follower_count'] = follower_count
                result['source'] = 'og_description'
                return result
            
            # Fallback: try to extract from snippet and title
            fallback_count = self._extract_followers_from_text(f"{title} {snippet}")
            if fallback_count > 0:
                result['follower_count'] = fallback_count
                result['source'] = 'search_text'
                if not best_result:
                    best_result = result
            elif not best_result:
                result['source'] = 'profile_only'
                best_result = result
        
        return best_result
    
    def _extract_followers_from_og_description(self, search_item: Dict) -> int:
        """
        Extract follower count from og:description metadata (most reliable method)
        
        Args:
            search_item: Individual search result item from Google API
            
        Returns:
            Follower count as integer, 0 if not found
        """
        try:
            # Check if this result has pagemap data
            if 'pagemap' not in search_item or 'metatags' not in search_item['pagemap']:
                return 0
                
            metatag = search_item['pagemap']['metatags'][0]
            og_desc = metatag.get('og:description', '')
            
            if not og_desc:
                return 0
            
            # Instagram format: "2M Followers, 1,038 Following, 757 Posts"
            # This is the most reliable pattern from Instagram's og:description
            instagram_pattern = r'(\d+(?:\.\d+)?)\s*([MK]?)\s*Followers'
            match = re.search(instagram_pattern, og_desc, re.IGNORECASE)
            
            if match:
                count_str = match.group(1)
                unit = match.group(2).upper() if match.group(2) else ''
                
                count = float(count_str)
                if unit == 'M':
                    count = int(count * 1000000)
                elif unit == 'K':
                    count = int(count * 1000)
                else:
                    count = int(count)
                
                return count
                    
        except (ValueError, KeyError, IndexError) as e:
            logger.debug(f"Error extracting from og:description: {e}")
            
        return 0
    
    def _extract_followers_from_text(self, text: str) -> int:
        """
        Extract follower count from search result text
        
        Args:
            text: Text from title and snippet
            
        Returns:
            Follower count as integer
        """
        # Patterns to match follower counts
        follower_patterns = [
            # "5.2M followers", "1.2k followers", etc.
            r'(\d+(?:\.\d+)?)\s*([kmb])\s*followers',
            # "5,200,000 followers", "1,200 followers", etc.
            r'(\d{1,3}(?:,\d{3})*)\s*followers',
            # "followers: 5.2M", "followers 1.2k", etc.
            r'followers[\s:]*(\d+(?:\.\d+)?)\s*([kmb])',
            # "5.2M Instagram followers"
            r'(\d+(?:\.\d+)?)\s*([kmb])\s*instagram\s*followers',
            # More flexible patterns
            r'(\d+(?:\.\d+)?)\s*([kmb])\s*(?:instagram\s*)?(?:followers|following)',
            r'(\d{1,3}(?:,\d{3})*)\s*(?:instagram\s*)?followers'
        ]
        
        text_lower = text.lower()
        
        for pattern in follower_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    if len(match) == 2:  # Has suffix (k, m, b)
                        number, suffix = match
                        count = self._convert_follower_number(number, suffix)
                    else:  # Just number with commas
                        number = match if isinstance(match, str) else match[0]
                        count = int(number.replace(',', ''))
                    
                    if count > 0:
                        return count
                except (ValueError, IndexError):
                    continue
        
        return 0
    
    def _convert_follower_number(self, number_str: str, suffix: str) -> int:
        """
        Convert follower count with suffix to integer
        
        Args:
            number_str: Number part (e.g., "5.2")
            suffix: Suffix (k, m, b)
            
        Returns:
            Integer follower count
        """
        try:
            base_number = float(number_str)
            suffix_lower = suffix.lower()
            
            if suffix_lower == 'k':
                return int(base_number * 1000)
            elif suffix_lower == 'm':
                return int(base_number * 1000000)
            elif suffix_lower == 'b':
                return int(base_number * 1000000000)
            else:
                return int(base_number)
        except ValueError:
            return 0
    
    def _calculate_confidence(self, comedian_name: str, username: str, full_text: str) -> float:
        """
        Calculate confidence score for the Instagram match
        
        Args:
            comedian_name: Original comedian name
            username: Instagram username
            full_text: Full search result text
            
        Returns:
            Confidence score between 0 and 1
        """
        score = 0.0
        name_parts = comedian_name.lower().split()
        username_lower = username.lower()
        text_lower = full_text.lower()
        
        # Check username similarity
        for part in name_parts:
            if len(part) > 2 and part in username_lower:
                score += 0.3
        
        # Check if comedian name appears in text
        if comedian_name.lower() in text_lower:
            score += 0.4
        
        # Check for comedy-related keywords
        comedy_keywords = ['comedian', 'comedy', 'stand-up', 'standup', 'comic']
        for keyword in comedy_keywords:
            if keyword in text_lower:
                score += 0.1
                break
        
        # Check for verification indicators
        if 'verified' in text_lower or '✓' in full_text:
            score += 0.2
        
        return min(score, 1.0)
    
    def _format_follower_count(self, count: int) -> str:
        """
        Format follower count as human-readable string
        
        Args:
            count: Follower count as integer
            
        Returns:
            Formatted string (e.g., "1.2M", "50K")
        """
        if count >= 1000000:
            return f"{count / 1000000:.1f}M"
        elif count >= 1000:
            return f"{count / 1000:.1f}K"
        else:
            return str(count)
    
    def _extract_username_from_url(self, url: str) -> Optional[str]:
        """Extract Instagram username from URL"""
        # Remove query parameters and fragments
        url = url.split('?')[0].split('#')[0]
        
        # Extract username
        match = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)', url)
        if match:
            username = match.group(1)
            # Filter out common non-username paths
            if username not in ['p', 'reel', 'tv', 'explore', 'accounts', 'stories']:
                return username
        
        return None
    
    def _validate_instagram_profile(self, username: str, comedian_name: str) -> bool:
        """
        Validate if the Instagram profile likely belongs to the comedian
        
        Args:
            username: Instagram username
            comedian_name: Comedian's name
            
        Returns:
            True if profile seems to match the comedian
        """
        # Simple validation based on name similarity
        username_lower = username.lower()
        name_parts = comedian_name.lower().split()
        
        logger.debug(f"Validating username '{username}' for comedian '{comedian_name}'")
        logger.debug(f"Name parts: {name_parts}")
        
        # Check if any part of the name is in the username
        for part in name_parts:
            if len(part) > 2 and part in username_lower:
                logger.debug(f"Found name part '{part}' in username '{username}' - VALID")
                return True
        
        # Check if username contains common comedian-related terms
        comedian_keywords = ['comedy', 'comic', 'standup', 'comedian']
        for keyword in comedian_keywords:
            if keyword in username_lower:
                logger.debug(f"Found comedy keyword '{keyword}' in username '{username}' - VALID")
                return True
        
        logger.debug(f"Username '{username}' does not match comedian '{comedian_name}' - INVALID")
        return False
    
    def get_instagram_follower_count(self, instagram_url: str) -> Tuple[int, str]:
        """
        Extract follower count from Instagram profile
        Note: This attempts basic scraping but Instagram's anti-scraping measures
        make this challenging. Success rate may be limited.
        
        Args:
            instagram_url: Instagram profile URL
            
        Returns:
            Tuple of (follower_count, followers_text)
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Add delay to be respectful
            time.sleep(2)
            
            response = requests.get(instagram_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            html_content = response.text
            
            # Try multiple patterns to extract follower count
            follower_patterns = [
                r'"edge_followed_by":{"count":(\d+)}',
                r'"follower_count":(\d+)',
                r'content="(\d+(?:,\d+)*)\s*Followers"',
                r'(\d+(?:\.\d+)?[KMB]?)\s*followers',
                r'<meta[^>]*content="([^"]*followers[^"]*)"',
            ]
            
            for pattern in follower_patterns:
                import re
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    follower_text = matches[0]
                    
                    # Convert text to number
                    follower_count = self._parse_follower_count(follower_text)
                    
                    if follower_count > 0:
                        logger.info(f"Extracted {follower_count} followers from {instagram_url}")
                        return follower_count, follower_text
            
            # If no patterns matched, try to find any mention of followers
            if 'followers' in html_content.lower():
                logger.info(f"Found followers mention but couldn't extract count from {instagram_url}")
                return 0, "Found but couldn't extract"
            else:
                logger.warning(f"No follower information found for {instagram_url} - may need login")
                return 0, "Requires login"
            
        except requests.RequestException as e:
            logger.error(f"Network error getting follower count for {instagram_url}: {e}")
            return 0, "Network error"
        except Exception as e:
            logger.error(f"Error getting follower count for {instagram_url}: {e}")
            return 0, "Error"
    
    def _parse_follower_count(self, follower_text: str) -> int:
        """
        Parse follower count from text (e.g., '1.2M', '50K', '1,234')
        
        Args:
            follower_text: Text containing follower count
            
        Returns:
            Numeric follower count
        """
        try:
            # Remove commas and clean the text
            clean_text = follower_text.replace(',', '').replace(' ', '').lower()
            
            # Handle K, M, B suffixes
            if clean_text.endswith('k'):
                return int(float(clean_text[:-1]) * 1000)
            elif clean_text.endswith('m'):
                return int(float(clean_text[:-1]) * 1000000)
            elif clean_text.endswith('b'):
                return int(float(clean_text[:-1]) * 1000000000)
            else:
                # Try to extract just the number
                import re
                numbers = re.findall(r'\d+', clean_text)
                if numbers:
                    return int(numbers[0])
            
            return 0
            
        except (ValueError, IndexError):
            return 0
    
    def process_comedian(self, comedian_name: str) -> Optional[ComedianInstagram]:
        """
        Process a single comedian to find their Instagram and follower count
        
        Args:
            comedian_name: Name of the comedian
            
        Returns:
            ComedianInstagram object if successful, None otherwise
        """
        # Check if comedian already exists in database
        existing = self._get_comedian_from_db(comedian_name)
        if existing and existing.instagram_url:
            logger.info(f"Comedian {comedian_name} already in database")
            return existing
        
        # Search for Instagram profile and follower data
        search_result = self.search_comedian_instagram(comedian_name)
        
        if not search_result:
            # Update search attempts in database
            self._update_search_attempts(comedian_name)
            return None
        
        instagram_url = search_result['instagram_url']
        follower_count_from_search = search_result.get('follower_count', 0)
        
        # If we got follower count from search, use it
        if follower_count_from_search > 0:
            follower_count = follower_count_from_search
            followers_text = self._format_follower_count(follower_count)
            logger.info(f"Using follower count from search results: {follower_count}")
        else:
            # Fallback to direct Instagram scraping (less reliable)
            follower_count, followers_text = self.get_instagram_follower_count(instagram_url)
        
        # Extract username from URL
        username = self._extract_username_from_url(instagram_url)
        
        # Create comedian object
        comedian_instagram = ComedianInstagram(
            name=comedian_name,
            instagram_username=username or "",
            instagram_url=instagram_url,
            follower_count=follower_count,
            followers_text=followers_text,
            last_updated=datetime.now().isoformat(),
            search_attempts=1,
            verified=False
        )
        
        # Save to database
        self._save_comedian_to_db(comedian_instagram)
        
        return comedian_instagram
    
    def _get_comedian_from_db(self, comedian_name: str) -> Optional[ComedianInstagram]:
        """Get comedian data from database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, instagram_username, instagram_url, follower_count,
                   followers_text, last_updated, search_attempts, verified
            FROM comedians WHERE name = ?
        ''', (comedian_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return ComedianInstagram(*row)
        return None
    
    def _save_comedian_to_db(self, comedian: ComedianInstagram):
        """Save comedian data to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO comedians 
            (name, instagram_username, instagram_url, follower_count,
             followers_text, last_updated, search_attempts, verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            comedian.name,
            comedian.instagram_username,
            comedian.instagram_url,
            comedian.follower_count,
            comedian.followers_text,
            comedian.last_updated,
            comedian.search_attempts,
            comedian.verified
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"Saved comedian {comedian.name} to database")
    
    def _update_search_attempts(self, comedian_name: str):
        """Update search attempts for a comedian"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO comedians (name, search_attempts) VALUES (?, 1)
        ''', (comedian_name,))
        
        cursor.execute('''
            UPDATE comedians SET search_attempts = search_attempts + 1 
            WHERE name = ?
        ''', (comedian_name,))
        
        conn.commit()
        conn.close()
    
    def process_comedian_dataframe(self, df: pd.DataFrame, comedian_name_column: str = 'comedian_name') -> pd.DataFrame:
        """
        Process a dataframe of comedians to find Instagram followers
        
        Args:
            df: DataFrame containing comedian data
            comedian_name_column: Name of the column containing comedian names
            
        Returns:
            Updated DataFrame with Instagram information
        """
        if comedian_name_column not in df.columns:
            raise ValueError(f"Column '{comedian_name_column}' not found in DataFrame")
        
        # Get unique comedian names
        unique_comedians = df[comedian_name_column].dropna().unique()
        logger.info(f"Processing {len(unique_comedians)} unique comedians")
        
        # Process each comedian
        instagram_data = []
        
        for i, comedian_name in enumerate(unique_comedians, 1):
            logger.info(f"Processing {i}/{len(unique_comedians)}: {comedian_name}")
            
            comedian_instagram = self.process_comedian(comedian_name)
            
            if comedian_instagram:
                instagram_data.append({
                    'comedian_name': comedian_name,
                    'instagram_username': comedian_instagram.instagram_username,
                    'instagram_url': comedian_instagram.instagram_url,
                    'follower_count': comedian_instagram.follower_count,
                    'followers_text': comedian_instagram.followers_text,
                    'last_updated': comedian_instagram.last_updated
                })
            else:
                instagram_data.append({
                    'comedian_name': comedian_name,
                    'instagram_username': None,
                    'instagram_url': None,
                    'follower_count': None,
                    'followers_text': None,
                    'last_updated': datetime.now().isoformat()
                })
            
            # Rate limiting for API calls
            if i % 10 == 0:
                logger.info("Taking a longer break to respect API limits...")
                time.sleep(5)
        
        # Create Instagram DataFrame
        instagram_df = pd.DataFrame(instagram_data)
        
        # Merge with original DataFrame
        result_df = df.merge(
            instagram_df, 
            left_on=comedian_name_column, 
            right_on='comedian_name', 
            how='left'
        )
        
        return result_df
    
    def save_to_database(self, data: dict):
        """
        Public method to save comedian data to database
        
        Args:
            data: Dictionary containing comedian data
        """
        # Convert dict to ComedianInstagram object
        comedian = ComedianInstagram(
            name=data.get('comedian_name', ''),
            instagram_username=data.get('instagram_username', ''),
            instagram_url=data.get('instagram_url', ''),
            follower_count=data.get('follower_count', 0),
            followers_text=data.get('followers_text', ''),
            last_updated=data.get('last_updated', datetime.now().isoformat()),
            search_attempts=data.get('search_attempts', 1),
            verified=data.get('verified', False)
        )
        
        self._save_comedian_to_db(comedian)
    
    def get_from_database(self, comedian_name: str) -> Optional[dict]:
        """
        Public method to get comedian data from database
        
        Args:
            comedian_name: Name of the comedian
            
        Returns:
            Dictionary with comedian data or None if not found
        """
        comedian = self._get_comedian_from_db(comedian_name)
        
        if comedian:
            return {
                'comedian_name': comedian.name,
                'instagram_username': comedian.instagram_username,
                'instagram_url': comedian.instagram_url,
                'follower_count': comedian.follower_count,
                'followers_text': comedian.followers_text,
                'last_updated': comedian.last_updated,
                'search_attempts': comedian.search_attempts,
                'verified': comedian.verified
            }
        
        return None
    
    def export_comedian_database(self, filename: str = None) -> str:
        """
        Export the comedian database to CSV
        
        Args:
            filename: Optional filename for export
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'comedian_instagram_database_{timestamp}.csv'
        
        # Create output directory
        output_dir = Path('comedian_data')
        output_dir.mkdir(exist_ok=True)
        filepath = output_dir / filename
        
        # Read all data from database
        conn = sqlite3.connect(self.database_path)
        df = pd.read_sql_query('''
            SELECT name, instagram_username, instagram_url, follower_count,
                   followers_text, last_updated, search_attempts, verified,
                   created_at
            FROM comedians
            ORDER BY name
        ''', conn)
        conn.close()
        
        # Export to CSV
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        logger.info(f"Exported {len(df)} comedians to {filepath}")
        return str(filepath)
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the comedian database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Total comedians
        cursor.execute('SELECT COUNT(*) FROM comedians')
        total_comedians = cursor.fetchone()[0]
        
        # Comedians with Instagram
        cursor.execute('SELECT COUNT(*) FROM comedians WHERE instagram_url IS NOT NULL')
        with_instagram = cursor.fetchone()[0]
        
        # Comedians with followers data
        cursor.execute('SELECT COUNT(*) FROM comedians WHERE follower_count > 0')
        with_followers = cursor.fetchone()[0]
        
        # Average follower count
        cursor.execute('SELECT AVG(follower_count) FROM comedians WHERE follower_count > 0')
        avg_followers = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_comedians': total_comedians,
            'with_instagram': with_instagram,
            'with_followers': with_followers,
            'instagram_found_rate': (with_instagram / total_comedians * 100) if total_comedians > 0 else 0,
            'average_followers': int(avg_followers)
        }

def main():
    """Main function for testing the Instagram follower extractor"""
    print("Instagram Follower Extractor for Comedy Cellar Comedians")
    print("=" * 60)
    
    try:
        extractor = InstagramFollowerExtractor()
        
        # Test with a few comedians
        test_comedians = [
            "Colin Quinn",
            "Dave Chappelle",
            "Jerry Seinfeld",
            "Amy Schumer",
            "Joe List"
        ]
        
        print("\nTesting with sample comedians...")
        for comedian in test_comedians:
            print(f"\nProcessing: {comedian}")
            result = extractor.process_comedian(comedian)
            if result:
                print(f"  Instagram: {result.instagram_url}")
                print(f"  Followers: {result.followers_text}")
            else:
                print("  No Instagram found")
        
        # Show database stats
        stats = extractor.get_database_stats()
        print(f"\nDatabase Statistics:")
        print(f"  Total comedians: {stats['total_comedians']}")
        print(f"  With Instagram: {stats['with_instagram']}")
        print(f"  Instagram found rate: {stats['instagram_found_rate']:.1f}%")
        
        # Export database
        export_file = extractor.export_comedian_database()
        print(f"\nDatabase exported to: {export_file}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()