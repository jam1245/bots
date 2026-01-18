"""
LangGraph Workflow: Orchestration Engine for Multi-Agent System

WHAT THIS MODULE DOES:
Defines the LangGraph workflow (state machine) that orchestrates agent
execution. This is the "brain" that controls how requests flow through agents.

WHY IT EXISTS:
Coordinates multiple agents working together:
1. Routes requests to appropriate agents
2. Manages state flow between agents
3. Enables cycles for multi-step workflows
4. Provides visualization and debugging

KEY LEARNING CONCEPTS:
- LangGraph StateGraph (state machine for AI agents)
- Nodes (processing steps - our agents)
- Edges (connections between nodes)
- Conditional routing (dynamic decision-making)
- Cycles (iterative workflows)

CURRENT IMPLEMENTATION: Phase 1 (Minimal)
This is the simplest possible graph to validate end-to-end functionality:
    START → writing_agent → END

Future phases will add:
- Phase 2: Delegator + conditional routing
- Phase 3: All 4 agents
- Phase 4: Multi-agent collaboration + synthesis

See Also:
    - LangGraph Docs: https://langchain-ai.github.io/langgraph/
    - State definition: graph/state.py
    - Agents: agents/*.py
"""

import logging
from typing import Literal
from langgraph.graph import StateGraph, END

# Import state and agents
from graph.state import AgentState
from agents.writing_agent import get_writing_agent_node
from agents.code_agent import get_code_agent_node
from agents.data_agent import get_data_agent_node
from agents.research_agent import get_research_agent_node
from agents.delegator import get_delegator_node

# Set up logging
logger = logging.getLogger(__name__)


# ============================================================================
# PHASE 1: MINIMAL GRAPH (Current Implementation)
# ============================================================================
# Just writing agent - validates basic flow
# ============================================================================

def create_minimal_workflow():
    """
    Create the simplest possible workflow for Phase 1 testing.

    LEARNING OBJECTIVE: Understanding LangGraph Basics
    This minimal graph demonstrates:
    1. Creating a StateGraph with our state schema
    2. Adding a node (our writing agent)
    3. Connecting nodes with edges
    4. Compiling the graph into a runnable

    Graph Structure:
        START → writing_agent → END

    WHY START WITH THIS:
    Before adding complexity (delegator, multiple agents, cycles), verify:
    - State flows correctly
    - Agent executes properly
    - Results are returned
    - Errors are handled

    Returns:
        Compiled LangGraph application

    Example:
        >>> app = create_minimal_workflow()
        >>> state = create_initial_state("Write a haiku about Python")
        >>> result = app.invoke(state)
        >>> print(result["writing_output"])
    """
    logger.info("Creating minimal workflow (Phase 1)...")

    # ========================================================================
    # STEP 1: Create the StateGraph
    # ========================================================================
    # StateGraph is parameterized by our AgentState TypedDict
    # This tells LangGraph what fields are in the state
    workflow = StateGraph(AgentState)

    # ========================================================================
    # STEP 2: Add nodes (processing steps)
    # ========================================================================
    # Each node is a function or callable that:
    # - Takes state as input
    # - Returns state updates (merged by LangGraph)
    #
    # LEARNING POINT: Node vs Edge
    # - Node: Does work, transforms state
    # - Edge: Connects nodes, no processing

    workflow.add_node(
        "writing_agent",  # Node name (used in edges)
        get_writing_agent_node()  # Callable that processes state
    )

    # ========================================================================
    # STEP 3: Set entry point
    # ========================================================================
    # Where does the graph start?
    # When you call app.invoke(state), it begins here
    workflow.set_entry_point("writing_agent")

    # ========================================================================
    # STEP 4: Add edges (connections)
    # ========================================================================
    # Connect writing_agent to END (terminal node)
    # This means: writing_agent → END (stop execution)
    workflow.add_edge("writing_agent", END)

    # ========================================================================
    # STEP 5: Compile the graph
    # ========================================================================
    # Converts the graph definition into a runnable application
    # Does validation (all nodes connected, no cycles without logic, etc.)
    app = workflow.compile()

    logger.info("Minimal workflow compiled successfully")
    return app


# ============================================================================
# FUTURE: PHASE 2+ NODES (To be implemented later)
# ============================================================================
# These will be added as we progress through the implementation phases
# ============================================================================

def analyze_request_node(state: AgentState) -> AgentState:
    """
    [PHASE 2] Analyze the user request to understand complexity and needs.

    This node will:
    1. Parse the request to understand intent
    2. Determine if single agent or collaboration needed
    3. Create a collaboration plan if necessary

    Args:
        state: Current agent state

    Returns:
        State updates with analysis results

    PLACEHOLDER: To be fully implemented in Phase 2
    """
    logger.info("Analyzing user request...")

    user_request = state["user_request"].lower()

    # Simple heuristic-based analysis
    multi_step_keywords = [
        "research and", "analyze and", "then", "after that",
        "first", "second", "finally", "compare"
    ]

    requires_collaboration = any(keyword in user_request for keyword in multi_step_keywords)

    # Try to infer collaboration plan from keywords
    collaboration_plan = None
    if requires_collaboration:
        plan = []
        if any(word in user_request for word in ["research", "find", "search", "look up"]):
            plan.append("research")
        if any(word in user_request for word in ["analyze", "calculate", "compare", "data"]):
            plan.append("data")
        if any(word in user_request for word in ["code", "function", "program", "script"]):
            plan.append("code")
        if any(word in user_request for word in ["write", "summary", "explain", "document"]):
            plan.append("writing")

        collaboration_plan = plan if plan else None

    logger.info(
        f"Analysis: collaboration={'yes' if requires_collaboration else 'no'}, "
        f"plan={collaboration_plan}"
    )

    return {
        "requires_collaboration": requires_collaboration,
        "collaboration_plan": collaboration_plan
    }


def synthesis_node(state: AgentState) -> AgentState:
    """Synthesize outputs from multiple agents into coherent response."""
    logger.info("Synthesizing agent outputs...")

    agent_count = sum([
        1 if state.get("writing_output") else 0,
        1 if state.get("code_output") else 0,
        1 if state.get("analysis_results") else 0,
        1 if state.get("research_results") else 0
    ])

    logger.info(f"Synthesis complete: {agent_count} agent(s) contributed")

    return {
        "messages": [{
            "role": "synthesis",
            "content": f"Combined outputs from {agent_count} agent(s)",
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }]
    }


def route_to_agent(state: AgentState) -> str:
    """Determine which agent node to route to based on delegator's decision."""
    selected = state.get("selected_agent")
    logger.info(f"Routing to: {selected}")

    if selected == "FINISH":
        return "synthesis"
    elif selected in ["research", "data", "writing", "code"]:
        return selected
    else:
        logger.warning(f"Unknown agent '{selected}', routing to synthesis")
        return "synthesis"


def should_continue(state: AgentState) -> str:
    """Decide whether to continue workflow or finish."""
    # Check if delegator said FINISH
    if state.get("selected_agent") == "FINISH":
        logger.info("Workflow finishing: delegator chose FINISH")
        return "finish"

    # Check iteration count
    from utils.config import MAX_ITERATIONS
    iteration = state.get("iteration_count", 0)
    if iteration >= MAX_ITERATIONS:
        logger.warning(f"Max iterations reached ({MAX_ITERATIONS}), finishing")
        return "finish"

    # Check collaboration plan
    plan = state.get("collaboration_plan", [])
    if plan:
        completed = []
        if state.get("research_results"):
            completed.append("research")
        if state.get("analysis_results"):
            completed.append("data")
        if state.get("writing_output"):
            completed.append("writing")
        if state.get("code_output"):
            completed.append("code")

        if all(agent in completed for agent in plan):
            logger.info("Workflow finishing: collaboration plan complete")
            return "finish"

    # Check for errors
    if state.get("errors"):
        logger.info("Workflow finishing: errors encountered")
        return "finish"

    # Default: finish if single-agent task
    if not state.get("requires_collaboration"):
        logger.info("Workflow finishing: single-agent task complete")
        return "finish"

    logger.info("Workflow continuing: more agents needed")
    return "continue"


def create_full_workflow():
    """
    Create the full multi-agent workflow with delegator and all agents.

    Graph Structure:
        START → analyze_request → delegator → [agent nodes] → synthesis
          ↑                                                        |
          └────────────── (if continue) ──────────────────────────┘
    """
    logger.info("Creating full workflow...")

    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("analyze_request", analyze_request_node)
    workflow.add_node("delegator", get_delegator_node())
    workflow.add_node("research", get_research_agent_node())
    workflow.add_node("data", get_data_agent_node())
    workflow.add_node("writing", get_writing_agent_node())
    workflow.add_node("code", get_code_agent_node())
    workflow.add_node("synthesis", synthesis_node)

    # Set entry point
    workflow.set_entry_point("analyze_request")

    # Add edges
    workflow.add_edge("analyze_request", "delegator")

    # Conditional routing from delegator to agents
    workflow.add_conditional_edges(
        "delegator",
        route_to_agent,
        {
            "research": "research",
            "data": "data",
            "writing": "writing",
            "code": "code",
            "synthesis": "synthesis"
        }
    )

    # All agents go to synthesis
    for agent in ["research", "data", "writing", "code"]:
        workflow.add_edge(agent, "synthesis")

    # Conditional: continue or finish
    workflow.add_conditional_edges(
        "synthesis",
        should_continue,
        {
            "continue": "delegator",  # Loop back
            "finish": END
        }
    )

    app = workflow.compile()
    logger.info("Full workflow compiled successfully!")
    return app


# ============================================================================
# KEY CONCEPT: LangGraph vs Simple Function Chains
# ============================================================================
"""
╔════════════════════════════════════════════════════════════════════════╗
║ KEY CONCEPT: Why LangGraph instead of simple functions?                ║
╠════════════════════════════════════════════════════════════════════════╣
║                                                                         ║
║ Simple Function Chain:                                                 ║
║   result = writing_agent(user_request)                                 ║
║   ✅ Simple                                                            ║
║   ❌ Always linear (can't route based on request)                      ║
║   ❌ No shared state                                                   ║
║   ❌ Hard to add collaboration                                         ║
║                                                                         ║
║ LangChain RunnableSequence:                                            ║
║   chain = research | analyze | write                                   ║
║   result = chain.invoke(request)                                       ║
║   ✅ Composable                                                        ║
║   ❌ Still linear (always same sequence)                               ║
║   ❌ No conditional routing                                            ║
║   ❌ Can't handle cycles (iterative workflows)                         ║
║                                                                         ║
║ LangGraph StateGraph:                                                  ║
║   - Conditional routing (request determines path)                      ║
║   - Cycles enabled (agent → synthesis → agent → ...)                   ║
║   - Shared state across all nodes                                      ║
║   - Visual graph representation                                        ║
║   - Streaming support                                                  ║
║                                                                         ║
║ WHEN TO USE WHAT:                                                      ║
║   • Simple chain → Use functions or RunnableSequence                   ║
║   • Need routing → Use LangGraph                                       ║
║   • Need cycles → Use LangGraph                                        ║
║   • Need multi-agent coordination → Use LangGraph                      ║
║                                                                         ║
║ OUR USE CASE:                                                          ║
║   We need routing (different agents for different requests) and        ║
║   cycles (multi-step workflows), so LangGraph is the right choice.     ║
║                                                                         ║
╚════════════════════════════════════════════════════════════════════════╝
"""


# ============================================================================
# MAIN WORKFLOW FACTORY
# ============================================================================

def create_workflow(phase: Literal["minimal", "full"] = "minimal"):
    """
    Factory function to create the appropriate workflow for current phase.

    WHY THIS FUNCTION EXISTS:
    As we implement phases, we want to:
    1. Keep old versions for testing
    2. Easy to switch between implementations
    3. Gradual complexity increase

    Args:
        phase: Which implementation to create
               - "minimal": Phase 1 (just writing agent)
               - "full": Phase 2+ (delegator, all agents, collaboration)

    Returns:
        Compiled LangGraph application

    Example:
        >>> # Start with minimal for testing
        >>> app = create_workflow("minimal")
        >>> result = app.invoke(state)
        >>>
        >>> # Later, switch to full
        >>> app = create_workflow("full")
    """
    if phase == "minimal":
        return create_minimal_workflow()
    elif phase == "full":
        return create_full_workflow()
    else:
        raise ValueError(f"Unknown phase: {phase}. Use 'minimal' or 'full'")


# ============================================================================
# WORKFLOW VISUALIZATION (Optional)
# ============================================================================

def visualize_workflow(save_path: str = "workflow_graph.png"):
    """
    Generate a visual representation of the workflow graph.

    LEARNING VALUE:
    Seeing the graph structure helps understand:
    - How nodes connect
    - Where cycles exist
    - Conditional routing paths

    Requires: graphviz system package installed

    Args:
        save_path: Where to save the image

    Example:
        >>> visualize_workflow("my_graph.png")
        >>> # Open my_graph.png to see the graph structure
    """
    try:
        app = create_workflow("minimal")

        # LangGraph apps have a .get_graph() method that returns a drawable graph
        graph = app.get_graph()

        # Draw the graph (requires graphviz)
        png_data = graph.draw_mermaid_png()

        with open(save_path, "wb") as f:
            f.write(png_data)

        logger.info(f"Workflow graph saved to {save_path}")
        return True

    except ImportError:
        logger.warning(
            "graphviz not installed. Cannot generate visualization. "
            "Install with: pip install graphviz (and system graphviz package)"
        )
        return False
    except Exception as e:
        logger.error(f"Failed to visualize workflow: {e}")
        return False


# ============================================================================
# WHY THIS MATTERS: Production Considerations
# ============================================================================
"""
In production multi-agent systems, the workflow orchestration is critical:

1. **Observability**: LangGraph provides tracing, metrics, visualization
2. **Error Handling**: Graceful failures, retry logic, partial results
3. **Streaming**: Real-time updates as agents work (important for UX)
4. **Persistence**: Save/resume workflows across sessions
5. **Human-in-the-Loop**: Approval gates before expensive operations
6. **Cost Optimization**: Route to cheaper models when appropriate
7. **Parallel Execution**: Run independent agents concurrently
8. **Testing**: Test individual nodes, edges, and full workflows

This minimal implementation provides the foundation for adding these features
as you learn and your needs evolve.
"""


if __name__ == "__main__":
    # Test workflow creation
    print("Testing workflow module...")

    try:
        # Create minimal workflow
        app = create_workflow("minimal")
        print("✅ Successfully created minimal workflow")

        # Test with example state
        from graph.state import create_initial_state

        state = create_initial_state("Write a haiku about coding")
        print("\nTesting workflow execution...")

        result = app.invoke(state)

        if "writing_output" in result:
            print("\n✅ Workflow executed successfully!")
            print("\nOutput:")
            print("=" * 80)
            print(result["writing_output"])
            print("=" * 80)
        else:
            print("\n❌ No output generated")

        if result.get("errors"):
            print(f"\n⚠️ Errors: {result['errors']}")

        # Try visualization (may fail if graphviz not installed)
        print("\nAttempting to generate workflow visualization...")
        if visualize_workflow():
            print("✅ Workflow visualization saved to workflow_graph.png")
        else:
            print("⚠️ Could not generate visualization (graphviz not installed)")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
