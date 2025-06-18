"""LinkedIn Job Postings Scraper."""

import argparse
import logging
import os
from dataclasses import dataclass
from typing import List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class JobPosting:
    """Data class representing a LinkedIn job posting."""

    title: str
    link: str


def parse_job_postings(html: str) -> List[JobPosting]:
    """Parse LinkedIn job postings from an HTML page.

    Parameters
    ----------
    html : str
        HTML content containing job listings.

    Returns
    -------
    List[JobPosting]
        Parsed list of job postings.
    """
    soup = BeautifulSoup(html, "html.parser")
    postings = []
    for item in soup.select(".jobs-search-results__list-item a"):
        title = item.get_text(strip=True)
        link = item.get("href")
        if title and link:
            postings.append(JobPosting(title=title, link=link))
    logger.info("Found %d job postings", len(postings))
    return postings


def login(driver: webdriver.Chrome, username: str, password: str) -> bool:
    """Perform login to LinkedIn using Selenium.

    Parameters
    ----------
    driver : webdriver.Chrome
        Selenium web driver instance.
    username : str
        LinkedIn username or email.
    password : str
        LinkedIn password.

    Returns
    -------
    bool
        True if login was successful, False otherwise.
    """
    try:
        driver.get("https://www.linkedin.com/login")
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        password_field = driver.find_element(By.ID, "password")
        username_field.send_keys(username)
        password_field.send_keys(password)
        password_field.submit()
        WebDriverWait(driver, 10).until(EC.url_contains("/feed"))
        logger.info("Successfully logged into LinkedIn")
        return True
    except WebDriverException as exc:
        logger.error("Failed to log into LinkedIn: %s", exc)
        return False


def fetch_job_postings(
    driver: webdriver.Chrome, search_url: str
) -> List[JobPosting]:
    """Fetch job postings from LinkedIn search results using Selenium.

    Parameters
    ----------
    driver : webdriver.Chrome
        Selenium web driver instance.
    search_url : str
        URL to the LinkedIn jobs search page.

    Returns
    -------
    List[JobPosting]
        List of parsed job postings.
    """
    try:
        driver.get(search_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".jobs-search-results__list-item")
            )
        )
        html = driver.page_source
        return parse_job_postings(html)
    except WebDriverException as exc:
        logger.error("Error fetching job postings: %s", exc)
        return []


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="LinkedIn job scraper")
    parser.add_argument("--search-url", help="LinkedIn jobs search URL")
    parser.add_argument(
        "--username",
        help="LinkedIn username",
        default=os.getenv("LINKEDIN_USERNAME"),
    )
    parser.add_argument(
        "--password",
        help="LinkedIn password",
        default=os.getenv("LINKEDIN_PASSWORD"),
    )
    parser.add_argument(
        "--driver-path",
        help="Path to chromedriver executable",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run scraper in test mode",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for the scraper script."""
    args = parse_arguments()
    if args.test:
        test_file = os.path.join(
            os.path.dirname(__file__),
            "..", "tests", "data", "sample_jobs.html"
        )
        with open(test_file, "r", encoding="utf-8") as fh:
            html = fh.read()
        postings = parse_job_postings(html)
        for post in postings:
            print(f"{post.title} - {post.link}")
        return

    if not args.search_url:
        logger.error("Search URL is required when not in test mode")
        return
    if not args.username or not args.password:
        logger.error("Username and password are required for authentication")
        return
    options = webdriver.ChromeOptions()
    if args.headless:
        options.add_argument("--headless")
    service = Service(args.driver_path) if args.driver_path else Service()
    with webdriver.Chrome(service=service, options=options) as driver:
        if not login(driver, args.username, args.password):
            return
        postings = fetch_job_postings(driver, args.search_url)
        for post in postings:
            print(f"{post.title} - {post.link}")


if __name__ == "__main__":
    main()
