"""
Portfolio Advisor Agent — Student 4 Contribution.

The Portfolio Advisor Agent synthesizes all research findings into
actionable investment advisory recommendations. It uses the Report
Generator tool to produce a comprehensive, formatted advisory report.

Responsibilities:
    - Synthesize market data, sentiment, and risk analysis
    - Generate balanced, risk-aware investment recommendations
    - Create a comprehensive advisory report with all sections
    - Include mandatory disclaimers about AI-generated advice
    - Base all recommendations strictly on data from prior agents

Interaction Strategy:
    Receives complete context from Coordinator, Market Analyst, and
    Risk Specialist → Synthesizes findings → Generates formatted
    advisory report using Report Generator tool → Returns report
    to Coordinator for final delivery

Author: Student 4
"""

from crewai import Agent
from langchain_community.llms import Ollama

from src.config import (
    AGENT_CONFIG,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    LLM_TEMPERATURE,
)
from src.tools.report_generator import ReportGeneratorTool


def create_portfolio_advisor_agent() -> Agent:
    """
    Create and return the Portfolio Advisor Agent.
    
    The Portfolio Advisor is the final agent in the pipeline. It receives
    all research findings and synthesizes them into a comprehensive
    advisory report with recommendations, caveats, and disclaimers.
    
    Returns:
        Agent: Configured CrewAI Portfolio Advisor Agent instance.
    """
    # Configure local LLM via Ollama
    local_llm = Ollama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=LLM_TEMPERATURE,
    )

    # Initialize tools
    report_tool = ReportGeneratorTool()

    portfolio_advisor = Agent(
        role="Portfolio Advisor",
        goal=(
            "Synthesize all research findings — market data, sentiment analysis, "
            "and risk metrics — into actionable portfolio recommendations. Use the "
            "Report Generator tool to create a comprehensive advisory report in "
            "Markdown format. Ensure all recommendations are based strictly on the "
            "data provided by prior agents — never hallucinate or assume data. "
            "Always include disclaimers that this is AI-generated analysis."
        ),
        backstory=(
            "You are a Chartered Financial Analyst (CFA) with a decade of experience "
            "in portfolio management at a premier wealth management firm. You are known "
            "for producing balanced, risk-aware investment strategies that align with "
            "client goals. You always base your advice on hard data and clearly "
            "communicate uncertainties. You MUST include a disclaimer in every report "
            "stating that this is AI-generated analysis and does NOT constitute "
            "financial advice. You synthesize complex data into clear, actionable "
            "insights that any investor can understand."
        ),
        llm=local_llm,
        tools=[report_tool],
        verbose=AGENT_CONFIG["verbose"],
        allow_delegation=False,
        max_iter=AGENT_CONFIG["max_iterations"],
        max_rpm=AGENT_CONFIG["max_rpm"],
    )

    return portfolio_advisor
