from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

app = FastAPI(title="Analysis Agent")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisRequest(BaseModel):
    market_data: List[Dict]
    portfolio_data: Optional[Dict] = None
    analysis_type: str = "comprehensive"  # comprehensive, risk, performance, sentiment

class RiskAnalysisRequest(BaseModel):
    portfolio: Dict[str, float]  # symbol: weight
    market_data: List[Dict]
    benchmark: Optional[str] = "SPY"

class PerformanceAnalysisRequest(BaseModel):
    symbols: List[str]
    market_data: List[Dict]
    period: Optional[str] = "1M"  # 1D, 1W, 1M, 3M, 6M, 1Y

class AnalysisResponse(BaseModel):
    analysis: Dict[str, Any]
    metrics: Dict[str, float]
    insights: List[str]
    status: str
    timestamp: str

class RiskMetrics(BaseModel):
    var_95: float  # Value at Risk 95%
    var_99: float  # Value at Risk 99%
    beta: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    correlation_matrix: Dict[str, Dict[str, float]]

@app.get("/")
async def root():
    return {"message": "Welcome to the Analysis Agent", "version": "1.0", "port": 8004}

@app.get("/favicon.ico")
async def favicon():
    return {}

@app.get("/health")
async def health_check():
    """Health check endpoint for orchestrator"""
    return {
        "status": "healthy",
        "service": "analysis_agent",
        "port": 8004,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/comprehensive_analysis", response_model=AnalysisResponse)
async def comprehensive_analysis(request: AnalysisRequest):
    """Perform comprehensive financial analysis"""
    try:
        analysis_result = {}
        metrics = {}
        insights = []
        
        if not request.market_data:
            raise HTTPException(status_code=400, detail="No market data provided")
        
        # Convert market data to DataFrame for analysis
        df = pd.DataFrame(request.market_data)
        
        # Basic statistics
        if 'price' in df.columns:
            metrics['avg_price'] = float(df['price'].mean())
            metrics['price_volatility'] = float(df['price'].std())
            metrics['min_price'] = float(df['price'].min())
            metrics['max_price'] = float(df['price'].max())
        
        # Performance analysis
        if 'change_percent' in df.columns:
            metrics['avg_return'] = float(df['change_percent'].mean())
            metrics['return_volatility'] = float(df['change_percent'].std())
            
            # Count positive/negative performers
            positive_performers = len(df[df['change_percent'] > 0])
            total_stocks = len(df)
            metrics['positive_ratio'] = positive_performers / total_stocks if total_stocks > 0 else 0
        
        # Volume analysis
        if 'volume' in df.columns:
            metrics['avg_volume'] = float(df['volume'].mean())
            metrics['volume_weighted_price'] = calculate_vwap(df)
        
        # Market cap analysis (if available)
        if 'market_cap' in df.columns:
            metrics['total_market_cap'] = float(df['market_cap'].sum())
            metrics['avg_market_cap'] = float(df['market_cap'].mean())
        
        # Generate insights based on analysis
        insights = generate_market_insights(df, metrics)
        
        # Sector/Regional analysis for Asia tech stocks
        if any('asia' in str(item).lower() or 'tech' in str(item).lower() for item in df.to_dict('records')):
            sector_analysis = analyze_asia_tech_sector(df)
            analysis_result['sector_analysis'] = sector_analysis
        
        analysis_result['summary'] = create_analysis_summary(metrics, insights)
        
        return AnalysisResponse(
            analysis=analysis_result,
            metrics=metrics,
            insights=insights,
            status="success",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/risk_analysis")
async def risk_analysis(request: RiskAnalysisRequest):
    """Perform portfolio risk analysis"""
    try:
        if not request.market_data:
            raise HTTPException(status_code=400, detail="No market data provided")
        
        df = pd.DataFrame(request.market_data)
        
        # Calculate returns if price data available
        returns = []
        if 'change_percent' in df.columns:
            returns = df['change_percent'].values / 100
        elif 'price' in df.columns:
            # Calculate daily returns from prices
            prices = df['price'].values
            returns = np.diff(prices) / prices[:-1]
        
        if len(returns) == 0:
            raise HTTPException(status_code=400, detail="Insufficient data for risk analysis")
        
        # Calculate risk metrics
        risk_metrics = calculate_risk_metrics(returns, request.portfolio)
        
        return {
            "risk_metrics": risk_metrics,
            "portfolio_exposure": request.portfolio,
            "recommendations": generate_risk_recommendations(risk_metrics),
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Risk analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")

@app.post("/performance_analysis")
async def performance_analysis(request: PerformanceAnalysisRequest):
    """Analyze stock performance metrics"""
    try:
        if not request.market_data:
            raise HTTPException(status_code=400, detail="No market data provided")
        
        df = pd.DataFrame(request.market_data)
        
        # Filter data for requested symbols
        if request.symbols:
            df = df[df['symbol'].isin(request.symbols)] if 'symbol' in df.columns else df
        
        performance_metrics = {}
        
        # Calculate performance metrics
        if 'change_percent' in df.columns:
            performance_metrics['total_return'] = float(df['change_percent'].sum())
            performance_metrics['avg_return'] = float(df['change_percent'].mean())
            performance_metrics['volatility'] = float(df['change_percent'].std())
            
            # Winners and losers
            winners = df.nlargest(3, 'change_percent')[['symbol', 'change_percent']].to_dict('records') if 'symbol' in df.columns else []
            losers = df.nsmallest(3, 'change_percent')[['symbol', 'change_percent']].to_dict('records') if 'symbol' in df.columns else []
            
            performance_metrics['top_performers'] = winners
            performance_metrics['worst_performers'] = losers
        
        # Calculate momentum indicators
        momentum_analysis = calculate_momentum_indicators(df)
        
        return {
            "performance_metrics": performance_metrics,
            "momentum_analysis": momentum_analysis,
            "period": request.period,
            "symbols_analyzed": request.symbols,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Performance analysis failed: {str(e)}")

@app.post("/earnings_analysis")
async def earnings_analysis(request: AnalysisRequest):
    """Analyze earnings surprises and expectations"""
    try:
        if not request.market_data:
            raise HTTPException(status_code=400, detail="No market data provided")
        
        df = pd.DataFrame(request.market_data)
        
        earnings_analysis = {}
        
        # Check for earnings-related fields
        if 'earnings_surprise' in df.columns:
            positive_surprises = df[df['earnings_surprise'] > 0]
            negative_surprises = df[df['earnings_surprise'] < 0]
            
            earnings_analysis['positive_surprises'] = len(positive_surprises)
            earnings_analysis['negative_surprises'] = len(negative_surprises)
            earnings_analysis['avg_surprise'] = float(df['earnings_surprise'].mean())
            
            # Top earnings beats and misses
            if 'symbol' in df.columns:
                earnings_analysis['top_beats'] = positive_surprises.nlargest(3, 'earnings_surprise')[['symbol', 'earnings_surprise']].to_dict('records')
                earnings_analysis['worst_misses'] = negative_surprises.nsmallest(3, 'earnings_surprise')[['symbol', 'earnings_surprise']].to_dict('records')
        
        # Generate earnings insights
        earnings_insights = generate_earnings_insights(df, earnings_analysis)
        
        return {
            "earnings_analysis": earnings_analysis,
            "insights": earnings_insights,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Earnings analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Earnings analysis failed: {str(e)}")

def calculate_vwap(df: pd.DataFrame) -> float:
    """Calculate Volume Weighted Average Price"""
    if 'price' in df.columns and 'volume' in df.columns:
        return float((df['price'] * df['volume']).sum() / df['volume'].sum())
    return 0.0

def calculate_risk_metrics(returns: np.ndarray, portfolio: Dict[str, float]) -> Dict[str, float]:
    """Calculate portfolio risk metrics"""
    if len(returns) == 0:
        return {}
    
    # Portfolio returns (simplified - assumes equal weighting if no portfolio data)
    portfolio_return = np.mean(returns)
    portfolio_vol = np.std(returns)
    
    # VaR calculations (95% and 99%)
    var_95 = np.percentile(returns, 5) * 100  # Convert to percentage
    var_99 = np.percentile(returns, 1) * 100
    
    # Sharpe ratio (assuming risk-free rate of 2%)
    risk_free_rate = 0.02 / 252  # Daily risk-free rate
    sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_vol if portfolio_vol > 0 else 0
    
    # Maximum drawdown
    cumulative_returns = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative_returns)
    drawdowns = (cumulative_returns - running_max) / running_max
    max_drawdown = np.min(drawdowns) * 100
    
    return {
        "var_95": float(var_95),
        "var_99": float(var_99),
        "volatility": float(portfolio_vol * 100),
        "sharpe_ratio": float(sharpe_ratio),
        "max_drawdown": float(max_drawdown),
        "beta": 1.0  # Simplified - would need benchmark data for actual calculation
    }

def generate_market_insights(df: pd.DataFrame, metrics: Dict[str, float]) -> List[str]:
    """Generate market insights based on analysis"""
    insights = []
    
    if 'positive_ratio' in metrics:
        if metrics['positive_ratio'] > 0.7:
            insights.append("Strong bullish sentiment with over 70% of stocks showing positive performance")
        elif metrics['positive_ratio'] < 0.3:
            insights.append("Bearish market conditions with less than 30% of stocks in positive territory")
        else:
            insights.append("Mixed market sentiment with balanced positive and negative performers")
    
    if 'return_volatility' in metrics:
        if metrics['return_volatility'] > 5:
            insights.append("High market volatility detected - increased risk environment")
        elif metrics['return_volatility'] < 1:
            insights.append("Low volatility environment suggests stable market conditions")
    
    if 'avg_return' in metrics:
        if metrics['avg_return'] > 2:
            insights.append("Strong average returns indicate positive market momentum")
        elif metrics['avg_return'] < -2:
            insights.append("Negative average returns suggest market weakness")
    
    return insights

def analyze_asia_tech_sector(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze Asia tech sector specifically"""
    analysis = {
        "sector": "Asia Technology",
        "total_stocks": len(df),
        "analysis_timestamp": datetime.now().isoformat()
    }
    
    if 'market_cap' in df.columns:
        analysis['total_market_cap'] = float(df['market_cap'].sum())
        analysis['avg_market_cap'] = float(df['market_cap'].mean())
    
    if 'change_percent' in df.columns:
        analysis['sector_performance'] = float(df['change_percent'].mean())
        analysis['performance_range'] = {
            'min': float(df['change_percent'].min()),
            'max': float(df['change_percent'].max())
        }
    
    return analysis

def calculate_momentum_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate technical momentum indicators"""
    momentum = {}
    
    if 'price' in df.columns and len(df) > 1:
        prices = df['price'].values
        
        # Simple moving average (if enough data points)
        if len(prices) >= 5:
            sma_5 = np.mean(prices[-5:])
            current_price = prices[-1]
            momentum['sma_signal'] = "bullish" if current_price > sma_5 else "bearish"
            momentum['price_vs_sma'] = float((current_price - sma_5) / sma_5 * 100)
    
    if 'volume' in df.columns:
        volumes = df['volume'].values
        if len(volumes) >= 2:
            momentum['volume_trend'] = "increasing" if volumes[-1] > volumes[-2] else "decreasing"
            momentum['avg_volume'] = float(np.mean(volumes))
    
    return momentum

def generate_risk_recommendations(risk_metrics: Dict[str, float]) -> List[str]:
    """Generate risk management recommendations"""
    recommendations = []
    
    if risk_metrics.get('var_95', 0) < -10:
        recommendations.append("High VaR detected - consider position sizing or hedging strategies")
    
    if risk_metrics.get('volatility', 0) > 25:
        recommendations.append("Elevated volatility - implement risk management protocols")
    
    if risk_metrics.get('sharpe_ratio', 0) < 0.5:
        recommendations.append("Low risk-adjusted returns - review portfolio allocation")
    
    if risk_metrics.get('max_drawdown', 0) < -20:
        recommendations.append("Significant drawdown risk - consider stop-loss mechanisms")
    
    return recommendations

def generate_earnings_insights(df: pd.DataFrame, earnings_analysis: Dict[str, Any]) -> List[str]:
    """Generate insights from earnings analysis"""
    insights = []
    
    if earnings_analysis.get('positive_surprises', 0) > earnings_analysis.get('negative_surprises', 0):
        insights.append("Earnings season showing more beats than misses - positive corporate sentiment")
    elif earnings_analysis.get('negative_surprises', 0) > earnings_analysis.get('positive_surprises', 0):
        insights.append("More earnings disappointments than beats - concerning corporate performance")
    
    avg_surprise = earnings_analysis.get('avg_surprise', 0)
    if avg_surprise > 5:
        insights.append("Strong average earnings surprise indicates robust corporate performance")
    elif avg_surprise < -5:
        insights.append("Negative average earnings surprise suggests challenging operating environment")
    
    return insights

def create_analysis_summary(metrics: Dict[str, float], insights: List[str]) -> str:
    """Create a summary of the analysis"""
    summary_parts = []
    
    if 'avg_return' in metrics:
        perf_desc = "positive" if metrics['avg_return'] > 0 else "negative"
        summary_parts.append(f"Market showing {perf_desc} performance with {metrics['avg_return']:.2f}% average return")
    
    if 'positive_ratio' in metrics:
        summary_parts.append(f"{metrics['positive_ratio']*100:.1f}% of stocks in positive territory")
    
    if 'return_volatility' in metrics:
        vol_desc = "high" if metrics['return_volatility'] > 3 else "moderate" if metrics['return_volatility'] > 1 else "low"
        summary_parts.append(f"{vol_desc} volatility environment at {metrics['return_volatility']:.2f}%")
    
    summary = ". ".join(summary_parts)
    if insights:
        summary += f". Key insight: {insights[0]}"
    
    return summary

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
