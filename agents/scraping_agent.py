from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from data_ingestion.scraper import FinancialScraper

app = FastAPI(title="Scraping Agent")

# --- Root and favicon endpoints to prevent 404 errors ---
@app.get("/")
async def root():
    return {"message": "Scraping API Operational"}

@app.get("/favicon.ico")
async def favicon():
    return {}

class ScrapingResponse(BaseModel):
    data: List[Dict]
    status: str

@app.get("/scrape_news", response_model=ScrapingResponse)
async def scrape_market_news():
    """Scrape latest market news"""
    try:
        scraper = FinancialScraper()
        news_data = scraper.scrape_market_news()
        return ScrapingResponse(data=news_data, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scrape_earnings", response_model=ScrapingResponse)
async def scrape_earnings():
    """Scrape earnings calendar"""
    try:
        scraper = FinancialScraper()
        earnings_data = scraper.scrape_earnings_calendar()
        return ScrapingResponse(data=earnings_data, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
