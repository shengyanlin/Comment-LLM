#!/usr/bin/env python3
"""
Example script demonstrating Comment-LLM usage.

This script shows how to use Comment-LLM to scrape reviews
and ask questions about a business.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comment_llm import CommentLLM

# Load environment variables
load_dotenv()

def main():
    """Main example function."""
    print("🚀 Comment-LLM Example")
    print("=" * 50)
    
    # Check if OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY in your .env file")
        print("Copy .env.example to .env and add your API key")
        return
    
    # Initialize Comment-LLM
    print("Initializing Comment-LLM...")
    app = CommentLLM()
    
    # Example Google Maps URL (replace with a real one)
    example_url = "https://maps.google.com/maps?cid=12345"  # Replace with real URL
    
    print(f"\n📍 Example workflow:")
    print(f"1. Scrape reviews from: {example_url}")
    print(f"2. Ask questions about the business")
    print(f"3. Generate business analysis")
    
    # For demonstration, we'll show the workflow without actually scraping
    print(f"\n💡 To use this script with a real business:")
    print(f"1. Find a Google Maps business URL")
    print(f"2. Replace the example_url variable with the real URL")
    print(f"3. Uncomment the scraping code below")
    
    print(f"\n🔍 Example questions you can ask:")
    print(f"- What do customers say about the food?")
    print(f"- How is the customer service?")
    print(f"- Are there any parking issues?")
    print(f"- What are the most common complaints?")
    print(f"- How do customers rate the atmosphere?")
    
    # Uncomment the following lines to actually scrape and analyze
    """
    # Scrape reviews
    print("\\nScraping reviews...")
    result = app.scrape_and_store_reviews(
        google_maps_url=example_url,
        max_reviews=50,
        save_csv=True
    )
    
    if result['success']:
        business_name = result['business_info']['name']
        print(f"✅ Successfully scraped {result['reviews_scraped']} reviews")
        print(f"Business: {business_name}")
        
        # Ask example questions
        questions = [
            "What do customers say about the food quality?",
            "How is the customer service?",
            "Are there any common complaints?"
        ]
        
        for question in questions:
            print(f"\\n❓ Question: {question}")
            response = app.ask_question(question, business_name=business_name)
            
            if response['success']:
                print(f"🤖 Answer: {response['response'][:200]}...")
            else:
                print(f"❌ Error: {response['error']}")
        
        # Generate business analysis
        print(f"\\n📊 Generating business analysis...")
        analysis = app.get_business_analysis(business_name)
        
        if analysis['success']:
            print(f"📋 Analysis preview: {analysis['analysis'][:300]}...")
        else:
            print(f"❌ Error: {analysis['error']}")
    
    else:
        print(f"❌ Error scraping reviews: {result['error']}")
    """
    
    # Show current database info
    print(f"\n📊 Current database information:")
    info = app.get_database_info()
    print(f"Total reviews: {info['total_reviews']}")
    print(f"Total businesses: {info['total_businesses']}")
    
    if info['businesses']:
        print(f"Businesses in database:")
        for business in info['businesses'][:5]:  # Show first 5
            print(f"  - {business}")
        if len(info['businesses']) > 5:
            print(f"  ... and {len(info['businesses']) - 5} more")
    
    print(f"\n🎯 Next steps:")
    print(f"1. Get a Google Maps business URL")
    print(f"2. Use: comment-llm scrape 'YOUR_GOOGLE_MAPS_URL'")
    print(f"3. Use: comment-llm ask 'Your question about the business'")
    print(f"4. Use: comment-llm interactive (for continuous questioning)")

if __name__ == "__main__":
    main()