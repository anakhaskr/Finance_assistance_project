import os
from typing import Dict, Any

class Config:
    # Ollama Configuration
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama2"
    
    # API Keys (Set these as environment variables)
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
    
    # Vector Store Configuration
    VECTOR_STORE_PATH = "data/embeddings"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    # Voice Configuration
    VOICE_RATE = 150
    VOICE_VOLUME = 0.9
    
    # Agent Configuration
    AGENTS_CONFIG = {
        "api_agent": {"port": 8001},
        "scraping_agent": {"port": 8002},
        "retriever_agent": {"port": 8003},
        "analysis_agent": {"port": 8004},
        "language_agent": {"port": 8005},
        "voice_agent": {"port": 8006}
    }
    
    # Retrieval Configuration
    RETRIEVAL_THRESHOLD = 0.7
    TOP_K_CHUNKS = 5