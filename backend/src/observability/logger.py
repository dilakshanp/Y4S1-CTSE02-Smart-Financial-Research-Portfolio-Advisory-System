"""
Custom JSON Logger for the Smart Financial Research MAS.

Implements a structured logging system that records every agent action
as a JSON event. This provides comprehensive observability into the
multi-agent pipeline execution for debugging, auditing, and performance analysis.

Log Format:
    Each log entry contains:
    - timestamp: ISO-8601 formatted timestamp
    - agent_name: Name of the agent performing the action
    - event_type: THINK | TOOL_CALL | TOOL_RESULT | OUTPUT | ERROR | SYSTEM
    - input_data: Input provided to the action (truncated to 500 chars)
    - output_data: Output produced by the action (truncated to 500 chars)
    - tool_name: Name of tool used (if applicable)
    - duration_ms: Time taken for the action in milliseconds
    - metadata: Additional contextual information
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import LOG_DIR, LOG_LEVEL


class AgentObserver:
    """
    Custom observability handler for tracking agent execution.
    
    Provides structured JSON logging for all agent actions including
    tool calls, reasoning steps, and output generation. Supports both
    file-based and console output for development and production use.
    
    Attributes:
        log_dir: Directory where log files are stored.
        session_id: Unique identifier for the current logging session.
        execution_log: In-memory list of all log events.
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        session_id: Optional[str] = None,
        console_output: bool = True
    ) -> None:
        """
        Initialize the AgentObserver.
        
        Args:
            log_dir: Directory for log files. Defaults to configured LOG_DIR.
            session_id: Unique session ID. Auto-generated if not provided.
            console_output: Whether to also print logs to console.
        """
        self.log_dir: Path = log_dir or LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_id: str = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.execution_log: List[Dict[str, Any]] = []
        self.console_output: bool = console_output
        self._start_time: Optional[float] = None
        self._action_start: Optional[float] = None
        
        # Configure Python logger for file output
        self._logger = logging.getLogger(f"agent_observer_{self.session_id}")
        self._logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        
        # File handler — JSON log file
        log_file = self.log_dir / f"execution_{self.session_id}.json"
        file_handler = logging.FileHandler(str(log_file), mode="a")
        file_handler.setLevel(logging.DEBUG)
        self._logger.addHandler(file_handler)
        
        # Console handler (rich formatting)
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-5s | %(message)s",
                datefmt="%H:%M:%S"
            )
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)

        # Log session start
        self._log_system_event("SESSION_START", f"Observer session {self.session_id} started")

    def log_event(
        self,
        agent_name: str,
        event_type: str,
        input_data: Any = None,
        output_data: Any = None,
        tool_name: Optional[str] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True
    ) -> Dict[str, Any]:
        """
        Log a structured agent event.
        
        Args:
            agent_name: Name of the agent performing the action.
            event_type: Type of event (THINK, TOOL_CALL, TOOL_RESULT, OUTPUT, ERROR).
            input_data: Input data for the action.
            output_data: Output data from the action.
            tool_name: Name of the tool used (if applicable).
            duration_ms: Duration of the action in milliseconds.
            metadata: Additional contextual information.
            success: Whether the action was successful.
            
        Returns:
            The created log event dictionary.
        """
        event: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "agent": agent_name,
            "event_type": event_type,
            "input": self._truncate(input_data),
            "output": self._truncate(output_data),
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "success": success,
            "metadata": metadata or {},
        }
        
        self.execution_log.append(event)
        self._write_to_file(event)
        
        # Console log with color-coded event type
        level = logging.ERROR if not success else logging.INFO
        icon = self._get_event_icon(event_type)
        self._logger.log(
            level,
            f"{icon} [{agent_name}] {event_type}"
            + (f" → {tool_name}" if tool_name else "")
            + (f" ({duration_ms:.0f}ms)" if duration_ms else "")
        )
        
        return event

    def log_agent_start(self, agent_name: str, task_description: str) -> None:
        """Log when an agent begins execution."""
        import time
        self._action_start = time.time()
        self.log_event(
            agent_name=agent_name,
            event_type="AGENT_START",
            input_data=task_description,
            metadata={"phase": "start"}
        )

    def log_agent_end(
        self, agent_name: str, output: str, success: bool = True
    ) -> None:
        """Log when an agent completes execution."""
        import time
        duration = None
        if self._action_start:
            duration = (time.time() - self._action_start) * 1000
            self._action_start = None
        
        self.log_event(
            agent_name=agent_name,
            event_type="AGENT_END",
            output_data=output,
            duration_ms=duration,
            success=success,
            metadata={"phase": "end"}
        )

    def log_tool_call(
        self, agent_name: str, tool_name: str, tool_input: Any
    ) -> None:
        """Log when an agent invokes a tool."""
        self.log_event(
            agent_name=agent_name,
            event_type="TOOL_CALL",
            input_data=tool_input,
            tool_name=tool_name
        )

    def log_tool_result(
        self,
        agent_name: str,
        tool_name: str,
        result: Any,
        duration_ms: Optional[float] = None,
        success: bool = True
    ) -> None:
        """Log the result of a tool execution."""
        self.log_event(
            agent_name=agent_name,
            event_type="TOOL_RESULT",
            output_data=result,
            tool_name=tool_name,
            duration_ms=duration_ms,
            success=success
        )

    def log_error(
        self, agent_name: str, error_message: str, metadata: Optional[Dict] = None
    ) -> None:
        """Log an error event."""
        self.log_event(
            agent_name=agent_name,
            event_type="ERROR",
            output_data=error_message,
            success=False,
            metadata=metadata
        )

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the entire execution.
        
        Returns:
            Dictionary containing execution statistics.
        """
        total_events = len(self.execution_log)
        tool_calls = [e for e in self.execution_log if e["event_type"] == "TOOL_CALL"]
        errors = [e for e in self.execution_log if not e["success"]]
        agents = set(e["agent"] for e in self.execution_log if e["agent"] != "SYSTEM")
        
        total_duration = sum(
            e.get("duration_ms", 0) or 0 for e in self.execution_log
        )
        
        return {
            "session_id": self.session_id,
            "total_events": total_events,
            "total_tool_calls": len(tool_calls),
            "total_errors": len(errors),
            "agents_involved": list(agents),
            "total_duration_ms": total_duration,
            "tools_used": list(set(
                e["tool_name"] for e in tool_calls if e["tool_name"]
            )),
        }

    def export_logs(self, filepath: Optional[Path] = None) -> Path:
        """
        Export all logs to a JSON file.
        
        Args:
            filepath: Optional custom file path.
            
        Returns:
            Path to the exported log file.
        """
        export_path = filepath or (
            self.log_dir / f"full_execution_{self.session_id}.json"
        )
        
        export_data = {
            "session_id": self.session_id,
            "summary": self.get_execution_summary(),
            "events": self.execution_log,
        }
        
        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2, default=str)
        
        self._log_system_event(
            "EXPORT", f"Logs exported to {export_path}"
        )
        return export_path

    def _write_to_file(self, event: Dict[str, Any]) -> None:
        """Write a single event as a JSON line to the log file."""
        log_file = self.log_dir / f"execution_{self.session_id}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")

    def _log_system_event(self, event_type: str, message: str) -> None:
        """Log a system-level event."""
        self.log_event(
            agent_name="SYSTEM",
            event_type=event_type,
            output_data=message,
            metadata={"system": True}
        )

    @staticmethod
    def _truncate(data: Any, max_length: int = 500) -> Optional[str]:
        """Truncate data to a maximum string length."""
        if data is None:
            return None
        text = str(data)
        return text[:max_length] + "..." if len(text) > max_length else text

    @staticmethod
    def _get_event_icon(event_type: str) -> str:
        """Get an icon for the event type."""
        icons = {
            "AGENT_START": "🚀",
            "AGENT_END": "✅",
            "TOOL_CALL": "🔧",
            "TOOL_RESULT": "📦",
            "THINK": "🧠",
            "OUTPUT": "📄",
            "ERROR": "❌",
            "SESSION_START": "🏁",
            "EXPORT": "💾",
        }
        return icons.get(event_type, "📋")
