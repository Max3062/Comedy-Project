# Comedy Cellar Lineup Scraper

A comprehensive Python scraper for extracting historical lineup data from the Comedy Cellar website (2020-2025).

## Features

- Scrapes all past lineups from Comedy Cellar's New York locations
- Extracts comedian information including names, descriptions, and websites
- Captures show details like times, venues, and dates
- Exports data to multiple CSV formats for analysis
- Respectful scraping with rate limiting and error handling
- Comprehensive logging for monitoring progress

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install requests pandas beautifulsoup4
   ```

2. **Run the scraper:**
   ```bash
   python run_scraper.py
   ```

3. **Choose your option:**
   - Full scrape (2020-2025): ~45 minutes, comprehensive dataset
   - Recent scrape (last 6 months): ~5 minutes, recent data
   - Specific year: Custom year between 2020-2025
   - Custom options: Run with full customization

## Output Files

The scraper generates three CSV files:

### 1. Shows CSV (`*_shows.csv`)
One row per show with:
- `show_id`: Unique show identifier
- `date`: Show date (YYYY-MM-DD)
- `time`: Show time (e.g., "8:00 pm")
- `venue`: Venue name (Village Underground, MacDougal Street, etc.)
- `comedian_count`: Number of comedians in the show
- `comedians`: Semicolon-separated list of comedian names

### 2. Comedians CSV (`*_comedians.csv`)
One row per comedian appearance with:
- `show_id`: Unique show identifier
- `date`: Show date
- `time`: Show time
- `venue`: Venue name
- `comedian_name`: Comedian's name
- `order`: Order of appearance in the show
- `description`: Comedian's bio/description
- `website`: Comedian's website (if available)
- `thumb_url`: URL to comedian's photo thumbnail

### 3. Summary CSV (`*_summary.csv`)
Statistics about the scraped data:
- `total_shows`: Total number of shows found
- `unique_dates_with_shows`: Number of dates with show data
- `unique_comedians`: Number of unique comedians
- `unique_venues`: Number of different venues
- `total_comedian_appearances`: Total comedian appearances
- `scrape_date`: When the scraping was performed

## Data Analysis Examples

### Most Frequent Comedians
```python
import pandas as pd

df = pd.read_csv('comedy_cellar_data/comedians.csv')
comedian_counts = df['comedian_name'].value_counts()
print("Top 10 most frequent comedians:")
print(comedian_counts.head(10))
```

### Shows by Venue
```python
venue_shows = df.groupby('venue').size().sort_values(ascending=False)
print("Shows by venue:")
print(venue_shows)
```

### Timeline Analysis
```python
df['date'] = pd.to_datetime(df['date'])
monthly_shows = df.groupby(df['date'].dt.to_period('M')).size()
print("Shows per month:")
print(monthly_shows)
```

## Technical Details

### API Endpoint
The scraper uses Comedy Cellar's internal API:
- **URL**: `https://www.comedycellar.com/lineup/api/`
- **Method**: POST
- **Parameters**: 
  - `action`: "cc_get_shows"
  - `json`: JSON string with date, venue, and type parameters

### Rate Limiting
- 1 second delay between requests
- 5 second pause every 50 requests
- Respectful of server resources

### Error Handling
- Network timeouts and connection errors
- JSON parsing errors
- HTML parsing failures
- Graceful degradation with logging

## File Structure

```
Comedy Project/
├── Lineup_scraper.py       # Main scraper class
├── run_scraper.py          # Quick start script
├── test_scraper.py         # Test script
├── debug_api.py           # API debugging utility
├── comedy_cellar_data/    # Output directory
│   ├── *_shows.csv
│   ├── *_comedians.csv
│   └── *_summary.csv
└── comedy_cellar_scraper.log  # Log file
```

## Usage Examples

### Command Line
```bash
# Quick start with menu
python run_scraper.py

# Full custom options
python Lineup_scraper.py
```

### Programmatic Usage
```python
from Lineup_scraper import ComedyCellarScraper
from datetime import date

scraper = ComedyCellarScraper()

# Scrape a specific date
shows = scraper.scrape_date(date(2024, 12, 7))

# Scrape a year
all_shows = scraper.scrape_all_dates(2024, 2024)

# Export to CSV
scraper.export_to_csv(all_shows, "my_export")
```

## Data Quality

The scraper has been tested and validated with:
- ✅ API connectivity and response parsing
- ✅ HTML content extraction
- ✅ Comedian data accuracy
- ✅ Show time and venue information
- ✅ CSV export functionality
- ✅ Error handling and recovery

## Estimated Data Volume

Based on testing:
- **2020-2025 Full Scrape**: ~15,000-20,000 shows
- **Unique Comedians**: ~1,000-2,000 performers
- **Total Appearances**: ~100,000+ individual comedian appearances
- **File Sizes**: Shows CSV (~2MB), Comedians CSV (~15MB)

## Legal and Ethical Notes

- This scraper accesses publicly available data from the Comedy Cellar website
- Rate limiting is implemented to be respectful of server resources
- Data is for research and analysis purposes
- Please respect the Comedy Cellar's terms of service

## Troubleshooting

### Common Issues

1. **Network Errors**: Check internet connection and retry
2. **Empty Results**: Some dates may not have shows (especially early pandemic period)
3. **Rate Limiting**: The scraper includes built-in delays, be patient
4. **Memory Usage**: Large scrapes may use significant memory, monitor system resources

### Logs
Check `comedy_cellar_scraper.log` for detailed information about:
- Request/response status
- Parsing errors
- Progress updates
- Error details

## Support

For issues or questions:
1. Check the log file for error details
2. Run the test script to verify basic functionality
3. Try a smaller date range first (recent scrape or single year)

---

**Created**: September 2025  
**Version**: 1.0  
**Python**: 3.8+ required