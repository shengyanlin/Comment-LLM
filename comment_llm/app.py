"""
Main Comment-LLM Application

This module provides the main application class that coordinates
the scraping, RAG system, and LLM components.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from .scraper import GoogleMapsScraper
from .rag_system import RAGSystem
from .llm_client import LLMClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class CommentLLM:
    """
    Main application class that coordinates scraping, RAG, and LLM functionality.
    """
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 chroma_persist_directory: Optional[str] = None,
                 headless_browser: bool = True):
        """
        Initialize the Comment-LLM application.
        
        Args:
            openai_api_key: OpenAI API key (if None, will try to get from environment)
            chroma_persist_directory: Directory for ChromaDB persistence
            headless_browser: Whether to run browser in headless mode
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.chroma_persist_directory = chroma_persist_directory or os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
        self.headless_browser = headless_browser
        
        # Initialize components
        self.scraper = None
        self.rag_system = None
        self.llm_client = None
        
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize all components of the system."""
        try:
            # Initialize RAG system
            self.rag_system = RAGSystem(persist_directory=self.chroma_persist_directory)
            logger.info("RAG system initialized successfully")
            
            # Initialize LLM client
            if self.openai_api_key:
                self.llm_client = LLMClient(api_key=self.openai_api_key)
                logger.info("LLM client initialized successfully")
            else:
                logger.warning("OpenAI API key not provided. LLM functionality will be limited.")
            
            # Scraper will be initialized when needed
            logger.info("Comment-LLM application initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def scrape_and_store_reviews(self, 
                                google_maps_url: str, 
                                max_reviews: int = 100,
                                save_csv: bool = False,
                                csv_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape reviews from Google Maps and store them in the RAG system.
        
        Args:
            google_maps_url: Google Maps URL of the business
            max_reviews: Maximum number of reviews to scrape
            save_csv: Whether to save reviews to CSV
            csv_filename: CSV filename (if None, auto-generated)
            
        Returns:
            Dictionary containing scraping results
        """
        try:
            # Initialize scraper if not already done
            if not self.scraper:
                self.scraper = GoogleMapsScraper(
                    headless=self.headless_browser,
                    chromedriver_path=os.getenv("CHROMEDRIVER_PATH")
                )
            
            logger.info(f"Starting to scrape reviews from: {google_maps_url}")
            
            # Scrape reviews
            reviews_data = self.scraper.scrape_reviews(google_maps_url, max_reviews)
            
            if reviews_data.get('error'):
                return {
                    'success': False,
                    'error': reviews_data['error'],
                    'reviews_scraped': 0
                }
            
            # Store in RAG system
            if reviews_data['reviews']:
                self.rag_system.add_reviews(reviews_data)
                logger.info(f"Stored {len(reviews_data['reviews'])} reviews in RAG system")
            
            # Save to CSV if requested
            if save_csv and reviews_data['reviews']:
                if not csv_filename:
                    business_name = reviews_data['business_info'].get('name', 'business')
                    safe_name = "".join(c for c in business_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    csv_filename = f"{safe_name}_reviews.csv"
                
                self.scraper.save_reviews_to_csv(reviews_data, csv_filename)
            
            return {
                'success': True,
                'business_info': reviews_data['business_info'],
                'reviews_scraped': len(reviews_data['reviews']),
                'csv_file': csv_filename if save_csv else None
            }
            
        except Exception as e:
            logger.error(f"Error scraping and storing reviews: {e}")
            return {
                'success': False,
                'error': str(e),
                'reviews_scraped': 0
            }
    
    def ask_question(self, 
                    query: str, 
                    business_name: Optional[str] = None,
                    n_results: int = 5) -> Dict[str, Any]:
        """
        Ask a question about a business and get an LLM-generated response based on reviews.
        
        Args:
            query: The question to ask
            business_name: Optional specific business name to filter by
            n_results: Number of relevant reviews to retrieve
            
        Returns:
            Dictionary containing the response and metadata
        """
        try:
            if not self.llm_client:
                return {
                    'success': False,
                    'error': 'LLM client not initialized. Please provide OpenAI API key.',
                    'response': 'Unable to generate response without LLM access.'
                }
            
            # Search for relevant reviews
            relevant_reviews = self.rag_system.search_reviews(
                query=query,
                n_results=n_results,
                business_name=business_name
            )
            
            # Get business summary if business name is specified
            business_summary = None
            if business_name:
                business_summary = self.rag_system.get_business_summary(business_name)
            
            # Generate response using LLM
            response_data = self.llm_client.generate_response(
                query=query,
                reviews_context=relevant_reviews,
                business_summary=business_summary
            )
            
            # Add RAG system information
            response_data['relevant_reviews_found'] = len(relevant_reviews)
            response_data['business_name'] = business_name
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f'Error processing your question: {str(e)}',
                'query': query
            }
    
    def get_business_analysis(self, business_name: str) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis of a business based on all its reviews.
        
        Args:
            business_name: Name of the business to analyze
            
        Returns:
            Dictionary containing comprehensive business analysis
        """
        try:
            if not self.llm_client:
                return {
                    'success': False,
                    'error': 'LLM client not initialized. Please provide OpenAI API key.'
                }
            
            # Get business summary
            business_summary = self.rag_system.get_business_summary(business_name)
            
            if business_summary.get('total_reviews', 0) == 0:
                return {
                    'success': False,
                    'error': f'No reviews found for business: {business_name}',
                    'business_name': business_name
                }
            
            # Get sample reviews for detailed analysis
            sample_reviews = self.rag_system.search_reviews(
                query=f"reviews for {business_name}",
                business_name=business_name,
                n_results=20
            )
            
            # Generate comprehensive analysis
            analysis_data = self.llm_client.generate_business_analysis(
                business_summary=business_summary,
                sample_reviews=sample_reviews
            )
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"Error generating business analysis: {e}")
            return {
                'success': False,
                'error': str(e),
                'business_name': business_name
            }
    
    def list_businesses(self) -> List[str]:
        """
        List all businesses in the database.
        
        Returns:
            List of business names
        """
        return self.rag_system.list_businesses()
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the current database.
        
        Returns:
            Dictionary containing database statistics
        """
        return self.rag_system.get_collection_info()
    
    def delete_business(self, business_name: str) -> Dict[str, Any]:
        """
        Delete all reviews for a specific business.
        
        Args:
            business_name: Name of the business to delete
            
        Returns:
            Dictionary containing deletion results
        """
        try:
            success = self.rag_system.delete_business_reviews(business_name)
            return {
                'success': success,
                'business_name': business_name,
                'message': f'Successfully deleted reviews for {business_name}' if success else f'No reviews found for {business_name}'
            }
        except Exception as e:
            logger.error(f"Error deleting business: {e}")
            return {
                'success': False,
                'business_name': business_name,
                'error': str(e)
            }
    
    def search_reviews(self, query: str, business_name: Optional[str] = None, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for reviews based on a query.
        
        Args:
            query: Search query
            business_name: Optional business name filter
            n_results: Number of results to return
            
        Returns:
            List of relevant reviews
        """
        return self.rag_system.search_reviews(
            query=query,
            business_name=business_name,
            n_results=n_results
        )