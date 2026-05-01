"""
Coordinator Agent — Student 1 Contribution.

The Coordinator Agent serves as the orchestrator of the research pipeline.
It receives user queries, parses input to identify stock tickers, creates
a structured research plan, and ensures data flows correctly through
the sequential pipeline.

Responsibilities:
    - Parse and validate user input queries
    - Extract stock ticker symbols from natural language
    - Create a structured research plan
    - Validate output quality from downstream agents
    - Maintain research state consistency

Interaction Strategy:
    Entry point → Creates plan → Delegates to Market Analyst → 
    Receives market data → Delegates to Risk Specialist → 
    Receives risk metrics → Delegates to Portfolio Advisor → 
    Returns final report to user

Author: Student 1
"""

from crewai import Agent
from langchain_community.llms import Ollama

from src.config import (
    AGENT_CONFIG,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    LLM_TEMPERATURE,
)
from src.tools.market_data_fetcher import MarketDataFetcherTool


def create_coordinator_agent() -> Agent:
    """
    Create and return the Coordinator Agent.
    
    The Coordinator is the first agent in the pipeline. It receives
    the user's query, parses it to identify tickers and intent,
    fetches initial market data, and creates a structured research
    plan for the downstream agents.
    
    Returns:
        Agent: Configured CrewAI Coordinator Agent instance.
    """
    # Configure local LLM via Ollama
    local_llm = Ollama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=LLM_TEMPERATURE,
    )

    # Initialize tools
    market_data_tool = MarketDataFetcherTool()

    coordinator = Agent(
        role="Research Coordinator",
        goal=(
            "Orchestrate the financial research pipeline by parsing user queries, "
            "extracting stock ticker symbols, fetching initial market data using the "
            "Market Data Fetcher tool, and creating a structured research plan that "
            "downstream agents can act upon."
        ),
        backstory=(
            "You are a Senior Financial Research Director with 20 years of experience "
            "managing analyst teams at top investment banks. You are known for your "
            "meticulous planning, quality control, and ability to distill complex "
            "financial queries into actionable research plans. You never provide "
            "financial advice directly — you coordinate the research team."
        ),
        llm=local_llm,
        tools=[market_data_tool],
        verbose=AGENT_CONFIG["verbose"],
        allow_delegation=False,
        max_iter=AGENT_CONFIG["max_iterations"],
        max_rpm=AGENT_CONFIG["max_rpm"],
    )

    return coordinator
