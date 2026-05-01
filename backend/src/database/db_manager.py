"""
SQLite Database Manager for the Smart Financial Research MAS.

Provides persistent storage for research queries, market data,
risk metrics, and generated reports. Uses a local SQLite database
to maintain an audit trail and enable historical comparisons.

This module handles all database operations including:
    - Schema creation and migration
    - Storing research sessions with full state
    - Querying historical data for analysis
    - Report metadata persistence
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import DATABASE_PATH


class DatabaseManager:
    """
    Manages all SQLite database operations for the research system.
    
    Provides methods to store and retrieve research sessions,
    market data, risk metrics, and report metadata.
    
    Attributes:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Initialize the DatabaseManager.
        
        Args:
            db_path: Optional custom path to the SQLite database.
                     Defaults to the configured DATABASE_PATH.
        """
        self.db_path: Path = db_path or DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Create and return a new database connection.
        
        Returns:
            sqlite3.Connection: A new SQLite connection with Row factory.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _initialize_schema(self) -> None:
        """Create database tables if they don't exist."""
        conn = self._get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS research_sessions (
                    query_id TEXT PRIMARY KEY,
                    user_query TEXT NOT NULL,
                    tickers TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'initialized',
                    research_plan TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    errors TEXT
                );

                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    current_price REAL,
                    price_change_pct REAL,
                    volume INTEGER,
                    market_cap REAL,
                    pe_ratio REAL,
                    week_52_high REAL,
                    week_52_low REAL,
                    historical_prices TEXT,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES research_sessions(query_id)
                );

                CREATE TABLE IF NOT EXISTS sentiment_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id TEXT NOT NULL,
                    query_text TEXT NOT NULL,
                    articles_analyzed INTEGER,
                    average_sentiment REAL,
                    sentiment_label TEXT,
                    top_headlines TEXT,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES research_sessions(query_id)
                );

                CREATE TABLE IF NOT EXISTS risk_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    volatility REAL,
                    beta REAL,
                    sharpe_ratio REAL,
                    var_95 REAL,
                    max_drawdown REAL,
                    risk_category TEXT,
                    confidence REAL,
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES research_sessions(query_id)
                );

                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id TEXT NOT NULL,
                    report_content TEXT NOT NULL,
                    report_path TEXT,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES research_sessions(query_id)
                );

                CREATE TABLE IF NOT EXISTS agent_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    input_data TEXT,
                    output_data TEXT,
                    tool_name TEXT,
                    duration_ms REAL,
                    success BOOLEAN DEFAULT 1,
                    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES research_sessions(query_id)
                );

                CREATE INDEX IF NOT EXISTS idx_market_data_query 
                    ON market_data(query_id);
                CREATE INDEX IF NOT EXISTS idx_sentiment_query 
                    ON sentiment_results(query_id);
                CREATE INDEX IF NOT EXISTS idx_risk_query 
                    ON risk_metrics(query_id);
                CREATE INDEX IF NOT EXISTS idx_agent_logs_query 
                    ON agent_logs(query_id);
            """)
            conn.commit()
        finally:
            conn.close()

    def save_research_session(
        self,
        query_id: str,
        user_query: str,
        tickers: List[str],
        status: str = "initialized",
        research_plan: Optional[Dict] = None
    ) -> None:
        """
        Save or update a research session.
        
        Args:
            query_id: Unique identifier for the research query.
            user_query: The original user query string.
            tickers: List of ticker symbols being analyzed.
            status: Current status of the research session.
            research_plan: Optional structured research plan.
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO research_sessions 
                   (query_id, user_query, tickers, status, research_plan)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    query_id,
                    user_query,
                    json.dumps(tickers),
                    status,
                    json.dumps(research_plan) if research_plan else None,
                )
            )
            conn.commit()
        finally:
            conn.close()

    def update_session_status(
        self,
        query_id: str,
        status: str,
        errors: Optional[List[str]] = None
    ) -> None:
        """
        Update the status of a research session.
        
        Args:
            query_id: Unique identifier for the research query.
            status: New status value.
            errors: Optional list of error messages.
        """
        conn = self._get_connection()
        try:
            if status in ("completed", "failed"):
                conn.execute(
                    """UPDATE research_sessions 
                       SET status = ?, completed_at = ?, errors = ?
                       WHERE query_id = ?""",
                    (
                        status,
                        datetime.now().isoformat(),
                        json.dumps(errors) if errors else None,
                        query_id,
                    )
                )
            else:
                conn.execute(
                    """UPDATE research_sessions SET status = ? WHERE query_id = ?""",
                    (status, query_id)
                )
            conn.commit()
        finally:
            conn.close()

    def save_market_data(
        self, query_id: str, data: Dict[str, Any]
    ) -> None:
        """
        Save market data for a specific ticker.
        
        Args:
            query_id: Research session identifier.
            data: Dictionary containing market data fields.
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT INTO market_data 
                   (query_id, ticker, current_price, price_change_pct, volume,
                    market_cap, pe_ratio, week_52_high, week_52_low, historical_prices)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    query_id,
                    data.get("ticker", ""),
                    data.get("current_price", 0),
                    data.get("price_change_pct", 0),
                    data.get("volume", 0),
                    data.get("market_cap"),
                    data.get("pe_ratio"),
                    data.get("week_52_high"),
                    data.get("week_52_low"),
                    json.dumps(data.get("historical_prices", [])),
                )
            )
            conn.commit()
        finally:
            conn.close()

    def save_risk_metrics(
        self, query_id: str, data: Dict[str, Any]
    ) -> None:
        """
        Save risk metrics for a specific ticker.
        
        Args:
            query_id: Research session identifier.
            data: Dictionary containing risk metric fields.
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT INTO risk_metrics 
                   (query_id, ticker, volatility, beta, sharpe_ratio,
                    var_95, max_drawdown, risk_category, confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    query_id,
                    data.get("ticker", ""),
                    data.get("volatility", 0),
                    data.get("beta", 0),
                    data.get("sharpe_ratio", 0),
                    data.get("var_95", 0),
                    data.get("max_drawdown", 0),
                    data.get("risk_category", "UNKNOWN"),
                    data.get("confidence", 0),
                )
            )
            conn.commit()
        finally:
            conn.close()

    def save_report(
        self, query_id: str, report_content: str, report_path: Optional[str] = None
    ) -> None:
        """
        Save a generated advisory report.
        
        Args:
            query_id: Research session identifier.
            report_content: Full report content string.
            report_path: Optional file path where report was saved.
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT INTO reports (query_id, report_content, report_path)
                   VALUES (?, ?, ?)""",
                (query_id, report_content, report_path)
            )
            conn.commit()
        finally:
            conn.close()

    def save_agent_log(
        self, query_id: str, log_entry: Dict[str, Any]
    ) -> None:
        """
        Save an agent log entry.
        
        Args:
            query_id: Research session identifier.
            log_entry: Dictionary containing log entry fields.
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT INTO agent_logs 
                   (query_id, agent_name, action_type, input_data, 
                    output_data, tool_name, duration_ms, success)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    query_id,
                    log_entry.get("agent_name", ""),
                    log_entry.get("action_type", ""),
                    log_entry.get("input_data"),
                    log_entry.get("output_data"),
                    log_entry.get("tool_name"),
                    log_entry.get("duration_ms"),
                    log_entry.get("success", True),
                )
            )
            conn.commit()
        finally:
            conn.close()

    def get_session(self, query_id: str) -> Optional[Dict]:
        """
        Retrieve a research session by ID.
        
        Args:
            query_id: Research session identifier.
            
        Returns:
            Dictionary with session data, or None if not found.
        """
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM research_sessions WHERE query_id = ?",
                (query_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """
        Retrieve recent research sessions.
        
        Args:
            limit: Maximum number of sessions to return.
            
        Returns:
            List of session dictionaries ordered by creation time.
        """
        conn = self._get_connection()
        try:
            rows = conn.execute(
                """SELECT * FROM research_sessions 
                   ORDER BY created_at DESC LIMIT ?""",
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_agent_logs(self, query_id: str) -> List[Dict]:
        """
        Retrieve all agent logs for a research session.
        
        Args:
            query_id: Research session identifier.
            
        Returns:
            List of agent log dictionaries.
        """
        conn = self._get_connection()
        try:
            rows = conn.execute(
                """SELECT * FROM agent_logs 
                   WHERE query_id = ? ORDER BY logged_at ASC""",
                (query_id,)
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
