import openai
from openai import OpenAI
import os
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMQuestionAnswering:
    """大語言模型問答系統"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", api_key: str = None):
        """
        初始化 LLM 問答系統
        
        Args:
            model_name: 模型名稱
            api_key: OpenAI API 密鑰
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            logger.warning("未提供 OpenAI API 密鑰，請設置 OPENAI_API_KEY 環境變數")
        
        # 設置 OpenAI 客戶端 (新版本)
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def create_system_prompt(self) -> str:
        """創建系統提示詞"""
        return """你是一個專業的餐廳評論分析助手。你的任務是基於提供的 Google Map 評論數據來回答用戶的問題。

請遵循以下指導原則：
1. 只基於提供的評論數據來回答問題，不要編造信息
2. 如果評論數據不足以回答問題，請誠實說明
3. 回答時要具體引用相關的評論內容
4. 分析時要考慮評論的時間、評分和內容
5. 提供平衡和客觀的分析
6. 如果用戶問題不清楚，請要求澄清
7. 使用繁體中文回答

回答格式建議：
- 首先總結相關評論的整體情況
- 然後分點說明具體發現
- 最後提供基於評論的結論或建議
- 適當引用具體的評論內容作為佐證"""

    def create_user_prompt(self, question: str, context: str) -> str:
        """
        創建用戶提示詞
        
        Args:
            question: 用戶問題
            context: RAG 檢索到的相關評論
            
        Returns:
            格式化的用戶提示詞
        """
        return f"""基於以下的餐廳評論數據，請回答我的問題：

評論數據：
{context}

用戶問題：
{question}

請基於上述評論數據來回答問題，並在回答中引用相關的評論內容。"""

    def generate_answer(self, question: str, context: str, temperature: float = 0.7) -> Dict[str, Any]:
        """
        生成答案
        
        Args:
            question: 用戶問題
            context: RAG 檢索到的相關評論
            temperature: 生成溫度
            
        Returns:
            包含答案和元數據的字典
        """
        try:
            if not self.client:
                return {
                    "answer": "錯誤：未設置 OpenAI API 密鑰。請設置 OPENAI_API_KEY 環境變數。",
                    "success": False,
                    "error": "Missing API key"
                }
            
            # 準備訊息
            messages = [
                {"role": "system", "content": self.create_system_prompt()},
                {"role": "user", "content": self.create_user_prompt(question, context)}
            ]
            
            # 調用 OpenAI API (新版本)
            logger.info(f"正在調用 {self.model_name} 生成答案...")
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=1500,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            answer = response.choices[0].message.content.strip()
            
            result = {
                "answer": answer,
                "success": True,
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "created_at": datetime.now().isoformat(),
                "question": question,
                "context_length": len(context)
            }
            
            logger.info(f"成功生成答案，使用了 {response.usage.total_tokens} 個 tokens")
            return result
            
        except Exception as e:
            logger.error(f"生成答案時發生錯誤: {e}")
            return {
                "answer": f"生成答案時發生錯誤: {str(e)}",
                "success": False,
                "error": str(e),
                "question": question
            }
    
    def generate_answer_with_ollama(self, question: str, context: str, model_name: str = "llama2") -> Dict[str, Any]:
        """
        使用 Ollama 本地模型生成答案（可選方案）
        
        Args:
            question: 用戶問題
            context: RAG 檢索到的相關評論
            model_name: Ollama 模型名稱
            
        Returns:
            包含答案和元數據的字典
        """
        try:
            import requests
            
            # Ollama API 端點
            url = "http://localhost:11434/api/generate"
            
            prompt = f"""系統：{self.create_system_prompt()}

用戶：{self.create_user_prompt(question, context)}"""
            
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }
            
            logger.info(f"正在調用 Ollama {model_name} 生成答案...")
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result_data = response.json()
            answer = result_data.get("response", "").strip()
            
            result = {
                "answer": answer,
                "success": True,
                "model": f"ollama/{model_name}",
                "created_at": datetime.now().isoformat(),
                "question": question,
                "context_length": len(context)
            }
            
            logger.info("成功使用 Ollama 生成答案")
            return result
            
        except Exception as e:
            logger.error(f"使用 Ollama 生成答案時發生錯誤: {e}")
            return {
                "answer": f"使用 Ollama 生成答案時發生錯誤: {str(e)}",
                "success": False,
                "error": str(e),
                "question": question
            }
    
    def analyze_sentiment(self, reviews_context: str) -> Dict[str, Any]:
        """
        分析評論情感
        
        Args:
            reviews_context: 評論上下文
            
        Returns:
            情感分析結果
        """
        sentiment_prompt = """請分析以下評論的整體情感傾向，並提供：
1. 整體情感分數（1-10，1最負面，10最正面）
2. 正面評論的主要內容
3. 負面評論的主要內容
4. 中性評論的主要內容
5. 總體建議

評論數據：
""" + reviews_context
        
        return self.generate_answer("請進行情感分析", sentiment_prompt)
    
    def generate_summary(self, reviews_context: str) -> Dict[str, Any]:
        """
        生成評論摘要
        
        Args:
            reviews_context: 評論上下文
            
        Returns:
            摘要結果
        """
        summary_prompt = """請為以下評論生成一個全面的摘要，包括：
1. 餐廳的整體評價
2. 食物品質和口味
3. 服務品質
4. 環境和氛圍
5. 價格合理性
6. 顧客推薦的熱門菜品
7. 需要改進的地方

評論數據：
""" + reviews_context
        
        return self.generate_answer("請生成評論摘要", summary_prompt)

# 使用示例
if __name__ == "__main__":
    # 設置 API 密鑰
    llm = LLMQuestionAnswering()
    
    # 示例評論上下文
    context = """
    評論 1:
    評分: 5星
    評論內容: 食物很好吃，服務態度很好，環境也很舒適
    評論時間: 1個月前
    
    評論 2:
    評分: 3星
    評論內容: 食物普通，等待時間太長
    評論時間: 2週前
    """
    
    # 示例問題
    question = "這家餐廳的食物品質如何？"
    
    # 生成答案
    result = llm.generate_answer(question, context)
    print(result["answer"])