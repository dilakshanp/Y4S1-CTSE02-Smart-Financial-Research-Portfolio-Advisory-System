"""
News Sentiment Analyzer Tool — Student 2 Contribution.

A custom CrewAI tool that fetches financial news from RSS feeds and
analyzes sentiment using the VADER (Valence Aware Dictionary and
sEntiment Reasoner) NLP library. This tool provides agents with
news-driven market sentiment intelligence without requiring any paid APIs.

Features:
    - RSS feed parsing from multiple financial news sources
    - VADER-based sentiment scoring (compound, positive, negative, neutral)
    - Aggregated sentiment classification (BULLISH / NEUTRAL / BEARISH)
    - Individual article sentiment breakdown
    - Fallback to multiple news sources for reliability
    - Strict type hints and comprehensive docstrings

Dependencies:
    - feedparser: RSS/Atom feed parser
    - vaderSentiment: Rule-based sentiment analysis
    - beautifulsoup4: HTML parsing for article content

Author: Student 2
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

import feedparser
from bs4 import BeautifulSoup
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class NewsSentimentInput(BaseModel):
    """
    Input schema for the NewsSentimentAnalyzer tool.
    
    Defines and validates the parameters required to fetch
    and analyze financial news sentiment.
    """
    query: str = Field(
        ...,
        description=(
            "Search query for financial news. Can be a company name, "
            "ticker symbol, or topic (e.g., 'Apple stock', 'AAPL', "
            "'tech sector earnings')."
        )
    )
    max_articles: int = Field(
        default=5,
        description=(
            "Maximum number of articles to analyze. Range: 1-15. "
            "Default is 5. Higher values provide more comprehensive "
            "sentiment but take longer."
        ),
        ge=1,
        le=15
    )


class NewsSentimentAnalyzerTool(BaseTool):
    """
    Fetches financial news articles and analyzes their sentiment.
    
    This tool gathers recent financial news from free RSS feeds
    (Google News, Yahoo Finance, Reuters) and performs VADER-based
    sentiment analysis to determine market sentiment.
    
    It returns:
    - Individual article headlines with sentiment scores
    - Aggregate sentiment score (-1.0 to 1.0)
    - Overall sentiment label (BEARISH / NEUTRAL / BULLISH)
    - Top headlines for context
    
    Example usage by an agent:
        Input: query="AAPL", max_articles=5
        Output: JSON with sentiment scores and article details
    """
    
    name: str = "News Sentiment Analyzer"
    description: str = (
        "Fetches recent financial news articles and analyzes their sentiment "
        "using NLP. Returns sentiment scores (bearish to bullish) and "
        "key headlines. Use this to understand market sentiment and "
        "news-driven price movements for stocks or financial topics."
    )
    args_schema: Type[BaseModel] = NewsSentimentInput

    def _run(self, query: str, max_articles: int = 5) -> str:
        """
        Execute the news sentiment analysis operation.
        
        Fetches financial news articles from RSS feeds and analyzes
        their sentiment using VADER sentiment analysis.
        
        Args:
            query: Search query for financial news.
            max_articles: Maximum number of articles to analyze (1-15).
            
        Returns:
            JSON string containing sentiment analysis with fields:
                - query: The original search query
                - articles_analyzed: Number of articles processed
                - average_sentiment: Aggregate sentiment (-1.0 to 1.0)
                - sentiment_label: BEARISH, NEUTRAL, or BULLISH
                - articles: List of article details with individual sentiments
                - top_headlines: List of top headlines
                - analyzed_at: Timestamp of analysis
                
            Returns an error message string if the analysis fails.
        """
        try:
            # Validate input
            query_clean: str = query.strip()
            if not query_clean:
                return json.dumps({
                    "error": True,
                    "message": "Search query cannot be empty."
                })

            # Initialize VADER sentiment analyzer
            analyzer: SentimentIntensityAnalyzer = SentimentIntensityAnalyzer()
            
            # Fetch news articles from multiple RSS sources
            articles: List[Dict[str, Any]] = self._fetch_news(query_clean, max_articles)
            
            if not articles:
                return json.dumps({
                    "error": False,
                    "query": query_clean,
                    "articles_analyzed": 0,
                    "average_sentiment": 0.0,
                    "sentiment_label": "NEUTRAL",
                    "message": f"No recent news articles found for '{query_clean}'.",
                    "articles": [],
                    "top_headlines": [],
                    "analyzed_at": datetime.now().isoformat()
                })

            # Analyze sentiment for each article
            analyzed_articles: List[Dict[str, Any]] = []
            sentiment_scores: List[float] = []
            
            for article in articles:
                # Combine title and summary for sentiment analysis
                text: str = f"{article.get('title', '')}. {article.get('summary', '')}"
                text_clean: str = self._clean_text(text)
                
                # Get VADER sentiment scores
                scores: Dict[str, float] = analyzer.polarity_scores(text_clean)
                compound_score: float = scores["compound"]
                sentiment_scores.append(compound_score)
                
                analyzed_articles.append({
                    "title": article.get("title", "N/A"),
                    "source": article.get("source", "N/A"),
                    "published": article.get("published", "N/A"),
                    "link": article.get("link", ""),
                    "sentiment_score": round(compound_score, 4),
                    "sentiment_label": self._classify_sentiment(compound_score),
                    "sentiment_details": {
                        "positive": round(scores["pos"], 4),
                        "negative": round(scores["neg"], 4),
                        "neutral": round(scores["neu"], 4),
                        "compound": round(scores["compound"], 4),
                    }
                })

            # Calculate aggregate sentiment
            avg_sentiment: float = (
                sum(sentiment_scores) / len(sentiment_scores)
                if sentiment_scores else 0.0
            )
            
            # Build result
            result: Dict[str, Any] = {
                "error": False,
                "query": query_clean,
                "articles_analyzed": len(analyzed_articles),
                "average_sentiment": round(avg_sentiment, 4),
                "sentiment_label": self._classify_sentiment(avg_sentiment),
                "sentiment_distribution": {
                    "bullish": sum(1 for s in sentiment_scores if s > 0.05),
                    "neutral": sum(1 for s in sentiment_scores if -0.05 <= s <= 0.05),
                    "bearish": sum(1 for s in sentiment_scores if s < -0.05),
                },
                "articles": analyzed_articles,
                "top_headlines": [a["title"] for a in analyzed_articles[:5]],
                "analyzed_at": datetime.now().isoformat(),
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({
                "error": True,
                "message": f"Failed to analyze sentiment for '{query}': {str(e)}",
                "query": query,
            })

    def _fetch_news(
        self, query: str, max_articles: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch news articles from multiple RSS feed sources.
        
        Tries multiple free RSS feed sources to gather financial news,
        falling back to alternative sources if the primary one fails.
        
        Args:
            query: Search query for news articles.
            max_articles: Maximum number of articles to return.
            
        Returns:
            List of article dictionaries with title, summary, link, etc.
        """
        articles: List[Dict[str, Any]] = []
        
        # RSS feed sources (all free, no API key required)
        rss_urls: List[str] = [
            # Google News RSS
            f"https://news.google.com/rss/search?q={query.replace(' ', '+')}+stock+market&hl=en-US&gl=US&ceid=US:en",
            # Yahoo Finance RSS
            f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={query.replace(' ', '+')}&region=US&lang=en-US",
            # MarketWatch RSS
            "https://feeds.marketwatch.com/marketwatch/topstories/",
        ]
        
        for rss_url in rss_urls:
            if len(articles) >= max_articles:
                break
                
            try:
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries:
                    if len(articles) >= max_articles:
                        break
                    
                    # Extract and clean article data
                    summary: str = entry.get("summary", "")
                    if summary:
                        soup = BeautifulSoup(summary, "html.parser")
                        summary = soup.get_text(strip=True)
                    
                    article: Dict[str, Any] = {
                        "title": entry.get("title", "N/A"),
                        "summary": summary[:300] if summary else "",
                        "link": entry.get("link", ""),
                        "published": entry.get("published", "N/A"),
                        "source": (
                            entry.get("source", {}).get("title", "")
                            if isinstance(entry.get("source"), dict)
                            else feed.feed.get("title", "Unknown")
                        ),
                    }
                    articles.append(article)
                    
            except Exception:
                # Skip failed feed sources silently and try next
                continue
        
        return articles

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean text for sentiment analysis.
        
        Removes HTML tags, special characters, and extra whitespace
        to prepare text for NLP processing.
        
        Args:
            text: Raw text string to clean.
            
        Returns:
            Cleaned text string suitable for sentiment analysis.
        """
        # Remove HTML tags
        text = BeautifulSoup(text, "html.parser").get_text()
        # Remove URLs
        text = re.sub(r"http\S+|www\.\S+", "", text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r"[^\w\s.,!?'-]", " ", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _classify_sentiment(score: float) -> str:
        """
        Classify a compound sentiment score into a label.
        
        Uses standard VADER thresholds adapted for financial context:
        - BULLISH: score > 0.05 (positive sentiment)
        - BEARISH: score < -0.05 (negative sentiment)  
        - NEUTRAL: -0.05 <= score <= 0.05
        
        Args:
            score: Compound sentiment score (-1.0 to 1.0).
            
        Returns:
            Sentiment label: 'BULLISH', 'BEARISH', or 'NEUTRAL'.
        """
        if score > 0.05:
            return "BULLISH"
        elif score < -0.05:
            return "BEARISH"
        else:
            return "NEUTRAL"
