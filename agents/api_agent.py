from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import uvicorn
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from data_ingestion.api_client import MarketDataClient

app = FastAPI(title="API Agent")

class StockRequest(BaseModel):
    symbols: List[str]

class MarketDataResponse(BaseModel):
    data: List[Dict]
    status: str

@app.get("/")
async def root():
    return {"message": "Welcome to the API Agent"}

@app.get("/favicon.ico")
async def favicon():
    return {}

@app.post("/get_market_data", response_model=MarketDataResponse)
async def get_market_data(request: StockRequest):
    """Get market data for specified stocks"""
    try:
        client = MarketDataClient()
        data = []
        for symbol in request.symbols:
            stock_data = client.get_stock_data(symbol)
            if stock_data:
                data.append(stock_data)
        return MarketDataResponse(data=data, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/asia_tech_stocks")
async def get_asia_tech_stocks():
    """Get Asia tech stocks data"""
    try:
        client = MarketDataClient()
        data = client.get_asia_tech_stocks()
        return {"data": data, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
