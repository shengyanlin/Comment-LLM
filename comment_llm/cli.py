"""
Command Line Interface for Comment-LLM

This module provides a CLI for interacting with the Comment-LLM system.
"""

import os
import sys
from typing import Optional

try:
    import click
except ImportError:
    print("Error: click package is required for CLI functionality")
    print("Install it with: pip install click")
    sys.exit(1)

try:
    from .app import CommentLLM
except ImportError as e:
    print(f"Error importing Comment-LLM components: {e}")
    print("Please install all dependencies with: pip install -r requirements.txt")
    sys.exit(1)


@click.group()
@click.option('--openai-api-key', help='OpenAI API key')
@click.option('--chroma-db-path', default='./chroma_db', help='Path to ChromaDB database')
@click.option('--headless/--no-headless', default=True, help='Run browser in headless mode')
@click.pass_context
def cli(ctx, openai_api_key: Optional[str], chroma_db_path: str, headless: bool):
    """Comment-LLM: A RAG-based system for analyzing Google Maps reviews."""
    ctx.ensure_object(dict)
    
    # Initialize the application
    try:
        app = CommentLLM(
            openai_api_key=openai_api_key,
            chroma_persist_directory=chroma_db_path,
            headless_browser=headless
        )
        ctx.obj['app'] = app
        click.echo("Comment-LLM initialized successfully!")
    except Exception as e:
        click.echo(f"Error initializing Comment-LLM: {e}", err=True)
        ctx.exit(1)


@cli.command()
@click.argument('google_maps_url')
@click.option('--max-reviews', default=100, help='Maximum number of reviews to scrape')
@click.option('--save-csv', is_flag=True, help='Save reviews to CSV file')
@click.option('--csv-filename', help='CSV filename (auto-generated if not provided)')
@click.pass_context
def scrape(ctx, google_maps_url: str, max_reviews: int, save_csv: bool, csv_filename: Optional[str]):
    """Scrape reviews from a Google Maps business URL."""
    app = ctx.obj['app']
    
    click.echo(f"Scraping reviews from: {google_maps_url}")
    click.echo(f"Maximum reviews: {max_reviews}")
    
    result = app.scrape_and_store_reviews(
        google_maps_url=google_maps_url,
        max_reviews=max_reviews,
        save_csv=save_csv,
        csv_filename=csv_filename
    )
    
    if result['success']:
        click.echo(f"✅ Successfully scraped {result['reviews_scraped']} reviews")
        click.echo(f"Business: {result['business_info'].get('name', 'Unknown')}")
        click.echo(f"Rating: {result['business_info'].get('rating', 'No rating')}")
        if result.get('csv_file'):
            click.echo(f"CSV saved to: {result['csv_file']}")
    else:
        click.echo(f"❌ Error: {result['error']}", err=True)


@cli.command()
@click.argument('question')
@click.option('--business', help='Filter by specific business name')
@click.option('--max-results', default=5, help='Maximum number of relevant reviews to consider')
@click.pass_context
def ask(ctx, question: str, business: Optional[str], max_results: int):
    """Ask a question about a business based on its reviews."""
    app = ctx.obj['app']
    
    click.echo(f"Question: {question}")
    if business:
        click.echo(f"Business filter: {business}")
    
    result = app.ask_question(
        query=question,
        business_name=business,
        n_results=max_results
    )
    
    if result['success']:
        click.echo("\n" + "="*50)
        click.echo("ANSWER:")
        click.echo("="*50)
        click.echo(result['response'])
        click.echo("\n" + "-"*50)
        click.echo(f"Based on {result['reviews_used']} relevant reviews")
        if result.get('token_usage'):
            click.echo(f"Tokens used: {result['token_usage']['total_tokens']}")
    else:
        click.echo(f"❌ Error: {result['error']}", err=True)


@cli.command()
@click.argument('business_name')
@click.pass_context
def analyze(ctx, business_name: str):
    """Generate a comprehensive analysis of a business."""
    app = ctx.obj['app']
    
    click.echo(f"Analyzing business: {business_name}")
    
    result = app.get_business_analysis(business_name)
    
    if result['success']:
        click.echo("\n" + "="*50)
        click.echo(f"BUSINESS ANALYSIS: {result['business_name']}")
        click.echo("="*50)
        click.echo(result['analysis'])
        click.echo("\n" + "-"*50)
        click.echo(f"Analysis based on {result['reviews_analyzed']} reviews")
        click.echo(f"Total reviews for business: {result['total_reviews']}")
    else:
        click.echo(f"❌ Error: {result['error']}", err=True)


@cli.command()
@click.argument('query')
@click.option('--business', help='Filter by specific business name')
@click.option('--max-results', default=10, help='Maximum number of results to return')
@click.pass_context
def search(ctx, query: str, business: Optional[str], max_results: int):
    """Search for reviews based on a query."""
    app = ctx.obj['app']
    
    click.echo(f"Searching for: {query}")
    if business:
        click.echo(f"Business filter: {business}")
    
    results = app.search_reviews(
        query=query,
        business_name=business,
        n_results=max_results
    )
    
    if results:
        click.echo(f"\nFound {len(results)} relevant reviews:")
        click.echo("="*50)
        
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            similarity = result['similarity_score']
            
            click.echo(f"\nResult {i} (Similarity: {similarity:.2f}):")
            click.echo(f"Business: {metadata.get('business_name', 'Unknown')}")
            click.echo(f"Reviewer: {metadata.get('reviewer_name', 'Anonymous')}")
            click.echo(f"Rating: {metadata.get('rating', 'No rating')}")
            click.echo(f"Date: {metadata.get('date', 'No date')}")
            click.echo(f"Review: {metadata.get('review_text', 'No text')[:200]}...")
            click.echo("-" * 30)
    else:
        click.echo("No relevant reviews found.")


@cli.command()
@click.pass_context
def list_businesses(ctx):
    """List all businesses in the database."""
    app = ctx.obj['app']
    
    businesses = app.list_businesses()
    
    if businesses:
        click.echo(f"Found {len(businesses)} businesses in database:")
        click.echo("="*40)
        for i, business in enumerate(businesses, 1):
            click.echo(f"{i}. {business}")
    else:
        click.echo("No businesses found in database.")


@cli.command()
@click.pass_context
def info(ctx):
    """Show database information."""
    app = ctx.obj['app']
    
    info_data = app.get_database_info()
    
    click.echo("DATABASE INFORMATION")
    click.echo("="*40)
    click.echo(f"Collection: {info_data['collection_name']}")
    click.echo(f"Total Reviews: {info_data['total_reviews']}")
    click.echo(f"Total Businesses: {info_data['total_businesses']}")
    
    if info_data.get('error'):
        click.echo(f"Error: {info_data['error']}", err=True)
    
    if info_data['businesses']:
        click.echo("\nBusinesses:")
        for business in info_data['businesses']:
            click.echo(f"  - {business}")


@cli.command()
@click.argument('business_name')
@click.confirmation_option(prompt='Are you sure you want to delete all reviews for this business?')
@click.pass_context
def delete(ctx, business_name: str):
    """Delete all reviews for a specific business."""
    app = ctx.obj['app']
    
    result = app.delete_business(business_name)
    
    if result['success']:
        click.echo(f"✅ {result['message']}")
    else:
        click.echo(f"❌ Error: {result.get('error', 'Unknown error')}", err=True)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive mode for asking questions."""
    app = ctx.obj['app']
    
    click.echo("Welcome to Comment-LLM Interactive Mode!")
    click.echo("Type 'quit' or 'exit' to leave, 'help' for commands.")
    click.echo("You can ask questions like:")
    click.echo("  - What do customers say about the food?")
    click.echo("  - How is the service at this restaurant?")
    click.echo("  - Are there any complaints about parking?")
    click.echo("")
    
    while True:
        try:
            # Get user input
            question = click.prompt("Your question", type=str)
            
            if question.lower() in ['quit', 'exit']:
                click.echo("Goodbye!")
                break
            
            if question.lower() == 'help':
                click.echo("\nAvailable commands:")
                click.echo("  - Ask any question about businesses")
                click.echo("  - 'list' - show all businesses")
                click.echo("  - 'info' - show database info")
                click.echo("  - 'quit' or 'exit' - leave interactive mode")
                continue
            
            if question.lower() == 'list':
                businesses = app.list_businesses()
                if businesses:
                    click.echo(f"\nBusinesses in database ({len(businesses)}):")
                    for business in businesses:
                        click.echo(f"  - {business}")
                else:
                    click.echo("No businesses found in database.")
                continue
            
            if question.lower() == 'info':
                info_data = app.get_database_info()
                click.echo(f"\nDatabase Info:")
                click.echo(f"  Total Reviews: {info_data['total_reviews']}")
                click.echo(f"  Total Businesses: {info_data['total_businesses']}")
                continue
            
            # Ask the question
            click.echo("\nThinking...")
            result = app.ask_question(query=question, n_results=5)
            
            if result['success']:
                click.echo("\n" + "="*50)
                click.echo("ANSWER:")
                click.echo("="*50)
                click.echo(result['response'])
                click.echo("\n" + "-"*30)
                click.echo(f"Based on {result['reviews_used']} relevant reviews")
            else:
                click.echo(f"❌ Error: {result['error']}")
            
            click.echo("")  # Empty line for readability
            
        except (KeyboardInterrupt, EOFError):
            click.echo("\nGoodbye!")
            break
        except Exception as e:
            click.echo(f"Error: {e}", err=True)


def main():
    """Main entry point for the CLI."""
    cli()