"""
Market Research Analyst Agent — Student 2 Contribution.

The Market Research Analyst Agent specializes in gathering comprehensive
market intelligence. It uses the News Sentiment Analyzer tool to fetch
and analyze financial news sentiment for the requested ticker symbols.

Responsibilities:
    - Analyze news sentiment for each ticker using the sentiment tool
    - Aggregate sentiment scores and classify market mood
    - Identify key headlines driving market sentiment
    - Output structured sentiment analysis results
    - Report data quality issues transparently

Interaction Strategy:
    Receives research plan from Coordinator → Fetches news sentiment
    for each ticker → Compiles sentiment report → Returns structured
    results for Risk Specialist and Portfolio Advisor

Author: Student 2
"""

from crewai import Agent
from langchain_community.llms import Ollama

from src.config import (
    AGENT_CONFIG,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    LLM_TEMPERATURE,
)
from src.tools.news_sentiment import NewsSentimentAnalyzerTool


def create_market_analyst_agent() -> Agent:
    """
    Create and return the Market Research Analyst Agent.
    
    The Market Analyst focuses on gathering news-driven market intelligence.
    It uses the News Sentiment Analyzer tool to assess how current news
    coverage affects market sentiment for the requested tickers.
    
    Returns:
        Agent: Configured CrewAI Market Research Analyst Agent instance.
    """
    # Configure local LLM via Ollama
    local_llm = Ollama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=LLM_TEMPERATURE,
    )

    # Initialize tools
    sentiment_tool = NewsSentimentAnalyzerTool()

    market_analyst = Agent(
        role="Market Research Analyst",
        goal=(
            "Gather comprehensive market intelligence by analyzing financial news "
            "sentiment for the requested stock tickers. Use the News Sentiment "
            "Analyzer tool to fetch recent news articles and compute sentiment "
            "scores. Provide a clear, data-driven sentiment assessment."
        ),
        backstory=(
            "You are a Quantitative Market Analyst with deep expertise in NLP-driven "
            "sentiment analysis and market data interpretation. You have spent 10 years "
            "at a leading hedge fund developing sentiment-based trading signals. "
            "You are meticulous about data quality and always report findings "
            "transparently — if data is unavailable or unreliable, you say so clearly. "
            "You never fabricate or assume data that wasn't provided by your tools."
        ),
        llm=local_llm,
        tools=[sentiment_tool],
        verbose=AGENT_CONFIG["verbose"],
        allow_delegation=False,
        max_iter=AGENT_CONFIG["max_iterations"],
        max_rpm=AGENT_CONFIG["max_rpm"],
    )

    return market_analyst
