"""
Request Input Component

Allows users to enter requests and select from example presets.
"""

import streamlit as st
from typing import Optional, Callable


# Example requests for quick testing
EXAMPLE_REQUESTS = {
    "Simple Writing": {
        "request": "Write a haiku about Python programming",
        "description": "Single agent: Writing agent creates content",
        "expected_agents": ["delegator", "writing"],
        "learning_focus": "Basic routing, single-agent execution"
    },
    "Code Generation": {
        "request": "Write a Python function to check if a number is prime, with docstring and example usage",
        "description": "Single agent: Code agent generates structured output",
        "expected_agents": ["delegator", "code"],
        "learning_focus": "Structured JSON output, code parsing"
    },
    "Data Analysis": {
        "request": "Analyze the following data: [10, 15, 23, 42, 8, 16, 35]. Calculate mean, median, and identify outliers.",
        "description": "Single agent: Data agent performs calculations",
        "expected_agents": ["delegator", "data"],
        "learning_focus": "Computational reasoning, statistical analysis"
    },
    "Research Task": {
        "request": "What are the key differences between async/await and threading in Python?",
        "description": "Single agent: Research synthesizes information",
        "expected_agents": ["delegator", "research"],
        "learning_focus": "Knowledge synthesis, source citation"
    },
    "Multi-Agent: Research + Write": {
        "request": "Research the latest trends in AI agent frameworks, then write a beginner-friendly summary",
        "description": "Multi-agent collaboration: Research then Writing",
        "expected_agents": ["delegator", "research", "writing"],
        "learning_focus": "Collaboration plan, state accumulation, agent handoff"
    },
    "Multi-Agent: Code + Document": {
        "request": "Create a Python decorator for timing function execution, and write documentation explaining how it works",
        "description": "Multi-agent: Code generates, Writing documents",
        "expected_agents": ["delegator", "code", "writing"],
        "learning_focus": "Sequential collaboration, context passing between agents"
    },
}


def render_request_input(on_submit: Optional[Callable[[str], None]] = None) -> Optional[str]:
    """
    Render the request input component.

    Args:
        on_submit: Callback function when request is submitted

    Returns:
        The submitted request string, or None if not submitted
    """
    st.subheader("📝 Your Request")

    # Example selector
    col1, col2 = st.columns([2, 1])

    with col1:
        example_names = ["(Select an example...)"] + list(EXAMPLE_REQUESTS.keys())
        selected_example = st.selectbox(
            "Quick Examples",
            options=example_names,
            index=0,
            help="Choose a preset example or type your own below"
        )

    with col2:
        if selected_example != "(Select an example...)":
            example = EXAMPLE_REQUESTS[selected_example]
            st.info(f"**Focus:** {example['learning_focus']}")

    # Show expected flow for selected example
    if selected_example != "(Select an example...)":
        example = EXAMPLE_REQUESTS[selected_example]
        with st.expander("📋 What to expect", expanded=False):
            st.markdown(f"**Description:** {example['description']}")
            st.markdown(f"**Expected Agent Flow:**")
            flow_str = " → ".join([f"`{a}`" for a in example['expected_agents']])
            st.markdown(flow_str)
            st.markdown(f"**Learning Focus:** {example['learning_focus']}")

    # Pre-fill text area if example selected
    default_text = ""
    if selected_example != "(Select an example...)":
        default_text = EXAMPLE_REQUESTS[selected_example]["request"]

    # Request text area
    request_text = st.text_area(
        "Enter your request:",
        value=default_text,
        height=100,
        placeholder="Type your request here... e.g., 'Write a function to sort a list'",
        key="request_input_text"
    )

    # Submit button row
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        submit_clicked = st.button(
            "🚀 Run",
            type="primary",
            disabled=not request_text.strip() or st.session_state.get("is_running", False),
            use_container_width=True
        )

    with col2:
        clear_clicked = st.button(
            "🗑️ Clear",
            disabled=st.session_state.get("is_running", False),
            use_container_width=True
        )

    with col3:
        if st.session_state.get("is_running", False):
            st.warning("⏳ Execution in progress...")

    # Handle clear
    if clear_clicked:
        st.session_state.current_request = ""
        st.rerun()

    # Handle submit
    if submit_clicked and request_text.strip():
        st.session_state.current_request = request_text.strip()
        if on_submit:
            on_submit(request_text.strip())
        return request_text.strip()

    return None


def render_request_status():
    """Render the current request status."""
    if st.session_state.get("current_request"):
        st.markdown("---")
        st.markdown("**Current Request:**")
        st.markdown(f"> {st.session_state.current_request}")

        if st.session_state.get("is_running"):
            current_node = st.session_state.get("current_node", "starting")
            st.markdown(f"**Status:** Running - currently at `{current_node}`")

            # Progress indicator
            visited = len(st.session_state.get("visited_nodes", set()))
            st.progress(min(visited / 6, 1.0))  # Rough progress (6 possible nodes)
