#!/usr/bin/env python3
"""
Simple script to run the Comedy Cellar scraper with predefined options
"""

from Lineup_scraper import ComedyCellarScraper
from datetime import datetime, date, timedelta
import sys

def run_full_scrape():
    """Run the full scrape for 2020-2025"""
    print("Starting full scrape (2020-2025)...")
    print("This will take approximately 30-60 minutes")
    print("The scraper will be respectful and add delays between requests")
    
    scraper = ComedyCellarScraper()
    shows = scraper.scrape_all_dates(2020, 2025)
    
    if shows:
        filename = scraper.export_to_csv(shows, "comedy_cellar_full_2020_2025")
        print(f"\nFull scrape completed! Data saved to: {filename}")
    else:
        print("No data found during scrape")

def run_recent_scrape():
    """Run scrape for the last 6 months"""
    print("Starting recent scrape (last 6 months)...")
    
    today = date.today()
    six_months_ago = today - timedelta(days=180)
    
    scraper = ComedyCellarScraper()
    shows = scraper.scrape_all_dates(six_months_ago.year, today.year)
    
    if shows:
        filename = scraper.export_to_csv(shows, f"comedy_cellar_recent_{six_months_ago}_to_{today}")
        print(f"\nRecent scrape completed! Data saved to: {filename}")
    else:
        print("No data found during scrape")

def run_year_scrape(year):
    """Run scrape for a specific year"""
    print(f"Starting scrape for year {year}...")
    
    scraper = ComedyCellarScraper()
    shows = scraper.scrape_all_dates(year, year)
    
    if shows:
        filename = scraper.export_to_csv(shows, f"comedy_cellar_{year}")
        print(f"\nYear {year} scrape completed! Data saved to: {filename}")
    else:
        print(f"No data found for year {year}")

def main():
    print("Comedy Cellar Scraper - Quick Start")
    print("=" * 50)
    print("1. Full scrape (2020-2025) - ~45 minutes")
    print("2. Recent scrape (last 6 months) - ~5 minutes")
    print("3. Specific year scrape")
    print("4. Custom options (run main scraper)")
    print("5. Exit")
    
    while True:
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            confirmation = input("This will take a long time. Continue? (y/n): ").lower()
            if confirmation == 'y':
                run_full_scrape()
            break
        elif choice == "2":
            run_recent_scrape()
            break
        elif choice == "3":
            try:
                year = int(input("Enter year (2020-2025): "))
                if 2020 <= year <= 2025:
                    run_year_scrape(year)
                else:
                    print("Year must be between 2020 and 2025")
                    continue
            except ValueError:
                print("Invalid year format")
                continue
            break
        elif choice == "4":
            print("Running main scraper with custom options...")
            from Lineup_scraper import main
            main()
            break
        elif choice == "5":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please select 1-5.")

if __name__ == "__main__":
    main()