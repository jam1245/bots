"""
Execution Timeline Component

Shows a detailed, step-by-step log of everything that
happens during agent execution - prompts, responses,
state changes, routing decisions.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from ..utils.formatters import (
    format_timestamp,
    format_duration,
    get_step_icon,
    get_agent_color,
    truncate_prompt
)


def render_timeline(
    timeline: Optional[List[Dict]] = None,
    show_prompts: bool = True,
    show_raw_responses: bool = True
):
    """
    Render the execution timeline.

    Shows every step of agent execution in chronological order
    with expandable details for learning.

    Args:
        timeline: List of execution steps (from tracker)
        show_prompts: Whether to show LLM prompts
        show_raw_responses: Whether to show raw LLM responses
    """
    st.subheader("📜 Execution Timeline")

    if timeline is None:
        timeline = st.session_state.get("timeline", [])

    if not timeline:
        st.info("Timeline will appear here as execution progresses")

        # Show what to expect
        with st.expander("📚 What you'll see here"):
            st.markdown("""
            The timeline shows every step of execution:

            - **▶️ Node Enter** - When an agent starts processing
            - **🤖 LLM Call** - The exact prompts sent to Claude
            - **💬 LLM Response** - Raw response before parsing
            - **✅ Validation** - Pydantic model validation
            - **📝 State Update** - Changes to AgentState
            - **🔀 Routing** - Delegator decisions
            - **⏹️ Node Exit** - When an agent finishes

            Expand each step to see full details!
            """)
        return

    # Render timeline entries
    for entry in timeline:
        _render_timeline_entry(
            entry,
            show_prompts=show_prompts,
            show_raw_responses=show_raw_responses
        )


def _render_timeline_entry(
    entry: Dict[str, Any],
    show_prompts: bool = True,
    show_raw_responses: bool = True
):
    """Render a single timeline entry."""
    step_type = entry.get("step_type", "unknown")
    node_name = entry.get("node_name", "unknown")
    details = entry.get("details", {})
    timestamp = entry.get("timestamp", "")
    step_number = entry.get("step_number", 0)
    duration_ms = entry.get("duration_ms")

    # Get styling
    icon = get_step_icon(step_type)
    color = get_agent_color(node_name)

    # Build header
    header = f"{icon} **Step {step_number}** | `{node_name}` | {step_type}"
    if duration_ms:
        header += f" | ⏱️ {format_duration(duration_ms)}"

    # Determine if this entry should be expanded
    is_important = step_type in ("llm_call", "routing", "error", "validation")

    with st.expander(header, expanded=is_important):
        # Timestamp
        st.caption(f"🕐 {format_timestamp(timestamp)}")

        # Message
        if "message" in details:
            st.markdown(f"**{details['message']}**")

        # Step-type specific rendering
        if step_type == "node_enter":
            _render_node_enter(details)
        elif step_type == "node_exit":
            _render_node_exit(details)
        elif step_type == "llm_call":
            _render_llm_call(details, show_prompts)
        elif step_type == "llm_response":
            _render_llm_response(details, show_raw_responses)
        elif step_type == "tool_call":
            _render_tool_call(details)
        elif step_type == "validation":
            _render_validation(details)
        elif step_type == "state_update":
            _render_state_update(details)
        elif step_type == "routing":
            _render_routing(details)
        elif step_type == "error":
            _render_error(details)


def _render_node_enter(details: Dict):
    """Render node entry details."""
    if "input_state_keys" in details:
        keys = details["input_state_keys"]
        st.markdown(f"**Available state fields:** {', '.join(f'`{k}`' for k in keys)}")


def _render_node_exit(details: Dict):
    """Render node exit details."""
    if "output_keys" in details:
        keys = details["output_keys"]
        if keys:
            st.markdown(f"**Output fields:** {', '.join(f'`{k}`' for k in keys)}")

    if "duration_ms" in details and details["duration_ms"]:
        st.metric("Execution Time", format_duration(details["duration_ms"]))


def _render_llm_call(details: Dict, show_prompts: bool):
    """Render LLM call details - THE MOST IMPORTANT FOR LEARNING."""
    # Model info
    col1, col2 = st.columns(2)
    with col1:
        if "model" in details:
            st.markdown(f"**Model:** `{details['model']}`")
    with col2:
        if "temperature" in details:
            st.markdown(f"**Temperature:** {details['temperature']}")

    if show_prompts:
        # System prompt
        if "system_prompt" in details and details["system_prompt"]:
            st.markdown("---")
            st.markdown("**📋 System Prompt:**")
            with st.container():
                prompt = details["system_prompt"]
                # Show truncated version with option to expand
                if len(prompt) > 500:
                    st.text_area(
                        "System prompt (scroll to see all):",
                        value=prompt,
                        height=200,
                        disabled=True,
                        label_visibility="collapsed"
                    )
                else:
                    st.code(prompt, language=None)

            # Educational note about system prompts
            st.caption("💡 System prompts define the agent's role, capabilities, and output format")

        # User message
        if "user_message" in details and details["user_message"]:
            st.markdown("---")
            st.markdown("**💬 User Message:**")
            user_msg = details["user_message"]
            if len(user_msg) > 500:
                st.text_area(
                    "User message:",
                    value=user_msg,
                    height=150,
                    disabled=True,
                    label_visibility="collapsed"
                )
            else:
                st.code(user_msg, language=None)

            st.caption("💡 User messages contain the request + context from previous agents")


def _render_llm_response(details: Dict, show_raw: bool):
    """Render LLM response details."""
    if show_raw and "raw_response" in details:
        st.markdown("**🤖 Raw LLM Response:**")
        response = details["raw_response"]
        if len(response) > 1000:
            st.text_area(
                "Raw response:",
                value=response,
                height=200,
                disabled=True,
                label_visibility="collapsed"
            )
        else:
            st.code(response, language=None)

        st.caption("💡 This is the unprocessed output - agents parse this into structured data")

    if "parsed_response" in details and details["parsed_response"]:
        st.markdown("**📊 Parsed Response:**")
        st.json(details["parsed_response"])

    if "tokens_used" in details and details["tokens_used"]:
        tokens = details["tokens_used"]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Input Tokens", tokens.get("input_tokens", "N/A"))
        with col2:
            st.metric("Output Tokens", tokens.get("output_tokens", "N/A"))
        with col3:
            total = tokens.get("input_tokens", 0) + tokens.get("output_tokens", 0)
            st.metric("Total", total)


def _render_tool_call(details: Dict):
    """Render tool call details."""
    if "tool_name" in details:
        st.markdown(f"**Tool:** `{details['tool_name']}`")

    if "tool_input" in details:
        st.markdown("**Input:**")
        st.json(details["tool_input"])

    if "tool_output" in details:
        st.markdown("**Output:**")
        output = details["tool_output"]
        if isinstance(output, str) and len(output) > 500:
            st.text_area("Output:", value=output, height=150, disabled=True, label_visibility="collapsed")
        else:
            st.json(output) if isinstance(output, (dict, list)) else st.code(str(output))

    st.caption("💡 Tools extend agent capabilities (web search, calculations, etc.)")


def _render_validation(details: Dict):
    """Render Pydantic validation details."""
    if "validation_type" in details:
        st.markdown(f"**Validation Type:** `{details['validation_type']}`")

    if "passed" in details:
        if details["passed"]:
            st.success("✅ Validation PASSED")
        else:
            st.error("❌ Validation FAILED")

    if "input_data" in details:
        st.markdown("**Data Validated:**")
        st.json(details["input_data"])

    if "errors" in details and details["errors"]:
        st.markdown("**Validation Errors:**")
        for error in details["errors"]:
            st.error(f"• {error}")

    st.caption("💡 Pydantic models ensure structured, type-safe outputs from LLMs")


def _render_state_update(details: Dict):
    """Render state update details."""
    if "field" in details:
        st.markdown(f"**Field:** `{details['field']}`")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Before:**")
        old = details.get("old_value")
        if old is None:
            st.code("None")
        elif isinstance(old, (dict, list)):
            st.json(old)
        else:
            st.code(str(old))

    with col2:
        st.markdown("**After:**")
        new = details.get("new_value")
        if new is None:
            st.code("None")
        elif isinstance(new, (dict, list)):
            st.json(new)
        else:
            st.code(str(new))


def _render_routing(details: Dict):
    """Render routing decision details."""
    col1, col2 = st.columns(2)
    with col1:
        if "from_node" in details:
            st.markdown(f"**From:** `{details['from_node']}`")
    with col2:
        if "to_node" in details:
            st.markdown(f"**To:** `{details['to_node']}`")

    if "reason" in details:
        st.markdown("**Reasoning:**")
        st.info(details["reason"])

    if "confidence" in details and details["confidence"] is not None:
        st.progress(details["confidence"])
        st.caption(f"Confidence: {details['confidence']:.0%}")

    st.caption("💡 The delegator uses LLM reasoning to route requests to specialist agents")


def _render_error(details: Dict):
    """Render error details."""
    st.error("An error occurred during execution")

    if "error_type" in details:
        st.markdown(f"**Error Type:** `{details['error_type']}`")

    if "error_message" in details:
        st.markdown("**Message:**")
        st.code(details["error_message"])

    if "context" in details:
        st.markdown(f"**Context:** {details['context']}")

    st.caption("💡 Agents handle errors gracefully and add them to the errors list in state")


def render_timeline_summary(timeline: Optional[List[Dict]] = None):
    """Render a summary of the timeline."""
    if timeline is None:
        timeline = st.session_state.get("timeline", [])

    if not timeline:
        return

    # Count step types
    step_counts = {}
    total_duration = 0

    for entry in timeline:
        step_type = entry.get("step_type", "unknown")
        step_counts[step_type] = step_counts.get(step_type, 0) + 1

        if entry.get("duration_ms"):
            total_duration += entry["duration_ms"]

    # Display summary
    st.markdown("### 📊 Execution Summary")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Steps", len(timeline))
    with col2:
        llm_calls = step_counts.get("llm_call", 0)
        st.metric("LLM Calls", llm_calls)
    with col3:
        st.metric("Total Time", format_duration(total_duration))

    # Step type breakdown
    with st.expander("Step Breakdown"):
        for step_type, count in sorted(step_counts.items(), key=lambda x: -x[1]):
            icon = get_step_icon(step_type)
            st.markdown(f"{icon} **{step_type}:** {count}")
