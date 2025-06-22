import pandas as pd
import getpass
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import smtplib
import argparse
import logging
import os
from dataclasses import dataclass
from typing import List
import time
import json
from logging.handlers import RotatingFileHandler

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains

# Enhanced logging configuration
# Create logs directory if it doesn't exist
logs_dir = 'logs'
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Configure logging with both file and console handlers
log_filename = os.path.join(logs_dir, 'linkedin_scraper.log')

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create file handler with rotation (max 10MB per file, keep 5 backup files)
file_handler = RotatingFileHandler(
    log_filename, 
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Less verbose on console
console_handler.setFormatter(formatter)

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)

# Log the start of the session
logger.info("="*60)
logger.info("STARTING NEW LINKEDIN SCRAPER SESSION")
logger.info(f"Log file location: {os.path.abspath(log_filename)}")
logger.info("="*60)

data_list = []  # Create an empty list to store data

def get_job_title(soup):
    title = 'disabled ember-view job-card-container__link job-card-list__title'
    title_tag = soup.find_all('a', {'class': title})
    titles = [title.text.strip() for title in title_tag]
    return titles

def get_company(soup):
    company = 'artdeco-entity-lockup__subtitle ember-view'
    companies = soup.find_all('div', {'class': company})
    company_name = [comp.text.strip() for comp in companies]
    return company_name
    
def get_location(soup):
    loc = 'artdeco-entity-lockup__caption ember-view'
    locat = soup.find_all('div',{'class':loc})
    location = [loct.text.strip() for loct in locat]
    return location

def get_url(soup):
    url_tag = soup.find_all('a','disabled ember-view job-card-container__link job-card-list__title')
    base_url = 'https://www.linkedin.com'
    link = [base_url + tag['href'] for tag in url_tag]
    return link


def info(soup):
    info_dict = {'Job Title': get_job_title(soup), 'Company Name': get_company(soup), 'Location': get_location(soup), 'Link':get_url(soup)}
    return info_dict


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

def safe_find_element(driver, by, value, timeout=10, description=""):
    """Safely find an element with proper error handling and logging."""
    try:
        logger.debug(f"Attempting to find element: {description} using {by}='{value}'")
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        logger.debug(f"Successfully found element: {description}")
        return element
    except TimeoutException:
        logger.error(f"Timeout waiting for element: {description} using {by}='{value}'")
        logger.debug(f"Current URL: {driver.current_url}")
        logger.debug(f"Page title: {driver.title}")
        return None
    except NoSuchElementException:
        logger.error(f"Element not found: {description} using {by}='{value}'")
        return None
    except Exception as e:
        logger.error(f"Unexpected error finding element {description}: {str(e)}")
        return None

def safe_click_element(driver, element, description=""):
    """Safely click an element with error handling."""
    try:
        if element:
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            element.click()
            logger.debug(f"Successfully clicked: {description}")
            return True
        else:
            logger.error(f"Cannot click null element: {description}")
            return False
    except Exception as e:
        logger.error(f"Error clicking element {description}: {str(e)}")
        return False

# Your original variables
username = 'sm3614@columbia.edu' #'sma34@dons.usfca.edu' #
password = 'Qw090909'
search = 'Senior Data Scientist'

logger.info("Starting LinkedIn scraper")
driver = webdriver.Chrome()
driver.maximize_window()

try:
    if not login(driver, username, password):
        logger.error("Login failed, exiting")
        driver.quit()
        exit(1)

    logger.info(f"Searching for: {search}")
    
    # Find search element with better error handling
    search_element = safe_find_element(
        driver, 
        By.CSS_SELECTOR, 
        "input.search-global-typeahead__input",
        description="search input field"
    )
    
    if not search_element:
        # Try alternative selectors
        logger.warning("Primary search selector failed, trying alternatives")
        alternative_selectors = [
            "input[placeholder*='Search']",
            ".search-global-typeahead__input",
            "input.global-nav__search-typeahead-input"
        ]
        
        for selector in alternative_selectors:
            search_element = safe_find_element(driver, By.CSS_SELECTOR, selector, timeout=5, description=f"alternative search selector: {selector}")
            if search_element:
                break
    
    if not search_element:
        logger.error("Could not find search input field")
        raise Exception("Search input field not found")
    
    search_element.clear()
    search_element.send_keys(search)
    search_element.send_keys(Keys.RETURN)
    logger.info("Search submitted, waiting for results")
    time.sleep(5)

    # Click Jobs filter with better error handling
    jobs_filter = safe_find_element(
        driver,
        By.CSS_SELECTOR,
        '.artdeco-pill.artdeco-pill--slate.artdeco-pill--choice.artdeco-pill--2.search-reusables__filter-pill-button',
        description="Jobs filter button"
    )
    
    if not jobs_filter:
        # Try alternative jobs filter selectors
        logger.warning("Primary jobs filter selector failed, trying alternatives")
        alternative_jobs_selectors = [
            "button[aria-label='Jobs']",
            ".search-reusables__filter-pill-button:contains('Jobs')",
            "button:contains('Jobs')"
        ]
        
        for selector in alternative_jobs_selectors:
            jobs_filter = safe_find_element(driver, By.CSS_SELECTOR, selector, timeout=5, description=f"alternative jobs filter: {selector}")
            if jobs_filter:
                break
    
    if not jobs_filter:
        logger.error("Could not find Jobs filter button")
        raise Exception("Jobs filter button not found")
    
    if not safe_click_element(driver, jobs_filter, "Jobs filter button"):
        raise Exception("Failed to click Jobs filter")
    
    logger.info("Jobs filter clicked, waiting for page to load")
    time.sleep(8)

    search_url = 'https://www.linkedin.com/jobs/collections/top-applicant/?currentJobId=4254759627'
    logger.info(f"Navigating to search URL: {search_url}")
    driver.get(search_url)
    
    # Add longer wait and human-like delay
    time.sleep(3)

    # Debug: Log current page state
    logger.debug(f"Current URL after jobs filter: {driver.current_url}")
    logger.debug(f"Page title: {driver.title}")

    data_list = []

    for i in range(40):
        logger.info(f"Processing page {i+1}/4")
        
        # Find pagination button with better error handling
        if i + 1 != 1:
            page_button = safe_find_element(
                driver,
                By.CSS_SELECTOR,
                f'button[aria-label="Page {i+1}"]',
                timeout=10,
                description=f"Page {i+1} button"
            )
            
            if not page_button:
                # Try alternative pagination selectors
                alternative_selectors = [
                    f'button:contains("{i+1}")',
                    f'li[data-test-pagination-page-btn="{i+1}"] button',
                    f'button[data-test-pagination-page-btn="{i+1}"]'
                ]
                
                for selector in alternative_selectors:
                    page_button = safe_find_element(driver, By.CSS_SELECTOR, selector, timeout=5, description=f"alternative page {i+1} selector")
                    if page_button:
                        break
            
            if page_button:
                if safe_click_element(driver, page_button, f"Page {i+1} button"):
                    logger.info(f"Clicked page {i+1} button, waiting for page to load")
                    time.sleep(15)
                else:
                    logger.warning(f"Failed to click page {i+1} button, continuing with current page")
            else:
                logger.warning(f"Could not find page {i+1} button, stopping pagination")
                break

        # Re-establish scroll origin for each page to avoid stale element reference
        logger.info(f"Establishing scroll origin for page {i+1}")
        scroll_containers = [
            '//div[contains(@class, "search-results")]'
        ]
        
        footer = None
        for xpath in scroll_containers:
            try:
                logger.debug(f"Trying to find scroll container with xpath: {xpath}")
                footer = driver.find_element(By.XPATH, xpath)
                logger.info(f"Found scroll container using xpath: {xpath}")
                break
            except NoSuchElementException:
                logger.debug(f"Container not found with xpath: {xpath}")
                continue
        
        if not footer:
            logger.error(f"Could not find any suitable scroll container for page {i+1}")
            logger.warning(f"Skipping scrolling for page {i+1}")
            scroll_origin = None
        else:
            scroll_origin = ScrollOrigin.from_element(footer)
            logger.info(f"Scroll origin established for page {i+1}")

        # Scroll and collect data
        if scroll_origin:
            logger.info(f"Scrolling page {i+1}")
            for scroll_count in range(6):
                try:
                    ActionChains(driver).scroll_from_origin(scroll_origin, 0, scroll_count*500).perform()
                    logger.debug(f"Scroll {scroll_count+1}/6 completed")
                    time.sleep(30)
                except Exception as e:
                    logger.error(f"Error during scroll {scroll_count+1}: {str(e)}")
                    # Try to re-establish scroll origin if it becomes stale
                    try:
                        footer = driver.find_element(By.XPATH, scroll_containers[0])
                        scroll_origin = ScrollOrigin.from_element(footer)
                        logger.info("Re-established scroll origin after error")
                        # Retry the scroll
                        ActionChains(driver).scroll_from_origin(scroll_origin, 0, scroll_count*500).perform()
                        logger.debug(f"Retry scroll {scroll_count+1}/6 completed")
                        time.sleep(30)
                    except Exception as retry_error:
                        logger.error(f"Failed to retry scroll {scroll_count+1}: {str(retry_error)}")
                        break
        else:
            logger.warning(f"No scroll origin available for page {i+1}, skipping scrolling")

        # Parse job elements using Selenium
        logger.info(f"Parsing page {i+1} content")
        selector = ".artdeco-entity-lockup"
        job_elements = None
        data = {'Job Title': [], 'Company Name': [], 'Location': [], 'Link': []}

        try:
            logger.info(f"Trying selector: {selector}")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            job_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            logger.info("Job elements details:")

            for i, element in enumerate(job_elements):
                logger.info(f"Element {i}:")
                logger.info(f"  Text content: {element.text}")
            
                try:
                    current_url = driver.current_url
                    element.click()
                    time.sleep(2)
                    new_url = driver.current_url
                    
                    # Extract job details
                    title = element.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__title").text
                    company = element.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__subtitle").text
                    location = element.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__caption").text
                    
                    data['Job Title'].append(title)
                    data['Company Name'].append(company)
                    data['Location'].append(location)
                    data['Link'].append(new_url)
                    
                    if new_url != current_url:
                        logger.info(f"  Element click navigated to: {new_url}")
                        driver.back()
                        time.sleep(2)
                    else:
                        logger.info(f"  Element click did not navigate to new page")
                except Exception as e:
                    logger.info(f"  Could not process element: {e}")

            if job_elements:
                logger.info(f"Found {len(job_elements)} elements with selector: {selector}")
        except Exception as e:
            logger.debug(f"Selector {selector} failed: {e}")
        
        logger.info(f"Page {i+1} data: {len(data.get('Job Title', []))} jobs found")
        logger.debug(f"Page {i+1} sample data: {data}")
        
        # Append the data to the list
        data_list.append(data)

    # Write data to text file
    logger.info("Writing collected data to text file")
    output_file = 'linkedin_data.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("LinkedIn Job Scraping Results\n")
        f.write("=" * 50 + "\n\n")
        
        job_count = 0
        for page_num, page_data in enumerate(data_list, 1):
            f.write(f"PAGE {page_num} RESULTS:\n")
            f.write("-" * 30 + "\n")
            
            # Get the length of the shortest list to avoid index errors
            min_length = min(len(page_data.get('Job Title', [])), 
                           len(page_data.get('Company Name', [])), 
                           len(page_data.get('Location', [])), 
                           len(page_data.get('Link', [])))
            
            for i in range(min_length):
                job_count += 1
                f.write(f"Job #{job_count}:\n")
                f.write(f"  Title: {page_data['Job Title'][i]}\n")
                f.write(f"  Company: {page_data['Company Name'][i]}\n")
                f.write(f"  Location: {page_data['Location'][i]}\n")
                f.write(f"  Link: {page_data['Link'][i]}\n")
                f.write("\n")
            
            f.write(f"Page {page_num} total jobs: {min_length}\n\n")
            # also save the data to a csv file
            df = pd.DataFrame(page_data)
            df.to_csv(f'linkedin_data_{page_num}.csv', index=False)

    logger.info(f"Data saved to {output_file} with {job_count} total job listings")

except Exception as e:
    logger.error(f"An error occurred during scraping: {str(e)}")
    logger.debug(f"Current URL: {driver.current_url}")
    logger.debug(f"Page title: {driver.title}")
    
    # Save screenshot for debugging
    try:
        screenshot_path = f"error_screenshot_{int(time.time())}.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"Screenshot saved to {screenshot_path}")
    except Exception as screenshot_error:
        logger.error(f"Could not save screenshot: {str(screenshot_error)}")
    
    raise e

finally:
    logger.info("Closing browser")
    driver.quit()