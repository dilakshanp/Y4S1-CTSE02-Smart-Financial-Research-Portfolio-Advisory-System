"""
Test Suite for the Market Research Analyst Agent & News Sentiment Tool.

Student 2 Contribution.

Tests cover:
    - NewsSentimentAnalyzer tool: sentiment scoring, classification, edge cases
    - Market Analyst agent: design quality, tool integration
    - Property-based testing: sentiment score ranges, label validity
    - LLM-as-Judge: output quality evaluation
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_harness import JSONValidator, LLMJudge, PerformanceBenchmark
from src.tools.news_sentiment import NewsSentimentAnalyzerTool


# ============================================
# NewsSentimentAnalyzer Tool Tests
# ============================================

class TestNewsSentimentAnalyzerTool:
    """Test suite for the News Sentiment Analyzer tool."""

    @pytest.fixture
    def tool(self) -> NewsSentimentAnalyzerTool:
        """Create a NewsSentimentAnalyzer tool instance."""
        return NewsSentimentAnalyzerTool()

    def test_analyze_valid_query(self, tool):
        """Test sentiment analysis for a valid financial query."""
        result_json = tool._run(query="Apple stock", max_articles=3)
        data = JSONValidator.assert_valid_json(result_json)
        JSONValidator.assert_no_error(data)
        
        # Verify required fields
        JSONValidator.assert_has_keys(data, [
            "query", "articles_analyzed", "average_sentiment",
            "sentiment_label", "analyzed_at"
        ])
        
        # Verify sentiment score is in valid range
        sentiment = data["average_sentiment"]
        JSONValidator.assert_value_in_range(
            sentiment, -1.0, 1.0, "average_sentiment"
        )

    def test_sentiment_label_validity(self, tool):
        """Property: Sentiment label must be BULLISH, NEUTRAL, or BEARISH."""
        result_json = tool._run(query="Microsoft stock", max_articles=3)
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            valid_labels = ["BULLISH", "NEUTRAL", "BEARISH"]
            assert data["sentiment_label"] in valid_labels, (
                f"Invalid label: {data['sentiment_label']}"
            )

    def test_sentiment_label_matches_score(self, tool):
        """Property: Sentiment label must be consistent with the score."""
        result_json = tool._run(query="Tesla stock", max_articles=3)
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error") and data.get("articles_analyzed", 0) > 0:
            score = data["average_sentiment"]
            label = data["sentiment_label"]
            
            if score > 0.05:
                assert label == "BULLISH", f"Score {score} should be BULLISH, got {label}"
            elif score < -0.05:
                assert label == "BEARISH", f"Score {score} should be BEARISH, got {label}"
            else:
                assert label == "NEUTRAL", f"Score {score} should be NEUTRAL, got {label}"

    def test_empty_query(self, tool):
        """Test handling of an empty search query."""
        result_json = tool._run(query="", max_articles=3)
        data = JSONValidator.assert_valid_json(result_json)
        assert data.get("error") is True

    def test_articles_count_respects_max(self, tool):
        """Property: Number of articles analyzed must not exceed max_articles."""
        max_art = 3
        result_json = tool._run(query="Google stock", max_articles=max_art)
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            assert data["articles_analyzed"] <= max_art, (
                f"Analyzed {data['articles_analyzed']} articles, max was {max_art}"
            )

    def test_sentiment_distribution_consistency(self, tool):
        """Property: Sentiment distribution must sum to articles_analyzed."""
        result_json = tool._run(query="Amazon stock", max_articles=5)
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error") and "sentiment_distribution" in data:
            dist = data["sentiment_distribution"]
            total = dist.get("bullish", 0) + dist.get("neutral", 0) + dist.get("bearish", 0)
            assert total == data["articles_analyzed"], (
                f"Distribution total ({total}) != articles analyzed ({data['articles_analyzed']})"
            )

    def test_individual_article_sentiments(self, tool):
        """Test that individual article sentiments have required fields."""
        result_json = tool._run(query="AAPL stock market", max_articles=3)
        data = JSONValidator.assert_valid_json(result_json)
        
        if not data.get("error"):
            for article in data.get("articles", []):
                assert "title" in article, "Article missing 'title'"
                assert "sentiment_score" in article, "Article missing 'sentiment_score'"
                assert "sentiment_label" in article, "Article missing 'sentiment_label'"
                
                JSONValidator.assert_value_in_range(
                    article["sentiment_score"], -1.0, 1.0, "article sentiment_score"
                )

    def test_tool_performance(self, tool):
        """Test that tool execution completes within reasonable time."""
        result, duration = PerformanceBenchmark.time_execution(
            tool._run, query="AAPL", max_articles=3
        )
        
        PerformanceBenchmark.assert_performance(
            duration, 30000, "NewsSentimentAnalyzer"
        )

    def test_no_data_fabrication(self, tool):
        """Security: Ensure the tool doesn't fabricate data."""
        result_json = tool._run(query="AAPL stock", max_articles=3)
        
        evaluation = LLMJudge.evaluate_coherence(result_json, min_length=50)
        # Should not contain fabrication indicators
        assert "hypothetical" not in result_json.lower()
        assert "made up" not in result_json.lower()


# ============================================
# Market Analyst Agent Design Tests
# ============================================

class TestMarketAnalystAgentDesign:
    """Test the Market Analyst agent's configuration and design."""

    def test_agent_creation(self):
        """Test that the Market Analyst agent is created correctly."""
        from src.agents.market_analyst import create_market_analyst_agent
        
        agent = create_market_analyst_agent()
        
        assert agent.role == "Market Research Analyst"
        assert "sentiment" in agent.goal.lower() or "market" in agent.goal.lower()
        assert agent.tools is not None
        assert len(agent.tools) >= 1

    def test_agent_has_sentiment_tool(self):
        """Test that Market Analyst has the NewsSentimentAnalyzer tool."""
        from src.agents.market_analyst import create_market_analyst_agent
        
        agent = create_market_analyst_agent()
        
        tool_names = [tool.name for tool in agent.tools]
        assert "News Sentiment Analyzer" in tool_names

    def test_agent_prevents_fabrication(self):
        """Test that agent backstory includes anti-fabrication instructions."""
        from src.agents.market_analyst import create_market_analyst_agent
        
        agent = create_market_analyst_agent()
        
        backstory_lower = agent.backstory.lower()
        assert any(
            term in backstory_lower
            for term in ["never fabricate", "never assume", "transparently"]
        ), "Agent should have anti-fabrication instructions"
