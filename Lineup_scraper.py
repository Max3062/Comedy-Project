#!/usr/bin/env python3
"""
Comedy Cellar Lineup Scraper

This script scrapes historical lineup data from the Comedy Cellar website
for all shows from 2020 to 2025, extracting comedian information, show times,
and venue details.

Author: Data Science Team
Date: 2025
"""

import requests
import json
import csv
import time
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
import urllib.parse
from dataclasses import dataclass
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comedy_cellar_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Comedian:
    """Data class for comedian information"""
    comedian_id: int
    name: str
    description: str
    website: str
    thumb_url: str
    order: int

@dataclass
class Show:
    """Data class for show information"""
    show_id: int
    date: str
    time: str
    hour_key: str
    title: str
    venue: str
    comedians: List[Comedian]

class ComedyCellarScraper:
    """
    A comprehensive scraper for Comedy Cellar lineup data
    """
    
    def __init__(self):
        self.base_url = "https://www.comedycellar.com/lineup/api/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest'
        })
        self.rate_limit_delay = 1.0  # seconds between requests
        
    def make_api_request(self, date_str: str, venue: str = "newyork", 
                        request_type: str = "past") -> Optional[Dict]:
        """
        Make an API request to get lineup data for a specific date
        
        Args:
            date_str: Date in format YYYY-MM-DD
            venue: Venue identifier (default: "newyork")
            request_type: Type of request (default: "past")
            
        Returns:
            Dictionary containing the API response or None if failed
        """
        try:
            # Prepare the request data as shown in the JavaScript
            request_data = {
                'date': date_str,
                'venue': venue,
                'type': request_type
            }
            
            # Convert to JSON string as the JavaScript does
            json_data = json.dumps(request_data)
            
            # Prepare form data
            form_data = {
                'action': 'cc_get_shows',
                'json': json_data
            }
            
            logger.info(f"Requesting data for {date_str}")
            
            # Make the POST request
            response = self.session.post(
                self.base_url,
                data=form_data,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Add delay to be respectful to the server
            time.sleep(self.rate_limit_delay)
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"Request failed for {date_str}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode failed for {date_str}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {date_str}: {e}")
            return None
    
    def parse_comedian_data(self, comedian_data: Dict, order: int) -> Comedian:
        """
        Parse comedian data from API response
        
        Args:
            comedian_data: Dictionary containing comedian information
            order: Order of appearance in the show
            
        Returns:
            Comedian object
        """
        return Comedian(
            comedian_id=comedian_data.get('comedianId', 0),
            name=comedian_data.get('name', ''),
            description=comedian_data.get('description', ''),
            website=comedian_data.get('website', ''),
            thumb_url=comedian_data.get('thumb', ''),
            order=order
        )
    
    def parse_html_data(self, date_str: str, html_content: str) -> List[Show]:
        """
        Parse show data from HTML content
        
        Args:
            date_str: Date string
            html_content: HTML content containing show information
            
        Returns:
            List of Show objects
        """
        import re
        from bs4 import BeautifulSoup
        
        shows = []
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all show containers
            show_containers = soup.find_all('div', class_='set-header')
            
            for i, header in enumerate(show_containers):
                try:
                    # Extract show time and venue from header
                    bold_span = header.find('span', class_='bold')
                    title_span = header.find('span', class_='title')
                    
                    if not bold_span or not title_span:
                        continue
                    
                    # Get show time (remove "show" text)
                    time_text = bold_span.get_text(strip=True)
                    time_clean = re.sub(r'\s*show\s*$', '', time_text, flags=re.IGNORECASE)
                    
                    # Get venue name
                    venue = title_span.get_text(strip=True)
                    
                    # Find corresponding lineup container
                    lineup_toggle = header.find('span', class_='lineup-toggle')
                    lineup_id = lineup_toggle.get('data-lineup-id') if lineup_toggle else str(i)
                    
                    # Find the lineup content
                    lineup_container = soup.find('div', {'data-set-content': lineup_id})
                    
                    comedians = []
                    if lineup_container:
                        # Find all comedian entries
                        comedian_divs = lineup_container.find_all('div', class_='set-content')
                        
                        for order, comedian_div in enumerate(comedian_divs):
                            try:
                                # Extract comedian name
                                name_span = comedian_div.find('span', class_='name')
                                if not name_span:
                                    continue
                                
                                name = name_span.get_text(strip=True)
                                
                                # Extract description (text after name span)
                                description_p = name_span.find_parent('p')
                                description = ""
                                if description_p:
                                    # Get all text, then remove the name part
                                    full_text = description_p.get_text(strip=True)
                                    description = full_text.replace(name, '', 1).strip()
                                
                                # Extract website
                                website = ""
                                website_link = comedian_div.find('a')
                                if website_link:
                                    website = website_link.get('href', '')
                                
                                # Extract image/thumbnail
                                thumb_url = ""
                                img_tag = comedian_div.find('img')
                                if img_tag:
                                    thumb_url = img_tag.get('src', '')
                                
                                # Create comedian object
                                comedian = Comedian(
                                    comedian_id=0,  # Not available in HTML
                                    name=name,
                                    description=description,
                                    website=website,
                                    thumb_url=thumb_url,
                                    order=order
                                )
                                
                                comedians.append(comedian)
                                
                            except Exception as e:
                                logger.warning(f"Error parsing comedian in show {lineup_id}: {e}")
                                continue
                    
                    # Create show object
                    show = Show(
                        show_id=int(lineup_id) if lineup_id.isdigit() else hash(f"{date_str}_{time_clean}_{venue}"),
                        date=date_str,
                        time=time_clean,
                        hour_key="",  # Not available in HTML
                        title=f"{time_clean} - {venue}",
                        venue=venue,
                        comedians=comedians
                    )
                    
                    shows.append(show)
                    
                except Exception as e:
                    logger.warning(f"Error parsing show {i} on {date_str}: {e}")
                    continue
            
            return shows
            
        except Exception as e:
            logger.error(f"Error parsing HTML data for {date_str}: {e}")
            return []
    
    def scrape_date(self, target_date: date) -> List[Show]:
        """
        Scrape lineup data for a specific date
        
        Args:
            target_date: Date object
            
        Returns:
            List of Show objects
        """
        date_str = target_date.strftime('%Y-%m-%d')
        
        # Make API request
        api_response = self.make_api_request(date_str)
        
        if not api_response:
            logger.warning(f"No data received for {date_str}")
            return []
        
        shows = []
        
        try:
            # Parse the response structure
            if 'show' in api_response and api_response['show']:
                show_data = api_response['show']
                
                # Check if there's HTML content with show data
                if 'html' in show_data and show_data['html']:
                    html_content = show_data['html']
                    shows = self.parse_html_data(date_str, html_content)
                                    
            logger.info(f"Found {len(shows)} shows for {date_str}")
            return shows
            
        except Exception as e:
            logger.error(f"Error processing data for {date_str}: {e}")
            return []
    
    def generate_date_range(self, start_year: int = 2020, end_year: int = 2025) -> List[date]:
        """
        Generate a list of dates to scrape
        
        Args:
            start_year: Starting year (default: 2020)
            end_year: Ending year (default: 2025)
            
        Returns:
            List of date objects
        """
        dates = []
        
        start_date = date(start_year, 1, 1)
        end_date = date(end_year, 12, 31)
        
        current_date = start_date
        
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)
        
        logger.info(f"Generated {len(dates)} dates from {start_date} to {end_date}")
        return dates
    
    def scrape_all_dates(self, start_year: int = 2020, end_year: int = 2025) -> List[Show]:
        """
        Scrape lineup data for all dates in the specified range
        
        Args:
            start_year: Starting year (default: 2020)
            end_year: Ending year (default: 2025)
            
        Returns:
            List of all Show objects
        """
        all_shows = []
        dates = self.generate_date_range(start_year, end_year)
        
        total_dates = len(dates)
        logger.info(f"Starting scrape of {total_dates} dates")
        
        for i, target_date in enumerate(dates, 1):
            if i % 100 == 0:
                logger.info(f"Progress: {i}/{total_dates} dates processed")
            
            try:
                shows = self.scrape_date(target_date)
                all_shows.extend(shows)
                
                # Longer delay every 50 requests to be extra respectful
                if i % 50 == 0:
                    logger.info("Taking a longer break...")
                    time.sleep(5)
                    
            except KeyboardInterrupt:
                logger.info("Scraping interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error scraping {target_date}: {e}")
                continue
        
        logger.info(f"Scraping completed. Found {len(all_shows)} total shows")
        return all_shows
    
    def export_to_csv(self, shows: List[Show], filename: str = None) -> str:
        """
        Export scraped data to CSV files
        
        Args:
            shows: List of Show objects
            filename: Optional base filename
            
        Returns:
            Path to the main CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'comedy_cellar_lineups_{timestamp}'
        
        # Create output directory
        output_dir = Path('comedy_cellar_data')
        output_dir.mkdir(exist_ok=True)
        
        # Prepare data for different CSV exports
        
        # 1. Shows CSV - one row per show
        shows_data = []
        for show in shows:
            shows_data.append({
                'show_id': show.show_id,
                'date': show.date,
                'time': show.time,
                'hour_key': show.hour_key,
                'venue': show.venue,
                'comedian_count': len(show.comedians),
                'comedians': '; '.join([c.name for c in show.comedians])
            })
        
        shows_file = output_dir / f'{filename}_shows.csv'
        with open(shows_file, 'w', newline='', encoding='utf-8') as f:
            if shows_data:
                writer = csv.DictWriter(f, fieldnames=shows_data[0].keys())
                writer.writeheader()
                writer.writerows(shows_data)
        
        # 2. Comedians CSV - one row per comedian appearance
        comedians_data = []
        for show in shows:
            for comedian in show.comedians:
                comedians_data.append({
                    'show_id': show.show_id,
                    'date': show.date,
                    'time': show.time,
                    'venue': show.venue,
                    'comedian_id': comedian.comedian_id,
                    'comedian_name': comedian.name,
                    'order': comedian.order,
                    'description': comedian.description,
                    'website': comedian.website,
                    'thumb_url': comedian.thumb_url
                })
        
        comedians_file = output_dir / f'{filename}_comedians.csv'
        with open(comedians_file, 'w', newline='', encoding='utf-8') as f:
            if comedians_data:
                writer = csv.DictWriter(f, fieldnames=comedians_data[0].keys())
                writer.writeheader()
                writer.writerows(comedians_data)
        
        # 3. Summary statistics
        unique_comedians = set()
        venues = set()
        dates_with_shows = set()
        
        for show in shows:
            dates_with_shows.add(show.date)
            venues.add(show.venue)
            for comedian in show.comedians:
                unique_comedians.add(comedian.name)
        
        summary_data = [{
            'total_shows': len(shows),
            'unique_dates_with_shows': len(dates_with_shows),
            'unique_comedians': len(unique_comedians),
            'unique_venues': len(venues),
            'total_comedian_appearances': len(comedians_data),
            'scrape_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }]
        
        summary_file = output_dir / f'{filename}_summary.csv'
        with open(summary_file, 'w', newline='', encoding='utf-8') as f:
            if summary_data:
                writer = csv.DictWriter(f, fieldnames=summary_data[0].keys())
                writer.writeheader()
                writer.writerows(summary_data)
        
        logger.info(f"Exported data to:")
        logger.info(f"  Shows: {shows_file}")
        logger.info(f"  Comedians: {comedians_file}")
        logger.info(f"  Summary: {summary_file}")
        logger.info(f"Total shows: {len(shows)}")
        logger.info(f"Total comedian appearances: {len(comedians_data)}")
        logger.info(f"Unique comedians: {len(unique_comedians)}")
        
        return str(shows_file)

def main():
    """Main function to run the scraper"""
    scraper = ComedyCellarScraper()
    
    print("Comedy Cellar Lineup Scraper")
    print("=" * 40)
    print("This will scrape lineup data from 2020 to 2025")
    print("Estimated time: 30-60 minutes depending on data availability")
    print()
    
    choice = input("Do you want to proceed? (y/n): ").lower().strip()
    
    if choice != 'y':
        print("Scraping cancelled.")
        return
    
    # Option to customize date range
    print("\nDate range options:")
    print("1. Full range (2020-2025)")
    print("2. Custom range")
    print("3. Test run (last 30 days)")
    
    range_choice = input("Choose option (1-3): ").strip()
    
    if range_choice == "2":
        try:
            start_year = int(input("Enter start year (e.g., 2020): "))
            end_year = int(input("Enter end year (e.g., 2025): "))
        except ValueError:
            print("Invalid year format. Using default range 2020-2025.")
            start_year, end_year = 2020, 2025
    elif range_choice == "3":
        # Test run - last 30 days
        today = datetime.now().date()
        start_date = today - timedelta(days=30)
        start_year, end_year = start_date.year, today.year
        print(f"Test run: {start_date} to {today}")
    else:
        start_year, end_year = 2020, 2025
    
    print(f"\nStarting scrape for years {start_year} to {end_year}...")
    
    try:
        # Scrape all data
        all_shows = scraper.scrape_all_dates(start_year, end_year)
        
        if all_shows:
            # Export to CSV
            main_file = scraper.export_to_csv(all_shows)
            print(f"\nScraping completed successfully!")
            print(f"Data exported to: {main_file}")
        else:
            print("No show data was found.")
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        print(f"Scraping failed: {e}")

if __name__ == "__main__":
    main()