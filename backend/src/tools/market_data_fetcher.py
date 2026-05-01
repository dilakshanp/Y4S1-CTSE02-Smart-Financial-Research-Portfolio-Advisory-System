"""
Market Data Fetcher Tool — Student 1 Contribution.

A custom CrewAI tool that fetches real-time and historical stock market data
using the Yahoo Finance (yfinance) library. This tool provides agents with
access to current pricing, volume, financial metrics, and historical price
data for any publicly traded stock.

Features:
    - Real-time stock price and volume data
    - Key financial metrics (P/E ratio, market cap, 52-week range)
    - Historical price data for trend analysis
    - Robust error handling for invalid tickers and network failures
    - Strict type hints and comprehensive docstrings

Dependencies:
    - yfinance: Yahoo Finance market data API (free, no key required)

Author: Student 1
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

import yfinance as yf
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class MarketDataFetcherInput(BaseModel):
    """
    Input schema for the MarketDataFetcher tool.
    
    Defines and validates the parameters required to fetch
    market data for a specific stock ticker symbol.
    """
    ticker_symbol: str = Field(
        ...,
        description=(
            "Stock ticker symbol to fetch data for (e.g., 'AAPL' for Apple Inc., "
            "'MSFT' for Microsoft, 'GOOGL' for Alphabet)."
        )
    )
    period: str = Field(
        default="1mo",
        description=(
            "Historical data period to fetch. Valid values: "
            "'1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'. "
            "Default is '1mo' (one month)."
        )
    )


class MarketDataFetcherTool(BaseTool):
    """
    Fetches real-time stock market data including price, volume,
    and key financial metrics for a given ticker symbol.
    
    This tool connects to Yahoo Finance to retrieve:
    - Current stock price and daily price change
    - Trading volume and market capitalization
    - Price-to-Earnings (P/E) ratio
    - 52-week high and low prices
    - Historical closing prices for the specified period
    
    The tool returns a JSON string with all gathered metrics,
    or a descriptive error message if the data cannot be fetched.
    
    Example usage by an agent:
        Input: ticker_symbol="AAPL", period="1mo"
        Output: JSON with price data, volume, metrics, and history
    """
    
    name: str = "Market Data Fetcher"
    description: str = (
        "Fetches real-time stock market data including current price, volume, "
        "market cap, P/E ratio, 52-week range, and historical prices for a "
        "given stock ticker symbol. Use this tool to gather financial data "
        "about any publicly traded company."
    )
    args_schema: Type[BaseModel] = MarketDataFetcherInput

    def _run(self, ticker_symbol: str, period: str = "1mo") -> str:
        """
        Execute the market data fetch operation.
        
        Connects to Yahoo Finance API via the yfinance library to retrieve
        comprehensive market data for the specified ticker symbol.
        
        Args:
            ticker_symbol: Stock ticker symbol (e.g., 'AAPL').
            period: Historical data period (default: '1mo').
            
        Returns:
            JSON string containing market data with fields:
                - ticker: The stock ticker symbol
                - current_price: Latest stock price
                - previous_close: Previous day's closing price
                - price_change_pct: Percentage change from previous close
                - volume: Current trading volume
                - market_cap: Market capitalization
                - pe_ratio: Price-to-Earnings ratio
                - week_52_high: 52-week high price
                - week_52_low: 52-week low price
                - historical_prices: List of historical closing prices
                - data_points: Number of historical data points
                - period: The data period requested
                - fetched_at: Timestamp of data retrieval
                
            Returns an error message string if the fetch fails.
        """
        try:
            # Sanitize and validate ticker symbol
            ticker_clean: str = ticker_symbol.strip().upper()
            if not ticker_clean or not ticker_clean.isalpha():
                return json.dumps({
                    "error": True,
                    "message": f"Invalid ticker symbol: '{ticker_symbol}'. "
                               "Please provide a valid stock ticker (e.g., 'AAPL')."
                })

            # Validate period
            valid_periods: List[str] = [
                "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"
            ]
            if period not in valid_periods:
                return json.dumps({
                    "error": True,
                    "message": f"Invalid period: '{period}'. "
                               f"Valid periods: {', '.join(valid_periods)}"
                })

            # Fetch stock data
            stock: yf.Ticker = yf.Ticker(ticker_clean)
            info: Dict[str, Any] = stock.info

            # Validate that we got meaningful data
            if not info or info.get("trailingPegRatio") is None and info.get("currentPrice") is None:
                # Check if the ticker exists by trying to get history
                hist = stock.history(period="5d")
                if hist.empty:
                    return json.dumps({
                        "error": True,
                        "message": f"No data found for ticker '{ticker_clean}'. "
                                   "Please verify the ticker symbol is correct."
                    })

            # Fetch historical data
            history = stock.history(period=period)
            historical_prices: List[float] = []
            if not history.empty:
                historical_prices = [
                    round(float(price), 2) for price in history["Close"].tolist()
                ]

            # Extract current price with fallback
            current_price: float = float(
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or (historical_prices[-1] if historical_prices else 0)
            )
            
            # Calculate price change
            previous_close: float = float(info.get("previousClose", 0))
            price_change_pct: float = 0.0
            if previous_close > 0:
                price_change_pct = round(
                    ((current_price - previous_close) / previous_close) * 100, 2
                )

            # Build result dictionary
            result: Dict[str, Any] = {
                "error": False,
                "ticker": ticker_clean,
                "company_name": info.get("longName", info.get("shortName", ticker_clean)),
                "current_price": round(current_price, 2),
                "previous_close": round(previous_close, 2),
                "price_change_pct": price_change_pct,
                "volume": int(info.get("volume", 0)),
                "market_cap": info.get("marketCap"),
                "pe_ratio": (
                    round(float(info.get("trailingPE", 0)), 2)
                    if info.get("trailingPE") else None
                ),
                "forward_pe": (
                    round(float(info.get("forwardPE", 0)), 2)
                    if info.get("forwardPE") else None
                ),
                "week_52_high": (
                    round(float(info.get("fiftyTwoWeekHigh", 0)), 2)
                    if info.get("fiftyTwoWeekHigh") else None
                ),
                "week_52_low": (
                    round(float(info.get("fiftyTwoWeekLow", 0)), 2)
                    if info.get("fiftyTwoWeekLow") else None
                ),
                "dividend_yield": (
                    round(float(info.get("dividendYield", 0)) * 100, 2)
                    if info.get("dividendYield") else None
                ),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "historical_prices": historical_prices,
                "data_points": len(historical_prices),
                "period": period,
                "currency": info.get("currency", "USD"),
                "fetched_at": datetime.now().isoformat(),
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({
                "error": True,
                "message": f"Failed to fetch market data for '{ticker_symbol}': {str(e)}",
                "ticker": ticker_symbol,
            })
