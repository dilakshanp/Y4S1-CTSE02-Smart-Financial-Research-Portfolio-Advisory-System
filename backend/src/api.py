"""
Flask REST API Server for the Financial Research MAS.

Exposes the multi-agent pipeline via HTTP endpoints with
Server-Sent Events (SSE) for real-time agent activity streaming.

Endpoints:
    POST /api/research          — Submit a new research query
    GET  /api/research/<id>     — Get results of a query
    GET  /api/research/<id>/stream — SSE stream of agent logs
    GET  /api/sessions          — List past research sessions
    GET  /api/health            — Health check

Usage:
    python -m src.api
"""

import json
import queue
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from flask import Flask, Response, jsonify, request
from flask_cors import CORS

from src.crew.research_crew import ResearchCrew
from src.database.db_manager import DatabaseManager
from src.observability.logger import AgentObserver

# ============================================
# Flask App Configuration
# ============================================

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# In-memory store for active research sessions
active_queries: Dict[str, Dict[str, Any]] = {}
# Event queues for SSE streaming (one per query_id)
event_queues: Dict[str, queue.Queue] = {}

db = DatabaseManager()


# ============================================
# Helper: Run pipeline in background thread
# ============================================

def run_pipeline(query_id: str, user_query: str) -> None:
    """
    Execute the research pipeline in a background thread.

    Updates the active_queries dict and pushes events to the
    SSE queue as the pipeline progresses.
    """
    q = event_queues.get(query_id)

    def push_event(event_type: str, data: Any) -> None:
        """Push an SSE event to the queue."""
        if q:
            q.put({
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            })

    try:
        push_event("status", {"status": "initializing", "message": "Creating research crew..."})

        crew = ResearchCrew(verbose=False)
        crew.state = None

        # Override observer to capture events for SSE
        original_log_event = crew.observer.log_event

        def patched_log_event(agent_name, event_type, **kwargs):
            event = original_log_event(agent_name, event_type, **kwargs)
            push_event("agent_log", {
                "agent": agent_name,
                "event_type": event_type,
                "tool_name": kwargs.get("tool_name"),
                "input": str(kwargs.get("input_data", ""))[:200],
                "output": str(kwargs.get("output_data", ""))[:500],
                "duration_ms": kwargs.get("duration_ms"),
            })
            return event

        crew.observer.log_event = patched_log_event

        push_event("status", {"status": "running", "message": "Pipeline started. Agents are working..."})

        # Execute the crew pipeline
        results = crew.run(user_query)

        # Store results
        active_queries[query_id]["status"] = results.get("status", "completed")
        active_queries[query_id]["results"] = results
        active_queries[query_id]["completed_at"] = datetime.now().isoformat()

        push_event("complete", {
            "status": results.get("status", "completed"),
            "result": results.get("result", ""),
            "execution_summary": results.get("execution_summary", {}),
            "state_summary": results.get("state_summary", {}),
            "total_duration_ms": results.get("total_duration_ms", 0),
        })

    except Exception as e:
        error_msg = str(e)
        active_queries[query_id]["status"] = "failed"
        active_queries[query_id]["error"] = error_msg
        push_event("error", {"message": error_msg})

    finally:
        # Signal stream end
        push_event("done", {"message": "Stream ended"})


# ============================================
# API Endpoints
# ============================================

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    try:
        from langchain_community.llms import Ollama
        llm = Ollama(model="llama3:8b", base_url="http://localhost:11434")
        # Quick connectivity test
        ollama_ok = True
        ollama_msg = "Connected"
    except Exception as e:
        ollama_ok = False
        ollama_msg = str(e)

    return jsonify({
        "status": "healthy",
        "ollama": {"connected": ollama_ok, "message": ollama_msg},
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/api/research", methods=["POST"])
def submit_research():
    """Submit a new research query."""
    data = request.get_json()
    if not data or not data.get("query"):
        return jsonify({"error": "Missing 'query' field"}), 400

    user_query = data["query"].strip()
    if len(user_query) < 3:
        return jsonify({"error": "Query is too short"}), 400

    query_id = str(uuid.uuid4())[:8]

    # Initialize tracking
    active_queries[query_id] = {
        "query_id": query_id,
        "query": user_query,
        "status": "queued",
        "submitted_at": datetime.now().isoformat(),
        "results": None,
        "error": None,
    }
    event_queues[query_id] = queue.Queue()

    # Run pipeline in background thread
    thread = threading.Thread(
        target=run_pipeline,
        args=(query_id, user_query),
        daemon=True,
    )
    thread.start()

    return jsonify({
        "query_id": query_id,
        "status": "queued",
        "message": "Research pipeline started",
    }), 202


@app.route("/api/research/<query_id>", methods=["GET"])
def get_research(query_id: str):
    """Get the status and results of a research query."""
    if query_id not in active_queries:
        return jsonify({"error": "Query not found"}), 404

    info = active_queries[query_id]
    return jsonify(info)


@app.route("/api/research/<query_id>/stream", methods=["GET"])
def stream_research(query_id: str):
    """
    Server-Sent Events stream for real-time agent activity.
    
    Frontend connects to this endpoint to receive live updates
    as the pipeline executes.
    """
    if query_id not in event_queues:
        return jsonify({"error": "Query not found or stream expired"}), 404

    def generate():
        q = event_queues[query_id]
        while True:
            try:
                event = q.get(timeout=120)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") == "done":
                    break
            except queue.Empty:
                # Send keepalive
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"

        # Cleanup queue after stream ends
        if query_id in event_queues:
            del event_queues[query_id]

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    """List past research sessions from the database."""
    try:
        sessions = db.get_recent_sessions(limit=50)
        return jsonify({"sessions": sessions})
    except Exception as e:
        return jsonify({"sessions": [], "error": str(e)})


@app.route("/api/sample-queries", methods=["GET"])
def sample_queries():
    """Return sample queries for the frontend."""
    queries = [
        "Analyze AAPL, MSFT, GOOGL for a moderate-risk portfolio",
        "Research Tesla and Amazon stock performance",
        "Evaluate NVDA and AMD for tech sector investment",
        "Give me a risk analysis of META, NFLX, and DIS",
        "Analyze Apple stock for long-term investment",
    ]
    return jsonify({"queries": queries})


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    print("\n📊 Financial Research MAS — API Server")
    print("=" * 45)
    print("  API:       http://localhost:5001/api")
    print("  Health:    http://localhost:5001/api/health")
    print("  Frontend:  http://localhost:5173")
    print("=" * 45)
    app.run(host="0.0.0.0", port=5001, debug=True, threaded=True)
