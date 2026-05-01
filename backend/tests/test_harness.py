"""
Unified Testing Harness for the Smart Financial Research MAS.

This module provides the common testing infrastructure shared by all
students, including:
    - JSON structure validation helpers
    - LLM-as-a-Judge evaluation framework
    - Performance benchmarking utilities
    - Property-based testing helpers
    - Integration test for the full pipeline

Each student contributes their specific test cases and assertions
to validate their own agent's output in their individual test files.
"""

import json
import time
from typing import Any, Dict, List, Optional

import pytest

from src.state.models import ResearchState


# ============================================
# JSON Structure Validation Helpers
# ============================================

class JSONValidator:
    """Helper class for validating JSON structure and content."""

    @staticmethod
    def assert_valid_json(text: str) -> Dict:
        """
        Assert that a string is valid JSON and return the parsed dict.
        
        Args:
            text: String to parse as JSON.
            
        Returns:
            Parsed dictionary.
            
        Raises:
            AssertionError: If the string is not valid JSON.
        """
        try:
            data = json.loads(text)
            assert isinstance(data, dict), "JSON root must be a dictionary"
            return data
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON: {e}\nContent: {text[:500]}")

    @staticmethod
    def assert_has_keys(data: Dict, required_keys: List[str]) -> None:
        """
        Assert that a dictionary contains all required keys.
        
        Args:
            data: Dictionary to check.
            required_keys: List of keys that must be present.
        """
        missing = [key for key in required_keys if key not in data]
        if missing:
            pytest.fail(
                f"Missing required keys: {missing}\n"
                f"Available keys: {list(data.keys())}"
            )

    @staticmethod
    def assert_no_error(data: Dict) -> None:
        """Assert that a tool response does not contain an error."""
        assert not data.get("error", False), (
            f"Tool returned an error: {data.get('message', 'Unknown error')}"
        )

    @staticmethod
    def assert_value_in_range(
        value: float, min_val: float, max_val: float, field_name: str = ""
    ) -> None:
        """Assert that a numeric value is within a specified range."""
        assert min_val <= value <= max_val, (
            f"{field_name}: {value} is not in range [{min_val}, {max_val}]"
        )


# ============================================
# LLM-as-a-Judge Evaluation
# ============================================

class LLMJudge:
    """
    Evaluates agent outputs using heuristic rules.
    
    Since we run on local LLMs, this judge uses deterministic
    heuristics rather than calling an LLM, making tests
    reproducible and fast.
    """

    @staticmethod
    def evaluate_coherence(text: str, min_length: int = 50) -> Dict[str, Any]:
        """
        Evaluate whether text is coherent and substantive.
        
        Args:
            text: Text to evaluate.
            min_length: Minimum acceptable length.
            
        Returns:
            Dictionary with score and feedback.
        """
        issues: List[str] = []
        score: float = 1.0
        
        if len(text) < min_length:
            issues.append(f"Too short ({len(text)} chars, minimum {min_length})")
            score -= 0.3
        
        # Check for common LLM failure patterns
        failure_patterns = [
            "I cannot", "I don't have access", "I'm unable to",
            "As an AI", "I apologize", "Error:", "Failed to"
        ]
        for pattern in failure_patterns:
            if pattern.lower() in text.lower():
                issues.append(f"Contains failure pattern: '{pattern}'")
                score -= 0.2
        
        # Check for data fabrication indicators
        if "made up" in text.lower() or "hypothetical" in text.lower():
            issues.append("Possible data fabrication detected")
            score -= 0.5
        
        return {
            "score": max(0, min(1, score)),
            "passed": score >= 0.5,
            "issues": issues,
        }

    @staticmethod
    def evaluate_financial_report(report: str) -> Dict[str, Any]:
        """
        Evaluate whether a financial report meets quality standards.
        
        Checks for required sections, disclaimer presence,
        and structural completeness.
        
        Args:
            report: Report content to evaluate.
            
        Returns:
            Dictionary with score, passed status, and feedback.
        """
        checks: Dict[str, bool] = {}
        
        report_lower = report.lower()
        
        # Required sections
        checks["has_summary"] = any(
            term in report_lower
            for term in ["executive summary", "summary", "overview"]
        )
        checks["has_market_analysis"] = any(
            term in report_lower
            for term in ["market analysis", "market data", "price"]
        )
        checks["has_risk_section"] = any(
            term in report_lower
            for term in ["risk", "volatility", "risk assessment"]
        )
        checks["has_recommendations"] = any(
            term in report_lower
            for term in ["recommendation", "advise", "suggest"]
        )
        checks["has_disclaimer"] = any(
            term in report_lower
            for term in ["disclaimer", "not financial advice", "educational"]
        )
        
        # Calculate score
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        score = passed / total if total > 0 else 0
        
        return {
            "score": score,
            "passed": score >= 0.6,
            "checks": checks,
            "issues": [k for k, v in checks.items() if not v],
        }


# ============================================
# Performance Benchmarking
# ============================================

class PerformanceBenchmark:
    """Utility for measuring and asserting execution performance."""

    @staticmethod
    def time_execution(func, *args, **kwargs) -> tuple:
        """
        Time the execution of a function.
        
        Args:
            func: Function to execute.
            *args: Positional arguments.
            **kwargs: Keyword arguments.
            
        Returns:
            Tuple of (result, duration_ms).
        """
        start = time.time()
        result = func(*args, **kwargs)
        duration_ms = (time.time() - start) * 1000
        return result, duration_ms

    @staticmethod
    def assert_performance(
        duration_ms: float,
        max_ms: float,
        operation: str = "operation"
    ) -> None:
        """Assert that an operation completed within a time budget."""
        assert duration_ms <= max_ms, (
            f"{operation} took {duration_ms:.0f}ms, "
            f"exceeding maximum of {max_ms:.0f}ms"
        )


# ============================================
# State Validation Helpers
# ============================================

def validate_research_state(state: ResearchState) -> Dict[str, Any]:
    """
    Validate that a ResearchState object is internally consistent.
    
    Args:
        state: ResearchState to validate.
        
    Returns:
        Dictionary with validation results.
    """
    issues: List[str] = []
    
    # Check required fields
    if not state.user_query:
        issues.append("user_query is empty")
    
    if not state.query_id:
        issues.append("query_id is missing")
    
    # Check status validity
    valid_statuses = ["initialized", "in_progress", "completed", "failed"]
    if state.status not in valid_statuses:
        issues.append(f"Invalid status: {state.status}")
    
    # If completed, check that all data is present
    if state.status == "completed":
        if not state.market_data:
            issues.append("Completed state has no market_data")
        if not state.advisory_report:
            issues.append("Completed state has no advisory_report")
    
    # Validate market data types
    if state.market_data:
        for md in state.market_data:
            if md.current_price < 0:
                issues.append(f"{md.ticker}: negative price ({md.current_price})")
    
    # Validate risk metrics ranges
    if state.risk_metrics:
        for rm in state.risk_metrics:
            if rm.confidence < 0 or rm.confidence > 1:
                issues.append(
                    f"{rm.ticker}: confidence {rm.confidence} out of [0, 1]"
                )
            if rm.risk_category not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                issues.append(
                    f"{rm.ticker}: invalid risk_category '{rm.risk_category}'"
                )
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


# ============================================
# Integration Tests
# ============================================

class TestStateManagement:
    """Tests for global state management across the pipeline."""

    def test_state_initialization(self, sample_user_query):
        """Test that ResearchState initializes correctly."""
        state = ResearchState(user_query=sample_user_query)
        
        assert state.user_query == sample_user_query
        assert state.query_id is not None
        assert state.status == "initialized"
        assert state.market_data is None
        assert state.sentiment_results is None
        assert state.risk_metrics is None
        assert state.advisory_report is None
        assert len(state.agent_logs) == 0
        assert len(state.errors) == 0

    def test_state_add_log(self, sample_research_state):
        """Test adding log entries to state."""
        initial_count = len(sample_research_state.agent_logs)
        
        sample_research_state.add_log(
            agent_name="TestAgent",
            action_type="TOOL_CALL",
            input_data="test input",
            output_data="test output",
            tool_name="TestTool",
            duration_ms=150.0,
        )
        
        assert len(sample_research_state.agent_logs) == initial_count + 1
        last_log = sample_research_state.agent_logs[-1]
        assert last_log.agent_name == "TestAgent"
        assert last_log.tool_name == "TestTool"

    def test_state_add_error(self, sample_research_state):
        """Test adding errors to state."""
        initial_count = len(sample_research_state.errors)
        
        sample_research_state.add_error("Test error message")
        
        assert len(sample_research_state.errors) == initial_count + 1
        assert "Test error message" in sample_research_state.errors[-1]

    def test_state_summary(self, sample_research_state):
        """Test state summary generation."""
        summary = sample_research_state.get_summary()
        
        assert "query_id" in summary
        assert "status" in summary
        assert summary["status"] == "completed"
        assert summary["market_data_count"] == 2
        assert summary["sentiment_count"] == 2
        assert summary["risk_metrics_count"] == 2

    def test_state_serialization(self, sample_research_state):
        """Test that state can be serialized and deserialized."""
        json_str = sample_research_state.model_dump_json()
        restored = ResearchState.model_validate_json(json_str)
        
        assert restored.query_id == sample_research_state.query_id
        assert restored.user_query == sample_research_state.user_query
        assert restored.status == sample_research_state.status

    def test_completed_state_validation(self, sample_research_state):
        """Test validation of a completed state."""
        result = validate_research_state(sample_research_state)
        assert result["valid"], f"State validation failed: {result['issues']}"


class TestDatabaseManager:
    """Tests for the SQLite database manager."""

    def test_save_and_retrieve_session(self, tmp_db_path):
        """Test saving and retrieving a research session."""
        from src.database.db_manager import DatabaseManager
        
        db = DatabaseManager(db_path=tmp_db_path)
        
        db.save_research_session(
            query_id="test-123",
            user_query="Test query",
            tickers=["AAPL", "MSFT"],
            status="in_progress"
        )
        
        session = db.get_session("test-123")
        assert session is not None
        assert session["query_id"] == "test-123"
        assert session["user_query"] == "Test query"

    def test_update_session_status(self, tmp_db_path):
        """Test updating session status."""
        from src.database.db_manager import DatabaseManager
        
        db = DatabaseManager(db_path=tmp_db_path)
        
        db.save_research_session(
            query_id="test-456",
            user_query="Test query",
            tickers=["AAPL"],
        )
        
        db.update_session_status("test-456", "completed")
        
        session = db.get_session("test-456")
        assert session["status"] == "completed"

    def test_save_agent_log(self, tmp_db_path):
        """Test saving and retrieving agent logs."""
        from src.database.db_manager import DatabaseManager
        
        db = DatabaseManager(db_path=tmp_db_path)
        
        db.save_research_session(
            query_id="test-789",
            user_query="Test",
            tickers=["AAPL"],
        )
        
        db.save_agent_log("test-789", {
            "agent_name": "Coordinator",
            "action_type": "TOOL_CALL",
            "input_data": "AAPL",
            "tool_name": "Market Data Fetcher",
            "success": True,
        })
        
        logs = db.get_agent_logs("test-789")
        assert len(logs) == 1
        assert logs[0]["agent_name"] == "Coordinator"


class TestObservability:
    """Tests for the observability/logging system."""

    def test_observer_initialization(self, tmp_logs_dir):
        """Test AgentObserver initializes correctly."""
        from src.observability.logger import AgentObserver
        
        observer = AgentObserver(
            log_dir=tmp_logs_dir,
            console_output=False
        )
        
        assert observer.session_id is not None
        assert len(observer.execution_log) > 0  # SESSION_START event

    def test_observer_log_event(self, tmp_logs_dir):
        """Test logging an event."""
        from src.observability.logger import AgentObserver
        
        observer = AgentObserver(
            log_dir=tmp_logs_dir,
            console_output=False
        )
        
        event = observer.log_event(
            agent_name="TestAgent",
            event_type="TOOL_CALL",
            input_data="test input",
            output_data="test output",
            tool_name="TestTool",
        )
        
        assert event["agent"] == "TestAgent"
        assert event["event_type"] == "TOOL_CALL"
        assert event["tool_name"] == "TestTool"

    def test_observer_export(self, tmp_logs_dir):
        """Test exporting logs to file."""
        from src.observability.logger import AgentObserver
        
        observer = AgentObserver(
            log_dir=tmp_logs_dir,
            console_output=False
        )
        
        observer.log_event("TestAgent", "TEST", output_data="test")
        log_path = observer.export_logs()
        
        assert log_path.exists()
        with open(log_path) as f:
            data = json.load(f)
        assert "events" in data
        assert "summary" in data

    def test_execution_summary(self, tmp_logs_dir):
        """Test execution summary generation."""
        from src.observability.logger import AgentObserver
        
        observer = AgentObserver(
            log_dir=tmp_logs_dir,
            console_output=False
        )
        
        observer.log_event("Agent1", "TOOL_CALL", tool_name="Tool1")
        observer.log_event("Agent2", "TOOL_CALL", tool_name="Tool2")
        observer.log_event("Agent1", "ERROR", success=False)
        
        summary = observer.get_execution_summary()
        
        assert summary["total_tool_calls"] == 2
        assert summary["total_errors"] == 1
        assert "Agent1" in summary["agents_involved"]
        assert "Agent2" in summary["agents_involved"]
