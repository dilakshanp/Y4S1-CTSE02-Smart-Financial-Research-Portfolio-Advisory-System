"""
Report Generator Tool — Student 4 Contribution.

A custom CrewAI tool that generates structured, professional advisory
reports in Markdown format. The tool synthesizes market data, sentiment
analysis, and risk metrics into a comprehensive investment advisory
document and saves it to disk.

Features:
    - Professional Markdown report generation
    - Executive summary with key findings
    - Detailed sections: Market Analysis, Sentiment, Risk, Recommendations
    - Automatic disclaimer insertion
    - File persistence with timestamped filenames
    - Report metadata storage in SQLite for audit trail
    - Strict type hints and comprehensive docstrings

Dependencies:
    - json: For parsing input data
    - pathlib: For file system operations

Author: Student 4
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.config import REPORTS_DIR


class ReportGeneratorInput(BaseModel):
    """
    Input schema for the ReportGenerator tool.
    
    Defines and validates the parameters required to generate
    a financial advisory report.
    """
    report_data: str = Field(
        ...,
        description=(
            "JSON string containing the report data. Expected keys: "
            "'tickers' (list of symbols), 'market_data' (market metrics), "
            "'sentiment' (sentiment analysis results), 'risk_metrics' (risk data), "
            "'recommendations' (advisory recommendations). "
            "The tool will synthesize all provided data into a formatted report."
        )
    )
    report_format: str = Field(
        default="markdown",
        description=(
            "Output format for the report. Options: 'markdown' (default) or 'text'. "
            "Markdown provides rich formatting with headers, tables, and emphasis."
        )
    )


class ReportGeneratorTool(BaseTool):
    """
    Generates structured financial advisory reports.
    
    Takes market data, sentiment analysis, and risk metrics as input
    and produces a comprehensive, professionally formatted advisory
    report in Markdown or plain text format.
    
    Report Sections:
    1. Executive Summary — Key findings overview
    2. Market Analysis — Price data, metrics, and trends
    3. Sentiment Analysis — News-driven market sentiment
    4. Risk Assessment — Quantitative risk metrics
    5. Recommendations — Actionable investment advice
    6. Disclaimers — Legal and AI-generated content notices
    
    Reports are automatically saved to the configured reports directory
    with timestamped filenames for audit and historical tracking.
    
    Example usage by an agent:
        Input: report_data="{...json data...}", report_format="markdown"
        Output: Formatted report content + file path where it was saved
    """
    
    name: str = "Report Generator"
    description: str = (
        "Generates a comprehensive financial advisory report in Markdown format. "
        "Takes market data, sentiment analysis, and risk metrics as JSON input "
        "and produces a structured report with executive summary, analysis "
        "sections, recommendations, and disclaimers. Saves the report to disk."
    )
    args_schema: Type[BaseModel] = ReportGeneratorInput

    def _run(
        self, report_data: str, report_format: str = "markdown"
    ) -> str:
        """
        Execute the report generation operation.
        
        Parses the input JSON data and generates a comprehensive
        advisory report, saving it to the reports directory.
        
        Args:
            report_data: JSON string with market_data, sentiment, risk_metrics.
            report_format: Output format ('markdown' or 'text').
            
        Returns:
            JSON string containing:
                - report_content: The full report text
                - report_path: File path where the report was saved
                - generated_at: Timestamp of report generation
                
            Returns an error message string if generation fails.
        """
        try:
            # Parse input data
            try:
                data: Dict[str, Any] = json.loads(report_data)
            except json.JSONDecodeError:
                # If not valid JSON, treat as plain text context
                data = {"raw_context": report_data}

            # Extract components with safe defaults
            tickers: list = data.get("tickers", [])
            market_data: Any = data.get("market_data", {})
            sentiment: Any = data.get("sentiment", {})
            risk_metrics: Any = data.get("risk_metrics", {})
            
            if "raw_context" in data:
                recommendations: Any = data["raw_context"]
            else:
                recommendations: Any = data.get("recommendations", "")

            # Generate report content
            if report_format == "text":
                report_content: str = self._generate_text_report(
                    tickers, market_data, sentiment, risk_metrics, recommendations
                )
            else:
                report_content = self._generate_markdown_report(
                    tickers, market_data, sentiment, risk_metrics, recommendations
                )

            # Save report to file
            report_path: str = self._save_report(report_content, tickers)

            # Build response
            result: Dict[str, Any] = {
                "error": False,
                "report_content": report_content,
                "report_path": report_path,
                "format": report_format,
                "tickers_covered": tickers,
                "sections_generated": [
                    "Executive Summary",
                    "Market Analysis",
                    "Sentiment Analysis",
                    "Risk Assessment",
                    "Recommendations",
                    "Disclaimers"
                ],
                "generated_at": datetime.now().isoformat(),
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({
                "error": True,
                "message": f"Failed to generate report: {str(e)}",
            })

    def _generate_markdown_report(
        self,
        tickers: list,
        market_data: Any,
        sentiment: Any,
        risk_metrics: Any,
        recommendations: Any
    ) -> str:
        """
        Generate a professional Markdown-formatted advisory report.
        
        Args:
            tickers: List of stock ticker symbols covered.
            market_data: Market data dictionary or list.
            sentiment: Sentiment analysis results.
            risk_metrics: Risk metric calculations.
            recommendations: Advisory recommendations.
            
        Returns:
            Complete Markdown report string.
        """
        timestamp: str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        tickers_str: str = ", ".join(tickers) if tickers else "N/A"
        
        report_lines: list = [
            f"# 📊 Financial Research & Advisory Report",
            f"",
            f"**Generated:** {timestamp}",
            f"**Tickers Analyzed:** {tickers_str}",
            f"**Report Type:** Comprehensive Investment Advisory",
            f"",
            f"---",
            f"",
            f"## 📋 Executive Summary",
            f"",
            self._generate_executive_summary(
                tickers, market_data, sentiment, risk_metrics
            ),
            f"",
            f"---",
            f"",
            f"## 📈 Market Analysis",
            f"",
            self._format_market_data_section(market_data),
            f"",
            f"---",
            f"",
            f"## 📰 Sentiment Analysis",
            f"",
            self._format_sentiment_section(sentiment),
            f"",
            f"---",
            f"",
            f"## ⚠️ Risk Assessment",
            f"",
            self._format_risk_section(risk_metrics),
            f"",
            f"---",
            f"",
            f"## 💡 Recommendations",
            f"",
            self._format_recommendations_section(recommendations),
            f"",
            f"---",
            f"",
            f"## ⚖️ Disclaimers",
            f"",
            f"> **IMPORTANT:** This report is generated by an AI-powered Multi-Agent System ",
            f"> for educational and informational purposes only. It does NOT constitute ",
            f"> financial advice, investment recommendations, or solicitation to buy or ",
            f"> sell any securities.",
            f">",
            f"> - Past performance is not indicative of future results.",
            f"> - All investments carry risk, including the potential loss of principal.",
            f"> - Always consult with a qualified financial advisor before making ",
            f">   investment decisions.",
            f"> - The data used in this analysis is sourced from public APIs and may ",
            f">   contain delays or inaccuracies.",
            f">",
            f"> **System:** Smart Financial Research MAS v1.0",
            f"> **Engine:** Local LLM via Ollama (llama3:8b)",
            f"",
            f"---",
            f"*Report generated by the Smart Financial Research & Portfolio Advisory System*",
        ]
        
        return "\n".join(report_lines)

    def _generate_executive_summary(
        self,
        tickers: list,
        market_data: Any,
        sentiment: Any,
        risk_metrics: Any
    ) -> str:
        """
        Generate an executive summary based on all available data.
        
        Args:
            tickers: List of tickers analyzed.
            market_data: Market data results.
            sentiment: Sentiment analysis results.
            risk_metrics: Risk metric results.
            
        Returns:
            Executive summary text string.
        """
        summary_parts: list = []
        
        summary_parts.append(
            f"This report provides a comprehensive analysis of "
            f"**{len(tickers)} securities** ({', '.join(tickers) if tickers else 'N/A'}), "
            f"covering market performance, news sentiment, and risk assessment."
        )
        
        # Summarize sentiment if available
        if isinstance(sentiment, dict) and sentiment.get("sentiment_label"):
            label = sentiment.get("sentiment_label", "NEUTRAL")
            score = sentiment.get("average_sentiment", 0)
            summary_parts.append(
                f"\n**Overall Market Sentiment:** {label} "
                f"(Score: {score})"
            )
        elif isinstance(sentiment, list):
            labels = [s.get("sentiment_label", "NEUTRAL") for s in sentiment if isinstance(s, dict)]
            if labels:
                summary_parts.append(
                    f"\n**Sentiment Distribution:** "
                    + ", ".join(labels)
                )
        
        # Summarize risk if available
        if isinstance(risk_metrics, dict):
            portfolio = risk_metrics.get("portfolio_summary", {})
            if portfolio:
                summary_parts.append(
                    f"\n**Portfolio Risk Profile:** "
                    f"Avg Volatility: {portfolio.get('avg_volatility', 'N/A')}, "
                    f"Avg Beta: {portfolio.get('avg_beta', 'N/A')}, "
                    f"Avg Sharpe: {portfolio.get('avg_sharpe', 'N/A')}"
                )
        
        return "\n".join(summary_parts)

    @staticmethod
    def _format_market_data_section(market_data: Any) -> str:
        """
        Format market data into a readable report section.
        
        Args:
            market_data: Market data dictionary, list, or string.
            
        Returns:
            Formatted market data section string.
        """
        if not market_data:
            return "*No market data available for this analysis.*"
        
        if isinstance(market_data, str):
            return market_data
        
        if isinstance(market_data, dict):
            market_data = [market_data]
        
        if isinstance(market_data, list):
            sections: list = []
            for item in market_data:
                if isinstance(item, dict):
                    ticker = item.get("ticker", "N/A")
                    sections.append(f"### {ticker}")
                    sections.append("")
                    sections.append(f"| Metric | Value |")
                    sections.append(f"|--------|-------|")
                    
                    field_map = {
                        "current_price": "Current Price",
                        "price_change_pct": "Price Change (%)",
                        "volume": "Volume",
                        "market_cap": "Market Cap",
                        "pe_ratio": "P/E Ratio",
                        "week_52_high": "52-Week High",
                        "week_52_low": "52-Week Low",
                        "sector": "Sector",
                        "industry": "Industry",
                    }
                    
                    for key, label in field_map.items():
                        value = item.get(key, "N/A")
                        if value is not None and value != "N/A":
                            if key in ("current_price", "week_52_high", "week_52_low"):
                                value = f"${value:,.2f}" if isinstance(value, (int, float)) else value
                            elif key == "market_cap" and isinstance(value, (int, float)):
                                if value >= 1e12:
                                    value = f"${value/1e12:.2f}T"
                                elif value >= 1e9:
                                    value = f"${value/1e9:.2f}B"
                                elif value >= 1e6:
                                    value = f"${value/1e6:.2f}M"
                            elif key == "volume" and isinstance(value, (int, float)):
                                value = f"{value:,.0f}"
                            elif key == "price_change_pct":
                                value = f"{value:+.2f}%" if isinstance(value, (int, float)) else value
                        sections.append(f"| {label} | {value} |")
                    
                    sections.append("")
            
            return "\n".join(sections)
        
        return str(market_data)

    @staticmethod
    def _format_sentiment_section(sentiment: Any) -> str:
        """
        Format sentiment analysis into a readable report section.
        
        Args:
            sentiment: Sentiment analysis results.
            
        Returns:
            Formatted sentiment analysis section string.
        """
        if not sentiment:
            return "*No sentiment analysis available.*"
        
        if isinstance(sentiment, str):
            return sentiment
        
        sections: list = []
        
        if isinstance(sentiment, dict):
            label = sentiment.get("sentiment_label", "N/A")
            score = sentiment.get("average_sentiment", "N/A")
            articles = sentiment.get("articles_analyzed", 0)
            
            emoji = "🟢" if label == "BULLISH" else "🔴" if label == "BEARISH" else "🟡"
            sections.append(f"**Overall Sentiment:** {emoji} **{label}** (Score: {score})")
            sections.append(f"**Articles Analyzed:** {articles}")
            sections.append("")
            
            # Distribution
            dist = sentiment.get("sentiment_distribution", {})
            if dist:
                sections.append("**Sentiment Distribution:**")
                sections.append(f"- 🟢 Bullish: {dist.get('bullish', 0)} articles")
                sections.append(f"- 🟡 Neutral: {dist.get('neutral', 0)} articles")
                sections.append(f"- 🔴 Bearish: {dist.get('bearish', 0)} articles")
                sections.append("")
            
            # Headlines
            headlines = sentiment.get("top_headlines", [])
            if headlines:
                sections.append("**Key Headlines:**")
                for hl in headlines[:5]:
                    sections.append(f"- {hl}")
        
        elif isinstance(sentiment, list):
            for s in sentiment:
                if isinstance(s, dict):
                    sections.append(f"- **{s.get('query', 'N/A')}**: "
                                   f"{s.get('sentiment_label', 'N/A')} "
                                   f"(Score: {s.get('average_sentiment', 'N/A')})")
        
        return "\n".join(sections) if sections else str(sentiment)

    @staticmethod
    def _format_risk_section(risk_metrics: Any) -> str:
        """
        Format risk metrics into a readable report section.
        
        Args:
            risk_metrics: Risk metric calculations.
            
        Returns:
            Formatted risk assessment section string.
        """
        if not risk_metrics:
            return "*No risk assessment available.*"
        
        if isinstance(risk_metrics, str):
            return risk_metrics
        
        sections: list = []
        
        individual = []
        if isinstance(risk_metrics, dict):
            individual = risk_metrics.get("individual_metrics", [risk_metrics])
            
            # Portfolio summary
            portfolio = risk_metrics.get("portfolio_summary", {})
            if portfolio:
                sections.append("### Portfolio Summary")
                sections.append("")
                sections.append(f"| Metric | Value |")
                sections.append(f"|--------|-------|")
                sections.append(f"| Average Volatility | {portfolio.get('avg_volatility', 'N/A')} |")
                sections.append(f"| Average Beta | {portfolio.get('avg_beta', 'N/A')} |")
                sections.append(f"| Average Sharpe Ratio | {portfolio.get('avg_sharpe', 'N/A')} |")
                sections.append(f"| Highest Risk | {portfolio.get('highest_risk_ticker', 'N/A')} |")
                sections.append(f"| Lowest Risk | {portfolio.get('lowest_risk_ticker', 'N/A')} |")
                sections.append("")
        elif isinstance(risk_metrics, list):
            individual = risk_metrics
        
        # Individual ticker metrics
        for item in individual:
            if isinstance(item, dict) and not item.get("error"):
                ticker = item.get("ticker", "N/A")
                category = item.get("risk_category", "N/A")
                
                emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}.get(
                    category, "⚪"
                )
                
                sections.append(f"### {ticker} — {emoji} {category} Risk")
                sections.append("")
                sections.append(f"| Metric | Value |")
                sections.append(f"|--------|-------|")
                sections.append(f"| Volatility | {item.get('volatility_pct', item.get('volatility', 'N/A'))} |")
                sections.append(f"| Beta | {item.get('beta', 'N/A')} |")
                sections.append(f"| Sharpe Ratio | {item.get('sharpe_ratio', 'N/A')} |")
                sections.append(f"| VaR (95%) | {item.get('var_95_pct', item.get('var_95', 'N/A'))} |")
                sections.append(f"| Max Drawdown | {item.get('max_drawdown_pct', item.get('max_drawdown', 'N/A'))} |")
                sections.append(f"| Confidence | {item.get('confidence', 'N/A')} |")
                sections.append("")
        
        return "\n".join(sections) if sections else str(risk_metrics)

    @staticmethod
    def _format_recommendations_section(recommendations: Any) -> str:
        """
        Format recommendations into a readable report section.
        
        Args:
            recommendations: Advisory recommendations (str, dict, or list).
            
        Returns:
            Formatted recommendations section string.
        """
        if not recommendations:
            return (
                "Based on the analysis above, please consult with a qualified "
                "financial advisor for personalized investment recommendations."
            )
        
        if isinstance(recommendations, str):
            return recommendations
        
        if isinstance(recommendations, dict):
            sections: list = []
            for key, value in recommendations.items():
                sections.append(f"**{key.replace('_', ' ').title()}:** {value}")
            return "\n\n".join(sections)
        
        if isinstance(recommendations, list):
            return "\n".join(
                f"- {item}" if isinstance(item, str) else f"- {str(item)}"
                for item in recommendations
            )
        
        return str(recommendations)

    def _generate_text_report(
        self,
        tickers: list,
        market_data: Any,
        sentiment: Any,
        risk_metrics: Any,
        recommendations: Any
    ) -> str:
        """
        Generate a plain text version of the advisory report.
        
        Args:
            tickers: List of ticker symbols.
            market_data: Market data results.
            sentiment: Sentiment analysis results.
            risk_metrics: Risk metric results.
            recommendations: Advisory recommendations.
            
        Returns:
            Plain text report string.
        """
        # Generate markdown first, then strip formatting
        md_report = self._generate_markdown_report(
            tickers, market_data, sentiment, risk_metrics, recommendations
        )
        # Simple markdown-to-text conversion
        text = md_report.replace("#", "").replace("**", "").replace("*", "")
        text = text.replace("|", " ").replace("---", "=" * 50)
        return text

    @staticmethod
    def _save_report(content: str, tickers: list) -> str:
        """
        Save the generated report to the reports directory.
        
        Args:
            content: Report content string.
            tickers: List of tickers (used in filename).
            
        Returns:
            Absolute path to the saved report file.
        """
        reports_dir: Path = REPORTS_DIR
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        tickers_slug: str = "_".join(tickers[:3]) if tickers else "analysis"
        filename: str = f"advisory_{tickers_slug}_{timestamp}.md"
        
        report_path: Path = reports_dir / filename
        report_path.write_text(content, encoding="utf-8")
        
        return str(report_path)
