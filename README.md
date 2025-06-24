# LinkedIn Job Scraper

A Python web scraper for collecting LinkedIn job postings using Selenium WebDriver with automated login, pagination, and CSV export.

## Features

- 🔐 Automated LinkedIn login
- 🔍 Customizable job search queries  
- 📄 Multi-page scraping with pagination
- 🖱️ Dynamic content loading via scrolling
- 💾 CSV/text export to `datastore/`
- 🏃 Built-in retry logic and error handling
- 📊 Comprehensive logging with rotation

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the scraper**:
   ```bash
   python linkedin_scraper.py --username your_email@example.com --password your_password
   ```

## Usage

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--username` | LinkedIn email (required) | - |
| `--password` | LinkedIn password (required) | - |
| `--search-query` | Job search keywords | "Senior Data Scientist" |
| `--total-pages` | Pages to scrape | 100 |
| `--scroll-count` | Scroll actions per page | 10 |

### Programmatic Usage

```python
from linkedin_scraper import LinkedInScraper, ScrapingConfig

config = ScrapingConfig(
    username="your_email@example.com",
    password="your_password",
    search_query="Python Developer",
    total_pages=10
)

scraper = LinkedInScraper(config)
success = scraper.scrape()
```

## Project Structure

```
linkedin-scraper/
├── linkedin_scraper.py       # Main entry point
├── src/scraper.py           # Core scraping logic
├── tests/                   # Unit tests
├── datastore/              # Output CSV files
├── logs/                   # Application logs
└── requirements.txt        # Dependencies
```

## Output

- **CSV files**: Structured job data in `datastore/`
- **Logs**: Detailed operation logs in `logs/linkedin_scraper.log`

Sample CSV output:
| Title | Company | Location | Link |
|-------|---------|----------|------|
| Senior Data Scientist | Tech Corp | San Francisco, CA | https://linkedin.com/jobs/view/123 |

## Testing

```bash
python -m pytest tests/
```

## Configuration

Key configuration options in `ScrapingConfig`:

```python
total_pages: int = 100          # Pages to scrape
scroll_count: int = 10          # Scrolls per page
page_load_timeout: int = 60     # Page timeout
max_retries: int = 3            # Retry attempts
```

## Troubleshooting

- **ChromeDriver issues**: Install ChromeDriver and add to PATH
- **Login failures**: Check credentials and account status
- **No data**: Verify search URL and check logs
- **Timeouts**: Increase timeout values in config

## Dependencies

- `selenium` - Web automation
- `beautifulsoup4` - HTML parsing  
- `pandas` - Data export

## Legal Notice

⚠️ **Educational use only**. Respect LinkedIn's Terms of Service and rate limits. Consider LinkedIn's official API for commercial use.

## Requirements

- Python 3.7+
- Chrome browser
- ChromeDriver
