import requests
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

class MarketDataClient:
    def __init__(self, alpha_vantage_key: str = "demo"):
        self.alpha_vantage_key = alpha_vantage_key
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_stock_data(self, symbol: str) -> Dict:
        """Get real-time stock data using yfinance as primary source"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="5d")
            
            return {
                "symbol": symbol,
                "current_price": info.get("currentPrice", 0),
                "change_percent": info.get("changePercent", 0),
                "volume": info.get("volume", 0),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "recent_prices": hist["Close"].tolist()[-5:],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return {}
    
    def get_asia_tech_stocks(self) -> List[Dict]:
        """Get data for major Asia tech stocks"""
        asia_tech_symbols = ["TSM", "005930.KS", "BABA", "TCEHY", "9988.HK"]
        stocks_data = []
        
        for symbol in asia_tech_symbols:
            data = self.get_stock_data(symbol)
            if data:
                stocks_data.append(data)
        
        return stocks_data
    
    def get_earnings_data(self, symbol: str) -> Dict:
        """Get earnings data for a stock"""
        try:
            ticker = yf.Ticker(symbol)
            calendar = ticker.calendar
            earnings = ticker.earnings
            
            return {
                "symbol": symbol,
                "next_earnings": calendar.index[0].strftime("%Y-%m-%d") if not calendar.empty else None,
                "recent_earnings": earnings.to_dict() if earnings is not None else {},
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error fetching earnings for {symbol}: {e}")
            return {}