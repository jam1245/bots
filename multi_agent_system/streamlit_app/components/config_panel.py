"""
Configuration Panel Component

Sidebar component for configuring the multi-agent system.
Allows users to adjust models, temperature, and learning settings.
"""

import streamlit as st
from typing import Dict, Any


# Available models with descriptions
MODELS = {
    "claude-3-5-haiku-20241022": {
        "name": "Claude 3.5 Haiku",
        "description": "Fastest & cheapest - $1/MTok input",
        "cost_tier": "💚 Budget"
    },
    "claude-3-5-sonnet-20241022": {
        "name": "Claude 3.5 Sonnet",
        "description": "Balanced performance - $3/MTok input",
        "cost_tier": "💛 Standard"
    },
    "claude-sonnet-4-5-20250929": {
        "name": "Claude Sonnet 4.5",
        "description": "Latest features - $3/MTok input",
        "cost_tier": "💛 Standard"
    },
    "claude-opus-4-5-20251101": {
        "name": "Claude Opus 4.5",
        "description": "Most powerful - $15/MTok input",
        "cost_tier": "❤️ Premium"
    },
}


def render_config_panel() -> Dict[str, Any]:
    """
    Render the configuration panel in the sidebar.

    Returns:
        Dictionary of configuration values
    """
    st.sidebar.title("⚙️ Configuration")

    # ========================================================================
    # Model Selection
    # ========================================================================
    st.sidebar.subheader("Model Settings")

    # Create display options for selectbox
    model_options = list(MODELS.keys())
    model_labels = [
        f"{MODELS[m]['cost_tier']} {MODELS[m]['name']}"
        for m in model_options
    ]

    current_model = st.session_state.config.get("model", model_options[0])
    current_index = model_options.index(current_model) if current_model in model_options else 0

    selected_model = st.sidebar.selectbox(
        "Select Model",
        options=model_options,
        index=current_index,
        format_func=lambda x: f"{MODELS[x]['cost_tier']} {MODELS[x]['name']}",
        help="Choose the Claude model. Haiku is cheapest for learning."
    )

    # Show model description
    st.sidebar.caption(MODELS[selected_model]["description"])

    # Temperature slider
    temperature = st.sidebar.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.config.get("temperature", 0.7),
        step=0.1,
        help="0.0 = deterministic, 1.0 = creative"
    )

    # Max iterations
    max_iterations = st.sidebar.number_input(
        "Max Iterations",
        min_value=1,
        max_value=20,
        value=st.session_state.config.get("max_iterations", 10),
        help="Maximum agent loop iterations (prevents infinite loops)"
    )

    st.sidebar.divider()

    # ========================================================================
    # Learning Mode Settings
    # ========================================================================
    st.sidebar.subheader("📚 Learning Mode")

    # Execution mode
    execution_mode = st.sidebar.radio(
        "Execution Mode",
        options=["auto", "step", "instant"],
        index=["auto", "step", "instant"].index(
            st.session_state.get("execution_mode", "auto")
        ),
        format_func=lambda x: {
            "auto": "🔄 Auto (with delay)",
            "step": "👆 Step-by-step",
            "instant": "⚡ Instant"
        }[x],
        help="Control how fast execution proceeds"
    )

    # Execution speed (only for auto mode)
    execution_speed = 1.0
    if execution_mode == "auto":
        execution_speed = st.sidebar.slider(
            "Auto Speed (seconds)",
            min_value=0.5,
            max_value=5.0,
            value=st.session_state.config.get("execution_speed", 1.0),
            step=0.5,
            help="Delay between steps in auto mode"
        )

    st.sidebar.divider()

    # ========================================================================
    # Display Settings
    # ========================================================================
    st.sidebar.subheader("👁️ Display Options")

    show_prompts = st.sidebar.checkbox(
        "Show System Prompts",
        value=st.session_state.config.get("show_prompts", True),
        help="Display the prompts sent to the LLM"
    )

    show_raw_responses = st.sidebar.checkbox(
        "Show Raw LLM Responses",
        value=st.session_state.config.get("show_raw_responses", True),
        help="Display unprocessed LLM output"
    )

    show_explanations = st.sidebar.checkbox(
        "Show Concept Explanations",
        value=st.session_state.get("show_explanations", True),
        help="Display educational tooltips and explanations"
    )

    st.sidebar.divider()

    # ========================================================================
    # Breakpoints (for step mode)
    # ========================================================================
    if execution_mode == "step":
        st.sidebar.subheader("🔴 Breakpoints")

        breakpoint_options = [
            "delegator",
            "writing",
            "code",
            "data",
            "research",
            "synthesis"
        ]

        current_breakpoints = st.session_state.get("breakpoints", set())

        selected_breakpoints = st.sidebar.multiselect(
            "Pause at nodes:",
            options=breakpoint_options,
            default=list(current_breakpoints),
            help="Execution will pause before these nodes"
        )

        st.session_state.breakpoints = set(selected_breakpoints)

    st.sidebar.divider()

    # ========================================================================
    # Info Section
    # ========================================================================
    with st.sidebar.expander("ℹ️ About This App"):
        st.markdown("""
        **Multi-Agent Learning Lab**

        This app visualizes how AI agents work together
        to complete complex tasks.

        **Key Concepts:**
        - **LangGraph**: Orchestrates agent workflows
        - **State**: Data shared between agents
        - **Delegator**: Routes requests to specialists
        - **Agents**: Writing, Code, Data, Research

        **Tips:**
        - Use Step mode to learn slowly
        - Watch the State Inspector for data flow
        - Check Timeline for detailed logs
        """)

    # ========================================================================
    # Update session state
    # ========================================================================
    st.session_state.config = {
        "model": selected_model,
        "temperature": temperature,
        "max_iterations": max_iterations,
        "show_prompts": show_prompts,
        "show_raw_responses": show_raw_responses,
        "execution_speed": execution_speed,
    }
    st.session_state.execution_mode = execution_mode
    st.session_state.show_explanations = show_explanations

    return st.session_state.config
