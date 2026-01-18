"""
Session State Management for Streamlit

Centralizes all session state initialization and management.
This ensures consistent state across reruns and component interactions.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List, Optional


def init_session_state():
    """
    Initialize all session state variables.

    Called once at app startup. Streamlit reruns the entire script
    on each interaction, so we need to check if state exists before
    initializing to avoid resetting user data.
    """

    # ========================================================================
    # Configuration State
    # ========================================================================
    if "config" not in st.session_state:
        st.session_state.config = {
            "model": "claude-3-5-haiku-20241022",
            "temperature": 0.7,
            "max_iterations": 10,
            "show_prompts": True,
            "show_raw_responses": True,
            "execution_speed": 1.0,  # seconds between steps
        }

    # ========================================================================
    # Execution State
    # ========================================================================
    if "is_running" not in st.session_state:
        st.session_state.is_running = False

    if "current_step" not in st.session_state:
        st.session_state.current_step = 0

    if "execution_mode" not in st.session_state:
        st.session_state.execution_mode = "auto"  # "auto", "step", "instant"

    if "paused" not in st.session_state:
        st.session_state.paused = False

    # ========================================================================
    # Agent State (mirrors the LangGraph AgentState)
    # ========================================================================
    if "agent_state" not in st.session_state:
        st.session_state.agent_state = None

    if "state_history" not in st.session_state:
        st.session_state.state_history = []  # List of state snapshots

    # ========================================================================
    # Execution Timeline
    # ========================================================================
    if "timeline" not in st.session_state:
        st.session_state.timeline = []  # List of execution steps

    # ========================================================================
    # Current Request
    # ========================================================================
    if "current_request" not in st.session_state:
        st.session_state.current_request = ""

    if "final_output" not in st.session_state:
        st.session_state.final_output = None

    # ========================================================================
    # Graph Visualization State
    # ========================================================================
    if "current_node" not in st.session_state:
        st.session_state.current_node = None

    if "visited_nodes" not in st.session_state:
        st.session_state.visited_nodes = set()

    if "edge_history" not in st.session_state:
        st.session_state.edge_history = []  # List of (from_node, to_node) tuples

    # ========================================================================
    # Error State
    # ========================================================================
    if "errors" not in st.session_state:
        st.session_state.errors = []

    # ========================================================================
    # Learning Mode State
    # ========================================================================
    if "breakpoints" not in st.session_state:
        st.session_state.breakpoints = set()  # Node names to pause at

    if "show_explanations" not in st.session_state:
        st.session_state.show_explanations = True


def reset_session_state():
    """
    Reset execution-related state for a new request.
    Preserves configuration settings.
    """
    st.session_state.is_running = False
    st.session_state.current_step = 0
    st.session_state.paused = False
    st.session_state.agent_state = None
    st.session_state.state_history = []
    st.session_state.timeline = []
    st.session_state.final_output = None
    st.session_state.current_node = None
    st.session_state.visited_nodes = set()
    st.session_state.edge_history = []
    st.session_state.errors = []


def add_timeline_entry(
    step_type: str,
    node_name: str,
    details: Dict[str, Any],
    state_before: Optional[Dict] = None,
    state_after: Optional[Dict] = None
):
    """
    Add an entry to the execution timeline.

    Args:
        step_type: Type of step ("node_start", "node_end", "llm_call", "state_update", etc.)
        node_name: Name of the node/agent
        details: Step-specific details (prompts, responses, etc.)
        state_before: State snapshot before this step
        state_after: State snapshot after this step
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "step_number": len(st.session_state.timeline) + 1,
        "step_type": step_type,
        "node_name": node_name,
        "details": details,
        "state_before": state_before,
        "state_after": state_after,
    }
    st.session_state.timeline.append(entry)

    # Also update state history if state changed
    if state_after and state_after != state_before:
        st.session_state.state_history.append({
            "timestamp": entry["timestamp"],
            "step_number": entry["step_number"],
            "node_name": node_name,
            "state": state_after.copy() if isinstance(state_after, dict) else state_after,
        })


def update_graph_state(node_name: str, from_node: Optional[str] = None):
    """
    Update graph visualization state when moving to a new node.

    Args:
        node_name: The node being entered
        from_node: The node we're coming from (for edge tracking)
    """
    st.session_state.current_node = node_name
    st.session_state.visited_nodes.add(node_name)

    if from_node:
        st.session_state.edge_history.append((from_node, node_name))


def get_state_diff(old_state: Dict, new_state: Dict) -> Dict[str, Any]:
    """
    Compute the difference between two state dictionaries.

    Returns:
        Dict with keys: "added", "removed", "changed"
    """
    if not old_state:
        return {"added": new_state, "removed": {}, "changed": {}}

    if not new_state:
        return {"added": {}, "removed": old_state, "changed": {}}

    diff = {"added": {}, "removed": {}, "changed": {}}

    all_keys = set(old_state.keys()) | set(new_state.keys())

    for key in all_keys:
        old_val = old_state.get(key)
        new_val = new_state.get(key)

        if key not in old_state:
            diff["added"][key] = new_val
        elif key not in new_state:
            diff["removed"][key] = old_val
        elif old_val != new_val:
            diff["changed"][key] = {"old": old_val, "new": new_val}

    return diff
