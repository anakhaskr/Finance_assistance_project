import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict
import time
import re

class FinancialScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_market_news(self) -> List[Dict]:
        """Scrape financial news from public sources"""
        news_data = []
        
        try:
            # Scrape from Yahoo Finance news
            url = "https://finance.yahoo.com/news/"
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all('h3', class_='Mb(5px)')[:10]
            
            for article in articles:
                try:
                    title = article.get_text().strip()
                    link_elem = article.find('a')
                    link = link_elem['href'] if link_elem else ""
                    
                    news_data.append({
                        "title": title,
                        "link": f"https://finance.yahoo.com{link}" if link.startswith('/') else link,
                        "source": "Yahoo Finance",
                        "timestamp": time.time()
                    })
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"Error scraping news: {e}")
        
        return news_data
    
    def scrape_earnings_calendar(self) -> List[Dict]:
        """Scrape earnings calendar data"""
        earnings_data = []
        
        try:
            # Mock earnings data for demonstration
            earnings_data = [
                {"company": "TSMC", "symbol": "TSM", "date": "2024-01-15", "estimate": 1.20, "actual": 1.25},
                {"company": "Samsung", "symbol": "005930.KS", "date": "2024-01-14", "estimate": 0.85, "actual": 0.83},
            ]
        except Exception as e:
            print(f"Error scraping earnings: {e}")
        
        return earnings_data