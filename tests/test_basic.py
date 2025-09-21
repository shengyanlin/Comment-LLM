"""
Basic tests for Comment-LLM components.

These tests validate core functionality without requiring
external API calls or web scraping.
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from comment_llm.rag_system import RAGSystem
from comment_llm.app import CommentLLM


class TestRAGSystem(unittest.TestCase):
    """Test the RAG system functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.rag_system = RAGSystem(persist_directory=self.temp_dir)
    
    def test_initialization(self):
        """Test RAG system initialization."""
        self.assertIsNotNone(self.rag_system.client)
        self.assertIsNotNone(self.rag_system.collection)
        self.assertIsNotNone(self.rag_system.embedding_model)
    
    def test_add_and_search_reviews(self):
        """Test adding reviews and searching."""
        # Sample review data
        sample_reviews = {
            'business_info': {
                'name': 'Test Restaurant',
                'rating': '4.5',
                'reviews_count': '100'
            },
            'reviews': [
                {
                    'reviewer_name': 'John Doe',
                    'rating': '5',
                    'date': '2 weeks ago',
                    'review_text': 'Great food and excellent service. The pasta was amazing!'
                },
                {
                    'reviewer_name': 'Jane Smith',
                    'rating': '4',
                    'date': '1 week ago',
                    'review_text': 'Good atmosphere but the service was a bit slow.'
                }
            ]
        }
        
        # Add reviews
        self.rag_system.add_reviews(sample_reviews)
        
        # Search for relevant reviews
        results = self.rag_system.search_reviews("food quality", n_results=2)
        
        self.assertGreater(len(results), 0)
        self.assertIn('document', results[0])
        self.assertIn('metadata', results[0])
        self.assertIn('similarity_score', results[0])
    
    def test_business_summary(self):
        """Test business summary functionality."""
        # Add sample reviews first
        sample_reviews = {
            'business_info': {
                'name': 'Test Cafe',
                'rating': '4.2',
                'reviews_count': '50'
            },
            'reviews': [
                {
                    'reviewer_name': 'Alice',
                    'rating': '5',
                    'date': '1 day ago',
                    'review_text': 'Best coffee in town!'
                }
            ]
        }
        
        self.rag_system.add_reviews(sample_reviews)
        
        # Get business summary
        summary = self.rag_system.get_business_summary('Test Cafe')
        
        self.assertEqual(summary['business_name'], 'Test Cafe')
        self.assertEqual(summary['total_reviews'], 1)
    
    def test_list_businesses(self):
        """Test listing businesses."""
        # Initially should be empty
        businesses = self.rag_system.list_businesses()
        self.assertEqual(len(businesses), 0)
        
        # Add a business
        sample_reviews = {
            'business_info': {
                'name': 'Test Shop',
                'rating': '4.0'
            },
            'reviews': [
                {
                    'reviewer_name': 'Bob',
                    'rating': '4',
                    'review_text': 'Good shop'
                }
            ]
        }
        
        self.rag_system.add_reviews(sample_reviews)
        
        # Should now have one business
        businesses = self.rag_system.list_businesses()
        self.assertEqual(len(businesses), 1)
        self.assertIn('Test Shop', businesses)


class TestCommentLLMApp(unittest.TestCase):
    """Test the main Comment-LLM application."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    @patch('comment_llm.app.LLMClient')
    def test_app_initialization_without_api_key(self, mock_llm_client):
        """Test app initialization without OpenAI API key."""
        # Mock environment to not have API key
        with patch.dict(os.environ, {}, clear=True):
            app = CommentLLM(
                openai_api_key=None,
                chroma_persist_directory=self.temp_dir
            )
            
            self.assertIsNotNone(app.rag_system)
            self.assertIsNone(app.llm_client)
    
    def test_app_initialization_with_api_key(self):
        """Test app initialization with API key."""
        try:
            app = CommentLLM(
                openai_api_key="test-key",
                chroma_persist_directory=self.temp_dir
            )
            
            self.assertIsNotNone(app.rag_system)
            self.assertIsNotNone(app.llm_client)
        except Exception as e:
            # This might fail due to invalid API key, which is expected
            self.assertIn("api", str(e).lower())
    
    def test_list_businesses_empty(self):
        """Test listing businesses when database is empty."""
        app = CommentLLM(
            openai_api_key=None,
            chroma_persist_directory=self.temp_dir
        )
        
        businesses = app.list_businesses()
        self.assertEqual(len(businesses), 0)
    
    def test_database_info(self):
        """Test getting database information."""
        app = CommentLLM(
            openai_api_key=None,
            chroma_persist_directory=self.temp_dir
        )
        
        info = app.get_database_info()
        
        self.assertIn('collection_name', info)
        self.assertIn('total_reviews', info)
        self.assertIn('total_businesses', info)
        self.assertIn('businesses', info)


if __name__ == '__main__':
    unittest.main()