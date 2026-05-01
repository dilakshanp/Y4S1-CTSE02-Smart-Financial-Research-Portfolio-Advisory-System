"""
Research Crew Orchestration for the Smart Financial Research MAS.

This module assembles the complete multi-agent crew and manages the
sequential execution pipeline. It brings together all 4 agents,
assigns their tasks, configures state management, and integrates
the observability system.

Pipeline Flow:
    User Query → Coordinator → Market Analyst → Risk Specialist → 
    Portfolio Advisor → Advisory Report

Key Features:
    - Sequential task execution with context passing
    - Integrated observability via AgentObserver and callbacks
    - Database persistence of all research sessions
    - Comprehensive error handling with state preservation
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, Optional

from crewai import Crew, Process

from src.agents.coordinator import create_coordinator_agent
from src.agents.market_analyst import create_market_analyst_agent
from src.agents.portfolio_advisor import create_portfolio_advisor_agent
from src.agents.risk_specialist import create_risk_specialist_agent
from src.database.db_manager import DatabaseManager
from src.observability.callbacks import CrewCallbackHandler
from src.observability.logger import AgentObserver
from src.state.models import ResearchState
from src.tasks.research_tasks import (
    create_advisory_report_task,
    create_coordination_task,
    create_risk_assessment_task,
    create_sentiment_analysis_task,
)


class ResearchCrew:
    """
    Assembles and manages the multi-agent research crew.
    
    Orchestrates the sequential pipeline of 4 agents, manages
    global state, integrates observability, and persists results
    to the database.
    
    Attributes:
        observer: AgentObserver for execution logging.
        callback_handler: CrewAI callback handler.
        db: DatabaseManager for persistence.
        state: ResearchState for global context.
    """

    def __init__(self, verbose: bool = True) -> None:
        """
        Initialize the ResearchCrew.
        
        Sets up the observability system, database connection,
        and prepares the agent/task configuration.
        
        Args:
            verbose: Whether to enable verbose agent output.
        """
        self.verbose: bool = verbose
        
        # Initialize observability
        self.observer: AgentObserver = AgentObserver(
            console_output=verbose
        )
        self.callback_handler: CrewCallbackHandler = CrewCallbackHandler(
            self.observer
        )
        
        # Initialize database
        self.db: DatabaseManager = DatabaseManager()
        
        # State will be initialized per-query
        self.state: Optional[ResearchState] = None

    def run(self, user_query: str) -> Dict[str, Any]:
        """
        Execute the full research pipeline for a user query.
        
        Creates all agents and tasks, assembles the crew, executes
        the sequential pipeline, and returns the results.
        
        Args:
            user_query: The user's research query (e.g., 
                       "Analyze AAPL, MSFT, GOOGL for investment").
                       
        Returns:
            Dictionary containing:
                - query_id: Unique identifier for this research
                - status: 'completed' or 'failed'
                - result: The crew's output
                - state_summary: Summary of the research state
                - execution_summary: Observability metrics
                - report_path: Path to generated report (if any)
        """
        start_time = time.time()
        
        # Initialize state for this query
        self.state = ResearchState(user_query=user_query)
        
        # Log session start
        self.callback_handler.on_crew_start("FinancialResearchCrew")
        self.observer.log_event(
            agent_name="SYSTEM",
            event_type="QUERY_RECEIVED",
            input_data=user_query,
            metadata={"query_id": self.state.query_id}
        )
        
        # Persist session to database
        self.db.save_research_session(
            query_id=self.state.query_id,
            user_query=user_query,
            tickers=[],  # Will be populated by Coordinator
            status="in_progress"
        )
        
        try:
            # ========================================
            # 1. Create Agents
            # ========================================
            self.observer.log_event(
                agent_name="SYSTEM",
                event_type="AGENTS_INIT",
                output_data="Creating 4 agents: Coordinator, Market Analyst, Risk Specialist, Portfolio Advisor"
            )
            
            coordinator = create_coordinator_agent()
            market_analyst = create_market_analyst_agent()
            risk_specialist = create_risk_specialist_agent()
            portfolio_advisor = create_portfolio_advisor_agent()

            # ========================================
            # 2. Create Tasks (Sequential Pipeline)
            # ========================================
            self.observer.log_event(
                agent_name="SYSTEM",
                event_type="TASKS_INIT",
                output_data="Creating 4 sequential tasks"
            )
            
            # Task 1: Coordinator parses query and fetches market data
            coord_task = create_coordination_task(coordinator, user_query)
            
            # Task 2: Market Analyst analyzes sentiment
            sentiment_task = create_sentiment_analysis_task(market_analyst)
            
            # Task 3: Risk Specialist calculates risk
            risk_task = create_risk_assessment_task(risk_specialist)
            
            # Task 4: Portfolio Advisor generates report
            advisory_task = create_advisory_report_task(portfolio_advisor)

            # ========================================
            # 3. Assemble and Execute Crew
            # ========================================
            self.observer.log_event(
                agent_name="SYSTEM",
                event_type="CREW_ASSEMBLE",
                output_data="Assembling crew with sequential process"
            )
            
            # Sequential process ensures each task's output is passed as
            # context to the next task in the pipeline automatically
            crew = Crew(
                agents=[coordinator, market_analyst, risk_specialist, portfolio_advisor],
                tasks=[coord_task, sentiment_task, risk_task, advisory_task],
                process=Process.sequential,
                verbose=True if self.verbose else 0,
            )
            
            # Execute the crew
            self.observer.log_event(
                agent_name="SYSTEM",
                event_type="EXECUTION_START",
                output_data="Starting sequential crew execution"
            )
            
            result = crew.kickoff()
            
            # ========================================
            # 4. Process Results
            # ========================================
            total_duration = (time.time() - start_time) * 1000
            
            self.callback_handler.on_crew_end(
                str(result), "FinancialResearchCrew"
            )
            
            # Update state
            self.state.status = "completed"
            self.state.advisory_report = str(result)
            
            # Update database
            self.db.update_session_status(
                self.state.query_id, "completed"
            )
            
            # Export logs
            log_path = self.observer.export_logs()
            
            # Build response
            response: Dict[str, Any] = {
                "query_id": self.state.query_id,
                "status": "completed",
                "user_query": user_query,
                "result": str(result),
                "state_summary": self.state.get_summary(),
                "execution_summary": self.observer.get_execution_summary(),
                "log_path": str(log_path),
                "total_duration_ms": round(total_duration, 2),
                "timestamp": datetime.now().isoformat(),
            }
            
            self.observer.log_event(
                agent_name="SYSTEM",
                event_type="EXECUTION_COMPLETE",
                output_data=f"Pipeline completed in {total_duration:.0f}ms",
                duration_ms=total_duration,
                metadata={"query_id": self.state.query_id}
            )
            
            return response

        except Exception as e:
            # Handle pipeline failures
            error_msg = f"Pipeline execution failed: {str(e)}"
            
            self.observer.log_error("SYSTEM", error_msg)
            
            if self.state:
                self.state.status = "failed"
                self.state.add_error(error_msg)
                self.db.update_session_status(
                    self.state.query_id,
                    "failed",
                    self.state.errors
                )
            
            # Still export logs for debugging
            log_path = self.observer.export_logs()
            
            total_duration = (time.time() - start_time) * 1000
            
            return {
                "query_id": self.state.query_id if self.state else "unknown",
                "status": "failed",
                "user_query": user_query,
                "error": error_msg,
                "state_summary": self.state.get_summary() if self.state else {},
                "execution_summary": self.observer.get_execution_summary(),
                "log_path": str(log_path),
                "total_duration_ms": round(total_duration, 2),
                "timestamp": datetime.now().isoformat(),
            }
