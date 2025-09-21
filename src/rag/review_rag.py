import json
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ReviewRAG:
    """評論檢索增強生成系統"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", vector_db_path: str = None):
        """
        初始化 RAG 系統
        
        Args:
            model_name: 嵌入模型名稱
            vector_db_path: 向量數據庫保存路徑
        """
        self.model_name = model_name
        self.vector_db_path = vector_db_path or "data/vector_db"
        self.embedding_model = None
        self.index = None
        self.reviews_metadata = []
        self.dimension = None
        
        # 確保數據目錄存在
        os.makedirs(os.path.dirname(self.vector_db_path), exist_ok=True)
        
    def load_embedding_model(self):
        """載入嵌入模型"""
        if self.embedding_model is None:
            logger.info(f"載入嵌入模型: {self.model_name}")
            self.embedding_model = SentenceTransformer(self.model_name)
            self.dimension = self.embedding_model.get_sentence_embedding_dimension()
            logger.info(f"嵌入維度: {self.dimension}")
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        創建文本嵌入
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量數組
        """
        self.load_embedding_model()
        logger.info(f"正在創建 {len(texts)} 個文本的嵌入...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return embeddings
    
    def preprocess_review(self, review: Dict) -> str:
        """
        預處理評論，組合相關信息為可搜索的文本
        
        Args:
            review: 評論字典
            
        Returns:
            處理後的文本
        """
        parts = []
        
        # 添加評分信息
        if review.get('rating'):
            parts.append(f"評分: {review['rating']}星")
        
        # 添加評論內容
        if review.get('content'):
            parts.append(f"評論內容: {review['content']}")
        
        # 添加日期信息
        if review.get('date_text'):
            parts.append(f"評論時間: {review['date_text']}")
        
        # 添加評論者信息
        if review.get('reviewer_name'):
            parts.append(f"評論者: {review['reviewer_name']}")
        
        # 添加照片信息
        if review.get('photo_count', 0) > 0:
            parts.append(f"包含 {review['photo_count']} 張照片")
        
        return " | ".join(parts)
    
    def build_vector_database(self, reviews: List[Dict], save_path: str = None):
        """
        建立向量數據庫
        
        Args:
            reviews: 評論列表
            save_path: 保存路徑
        """
        if not reviews:
            raise ValueError("評論列表不能為空")
        
        # 預處理評論
        processed_texts = []
        valid_reviews = []
        
        for review in reviews:
            processed_text = self.preprocess_review(review)
            if processed_text.strip():  # 只處理非空文本
                processed_texts.append(processed_text)
                valid_reviews.append(review)
        
        if not processed_texts:
            raise ValueError("沒有有效的評論文本可以處理")
        
        logger.info(f"處理 {len(processed_texts)} 條有效評論")
        
        # 創建嵌入
        embeddings = self.create_embeddings(processed_texts)
        
        # 創建 FAISS 索引
        self.dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(self.dimension)  # 使用內積相似度
        
        # 標準化嵌入向量（為了使用餘弦相似度）
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))
        
        # 保存元數據
        self.reviews_metadata = []
        for i, review in enumerate(valid_reviews):
            metadata = {
                'index': i,
                'review': review,
                'processed_text': processed_texts[i],
                'embedding_created_at': datetime.now().isoformat()
            }
            self.reviews_metadata.append(metadata)
        
        logger.info(f"向量數據庫建立完成，包含 {self.index.ntotal} 條記錄")
        
        # 保存到磁盤
        if save_path:
            self.save_vector_database(save_path)
        else:
            self.save_vector_database(self.vector_db_path)
    
    def save_vector_database(self, save_path: str):
        """保存向量數據庫到磁盤"""
        try:
            # 保存 FAISS 索引
            faiss.write_index(self.index, f"{save_path}.faiss")
            
            # 保存元數據
            with open(f"{save_path}_metadata.pkl", 'wb') as f:
                pickle.dump({
                    'reviews_metadata': self.reviews_metadata,
                    'model_name': self.model_name,
                    'dimension': self.dimension,
                    'created_at': datetime.now().isoformat()
                }, f)
            
            logger.info(f"向量數據庫已保存到: {save_path}")
            
        except Exception as e:
            logger.error(f"保存向量數據庫時發生錯誤: {e}")
            raise
    
    def load_vector_database(self, load_path: str = None):
        """從磁盤載入向量數據庫"""
        load_path = load_path or self.vector_db_path
        
        try:
            # 載入 FAISS 索引
            if os.path.exists(f"{load_path}.faiss"):
                self.index = faiss.read_index(f"{load_path}.faiss")
                logger.info(f"載入 FAISS 索引，包含 {self.index.ntotal} 條記錄")
            else:
                raise FileNotFoundError(f"找不到索引檔案: {load_path}.faiss")
            
            # 載入元數據
            if os.path.exists(f"{load_path}_metadata.pkl"):
                with open(f"{load_path}_metadata.pkl", 'rb') as f:
                    metadata = pickle.load(f)
                    self.reviews_metadata = metadata['reviews_metadata']
                    self.model_name = metadata['model_name']
                    self.dimension = metadata['dimension']
                    logger.info(f"載入元數據，包含 {len(self.reviews_metadata)} 條記錄")
            else:
                raise FileNotFoundError(f"找不到元數據檔案: {load_path}_metadata.pkl")
            
            # 載入嵌入模型
            self.load_embedding_model()
            
            logger.info("向量數據庫載入完成")
            
        except Exception as e:
            logger.error(f"載入向量數據庫時發生錯誤: {e}")
            raise
    
    def search_similar_reviews(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        搜索相似的評論
        
        Args:
            query: 查詢文本
            top_k: 返回前 k 個最相似的結果
            
        Returns:
            相似評論列表
        """
        if self.index is None:
            raise ValueError("向量數據庫尚未建立或載入")
        
        # 創建查詢嵌入
        query_embedding = self.create_embeddings([query])
        faiss.normalize_L2(query_embedding)
        
        # 搜索
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # 整理結果
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.reviews_metadata):
                result = {
                    'rank': i + 1,
                    'score': float(score),
                    'review': self.reviews_metadata[idx]['review'],
                    'processed_text': self.reviews_metadata[idx]['processed_text']
                }
                results.append(result)
        
        logger.info(f"找到 {len(results)} 個相似評論")
        return results
    
    def get_context_for_llm(self, query: str, top_k: int = 5) -> str:
        """
        為 LLM 準備上下文
        
        Args:
            query: 用戶查詢
            top_k: 檢索的評論數量
            
        Returns:
            格式化的上下文字符串
        """
        similar_reviews = self.search_similar_reviews(query, top_k)
        
        if not similar_reviews:
            return "沒有找到相關的評論。"
        
        context_parts = ["以下是與您的問題最相關的評論：\n"]
        
        for result in similar_reviews:
            review = result['review']
            context_parts.append(f"評論 {result['rank']}:")
            context_parts.append(f"評分: {review.get('rating', '未知')}星")
            context_parts.append(f"評論內容: {review.get('content', '無內容')}")
            context_parts.append(f"評論時間: {review.get('date_text', '未知')}")
            context_parts.append(f"評論者: {review.get('reviewer_name', '匿名')}")
            if review.get('photo_count', 0) > 0:
                context_parts.append(f"附有 {review['photo_count']} 張照片")
            context_parts.append(f"相似度分數: {result['score']:.3f}")
            context_parts.append("---")
        
        return "\n".join(context_parts)
    
    def get_database_stats(self) -> Dict:
        """獲取數據庫統計信息"""
        if not self.reviews_metadata:
            return {"message": "數據庫為空"}
        
        # 統計評分分佈
        ratings = [r['review'].get('rating') for r in self.reviews_metadata if r['review'].get('rating')]
        rating_distribution = {}
        for rating in ratings:
            rating_distribution[rating] = rating_distribution.get(rating, 0) + 1
        
        # 統計日期範圍
        dates = [r['review'].get('date') for r in self.reviews_metadata if r['review'].get('date')]
        
        stats = {
            'total_reviews': len(self.reviews_metadata),
            'reviews_with_rating': len(ratings),
            'rating_distribution': rating_distribution,
            'average_rating': sum(ratings) / len(ratings) if ratings else None,
            'reviews_with_dates': len(dates),
            'date_range': {
                'earliest': min(dates) if dates else None,
                'latest': max(dates) if dates else None
            },
            'model_name': self.model_name,
            'vector_dimension': self.dimension
        }
        
        return stats

# 使用示例
if __name__ == "__main__":
    # 載入評論數據
    with open('reviews.json', 'r', encoding='utf-8') as f:
        reviews = json.load(f)
    
    # 建立 RAG 系統
    rag = ReviewRAG()
    rag.build_vector_database(reviews)
    
    # 測試檢索
    query = "食物好吃嗎？"
    context = rag.get_context_for_llm(query)
    print(context)