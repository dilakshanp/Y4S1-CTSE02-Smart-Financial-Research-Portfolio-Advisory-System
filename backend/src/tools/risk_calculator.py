"""
Risk Calculator Tool — Student 3 Contribution.

A custom CrewAI tool that computes quantitative risk metrics for portfolio
evaluation using historical price data. Calculates industry-standard
risk measures including volatility, beta, Sharpe ratio, Value-at-Risk,
and maximum drawdown.

Features:
    - Annualized volatility (standard deviation of daily returns)
    - Beta coefficient relative to S&P 500 benchmark
    - Sharpe ratio for risk-adjusted return measurement
    - Value-at-Risk (VaR) at 95% confidence level
    - Maximum drawdown calculation
    - Risk categorization (LOW / MEDIUM / HIGH / CRITICAL)
    - Robust error handling for insufficient data
    - Strict type hints and comprehensive docstrings

Dependencies:
    - yfinance: For fetching historical price data
    - numpy: Numerical computations
    - pandas: Data manipulation and time series handling

Author: Student 3
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

import numpy as np
import pandas as pd
import yfinance as yf
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class RiskCalculatorInput(BaseModel):
    """
    Input schema for the RiskCalculator tool.
    
    Defines and validates the parameters required to calculate
    risk metrics for a portfolio of stock ticker symbols.
    """
    ticker_symbols: str = Field(
        ...,
        description=(
            "Comma-separated stock ticker symbols to calculate risk for "
            "(e.g., 'AAPL,MSFT,GOOGL'). Minimum 1 ticker, maximum 10."
        )
    )
    risk_free_rate: float = Field(
        default=0.05,
        description=(
            "Annual risk-free rate for Sharpe ratio calculation. "
            "Default is 0.05 (5%). Use current Treasury Bill rate for accuracy."
        )
    )
    period: str = Field(
        default="6mo",
        description=(
            "Historical data period for risk calculations. "
            "Longer periods provide more reliable metrics. "
            "Valid: '3mo', '6mo', '1y', '2y'. Default is '6mo'."
        )
    )


class RiskCalculatorTool(BaseTool):
    """
    Computes quantitative risk metrics for portfolio evaluation.
    
    Calculates industry-standard risk measurements using historical
    price data from Yahoo Finance:
    
    - **Volatility**: Annualized standard deviation of daily returns
    - **Beta**: Systematic risk relative to S&P 500 (^GSPC)
    - **Sharpe Ratio**: Risk-adjusted excess return
    - **Value-at-Risk (95%)**: Maximum expected loss at 95% confidence
    - **Max Drawdown**: Largest peak-to-trough decline
    
    Risk categories are assigned based on composite scoring:
    - LOW: Stable, blue-chip-like risk profile
    - MEDIUM: Moderate volatility, acceptable for balanced portfolios
    - HIGH: Elevated risk, suitable for aggressive investors
    - CRITICAL: Extreme risk, speculative territory
    
    Example usage by an agent:
        Input: ticker_symbols="AAPL,MSFT", risk_free_rate=0.05
        Output: JSON with per-ticker risk metrics and portfolio summary
    """
    
    name: str = "Risk Calculator"
    description: str = (
        "Calculates quantitative risk metrics including volatility, beta, "
        "Sharpe ratio, Value-at-Risk (95%), and maximum drawdown for given "
        "stock tickers. Categorizes overall risk as LOW, MEDIUM, HIGH, or "
        "CRITICAL. Use this tool to assess investment risk exposure."
    )
    args_schema: Type[BaseModel] = RiskCalculatorInput

    def _run(
        self,
        ticker_symbols: str,
        risk_free_rate: float = 0.05,
        period: str = "6mo"
    ) -> str:
        """
        Execute the risk calculation operation.
        
        Fetches historical price data and computes comprehensive risk
        metrics for each ticker symbol provided.
        
        Args:
            ticker_symbols: Comma-separated ticker symbols.
            risk_free_rate: Annual risk-free rate (default: 0.05).
            period: Historical data period (default: '6mo').
            
        Returns:
            JSON string containing risk metrics with fields per ticker:
                - ticker: Stock ticker symbol
                - volatility: Annualized volatility
                - beta: Beta coefficient vs S&P 500
                - sharpe_ratio: Risk-adjusted return
                - var_95: Value-at-Risk at 95% confidence
                - max_drawdown: Maximum drawdown percentage
                - risk_category: LOW, MEDIUM, HIGH, or CRITICAL
                - confidence: Confidence level of assessment
                
            Returns an error message string if calculation fails.
        """
        try:
            # Parse and validate ticker symbols
            tickers: List[str] = [
                t.strip().upper() for t in ticker_symbols.split(",")
                if t.strip()
            ]
            
            if not tickers:
                return json.dumps({
                    "error": True,
                    "message": "No valid ticker symbols provided."
                })
            
            if len(tickers) > 10:
                return json.dumps({
                    "error": True,
                    "message": "Maximum 10 tickers allowed per request."
                })

            # Validate period
            valid_periods: List[str] = ["3mo", "6mo", "1y", "2y"]
            if period not in valid_periods:
                period = "6mo"  # Fallback to default

            # Fetch S&P 500 benchmark data
            benchmark_returns: Optional[pd.Series] = self._get_daily_returns(
                "^GSPC", period
            )

            # Calculate risk metrics for each ticker
            results: List[Dict[str, Any]] = []
            errors: List[str] = []
            
            for ticker in tickers:
                try:
                    metrics = self._calculate_ticker_risk(
                        ticker, period, risk_free_rate, benchmark_returns
                    )
                    results.append(metrics)
                except Exception as e:
                    errors.append(f"{ticker}: {str(e)}")
                    results.append({
                        "ticker": ticker,
                        "error": True,
                        "message": str(e),
                    })

            # Calculate portfolio-level summary
            valid_results = [r for r in results if not r.get("error")]
            portfolio_summary = self._calculate_portfolio_summary(
                valid_results
            ) if valid_results else {}

            # Build response
            response: Dict[str, Any] = {
                "error": False,
                "tickers_analyzed": len(results),
                "period": period,
                "risk_free_rate": risk_free_rate,
                "individual_metrics": results,
                "portfolio_summary": portfolio_summary,
                "errors": errors if errors else None,
                "calculated_at": datetime.now().isoformat(),
            }

            return json.dumps(response, indent=2)

        except Exception as e:
            return json.dumps({
                "error": True,
                "message": f"Risk calculation failed: {str(e)}",
            })

    def _get_daily_returns(
        self, ticker: str, period: str
    ) -> Optional[pd.Series]:
        """
        Fetch historical data and calculate daily returns.
        
        Args:
            ticker: Stock ticker symbol.
            period: Historical data period.
            
        Returns:
            Pandas Series of daily percentage returns, or None if unavailable.
        """
        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period=period)
            
            if history.empty or len(history) < 10:
                return None
            
            returns: pd.Series = history["Close"].pct_change().dropna()
            return returns
        except Exception:
            return None

    def _calculate_ticker_risk(
        self,
        ticker: str,
        period: str,
        risk_free_rate: float,
        benchmark_returns: Optional[pd.Series]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive risk metrics for a single ticker.
        
        Args:
            ticker: Stock ticker symbol.
            period: Historical data period.
            risk_free_rate: Annual risk-free rate.
            benchmark_returns: S&P 500 daily returns for beta calculation.
            
        Returns:
            Dictionary containing all risk metrics for the ticker.
            
        Raises:
            ValueError: If insufficient data is available for analysis.
        """
        # Get daily returns
        returns: Optional[pd.Series] = self._get_daily_returns(ticker, period)
        
        if returns is None or len(returns) < 20:
            raise ValueError(
                f"Insufficient price data for '{ticker}'. "
                "Need at least 20 trading days of data."
            )

        # 1. Annualized Volatility
        daily_volatility: float = float(returns.std())
        annualized_volatility: float = daily_volatility * np.sqrt(252)

        # 2. Beta (relative to S&P 500)
        beta: float = self._calculate_beta(returns, benchmark_returns)

        # 3. Sharpe Ratio
        daily_risk_free: float = risk_free_rate / 252
        excess_returns: pd.Series = returns - daily_risk_free
        sharpe_ratio: float = 0.0
        if daily_volatility > 0:
            sharpe_ratio = float(
                (excess_returns.mean() / daily_volatility) * np.sqrt(252)
            )

        # 4. Value-at-Risk (95% confidence)
        var_95: float = float(np.percentile(returns, 5))

        # 5. Maximum Drawdown
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)
        max_drawdown: float = self._calculate_max_drawdown(history["Close"])

        # 6. Risk Category
        risk_category: str = self._categorize_risk(
            annualized_volatility, beta, var_95, max_drawdown
        )

        # 7. Confidence level (based on data sufficiency)
        data_points: int = len(returns)
        confidence: float = min(1.0, data_points / 252)  # Full year = 100%

        return {
            "ticker": ticker,
            "error": False,
            "volatility": round(annualized_volatility, 4),
            "volatility_pct": f"{round(annualized_volatility * 100, 2)}%",
            "beta": round(beta, 4),
            "sharpe_ratio": round(sharpe_ratio, 4),
            "var_95": round(var_95, 4),
            "var_95_pct": f"{round(var_95 * 100, 2)}%",
            "max_drawdown": round(max_drawdown, 4),
            "max_drawdown_pct": f"{round(max_drawdown * 100, 2)}%",
            "risk_category": risk_category,
            "confidence": round(confidence, 2),
            "data_points": data_points,
            "daily_avg_return": round(float(returns.mean()), 6),
            "annualized_return": round(float(returns.mean() * 252), 4),
        }

    @staticmethod
    def _calculate_beta(
        stock_returns: pd.Series,
        benchmark_returns: Optional[pd.Series]
    ) -> float:
        """
        Calculate beta coefficient relative to the benchmark.
        
        Beta measures systematic risk:
        - Beta = 1.0: Moves with the market
        - Beta > 1.0: More volatile than the market
        - Beta < 1.0: Less volatile than the market
        
        Args:
            stock_returns: Daily returns of the stock.
            benchmark_returns: Daily returns of the benchmark (S&P 500).
            
        Returns:
            Beta coefficient as a float. Returns 1.0 if benchmark data unavailable.
        """
        if benchmark_returns is None or benchmark_returns.empty:
            return 1.0  # Default to market beta if benchmark unavailable
        
        # Align the two series by date
        aligned = pd.DataFrame({
            "stock": stock_returns,
            "benchmark": benchmark_returns
        }).dropna()
        
        if len(aligned) < 10:
            return 1.0
        
        covariance: float = float(aligned["stock"].cov(aligned["benchmark"]))
        benchmark_variance: float = float(aligned["benchmark"].var())
        
        if benchmark_variance == 0:
            return 1.0
        
        return covariance / benchmark_variance

    @staticmethod
    def _calculate_max_drawdown(prices: pd.Series) -> float:
        """
        Calculate the maximum drawdown from peak to trough.
        
        Maximum drawdown represents the largest peak-to-trough decline
        in the price series, measuring the worst-case scenario for investors.
        
        Args:
            prices: Series of closing prices.
            
        Returns:
            Maximum drawdown as a negative decimal (e.g., -0.15 for 15% decline).
        """
        if prices.empty:
            return 0.0
        
        cumulative_max: pd.Series = prices.cummax()
        drawdown: pd.Series = (prices - cumulative_max) / cumulative_max
        max_dd: float = float(drawdown.min())
        
        return max_dd

    @staticmethod
    def _categorize_risk(
        volatility: float,
        beta: float,
        var_95: float,
        max_drawdown: float
    ) -> str:
        """
        Categorize overall risk based on composite metric scoring.
        
        Uses a weighted scoring system combining volatility, beta,
        VaR, and max drawdown to determine risk classification.
        
        Args:
            volatility: Annualized volatility.
            beta: Beta coefficient.
            var_95: Value-at-Risk at 95% confidence.
            max_drawdown: Maximum drawdown.
            
        Returns:
            Risk category: 'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'.
        """
        score: float = 0.0
        
        # Volatility scoring (weight: 30%)
        if volatility < 0.15:
            score += 0
        elif volatility < 0.25:
            score += 1
        elif volatility < 0.40:
            score += 2
        else:
            score += 3
        
        # Beta scoring (weight: 25%)
        if beta < 0.8:
            score += 0
        elif beta < 1.2:
            score += 1
        elif beta < 1.5:
            score += 2
        else:
            score += 3
        
        # VaR scoring (weight: 25%)
        if var_95 > -0.02:
            score += 0
        elif var_95 > -0.03:
            score += 1
        elif var_95 > -0.05:
            score += 2
        else:
            score += 3
        
        # Max Drawdown scoring (weight: 20%)
        if max_drawdown > -0.10:
            score += 0
        elif max_drawdown > -0.20:
            score += 1
        elif max_drawdown > -0.35:
            score += 2
        else:
            score += 3
        
        # Classify based on composite score
        if score <= 3:
            return "LOW"
        elif score <= 6:
            return "MEDIUM"
        elif score <= 9:
            return "HIGH"
        else:
            return "CRITICAL"

    @staticmethod
    def _calculate_portfolio_summary(
        metrics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate portfolio-level risk summary from individual ticker metrics.
        
        Args:
            metrics: List of individual ticker risk metric dictionaries.
            
        Returns:
            Dictionary containing portfolio-level risk statistics.
        """
        if not metrics:
            return {}
        
        volatilities = [m["volatility"] for m in metrics if "volatility" in m]
        betas = [m["beta"] for m in metrics if "beta" in m]
        sharpes = [m["sharpe_ratio"] for m in metrics if "sharpe_ratio" in m]
        
        return {
            "avg_volatility": round(
                sum(volatilities) / len(volatilities), 4
            ) if volatilities else 0,
            "avg_beta": round(
                sum(betas) / len(betas), 4
            ) if betas else 0,
            "avg_sharpe": round(
                sum(sharpes) / len(sharpes), 4
            ) if sharpes else 0,
            "highest_risk_ticker": max(
                metrics, key=lambda m: m.get("volatility", 0)
            ).get("ticker", "N/A"),
            "lowest_risk_ticker": min(
                metrics, key=lambda m: m.get("volatility", float("inf"))
            ).get("ticker", "N/A"),
            "tickers_count": len(metrics),
        }
