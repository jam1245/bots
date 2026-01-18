"""
Workflow Graph Visualization Component

Visualizes the LangGraph workflow structure with
highlighting for current position and visited nodes.
"""

import streamlit as st
from typing import Dict, Any, Optional, Set, List, Tuple


# Graph structure definition
WORKFLOW_NODES = [
    "START",
    "analyze_request",
    "delegator",
    "writing",
    "code",
    "data",
    "research",
    "synthesis",
    "END"
]

WORKFLOW_EDGES = [
    ("START", "analyze_request"),
    ("analyze_request", "delegator"),
    ("delegator", "writing"),
    ("delegator", "code"),
    ("delegator", "data"),
    ("delegator", "research"),
    ("delegator", "END"),  # FINISH case
    ("writing", "synthesis"),
    ("code", "synthesis"),
    ("data", "synthesis"),
    ("research", "synthesis"),
    ("synthesis", "delegator"),  # Loop back
    ("synthesis", "END"),
]

# Node descriptions for education
NODE_DESCRIPTIONS = {
    "START": "Entry point - workflow begins here",
    "analyze_request": "Analyzes if request needs single or multiple agents",
    "delegator": "Meta-agent: Routes requests to specialist agents using LLM",
    "writing": "Specialist: Creates written content (articles, summaries, etc.)",
    "code": "Specialist: Generates code with explanations",
    "data": "Specialist: Performs data analysis and statistics",
    "research": "Specialist: Synthesizes information, optionally with web search",
    "synthesis": "Combines outputs and decides if more agents are needed",
    "END": "Workflow complete - return final state",
}

# Node colors
NODE_COLORS = {
    "START": "#90EE90",          # Light green
    "analyze_request": "#778899", # Slate gray
    "delegator": "#FF6B6B",      # Red (decision maker)
    "writing": "#4ECDC4",        # Teal
    "code": "#45B7D1",           # Blue
    "data": "#96CEB4",           # Green
    "research": "#FFEAA7",       # Yellow
    "synthesis": "#DDA0DD",      # Plum
    "END": "#FFB6C1",            # Light pink
}


def render_workflow_graph(
    current_node: Optional[str] = None,
    visited_nodes: Optional[Set[str]] = None,
    edge_history: Optional[List[Tuple[str, str]]] = None,
    show_explanations: bool = True
):
    """
    Render the workflow graph visualization.

    Args:
        current_node: Currently executing node
        visited_nodes: Set of already visited nodes
        edge_history: List of (from, to) edge traversals
        show_explanations: Whether to show educational content
    """
    st.subheader("🔄 Workflow Graph")

    if current_node is None:
        current_node = st.session_state.get("current_node")
    if visited_nodes is None:
        visited_nodes = st.session_state.get("visited_nodes", set())
    if edge_history is None:
        edge_history = st.session_state.get("edge_history", [])

    # Create visual representation using columns
    _render_graph_visual(current_node, visited_nodes, edge_history)

    # Show legend
    with st.expander("📚 Graph Legend & Concepts", expanded=show_explanations):
        _render_legend()
        _render_langgraph_concepts()


def _render_graph_visual(
    current_node: Optional[str],
    visited_nodes: Set[str],
    edge_history: List[Tuple[str, str]]
):
    """Render the visual graph representation."""

    # Create a simplified visual layout
    # Row 1: START
    # Row 2: analyze_request
    # Row 3: delegator
    # Row 4: agents (writing, code, data, research)
    # Row 5: synthesis
    # Row 6: END

    # Row 1: START
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        _render_node("START", current_node, visited_nodes)
        st.markdown("<center>↓</center>", unsafe_allow_html=True)

    # Row 2: analyze_request
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        _render_node("analyze_request", current_node, visited_nodes)
        st.markdown("<center>↓</center>", unsafe_allow_html=True)

    # Row 3: delegator
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        _render_node("delegator", current_node, visited_nodes)

    # Show routing arrows
    st.markdown("""
    <center style="font-size: 12px; color: #666;">
    ↙️ &nbsp;&nbsp;&nbsp; ↓ &nbsp;&nbsp;&nbsp; ↓ &nbsp;&nbsp;&nbsp; ↘️
    </center>
    """, unsafe_allow_html=True)

    # Row 4: specialist agents
    cols = st.columns(4)
    agents = ["writing", "code", "data", "research"]
    for i, agent in enumerate(agents):
        with cols[i]:
            _render_node(agent, current_node, visited_nodes)

    # Show converging arrows
    st.markdown("""
    <center style="font-size: 12px; color: #666;">
    ↘️ &nbsp;&nbsp;&nbsp; ↓ &nbsp;&nbsp;&nbsp; ↓ &nbsp;&nbsp;&nbsp; ↙️
    </center>
    """, unsafe_allow_html=True)

    # Row 5: synthesis
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        _render_node("synthesis", current_node, visited_nodes)

    # Show loop back and exit arrows
    st.markdown("""
    <center style="font-size: 12px; color: #666;">
    ↺ loop back &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ↓ finish
    </center>
    """, unsafe_allow_html=True)

    # Row 6: END
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        _render_node("END", current_node, visited_nodes)


def _render_node(
    node_name: str,
    current_node: Optional[str],
    visited_nodes: Set[str]
):
    """Render a single node with appropriate styling."""

    is_current = node_name == current_node
    is_visited = node_name in visited_nodes
    base_color = NODE_COLORS.get(node_name, "#CCCCCC")

    # Determine styling
    if is_current:
        # Pulsing effect for current node
        border = "3px solid #FF0000"
        bg_color = base_color
        icon = "🔴"
    elif is_visited:
        border = f"2px solid {base_color}"
        bg_color = base_color
        icon = "✅"
    else:
        border = "1px dashed #999"
        bg_color = "#f0f0f0"
        icon = "⚪"

    # Render as a styled container
    st.markdown(f"""
    <div style="
        background-color: {bg_color};
        border: {border};
        border-radius: 8px;
        padding: 8px;
        text-align: center;
        margin: 4px;
        font-size: 12px;
    ">
        {icon} <b>{node_name}</b>
    </div>
    """, unsafe_allow_html=True)


def _render_legend():
    """Render the graph legend."""
    st.markdown("### Legend")

    cols = st.columns(3)
    with cols[0]:
        st.markdown("🔴 **Current** - Executing now")
    with cols[1]:
        st.markdown("✅ **Visited** - Completed")
    with cols[2]:
        st.markdown("⚪ **Pending** - Not yet visited")

    st.markdown("### Node Types")

    # Show node colors and descriptions
    for node, description in NODE_DESCRIPTIONS.items():
        color = NODE_COLORS.get(node, "#CCC")
        st.markdown(f"""
        <span style="
            background-color: {color};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        ">{node}</span> - {description}
        """, unsafe_allow_html=True)


def _render_langgraph_concepts():
    """Render educational content about LangGraph concepts."""
    st.markdown("---")
    st.markdown("### LangGraph Concepts")

    st.markdown("""
    **What is LangGraph?**

    LangGraph is a library for building stateful, multi-agent applications.
    It models workflows as graphs with:

    - **Nodes**: Functions that process state (our agents)
    - **Edges**: Connections between nodes
    - **Conditional Edges**: Dynamic routing based on state
    - **State**: Shared data that flows through the graph

    **Key Patterns in This Workflow:**

    1. **Conditional Routing** (delegator → agents)
       - The delegator uses LLM reasoning to pick the next node
       - This is implemented with `add_conditional_edges()`

    2. **Cycles** (synthesis → delegator)
       - The workflow can loop back for multi-agent collaboration
       - LangGraph supports cycles unlike simple pipelines

    3. **State Accumulation** (messages field)
       - Uses `operator.add` reducer to append, not replace
       - Preserves conversation history across iterations

    4. **Convergence** (agents → synthesis)
       - Multiple paths converge at synthesis node
       - Combines outputs from different specialists
    """)


def render_edge_history(edge_history: Optional[List[Tuple[str, str]]] = None):
    """Render the history of edge traversals."""
    if edge_history is None:
        edge_history = st.session_state.get("edge_history", [])

    if not edge_history:
        return

    st.markdown("### Edge Traversal History")

    for i, (from_node, to_node) in enumerate(edge_history):
        st.markdown(f"{i+1}. `{from_node}` → `{to_node}`")


def render_simple_flow_indicator():
    """Render a simple horizontal flow indicator for compact display."""
    visited = st.session_state.get("visited_nodes", set())
    current = st.session_state.get("current_node")

    if not visited and not current:
        return

    # Show as inline badges
    flow_parts = []
    for node in ["START", "analyze_request", "delegator"]:
        if node == current:
            flow_parts.append(f"🔴 **{node}**")
        elif node in visited:
            flow_parts.append(f"✅ {node}")

    # Add current agent if any
    for agent in ["writing", "code", "data", "research"]:
        if agent == current:
            flow_parts.append(f"🔴 **{agent}**")
        elif agent in visited:
            flow_parts.append(f"✅ {agent}")

    for node in ["synthesis", "END"]:
        if node == current:
            flow_parts.append(f"🔴 **{node}**")
        elif node in visited:
            flow_parts.append(f"✅ {node}")

    if flow_parts:
        st.markdown(" → ".join(flow_parts))
