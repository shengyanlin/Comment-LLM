#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google Map 評論分析系統
主程式入口
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional

# 添加項目根目錄到 Python 路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.scraper.google_map_scraper import GoogleMapReviewScraper
from src.rag.review_rag import ReviewRAG
from src.llm.question_answering import LLMQuestionAnswering

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CommentLLMApp:
    """Google Map 評論分析應用程式主類"""
    
    def __init__(self, config_path: str = None):
        """
        初始化應用程式
        
        Args:
            config_path: 配置文件路徑
        """
        self.config = self.load_config(config_path)
        self.scraper = None
        self.rag = None
        self.llm = None
        self.current_reviews = []
        self.current_restaurant_name = ""
        
    def load_config(self, config_path: str = None) -> Dict:
        """載入配置"""
        default_config = {
            "scraper": {
                "headless": True,
                "max_reviews": 100,
                "year_limit": 1
            },
            "rag": {
                "model_name": "all-MiniLM-L6-v2",
                "vector_db_path": "data/vector_db",
                "top_k": 5
            },
            "llm": {
                "model_name": "gpt-3.5-turbo",
                "temperature": 0.7
            },
            "data": {
                "reviews_dir": "data/reviews",
                "vector_db_dir": "data/vector_db"
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    custom_config = json.load(f)
                # 合併配置
                for key, value in custom_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
            except Exception as e:
                logger.warning(f"載入配置檔案失敗: {e}，使用預設配置")
        
        return default_config
    
    def initialize_components(self):
        """初始化所有組件"""
        logger.info("正在初始化系統組件...")
        
        # 初始化爬蟲
        self.scraper = GoogleMapReviewScraper(
            headless=self.config["scraper"]["headless"]
        )
        
        # 初始化 RAG 系統
        self.rag = ReviewRAG(
            model_name=self.config["rag"]["model_name"],
            vector_db_path=self.config["rag"]["vector_db_path"]
        )
        
        # 初始化 LLM
        self.llm = LLMQuestionAnswering(
            model_name=self.config["llm"]["model_name"]
        )
        
        logger.info("系統組件初始化完成")
    
    def scrape_restaurant_reviews(self, url: str, restaurant_name: str = None) -> bool:
        """
        爬取餐廳評論
        
        Args:
            url: Google Map 餐廳 URL
            restaurant_name: 餐廳名稱（可選）
            
        Returns:
            是否成功
        """
        try:
            logger.info(f"開始爬取餐廳評論: {url}")
            
            # 爬取評論
            reviews = self.scraper.scrape_reviews(
                url=url,
                max_reviews=self.config["scraper"]["max_reviews"],
                year_limit=self.config["scraper"]["year_limit"]
            )
            
            if not reviews:
                logger.error("未能爬取到任何評論")
                return False
            
            self.current_reviews = reviews
            self.current_restaurant_name = restaurant_name or "未知餐廳"
            
            # 保存評論到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            reviews_filename = f"reviews_{timestamp}.json"
            reviews_filepath = os.path.join(
                self.config["data"]["reviews_dir"], 
                reviews_filename
            )
            
            # 確保目錄存在
            os.makedirs(os.path.dirname(reviews_filepath), exist_ok=True)
            
            with open(reviews_filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    "restaurant_name": self.current_restaurant_name,
                    "url": url,
                    "scraped_at": datetime.now().isoformat(),
                    "total_reviews": len(reviews),
                    "reviews": reviews
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功爬取 {len(reviews)} 條評論，已保存到: {reviews_filepath}")
            return True
            
        except Exception as e:
            logger.error(f"爬取評論時發生錯誤: {e}")
            return False
    
    def build_knowledge_base(self) -> bool:
        """建立知識庫"""
        try:
            if not self.current_reviews:
                logger.error("沒有評論數據可以建立知識庫")
                return False
            
            logger.info("正在建立知識庫...")
            
            # 確保目錄存在
            os.makedirs(os.path.dirname(self.config["rag"]["vector_db_path"]), exist_ok=True)
            
            # 建立向量數據庫
            self.rag.build_vector_database(
                self.current_reviews,
                self.config["rag"]["vector_db_path"]
            )
            
            # 顯示統計信息
            stats = self.rag.get_database_stats()
            logger.info(f"知識庫建立完成: {stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"建立知識庫時發生錯誤: {e}")
            return False
    
    def answer_question(self, question: str) -> Dict:
        """
        回答問題
        
        Args:
            question: 用戶問題
            
        Returns:
            答案結果
        """
        try:
            if not self.rag.index:
                logger.error("知識庫尚未建立")
                return {
                    "success": False,
                    "error": "知識庫尚未建立，請先爬取評論並建立知識庫"
                }
            
            logger.info(f"正在回答問題: {question}")
            
            # 檢索相關評論
            context = self.rag.get_context_for_llm(
                question, 
                self.config["rag"]["top_k"]
            )
            
            # 生成答案
            result = self.llm.generate_answer(
                question=question,
                context=context,
                temperature=self.config["llm"]["temperature"]
            )
            
            # 添加額外信息
            result["restaurant_name"] = self.current_restaurant_name
            result["total_reviews"] = len(self.current_reviews)
            
            return result
            
        except Exception as e:
            logger.error(f"回答問題時發生錯誤: {e}")
            return {
                "success": False,
                "error": str(e),
                "question": question
            }
    
    def interactive_mode(self):
        """互動模式"""
        print("=" * 60)
        print("🍽️  Google Map 評論分析系統")
        print("=" * 60)
        print()
        
        # 步驟 1: 輸入餐廳 URL
        while True:
            url = input("請輸入 Google Map 餐廳 URL: ").strip()
            if url:
                break
            print("URL 不能為空，請重新輸入")
        
        restaurant_name = input("請輸入餐廳名稱（可選）: ").strip()
        
        print("\n🕷️ 正在爬取評論...")
        if not self.scrape_restaurant_reviews(url, restaurant_name):
            print("❌ 爬取評論失敗，程式結束")
            return
        
        print(f"✅ 成功爬取 {len(self.current_reviews)} 條評論")
        
        # 步驟 2: 建立知識庫
        print("\n🧠 正在建立知識庫...")
        if not self.build_knowledge_base():
            print("❌ 建立知識庫失敗，程式結束")
            return
        
        print("✅ 知識庫建立完成")
        
        # 步驟 3: 互動問答
        print(f"\n💬 現在可以開始提問關於 '{self.current_restaurant_name}' 的問題")
        print("輸入 'quit' 或 'exit' 退出程式")
        print("輸入 'stats' 查看數據統計")
        print("輸入 'summary' 生成評論摘要")
        print("=" * 60)
        
        while True:
            try:
                question = input("\n❓ 請輸入您的問題: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['quit', 'exit', '退出']:
                    print("👋 感謝使用，再見！")
                    break
                
                if question.lower() == 'stats':
                    stats = self.rag.get_database_stats()
                    print("\n📊 數據統計:")
                    print(f"總評論數: {stats['total_reviews']}")
                    print(f"平均評分: {stats.get('average_rating', 'N/A')}")
                    print(f"評分分佈: {stats.get('rating_distribution', {})}")
                    continue
                
                if question.lower() == 'summary':
                    print("\n📝 正在生成評論摘要...")
                    context = self.rag.get_context_for_llm("整體評價", 10)
                    result = self.llm.generate_summary(context)
                    if result["success"]:
                        print(f"\n📋 評論摘要:\n{result['answer']}")
                    else:
                        print(f"❌ 摘要生成失敗: {result.get('error', '未知錯誤')}")
                    continue
                
                print("\n🤔 正在思考...")
                result = self.answer_question(question)
                
                if result["success"]:
                    print(f"\n🤖 回答:\n{result['answer']}")
                    if result.get("usage"):
                        print(f"\n💰 Token 使用量: {result['usage']['total_tokens']}")
                else:
                    print(f"\n❌ 回答失敗: {result.get('error', '未知錯誤')}")
                
            except KeyboardInterrupt:
                print("\n\n👋 程式被中斷，再見！")
                break
            except Exception as e:
                print(f"\n❌ 發生錯誤: {e}")
    
    def load_existing_reviews(self, reviews_file: str) -> bool:
        """載入現有的評論文件"""
        try:
            with open(reviews_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'reviews' in data:
                self.current_reviews = data['reviews']
                self.current_restaurant_name = data.get('restaurant_name', '未知餐廳')
            else:
                self.current_reviews = data
                self.current_restaurant_name = "未知餐廳"
            
            logger.info(f"成功載入 {len(self.current_reviews)} 條評論")
            return True
            
        except Exception as e:
            logger.error(f"載入評論文件失敗: {e}")
            return False

def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(description="Google Map 評論分析系統")
    parser.add_argument("--config", type=str, help="配置檔案路徑")
    parser.add_argument("--url", type=str, help="Google Map 餐廳 URL")
    parser.add_argument("--reviews", type=str, help="現有評論檔案路徑")
    parser.add_argument("--question", type=str, help="直接提問")
    parser.add_argument("--batch", action="store_true", help="批次模式")
    
    args = parser.parse_args()
    
    # 初始化應用程式
    app = CommentLLMApp(args.config)
    app.initialize_components()
    
    try:
        if args.reviews:
            # 載入現有評論
            if app.load_existing_reviews(args.reviews):
                if app.build_knowledge_base():
                    if args.question:
                        result = app.answer_question(args.question)
                        if result["success"]:
                            print(result["answer"])
                        else:
                            print(f"錯誤: {result.get('error')}")
                    else:
                        app.interactive_mode()
        elif args.url:
            # 爬取新評論
            if app.scrape_restaurant_reviews(args.url):
                if app.build_knowledge_base():
                    if args.question:
                        result = app.answer_question(args.question)
                        if result["success"]:
                            print(result["answer"])
                        else:
                            print(f"錯誤: {result.get('error')}")
                    else:
                        app.interactive_mode()
        else:
            # 互動模式
            app.interactive_mode()
            
    except KeyboardInterrupt:
        print("\n程式被用戶中斷")
    except Exception as e:
        logger.error(f"程式執行錯誤: {e}")
        print(f"程式執行錯誤: {e}")

if __name__ == "__main__":
    main()