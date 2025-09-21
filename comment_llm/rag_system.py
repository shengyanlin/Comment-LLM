"""
RAG (Retrieval-Augmented Generation) System

This module provides functionality to store and retrieve relevant review
information using vector embeddings and similarity search.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class RAGSystem:
    """
    A RAG system for storing and retrieving review information using vector embeddings.
    """
    
    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "reviews"):
        """
        Initialize the RAG system.
        
        Args:
            persist_directory: Directory to persist the vector database
            collection_name: Name of the collection to store reviews
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self._setup_chroma_db()
        
    def _setup_chroma_db(self) -> None:
        """Set up ChromaDB client and collection."""
        try:
            # Create persist directory if it doesn't exist
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"ChromaDB collection '{self.collection_name}' initialized")
            
        except Exception as e:
            logger.error(f"Error setting up ChromaDB: {e}")
            raise
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        try:
            embeddings = self.embedding_model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def add_reviews(self, reviews_data: Dict[str, Any]) -> None:
        """
        Add reviews to the vector database.
        
        Args:
            reviews_data: Dictionary containing business info and reviews
        """
        try:
            business_info = reviews_data.get('business_info', {})
            reviews = reviews_data.get('reviews', [])
            
            if not reviews:
                logger.warning("No reviews to add to the database")
                return
            
            documents = []
            metadatas = []
            ids = []
            
            business_name = business_info.get('name', 'Unknown Business')
            business_rating = business_info.get('rating', 'No rating')
            
            for i, review in enumerate(reviews):
                # Create document text combining review text with context
                doc_text = f"Review for {business_name}: {review.get('review_text', '')}"
                documents.append(doc_text)
                
                # Create metadata
                metadata = {
                    'business_name': business_name,
                    'business_rating': business_rating,
                    'reviewer_name': review.get('reviewer_name', 'Anonymous'),
                    'rating': review.get('rating', 'No rating'),
                    'date': review.get('date', 'No date'),
                    'review_text': review.get('review_text', ''),
                    'added_timestamp': datetime.now().isoformat()
                }
                metadatas.append(metadata)
                
                # Create unique ID
                review_id = f"{business_name}_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                ids.append(review_id)
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(documents)} reviews...")
            embeddings = self._generate_embeddings(documents)
            
            # Add to collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully added {len(reviews)} reviews to the vector database")
            
        except Exception as e:
            logger.error(f"Error adding reviews to database: {e}")
            raise
    
    def search_reviews(self, query: str, n_results: int = 5, business_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant reviews based on a query.
        
        Args:
            query: The search query
            n_results: Number of results to return
            business_name: Optional filter by business name
            
        Returns:
            List of relevant review documents with metadata
        """
        try:
            # Generate embedding for the query
            query_embedding = self._generate_embeddings([query])[0]
            
            # Prepare where clause for filtering
            where_clause = None
            if business_name:
                where_clause = {"business_name": {"$eq": business_name}}
            
            # Search in the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} relevant reviews for query: '{query}'")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching reviews: {e}")
            return []
    
    def get_business_summary(self, business_name: str) -> Dict[str, Any]:
        """
        Get a summary of all reviews for a specific business.
        
        Args:
            business_name: Name of the business
            
        Returns:
            Dictionary containing business summary statistics
        """
        try:
            # Get all reviews for the business
            results = self.collection.get(
                where={"business_name": {"$eq": business_name}},
                include=['metadatas']
            )
            
            if not results['metadatas']:
                return {
                    'business_name': business_name,
                    'total_reviews': 0,
                    'error': 'No reviews found for this business'
                }
            
            metadatas = results['metadatas']
            
            # Calculate statistics
            total_reviews = len(metadatas)
            ratings = []
            
            for metadata in metadatas:
                rating_str = metadata.get('rating', '0')
                try:
                    if rating_str != 'No rating':
                        ratings.append(float(rating_str))
                except ValueError:
                    continue
            
            avg_rating = np.mean(ratings) if ratings else 0
            
            summary = {
                'business_name': business_name,
                'total_reviews': total_reviews,
                'average_rating': round(avg_rating, 2) if avg_rating else 'No ratings available',
                'business_rating': metadatas[0].get('business_rating', 'No rating') if metadatas else 'No rating'
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting business summary: {e}")
            return {
                'business_name': business_name,
                'total_reviews': 0,
                'error': str(e)
            }
    
    def list_businesses(self) -> List[str]:
        """
        List all businesses in the database.
        
        Returns:
            List of business names
        """
        try:
            # Get all documents with metadata
            results = self.collection.get(include=['metadatas'])
            
            if not results['metadatas']:
                return []
            
            # Extract unique business names
            business_names = set()
            for metadata in results['metadatas']:
                business_name = metadata.get('business_name')
                if business_name:
                    business_names.add(business_name)
            
            return sorted(list(business_names))
            
        except Exception as e:
            logger.error(f"Error listing businesses: {e}")
            return []
    
    def delete_business_reviews(self, business_name: str) -> bool:
        """
        Delete all reviews for a specific business.
        
        Args:
            business_name: Name of the business to delete reviews for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all IDs for the business
            results = self.collection.get(
                where={"business_name": {"$eq": business_name}},
                include=['ids']
            )
            
            if not results['ids']:
                logger.warning(f"No reviews found for business: {business_name}")
                return False
            
            # Delete the reviews
            self.collection.delete(ids=results['ids'])
            
            logger.info(f"Deleted {len(results['ids'])} reviews for business: {business_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting business reviews: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the current collection.
        
        Returns:
            Dictionary containing collection statistics
        """
        try:
            count = self.collection.count()
            businesses = self.list_businesses()
            
            return {
                'collection_name': self.collection_name,
                'total_reviews': count,
                'total_businesses': len(businesses),
                'businesses': businesses
            }
            
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {
                'collection_name': self.collection_name,
                'total_reviews': 0,
                'total_businesses': 0,
                'businesses': [],
                'error': str(e)
            }