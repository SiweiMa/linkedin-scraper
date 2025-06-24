#!/usr/bin/env python3
"""
LinkedIn Job Scraper

A web scraper for collecting job postings from LinkedIn using Selenium WebDriver.
Supports pagination, scrolling, and saves results to CSV and text files.

Usage:
    python linkedin_scraper.py --username your_email@example.com --password your_password
"""

import argparse
import json
import logging
import os
import time
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Optional, Union

import pandas as pd
import smtplib
from bs4 import BeautifulSoup
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException, 
    TimeoutException, 
    WebDriverException
)
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement


@dataclass
class ScrapingConfig:
    """Configuration class for scraping parameters."""
    username: str = ""
    password: str = ""
    search_query: str = "Senior Data Scientist"
    search_url: str = 'https://www.linkedin.com/jobs/search-results/?f_TPR=r604800&keywords=%22senior%20data%20engineer%22&origin=JOBS_HOME_SEARCH_BUTTON'
    total_pages: int = 100
    scroll_count: int = 10
    scroll_step: int = 500
    page_load_timeout: int = 60
    script_timeout: int = 30
    implicit_wait: int = 10
    element_wait_timeout: int = 15
    max_retries: int = 3
    retry_delay: int = 5


class LinkedInScraper:
    """Main scraper class for LinkedIn job postings."""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.data_list: List[Dict[str, List[str]]] = []
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logs_dir = 'logs'
        os.makedirs(logs_dir, exist_ok=True)

        log_filename = os.path.join(logs_dir, 'linkedin_scraper.log')
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_filename, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # Configure logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Log session start
        logger.info("="*60)
        logger.info("STARTING NEW LINKEDIN SCRAPER SESSION")
        logger.info(f"Log file: {os.path.abspath(log_filename)}")
        logger.info("="*60)
        
        return logger

    def _create_driver(self) -> webdriver.Chrome:
        """Create and configure Chrome WebDriver."""
        chrome_options = Options()
        
        # Performance and stability options
        performance_options = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-images",
            "--page-load-strategy=eager",
            "--memory-pressure-off",
            "--max_old_space_size=4096",
            "--aggressive-cache-discard",
            "--timeout=30000"
        ]
        
        for option in performance_options:
            chrome_options.add_argument(option)
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(self.config.page_load_timeout)
            driver.set_script_timeout(self.config.script_timeout)
            driver.implicitly_wait(self.config.implicit_wait)
            driver.maximize_window()
            
            self.logger.info("Chrome WebDriver created successfully")
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to create Chrome WebDriver: {e}")
            raise

    def _safe_find_element(self, by: By, value: str, timeout: Optional[int] = None, 
                          description: str = "") -> Optional[WebElement]:
        """Safely find an element with error handling."""
        if not self.driver:
            self.logger.error("Driver not initialized")
            return None
            
        timeout = timeout or self.config.element_wait_timeout
        
        try:
            self.logger.debug(f"Finding element: {description}")
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))  # type: ignore
            )
            self.logger.debug(f"Found element: {description}")
            return element
        except TimeoutException:
            self.logger.warning(f"Timeout finding element: {description}")
            return None
        except Exception as e:
            self.logger.error(f"Error finding element {description}: {e}")
            return None

    def _safe_click_element(self, element: Optional[WebElement], description: str = "") -> bool:
        """Safely click an element."""
        if not self.driver or not element:
            self.logger.error(f"Cannot click element: {description}")
            return False
            
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            element.click()
            self.logger.debug(f"Clicked: {description}")
            return True
        except Exception as e:
            self.logger.error(f"Error clicking {description}: {e}")
            return False

    def _validate_credentials(self) -> bool:
        """Validate that credentials are provided."""
        if not self.config.username or not self.config.password:
            self.logger.error("Username and password are required")
            return False
        return True

    def login(self) -> bool:
        """Perform login to LinkedIn."""
        if not self.driver:
            self.logger.error("Driver not initialized")
            return False
            
        if not self._validate_credentials():
            return False
            
        try:
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)
            
            # Enter username
            username_field = self._safe_find_element(By.ID, "username", description="username field")
            if not username_field:
                return False
                
            username_field.clear()
            time.sleep(0.5)
            username_field.send_keys(self.config.username)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            time.sleep(0.5)
            password_field.send_keys(self.config.password)
            
            time.sleep(1)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login success
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda d: any([
                        "/feed" in d.current_url,
                        "/in/" in d.current_url,
                        "linkedin.com/feed" in d.current_url,
                        d.find_elements(By.CSS_SELECTOR, "[data-test-id='nav-top-secondary']")
                    ])
                )
                self.logger.info("Successfully logged into LinkedIn")
                return True
                
            except Exception:
                current_url = self.driver.current_url
                page_source = self.driver.page_source.lower()
                
                if "challenge" in current_url or "verification" in page_source:
                    self.logger.error("Login blocked - security challenge detected")
                elif "login" in current_url:
                    self.logger.error("Login failed - still on login page")
                else:
                    self.logger.error(f"Unexpected page after login: {current_url}")
                return False
                    
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False

    def _navigate_to_page(self, page_num: int) -> bool:
        """Navigate to a specific page in search results."""
        if page_num == 1:
            return True
            
        # Try multiple selectors for pagination
        selectors = [
            f'button[aria-label="Page {page_num}"]',
            f'li[data-test-pagination-page-btn="{page_num}"] button',
            f'button[data-test-pagination-page-btn="{page_num}"]'
        ]
        
        for selector in selectors:
            page_button = self._safe_find_element(
                By.CSS_SELECTOR, selector, timeout=10,
                description=f"Page {page_num} button"
            )
            if page_button and self._safe_click_element(page_button, f"Page {page_num}"):
                self.logger.info(f"Navigated to page {page_num}")
                time.sleep(15)
                return True
        
        self.logger.warning(f"Could not navigate to page {page_num}")
        return False

    def _scroll_page(self) -> None:
        """Scroll through the page to load all job listings."""
        if not self.driver:
            return
            
        try:
            # Find scroll container
            footer = self.driver.find_element(By.XPATH, '//div[contains(@class, "search-results")]')
            scroll_origin = ScrollOrigin.from_element(footer)
            
            # Perform scrolling
            for i in range(self.config.scroll_count):
                try:
                    ActionChains(self.driver).scroll_from_origin(
                        scroll_origin, 0, i * self.config.scroll_step
                    ).perform()
                    time.sleep(2)
                except Exception as e:
                    self.logger.warning(f"Scroll error at step {i}: {e}")
                    break
                    
        except NoSuchElementException:
            self.logger.warning("No scroll container found, skipping scrolling")

    def _extract_job_data(self) -> Dict[str, List[str]]:
        """Extract job data from current page."""
        if not self.driver:
            return {'Job Title': [], 'Company Name': [], 'Location': [], 'Link': []}
            
        data = {'Job Title': [], 'Company Name': [], 'Location': [], 'Link': []}
        
        try:
            # Wait for job elements to load
            WebDriverWait(self.driver, self.config.element_wait_timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".artdeco-entity-lockup"))  # type: ignore
            )
            
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, ".artdeco-entity-lockup")
            
            for element in job_elements:
                try:
                    # Extract job information
                    title_elem = element.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__title")
                    company_elem = element.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__subtitle")
                    location_elem = element.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__caption")
                    
                    # Get job URL by clicking element
                    current_url = self.driver.current_url
                    element.click()
                    time.sleep(2)
                    job_url = self.driver.current_url
                    
                    # Store data
                    data['Job Title'].append(title_elem.text.strip())
                    data['Company Name'].append(company_elem.text.strip())
                    data['Location'].append(location_elem.text.strip())
                    data['Link'].append(job_url)
                    
                    # Navigate back if URL changed
                    if job_url != current_url:
                        self.driver.back()
                        time.sleep(2)
                        
                except Exception as e:
                    self.logger.debug(f"Error processing job element: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error extracting job data: {e}")
            
        return data

    def _save_page_data(self, page_data: Dict[str, List[str]], page_num: int) -> None:
        """Save data for a single page immediately to CSV."""
        try:
            # Get minimum length to avoid index errors
            min_length = min(
                len(page_data.get('Job Title', [])),
                len(page_data.get('Company Name', [])),
                len(page_data.get('Location', [])),
                len(page_data.get('Link', []))
            )
            
            if min_length > 0:
                df = pd.DataFrame(page_data)
                csv_filename = f'linkedin_data_page_{page_num}.csv'
                df.to_csv(csv_filename, index=False)
                self.logger.info(f"Saved page {page_num} to {csv_filename} ({min_length} jobs)")
            else:
                self.logger.warning(f"No valid data to save for page {page_num}")
                
        except Exception as e:
            self.logger.error(f"Error saving page {page_num} data: {e}")

    def scrape(self) -> bool:
        """Main scraping method."""
        try:
            self.driver = self._create_driver()
            
            if not self.login():
                self.logger.error("Login failed, exiting")
                return False
            
            self.logger.info(f"Navigating to: {self.config.search_url}")
            self.driver.get(self.config.search_url)
            time.sleep(3)
            
            # Scrape pages
            for page_num in range(1, self.config.total_pages + 1):
                self.logger.info(f"Processing page {page_num}/{self.config.total_pages}")
                
                if not self._navigate_to_page(page_num):
                    self.logger.warning(f"Stopping at page {page_num-1}")
                    break
                
                self._scroll_page()
                page_data = self._extract_job_data()
                
                jobs_found = len(page_data.get('Job Title', []))
                self.logger.info(f"Page {page_num}: {jobs_found} jobs found")
                
                if jobs_found > 0:
                    # Save page data immediately and don't keep it in memory
                    self._save_page_data(page_data, page_num)
                else:
                    self.logger.warning(f"No jobs found on page {page_num}")
            
            self.logger.info("Scraping completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Scraping error: {e}")
            
            # Save error screenshot
            if self.driver:
                try:
                    screenshot_path = f"error_screenshot_{int(time.time())}.png"
                    self.driver.save_screenshot(screenshot_path)
                    self.logger.info(f"Error screenshot saved: {screenshot_path}")
                except Exception:
                    pass
                    
            return False
            
        finally:
            if self.driver:
                self.logger.info("Closing browser")
                self.driver.quit()


def create_config_from_args(args: argparse.Namespace) -> ScrapingConfig:
    """Create configuration from command line arguments."""
    config = ScrapingConfig()
    
    if args.username:
        config.username = args.username
    if args.password:
        config.password = args.password
    if args.search_query:
        config.search_query = args.search_query
    if args.pages:
        config.total_pages = args.pages
        
    return config


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='LinkedIn Job Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python linkedin_scraper.py --username user@example.com --password mypass
  python linkedin_scraper.py --username user@example.com --password mypass --pages 50
        """
    )
    
    parser.add_argument('--username', required=True, help='LinkedIn username/email')
    parser.add_argument('--password', required=True, help='LinkedIn password')
    parser.add_argument('--search-query', help='Job search query')
    parser.add_argument('--pages', type=int, default=100, help='Number of pages to scrape')
    
    args = parser.parse_args()
    
    # Create configuration and run scraper
    config = create_config_from_args(args)
    scraper = LinkedInScraper(config)
    
    success = scraper.scrape()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()