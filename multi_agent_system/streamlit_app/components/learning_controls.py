"""
Learning Controls Component

Provides controls for educational exploration:
- Step-through execution
- Speed control
- Breakpoints
- Concept explanations
"""

import streamlit as st
from typing import Optional, Callable


def render_learning_controls(
    on_step: Optional[Callable] = None,
    on_continue: Optional[Callable] = None,
    on_reset: Optional[Callable] = None
):
    """
    Render learning mode controls.

    Args:
        on_step: Callback for step button
        on_continue: Callback for continue button
        on_reset: Callback for reset button
    """
    execution_mode = st.session_state.get("execution_mode", "auto")
    is_running = st.session_state.get("is_running", False)
    is_paused = st.session_state.get("paused", False)

    st.markdown("### 🎮 Execution Controls")

    if execution_mode == "step":
        _render_step_controls(on_step, on_continue, on_reset, is_running, is_paused)
    elif execution_mode == "auto":
        _render_auto_controls(on_continue, on_reset, is_running, is_paused)
    else:  # instant
        _render_instant_controls(on_reset, is_running)


def _render_step_controls(
    on_step: Optional[Callable],
    on_continue: Optional[Callable],
    on_reset: Optional[Callable],
    is_running: bool,
    is_paused: bool
):
    """Render controls for step-by-step mode."""

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        step_clicked = st.button(
            "▶️ Step",
            disabled=not is_running or not is_paused,
            use_container_width=True,
            help="Execute one step"
        )
        if step_clicked and on_step:
            on_step()

    with col2:
        continue_clicked = st.button(
            "⏩ Continue",
            disabled=not is_running or not is_paused,
            use_container_width=True,
            help="Run until next breakpoint or end"
        )
        if continue_clicked and on_continue:
            on_continue()

    with col3:
        pause_clicked = st.button(
            "⏸️ Pause" if not is_paused else "⏸️ Paused",
            disabled=not is_running or is_paused,
            use_container_width=True,
            help="Pause execution"
        )
        if pause_clicked:
            st.session_state.paused = True

    with col4:
        reset_clicked = st.button(
            "🔄 Reset",
            use_container_width=True,
            help="Clear and start over"
        )
        if reset_clicked and on_reset:
            on_reset()

    # Show current state info
    if is_running:
        current_node = st.session_state.get("current_node", "N/A")
        current_step = st.session_state.get("current_step", 0)

        st.info(f"**Current Position:** `{current_node}` | **Step:** {current_step}")

        # Check for breakpoints
        breakpoints = st.session_state.get("breakpoints", set())
        if current_node in breakpoints:
            st.warning(f"🔴 Breakpoint hit at `{current_node}`")


def _render_auto_controls(
    on_continue: Optional[Callable],
    on_reset: Optional[Callable],
    is_running: bool,
    is_paused: bool
):
    """Render controls for auto mode."""

    col1, col2, col3 = st.columns(3)

    with col1:
        if is_paused:
            resume_clicked = st.button(
                "▶️ Resume",
                use_container_width=True,
                help="Resume auto execution"
            )
            if resume_clicked:
                st.session_state.paused = False
                if on_continue:
                    on_continue()
        else:
            pause_clicked = st.button(
                "⏸️ Pause",
                disabled=not is_running,
                use_container_width=True,
                help="Pause execution"
            )
            if pause_clicked:
                st.session_state.paused = True

    with col2:
        # Speed indicator
        speed = st.session_state.config.get("execution_speed", 1.0)
        st.markdown(f"**Speed:** {speed}s delay")

    with col3:
        reset_clicked = st.button(
            "🔄 Reset",
            use_container_width=True,
            help="Clear and start over"
        )
        if reset_clicked and on_reset:
            on_reset()

    if is_running and not is_paused:
        st.info("⏳ Auto-executing... (adjust speed in sidebar)")


def _render_instant_controls(
    on_reset: Optional[Callable],
    is_running: bool
):
    """Render controls for instant mode."""

    col1, col2 = st.columns(2)

    with col1:
        if is_running:
            st.info("⚡ Running at full speed...")
        else:
            st.markdown("_Ready for instant execution_")

    with col2:
        reset_clicked = st.button(
            "🔄 Reset",
            use_container_width=True,
            help="Clear and start over"
        )
        if reset_clicked and on_reset:
            on_reset()


def render_concept_cards():
    """Render educational concept cards based on current context."""

    current_node = st.session_state.get("current_node")
    show_explanations = st.session_state.get("show_explanations", True)

    if not show_explanations:
        return

    st.markdown("### 💡 Learning Concepts")

    # Show relevant concept based on current node
    if current_node == "delegator":
        _render_concept_card(
            "Meta-Agent Pattern",
            """
            The **delegator** is a meta-agent - an agent that manages other agents.

            **How it works:**
            1. Receives the user request
            2. Uses LLM reasoning to analyze the request
            3. Routes to the most appropriate specialist
            4. Can be called multiple times for complex tasks

            **Key Code:**
            ```python
            class DelegationDecision(BaseModel):
                selected_agent: Literal["writing", "code", "data", "research", "FINISH"]
                reasoning: str
                confidence: float
            ```

            This Pydantic model ensures structured, validated output from the LLM.
            """,
            "delegator"
        )

    elif current_node in ["writing", "code", "data", "research"]:
        _render_concept_card(
            "Single-Purpose Agent",
            f"""
            **{current_node.title()} Agent** is a specialist focused on one task type.

            **Design Principle:** Each agent should do ONE thing well.

            **Benefits:**
            - Easier to test and debug
            - Better prompts (more focused)
            - Simpler maintenance
            - Can use different models per agent

            **Pattern in LangGraph:**
            ```python
            # Agent as a callable class
            class {current_node.title()}Agent:
                def __call__(self, state: AgentState) -> Dict:
                    # Process and return state updates
                    return {{"output_field": result}}
            ```
            """,
            current_node
        )

    elif current_node == "synthesis":
        _render_concept_card(
            "State Synthesis",
            """
            The **synthesis** node combines outputs from multiple agents.

            **Responsibilities:**
            1. Check what outputs are available
            2. Determine if collaboration plan is complete
            3. Decide: continue (loop back) or finish

            **Key Decision:**
            ```python
            if collaboration_complete:
                return {"next_action": "finish"}
            else:
                return {"next_action": "continue"}
            ```

            This enables **iterative refinement** where agents build on each other's work.
            """,
            "synthesis"
        )

    elif current_node == "analyze_request":
        _render_concept_card(
            "Request Analysis",
            """
            This node analyzes whether the request needs multiple agents.

            **Detection Patterns:**
            - Keywords: "research AND write", "analyze AND summarize"
            - Explicit steps: "first..., then..."
            - Complex requirements: multiple distinct tasks

            **Output:**
            ```python
            {
                "requires_collaboration": True/False,
                "collaboration_plan": ["research", "data", "writing"]
            }
            ```

            Simple requests go straight to one agent.
            Complex requests get a multi-step plan.
            """,
            "analyze_request"
        )


def _render_concept_card(title: str, content: str, node_name: str):
    """Render a single concept card."""
    from ..utils.formatters import get_agent_color

    color = get_agent_color(node_name)

    st.markdown(f"""
    <div style="
        border-left: 4px solid {color};
        padding: 12px;
        margin: 8px 0;
        background-color: #f8f9fa;
        border-radius: 0 8px 8px 0;
    ">
        <h4 style="margin-top: 0;">{title}</h4>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(content)


def render_keyboard_shortcuts():
    """Display keyboard shortcuts (for documentation)."""
    with st.expander("⌨️ Tips"):
        st.markdown("""
        **Quick Tips:**

        - Use **Step mode** when learning a new concept
        - Watch the **State Inspector** to see data flow
        - Expand **Timeline entries** to see exact prompts
        - Check **Routing decisions** to understand delegator logic

        **Best Practices:**

        1. Start with simple requests (single agent)
        2. Progress to multi-agent collaboration
        3. Compare similar requests with different phrasings
        4. Experiment with temperature settings
        """)
