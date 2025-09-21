#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試腳本 - 檢查所有模組是否能正常導入
"""

import sys
import os

# 添加項目根目錄到 Python 路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """測試所有模組導入"""
    try:
        print("🔍 測試模組導入...")
        
        # 測試爬蟲模組
        print("- 測試爬蟲模組...")
        from src.scraper.google_map_scraper import GoogleMapReviewScraper
        print("  ✅ GoogleMapReviewScraper 導入成功")
        
        # 測試 RAG 模組
        print("- 測試 RAG 模組...")
        from src.rag.review_rag import ReviewRAG
        print("  ✅ ReviewRAG 導入成功")
        
        # 測試 LLM 模組
        print("- 測試 LLM 模組...")
        from src.llm.question_answering import LLMQuestionAnswering
        print("  ✅ LLMQuestionAnswering 導入成功")
        
        print("\n🎉 所有模組導入測試通過！")
        return True
        
    except Exception as e:
        print(f"\n❌ 模組導入失敗: {e}")
        return False

def test_basic_functionality():
    """測試基本功能"""
    try:
        print("\n🔧 測試基本功能...")
        
        # 測試 RAG 系統
        from src.rag.review_rag import ReviewRAG
        rag = ReviewRAG()
        print("  ✅ RAG 系統初始化成功")
        
        # 測試 LLM 系統
        from src.llm.question_answering import LLMQuestionAnswering
        llm = LLMQuestionAnswering()
        print("  ✅ LLM 系統初始化成功")
        
        # 測試爬蟲系統
        from src.scraper.google_map_scraper import GoogleMapReviewScraper
        scraper = GoogleMapReviewScraper()
        print("  ✅ 爬蟲系統初始化成功")
        
        print("\n🎉 基本功能測試通過！")
        return True
        
    except Exception as e:
        print(f"\n❌ 基本功能測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 Comment-LLM 系統測試")
    print("=" * 50)
    
    # 測試導入
    import_success = test_imports()
    
    if import_success:
        # 測試基本功能
        func_success = test_basic_functionality()
        
        if func_success:
            print("\n✨ 所有測試通過！系統準備就緒。")
            print("\n使用方法:")
            print("python main.py")
        else:
            print("\n⚠️  基本功能測試失敗，請檢查配置。")
    else:
        print("\n⚠️  模組導入失敗，請檢查依賴套件。")