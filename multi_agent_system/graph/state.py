"""
State Schema: The Data Foundation of the Multi-Agent System

WHAT THIS MODULE DOES:
Defines the AgentState TypedDict that flows through the LangGraph workflow.
This is the shared memory that all nodes (agents) can read from and write to.

WHY IT EXISTS:
LangGraph requires a state schema to:
1. Track data as it flows through the graph
2. Enable nodes to communicate with each other
3. Persist information across agent invocations
4. Provide type safety and validation

KEY LEARNING CONCEPTS:
- TypedDict for structured state with type hints
- Annotated types for special behaviors (like operator.add)
- State as shared memory in graph-based workflows
- Immutable state updates (functional programming pattern)

COMPARISON: State vs Traditional Function Arguments
┌────────────────────────────────────────────────────────────────────────┐
│ Traditional Function Chain:                                            │
│   result1 = agent1(user_input)                                        │
│   result2 = agent2(result1)  # Must pass data explicitly             │
│   result3 = agent3(result2)                                           │
│                                                                        │
│ LangGraph State:                                                       │
│   state = {"user_request": "..."}                                     │
│   agent1(state)  # Updates state with results                        │
│   agent2(state)  # Can access agent1's results from state            │
│   agent3(state)  # Can access both agent1 and agent2 results         │
│                                                                        │
│ BENEFIT: Nodes don't need to know about each other, just the state   │
└────────────────────────────────────────────────────────────────────────┘
"""

from typing import TypedDict, Optional, List, Dict, Any, Annotated
import operator

# ============================================================================
# LEARNING POINT: Why use Annotated with operator.add?
# ============================================================================
"""
When you annotate a list field with operator.add, LangGraph will APPEND to
the list instead of REPLACING it when nodes return updates.

Without Annotated:
    state = {"messages": [msg1]}
    node returns {"messages": [msg2]}
    Result: state["messages"] = [msg2]  # msg1 is LOST

With Annotated[List[dict], operator.add]:
    state = {"messages": [msg1]}
    node returns {"messages": [msg2]}
    Result: state["messages"] = [msg1, msg2]  # msg2 is APPENDED

This is crucial for accumulating conversation history, agent outputs, etc.
"""


class AgentState(TypedDict):
    """
    Central state object that flows through the LangGraph workflow.

    This state is the "shared memory" of the system. Every node (agent) in the
    graph receives this state, can read from it, and returns updates to it.

    WHY THIS STRUCTURE:
    - User Input: What the user wants
    - Delegation: How the system decided to route the request
    - Agent Outputs: Results from each specialized agent
    - Workflow Control: Signals for how the graph should proceed
    - Safety: Prevents infinite loops and tracks errors

    LEARNING OBJECTIVE: Understanding State Machines
    This state represents a "snapshot" of the system at any point in time.
    As it flows through nodes, it accumulates information, building up a
    complete picture of the request processing.

    STATE LIFECYCLE EXAMPLE:
    1. Initial: {"user_request": "Write a summary of X"}
    2. After analyze: + {"requires_collaboration": False}
    3. After delegator: + {"selected_agent": "writing"}
    4. After writing_agent: + {"writing_output": "Summary..."}
    5. After synthesis: + {"final_response": "Here's your summary..."}

    See Also:
        - LangGraph State Docs: https://langchain-ai.github.io/langgraph/
        - TypedDict: https://docs.python.org/3/library/typing.html#typing.TypedDict
    """

    # ========================================================================
    # USER INPUT
    # ========================================================================
    user_request: str
    """
    The original request from the user.

    Examples:
        - "Write a summary of microservices architecture"
        - "Research Python web frameworks and create a comparison"
        - "Generate code for a CSV parser"

    This field is set at the start and typically doesn't change, serving as
    the "north star" for what the user actually wants.
    """

    # ========================================================================
    # DELEGATION METADATA
    # ========================================================================
    selected_agent: Optional[str]
    """
    Which agent the delegator chose for the next step.

    Valid values:
        - "writing": Content creation agent
        - "code": Code generation agent
        - "data": Data analysis agent
        - "research": Research agent
        - "FINISH": No more agents needed
        - None: Not yet determined

    WHY THIS FIELD EXISTS:
    The delegator needs to communicate its routing decision to the graph's
    conditional edges. This field serves as the bridge between the delegator's
    LLM decision and the graph's routing logic.
    """

    delegation_reasoning: Optional[str]
    """
    Why the delegator chose this agent (for debugging and learning).

    Example: "User needs content creation with no research required, so
              routing directly to writing agent."

    WHY THIS MATTERS:
    When debugging or learning, seeing the "why" behind routing decisions
    helps understand agent behavior and improve prompts.
    """

    # ========================================================================
    # CONVERSATION HISTORY (Accumulated)
    # ========================================================================
    messages: Annotated[List[Dict[str, Any]], operator.add]
    """
    Accumulated messages from all agents.

    IMPORTANT: Uses operator.add annotation for list concatenation!
    When a node returns {"messages": [new_msg]}, it's APPENDED to existing
    messages, not replaced.

    Message format:
        {
            "role": "agent_name",  # "writing", "code", "delegator", etc.
            "content": "What the agent did",
            "timestamp": "ISO timestamp",
            "metadata": {...}  # Optional agent-specific data
        }

    Example accumulated messages:
        [
            {"role": "delegator", "content": "Routing to writing agent"},
            {"role": "writing", "content": "Generated 3-paragraph summary"},
            {"role": "user", "content": "Thanks! Now make it shorter"},
            {"role": "delegator", "content": "Routing to writing agent again"},
            {"role": "writing", "content": "Created shortened version"}
        ]

    WHY THIS FIELD EXISTS:
    Provides conversation continuity, debugging trace, and context for
    future agent decisions.
    """

    # ========================================================================
    # AGENT-SPECIFIC OUTPUTS
    # ========================================================================
    research_results: Optional[Dict[str, Any]]
    """
    Output from the research agent.

    Typical structure:
        {
            "query": "What was searched",
            "findings": "Summary of findings",
            "sources": ["url1", "url2"],
            "timestamp": "ISO timestamp",
            "confidence": 0.85
        }

    None if research agent hasn't run yet.
    """

    analysis_results: Optional[Dict[str, Any]]
    """
    Output from the data analysis agent.

    Typical structure:
        {
            "analysis_type": "statistical" | "comparative" | "trend",
            "results": {...},  # Agent-specific results
            "visualizations": ["Description of charts/graphs to create"],
            "insights": ["Key insight 1", "Key insight 2"],
            "timestamp": "ISO timestamp"
        }

    None if data agent hasn't run yet.
    """

    writing_output: Optional[str]
    """
    Output from the writing agent.

    Could be:
    - A summary
    - An article
    - Edited content
    - Formatted text

    None if writing agent hasn't run yet.
    """

    code_output: Optional[Dict[str, Any]]
    """
    Output from the code agent.

    Typical structure:
        {
            "code": "The generated code",
            "language": "python" | "javascript" | etc.,
            "explanation": "What the code does",
            "usage_example": "How to use it",
            "dependencies": ["Required libraries"],
            "timestamp": "ISO timestamp"
        }

    None if code agent hasn't run yet.
    """

    # ========================================================================
    # WORKFLOW CONTROL
    # ========================================================================
    next_action: Optional[str]
    """
    Signal for how the workflow should proceed.

    Valid values:
        - "continue": More work needed, loop back to delegator
        - "finish": Request complete, end workflow
        - None: Not yet determined

    WHY THIS FIELD EXISTS:
    LangGraph's conditional edges use this to decide whether to:
    1. Continue the cycle (back to delegator for next agent)
    2. Exit to synthesis and end

    This enables multi-agent workflows where multiple agents contribute
    sequentially.
    """

    requires_collaboration: bool
    """
    Does this request need multiple agents?

    Set by analyze_request node based on request complexity.

    Examples:
        - "Write a summary" → False (single agent sufficient)
        - "Research X, analyze Y, write report" → True (needs 3 agents)

    WHY THIS MATTERS:
    Helps the delegator understand whether it's orchestrating a single task
    or a multi-step workflow. Affects prompting and planning.
    """

    collaboration_plan: Optional[List[str]]
    """
    Ordered list of agents needed for this request.

    Example: ["research", "data", "writing"]

    Set by analyze_request when requires_collaboration=True.
    The delegator can follow this plan sequentially.

    WHY THIS FIELD EXISTS:
    Pre-planning the workflow helps ensure:
    1. All necessary steps happen
    2. Steps happen in logical order
    3. No redundant agent calls
    4. Better prompts to delegator
    """

    # ========================================================================
    # SAFETY & DEBUGGING
    # ========================================================================
    iteration_count: int
    """
    How many times we've looped through agents.

    Incremented each time we return to the delegator.
    Used to prevent infinite loops.

    WHY THIS MATTERS:
    Without a limit, bugs or unclear requests could cause infinite cycling:
        delegator → agent → synthesis → delegator → agent → ...forever

    When iteration_count exceeds MAX_ITERATIONS (from config), the system
    should gracefully exit with partial results.
    """

    errors: List[str]
    """
    Accumulated errors from any failed operations.

    When an agent encounters an error, it adds a description here instead of
    crashing the whole workflow. This enables graceful degradation.

    Example errors:
        - "Research agent: Web search API unavailable"
        - "Code agent: Syntax error in generated code"
        - "Data agent: Insufficient data for analysis"

    WHY THIS MATTERS:
    Better to complete with partial results + clear error messages than to
    fail completely. Users can understand what worked and what didn't.
    """

    # ========================================================================
    # OPTIONAL: Future Extensions
    # ========================================================================
    # These fields aren't used in the basic implementation but show how you
    # could extend the system

    # user_id: Optional[str]  # For multi-user systems
    # session_id: Optional[str]  # For conversation persistence
    # metadata: Optional[Dict[str, Any]]  # For custom data
    # tools_used: Optional[List[str]]  # Track which tools were called
    # costs: Optional[Dict[str, float]]  # Track API costs per agent


# ============================================================================
# HELPER FUNCTIONS FOR STATE MANIPULATION
# ============================================================================

def create_initial_state(user_request: str) -> AgentState:
    """
    Create a fresh state for a new request.

    WHY THIS FUNCTION EXISTS:
    Instead of manually building state dicts with all required fields,
    this ensures consistent initialization with sensible defaults.

    Args:
        user_request: The user's request

    Returns:
        Fully initialized AgentState ready for the workflow

    Example:
        >>> state = create_initial_state("Write a summary of microservices")
        >>> result = workflow.invoke(state)
    """
    return AgentState(
        # User input
        user_request=user_request,

        # Delegation (not yet determined)
        selected_agent=None,
        delegation_reasoning=None,

        # Agent outputs (empty initially)
        messages=[],
        research_results=None,
        analysis_results=None,
        writing_output=None,
        code_output=None,

        # Workflow control (defaults)
        next_action=None,
        requires_collaboration=False,
        collaboration_plan=None,

        # Safety (start at 0)
        iteration_count=0,
        errors=[]
    )


def validate_state(state: AgentState) -> None:
    """
    Validate that state is consistent and within safety limits.

    WHY THIS FUNCTION EXISTS:
    Defensive programming - catch state corruption or infinite loops early
    with clear error messages.

    Args:
        state: State to validate

    Raises:
        ValueError: If state is invalid or unsafe

    Example:
        >>> validate_state(state)  # Call before critical operations
    """
    # Import here to avoid circular dependency
    from utils.config import MAX_ITERATIONS

    # Check iteration limit
    if state.get("iteration_count", 0) > MAX_ITERATIONS:
        raise ValueError(
            f"Exceeded maximum iterations ({MAX_ITERATIONS}). "
            f"Possible infinite loop. Request: {state.get('user_request', 'Unknown')}"
        )

    # Check required fields are present
    if "user_request" not in state or not state["user_request"]:
        raise ValueError("State missing required field 'user_request'")

    # Check collaboration consistency
    if state.get("requires_collaboration") and not state.get("collaboration_plan"):
        raise ValueError(
            "State inconsistency: requires_collaboration=True but no collaboration_plan"
        )

    # Check selected_agent is valid
    valid_agents = {"writing", "code", "data", "research", "FINISH", None}
    if state.get("selected_agent") not in valid_agents:
        raise ValueError(
            f"Invalid selected_agent: {state.get('selected_agent')}. "
            f"Must be one of {valid_agents}"
        )


# ============================================================================
# KEY CONCEPT: Why TypedDict instead of dataclass or Pydantic?
# ============================================================================
"""
╔════════════════════════════════════════════════════════════════════════╗
║ KEY CONCEPT: TypedDict vs Other Options                                ║
╠════════════════════════════════════════════════════════════════════════╣
║                                                                         ║
║ TypedDict (Chosen for LangGraph State):                                ║
║   ✅ Native support in LangGraph                                       ║
║   ✅ Lightweight - just a dict with type hints                         ║
║   ✅ Easy to serialize/deserialize                                     ║
║   ✅ Supports Annotated types (for operator.add)                       ║
║   ❌ No runtime validation                                             ║
║   ❌ No methods or behavior                                            ║
║                                                                         ║
║ Pydantic BaseModel:                                                    ║
║   ✅ Runtime validation                                                ║
║   ✅ Serialization/deserialization built-in                            ║
║   ❌ LangGraph requires extra conversion                               ║
║   ❌ Heavier weight                                                    ║
║                                                                         ║
║ Dataclass:                                                             ║
║   ✅ Simple and Pythonic                                               ║
║   ❌ LangGraph requires extra work                                     ║
║   ❌ No Annotated support                                              ║
║                                                                         ║
║ BEST PRACTICE FOR LANGGRAPH:                                           ║
║   Use TypedDict for state + Pydantic for structured outputs            ║
║   - State: TypedDict (LangGraph native)                                ║
║   - Agent outputs: Pydantic (validation & structure)                   ║
║                                                                         ║
╚════════════════════════════════════════════════════════════════════════╝
"""


if __name__ == "__main__":
    # Test state creation and validation
    print("Testing state module...")

    # Create initial state
    state = create_initial_state("Write a summary of microservices")
    print(f"✅ Created initial state with {len(state)} fields")

    # Validate state
    try:
        validate_state(state)
        print("✅ State validation passed")
    except ValueError as e:
        print(f"❌ State validation failed: {e}")

    # Test iteration limit
    state["iteration_count"] = 100
    try:
        validate_state(state)
        print("❌ Should have caught iteration limit")
    except ValueError as e:
        print(f"✅ Correctly caught iteration limit: {e}")

    print("\nState structure:")
    for key in state.keys():
        print(f"  - {key}: {type(state[key]).__name__}")
