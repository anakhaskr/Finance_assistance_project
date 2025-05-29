import asyncio
import httpx
from typing import Dict, List, Optional
from pydantic import BaseModel

class OrchestratorRequest(BaseModel):
    query: str
    mode: str = "text"  # "text" or "voice"
    audio_file: Optional[str] = None

class OrchestratorResponse(BaseModel):
    response: str
    confidence: float
    audio_file: Optional[str] = None
    status: str

class MainOrchestrator:
    def __init__(self):
        self.agents = {
            "api": "http://localhost:8001",
            "scraping": "http://localhost:8002", 
            "retriever": "http://localhost:8003",
            "analysis": "http://localhost:8004",
            "language": "http://localhost:8005",
            "voice": "http://localhost:8006"
        }
        self.confidence_threshold = 0.7
    
    async def process_request(self, request: OrchestratorRequest) -> OrchestratorResponse:
        """Main orchestration logic"""
        try:
            # Step 1: Handle voice input if needed
            query_text = request.query
            if request.mode == "voice" and request.audio_file:
                query_text = await self.process_voice_input(request.audio_file)
            
            # Step 2: Get market data
            market_data = await self.get_market_data()
            
            # Step 3: Get scraped news data if query is news-related
            news_data = []
            earnings_data = []
            if self._is_news_query(query_text):
                news_data = await self.get_scraped_news()
            if self._is_earnings_query(query_text):
                earnings_data = await self.get_scraped_earnings()
            
            # Step 4: Retrieve relevant context
            context_chunks = await self.retrieve_context(query_text)
            
            # Step 5: Synthesize response with all data sources
            synthesis_response = await self.synthesize_response(
                query_text, context_chunks, market_data, news_data, earnings_data
            )
            
            response_text = synthesis_response["response"]
            confidence = synthesis_response["confidence"]
            
            # Step 6: Handle voice output if needed
            audio_file = None
            if request.mode == "voice":
                audio_file = await self.generate_voice_response(response_text)
            
            # Step 7: Check confidence and handle fallback
            if confidence < self.confidence_threshold:
                fallback_msg = "I need more specific information to provide an accurate response. Could you please clarify your question?"
                if request.mode == "voice":
                    audio_file = await self.generate_voice_response(fallback_msg)
                response_text = fallback_msg
            
            return OrchestratorResponse(
                response=response_text,
                confidence=confidence,
                audio_file=audio_file,
                status="success"
            )
            
        except Exception as e:
            return OrchestratorResponse(
                response=f"Error processing request: {str(e)}",
                confidence=0.0,
                status="error"
            )
    
    def _is_news_query(self, query: str) -> bool:
        """Check if query is asking for news"""
        news_keywords = ["news", "headlines", "latest", "breaking", "announcements", "reports"]
        return any(keyword in query.lower() for keyword in news_keywords)
    
    def _is_earnings_query(self, query: str) -> bool:
        """Check if query is asking for earnings"""
        earnings_keywords = ["earnings", "quarterly", "results", "profit", "revenue", "eps"]
        return any(keyword in query.lower() for keyword in earnings_keywords)
    
    async def process_voice_input(self, audio_file: str) -> str:
        """Process voice input through STT"""
        async with httpx.AsyncClient() as client:
            with open(audio_file, 'rb') as f:
                files = {'file': f}
                response = await client.post(f"{self.agents['voice']}/speech_to_text", files=files)
                if response.status_code == 200:
                    return response.json()["text"]
                return "Error processing voice input"
    
    async def get_market_data(self) -> List[Dict]:
        """Get market data from API agent"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.agents['api']}/asia_tech_stocks")
                if response.status_code == 200:
                    return response.json()["data"]
                return []
        except:
            return []
    
    async def get_scraped_news(self) -> List[Dict]:
        """Get scraped news from scraping agent"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.agents['scraping']}/scrape_news")
                if response.status_code == 200:
                    return response.json()["data"]
                return []
        except:
            return []
    
    async def get_scraped_earnings(self) -> List[Dict]:
        """Get scraped earnings from scraping agent"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.agents['scraping']}/scrape_earnings")
                if response.status_code == 200:
                    return response.json()["data"]
                return []
        except:
            return []
    
    async def retrieve_context(self, query: str) -> List[Dict]:
        """Retrieve relevant context from retriever agent"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.agents['retriever']}/search",
                    json={"query": query, "top_k": 5}
                )
                if response.status_code == 200:
                    return response.json()["chunks"]
                return []
        except:
            return []
    
    async def synthesize_response(self, query: str, context: List[Dict], market_data: List[Dict], 
                                 news_data: List[Dict] = None, earnings_data: List[Dict] = None) -> Dict:
        """Synthesize response using language agent with all data sources"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Prepare additional context from scraped data
                additional_context = []
                
                if news_data:
                    for news in news_data[:3]:  # Top 3 news items
                        additional_context.append({
                            "text": f"Latest News - {news.get('title', '')}: {news.get('source', '')}",
                            "source": "scraped_news"
                        })
                
                if earnings_data:
                    for earnings in earnings_data[:3]:  # Top 3 earnings
                        additional_context.append({
                            "text": f"Earnings Update - {earnings.get('company', '')}: Expected {earnings.get('estimate', 0)}, Actual {earnings.get('actual', 0)}",
                            "source": "scraped_earnings"
                        })
                
                # Combine all context
                all_context = context + additional_context
                
                response = await client.post(
                    f"{self.agents['language']}/synthesize",
                    json={
                        "query": query,
                        "context_chunks": all_context,
                        "market_data": market_data
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    # Boost confidence if we have scraped data
                    if news_data or earnings_data:
                        result["confidence"] = min(0.95, result.get("confidence", 0.5) + 0.1)
                    return result
                return {"response": "Error generating response", "confidence": 0.0}
        except:
            return {"response": "Error connecting to language agent", "confidence": 0.0}
    
    async def generate_voice_response(self, text: str) -> str:
        """Generate voice response using TTS"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.agents['voice']}/text_to_speech",
                    json={"text": text, "voice_rate": 150}
                )
                if response.status_code == 200:
                    return response.json()["audio_file"]
                return None
        except:
            return None
