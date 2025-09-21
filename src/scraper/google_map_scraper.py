import time
import json
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import List, Dict, Optional
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleMapReviewScraper:
    """Google Map 評論爬蟲"""
    
    def __init__(self, headless: bool = True):
        """
        初始化爬蟲
        
        Args:
            headless: 是否使用無頭模式
        """
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """設置 Chrome WebDriver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def close_driver(self):
        """關閉 WebDriver"""
        if self.driver:
            self.driver.quit()
            
    def extract_place_id_from_url(self, url: str) -> Optional[str]:
        """從 Google Map URL 中提取 place_id"""
        # 匹配各種 Google Map URL 格式
        patterns = [
            r'place/[^/]+/data=.*?1s([^!]+)',  # 新格式
            r'place_id:([^&]+)',  # 直接包含 place_id
            r'ftid:([^&]+)',  # ftid 格式
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def parse_review_date(self, date_text: str) -> Optional[datetime]:
        """解析評論日期"""
        try:
            # 處理中文日期格式
            if "年前" in date_text:
                years = int(re.search(r'(\d+)年前', date_text).group(1))
                return datetime.now() - timedelta(days=years * 365)
            elif "個月前" in date_text:
                months = int(re.search(r'(\d+)個月前', date_text).group(1))
                return datetime.now() - timedelta(days=months * 30)
            elif "週前" in date_text:
                weeks = int(re.search(r'(\d+)週前', date_text).group(1))
                return datetime.now() - timedelta(weeks=weeks)
            elif "天前" in date_text:
                days = int(re.search(r'(\d+)天前', date_text).group(1))
                return datetime.now() - timedelta(days=days)
            elif "小時前" in date_text:
                hours = int(re.search(r'(\d+)小時前', date_text).group(1))
                return datetime.now() - timedelta(hours=hours)
            elif "分鐘前" in date_text:
                minutes = int(re.search(r'(\d+)分鐘前', date_text).group(1))
                return datetime.now() - timedelta(minutes=minutes)
            
            # 處理英文日期格式
            if "year" in date_text:
                years = int(re.search(r'(\d+)\s+year', date_text).group(1))
                return datetime.now() - timedelta(days=years * 365)
            elif "month" in date_text:
                months = int(re.search(r'(\d+)\s+month', date_text).group(1))
                return datetime.now() - timedelta(days=months * 30)
            elif "week" in date_text:
                weeks = int(re.search(r'(\d+)\s+week', date_text).group(1))
                return datetime.now() - timedelta(weeks=weeks)
            elif "day" in date_text:
                days = int(re.search(r'(\d+)\s+day', date_text).group(1))
                return datetime.now() - timedelta(days=days)
                
        except Exception as e:
            logger.warning(f"無法解析日期: {date_text}, 錯誤: {e}")
            
        return None
    
    def scroll_to_load_reviews(self, max_scrolls: int = 10):
        """滾動頁面載入更多評論"""
        # 找到評論容器
        try:
            reviews_container = self.driver.find_element(
                By.CSS_SELECTOR, 
                '[data-review-id], .m6QErb.DxyBCb.kA9KIf.dS8AEf'
            )
            
            for i in range(max_scrolls):
                # 滾動到容器底部
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", 
                    reviews_container
                )
                time.sleep(2)
                
                # 檢查是否有"查看更多評論"按鈕
                try:
                    more_button = self.driver.find_element(
                        By.CSS_SELECTOR, 
                        '[data-value="查看更多評論"], [data-value="See more reviews"]'
                    )
                    if more_button.is_displayed():
                        more_button.click()
                        time.sleep(2)
                except NoSuchElementException:
                    pass
                    
        except NoSuchElementException:
            logger.warning("找不到評論容器，使用頁面滾動")
            for i in range(max_scrolls):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
    
    def extract_reviews(self, max_reviews: int = 100, year_limit: int = 1) -> List[Dict]:
        """提取評論"""
        reviews = []
        cutoff_date = datetime.now() - timedelta(days=year_limit * 365)
        
        # 滾動載入更多評論
        self.scroll_to_load_reviews()
        
        # 查找所有評論元素
        review_elements = self.driver.find_elements(
            By.CSS_SELECTOR, 
            '.jftiEf, .MyEned, [data-review-id]'
        )
        
        logger.info(f"找到 {len(review_elements)} 個評論元素")
        
        for idx, review_element in enumerate(review_elements[:max_reviews]):
            try:
                review_data = {}
                
                # 提取評論者姓名
                try:
                    name_element = review_element.find_element(
                        By.CSS_SELECTOR, 
                        '.d4r55, .X43Kjb'
                    )
                    review_data['reviewer_name'] = name_element.text
                except NoSuchElementException:
                    review_data['reviewer_name'] = "匿名用戶"
                
                # 提取評分
                try:
                    rating_element = review_element.find_element(
                        By.CSS_SELECTOR, 
                        '[role="img"][aria-label*="星"], .kvMYJc'
                    )
                    rating_text = rating_element.get_attribute('aria-label')
                    rating_match = re.search(r'(\d+)', rating_text)
                    review_data['rating'] = int(rating_match.group(1)) if rating_match else None
                except NoSuchElementException:
                    review_data['rating'] = None
                
                # 提取評論日期
                try:
                    date_element = review_element.find_element(
                        By.CSS_SELECTOR, 
                        '.rsqaWe, .DU9Pgb'
                    )
                    date_text = date_element.text
                    review_date = self.parse_review_date(date_text)
                    
                    # 檢查是否在時間範圍內
                    if review_date and review_date < cutoff_date:
                        logger.info(f"評論日期 {review_date} 超出範圍，停止提取")
                        break
                        
                    review_data['date'] = review_date.isoformat() if review_date else None
                    review_data['date_text'] = date_text
                except NoSuchElementException:
                    review_data['date'] = None
                    review_data['date_text'] = ""
                
                # 提取評論內容
                try:
                    # 先嘗試點擊"更多"按鈕展開完整評論
                    try:
                        more_button = review_element.find_element(
                            By.CSS_SELECTOR, 
                            '.w8nwRe.kyuRq, [data-expandable-section]'
                        )
                        if more_button.is_displayed():
                            more_button.click()
                            time.sleep(0.5)
                    except NoSuchElementException:
                        pass
                    
                    content_element = review_element.find_element(
                        By.CSS_SELECTOR, 
                        '.wiI7pd, .MyEned'
                    )
                    review_data['content'] = content_element.text
                except NoSuchElementException:
                    review_data['content'] = ""
                
                # 提取照片數量（如果有）
                try:
                    photos = review_element.find_elements(
                        By.CSS_SELECTOR, 
                        '.KtCyie img, .EDblX img'
                    )
                    review_data['photo_count'] = len(photos)
                except NoSuchElementException:
                    review_data['photo_count'] = 0
                
                # 只添加有內容的評論
                if review_data.get('content') or review_data.get('rating'):
                    reviews.append(review_data)
                    logger.info(f"提取評論 {idx + 1}: {review_data['reviewer_name']}")
                
            except Exception as e:
                logger.warning(f"提取評論 {idx + 1} 時發生錯誤: {e}")
                continue
        
        logger.info(f"總共提取了 {len(reviews)} 條評論")
        return reviews
    
    def scrape_reviews(self, url: str, max_reviews: int = 100, year_limit: int = 1) -> List[Dict]:
        """
        爬取 Google Map 評論
        
        Args:
            url: Google Map 店家 URL
            max_reviews: 最大評論數量
            year_limit: 時間限制（年）
            
        Returns:
            評論列表
        """
        try:
            self.setup_driver()
            
            # 訪問 URL
            logger.info(f"正在訪問: {url}")
            self.driver.get(url)
            
            # 等待頁面載入
            time.sleep(5)
            
            # 嘗試點擊評論標籤
            try:
                reviews_tab = self.wait.until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR, 
                        '[data-tab-index="1"], .hh2c6.LAhh6b, button[data-value="評論"], button[data-value="Reviews"]'
                    ))
                )
                reviews_tab.click()
                time.sleep(3)
            except TimeoutException:
                logger.warning("無法找到評論標籤，嘗試滾動尋找評論")
            
            # 提取評論
            reviews = self.extract_reviews(max_reviews, year_limit)
            
            return reviews
            
        except Exception as e:
            logger.error(f"爬取評論時發生錯誤: {e}")
            return []
        finally:
            self.close_driver()
    
    def save_reviews_to_json(self, reviews: List[Dict], filename: str):
        """保存評論到 JSON 文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
        logger.info(f"評論已保存到: {filename}")

# 使用示例
if __name__ == "__main__":
    scraper = GoogleMapReviewScraper(headless=False)
    
    # 示例 URL（請替換為實際的 Google Map URL）
    url = "https://www.google.com/maps/place/店家名稱"
    
    reviews = scraper.scrape_reviews(url, max_reviews=50, year_limit=1)
    
    if reviews:
        scraper.save_reviews_to_json(reviews, "reviews.json")
        print(f"成功爬取 {len(reviews)} 條評論")
    else:
        print("未能爬取到評論")