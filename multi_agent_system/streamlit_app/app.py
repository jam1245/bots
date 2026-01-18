"""
Multi-Agent Orchestration Learning Lab

A Streamlit application for learning how AI agents work together
using LangGraph and LangChain.

Run with:
    cd multi_agent_system
    ..\\venv\\Scripts\\streamlit.exe run streamlit_app/app.py

Or with activated venv:
    streamlit run streamlit_app/app.py
"""

import streamlit as st
import sys
import os
from pathlib import Path
import time
from datetime import datetime

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import components
from streamlit_app.components.config_panel import render_config_panel
from streamlit_app.components.request_input import render_request_input, render_request_status
from streamlit_app.components.output_display import render_output_display, render_raw_state
from streamlit_app.components.state_inspector import (
    render_state_inspector,
    render_state_history,
    render_collaboration_progress
)
from streamlit_app.components.timeline import render_timeline, render_timeline_summary
from streamlit_app.components.graph_viz import render_workflow_graph, render_simple_flow_indicator
from streamlit_app.components.learning_controls import render_learning_controls, render_concept_cards
from streamlit_app.components.export_panel import render_export_panel, render_session_stats

from streamlit_app.utils.session_state import init_session_state, reset_session_state
from streamlit_app.workflow_runner import StreamlitWorkflowRunner


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Multi-Agent Learning Lab",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main container styling */
    .main > div {
        padding-top: 1rem;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-size: 14px;
    }

    /* Code block styling */
    code {
        font-size: 12px;
    }

    /* Timeline entry styling */
    .timeline-entry {
        border-left: 3px solid #4CAF50;
        padding-left: 10px;
        margin-bottom: 10px;
    }

    /* Node styling for graph */
    .graph-node {
        padding: 8px;
        border-radius: 8px;
        text-align: center;
        margin: 4px;
    }

    /* Reduce padding in columns */
    .css-1d391kg {
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# INITIALIZATION
# ============================================================================
init_session_state()


# ============================================================================
# SIDEBAR - CONFIGURATION
# ============================================================================
config = render_config_panel()


# ============================================================================
# MAIN LAYOUT
# ============================================================================
st.title("🤖 Multi-Agent Orchestration Learning Lab")
st.markdown("""
Learn how AI agents collaborate to complete complex tasks.
Watch the workflow execute, see state changes, and understand the prompts!
""")

# Two-column layout
left_col, right_col = st.columns([2, 3])


# ============================================================================
# LEFT COLUMN - USER INTERACTION
# ============================================================================
with left_col:
    # Request input
    submitted_request = render_request_input(on_submit=None)

    # Handle new submission
    if submitted_request and not st.session_state.is_running:
        # Reset state for new run
        reset_session_state()
        st.session_state.current_request = submitted_request
        st.session_state.is_running = True
        st.rerun()

    # Show request status
    render_request_status()

    st.divider()

    # Output display
    render_output_display(st.session_state.get("agent_state"))

    # Debug view
    render_raw_state(st.session_state.get("agent_state"))

    # Export options (after execution)
    if st.session_state.get("agent_state"):
        st.divider()
        render_export_panel()
        render_session_stats()


# ============================================================================
# RIGHT COLUMN - BACKEND TRANSPARENCY
# ============================================================================
with right_col:
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Graph",
        "🔍 State",
        "📜 Timeline",
        "💡 Learn"
    ])

    with tab1:
        render_workflow_graph(
            show_explanations=st.session_state.get("show_explanations", True)
        )

    with tab2:
        render_state_inspector(
            current_state=st.session_state.get("agent_state"),
            show_explanations=st.session_state.get("show_explanations", True)
        )
        render_collaboration_progress()
        render_state_history()

    with tab3:
        render_timeline(
            timeline=st.session_state.get("timeline", []),
            show_prompts=config.get("show_prompts", True),
            show_raw_responses=config.get("show_raw_responses", True)
        )
        render_timeline_summary()

    with tab4:
        render_concept_cards()
        render_learning_controls(
            on_step=lambda: setattr(st.session_state, "paused", False),
            on_continue=lambda: setattr(st.session_state, "paused", False),
            on_reset=reset_session_state
        )


# ============================================================================
# WORKFLOW EXECUTION
# ============================================================================
def execute_workflow():
    """Execute the workflow and update UI."""
    if not st.session_state.current_request:
        return

    runner = StreamlitWorkflowRunner(
        model_name=config.get("model"),
        temperature=config.get("temperature"),
        max_iterations=config.get("max_iterations", 10)
    )

    execution_mode = st.session_state.get("execution_mode", "auto")
    execution_speed = config.get("execution_speed", 1.0)

    # Create a placeholder for status updates
    status_placeholder = st.empty()

    try:
        for step in runner.run(st.session_state.current_request):
            # Update session state
            st.session_state.agent_state = step.get("state")
            st.session_state.current_node = step.get("node_name")

            if step.get("node_name"):
                st.session_state.visited_nodes.add(step["node_name"])

            # Add to timeline
            st.session_state.timeline.append({
                "timestamp": datetime.now().isoformat(),
                "step_number": len(st.session_state.timeline) + 1,
                "step_type": step.get("step_type"),
                "node_name": step.get("node_name"),
                "details": step.get("details", {}),
                "state_snapshot": step.get("state"),
            })

            # Update state history
            st.session_state.state_history.append({
                "timestamp": datetime.now().isoformat(),
                "step_number": len(st.session_state.state_history) + 1,
                "node_name": step.get("node_name"),
                "state": step.get("state"),
            })

            # Update status
            status_placeholder.info(f"🔄 {step.get('message', 'Processing...')}")

            # Handle execution modes
            if execution_mode == "step":
                st.session_state.paused = True
                # In step mode, we'd need to yield control back
                # For now, just add a delay
                time.sleep(0.5)

            elif execution_mode == "auto":
                time.sleep(execution_speed)

            # Check for finish
            if step.get("step_type") == "finish":
                break

            # Check for pause
            if st.session_state.get("paused"):
                status_placeholder.warning("⏸️ Paused - click Step or Continue")
                break

    except Exception as e:
        st.error(f"Error during execution: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

    finally:
        st.session_state.is_running = False
        status_placeholder.success("✅ Execution complete!")


# Run workflow if needed
if st.session_state.is_running and st.session_state.current_request:
    execute_workflow()
    st.rerun()


# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <b>Multi-Agent Learning Lab</b> |
    Built with Streamlit, LangGraph, and LangChain |
    Model: {model}
</div>
""".format(model=config.get("model", "N/A")), unsafe_allow_html=True)


# ============================================================================
# HELP SECTION (Expandable)
# ============================================================================
with st.expander("❓ Help & Documentation"):
    st.markdown("""
    ## How to Use This App

    ### 1. Configure Settings (Sidebar)
    - **Model**: Choose the Claude model (Haiku is cheapest)
    - **Temperature**: 0 = deterministic, 1 = creative
    - **Execution Mode**: Step through slowly or run instantly

    ### 2. Enter a Request
    - Use the example presets or type your own
    - Click "Run" to start execution

    ### 3. Watch the Execution
    - **Graph Tab**: See which node is currently executing
    - **State Tab**: Watch the AgentState change in real-time
    - **Timeline Tab**: See every step with full details
    - **Learn Tab**: Get explanations of key concepts

    ### Key Concepts

    **LangGraph Workflow**
    - Nodes are agents (functions that process state)
    - Edges connect nodes (some are conditional)
    - State flows through the entire graph

    **AgentState**
    - Shared data structure (TypedDict)
    - Each agent reads from and writes to state
    - `messages` uses operator.add (appends, not replaces!)

    **Delegator (Meta-Agent)**
    - Uses LLM to decide which specialist to call
    - Can loop back for multi-agent collaboration

    ### Keyboard Shortcuts
    - Enter: Submit request
    - Ctrl+Enter: Submit in text area
    """)
