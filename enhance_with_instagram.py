#!/usr/bin/env python3
"""
Integration script to combine Comedy Cellar lineup data with Instagram follower data

This script takes the comedian data from the Comedy Cellar scraper and enhances it
with Instagram follower information using the Google Search API.

Usage:
    python enhance_with_instagram.py --input comedians.csv --output enhanced_comedians.csv
    python enhance_with_instagram.py --auto  # Process latest scraper output
"""

import argparse
import pandas as pd
import sys
from pathlib import Path
import logging
from datetime import datetime

# Import our modules
from instagram_follower_extractor import InstagramFollowerExtractor
from Lineup_scraper import ComedyCellarScraper

logger = logging.getLogger(__name__)

def find_latest_comedian_csv() -> str:
    """Find the most recent comedian CSV file from the scraper"""
    data_dir = Path('comedy_cellar_data')
    
    if not data_dir.exists():
        raise FileNotFoundError("No comedy_cellar_data directory found. Run the scraper first.")
    
    # Look for comedian CSV files
    comedian_files = list(data_dir.glob('*comedians.csv'))
    
    if not comedian_files:
        raise FileNotFoundError("No comedian CSV files found. Run the scraper first.")
    
    # Get the most recent file
    latest_file = max(comedian_files, key=lambda f: f.stat().st_mtime)
    return str(latest_file)

def enhance_comedian_data(input_file: str, output_file: str = None) -> str:
    """
    Enhance comedian data with Instagram follower information
    
    Args:
        input_file: Path to the comedian CSV file
        output_file: Output file path (optional)
        
    Returns:
        Path to the enhanced CSV file
    """
    # Load the comedian data
    print(f"Loading comedian data from: {input_file}")
    df = pd.read_csv(input_file)
    
    print(f"Found {len(df)} comedian appearances")
    print(f"Unique comedians: {df['comedian_name'].nunique()}")
    
    # Initialize Instagram extractor
    print("Initializing Instagram follower extractor...")
    try:
        extractor = InstagramFollowerExtractor()
    except ValueError as e:
        print(f"Error: {e}")
        print("Make sure GOOGLE_API_KEY and GOOGLE_CSE_ID are set in your .env file")
        return None
    
    # Process the comedian data
    print("Searching for Instagram profiles and follower counts...")
    print("This may take a while due to API rate limits...")
    
    enhanced_df = extractor.process_comedian_dataframe(df, 'comedian_name')
    
    # Generate output filename if not provided
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'enhanced_comedians_{timestamp}.csv'
    
    # Save enhanced data
    output_path = Path('comedian_data') / output_file
    output_path.parent.mkdir(exist_ok=True)
    
    enhanced_df.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"\nEnhanced data saved to: {output_path}")
    
    # Show statistics
    stats = analyze_enhanced_data(enhanced_df)
    print_statistics(stats)
    
    return str(output_path)

def analyze_enhanced_data(df: pd.DataFrame) -> dict:
    """Analyze the enhanced comedian data"""
    total_appearances = len(df)
    unique_comedians = df['comedian_name'].nunique()
    
    # Instagram statistics
    with_instagram = df['instagram_url'].notna().sum()
    with_followers = df['follower_count'].notna().sum()
    
    # Get unique comedian stats
    unique_df = df.drop_duplicates('comedian_name')
    unique_with_instagram = unique_df['instagram_url'].notna().sum()
    
    return {
        'total_appearances': total_appearances,
        'unique_comedians': unique_comedians,
        'appearances_with_instagram': with_instagram,
        'unique_with_instagram': unique_with_instagram,
        'with_follower_data': with_followers,
        'instagram_rate': (unique_with_instagram / unique_comedians * 100) if unique_comedians > 0 else 0
    }

def print_statistics(stats: dict):
    """Print enhancement statistics"""
    print("\n" + "="*50)
    print("ENHANCEMENT STATISTICS")
    print("="*50)
    print(f"Total comedian appearances: {stats['total_appearances']:,}")
    print(f"Unique comedians: {stats['unique_comedians']:,}")
    print(f"Appearances with Instagram: {stats['appearances_with_instagram']:,}")
    print(f"Unique comedians with Instagram: {stats['unique_with_instagram']:,}")
    print(f"Instagram discovery rate: {stats['instagram_rate']:.1f}%")
    print(f"With follower data: {stats['with_follower_data']:,}")

def run_full_pipeline(start_year: int = 2020, end_year: int = 2025):
    """
    Run the complete pipeline: scrape comedy data + enhance with Instagram
    
    Args:
        start_year: Start year for scraping
        end_year: End year for scraping
    """
    print("Running Complete Comedy Cellar + Instagram Pipeline")
    print("="*60)
    
    # Step 1: Scrape Comedy Cellar data
    print(f"\nStep 1: Scraping Comedy Cellar data ({start_year}-{end_year})")
    print("This may take 30-60 minutes...")
    
    scraper = ComedyCellarScraper()
    shows = scraper.scrape_all_dates(start_year, end_year)
    
    if not shows:
        print("No show data found. Exiting.")
        return
    
    # Export Comedy Cellar data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    comedy_file = scraper.export_to_csv(shows, f"pipeline_{timestamp}")
    
    # Find the comedians file
    comedians_file = comedy_file.replace('_shows.csv', '_comedians.csv')
    
    print(f"Comedy Cellar data saved to: {comedians_file}")
    
    # Step 2: Enhance with Instagram data
    print(f"\nStep 2: Enhancing with Instagram follower data")
    enhanced_file = enhance_comedian_data(comedians_file)
    
    if enhanced_file:
        print(f"\nPipeline completed successfully!")
        print(f"Final enhanced data: {enhanced_file}")
    else:
        print("Instagram enhancement failed.")

def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description='Enhance comedian data with Instagram followers')
    parser.add_argument('--input', '-i', help='Input comedian CSV file')
    parser.add_argument('--output', '-o', help='Output enhanced CSV file')
    parser.add_argument('--auto', action='store_true', help='Auto-find latest comedian file')
    parser.add_argument('--pipeline', action='store_true', help='Run complete pipeline (scrape + enhance)')
    parser.add_argument('--year', type=int, help='Single year for pipeline (default: current year)')
    parser.add_argument('--start-year', type=int, default=2020, help='Start year for pipeline')
    parser.add_argument('--end-year', type=int, default=2025, help='End year for pipeline')
    
    args = parser.parse_args()
    
    try:
        if args.pipeline:
            # Run complete pipeline
            if args.year:
                run_full_pipeline(args.year, args.year)
            else:
                run_full_pipeline(args.start_year, args.end_year)
        
        elif args.auto:
            # Auto-find latest file
            input_file = find_latest_comedian_csv()
            enhance_comedian_data(input_file, args.output)
        
        elif args.input:
            # Use specified input file
            enhance_comedian_data(args.input, args.output)
        
        else:
            # Interactive mode
            print("Instagram Follower Enhancement Tool")
            print("="*40)
            print("1. Enhance existing comedian CSV file")
            print("2. Auto-enhance latest scraper output") 
            print("3. Run complete pipeline (scrape + enhance)")
            print("4. Exit")
            
            while True:
                choice = input("\nSelect option (1-4): ").strip()
                
                if choice == "1":
                    input_file = input("Enter path to comedian CSV file: ").strip()
                    if Path(input_file).exists():
                        enhance_comedian_data(input_file)
                    else:
                        print("File not found!")
                    break
                
                elif choice == "2":
                    try:
                        input_file = find_latest_comedian_csv()
                        enhance_comedian_data(input_file)
                    except FileNotFoundError as e:
                        print(f"Error: {e}")
                    break
                
                elif choice == "3":
                    print("Pipeline options:")
                    print("1. Current year only")
                    print("2. Last 2 years")
                    print("3. Full range (2020-2025)")
                    
                    pipeline_choice = input("Select pipeline option (1-3): ").strip()
                    
                    current_year = datetime.now().year
                    
                    if pipeline_choice == "1":
                        run_full_pipeline(current_year, current_year)
                    elif pipeline_choice == "2":
                        run_full_pipeline(current_year - 1, current_year)
                    else:
                        run_full_pipeline(2020, 2025)
                    break
                
                elif choice == "4":
                    print("Goodbye!")
                    sys.exit(0)
                
                else:
                    print("Invalid choice. Please select 1-4.")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()