"""
Global State Models for the Smart Financial Research MAS.

This module defines Pydantic models that represent the global state
passed between agents throughout the research pipeline. Using Pydantic
ensures type safety, validation, and serialization at every agent handoff.

State Flow:
    1. Coordinator creates ResearchState with user_query and tickers
    2. Market Analyst populates market_data and sentiment_results
    3. Risk Specialist populates risk_metrics
    4. Portfolio Advisor reads all fields and generates advisory_report
    5. Each agent appends to agent_logs for observability
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class MarketData(BaseModel):
    """
    Market data collected by the Market Research Analyst agent.
    
    Contains current pricing, volume, and key financial metrics
    for a single stock ticker symbol.
    """
    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL')")
    current_price: float = Field(..., description="Current stock price in USD")
    price_change_pct: float = Field(
        ..., description="Price change percentage over the analysis period"
    )
    volume: int = Field(..., description="Trading volume")
    market_cap: Optional[float] = Field(
        None, description="Market capitalization in USD"
    )
    pe_ratio: Optional[float] = Field(
        None, description="Price-to-Earnings ratio"
    )
    week_52_high: Optional[float] = Field(
        None, description="52-week high price"
    )
    week_52_low: Optional[float] = Field(
        None, description="52-week low price"
    )
    historical_prices: List[float] = Field(
        default_factory=list,
        description="List of historical closing prices for the analysis period"
    )
    data_source: str = Field(
        default="yfinance", description="Source of the market data"
    )
    fetched_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when data was fetched"
    )


class SentimentResult(BaseModel):
    """
    Sentiment analysis results from the News Sentiment Analyzer tool.
    
    Contains aggregated sentiment scores and individual article details
    for a financial news search query.
    """
    query: str = Field(..., description="Original search query")
    articles_analyzed: int = Field(
        ..., description="Number of articles analyzed"
    )
    average_sentiment: float = Field(
        ...,
        description="Average sentiment score from -1.0 (bearish) to 1.0 (bullish)",
        ge=-1.0,
        le=1.0
    )
    sentiment_label: str = Field(
        ...,
        description="Aggregated sentiment label: BEARISH, NEUTRAL, or BULLISH"
    )
    top_headlines: List[str] = Field(
        default_factory=list,
        description="Top news headlines analyzed"
    )
    article_sentiments: List[Dict] = Field(
        default_factory=list,
        description="Individual article sentiment details"
    )
    analyzed_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when analysis was performed"
    )


class RiskMetrics(BaseModel):
    """
    Risk assessment metrics computed by the Risk Calculator tool.
    
    Contains quantitative risk measurements for portfolio evaluation
    including volatility, beta, Sharpe ratio, and Value-at-Risk.
    """
    ticker: str = Field(..., description="Stock ticker symbol")
    volatility: float = Field(
        ..., description="Annualized volatility (standard deviation of returns)"
    )
    beta: float = Field(
        ..., description="Beta coefficient relative to S&P 500 benchmark"
    )
    sharpe_ratio: float = Field(
        ..., description="Risk-adjusted return (Sharpe ratio)"
    )
    var_95: float = Field(
        ..., description="Value-at-Risk at 95% confidence level"
    )
    max_drawdown: float = Field(
        ..., description="Maximum drawdown percentage"
    )
    risk_category: str = Field(
        ...,
        description="Risk classification: LOW, MEDIUM, HIGH, or CRITICAL"
    )
    confidence: float = Field(
        ...,
        description="Confidence level of the risk assessment (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    calculated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when metrics were calculated"
    )


class AgentLogEntry(BaseModel):
    """
    Log entry for tracking individual agent actions.
    
    Used for observability and tracing of the agent execution pipeline.
    """
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the event occurred"
    )
    agent_name: str = Field(..., description="Name of the agent")
    action_type: str = Field(
        ...,
        description="Type of action: THINK, TOOL_CALL, TOOL_RESULT, OUTPUT, ERROR"
    )
    input_data: Optional[str] = Field(
        None, description="Input data for the action (truncated)"
    )
    output_data: Optional[str] = Field(
        None, description="Output data from the action (truncated)"
    )
    tool_name: Optional[str] = Field(
        None, description="Name of the tool used (if applicable)"
    )
    duration_ms: Optional[float] = Field(
        None, description="Duration of the action in milliseconds"
    )
    success: bool = Field(
        default=True, description="Whether the action was successful"
    )


class ResearchState(BaseModel):
    """
    Global state object passed between all agents in the research pipeline.
    
    This is the central data structure that maintains context across the
    entire multi-agent workflow. Each agent reads from and writes to
    specific fields, ensuring data flows correctly through the pipeline.
    
    State Flow:
        Coordinator → Market Analyst → Risk Specialist → Portfolio Advisor
    """
    # Identification
    query_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this research query"
    )
    
    # Input
    user_query: str = Field(
        ..., description="Original user query string"
    )
    tickers: List[str] = Field(
        default_factory=list,
        description="List of stock ticker symbols to analyze"
    )
    
    # Metadata
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the research was initiated"
    )
    
    # Coordinator Output
    research_plan: Optional[Dict] = Field(
        None,
        description="Structured research plan created by the Coordinator"
    )
    
    # Market Analyst Output
    market_data: Optional[List[MarketData]] = Field(
        None,
        description="Market data collected for each ticker"
    )
    sentiment_results: Optional[List[SentimentResult]] = Field(
        None,
        description="Sentiment analysis results for each ticker"
    )
    
    # Risk Specialist Output
    risk_metrics: Optional[List[RiskMetrics]] = Field(
        None,
        description="Risk metrics calculated for each ticker"
    )
    
    # Portfolio Advisor Output
    advisory_report: Optional[str] = Field(
        None,
        description="Final advisory report in markdown format"
    )
    report_path: Optional[str] = Field(
        None,
        description="File path where the report was saved"
    )
    
    # Observability
    agent_logs: List[AgentLogEntry] = Field(
        default_factory=list,
        description="Ordered list of agent action logs"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of errors encountered during execution"
    )
    
    # Status
    status: str = Field(
        default="initialized",
        description="Current pipeline status: initialized, in_progress, completed, failed"
    )

    def add_log(
        self,
        agent_name: str,
        action_type: str,
        input_data: Optional[str] = None,
        output_data: Optional[str] = None,
        tool_name: Optional[str] = None,
        duration_ms: Optional[float] = None,
        success: bool = True
    ) -> None:
        """Add a log entry to the agent logs."""
        entry = AgentLogEntry(
            agent_name=agent_name,
            action_type=action_type,
            input_data=input_data[:500] if input_data else None,
            output_data=output_data[:500] if output_data else None,
            tool_name=tool_name,
            duration_ms=duration_ms,
            success=success
        )
        self.agent_logs.append(entry)

    def add_error(self, error_message: str) -> None:
        """Record an error that occurred during execution."""
        self.errors.append(f"[{datetime.now().isoformat()}] {error_message}")

    def get_summary(self) -> Dict:
        """Get a summary of the current research state."""
        return {
            "query_id": self.query_id,
            "user_query": self.user_query,
            "tickers": self.tickers,
            "status": self.status,
            "market_data_count": len(self.market_data) if self.market_data else 0,
            "sentiment_count": len(self.sentiment_results) if self.sentiment_results else 0,
            "risk_metrics_count": len(self.risk_metrics) if self.risk_metrics else 0,
            "has_report": self.advisory_report is not None,
            "total_logs": len(self.agent_logs),
            "total_errors": len(self.errors),
        }
