from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import uvicorn
from typing import List, Dict

app = FastAPI(title="Language Agent")

# --- Root and favicon endpoints to prevent 404 errors ---
@app.get("/")
async def root():
    return {"message": "Language API Operational"}

@app.get("/favicon.ico")
async def favicon():
    return {}

class SynthesisRequest(BaseModel):
    query: str
    context_chunks: List[Dict]
    market_data: List[Dict] = []

class SynthesisResponse(BaseModel):
    response: str
    confidence: float
    status: str

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434", model="llama3.1:latest"):
        self.base_url = base_url
        self.model = model
    
    def generate_response(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            if response.status_code == 200:
                return response.json()["response"]
            else:
                return f"Error from Ollama: {response.text}"
        except Exception as e:
            return f"Connection error to Ollama: {str(e)}"


ollama_client = OllamaClient()

@app.post("/synthesize", response_model=SynthesisResponse)
async def synthesize_response(request: SynthesisRequest):
    """Synthesize narrative response from context and data"""
    try:
        # Prepare context
        context_text = "\n".join([chunk.get("text", "") for chunk in request.context_chunks])
        
        # Prepare market data summary
        market_summary = ""
        if request.market_data:
            for stock in request.market_data:
                market_summary += f"{stock.get('symbol', 'Unknown')}: ${stock.get('current_price', 0):.2f} ({stock.get('change_percent', 0):.2f}%)\n"
        
        # Create comprehensive prompt
        prompt = f"""
You are a financial analyst providing a market brief. Based on the following context and market data, provide a concise, professional response to the query.

Query: {request.query}

Context Information:
{context_text}

Market Data:
{market_summary}

Please provide a clear, actionable response in the style of a portfolio manager's morning brief. Be specific about numbers, percentages, and key insights.

Response:"""
        
        # Generate response using Ollama
        response_text = ollama_client.generate_response(prompt)
        
        # Calculate confidence based on available data
        confidence = min(0.9, 0.5 + 0.1 * len(request.context_chunks) + 0.1 * len(request.market_data))
        
        return SynthesisResponse(
            response=response_text,
            confidence=confidence,
            status="success"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
