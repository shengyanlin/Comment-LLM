# Comment-LLM

A powerful RAG (Retrieval-Augmented Generation) based system for analyzing Google Maps reviews. Input a Google Maps shop URL, and Comment-LLM will scrape all recent comments, store them in a vector database, and provide intelligent answers to your questions about the business using Large Language Models.

## Features

- 🌐 **Google Maps Review Scraping**: Automatically extract reviews from Google Maps business pages
- 🧠 **RAG System**: Store reviews in a vector database for intelligent retrieval
- 🤖 **LLM Integration**: Get AI-powered insights and answers about businesses
- 💾 **Persistent Storage**: Reviews are stored locally using ChromaDB
- 🔍 **Smart Search**: Find relevant reviews based on semantic similarity
- 📊 **Business Analysis**: Generate comprehensive business reports
- 🖥️ **CLI Interface**: Easy-to-use command-line interface
- 📝 **CSV Export**: Save scraped reviews to CSV files

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/shengyanlin/Comment-LLM.git
cd Comment-LLM

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### 2. Setup

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Usage

#### Scrape Reviews from Google Maps

```bash
# Scrape reviews from a Google Maps business URL
comment-llm scrape "https://maps.google.com/your-business-url" --max-reviews 100 --save-csv
```

#### Ask Questions About a Business

```bash
# Ask questions about the scraped reviews
comment-llm ask "What do customers say about the food quality?"
comment-llm ask "How is the customer service?" --business "Restaurant Name"
```

#### Generate Business Analysis

```bash
# Get a comprehensive analysis of a business
comment-llm analyze "Restaurant Name"
```

#### Interactive Mode

```bash
# Start interactive mode for continuous questioning
comment-llm interactive
```

## Command Reference

### Available Commands

| Command | Description |
|---------|-------------|
| `scrape` | Scrape reviews from Google Maps URL |
| `ask` | Ask questions about businesses |
| `analyze` | Generate comprehensive business analysis |
| `search` | Search for specific reviews |
| `list-businesses` | List all businesses in database |
| `info` | Show database information |
| `delete` | Delete reviews for a business |
| `interactive` | Start interactive question mode |

### Detailed Examples

#### Scraping Reviews

```bash
# Basic scraping
comment-llm scrape "https://maps.google.com/business-url"

# Scrape with options
comment-llm scrape "https://maps.google.com/business-url" \
  --max-reviews 200 \
  --save-csv \
  --csv-filename "my_business_reviews.csv"
```

#### Asking Questions

```bash
# General questions
comment-llm ask "What are the most common complaints?"
comment-llm ask "Is the parking situation good?"

# Business-specific questions
comment-llm ask "How is the food?" --business "Mario's Pizza"
comment-llm ask "What about the ambiance?" --business "Fancy Restaurant"
```

#### Search Reviews

```bash
# Search for specific topics
comment-llm search "parking" --max-results 10
comment-llm search "food quality" --business "Restaurant Name"
```

#### Database Management

```bash
# List all businesses
comment-llm list-businesses

# Get database info
comment-llm info

# Delete business reviews
comment-llm delete "Business Name"
```

## Python API Usage

You can also use Comment-LLM as a Python library:

```python
from comment_llm import CommentLLM

# Initialize the application
app = CommentLLM(openai_api_key="your-api-key")

# Scrape reviews
result = app.scrape_and_store_reviews(
    google_maps_url="https://maps.google.com/business-url",
    max_reviews=100
)

# Ask questions
response = app.ask_question(
    query="What do customers say about the service?",
    business_name="Restaurant Name"
)

print(response['response'])

# Get business analysis
analysis = app.get_business_analysis("Restaurant Name")
print(analysis['analysis'])

# Search reviews
reviews = app.search_reviews("food quality", n_results=5)
```

## Architecture

The system consists of three main components:

1. **GoogleMapsScraper**: Uses Selenium to scrape reviews from Google Maps
2. **RAGSystem**: Manages vector embeddings and similarity search using ChromaDB
3. **LLMClient**: Interfaces with OpenAI's API for generating responses

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB storage directory | `./chroma_db` |
| `HEADLESS_BROWSER` | Run browser in headless mode | `true` |
| `CHROMEDRIVER_PATH` | Path to ChromeDriver | Auto-detected |

### Browser Requirements

Comment-LLM uses Selenium with Chrome for web scraping. Make sure you have:

- Chrome browser installed
- ChromeDriver installed (or use `webdriver-manager` for auto-installation)

## Features in Detail

### RAG (Retrieval-Augmented Generation)

- Uses sentence transformers for semantic embedding
- Stores reviews in ChromaDB vector database
- Retrieves relevant reviews based on question similarity
- Provides context to LLM for accurate responses

### Review Scraping

- Handles dynamic loading of Google Maps reviews
- Extracts reviewer name, rating, date, and review text
- Supports scrolling to load more reviews
- Robust error handling for various page layouts

### LLM Integration

- Uses OpenAI's GPT models for response generation
- Provides context-aware answers based on retrieved reviews
- Generates comprehensive business analysis reports
- Supports custom prompts and temperature settings

## Troubleshooting

### Common Issues

1. **ChromeDriver Issues**
   - Make sure ChromeDriver is installed and in PATH
   - Or specify path in `.env`: `CHROMEDRIVER_PATH=/path/to/chromedriver`

2. **Google Maps Access**
   - Some business pages may have anti-scraping measures
   - Try running with `--no-headless` to see what's happening
   - Ensure the URL is a valid Google Maps business page

3. **API Rate Limits**
   - OpenAI has rate limits on API calls
   - The system handles rate limiting gracefully
   - Consider upgrading your OpenAI plan for higher limits

4. **Memory Usage**
   - Large numbers of reviews may use significant memory
   - Consider processing in smaller batches
   - ChromaDB persists data to disk to manage memory

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes. Please respect robots.txt files and terms of service when scraping websites. Be mindful of rate limits and don't overload servers.
