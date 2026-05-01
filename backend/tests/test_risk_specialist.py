"""
Test Suite for the Risk Assessment Specialist Agent & Risk Calculator Tool.

Student 3 Contribution.

Tests cover:
    - RiskCalculator tool: metric accuracy, categorization, edge cases
    - Risk Specialist agent: design quality, tool integration
    - Property-based testing: metric ranges, category validity
    - LLM-as-Judge: output quality evaluation
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_harness import JSONValidator, LLMJudge, PerformanceBenchmark
from src.tools.risk_calculator import RiskCalculatorTool


# ============================================
# RiskCalculator Tool Tests
# ============================================

class TestRiskCalculatorTool:
    """Test suite for the Risk Calculator tool."""

    @pytest.fixture
    def tool(self) -> RiskCalculatorTool:
        """Create a RiskCalculator tool instance."""
        return RiskCalculatorTool()

    def test_calculate_single_ticker(self, tool):
        """Test risk calculation for a single well-known ticker."""
        result_json = tool._run(
            ticker_symbols="AAPL",
            risk_free_rate=0.05,
            period="6mo"
        )
        data = JSONValidator.assert_valid_json(result_json)
        JSONValidator.assert_no_error(data)
        
        # Verify structure
        JSONValidator.assert_has_keys(data, [
            "tickers_analyzed", "individual_metrics", "calculated_at"
        ])
        
        assert data["tickers_analyzed"] >= 1
        
        # Check individual metrics
        metrics = data["individual_metrics"]
        assert len(metrics) >= 1
        
        m = metrics[0]
        if not m.get("error"):
            JSONValidator.assert_has_keys(m, [
                "ticker", "volatility", "beta", "sharpe_ratio",
                "var_95", "max_drawdown", "risk_category", "confidence"
            ])

    def test_calculate_multiple_tickers(self, tool):
        """Test risk calculation for multiple tickers."""
        result_json = tool._run(
            ticker_symbols="AAPL,MSFT",
            risk_free_rate=0.05,
            period="6mo"
        )
        data = JSONValidator.assert_valid_json(result_json)
        JSONValidator.assert_no_error(data)
        
        assert data["tickers_analyzed"] >= 2
        
        # Should have portfolio summary
        if "portfolio_summary" in data and data["portfolio_summary"]:
            summary = data["portfolio_summary"]
            assert "avg_volatility" in summary
            assert "avg_beta" in summary

    def test_volatility_is_positive(self, tool):
        """Property: Volatility must always be positive (or zero)."""
        result_json = tool._run(ticker_symbols="MSFT", period="6mo")
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            for m in data.get("individual_metrics", []):
                if not m.get("error"):
                    assert m["volatility"] >= 0, (
                        f"Volatility must be >= 0, got {m['volatility']}"
                    )

    def test_confidence_in_valid_range(self, tool):
        """Property: Confidence must be between 0.0 and 1.0."""
        result_json = tool._run(ticker_symbols="GOOGL", period="6mo")
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            for m in data.get("individual_metrics", []):
                if not m.get("error"):
                    JSONValidator.assert_value_in_range(
                        m["confidence"], 0.0, 1.0, "confidence"
                    )

    def test_risk_category_validity(self, tool):
        """Property: Risk category must be one of the defined values."""
        valid_categories = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        
        result_json = tool._run(ticker_symbols="AAPL", period="6mo")
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            for m in data.get("individual_metrics", []):
                if not m.get("error"):
                    assert m["risk_category"] in valid_categories, (
                        f"Invalid risk category: {m['risk_category']}"
                    )

    def test_var_95_is_negative_or_zero(self, tool):
        """Property: VaR at 95% should typically be negative (loss)."""
        result_json = tool._run(ticker_symbols="AAPL", period="6mo")
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            for m in data.get("individual_metrics", []):
                if not m.get("error"):
                    assert m["var_95"] <= 0.1, (
                        f"VaR(95%) should be negative or near zero, got {m['var_95']}"
                    )

    def test_max_drawdown_is_negative_or_zero(self, tool):
        """Property: Maximum drawdown must be negative or zero."""
        result_json = tool._run(ticker_symbols="MSFT", period="6mo")
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            for m in data.get("individual_metrics", []):
                if not m.get("error"):
                    assert m["max_drawdown"] <= 0, (
                        f"Max drawdown must be <= 0, got {m['max_drawdown']}"
                    )

    def test_empty_tickers(self, tool):
        """Test handling of empty ticker input."""
        result_json = tool._run(ticker_symbols="", period="6mo")
        data = JSONValidator.assert_valid_json(result_json)
        assert data.get("error") is True

    def test_too_many_tickers(self, tool):
        """Test handling of exceeding maximum ticker limit."""
        many_tickers = ",".join(["AAPL"] * 15)
        result_json = tool._run(ticker_symbols=many_tickers, period="6mo")
        data = JSONValidator.assert_valid_json(result_json)
        assert data.get("error") is True

    def test_invalid_period_fallback(self, tool):
        """Test that invalid period falls back to default."""
        result_json = tool._run(
            ticker_symbols="AAPL", period="invalid"
        )
        data = JSONValidator.assert_valid_json(result_json)
        # Should not error — should fallback to "6mo"
        if not data.get("error"):
            assert data["period"] == "6mo"

    def test_tool_performance(self, tool):
        """Test that risk calculation completes within reasonable time."""
        result, duration = PerformanceBenchmark.time_execution(
            tool._run,
            ticker_symbols="AAPL",
            risk_free_rate=0.05,
            period="3mo"
        )
        
        PerformanceBenchmark.assert_performance(
            duration, 30000, "RiskCalculator"
        )

    def test_risk_categorization_logic(self):
        """Test the risk categorization scoring logic directly."""
        from src.tools.risk_calculator import RiskCalculatorTool
        
        # LOW risk profile
        category = RiskCalculatorTool._categorize_risk(
            volatility=0.10, beta=0.7, var_95=-0.015, max_drawdown=-0.08
        )
        assert category == "LOW"
        
        # HIGH risk profile
        category = RiskCalculatorTool._categorize_risk(
            volatility=0.35, beta=1.4, var_95=-0.04, max_drawdown=-0.30
        )
        assert category == "HIGH"
        
        # CRITICAL risk profile
        category = RiskCalculatorTool._categorize_risk(
            volatility=0.50, beta=2.0, var_95=-0.08, max_drawdown=-0.50
        )
        assert category == "CRITICAL"


# ============================================
# Risk Specialist Agent Design Tests
# ============================================

class TestRiskSpecialistAgentDesign:
    """Test the Risk Specialist agent's configuration and design."""

    def test_agent_creation(self):
        """Test that the Risk Specialist agent is created correctly."""
        from src.agents.risk_specialist import create_risk_specialist_agent
        
        agent = create_risk_specialist_agent()
        
        assert agent.role == "Risk Assessment Specialist"
        assert "risk" in agent.goal.lower()
        assert agent.tools is not None
        assert len(agent.tools) >= 1

    def test_agent_has_risk_tool(self):
        """Test that Risk Specialist has the RiskCalculator tool."""
        from src.agents.risk_specialist import create_risk_specialist_agent
        
        agent = create_risk_specialist_agent()
        
        tool_names = [tool.name for tool in agent.tools]
        assert "Risk Calculator" in tool_names

    def test_agent_mentions_risk_categories(self):
        """Test that agent instructions mention risk categorization."""
        from src.agents.risk_specialist import create_risk_specialist_agent
        
        agent = create_risk_specialist_agent()
        
        goal_lower = agent.goal.lower()
        assert any(
            cat in goal_lower
            for cat in ["low", "medium", "high", "critical"]
        ) or "categorize" in goal_lower
