"""
Output Display Component

Displays the final output from agent execution with
appropriate formatting for different output types.
"""

import streamlit as st
from typing import Dict, Any, Optional
import json


def render_output_display(state: Optional[Dict[str, Any]] = None):
    """
    Render the output display component.

    Shows the final results from agent execution, formatted
    appropriately for each output type.

    Args:
        state: The final agent state containing outputs
    """
    st.subheader("📤 Output")

    if state is None:
        state = st.session_state.get("agent_state")

    if not state:
        st.info("Run a request to see output here")
        return

    # Check for errors first
    errors = state.get("errors", [])
    if errors:
        st.error("**Errors occurred during execution:**")
        for error in errors:
            st.error(f"• {error}")

    # Determine which outputs are available
    has_writing = bool(state.get("writing_output"))
    has_code = bool(state.get("code_output"))
    has_research = bool(state.get("research_results"))
    has_data = bool(state.get("analysis_results"))

    output_count = sum([has_writing, has_code, has_research, has_data])

    if output_count == 0:
        st.warning("No output generated yet")
        return

    # If multiple outputs, use tabs
    if output_count > 1:
        tabs = []
        tab_names = []

        if has_writing:
            tab_names.append("📝 Writing")
        if has_code:
            tab_names.append("💻 Code")
        if has_research:
            tab_names.append("🔍 Research")
        if has_data:
            tab_names.append("📊 Data")

        tabs = st.tabs(tab_names)
        tab_index = 0

        if has_writing:
            with tabs[tab_index]:
                _render_writing_output(state["writing_output"])
            tab_index += 1

        if has_code:
            with tabs[tab_index]:
                _render_code_output(state["code_output"])
            tab_index += 1

        if has_research:
            with tabs[tab_index]:
                _render_research_output(state["research_results"])
            tab_index += 1

        if has_data:
            with tabs[tab_index]:
                _render_data_output(state["analysis_results"])
            tab_index += 1

    else:
        # Single output - display directly
        if has_writing:
            _render_writing_output(state["writing_output"])
        elif has_code:
            _render_code_output(state["code_output"])
        elif has_research:
            _render_research_output(state["research_results"])
        elif has_data:
            _render_data_output(state["analysis_results"])

    # Show delegation info
    if state.get("delegation_reasoning"):
        with st.expander("🧭 Routing Decision", expanded=False):
            st.markdown(f"**Selected Agent:** `{state.get('selected_agent', 'N/A')}`")
            st.markdown(f"**Reasoning:** {state.get('delegation_reasoning')}")


def _render_writing_output(output: str):
    """Render writing agent output."""
    st.markdown("### Writing Output")

    if not output:
        st.info("No writing output")
        return

    # Render as markdown (writing output is typically markdown-formatted)
    st.markdown(output)

    # Copy button
    st.text_area(
        "Copy raw text:",
        value=output,
        height=100,
        key="writing_output_copy",
        label_visibility="collapsed"
    )


def _render_code_output(output: Dict[str, Any]):
    """Render code agent output."""
    st.markdown("### Code Output")

    if not output:
        st.info("No code output")
        return

    # Handle string output (sometimes happens)
    if isinstance(output, str):
        st.code(output, language="python")
        return

    # Main code
    if "code" in output:
        language = output.get("language", "python")
        st.markdown(f"**Language:** `{language}`")
        st.code(output["code"], language=language)

    # Explanation
    if "explanation" in output:
        st.markdown("**Explanation:**")
        st.markdown(output["explanation"])

    # Usage example
    if "usage_example" in output:
        st.markdown("**Usage Example:**")
        st.code(output["usage_example"], language=output.get("language", "python"))

    # Dependencies
    if "dependencies" in output and output["dependencies"]:
        st.markdown("**Dependencies:**")
        for dep in output["dependencies"]:
            st.markdown(f"• `{dep}`")


def _render_research_output(output: Dict[str, Any]):
    """Render research agent output."""
    st.markdown("### Research Results")

    if not output:
        st.info("No research output")
        return

    # Handle string output
    if isinstance(output, str):
        st.markdown(output)
        return

    # Query
    if "query" in output:
        st.markdown(f"**Research Query:** {output['query']}")

    # Confidence
    if "confidence" in output:
        confidence = output["confidence"]
        if isinstance(confidence, (int, float)):
            st.progress(confidence)
            st.caption(f"Confidence: {confidence:.0%}")

    # Findings
    if "findings" in output:
        st.markdown("**Findings:**")
        st.markdown(output["findings"])

    # Sources
    if "sources" in output and output["sources"]:
        st.markdown("**Sources:**")
        for source in output["sources"]:
            if source.startswith("http"):
                st.markdown(f"• [{source}]({source})")
            else:
                st.markdown(f"• {source}")

    # Limitations
    if "limitations" in output and output["limitations"]:
        with st.expander("⚠️ Limitations"):
            for limitation in output["limitations"]:
                st.markdown(f"• {limitation}")


def _render_data_output(output: Dict[str, Any]):
    """Render data analysis agent output."""
    st.markdown("### Data Analysis Results")

    if not output:
        st.info("No analysis output")
        return

    # Handle string output
    if isinstance(output, str):
        st.markdown(output)
        return

    # Analysis type
    if "analysis_type" in output:
        st.markdown(f"**Analysis Type:** `{output['analysis_type']}`")

    # Results
    if "results" in output:
        st.markdown("**Results:**")
        results = output["results"]
        if isinstance(results, dict):
            # Try to display as metrics
            cols = st.columns(min(len(results), 4))
            for i, (key, value) in enumerate(list(results.items())[:4]):
                with cols[i % len(cols)]:
                    if isinstance(value, (int, float)):
                        st.metric(key, f"{value:.4g}" if isinstance(value, float) else value)
                    else:
                        st.markdown(f"**{key}:** {value}")

            # Show full results in expander
            if len(results) > 4:
                with st.expander("Full Results"):
                    st.json(results)
        else:
            st.json(results)

    # Insights
    if "insights" in output and output["insights"]:
        st.markdown("**Insights:**")
        for insight in output["insights"]:
            st.markdown(f"• {insight}")

    # Visualizations
    if "visualizations" in output and output["visualizations"]:
        st.markdown("**Suggested Visualizations:**")
        for viz in output["visualizations"]:
            st.markdown(f"• {viz}")


def render_raw_state(state: Optional[Dict[str, Any]] = None):
    """Render the raw state as JSON (for debugging)."""
    if state is None:
        state = st.session_state.get("agent_state")

    if not state:
        return

    with st.expander("🔧 Raw State (Debug)", expanded=False):
        st.json(state)
