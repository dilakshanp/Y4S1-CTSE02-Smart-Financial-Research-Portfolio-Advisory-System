"""
Research Task Definitions for the Smart Financial Research MAS.

This module defines the specific tasks assigned to each agent in the
research pipeline. Each task includes a description and the agent
responsible for execution.

Task Pipeline:
    1. coordinate_research — Coordinator: Parse query, extract tickers, fetch data
    2. analyze_sentiment — Market Analyst: Analyze news sentiment
    3. assess_risk — Risk Specialist: Calculate risk metrics
    4. generate_advisory — Portfolio Advisor: Create advisory report
"""

from crewai import Agent, Task


def create_coordination_task(agent: Agent, user_query: str) -> Task:
    """
    Create the research coordination task for the Coordinator Agent.
    
    The Coordinator parses the user query, extracts stock ticker symbols,
    and fetches initial market data using the Market Data Fetcher tool.
    
    Args:
        agent: The Coordinator Agent instance.
        user_query: The original user query string.
        
    Returns:
        Task: Configured coordination task.
    """
    task = Task(
        description=(
            f"You are the Research Coordinator. Your task is to analyze the following "
            f"user query and orchestrate the research:\n\n"
            f"USER QUERY: \"{user_query}\"\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Parse the query to identify stock ticker symbols (e.g., AAPL, MSFT, GOOGL).\n"
            f"2. For EACH ticker symbol identified, use the 'Market Data Fetcher' tool "
            f"   to retrieve current market data.\n"
            f"3. Compile ALL the market data you fetched into a structured summary.\n"
            f"4. Your output must be a valid JSON object with exactly this structure:\n"
            f"   {{\n"
            f'     "tickers": ["AAPL", "MSFT"],\n'
            f'     "research_plan": "Analyze market data, sentiment, and risk for the tickers",\n'
            f'     "market_data": [<market data from tool for each ticker>]\n'
            f"   }}\n\n"
            f"CONSTRAINTS:\n"
            f"- You MUST use the Market Data Fetcher tool for each ticker.\n"
            f"- Do NOT make up any data. Use only data returned by the tool.\n"
            f"- If the query doesn't contain clear ticker symbols, infer the most "
            f"  likely tickers from company names (e.g., 'Apple' → 'AAPL').\n"
            f"- If no tickers can be identified, return an error message.\n\n"
            f"EXPECTED OUTPUT: A JSON object containing 'tickers', 'research_plan', "
            f"and 'market_data' (list of market data objects fetched for each ticker)."
        ),
        agent=agent,
    )
    return task


def create_sentiment_analysis_task(agent: Agent) -> Task:
    """
    Create the sentiment analysis task for the Market Research Analyst.
    
    The Market Analyst uses the News Sentiment Analyzer tool to assess
    news-driven market sentiment for each ticker identified by the Coordinator.
    
    Args:
        agent: The Market Research Analyst Agent instance.
        
    Returns:
        Task: Configured sentiment analysis task.
    """
    task = Task(
        description=(
            "You are the Market Research Analyst. Using the context provided by the "
            "Coordinator (which includes the list of ticker symbols and market data), "
            "your task is to analyze news sentiment for EACH ticker.\n\n"
            "INSTRUCTIONS:\n"
            "1. Extract the list of ticker symbols from the previous task's output.\n"
            "2. Use the 'News Sentiment Analyzer' tool ONCE with ALL ticker symbols "
            "   as a comma-separated string (e.g., 'AAPL,MSFT,GOOGL').\n"
            "3. The tool will return sentiment results for ALL tickers in a single JSON.\n"
            "4. Your output must be a valid JSON object with this structure:\n"
            "   {\n"
            '     "sentiment_results": [\n'
            "       {\n"
            '         "ticker": "AAPL",\n'
            '         "sentiment_label": "BULLISH",\n'
            '         "average_sentiment": 0.45,\n'
            '         "articles_analyzed": 5,\n'
            '         "top_headlines": ["headline1", "headline2"]\n'
            "       }\n"
            "     ],\n"
            '     "overall_sentiment": "BULLISH"\n'
            "   }\n\n"
            "CONSTRAINTS:\n"
            "- You MUST use the News Sentiment Analyzer tool.\n"
            "- Pass ALL tickers as a single comma-separated string (e.g., 'AAPL,MSFT').\n"
            "- Do NOT fabricate sentiment scores. Use only tool output.\n"
            "- If the tool returns no articles, report 'NEUTRAL' sentiment.\n"
            "- Include the top headlines in your output for context.\n"
            "- STRICTLY follow ReAct formatting: Do NOT use markdown bolding (e.g., **Action:**). Use exactly 'Action:' and 'Action Input:'.\n"
            "- Once you finish analyzing all tickers, you MUST provide your final response starting exactly with 'Final Answer:'.\n\n"
            "EXPECTED OUTPUT: A JSON object containing 'sentiment_results' (list of "
            "sentiment analysis for each ticker) and 'overall_sentiment'."
        ),
        agent=agent,
    )
    return task


def create_risk_assessment_task(agent: Agent) -> Task:
    """
    Create the risk assessment task for the Risk Specialist.
    
    The Risk Specialist uses the Risk Calculator tool to compute
    quantitative risk metrics for the identified tickers.
    
    Args:
        agent: The Risk Assessment Specialist Agent instance.
        
    Returns:
        Task: Configured risk assessment task.
    """
    task = Task(
        description=(
            "You are the Risk Assessment Specialist. Using the context from the "
            "Coordinator and Market Analyst (ticker symbols, market data, and sentiment), "
            "your task is to compute quantitative risk metrics.\n\n"
            "INSTRUCTIONS:\n"
            "1. Extract the list of ticker symbols from the context.\n"
            "2. Use the 'Risk Calculator' tool with ALL tickers as a comma-separated "
            "   string (e.g., 'AAPL,MSFT,GOOGL').\n"
            "3. Set risk_free_rate to 0.05 (5%) and period to '6mo'.\n"
            "4. Compile the risk analysis results.\n"
            "5. Your output must be a valid JSON object with this structure:\n"
            "   {\n"
            '     "risk_analysis": {\n'
            '       "individual_metrics": [<metrics per ticker>],\n'
            '       "portfolio_summary": {<portfolio-level stats>}\n'
            "     },\n"
            '     "overall_risk_category": "MEDIUM"\n'
            "   }\n\n"
            "CONSTRAINTS:\n"
            "- You MUST use the Risk Calculator tool.\n"
            "- Do NOT fabricate risk metrics. Use only tool output.\n"
            "- Clearly state the risk category for each ticker and overall portfolio.\n"
            "- Include confidence levels in your assessment.\n\n"
            "EXPECTED OUTPUT: A JSON object containing 'risk_analysis' and "
            "'overall_risk_category'."
        ),
        agent=agent,
    )
    return task


def create_advisory_report_task(agent: Agent) -> Task:
    """
    Create the advisory report task for the Portfolio Advisor.
    
    The Portfolio Advisor synthesizes all findings and generates
    a comprehensive advisory report using the Report Generator tool.
    
    Args:
        agent: The Portfolio Advisor Agent instance.
        
    Returns:
        Task: Configured advisory report generation task.
    """
    task = Task(
        description=(
            "You are the Portfolio Advisor. Using ALL the research context from the "
            "Coordinator (market data), Market Analyst (sentiment), and Risk Specialist "
            "(risk metrics), your task is to generate a comprehensive advisory report.\n\n"
            "INSTRUCTIONS:\n"
            "1. Review all available data from previous agents.\n"
            "2. Formulate investment recommendations based on the data.\n"
            "3. Use the 'Report Generator' tool to create the final report.\n"
            "4. The tool expects a JSON string as 'report_data' with these keys:\n"
            '   - "tickers": list of ticker symbols\n'
            '   - "market_data": market data from the Coordinator\n'
            '   - "sentiment": sentiment results from the Market Analyst\n'
            '   - "risk_metrics": risk analysis from the Risk Specialist\n'
            '   - "recommendations": your investment recommendations\n'
            "5. Set report_format to 'markdown'.\n\n"
            "CONSTRAINTS:\n"
            "- You MUST use the Report Generator tool to create the report.\n"
            "- Ensure your tool input is VALID JSON format (use double quotes for keys/strings).\n"
            "- Base ALL recommendations strictly on data from prior agents.\n"
            "- NEVER hallucinate metrics or data that wasn't provided.\n"
            "- ALWAYS include a disclaimer that this is AI-generated, not financial advice.\n"
            "- Your recommendations must consider risk tolerance and be balanced.\n\n"
            "EXPECTED OUTPUT: The full advisory report generated by the Report Generator "
            "tool, including the report content and the file path where it was saved."
        ),
        agent=agent,
    )
    return task
