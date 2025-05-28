from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os
from typing import List, Dict
import uvicorn

app = FastAPI(title="Retriever Agent")

# --- Root and favicon endpoints to prevent 404 errors ---
@app.get("/")
async def root():
    return {"message": "Retrieval API Operational"}

@app.get("/favicon.ico")
async def favicon():
    return {}

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class RetrievalResponse(BaseModel):
    chunks: List[Dict]
    scores: List[float]
    status: str

class VectorStore:
    def __init__(self, embedding_model="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(embedding_model)
        self.index = None
        self.documents = []
        self.embeddings_path = "data/embeddings"
        os.makedirs(self.embeddings_path, exist_ok=True)
        self.load_or_create_index()
    
    def load_or_create_index(self):
        """Load existing index or create new one"""
        index_path = os.path.join(self.embeddings_path, "faiss_index")
        docs_path = os.path.join(self.embeddings_path, "documents.pkl")
        
        if os.path.exists(index_path) and os.path.exists(docs_path):
            self.index = faiss.read_index(index_path)
            with open(docs_path, 'rb') as f:
                self.documents = pickle.load(f)
        else:
            # Create sample financial documents
            self.create_sample_documents()
    
    def create_sample_documents(self):
        """Create sample financial documents for demonstration"""
        sample_docs = [
            {"text": "TSMC reported strong Q4 earnings with revenue growth of 15% year-over-year", "source": "earnings_report"},
            {"text": "Samsung Electronics missed earnings estimates due to weak memory chip demand", "source": "earnings_report"},
            {"text": "Asia tech stocks showing mixed performance amid rising interest rates", "source": "market_analysis"},
            {"text": "Portfolio risk exposure in Asia tech sector increased to 22% of total AUM", "source": "portfolio_report"},
            {"text": "Regional sentiment remains neutral with cautionary outlook on tech valuations", "source": "analyst_report"}
        ]
        
        texts = [doc["text"] for doc in sample_docs]
        embeddings = self.model.encode(texts)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings.astype('float32'))
        
        self.documents = sample_docs
        self.save_index()
    
    def save_index(self):
        """Save FAISS index and documents"""
        index_path = os.path.join(self.embeddings_path, "faiss_index")
        docs_path = os.path.join(self.embeddings_path, "documents.pkl")
        
        faiss.write_index(self.index, index_path)
        with open(docs_path, 'wb') as f:
            pickle.dump(self.documents, f)
    
    def search(self, query: str, top_k: int = 5):
        """Search for similar documents"""
        query_embedding = self.model.encode([query])
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                results.append({
                    "document": self.documents[idx],
                    "score": float(scores[0][i])
                })
        
        return results

vector_store = VectorStore()

@app.post("/search", response_model=RetrievalResponse)
async def search_documents(request: QueryRequest):
    """Search for relevant documents"""
    try:
        results = vector_store.search(request.query, request.top_k)
        
        chunks = [r["document"] for r in results]
        scores = [r["score"] for r in results]
        
        return RetrievalResponse(chunks=chunks, scores=scores, status="success")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
