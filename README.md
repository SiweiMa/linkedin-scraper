# LinkedIn Job Scraper

A comprehensive Python web scraper for collecting job postings from LinkedIn using Selenium WebDriver. This tool supports automated login, pagination, scrolling, and exports results to CSV format.

## Features

- 🔐 **Automated LinkedIn Login**: Secure login with username/password
- 🔍 **Advanced Job Search**: Customizable search queries and filters
- 📄 **Multi-page Scraping**: Support for pagination across multiple result pages
- 🖱️ **Infinite Scroll**: Handles dynamic content loading with smart scrolling
- 💾 **Data Export**: Saves results to CSV and text files
- 🏃 **Retry Logic**: Built-in error handling and retry mechanisms
- 📊 **Comprehensive Logging**: Detailed logging with rotation support
- 🧪 **Tested**: Unit tests for core functionality

## Project Structure

```
linkedin-scraper/
├── linkedin_scraper.py       # Main entry point with full functionality
├── src/
│   ├── __init__.py
│   └── scraper.py           # Core scraping modules
├── tests/
│   ├── test_scraper.py      # Unit tests
│   └── data/
│       └── sample_jobs.html # Test data
├── datastore/               # Output directory for scraped data
├── logs/                    # Application logs
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd linkedin-scraper
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install ChromeDriver**:
   - Download ChromeDriver from [here](https://chromedriver.chromium.org/)
   - Ensure it's in your PATH or update the script to point to its location

## Usage

### Basic Usage

```bash
python linkedin_scraper.py --username your_email@example.com --password your_password
```

### Advanced Usage

```bash
python linkedin_scraper.py \
    --username your_email@example.com \
    --password your_password \
    --search-query "Senior Data Scientist" \
    --total-pages 50 \
    --scroll-count 5
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--username` | LinkedIn email/username | Required |
| `--password` | LinkedIn password | Required |
| `--search-query` | Job search keywords | "Senior Data Scientist" |
| `--search-url` | Custom LinkedIn search URL | Predefined URL |
| `--total-pages` | Number of pages to scrape | 100 |
| `--scroll-count` | Number of scroll actions per page | 10 |
| `--scroll-step` | Pixels to scroll each time | 500 |

### Using the Module

You can also import and use the scraper programmatically:

```python
from linkedin_scraper import LinkedInScraper, ScrapingConfig

# Configure scraping parameters
config = ScrapingConfig(
    username="your_email@example.com",
    password="your_password",
    search_query="Python Developer",
    total_pages=10
)

# Create and run scraper
scraper = LinkedInScraper(config)
success = scraper.scrape()

if success:
    print("Scraping completed successfully!")
```

## Configuration

The scraper supports extensive configuration through the `ScrapingConfig` class:

```python
@dataclass
class ScrapingConfig:
    username: str = ""
    password: str = ""
    search_query: str = "Senior Data Scientist"
    total_pages: int = 100
    scroll_count: int = 10
    scroll_step: int = 500
    page_load_timeout: int = 60
    script_timeout: int = 30
    implicit_wait: int = 10
    element_wait_timeout: int = 15
    max_retries: int = 3
    retry_delay: int = 5
```

## Output

The scraper generates several output files:

- **CSV files**: Structured job data saved in `datastore/` directory
- **Text files**: Raw job listings for manual review
- **Logs**: Detailed operation logs in `logs/` directory

### Sample CSV Output

| Title | Company | Location | Link | Date Posted |
|-------|---------|----------|------|-------------|
| Senior Data Scientist | Tech Corp | San Francisco, CA | https://linkedin.com/jobs/view/123 | 2 days ago |
| Machine Learning Engineer | AI Startup | Remote | https://linkedin.com/jobs/view/456 | 1 week ago |

## Error Handling

The scraper includes robust error handling:

- **Connection Issues**: Automatic retries with exponential backoff
- **Element Not Found**: Graceful degradation and logging
- **Login Failures**: Clear error messages and troubleshooting tips
- **Rate Limiting**: Smart delays and human-like behavior

## Testing

Run the test suite to verify functionality:

```bash
python -m pytest tests/
```

The tests include:
- HTML parsing validation
- Job posting extraction
- Error handling scenarios

## Logging

Detailed logs are saved to `logs/linkedin_scraper.log` with rotation:

- **DEBUG**: Detailed operation information
- **INFO**: General progress updates
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures

## Best Practices

1. **Respect Rate Limits**: Don't set scroll counts too high
2. **Use Realistic Delays**: Mimic human browsing behavior
3. **Monitor Logs**: Check logs regularly for issues
4. **Update Selectors**: LinkedIn may change their HTML structure
5. **Secure Credentials**: Consider using environment variables

## Dependencies

- `selenium`: Web automation and browser control
- `beautifulsoup4`: HTML parsing and data extraction
- `pandas`: Data manipulation and CSV export

## Legal Considerations

⚠️ **Important**: This tool is for educational and personal use only. Please:

- Respect LinkedIn's Terms of Service
- Don't overload their servers with excessive requests
- Consider using LinkedIn's official API for commercial use
- Be mindful of data privacy and usage rights

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**: Ensure ChromeDriver is installed and in PATH
2. **Login failures**: Check credentials and account status
3. **No data scraped**: Verify search URL and LinkedIn layout changes
4. **Timeout errors**: Increase timeout values in configuration

### Getting Help

- Check the logs in `logs/` directory for detailed error information
- Ensure your Chrome browser is up to date
- Verify your LinkedIn account is not restricted

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is intended for educational purposes. Please respect LinkedIn's Terms of Service and use responsibly.
