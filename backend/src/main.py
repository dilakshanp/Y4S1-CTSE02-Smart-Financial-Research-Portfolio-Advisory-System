"""
Main Entry Point for the Smart Financial Research MAS.

Provides both CLI (command-line) and programmatic interfaces to run
the multi-agent research pipeline. Supports interactive mode and
single-query execution.

Usage:
    # Single query mode
    python -m src.main "Analyze AAPL, MSFT, GOOGL for a moderate-risk portfolio"
    
    # Interactive mode
    python -m src.main --interactive
    
    # Quiet mode (minimal output)
    python -m src.main --quiet "Analyze AAPL"
"""

import argparse
import json
import sys
import time
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.crew.research_crew import ResearchCrew


# Rich console for formatted output
console = Console()


def print_banner() -> None:
    """Display the application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║     📊 Smart Financial Research & Portfolio Advisory MAS     ║
║     ─────────────────────────────────────────────────────    ║
║     Multi-Agent System powered by CrewAI + Ollama            ║
║     Local LLM • Zero Cloud Cost • Full Privacy              ║
╚══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def print_results(results: dict) -> None:
    """
    Display execution results in a formatted table.
    
    Args:
        results: Dictionary containing the crew execution results.
    """
    # Status Panel
    status = results.get("status", "unknown")
    status_color = "green" if status == "completed" else "red"
    
    console.print()
    console.print(Panel(
        f"[bold {status_color}]Status: {status.upper()}[/]\n"
        f"Query ID: {results.get('query_id', 'N/A')}\n"
        f"Duration: {results.get('total_duration_ms', 0):.0f}ms\n"
        f"Log File: {results.get('log_path', 'N/A')}",
        title="📋 Execution Summary",
        border_style=status_color,
    ))
    
    # Execution Metrics Table
    exec_summary = results.get("execution_summary", {})
    if exec_summary:
        table = Table(title="🔍 Observability Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Total Events", str(exec_summary.get("total_events", 0)))
        table.add_row("Tool Calls", str(exec_summary.get("total_tool_calls", 0)))
        table.add_row("Errors", str(exec_summary.get("total_errors", 0)))
        table.add_row(
            "Agents Used",
            ", ".join(exec_summary.get("agents_involved", []))
        )
        table.add_row(
            "Tools Used",
            ", ".join(exec_summary.get("tools_used", []))
        )
        
        console.print(table)
    
    # State Summary
    state_summary = results.get("state_summary", {})
    if state_summary:
        table = Table(title="📦 State Summary")
        table.add_column("Component", style="cyan")
        table.add_column("Count", style="white")
        
        table.add_row("Market Data Items", str(state_summary.get("market_data_count", 0)))
        table.add_row("Sentiment Results", str(state_summary.get("sentiment_count", 0)))
        table.add_row("Risk Metrics", str(state_summary.get("risk_metrics_count", 0)))
        table.add_row("Has Report", str(state_summary.get("has_report", False)))
        table.add_row("Total Logs", str(state_summary.get("total_logs", 0)))
        table.add_row("Total Errors", str(state_summary.get("total_errors", 0)))
        
        console.print(table)
    
    # Report Output
    result_text = results.get("result", "")
    if result_text and status == "completed":
        console.print()
        console.print(Panel(
            Markdown(result_text[:3000]),  # Truncate for display
            title="📄 Advisory Report (Preview)",
            border_style="green",
        ))
    elif status == "failed":
        console.print()
        console.print(Panel(
            results.get("error", "Unknown error occurred"),
            title="❌ Error Details",
            border_style="red",
        ))


def run_query(query: str, verbose: bool = True) -> dict:
    """
    Run a single research query through the pipeline.
    
    Args:
        query: The user's research query.
        verbose: Whether to show detailed agent output.
        
    Returns:
        Dictionary containing the execution results.
    """
    crew = ResearchCrew(verbose=verbose)
    
    console.print(f"\n🔬 [bold]Processing query:[/] {query}")
    console.print(f"⏰ [dim]Started at {datetime.now().strftime('%H:%M:%S')}[/]")
    console.print()
    
    results = crew.run(query)
    
    return results


def interactive_mode(verbose: bool = True) -> None:
    """
    Run the system in interactive mode, accepting multiple queries.
    
    Args:
        verbose: Whether to show detailed agent output.
    """
    print_banner()
    
    console.print(
        "[bold green]Interactive Mode[/] — Type your research queries below.\n"
        "Type [bold]'quit'[/] or [bold]'exit'[/] to stop.\n"
        "Type [bold]'help'[/] for example queries.\n"
    )
    
    while True:
        try:
            query = console.input("\n[bold cyan]📊 Your query > [/]").strip()
            
            if not query:
                continue
            
            if query.lower() in ("quit", "exit", "q"):
                console.print("\n👋 [bold]Goodbye![/] Thank you for using the Financial Research MAS.")
                break
            
            if query.lower() == "help":
                console.print("\n[bold]Example queries:[/]")
                console.print("  • Analyze AAPL, MSFT, GOOGL for a moderate-risk portfolio")
                console.print("  • Research Tesla and Amazon stock performance")
                console.print("  • Evaluate NVDA and AMD for tech sector investment")
                console.print("  • Give me a risk analysis of META, NFLX, and DIS")
                continue
            
            results = run_query(query, verbose=verbose)
            print_results(results)
            
        except KeyboardInterrupt:
            console.print("\n\n👋 [bold]Interrupted. Goodbye![/]")
            break


def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Smart Financial Research & Portfolio Advisory MAS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main "Analyze AAPL, MSFT, GOOGL"
  python -m src.main --interactive
  python -m src.main --quiet "Analyze AAPL"
        """
    )
    
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Research query to analyze (e.g., 'Analyze AAPL, MSFT, GOOGL')"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode (accepts multiple queries)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output (disable verbose agent logging)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of formatted text"
    )
    
    args = parser.parse_args()
    verbose = not args.quiet
    
    if args.interactive:
        interactive_mode(verbose=verbose)
    elif args.query:
        print_banner()
        results = run_query(args.query, verbose=verbose)
        
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            print_results(results)
    else:
        # Default: interactive mode
        interactive_mode(verbose=verbose)


if __name__ == "__main__":
    main()
