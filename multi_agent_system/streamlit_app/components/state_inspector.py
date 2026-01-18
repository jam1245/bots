"""
State Inspector Component

Real-time visualization of the AgentState as it changes
during execution. This is one of the most important
educational components.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import json


# State field explanations for education
STATE_FIELD_EXPLANATIONS = {
    "user_request": {
        "description": "The original request from the user",
        "type": "str",
        "set_by": "Initial input",
        "learning": "This is the starting point - everything flows from here"
    },
    "selected_agent": {
        "description": "The agent chosen by the delegator to handle the request",
        "type": "str (writing|code|data|research|FINISH)",
        "set_by": "Delegator agent",
        "learning": "The delegator uses LLM reasoning to route requests"
    },
    "delegation_reasoning": {
        "description": "Why the delegator chose this agent",
        "type": "str",
        "set_by": "Delegator agent",
        "learning": "Transparency into the routing decision"
    },
    "messages": {
        "description": "Conversation history from all agents",
        "type": "List[Dict] with operator.add",
        "set_by": "All agents (accumulated)",
        "learning": "Uses operator.add reducer - APPENDS, never replaces!"
    },
    "research_results": {
        "description": "Output from the research agent",
        "type": "Dict with query, findings, sources",
        "set_by": "Research agent",
        "learning": "Can include web search results or LLM knowledge"
    },
    "analysis_results": {
        "description": "Output from the data analysis agent",
        "type": "Dict with analysis_type, results, insights",
        "set_by": "Data agent",
        "learning": "Computational analysis and insights"
    },
    "writing_output": {
        "description": "Output from the writing agent",
        "type": "str (markdown formatted)",
        "set_by": "Writing agent",
        "learning": "Final text content, may incorporate other outputs"
    },
    "code_output": {
        "description": "Output from the code agent",
        "type": "Dict with code, language, explanation",
        "set_by": "Code agent",
        "learning": "Structured code output with metadata"
    },
    "next_action": {
        "description": "What should happen after current step",
        "type": "str (continue|finish)",
        "set_by": "Agents/Synthesis",
        "learning": "Controls the workflow loop"
    },
    "requires_collaboration": {
        "description": "Whether multiple agents are needed",
        "type": "bool",
        "set_by": "Request analyzer",
        "learning": "Triggers multi-agent workflow"
    },
    "collaboration_plan": {
        "description": "Ordered list of agents to execute",
        "type": "List[str]",
        "set_by": "Request analyzer",
        "learning": "Pre-planned sequence for complex requests"
    },
    "iteration_count": {
        "description": "Current loop iteration",
        "type": "int",
        "set_by": "Workflow (incremented each loop)",
        "learning": "Safety mechanism against infinite loops"
    },
    "errors": {
        "description": "Accumulated error messages",
        "type": "List[str]",
        "set_by": "Any agent (on error)",
        "learning": "Graceful error handling"
    },
}


def render_state_inspector(
    current_state: Optional[Dict[str, Any]] = None,
    previous_state: Optional[Dict[str, Any]] = None,
    show_explanations: bool = True
):
    """
    Render the state inspector component.

    Shows the current AgentState with:
    - Color-coded changes (green=new, yellow=changed, gray=unchanged)
    - Expandable field details
    - Educational explanations

    Args:
        current_state: The current state to display
        previous_state: Previous state for diff highlighting
        show_explanations: Whether to show educational tooltips
    """
    st.subheader("🔍 State Inspector")

    if current_state is None:
        current_state = st.session_state.get("agent_state", {})

    if not current_state:
        st.info("State will appear here once execution starts")

        # Show empty state structure for learning
        if show_explanations:
            with st.expander("📚 AgentState Structure"):
                st.markdown("""
                The **AgentState** is a TypedDict that flows through the entire workflow.
                Every agent reads from and writes to this shared state.

                **Key Fields:**
                - `user_request`: Your original input
                - `selected_agent`: Which agent is handling the task
                - `messages`: Conversation history (accumulated)
                - `*_output`: Results from each agent type

                **Key Concept: Reducers**
                The `messages` field uses `operator.add` as a reducer.
                This means new messages are APPENDED, not replaced!
                """)
        return

    # Compute diff if we have previous state
    diff = _compute_state_diff(previous_state, current_state) if previous_state else None

    # Render each field
    for field, value in current_state.items():
        _render_state_field(
            field,
            value,
            diff.get(field) if diff else None,
            show_explanations
        )


def _render_state_field(
    field: str,
    value: Any,
    change_type: Optional[str],  # "added", "changed", "unchanged"
    show_explanations: bool
):
    """Render a single state field."""

    # Determine styling based on change type
    if change_type == "added":
        icon = "🟢"
        border_color = "#00ff00"
    elif change_type == "changed":
        icon = "🟡"
        border_color = "#ffff00"
    else:
        icon = "⚪"
        border_color = "#cccccc"

    # Field header
    explanation = STATE_FIELD_EXPLANATIONS.get(field, {})

    # Create expandable section for complex values
    is_complex = isinstance(value, (dict, list)) and value
    is_none = value is None
    is_empty = (isinstance(value, (list, dict)) and not value) or value == ""

    # Format value for display
    if is_none:
        value_preview = "_None_"
    elif is_empty:
        value_preview = "_Empty_"
    elif isinstance(value, str):
        value_preview = f'"{value[:50]}..."' if len(value) > 50 else f'"{value}"'
    elif isinstance(value, list):
        value_preview = f"[{len(value)} items]"
    elif isinstance(value, dict):
        value_preview = f"{{...}} ({len(value)} keys)"
    elif isinstance(value, bool):
        value_preview = str(value)
    elif isinstance(value, (int, float)):
        value_preview = str(value)
    else:
        value_preview = str(value)[:50]

    # Render the field
    if is_complex:
        with st.expander(f"{icon} **{field}**: {value_preview}", expanded=(change_type == "changed")):
            # Show explanation if available
            if show_explanations and explanation:
                st.caption(f"ℹ️ {explanation.get('description', '')}")
                if explanation.get('learning'):
                    st.info(f"💡 **Learning Point:** {explanation['learning']}")

            # Render the value
            if isinstance(value, dict):
                st.json(value)
            elif isinstance(value, list):
                if all(isinstance(item, dict) for item in value):
                    # List of dicts - show as expandable items
                    for i, item in enumerate(value):
                        with st.expander(f"[{i}]", expanded=False):
                            st.json(item)
                else:
                    st.json(value)
    else:
        # Simple value - show inline
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"{icon} **{field}**")
        with col2:
            st.markdown(value_preview)

        # Show explanation on hover (using expander for now)
        if show_explanations and explanation and change_type in ("added", "changed"):
            st.caption(f"   ↳ {explanation.get('description', '')}")


def _compute_state_diff(
    old_state: Optional[Dict],
    new_state: Dict
) -> Dict[str, str]:
    """
    Compute what changed between states.

    Returns:
        Dict mapping field names to change type ("added", "changed", "unchanged")
    """
    if not old_state:
        return {k: "added" for k in new_state.keys()}

    diff = {}
    all_keys = set(old_state.keys()) | set(new_state.keys())

    for key in all_keys:
        if key not in old_state:
            diff[key] = "added"
        elif key not in new_state:
            diff[key] = "removed"
        elif old_state[key] != new_state[key]:
            diff[key] = "changed"
        else:
            diff[key] = "unchanged"

    return diff


def render_state_history():
    """Render the state change history."""
    history = st.session_state.get("state_history", [])

    if not history:
        st.info("State history will appear here as execution progresses")
        return

    st.markdown("### State Change History")

    for i, entry in enumerate(reversed(history)):
        with st.expander(
            f"Step {entry['step_number']}: {entry['node_name']} @ {entry['timestamp'][-12:]}",
            expanded=(i == 0)  # Expand most recent
        ):
            if entry.get("state"):
                st.json(entry["state"])


def render_collaboration_progress(state: Optional[Dict] = None):
    """Render progress through collaboration plan."""
    if state is None:
        state = st.session_state.get("agent_state", {})

    if not state:
        return

    plan = state.get("collaboration_plan", [])
    if not plan:
        return

    st.markdown("### 🤝 Collaboration Progress")

    visited = st.session_state.get("visited_nodes", set())

    # Show plan progress
    cols = st.columns(len(plan))
    for i, agent in enumerate(plan):
        with cols[i]:
            if agent in visited:
                st.success(f"✅ {agent}")
            elif agent == st.session_state.get("current_node"):
                st.warning(f"🔄 {agent}")
            else:
                st.info(f"⏳ {agent}")

    # Progress bar
    completed = sum(1 for a in plan if a in visited)
    progress = completed / len(plan) if plan else 0
    st.progress(progress)
    st.caption(f"{completed}/{len(plan)} agents completed")
