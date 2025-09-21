"""
LLM Client Module

This module provides functionality to interact with various LLM APIs
for generating responses based on retrieved review information.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMClient:
    """
    A client for interacting with Large Language Models (LLMs) to generate
    responses based on retrieved review information.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the LLM client.
        
        Args:
            api_key: OpenAI API key (if None, will try to get from environment)
            model: The model to use for generation
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info(f"LLM client initialized with model: {self.model}")
    
    def _create_system_prompt(self) -> str:
        """Create a system prompt for the LLM."""
        return """You are a helpful AI assistant that analyzes customer reviews and provides insights about businesses. 

Your role is to:
1. Analyze customer reviews and provide accurate, helpful insights
2. Answer questions about businesses based on the review data provided
3. Summarize customer sentiment and key themes from reviews
4. Provide balanced perspectives that consider both positive and negative feedback
5. Be objective and factual in your analysis

When answering questions:
- Base your responses primarily on the provided review data
- Be specific and cite relevant details from the reviews when possible
- If the review data doesn't contain enough information to answer a question, say so clearly
- Provide balanced insights that consider different customer perspectives
- Be helpful and informative while maintaining objectivity"""
    
    def _create_user_prompt(self, query: str, reviews_context: List[Dict[str, Any]], business_summary: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a user prompt with the query and relevant review context.
        
        Args:
            query: The user's question
            reviews_context: Relevant reviews retrieved from RAG system
            business_summary: Optional business summary information
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        # Add business summary if available
        if business_summary:
            prompt_parts.append("BUSINESS SUMMARY:")
            prompt_parts.append(f"Business Name: {business_summary.get('business_name', 'Unknown')}")
            prompt_parts.append(f"Overall Rating: {business_summary.get('business_rating', 'No rating')}")
            prompt_parts.append(f"Average Review Rating: {business_summary.get('average_rating', 'No rating')}")
            prompt_parts.append(f"Total Reviews Analyzed: {business_summary.get('total_reviews', 0)}")
            prompt_parts.append("")
        
        # Add relevant reviews context
        if reviews_context:
            prompt_parts.append("RELEVANT CUSTOMER REVIEWS:")
            for i, review_data in enumerate(reviews_context, 1):
                metadata = review_data.get('metadata', {})
                similarity_score = review_data.get('similarity_score', 0)
                
                prompt_parts.append(f"\nReview {i} (Relevance: {similarity_score:.2f}):")
                prompt_parts.append(f"Reviewer: {metadata.get('reviewer_name', 'Anonymous')}")
                prompt_parts.append(f"Rating: {metadata.get('rating', 'No rating')}")
                prompt_parts.append(f"Date: {metadata.get('date', 'No date')}")
                prompt_parts.append(f"Review Text: {metadata.get('review_text', 'No text')}")
        else:
            prompt_parts.append("No relevant reviews found for this query.")
        
        # Add the user's question
        prompt_parts.append(f"\nUSER QUESTION: {query}")
        prompt_parts.append("\nPlease analyze the provided review information and answer the user's question. Be specific and reference relevant details from the reviews when possible.")
        
        return "\n".join(prompt_parts)
    
    def generate_response(self, 
                         query: str, 
                         reviews_context: List[Dict[str, Any]], 
                         business_summary: Optional[Dict[str, Any]] = None,
                         max_tokens: int = 1000,
                         temperature: float = 0.7) -> Dict[str, Any]:
        """
        Generate a response based on the query and review context.
        
        Args:
            query: The user's question
            reviews_context: Relevant reviews from RAG system
            business_summary: Optional business summary
            max_tokens: Maximum tokens in response
            temperature: Temperature for response generation
            
        Returns:
            Dictionary containing the response and metadata
        """
        try:
            # Create prompts
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(query, reviews_context, business_summary)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract response
            generated_text = response.choices[0].message.content
            
            result = {
                'response': generated_text,
                'query': query,
                'model': self.model,
                'reviews_used': len(reviews_context),
                'token_usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'success': True
            }
            
            logger.info(f"Generated response for query: '{query[:50]}...'")
            logger.info(f"Token usage - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'response': f"I apologize, but I encountered an error while processing your question: {str(e)}",
                'query': query,
                'model': self.model,
                'reviews_used': len(reviews_context),
                'error': str(e),
                'success': False
            }
    
    def generate_business_analysis(self, business_summary: Dict[str, Any], sample_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis of a business based on all its reviews.
        
        Args:
            business_summary: Summary statistics of the business
            sample_reviews: Sample of reviews for detailed analysis
            
        Returns:
            Dictionary containing comprehensive business analysis
        """
        try:
            system_prompt = """You are a business analyst AI that provides comprehensive insights about businesses based on customer review data. 

Your task is to analyze the provided review data and generate a comprehensive business analysis that includes:
1. Overall customer sentiment and satisfaction
2. Key strengths and areas for improvement
3. Common themes in customer feedback
4. Recommendations for the business
5. Summary of customer experience patterns

Be objective, balanced, and provide actionable insights."""
            
            user_prompt = f"""Please analyze the following business based on customer review data:

BUSINESS SUMMARY:
Business Name: {business_summary.get('business_name', 'Unknown')}
Overall Rating: {business_summary.get('business_rating', 'No rating')}
Average Review Rating: {business_summary.get('average_rating', 'No rating')}
Total Reviews: {business_summary.get('total_reviews', 0)}

SAMPLE CUSTOMER REVIEWS:
"""
            
            for i, review_data in enumerate(sample_reviews[:10], 1):  # Limit to 10 reviews for analysis
                metadata = review_data.get('metadata', {})
                user_prompt += f"""
Review {i}:
Reviewer: {metadata.get('reviewer_name', 'Anonymous')}
Rating: {metadata.get('rating', 'No rating')}
Date: {metadata.get('date', 'No date')}
Review: {metadata.get('review_text', 'No text')}
"""
            
            user_prompt += """
Please provide a comprehensive analysis including:
1. Overall Assessment
2. Key Strengths
3. Areas for Improvement
4. Customer Sentiment Analysis
5. Recommendations
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            generated_analysis = response.choices[0].message.content
            
            result = {
                'business_name': business_summary.get('business_name', 'Unknown'),
                'analysis': generated_analysis,
                'reviews_analyzed': len(sample_reviews),
                'total_reviews': business_summary.get('total_reviews', 0),
                'model': self.model,
                'token_usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'success': True
            }
            
            logger.info(f"Generated business analysis for: {business_summary.get('business_name', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating business analysis: {e}")
            return {
                'business_name': business_summary.get('business_name', 'Unknown'),
                'analysis': f"Error generating analysis: {str(e)}",
                'error': str(e),
                'success': False
            }
    
    def summarize_reviews(self, reviews: List[Dict[str, Any]], max_reviews: int = 20) -> Dict[str, Any]:
        """
        Generate a summary of multiple reviews.
        
        Args:
            reviews: List of review data
            max_reviews: Maximum number of reviews to include in summary
            
        Returns:
            Dictionary containing review summary
        """
        try:
            if not reviews:
                return {
                    'summary': 'No reviews available to summarize.',
                    'total_reviews': 0,
                    'success': True
                }
            
            # Limit the number of reviews for summarization
            reviews_to_summarize = reviews[:max_reviews]
            
            system_prompt = """You are an AI assistant that specializes in summarizing customer reviews. 
            
Your task is to analyze multiple customer reviews and provide a concise, balanced summary that captures:
1. Overall sentiment
2. Most commonly mentioned positive aspects
3. Most commonly mentioned negative aspects or concerns
4. Key themes and patterns in customer feedback

Be objective and balanced in your summary."""
            
            user_prompt = "Please summarize the following customer reviews:\n\n"
            
            for i, review_data in enumerate(reviews_to_summarize, 1):
                metadata = review_data.get('metadata', {})
                user_prompt += f"Review {i}: Rating {metadata.get('rating', 'No rating')} - {metadata.get('review_text', 'No text')}\n\n"
            
            user_prompt += f"Please provide a concise summary of these {len(reviews_to_summarize)} reviews, highlighting the main themes and overall customer sentiment."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            summary_text = response.choices[0].message.content
            
            result = {
                'summary': summary_text,
                'reviews_summarized': len(reviews_to_summarize),
                'total_reviews': len(reviews),
                'model': self.model,
                'token_usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'success': True
            }
            
            logger.info(f"Generated summary for {len(reviews_to_summarize)} reviews")
            return result
            
        except Exception as e:
            logger.error(f"Error summarizing reviews: {e}")
            return {
                'summary': f"Error generating summary: {str(e)}",
                'total_reviews': len(reviews),
                'error': str(e),
                'success': False
            }