import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found in environment variables. "
        "Please create a .env file with your Groq API key."
    )

# LLM Configuration - Groq Models (Updated January 2026)
# Available models (free tier):
# - llama-3.3-70b-versatile (RECOMMENDED - best quality, latest)
# - llama-3.1-8b-instant (faster, good quality)
# - mixtral-8x7b-32768 (good balance, large context)
# - gemma2-9b-it (Google's model, fast)

GROQ_MODEL = "llama-3.3-70b-versatile"  # Latest and best quality for RAG
GROQ_TEMPERATURE = 0.1  # Low temperature for factual responses

# Embedding Configuration (runs locally - FREE)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# RAG Configuration 
CHUNK_SIZE = 1500        
CHUNK_OVERLAP = 300      
TOP_K_RESULTS = 9        

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000

# Rate Limiting (Groq free tier)
GROQ_RATE_LIMIT = {
    "requests_per_minute": 30,
    "tokens_per_minute": 6000
}