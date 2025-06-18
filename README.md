# LinkedIn Scraper

This project provides a simple example of how to scrape LinkedIn job postings.
It uses Selenium with headless Chrome to fetch pages and BeautifulSoup to parse job listings.

## Usage

Install dependencies:

```bash
pip install -r requirements.txt
```

Run in test mode with sample HTML:

```bash
python src/scraper.py --test
```

To run against LinkedIn directly, provide your credentials, a search URL, and the path to `chromedriver`:

```bash
export LINKEDIN_USERNAME=********
export LINKEDIN_PASSWORD=********
python src/scraper.py \
    --search-url "https://www.linkedin.com/jobs/search/?keywords=python" \
    --driver-path /path/to/chromedriver --headless
python src/scraper.py \
    --search-url "https://www.linkedin.com/jobs/search-results/?distance=25&f_TPR=r604800&geoId=102095887&keywords=Senior%20Data%20Scientist&origin=SEMANTIC_SEARCH_HISTORY" \
    --headless
```

Be mindful of LinkedIn's Terms of Service when scraping their website.

