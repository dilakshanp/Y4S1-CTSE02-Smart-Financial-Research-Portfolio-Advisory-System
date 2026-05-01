"""
Shared Test Fixtures for the Smart Financial Research MAS.

Provides common pytest fixtures including mock data, sample states,
and test utilities shared across all individual test files.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pytest

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state.models import (
    AgentLogEntry,
    MarketData,
    ResearchState,
    RiskMetrics,
    SentimentResult,
)


# ============================================
# Sample Data Fixtures
# ============================================

@pytest.fixture
def sample_tickers() -> List[str]:
    """Provide sample stock ticker symbols."""
    return ["AAPL", "MSFT", "GOOGL"]


@pytest.fixture
def sample_user_query() -> str:
    """Provide a sample user query."""
    return "Analyze AAPL, MSFT, GOOGL for a moderate-risk portfolio"


@pytest.fixture
def sample_market_data() -> List[MarketData]:
    """Provide sample market data for testing."""
    return [
        MarketData(
            ticker="AAPL",
            current_price=175.50,
            price_change_pct=1.25,
            volume=55000000,
            market_cap=2800000000000,
            pe_ratio=28.5,
            week_52_high=199.62,
            week_52_low=124.17,
            historical_prices=[170.0, 172.5, 174.0, 175.5],
        ),
        MarketData(
            ticker="MSFT",
            current_price=420.30,
            price_change_pct=0.85,
            volume=22000000,
            market_cap=3100000000000,
            pe_ratio=36.2,
            week_52_high=468.35,
            week_52_low=309.45,
            historical_prices=[415.0, 417.0, 419.0, 420.3],
        ),
    ]


@pytest.fixture
def sample_sentiment_results() -> List[SentimentResult]:
    """Provide sample sentiment analysis results."""
    return [
        SentimentResult(
            query="AAPL",
            articles_analyzed=5,
            average_sentiment=0.35,
            sentiment_label="BULLISH",
            top_headlines=[
                "Apple Reports Record Q4 Earnings",
                "iPhone Sales Exceed Expectations",
            ],
        ),
        SentimentResult(
            query="MSFT",
            articles_analyzed=5,
            average_sentiment=0.42,
            sentiment_label="BULLISH",
            top_headlines=[
                "Microsoft Cloud Revenue Surges",
                "AI Integration Drives Growth",
            ],
        ),
    ]


@pytest.fixture
def sample_risk_metrics() -> List[RiskMetrics]:
    """Provide sample risk metrics."""
    return [
        RiskMetrics(
            ticker="AAPL",
            volatility=0.22,
            beta=1.15,
            sharpe_ratio=1.45,
            var_95=-0.025,
            max_drawdown=-0.18,
            risk_category="MEDIUM",
            confidence=0.85,
        ),
        RiskMetrics(
            ticker="MSFT",
            volatility=0.19,
            beta=1.05,
            sharpe_ratio=1.62,
            var_95=-0.021,
            max_drawdown=-0.14,
            risk_category="LOW",
            confidence=0.90,
        ),
    ]


@pytest.fixture
def sample_research_state(
    sample_user_query,
    sample_tickers,
    sample_market_data,
    sample_sentiment_results,
    sample_risk_metrics,
) -> ResearchState:
    """Provide a fully populated research state for testing."""
    state = ResearchState(
        user_query=sample_user_query,
        tickers=sample_tickers[:2],  # AAPL, MSFT
        market_data=sample_market_data,
        sentiment_results=sample_sentiment_results,
        risk_metrics=sample_risk_metrics,
        advisory_report="Sample advisory report content for testing.",
        status="completed",
    )
    return state


@pytest.fixture
def sample_market_data_json() -> str:
    """Provide sample market data as JSON (tool output format)."""
    return json.dumps({
        "error": False,
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "current_price": 175.50,
        "previous_close": 173.33,
        "price_change_pct": 1.25,
        "volume": 55000000,
        "market_cap": 2800000000000,
        "pe_ratio": 28.5,
        "week_52_high": 199.62,
        "week_52_low": 124.17,
        "historical_prices": [170.0, 172.5, 174.0, 175.5],
        "data_points": 4,
        "period": "1mo",
        "currency": "USD",
        "fetched_at": datetime.now().isoformat(),
    })


@pytest.fixture
def sample_sentiment_json() -> str:
    """Provide sample sentiment analysis as JSON (tool output format)."""
    return json.dumps({
        "error": False,
        "query": "AAPL",
        "articles_analyzed": 5,
        "average_sentiment": 0.35,
        "sentiment_label": "BULLISH",
        "sentiment_distribution": {
            "bullish": 3,
            "neutral": 1,
            "bearish": 1,
        },
        "articles": [
            {
                "title": "Apple Reports Record Earnings",
                "sentiment_score": 0.65,
                "sentiment_label": "BULLISH",
            }
        ],
        "top_headlines": ["Apple Reports Record Earnings"],
        "analyzed_at": datetime.now().isoformat(),
    })


@pytest.fixture
def sample_risk_json() -> str:
    """Provide sample risk metrics as JSON (tool output format)."""
    return json.dumps({
        "error": False,
        "tickers_analyzed": 2,
        "period": "6mo",
        "risk_free_rate": 0.05,
        "individual_metrics": [
            {
                "ticker": "AAPL",
                "error": False,
                "volatility": 0.22,
                "beta": 1.15,
                "sharpe_ratio": 1.45,
                "var_95": -0.025,
                "max_drawdown": -0.18,
                "risk_category": "MEDIUM",
                "confidence": 0.85,
            }
        ],
        "portfolio_summary": {
            "avg_volatility": 0.205,
            "avg_beta": 1.10,
            "avg_sharpe": 1.535,
        },
        "calculated_at": datetime.now().isoformat(),
    })


@pytest.fixture
def tmp_reports_dir(tmp_path) -> Path:
    """Provide a temporary reports directory for testing."""
    reports = tmp_path / "reports"
    reports.mkdir()
    return reports


@pytest.fixture
def tmp_logs_dir(tmp_path) -> Path:
    """Provide a temporary logs directory for testing."""
    logs = tmp_path / "logs"
    logs.mkdir()
    return logs


@pytest.fixture
def tmp_db_path(tmp_path) -> Path:
    """Provide a temporary database path for testing."""
    return tmp_path / "test_db.sqlite"
