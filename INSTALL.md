# Installation Guide for Comment-LLM

## Quick Start with Dependencies

If you encounter dependency installation issues, try these alternatives:

### Option 1: Install core dependencies individually
```bash
# Install core Python packages
pip install click python-dotenv

# Install ML/AI packages (may take longer)
pip install numpy pandas
pip install sentence-transformers
pip install chromadb
pip install openai

# Install web scraping packages
pip install selenium beautifulsoup4 requests
pip install tqdm
```

### Option 2: Use conda (recommended for ML packages)
```bash
# Install with conda for better dependency management
conda install numpy pandas requests
conda install -c conda-forge chromadb
pip install selenium beautifulsoup4 openai sentence-transformers click python-dotenv tqdm
```

### Option 3: Use Docker (coming soon)
We're working on a Docker image for easier deployment.

## Browser Setup for Scraping

For Google Maps scraping, you need Chrome and ChromeDriver:

### Ubuntu/Debian:
```bash
# Install Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install google-chrome-stable

# Install ChromeDriver
sudo apt install chromium-chromedriver
```

### macOS:
```bash
# Using Homebrew
brew install --cask google-chrome
brew install chromedriver
```

### Windows:
1. Download Chrome from https://www.google.com/chrome/
2. Download ChromeDriver from https://chromedriver.chromium.org/
3. Add ChromeDriver to your PATH

## Verify Installation

Test the basic structure:
```bash
python test_basic_structure.py
```

## OpenAI API Setup

1. Get your API key from https://platform.openai.com/
2. Copy `.env.example` to `.env`
3. Add your API key to the `.env` file

## Troubleshooting

### Common Issues:

1. **Module not found errors**: Install missing dependencies individually
2. **ChromeDriver issues**: Make sure Chrome and ChromeDriver versions match
3. **OpenAI API errors**: Check your API key and billing setup
4. **Memory issues**: Start with smaller numbers of reviews (--max-reviews 50)

### Getting Help:

If you encounter issues, please check:
1. Python version (3.8+ required)
2. All dependencies are installed
3. Environment variables are set correctly
4. Chrome/ChromeDriver are properly installed