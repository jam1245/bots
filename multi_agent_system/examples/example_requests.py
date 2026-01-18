"""
Example Requests: Demonstrating Multi-Agent System Capabilities

This module contains example requests that showcase different routing patterns
and multi-agent collaboration scenarios.

Usage:
    python examples/example_requests.py

Or run individual scenarios:
    python examples/example_requests.py --scenario 1
"""

from graph.state import create_initial_state
from graph.workflow import create_workflow


# ============================================================================
# SCENARIO 1: Simple Single-Agent Request
# ============================================================================

SCENARIO_1 = {
    "name": "Simple Single-Agent: Writing",
    "request": "Write a 2-paragraph summary of the benefits of microservices architecture",
    "expected_agents": ["writing"],
    "learning_points": [
        "Simplest case: request maps to single agent",
        "Delegator correctly identifies writing capability needed",
        "No multi-agent collaboration required",
        "Clean, direct routing"
    ],
    "expected_output_format": "2-paragraph text summary"
}


# ============================================================================
# SCENARIO 2: Sequential Multi-Agent Collaboration
# ============================================================================

SCENARIO_2 = {
    "name": "Sequential Multi-Agent: Research → Data → Writing",
    "request": "Research the top 3 Python async frameworks, analyze their GitHub stars, then write a comparison report",
    "expected_agents": ["research", "data", "writing"],
    "learning_points": [
        "Multi-step workflow with clear sequence",
        "Each agent builds on previous agent's output",
        "Collaboration plan created by analyze_request",
        "Delegator follows plan sequentially",
        "State accumulates information across agents",
        "Synthesis combines all outputs"
    ],
    "expected_output_format": "Research findings + analysis + formatted report"
}


# ============================================================================
# SCENARIO 3: Code Generation
# ============================================================================

SCENARIO_3 = {
    "name": "Single-Agent: Code Generation",
    "request": "Generate a Python function to calculate Fibonacci numbers using dynamic programming",
    "expected_agents": ["code"],
    "learning_points": [
        "Delegator routes to code agent for programming tasks",
        "Code agent returns structured output (code + explanation)",
        "No other agents needed for pure code generation"
    ],
    "expected_output_format": "Python code with docstrings and explanation"
}


# ============================================================================
# SCENARIO 4: Data Analysis
# ============================================================================

SCENARIO_4 = {
    "name": "Single-Agent: Data Analysis",
    "request": "Analyze this dataset and calculate mean, median, and standard deviation: [12, 15, 18, 22, 25, 28, 30, 35]",
    "expected_agents": ["data"],
    "learning_points": [
        "Delegator identifies computational/analytical task",
        "Data agent performs calculations and provides insights",
        "Statistical analysis with interpretation"
    ],
    "expected_output_format": "Statistical results + insights"
}


# ============================================================================
# SCENARIO 5: Research Task
# ============================================================================

SCENARIO_5 = {
    "name": "Single-Agent: Research (Web Search)",
    "request": "Research the latest features in Python 3.12",
    "expected_agents": ["research"],
    "learning_points": [
        "Research agent uses web search tools",
        "Synthesizes information from multiple sources",
        "Provides sourced, current information",
        "Demonstrates tool-augmented agent pattern"
    ],
    "expected_output_format": "Research summary with sources"
}


# ============================================================================
# SCENARIO 6: Complex Multi-Agent Workflow
# ============================================================================

SCENARIO_6 = {
    "name": "Complex Multi-Agent: Code + Documentation",
    "request": "Create a Python function to parse CSV files, then write documentation explaining how to use it",
    "expected_agents": ["code", "writing"],
    "learning_points": [
        "Two independent but related tasks",
        "Code agent generates function first",
        "Writing agent uses code output to create documentation",
        "Demonstrates context passing between agents",
        "Shows how agents can reference each other's work"
    ],
    "expected_output_format": "Python code + usage documentation"
}


# ============================================================================
# ALL SCENARIOS
# ============================================================================

ALL_SCENARIOS = [
    SCENARIO_1,
    SCENARIO_2,
    SCENARIO_3,
    SCENARIO_4,
    SCENARIO_5,
    SCENARIO_6
]


# ============================================================================
# RUNNING SCENARIOS
# ============================================================================

def run_scenario(scenario: dict, app=None):
    """
    Run a single scenario and display results.

    Args:
        scenario: Scenario dictionary with request and metadata
        app: Optional pre-compiled workflow app (creates new if None)
    """
    print("\n" + "="*80)
    print(f"SCENARIO: {scenario['name']}")
    print("="*80)
    print(f"\nRequest: {scenario['request']}")
    print(f"\nExpected agents: {', '.join(scenario['expected_agents'])}")
    print(f"\nLearning points:")
    for point in scenario['learning_points']:
        print(f"  • {point}")

    print(f"\n{'-'*80}")
    print("EXECUTION:")
    print("-"*80)

    # Create or use provided app
    if app is None:
        app = create_workflow("full")

    # Create initial state
    state = create_initial_state(scenario['request'])

    # Execute workflow
    try:
        result = app.invoke(state)

        # Display which agents ran
        messages = result.get("messages", [])
        agents_used = set()
        for msg in messages:
            role = msg.get("role")
            if role in ["research", "data", "writing", "code"]:
                agents_used.add(role)

        print(f"\nAgents invoked: {', '.join(sorted(agents_used))}")

        # Check if matches expectations
        expected_set = set(scenario['expected_agents'])
        if agents_used == expected_set:
            print("✅ Routing matched expectations!")
        else:
            print(f"⚠️  Routing differed from expectations")
            print(f"   Expected: {expected_set}")
            print(f"   Got: {agents_used}")

        # Display outputs
        print(f"\n{'-'*80}")
        print("OUTPUTS:")
        print("-"*80)

        if result.get("research_results"):
            print("\n[Research Agent Output]")
            print(result['research_results'].get('findings', result['research_results'])[:200] + "...")

        if result.get("analysis_results"):
            print("\n[Data Analysis Agent Output]")
            print(result['analysis_results'])

        if result.get("code_output"):
            print("\n[Code Agent Output]")
            code_info = result['code_output']
            print(f"Language: {code_info.get('language', 'unknown')}")
            print(code_info.get('code', '')[:200] + "...")

        if result.get("writing_output"):
            print("\n[Writing Agent Output]")
            print(result['writing_output'][:300] + "...")

        if result.get("errors"):
            print("\n⚠️  ERRORS:")
            for error in result['errors']:
                print(f"  • {error}")

        print("\n" + "="*80 + "\n")
        return result

    except Exception as e:
        print(f"\n❌ Scenario failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_all_scenarios():
    """Run all example scenarios."""
    print("\n" + "#"*80)
    print("# MULTI-AGENT SYSTEM: EXAMPLE SCENARIOS")
    print("#"*80)

    # Create workflow once, reuse for all scenarios
    print("\nInitializing workflow...")
    app = create_workflow("full")
    print("✅ Workflow ready\n")

    results = []
    for i, scenario in enumerate(ALL_SCENARIOS, 1):
        print(f"\n>>> Running Scenario {i}/{len(ALL_SCENARIOS)}")
        result = run_scenario(scenario, app=app)
        results.append((scenario['name'], result))

        if i < len(ALL_SCENARIOS):
            input("\nPress Enter to continue to next scenario...")

    # Summary
    print("\n" + "#"*80)
    print("# SUMMARY")
    print("#"*80)
    for name, result in results:
        status = "✅ Success" if result and not result.get("errors") else "❌ Failed"
        print(f"{status}: {name}")


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run example scenarios for the multi-agent system"
    )
    parser.add_argument(
        "--scenario",
        type=int,
        choices=range(1, len(ALL_SCENARIOS) + 1),
        help=f"Run a specific scenario (1-{len(ALL_SCENARIOS)})"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available scenarios"
    )

    args = parser.parse_args()

    if args.list:
        print("\nAvailable scenarios:")
        for i, scenario in enumerate(ALL_SCENARIOS, 1):
            print(f"\n{i}. {scenario['name']}")
            print(f"   Request: {scenario['request']}")
            print(f"   Expected agents: {', '.join(scenario['expected_agents'])}")

    elif args.scenario:
        # Run specific scenario
        scenario = ALL_SCENARIOS[args.scenario - 1]
        run_scenario(scenario)

    else:
        # Run all scenarios
        run_all_scenarios()
