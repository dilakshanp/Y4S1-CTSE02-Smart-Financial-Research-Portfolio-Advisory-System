"""
Test Suite for the Coordinator Agent & Market Data Fetcher Tool.

Student 1 Contribution.

Tests cover:
    - MarketDataFetcher tool: data accuracy, error handling, edge cases
    - Coordinator agent: input parsing, research plan structure
    - Property-based testing: output structure validation
    - LLM-as-Judge: output coherence evaluation
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_harness import JSONValidator, LLMJudge, PerformanceBenchmark
from src.tools.market_data_fetcher import MarketDataFetcherTool


# ============================================
# MarketDataFetcher Tool Tests
# ============================================

class TestMarketDataFetcherTool:
    """Test suite for the Market Data Fetcher tool."""

    @pytest.fixture
    def tool(self) -> MarketDataFetcherTool:
        """Create a MarketDataFetcher tool instance."""
        return MarketDataFetcherTool()

    def test_fetch_valid_ticker(self, tool):
        """Test fetching data for a valid, well-known ticker (AAPL)."""
        result_json = tool._run(ticker_symbol="AAPL", period="1mo")
        data = JSONValidator.assert_valid_json(result_json)
        JSONValidator.assert_no_error(data)
        
        # Verify required fields
        JSONValidator.assert_has_keys(data, [
            "ticker", "current_price", "volume",
            "historical_prices", "fetched_at"
        ])
        
        # Verify data types and ranges
        assert data["ticker"] == "AAPL"
        assert isinstance(data["current_price"], (int, float))
        assert data["current_price"] > 0, "Price must be positive"
        assert isinstance(data["volume"], int)
        assert data["volume"] >= 0, "Volume must be non-negative"
        assert isinstance(data["historical_prices"], list)
        assert len(data["historical_prices"]) > 0, "Should have historical data"

    def test_fetch_invalid_ticker(self, tool):
        """Test handling of an invalid ticker symbol."""
        result_json = tool._run(ticker_symbol="ZZZZZ99", period="1mo")
        data = JSONValidator.assert_valid_json(result_json)
        
        # Should either return an error or empty data
        # (yfinance behavior varies)
        assert data.get("error") is True or data.get("current_price", 0) == 0

    def test_fetch_invalid_period(self, tool):
        """Test handling of an invalid period parameter."""
        result_json = tool._run(ticker_symbol="AAPL", period="invalid_period")
        data = JSONValidator.assert_valid_json(result_json)
        assert data.get("error") is True

    def test_fetch_empty_ticker(self, tool):
        """Test handling of an empty ticker symbol."""
        result_json = tool._run(ticker_symbol="", period="1mo")
        data = JSONValidator.assert_valid_json(result_json)
        assert data.get("error") is True

    def test_fetch_ticker_with_whitespace(self, tool):
        """Test that whitespace in ticker symbols is handled."""
        result_json = tool._run(ticker_symbol="  aapl  ", period="1mo")
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            assert data["ticker"] == "AAPL", "Ticker should be uppercase and trimmed"

    def test_price_change_calculation(self, tool):
        """Test that price change percentage is calculated correctly."""
        result_json = tool._run(ticker_symbol="MSFT", period="1mo")
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            # Price change should be a reasonable percentage
            pct = data.get("price_change_pct", 0)
            assert isinstance(pct, (int, float))
            JSONValidator.assert_value_in_range(
                pct, -50.0, 50.0, "price_change_pct"
            )

    def test_historical_prices_are_positive(self, tool):
        """Property: All historical prices must be positive."""
        result_json = tool._run(ticker_symbol="GOOGL", period="1mo")
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            for price in data.get("historical_prices", []):
                assert price > 0, f"Historical price {price} is not positive"

    def test_multiple_period_options(self, tool):
        """Test that different period options work correctly."""
        for period in ["5d", "1mo", "3mo"]:
            result_json = tool._run(ticker_symbol="AAPL", period=period)
            data = JSONValidator.assert_valid_json(result_json)
            
            if not data.get("error"):
                assert data.get("period") == period

    def test_tool_performance(self, tool):
        """Test that tool execution completes within reasonable time."""
        result, duration = PerformanceBenchmark.time_execution(
            tool._run, ticker_symbol="AAPL", period="5d"
        )
        
        # Should complete within 30 seconds (network dependent)
        PerformanceBenchmark.assert_performance(
            duration, 30000, "MarketDataFetcher"
        )

    def test_output_coherence(self, tool):
        """LLM-as-Judge: Evaluate output coherence."""
        result_json = tool._run(ticker_symbol="AAPL", period="1mo")
        
        evaluation = LLMJudge.evaluate_coherence(result_json, min_length=100)
        assert evaluation["passed"], (
            f"Output coherence check failed: {evaluation['issues']}"
        )


# ============================================
# Coordinator Agent Design Tests  
# ============================================

class TestCoordinatorAgentDesign:
    """Test the Coordinator agent's configuration and design."""

    def test_agent_creation(self):
        """Test that the Coordinator agent is created correctly."""
        from src.agents.coordinator import create_coordinator_agent
        
        agent = create_coordinator_agent()
        
        assert agent.role == "Research Coordinator"
        assert "orchestrate" in agent.goal.lower() or "coordinate" in agent.goal.lower()
        assert agent.tools is not None
        assert len(agent.tools) >= 1

    def test_agent_has_market_data_tool(self):
        """Test that Coordinator has the MarketDataFetcher tool."""
        from src.agents.coordinator import create_coordinator_agent
        
        agent = create_coordinator_agent()
        
        tool_names = [tool.name for tool in agent.tools]
        assert "Market Data Fetcher" in tool_names

    def test_agent_backstory_quality(self):
        """Test that the agent backstory is substantive."""
        from src.agents.coordinator import create_coordinator_agent
        
        agent = create_coordinator_agent()
        
        assert len(agent.backstory) > 100, "Backstory should be detailed"
        assert "financial" in agent.backstory.lower() or "research" in agent.backstory.lower()
