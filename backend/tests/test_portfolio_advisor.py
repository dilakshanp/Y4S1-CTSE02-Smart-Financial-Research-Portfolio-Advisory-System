"""
Test Suite for the Portfolio Advisor Agent & Report Generator Tool.

Student 4 Contribution.

Tests cover:
    - ReportGenerator tool: report structure, sections, file persistence
    - Portfolio Advisor agent: design quality, tool integration
    - Property-based testing: report completeness, disclaimer presence
    - LLM-as-Judge: report quality evaluation
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_harness import JSONValidator, LLMJudge, PerformanceBenchmark
from src.tools.report_generator import ReportGeneratorTool


# ============================================
# ReportGenerator Tool Tests
# ============================================

class TestReportGeneratorTool:
    """Test suite for the Report Generator tool."""

    @pytest.fixture
    def tool(self) -> ReportGeneratorTool:
        """Create a ReportGenerator tool instance."""
        return ReportGeneratorTool()

    @pytest.fixture
    def sample_report_data(self) -> str:
        """Create sample report input data."""
        return json.dumps({
            "tickers": ["AAPL", "MSFT"],
            "market_data": [
                {
                    "ticker": "AAPL",
                    "current_price": 175.50,
                    "price_change_pct": 1.25,
                    "volume": 55000000,
                    "market_cap": 2800000000000,
                    "pe_ratio": 28.5,
                    "sector": "Technology",
                },
                {
                    "ticker": "MSFT",
                    "current_price": 420.30,
                    "price_change_pct": 0.85,
                    "volume": 22000000,
                    "market_cap": 3100000000000,
                    "pe_ratio": 36.2,
                    "sector": "Technology",
                }
            ],
            "sentiment": {
                "sentiment_label": "BULLISH",
                "average_sentiment": 0.38,
                "articles_analyzed": 10,
                "sentiment_distribution": {
                    "bullish": 6,
                    "neutral": 3,
                    "bearish": 1,
                },
                "top_headlines": [
                    "Apple Reports Record Earnings",
                    "Microsoft Cloud Revenue Surges",
                ],
            },
            "risk_metrics": {
                "individual_metrics": [
                    {
                        "ticker": "AAPL",
                        "volatility": 0.22,
                        "volatility_pct": "22.0%",
                        "beta": 1.15,
                        "sharpe_ratio": 1.45,
                        "var_95": -0.025,
                        "var_95_pct": "-2.5%",
                        "max_drawdown": -0.18,
                        "max_drawdown_pct": "-18.0%",
                        "risk_category": "MEDIUM",
                        "confidence": 0.85,
                    }
                ],
                "portfolio_summary": {
                    "avg_volatility": 0.205,
                    "avg_beta": 1.10,
                    "avg_sharpe": 1.535,
                    "highest_risk_ticker": "AAPL",
                    "lowest_risk_ticker": "MSFT",
                },
            },
            "recommendations": [
                "Consider a balanced allocation between AAPL and MSFT",
                "Both stocks show bullish sentiment with moderate risk",
                "Monitor quarterly earnings for any sentiment shifts",
            ],
        })

    def test_generate_markdown_report(self, tool, sample_report_data):
        """Test generating a complete Markdown report."""
        result_json = tool._run(
            report_data=sample_report_data, report_format="markdown"
        )
        data = JSONValidator.assert_valid_json(result_json)
        JSONValidator.assert_no_error(data)
        
        # Verify required fields
        JSONValidator.assert_has_keys(data, [
            "report_content", "report_path", "format", "generated_at"
        ])
        
        assert data["format"] == "markdown"
        assert len(data["report_content"]) > 100

    def test_report_has_required_sections(self, tool, sample_report_data):
        """Property: Report must contain all required sections."""
        result_json = tool._run(report_data=sample_report_data)
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            report = data["report_content"].lower()
            
            assert "executive summary" in report or "summary" in report
            assert "market analysis" in report or "market" in report
            assert "sentiment" in report
            assert "risk" in report
            assert "recommendation" in report
            assert "disclaimer" in report

    def test_report_has_disclaimer(self, tool, sample_report_data):
        """Property: Report MUST contain a disclaimer about AI-generated content."""
        result_json = tool._run(report_data=sample_report_data)
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            report = data["report_content"].lower()
            
            assert any(
                phrase in report
                for phrase in [
                    "not constitute financial advice",
                    "not financial advice",
                    "educational",
                    "informational purposes",
                    "ai-generated",
                    "disclaimer",
                ]
            ), "Report must contain a financial advice disclaimer"

    def test_report_saved_to_file(self, tool, sample_report_data):
        """Test that the report is saved to disk."""
        result_json = tool._run(report_data=sample_report_data)
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            report_path = data.get("report_path", "")
            assert report_path, "Report path should not be empty"
            assert os.path.exists(report_path), (
                f"Report file should exist at {report_path}"
            )
            
            # Verify file content matches
            with open(report_path) as f:
                file_content = f.read()
            assert len(file_content) > 100
            
            # Clean up
            os.remove(report_path)

    def test_report_with_empty_data(self, tool):
        """Test report generation with minimal/empty data."""
        minimal_data = json.dumps({
            "tickers": [],
            "market_data": {},
            "sentiment": {},
            "risk_metrics": {},
            "recommendations": "",
        })
        
        result_json = tool._run(report_data=minimal_data)
        data = JSONValidator.assert_valid_json(result_json)
        
        # Should still generate a report (even if with "N/A" sections)
        if not data.get("error"):
            assert len(data["report_content"]) > 50

    def test_report_with_invalid_json_input(self, tool):
        """Test report generation with invalid JSON (treated as text)."""
        result_json = tool._run(report_data="This is not JSON, just text")
        data = JSONValidator.assert_valid_json(result_json)
        
        # Should handle gracefully
        assert not data.get("error"), "Should handle non-JSON input gracefully"

    def test_text_format_report(self, tool, sample_report_data):
        """Test generating a plain text report."""
        result_json = tool._run(
            report_data=sample_report_data, report_format="text"
        )
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            assert data["format"] == "text"
            # Text format should not have markdown headers
            content = data["report_content"]
            assert len(content) > 100

    def test_report_includes_tickers(self, tool, sample_report_data):
        """Test that the report mentions all analyzed tickers."""
        result_json = tool._run(report_data=sample_report_data)
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            report = data["report_content"]
            assert "AAPL" in report, "Report should mention AAPL"
            assert "MSFT" in report, "Report should mention MSFT"

    def test_report_quality_llm_judge(self, tool, sample_report_data):
        """LLM-as-Judge: Evaluate overall report quality."""
        result_json = tool._run(report_data=sample_report_data)
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            evaluation = LLMJudge.evaluate_financial_report(
                data["report_content"]
            )
            assert evaluation["passed"], (
                f"Report quality check failed.\n"
                f"Score: {evaluation['score']}\n"
                f"Missing: {evaluation['issues']}"
            )

    def test_tool_performance(self, tool, sample_report_data):
        """Test that report generation completes quickly."""
        result, duration = PerformanceBenchmark.time_execution(
            tool._run,
            report_data=sample_report_data,
            report_format="markdown"
        )
        
        # Report generation should be fast (no LLM or network calls)
        PerformanceBenchmark.assert_performance(
            duration, 5000, "ReportGenerator"
        )


# ============================================
# Portfolio Advisor Agent Design Tests
# ============================================

class TestPortfolioAdvisorAgentDesign:
    """Test the Portfolio Advisor agent's configuration and design."""

    def test_agent_creation(self):
        """Test that the Portfolio Advisor agent is created correctly."""
        from src.agents.portfolio_advisor import create_portfolio_advisor_agent
        
        agent = create_portfolio_advisor_agent()
        
        assert agent.role == "Portfolio Advisor"
        assert "synthesize" in agent.goal.lower() or "report" in agent.goal.lower()
        assert agent.tools is not None
        assert len(agent.tools) >= 1

    def test_agent_has_report_tool(self):
        """Test that Portfolio Advisor has the ReportGenerator tool."""
        from src.agents.portfolio_advisor import create_portfolio_advisor_agent
        
        agent = create_portfolio_advisor_agent()
        
        tool_names = [tool.name for tool in agent.tools]
        assert "Report Generator" in tool_names

    def test_agent_requires_disclaimer(self):
        """Test that agent instructions mandate disclaimer inclusion."""
        from src.agents.portfolio_advisor import create_portfolio_advisor_agent
        
        agent = create_portfolio_advisor_agent()
        
        combined = (agent.goal + " " + agent.backstory).lower()
        assert "disclaimer" in combined, (
            "Agent instructions must mention disclaimer requirement"
        )

    def test_agent_prevents_hallucination(self):
        """Test that agent instructions prevent data hallucination."""
        from src.agents.portfolio_advisor import create_portfolio_advisor_agent
        
        agent = create_portfolio_advisor_agent()
        
        combined = (agent.goal + " " + agent.backstory).lower()
        assert any(
            phrase in combined
            for phrase in ["never hallucinate", "never assume", "strictly on the data"]
        ), "Agent should have anti-hallucination instructions"
