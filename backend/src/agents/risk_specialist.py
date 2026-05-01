"""
Risk Assessment Specialist Agent — Student 3 Contribution.

The Risk Assessment Specialist Agent evaluates portfolio risk using
quantitative metrics. It uses the Risk Calculator tool to compute
volatility, beta, Sharpe ratio, Value-at-Risk, and maximum drawdown
for the requested tickers.

Responsibilities:
    - Calculate comprehensive risk metrics using the Risk Calculator tool
    - Categorize risk levels (LOW / MEDIUM / HIGH / CRITICAL)
    - Identify the highest and lowest risk assets in the portfolio
    - Provide confidence levels for each assessment
    - Output structured risk analysis for the Portfolio Advisor

Interaction Strategy:
    Receives context from Coordinator and Market Analyst → Runs risk
    calculations for each ticker → Computes portfolio-level summary →
    Returns structured risk metrics for Portfolio Advisor

Author: Student 3
"""

from crewai import Agent
from langchain_community.llms import Ollama

from src.config import (
    AGENT_CONFIG,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    LLM_TEMPERATURE,
)
from src.tools.risk_calculator import RiskCalculatorTool


def create_risk_specialist_agent() -> Agent:
    """
    Create and return the Risk Assessment Specialist Agent.
    
    The Risk Specialist computes quantitative risk metrics for each
    ticker and the overall portfolio. It uses the Risk Calculator tool
    to produce volatility, beta, Sharpe ratio, VaR, and drawdown metrics.
    
    Returns:
        Agent: Configured CrewAI Risk Assessment Specialist Agent instance.
    """
    # Configure local LLM via Ollama
    local_llm = Ollama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=LLM_TEMPERATURE,
    )

    # Initialize tools
    risk_tool = RiskCalculatorTool()

    risk_specialist = Agent(
        role="Risk Assessment Specialist",
        goal=(
            "Evaluate portfolio risk by calculating quantitative risk metrics for "
            "the requested stock tickers. Use the Risk Calculator tool to compute "
            "volatility, beta, Sharpe ratio, Value-at-Risk (95%), and maximum "
            "drawdown. Categorize each ticker's risk level and provide a portfolio "
            "risk summary with confidence levels."
        ),
        backstory=(
            "You are a Certified Risk Analyst (CRA) with 15 years of experience "
            "specializing in portfolio theory and quantitative risk management. "
            "You have worked at top-tier asset management firms developing risk "
            "models. You are known for your rigorous, data-driven approach — you "
            "always provide confidence levels for your assessments and clearly "
            "explain what each metric means for the investor. You categorize risk "
            "as LOW, MEDIUM, HIGH, or CRITICAL based on composite metric scoring."
        ),
        llm=local_llm,
        tools=[risk_tool],
        verbose=AGENT_CONFIG["verbose"],
        allow_delegation=False,
        max_iter=AGENT_CONFIG["max_iterations"],
        max_rpm=AGENT_CONFIG["max_rpm"],
    )

    return risk_specialist
