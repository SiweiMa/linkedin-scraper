"""LinkedIn Job Postings Scraper."""

import argparse
import logging
import os
from dataclasses import dataclass
from typing import List
import time
import json

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains

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
    
    # Try multiple parsing strategies for different LinkedIn page layouts
    parsing_strategies = [
        # Strategy 1: Original selector
        {
            "container": ".jobs-search-results__list-item",
            "link_selector": "a",
            "title_selector": None  # Use the link text directly
        },
        # Strategy 2: Job result cards
        {
            "container": ".job-result-card",
            "link_selector": "a[data-control-name='job_card_click']",
            "title_selector": "h3, .job-result-card__title"
        },
        # Strategy 3: Entity lockup (newer LinkedIn layout)
        {
            "container": ".artdeco-entity-lockup",
            "link_selector": "a",
            "title_selector": ".artdeco-entity-lockup__title"
        },
        # Strategy 4: General job listings
        {
            "container": "[data-entity-urn*='job']",
            "link_selector": "a",
            "title_selector": "h3, h4, .job-title"
        }
    ]
    
    for strategy in parsing_strategies:
        containers = soup.select(strategy["container"])
        if not containers:
            continue
            
        logger.info(f"Trying parsing strategy with {len(containers)} containers found")
        
        for container in containers:
            try:
                # Find the link
                if strategy["link_selector"]:
                    link_element = container.select_one(strategy["link_selector"])
                else:
                    link_element = container if container.name == 'a' else container.find('a')
                
                if not link_element:
                    continue
                
                link = link_element.get("href")
                if not link:
                    continue
                
                # Ensure link is absolute
                if link.startswith("/"):
                    link = "https://www.linkedin.com" + link
                
                # Find the title
                title = ""
                if strategy["title_selector"]:
                    title_element = container.select_one(strategy["title_selector"])
                    if title_element:
                        title = title_element.get_text(strip=True)
                
                # Fallback: use link text if no title found
                if not title:
                    title = link_element.get_text(strip=True)
                
                # Clean up title
                title = title.replace('\n', ' ').strip()
                if len(title) > 200:  # Truncate very long titles
                    title = title[:200] + "..."
                
                if title and link and title.lower() not in ['see more jobs', 'view more']:
                    postings.append(JobPosting(title=title, link=link))
                    
            except Exception as e:
                logger.debug(f"Error parsing job posting: {e}")
                continue
        
        # If we found postings with this strategy, use them
        if postings:
            logger.info(f"Successfully parsed {len(postings)} job postings")
            return postings
    
    # If no strategy worked, log some debug info
    logger.warning("No job postings found with any parsing strategy")
    
    # Look for any links that might be jobs for debugging
    all_links = soup.find_all('a', href=True)
    job_links = [link for link in all_links if '/jobs/' in link.get('href', '')]
    if job_links:
        logger.debug(f"Found {len(job_links)} links containing '/jobs/' for debugging")
    
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
        # Use the standard LinkedIn login URL
        driver.get("https://www.linkedin.com/login")
        
        # Add a small delay to mimic human behavior
        time.sleep(2)
        
        # Wait for and find the username field
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        
        # Clear and enter username with human-like typing
        username_field.clear()
        time.sleep(0.5)
        for char in username:
            username_field.send_keys(char)
            time.sleep(0.1)  # Small delay between keystrokes
        
        # Find password field
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        time.sleep(0.5)
        
        # Enter password with human-like typing
        for char in password:
            password_field.send_keys(char)
            time.sleep(0.1)
        
        time.sleep(1)
        
        # Find and click the login button
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        # Wait for login to complete - check for multiple possible success indicators
        try:
            # Wait for either feed page or any post-login page
            WebDriverWait(driver, 15).until(
                lambda d: "/feed" in d.current_url or 
                         "/in/" in d.current_url or
                         "linkedin.com/feed" in d.current_url or
                         d.find_elements(By.CSS_SELECTOR, "[data-test-id='nav-top-secondary']")
            )
            logger.info("Successfully logged into LinkedIn")
            return True
            
        except Exception as e:
            # Check if we're on a challenge page (CAPTCHA, verification, etc.)
            current_url = driver.current_url
            page_source = driver.page_source.lower()
            
            if "challenge" in current_url or "verification" in page_source or "captcha" in page_source:
                logger.error("Login blocked - security challenge detected. LinkedIn may have detected automation.")
                return False
            elif "login" in current_url:
                # Check for error messages
                error_elements = driver.find_elements(By.CSS_SELECTOR, ".form__label--error, .alert, .error")
                if error_elements:
                    error_msg = error_elements[0].text
                    logger.error(f"Login failed with error: {error_msg}")
                else:
                    logger.error("Login failed - still on login page")
                return False
            else:
                logger.error(f"Unexpected page after login: {current_url}")
                return False
                
    except WebDriverException as exc:
        logger.error("Failed to log into LinkedIn: %s", str(exc))
        return False
    except Exception as exc:
        logger.error("Unexpected error during login: %s", str(exc))
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
        logger.info(f"Navigating to search URL: {search_url}")
        driver.get(search_url)
        
        # Add longer wait and human-like delay
        time.sleep(3)
        
        # Check current URL to see if we were redirected
        current_url = driver.current_url
        logger.info(f"Current URL after navigation: {current_url}")
        
        # Check if we're on an unexpected page
        if "login" in current_url or "challenge" in current_url:
            logger.error("Redirected to login or challenge page")
            return []
        
        selector = ".artdeco-entity-lockup"
        job_elements = None
        result = {}

        try:
            logger.info(f"Trying selector: {selector}")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            job_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            # Print details about job elements for debugging
            logger.info("Job elements details:")

            for i, element in enumerate(job_elements):
                logger.info(f"Element {i}:")
                logger.info(f"  Text content: {element.text}")
            
                # Try to click the element and see where it navigates
                try:
                    current_url = driver.current_url
                    element.click()
                    time.sleep(2)
                    new_url = driver.current_url
                    if new_url != current_url:
                        logger.info(f"  Element click navigated to: {new_url}")
                        result[element.text] = new_url
                        # Navigate back
                        driver.back()
                        time.sleep(2)
                    else:
                        logger.info(f"  Element click did not navigate to new page")
                except Exception as e:
                    logger.info(f"  Could not click element: {e}")

                
            if job_elements:
                logger.info(f"Found {len(job_elements)} elements with selector: {selector}")
        except Exception as e:
            logger.debug(f"Selector {selector} failed: {e}")
        
        if not job_elements:
            # Save page source for debugging
            logger.error("No job elements found with any selector")
            logger.debug(f"Page title: {driver.title}")
            
            # Check for common error indicators
            page_source = driver.page_source.lower()
            if "no results" in page_source or "try a different search" in page_source:
                logger.info("No job results found for this search")
            elif "sign in" in page_source or "log in" in page_source:
                logger.error("Authentication required - may need to re-login")
            else:
                logger.error("Unknown page structure - LinkedIn may have changed their layout")
            
            return []
        
        html = driver.page_source
        # store the result in a file
        with open("job_postings.json", "w") as f:
            json.dump(result, f)
        return parse_job_postings(html)
        
    except WebDriverException as exc:
        logger.error("WebDriver error fetching job postings: %s", str(exc))
        # Try to get more context about the error
        try:
            current_url = driver.current_url
            page_title = driver.title
            logger.error(f"Error occurred on page: {current_url}")
            logger.error(f"Page title: {page_title}")
        except:
            pass
        return []
    except Exception as exc:
        logger.error("Unexpected error fetching job postings: %s", str(exc))
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
    
    # Add options to avoid detection and improve stability
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")  # Faster loading
# Removed --disable-javascript as LinkedIn requires JS to function
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Set window size for consistency
    options.add_argument("--window-size=1920,1080")
    
    if args.headless:
        options.add_argument("--headless=new")  # Use new headless mode
    
    # Set page load strategy
    options.page_load_strategy = 'normal'
    
    try:
        service = Service(args.driver_path) if args.driver_path else Service()
        with webdriver.Chrome(service=service, options=options) as driver:
            # Set timeouts
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            # Execute script to remove webdriver property
            try:
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except Exception as e:
                logger.warning(f"Could not execute anti-detection script: {e}")
            
            if not login(driver, args.username, args.password):
                logger.error("Login failed, exiting")
                return
            
            # Add delay before fetching jobs
            time.sleep(2)
            
            postings = fetch_job_postings(driver, args.search_url)
            if not postings:
                logger.warning("No job postings found")
                return
            
            logger.info(f"Successfully scraped {len(postings)} job postings")
            for post in postings:
                print(f"{post.title} - {post.link}")
                
    except Exception as exc:
        logger.error(f"Failed to initialize or run Chrome driver: {exc}")
        return


if __name__ == "__main__":
    main()
