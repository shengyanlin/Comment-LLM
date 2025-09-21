"""
Google Maps Reviews Scraper

This module provides functionality to scrape reviews from Google Maps
for a given business using the Google Maps URL.
"""

import time
import re
import logging
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd

logger = logging.getLogger(__name__)


class GoogleMapsScraper:
    """
    A scraper for extracting reviews from Google Maps business pages.
    """
    
    def __init__(self, headless: bool = True, chromedriver_path: Optional[str] = None):
        """
        Initialize the Google Maps scraper.
        
        Args:
            headless: Whether to run Chrome in headless mode
            chromedriver_path: Path to chromedriver executable
        """
        self.headless = headless
        self.chromedriver_path = chromedriver_path
        self.driver = None
        
    def _setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        if self.chromedriver_path:
            driver = webdriver.Chrome(executable_path=self.chromedriver_path, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
            
        return driver
    
    def _extract_business_info(self) -> Dict[str, str]:
        """Extract basic business information from the Google Maps page."""
        business_info = {}
        
        try:
            # Business name
            name_element = self.driver.find_element(By.CSS_SELECTOR, "h1[data-attrid='title']")
            business_info['name'] = name_element.text
        except NoSuchElementException:
            try:
                name_element = self.driver.find_element(By.CSS_SELECTOR, "h1.x3AX1-LfntMc-header-title-title")
                business_info['name'] = name_element.text
            except NoSuchElementException:
                business_info['name'] = "Unknown Business"
        
        try:
            # Rating
            rating_element = self.driver.find_element(By.CSS_SELECTOR, "span.ceNzKf")
            business_info['rating'] = rating_element.text
        except NoSuchElementException:
            business_info['rating'] = "No rating"
        
        try:
            # Number of reviews
            reviews_count_element = self.driver.find_element(By.CSS_SELECTOR, "span.RDApEe.YrbPuc")
            business_info['reviews_count'] = reviews_count_element.text
        except NoSuchElementException:
            business_info['reviews_count'] = "No reviews count"
        
        return business_info
    
    def _scroll_to_load_reviews(self, max_reviews: int = 100) -> None:
        """Scroll through the reviews section to load more reviews."""
        try:
            # Find the reviews container
            reviews_container = self.driver.find_element(By.CSS_SELECTOR, "div[data-review-id]")
            parent_container = reviews_container.find_element(By.XPATH, "..")
            
            last_height = self.driver.execute_script("return arguments[0].scrollHeight", parent_container)
            reviews_loaded = 0
            
            while reviews_loaded < max_reviews:
                # Scroll down
                self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", parent_container)
                time.sleep(2)
                
                # Wait for new content to load
                try:
                    WebDriverWait(self.driver, 5).until(
                        lambda driver: driver.execute_script("return arguments[0].scrollHeight", parent_container) > last_height
                    )
                    new_height = self.driver.execute_script("return arguments[0].scrollHeight", parent_container)
                    if new_height == last_height:
                        break
                    last_height = new_height
                    
                    # Count current reviews
                    current_reviews = len(self.driver.find_elements(By.CSS_SELECTOR, "div[data-review-id]"))
                    reviews_loaded = current_reviews
                    logger.info(f"Loaded {reviews_loaded} reviews so far...")
                    
                except TimeoutException:
                    break
                    
        except NoSuchElementException:
            logger.warning("Could not find reviews container for scrolling")
    
    def _parse_reviews(self) -> List[Dict[str, str]]:
        """Parse individual reviews from the page."""
        reviews = []
        
        try:
            review_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-review-id]")
            
            for review_element in review_elements:
                review_data = {}
                
                try:
                    # Reviewer name
                    name_element = review_element.find_element(By.CSS_SELECTOR, "div.d4r55")
                    review_data['reviewer_name'] = name_element.text
                except NoSuchElementException:
                    review_data['reviewer_name'] = "Anonymous"
                
                try:
                    # Review rating
                    rating_element = review_element.find_element(By.CSS_SELECTOR, "span.kvMYJc")
                    rating_style = rating_element.get_attribute("style")
                    # Extract rating from width percentage
                    width_match = re.search(r'width:\s*(\d+)%', rating_style)
                    if width_match:
                        rating = int(width_match.group(1)) / 20  # Convert percentage to 5-star rating
                        review_data['rating'] = str(rating)
                    else:
                        review_data['rating'] = "No rating"
                except NoSuchElementException:
                    review_data['rating'] = "No rating"
                
                try:
                    # Review text
                    text_element = review_element.find_element(By.CSS_SELECTOR, "span.wiI7pd")
                    review_data['review_text'] = text_element.text
                except NoSuchElementException:
                    review_data['review_text'] = "No text"
                
                try:
                    # Review date
                    date_element = review_element.find_element(By.CSS_SELECTOR, "span.rsqaWe")
                    review_data['date'] = date_element.text
                except NoSuchElementException:
                    review_data['date'] = "No date"
                
                if review_data['review_text'] and review_data['review_text'] != "No text":
                    reviews.append(review_data)
                    
        except Exception as e:
            logger.error(f"Error parsing reviews: {e}")
        
        return reviews
    
    def scrape_reviews(self, google_maps_url: str, max_reviews: int = 100) -> Dict[str, any]:
        """
        Scrape reviews from a Google Maps business page.
        
        Args:
            google_maps_url: The Google Maps URL of the business
            max_reviews: Maximum number of reviews to scrape
            
        Returns:
            Dictionary containing business info and reviews
        """
        logger.info(f"Starting to scrape reviews from: {google_maps_url}")
        
        try:
            self.driver = self._setup_driver()
            self.driver.get(google_maps_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
            )
            
            # Extract business information
            business_info = self._extract_business_info()
            logger.info(f"Scraping reviews for: {business_info.get('name', 'Unknown Business')}")
            
            # Try to find and click on reviews tab/section
            try:
                reviews_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-value='Sort']"))
                )
                reviews_button.click()
                time.sleep(2)
            except TimeoutException:
                # Try alternative method to access reviews
                try:
                    reviews_element = self.driver.find_element(By.CSS_SELECTOR, "div[data-review-id]")
                except NoSuchElementException:
                    logger.warning("Could not find reviews section")
            
            # Scroll to load more reviews
            self._scroll_to_load_reviews(max_reviews)
            
            # Parse reviews
            reviews = self._parse_reviews()
            
            logger.info(f"Successfully scraped {len(reviews)} reviews")
            
            return {
                'business_info': business_info,
                'reviews': reviews,
                'total_scraped': len(reviews)
            }
            
        except Exception as e:
            logger.error(f"Error scraping reviews: {e}")
            return {
                'business_info': {},
                'reviews': [],
                'total_scraped': 0,
                'error': str(e)
            }
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_reviews_to_csv(self, reviews_data: Dict[str, any], filename: str) -> None:
        """Save scraped reviews to a CSV file."""
        if not reviews_data['reviews']:
            logger.warning("No reviews to save")
            return
        
        df = pd.DataFrame(reviews_data['reviews'])
        df['business_name'] = reviews_data['business_info'].get('name', 'Unknown')
        df['business_rating'] = reviews_data['business_info'].get('rating', 'No rating')
        
        df.to_csv(filename, index=False)
        logger.info(f"Saved {len(reviews_data['reviews'])} reviews to {filename}")