#!/usr/bin/env python3
"""Debug script for LinkedIn login issues."""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_login():
    """Debug LinkedIn login process with detailed logging."""
    
    # Get credentials from environment variables
    username = os.getenv("LINKEDIN_USERNAME")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if not username or not password:
        logger.error("Please set LINKEDIN_USERNAME and LINKEDIN_PASSWORD environment variables")
        return
    
    # Setup Chrome with anti-detection measures
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("Navigating to LinkedIn login page...")
        driver.get("https://www.linkedin.com/login")
        
        # Take screenshot of login page
        driver.save_screenshot("debug_login_page.png")
        logger.info("Screenshot saved: debug_login_page.png")
        
        time.sleep(3)
        
        logger.info("Looking for username field...")
        try:
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            logger.info("Found username field")
        except Exception as e:
            logger.error(f"Could not find username field: {e}")
            # Try alternative selectors
            try:
                username_field = driver.find_element(By.NAME, "session_key")
                logger.info("Found username field with alternative selector")
            except Exception as e2:
                logger.error(f"Could not find username field with alternative selector: {e2}")
                driver.save_screenshot("debug_no_username_field.png")
                return
        
        logger.info("Looking for password field...")
        try:
            password_field = driver.find_element(By.ID, "password")
            logger.info("Found password field")
        except Exception as e:
            logger.error(f"Could not find password field: {e}")
            # Try alternative selectors
            try:
                password_field = driver.find_element(By.NAME, "session_password")
                logger.info("Found password field with alternative selector")
            except Exception as e2:
                logger.error(f"Could not find password field with alternative selector: {e2}")
                driver.save_screenshot("debug_no_password_field.png")
                return
        
        logger.info("Entering credentials...")
        username_field.clear()
        time.sleep(0.5)
        username_field.send_keys(username)
        
        password_field.clear()
        time.sleep(0.5)
        password_field.send_keys(password)
        
        time.sleep(1)
        
        logger.info("Looking for login button...")
        try:
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            logger.info("Found login button")
        except Exception as e:
            logger.error(f"Could not find login button: {e}")
            # Try alternative selectors
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, "button[data-litms-control-urn='login-submit']")
                logger.info("Found login button with alternative selector")
            except Exception as e2:
                logger.error(f"Could not find login button with alternative selector: {e2}")
                driver.save_screenshot("debug_no_login_button.png")
                return
        
        # Take screenshot before clicking login
        driver.save_screenshot("debug_before_login.png")
        logger.info("Screenshot before login saved: debug_before_login.png")
        
        logger.info("Clicking login button...")
        login_button.click()
        
        # Wait a bit for the page to respond
        time.sleep(5)
        
        # Take screenshot after login attempt
        driver.save_screenshot("debug_after_login.png")
        logger.info("Screenshot after login saved: debug_after_login.png")
        
        current_url = driver.current_url
        logger.info(f"Current URL after login: {current_url}")
        
        # Check page title
        page_title = driver.title
        logger.info(f"Page title: {page_title}")
        
        # Check for common indicators
        if "/feed" in current_url or "/in/" in current_url:
            logger.info("SUCCESS: Login appears successful!")
        elif "login" in current_url:
            logger.warning("Still on login page - login may have failed")
            
            # Check for error messages
            error_selectors = [
                ".form__label--error",
                ".alert",
                ".error",
                "[data-js-module-id='guest-frontend-challenge-alert']",
                ".challenge",
                ".verification"
            ]
            
            for selector in error_selectors:
                try:
                    error_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if error_elements:
                        error_text = error_elements[0].text.strip()
                        if error_text:
                            logger.error(f"Error message found: {error_text}")
                except Exception:
                    continue
                    
        elif "challenge" in current_url or "verification" in current_url:
            logger.warning("LinkedIn security challenge detected - automation may be blocked")
        else:
            logger.info(f"Redirected to unexpected page: {current_url}")
        
        # Wait a bit more to see final state
        time.sleep(3)
        driver.save_screenshot("debug_final_state.png")
        logger.info("Final screenshot saved: debug_final_state.png")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        driver.save_screenshot("debug_error.png")
        
    finally:
        logger.info("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    debug_login() 