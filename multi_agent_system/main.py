"""
Multi-Agent Orchestration System - Main Entry Point

WHAT THIS MODULE DOES:
Provides a CLI interface for interacting with the multi-agent system.
Users can submit requests and see how agents collaborate to fulfill them.

USAGE:
    # Interactive mode
    python main.py

    # Single request mode
    python main.py "Write a summary of microservices architecture"

    # With specific phase
    python main.py --phase minimal "Your request here"

WHY THIS FILE EXISTS:
Acts as the user-facing interface to the system:
1. Validates configuration before starting
2. Creates and manages the workflow
3. Handles user input and output
4. Provides helpful error messages
5. Shows agent decision logs

For learning, this demonstrates:
- CLI argument parsing
- Pretty terminal output with Rich
- Error handling and user feedback
- System initialization patterns
"""

import sys
import argparse
import logging
from typing import Optional

# Rich for pretty terminal output
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.logging import RichHandler
from rich import print as rprint
from rich.table import Table

# Our modules
from utils.config import validate_config, SHOW_DECISION_LOG
from graph.state import create_initial_state, validate_state
from graph.workflow import create_workflow

# Set up rich console
console = Console()

# Configure logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def display_banner():
    """
    Display welcome banner.

    WHY THIS FUNCTION EXISTS:
    First impressions matter! A nice banner helps users understand what
    they're using and sets a professional tone.
    """
    banner_text = """
# 🤖 Multi-Agent Orchestration System

*An educational project demonstrating AI agent architecture patterns*

**Features:**
- 🎯 Intelligent request routing
- 🔄 Multi-agent collaboration
- 📊 State management with LangGraph
- 🎓 Extensive inline documentation
"""
    console.print(Panel(Markdown(banner_text), border_style="blue"))


def display_help():
    """Display usage instructions."""
    help_text = """
**How to use:**

1. **Interactive mode** (recommended for learning):
   ```bash
   python main.py
   ```
   Then enter your requests when prompted.

2. **Single request mode**:
   ```bash
   python main.py "Write a summary of Python async programming"
   ```

3. **With options**:
   ```bash
   python main.py --phase minimal "Your request"
   ```

**Example requests:**
- "Write a 3-paragraph summary of microservices architecture"
- "Create a Python function to calculate Fibonacci numbers"
- "Explain the benefits of type hints in Python"

**Tips:**
- Be specific in your requests
- Check the decision log to see how requests are routed
- Use Ctrl+C to exit interactive mode
"""
    console.print(Panel(Markdown(help_text), title="Help", border_style="green"))


def display_decision_log(state: dict):
    """
    Display the agent decision log (if enabled in config).

    WHY THIS FUNCTION EXISTS:
    For learning, it's crucial to see HOW the system made decisions.
    This shows which agents were invoked and why.

    Args:
        state: Final state after workflow execution
    """
    if not SHOW_DECISION_LOG:
        return

    messages = state.get("messages", [])
    if not messages:
        return

    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Agent Decision Log[/bold cyan]",
        border_style="cyan"
    ))

    # Create a table for messages
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Agent", style="cyan", width=15)
    table.add_column("Action", style="white")
    table.add_column("Time", style="dim", width=20)

    for msg in messages:
        table.add_row(
            msg.get("role", "unknown"),
            msg.get("content", ""),
            msg.get("timestamp", "")[:19]  # Trim milliseconds
        )

    console.print(table)


def display_result(state: dict):
    """
    Display the final result to the user.

    WHY THIS FUNCTION EXISTS:
    Results should be formatted nicely and clearly indicate which agents
    contributed. This improves the learning experience.

    Args:
        state: Final state after workflow execution
    """
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]Result[/bold green]",
        border_style="green"
    ))

    # Check for errors
    if state.get("errors"):
        console.print("[bold red]Errors occurred:[/bold red]")
        for error in state["errors"]:
            console.print(f"  ❌ {error}")
        console.print()

    # Display agent outputs
    if state.get("writing_output"):
        console.print(Panel(
            Markdown(state["writing_output"]),
            title="Writing Agent Output",
            border_style="blue"
        ))

    if state.get("code_output"):
        code_info = state["code_output"]
        code = f"```{code_info.get('language', 'python')}\n{code_info.get('code', '')}\n```"
        console.print(Panel(
            Markdown(code),
            title="Code Agent Output",
            border_style="magenta"
        ))
        if code_info.get("explanation"):
            console.print(f"\n[dim]{code_info['explanation']}[/dim]")

    if state.get("research_results"):
        research = state["research_results"]
        console.print(Panel(
            str(research.get("findings", research)),
            title="Research Agent Output",
            border_style="yellow"
        ))

    if state.get("analysis_results"):
        analysis = state["analysis_results"]
        console.print(Panel(
            str(analysis.get("results", analysis)),
            title="Data Analysis Agent Output",
            border_style="cyan"
        ))

    # Display decision log if enabled
    display_decision_log(state)


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def initialize_system(phase: str = "minimal") -> Optional[object]:
    """
    Initialize the multi-agent system.

    WHY THIS FUNCTION EXISTS:
    Centralized initialization with validation helps:
    1. Catch configuration errors early (fail fast)
    2. Provide clear error messages
    3. Ensure system is ready before accepting requests

    Args:
        phase: Which workflow phase to use ("minimal" or "full")

    Returns:
        Compiled workflow app, or None if initialization failed

    LEARNING POINT: Fail Fast Principle
    Better to fail during initialization with a clear error than to fail
    mysteriously later during execution.
    """
    try:
        logger.info("Initializing system...")

        # Step 1: Validate configuration
        logger.info("Validating configuration...")
        validate_config()

        # Step 2: Create workflow
        logger.info(f"Creating workflow (phase: {phase})...")
        app = create_workflow(phase=phase)

        logger.info("System initialized successfully!")
        return app

    except ValueError as e:
        console.print(f"\n[bold red]Configuration Error:[/bold red] {e}")
        console.print("\n[yellow]Please check:[/yellow]")
        console.print("  1. Do you have a .env file? (copy from .env.example)")
        console.print("  2. Is ANTHROPIC_API_KEY set in .env?")
        console.print("  3. Are all required environment variables present?")
        return None

    except Exception as e:
        console.print(f"\n[bold red]Initialization Error:[/bold red] {e}")
        logger.exception("Failed to initialize system")
        return None


def process_request(app: object, user_request: str) -> dict:
    """
    Process a single user request through the workflow.

    WHY THIS FUNCTION EXISTS:
    Encapsulates the request→result flow:
    1. Create initial state
    2. Validate state
    3. Execute workflow
    4. Handle errors gracefully

    Args:
        app: Compiled workflow application
        user_request: The user's request string

    Returns:
        Final state after workflow execution

    LEARNING POINT: Error Handling in Production
    Don't let exceptions crash the system. Catch, log, and provide
    helpful feedback to users.
    """
    try:
        # Create initial state
        logger.info("Creating initial state...")
        state = create_initial_state(user_request)

        # Validate state
        validate_state(state)

        # Execute workflow
        logger.info("Executing workflow...")
        result = app.invoke(state)

        logger.info("Workflow completed successfully")
        return result

    except KeyboardInterrupt:
        # User interrupted - not an error
        console.print("\n[yellow]Request cancelled by user[/yellow]")
        raise

    except Exception as e:
        console.print(f"\n[bold red]Execution Error:[/bold red] {e}")
        logger.exception("Failed to process request")

        # Return a state with error information
        return {
            "user_request": user_request,
            "errors": [str(e)],
            "messages": [],
            "writing_output": None,
            "code_output": None,
            "research_results": None,
            "analysis_results": None
        }


# ============================================================================
# INTERACTIVE MODE
# ============================================================================

def interactive_mode(app: object):
    """
    Run in interactive mode - continuously prompt for requests.

    WHY THIS FUNCTION EXISTS:
    Interactive mode is better for learning and exploration than one-shot
    execution. Users can try multiple requests and see patterns.

    Args:
        app: Compiled workflow application

    LEARNING POINT: REPL Pattern
    Read-Eval-Print Loop (REPL) is a common pattern for interactive tools.
    Python interpreter, database CLIs, etc. all use this pattern.
    """
    console.print("\n[bold green]Interactive Mode[/bold green]")
    console.print("Enter your requests below. Type 'help' for examples, 'quit' to exit.\n")

    while True:
        try:
            # Get user input
            user_request = console.input("[bold blue]Request:[/bold blue] ").strip()

            # Handle special commands
            if not user_request:
                continue

            if user_request.lower() in ["quit", "exit", "q"]:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if user_request.lower() == "help":
                display_help()
                continue

            # Process the request
            result = process_request(app, user_request)

            # Display results
            display_result(result)

            console.print("\n" + "─" * 80 + "\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting...[/yellow]")
            break

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            logger.exception("Unexpected error in interactive mode")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """
    Main entry point for the CLI application.

    Handles:
    - Argument parsing
    - System initialization
    - Mode selection (interactive vs single request)
    - Graceful shutdown
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Multi-Agent Orchestration System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py "Write a summary of Python type hints"
  python main.py --phase minimal "Your request here"

For more information, see README.md
        """
    )

    parser.add_argument(
        "request",
        nargs="*",  # Optional positional argument
        help="User request (if not provided, enters interactive mode)"
    )

    parser.add_argument(
        "--phase",
        choices=["minimal", "full"],
        default="full",
        help="Workflow phase to use (default: full)"
    )

    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Suppress welcome banner"
    )

    parser.add_argument(
        "--help-guide",
        action="store_true",
        help="Show detailed usage guide"
    )

    args = parser.parse_args()

    # Show help guide if requested
    if args.help_guide:
        display_banner()
        display_help()
        return 0

    # Display banner (unless suppressed)
    if not args.no_banner:
        display_banner()

    # Initialize system
    app = initialize_system(phase=args.phase)
    if app is None:
        return 1  # Exit with error code

    # Determine mode based on arguments
    if args.request:
        # Single request mode
        user_request = " ".join(args.request)
        result = process_request(app, user_request)
        display_result(result)

        # Exit code based on success
        return 0 if not result.get("errors") else 1

    else:
        # Interactive mode
        try:
            interactive_mode(app)
            return 0
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
            return 0


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        console.print(f"\n[bold red]Fatal Error:[/bold red] {e}")
        logger.exception("Fatal error in main")
        sys.exit(1)
