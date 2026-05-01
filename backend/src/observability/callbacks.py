"""
CrewAI Callback Handlers for Agent Observability.

Implements callback hooks that integrate with CrewAI's execution lifecycle
to automatically capture agent interactions, tool usage, and task transitions.
These callbacks feed into the AgentObserver for unified logging.

Callback Events Captured:
    - on_agent_start / on_agent_end
    - on_tool_start / on_tool_end
    - on_task_start / on_task_end
    - on_crew_start / on_crew_end
"""

import time
from typing import Any, Dict, Optional

from src.observability.logger import AgentObserver


class CrewCallbackHandler:
    """
    Callback handler that integrates with CrewAI's execution lifecycle.
    
    Captures all agent, tool, and task events and forwards them to
    the AgentObserver for structured logging and tracing.
    
    Attributes:
        observer: The AgentObserver instance for logging events.
        _timers: Dictionary tracking start times for duration calculation.
    """

    def __init__(self, observer: AgentObserver) -> None:
        """
        Initialize the callback handler.
        
        Args:
            observer: AgentObserver instance for logging.
        """
        self.observer: AgentObserver = observer
        self._timers: Dict[str, float] = {}

    def on_crew_start(self, crew_name: str = "ResearchCrew") -> None:
        """Called when the crew begins execution."""
        self._timers["crew"] = time.time()
        self.observer.log_event(
            agent_name="SYSTEM",
            event_type="CREW_START",
            metadata={"crew_name": crew_name}
        )

    def on_crew_end(
        self, output: str = "", crew_name: str = "ResearchCrew"
    ) -> None:
        """Called when the crew completes execution."""
        duration = self._get_duration("crew")
        self.observer.log_event(
            agent_name="SYSTEM",
            event_type="CREW_END",
            output_data=output,
            duration_ms=duration,
            metadata={"crew_name": crew_name}
        )

    def on_agent_start(self, agent_name: str, task: str = "") -> None:
        """
        Called when an agent begins working on a task.
        
        Args:
            agent_name: Name of the agent starting execution.
            task: Description of the task assigned to the agent.
        """
        timer_key = f"agent_{agent_name}"
        self._timers[timer_key] = time.time()
        self.observer.log_agent_start(agent_name, task)

    def on_agent_end(
        self, agent_name: str, output: str = "", success: bool = True
    ) -> None:
        """
        Called when an agent completes its task.
        
        Args:
            agent_name: Name of the agent completing execution.
            output: The agent's output.
            success: Whether the agent completed successfully.
        """
        self.observer.log_agent_end(agent_name, output, success)

    def on_tool_start(
        self, agent_name: str, tool_name: str, tool_input: Any = None
    ) -> None:
        """
        Called when an agent invokes a tool.
        
        Args:
            agent_name: Name of the agent using the tool.
            tool_name: Name of the tool being invoked.
            tool_input: Input arguments passed to the tool.
        """
        timer_key = f"tool_{agent_name}_{tool_name}"
        self._timers[timer_key] = time.time()
        self.observer.log_tool_call(agent_name, tool_name, tool_input)

    def on_tool_end(
        self,
        agent_name: str,
        tool_name: str,
        result: Any = None,
        success: bool = True
    ) -> None:
        """
        Called when a tool completes execution.
        
        Args:
            agent_name: Name of the agent that used the tool.
            tool_name: Name of the tool that completed.
            result: The tool's output.
            success: Whether the tool executed successfully.
        """
        timer_key = f"tool_{agent_name}_{tool_name}"
        duration = self._get_duration(timer_key)
        self.observer.log_tool_result(
            agent_name, tool_name, result, duration, success
        )

    def on_task_start(
        self, task_name: str, agent_name: str = ""
    ) -> None:
        """
        Called when a task begins execution.
        
        Args:
            task_name: Name or description of the task.
            agent_name: Name of the agent assigned to the task.
        """
        timer_key = f"task_{task_name}"
        self._timers[timer_key] = time.time()
        self.observer.log_event(
            agent_name=agent_name or "SYSTEM",
            event_type="TASK_START",
            input_data=task_name,
            metadata={"task": task_name}
        )

    def on_task_end(
        self,
        task_name: str,
        output: str = "",
        agent_name: str = "",
        success: bool = True
    ) -> None:
        """
        Called when a task completes execution.
        
        Args:
            task_name: Name or description of the task.
            output: The task's output.
            agent_name: Name of the agent that completed the task.
            success: Whether the task completed successfully.
        """
        timer_key = f"task_{task_name}"
        duration = self._get_duration(timer_key)
        self.observer.log_event(
            agent_name=agent_name or "SYSTEM",
            event_type="TASK_END",
            output_data=output,
            duration_ms=duration,
            success=success,
            metadata={"task": task_name}
        )

    def on_error(
        self, agent_name: str, error: str, context: Optional[Dict] = None
    ) -> None:
        """
        Called when an error occurs during execution.
        
        Args:
            agent_name: Name of the agent where the error occurred.
            error: Error message.
            context: Additional error context.
        """
        self.observer.log_error(agent_name, error, context)

    def _get_duration(self, timer_key: str) -> Optional[float]:
        """
        Calculate duration from a stored timer.
        
        Args:
            timer_key: Key for the timer in the _timers dict.
            
        Returns:
            Duration in milliseconds, or None if timer not found.
        """
        start = self._timers.pop(timer_key, None)
        if start is not None:
            return (time.time() - start) * 1000
        return None
