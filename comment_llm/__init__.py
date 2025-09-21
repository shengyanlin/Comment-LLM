"""
Comment-LLM: A RAG-based system for analyzing Google Maps reviews
"""

__version__ = "0.1.0"
__author__ = "Comment-LLM"
__email__ = ""

# Import classes only when explicitly requested to avoid dependency issues
def get_scraper():
    from .scraper import GoogleMapsScraper
    return GoogleMapsScraper

def get_rag_system():
    from .rag_system import RAGSystem
    return RAGSystem

def get_llm_client():
    from .llm_client import LLMClient
    return LLMClient

def get_app():
    from .app import CommentLLM
    return CommentLLM

# For backwards compatibility, try to import if dependencies are available
try:
    from .scraper import GoogleMapsScraper
    from .rag_system import RAGSystem
    from .llm_client import LLMClient
    from .app import CommentLLM
    
    __all__ = ["GoogleMapsScraper", "RAGSystem", "LLMClient", "CommentLLM"]
except ImportError:
    # Dependencies not available, that's okay
    __all__ = ["get_scraper", "get_rag_system", "get_llm_client", "get_app"]