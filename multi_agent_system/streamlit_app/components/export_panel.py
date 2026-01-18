"""
Export Panel Component

Allows users to export execution data for learning and documentation.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime
import json


def render_export_panel(
    state: Optional[Dict[str, Any]] = None,
    timeline: Optional[List[Dict]] = None
):
    """
    Render the export panel for saving execution data.

    Args:
        state: The agent state to export
        timeline: The execution timeline to export
    """
    st.subheader("📥 Export Data")

    if state is None:
        state = st.session_state.get("agent_state")
    if timeline is None:
        timeline = st.session_state.get("timeline", [])

    if not state and not timeline:
        st.info("Run a request first to have data to export")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Export as JSON", use_container_width=True):
            _export_json(state, timeline)

    with col2:
        if st.button("📝 Export as Markdown", use_container_width=True):
            _export_markdown(state, timeline)

    with col3:
        if st.button("📋 Copy Summary", use_container_width=True):
            _copy_summary(state, timeline)


def _export_json(state: Dict, timeline: List[Dict]):
    """Export data as JSON."""
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "request": st.session_state.get("current_request", ""),
        "final_state": state,
        "timeline": timeline,
        "config": st.session_state.get("config", {}),
    }

    json_str = json.dumps(export_data, indent=2, default=str)

    st.download_button(
        label="💾 Download JSON",
        data=json_str,
        file_name=f"agent_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

    with st.expander("Preview JSON"):
        st.code(json_str[:2000] + "..." if len(json_str) > 2000 else json_str, language="json")


def _export_markdown(state: Dict, timeline: List[Dict]):
    """Export data as Markdown report."""
    request = st.session_state.get("current_request", "")
    config = st.session_state.get("config", {})

    md_parts = []

    # Header
    md_parts.append("# Multi-Agent Execution Report")
    md_parts.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_parts.append(f"\n**Model:** {config.get('model', 'N/A')}")
    md_parts.append(f"\n**Temperature:** {config.get('temperature', 'N/A')}")

    # Request
    md_parts.append("\n\n## User Request")
    md_parts.append(f"\n> {request}")

    # Execution Timeline
    md_parts.append("\n\n## Execution Timeline")
    for entry in timeline:
        step_num = entry.get("step_number", "?")
        node = entry.get("node_name", "unknown")
        step_type = entry.get("step_type", "")
        message = entry.get("details", {}).get("message", "")

        md_parts.append(f"\n### Step {step_num}: {node} ({step_type})")
        if message:
            md_parts.append(f"\n{message}")

        # Add details for important steps
        details = entry.get("details", {})
        if step_type == "llm_call" and "system_prompt" in details:
            md_parts.append("\n\n**System Prompt:**")
            md_parts.append(f"\n```\n{details['system_prompt'][:500]}...\n```")

        if step_type == "routing":
            md_parts.append(f"\n- **Selected Agent:** {details.get('selected_agent', 'N/A')}")
            md_parts.append(f"\n- **Reasoning:** {details.get('reasoning', 'N/A')}")

    # Final Output
    md_parts.append("\n\n## Final Output")

    if state.get("writing_output"):
        md_parts.append("\n### Writing Output")
        md_parts.append(f"\n{state['writing_output']}")

    if state.get("code_output"):
        md_parts.append("\n### Code Output")
        code = state["code_output"]
        if isinstance(code, dict) and "code" in code:
            lang = code.get("language", "python")
            md_parts.append(f"\n```{lang}\n{code['code']}\n```")
        else:
            md_parts.append(f"\n```\n{code}\n```")

    if state.get("research_results"):
        md_parts.append("\n### Research Results")
        research = state["research_results"]
        if isinstance(research, dict):
            if "findings" in research:
                md_parts.append(f"\n{research['findings']}")

    if state.get("analysis_results"):
        md_parts.append("\n### Analysis Results")
        md_parts.append(f"\n```json\n{json.dumps(state['analysis_results'], indent=2)}\n```")

    # State Summary
    md_parts.append("\n\n## State Summary")
    md_parts.append(f"\n- **Iterations:** {state.get('iteration_count', 0)}")
    md_parts.append(f"\n- **Collaboration:** {state.get('requires_collaboration', False)}")
    if state.get("collaboration_plan"):
        md_parts.append(f"\n- **Plan:** {' → '.join(state['collaboration_plan'])}")
    if state.get("errors"):
        md_parts.append(f"\n- **Errors:** {len(state['errors'])}")

    md_content = "\n".join(md_parts)

    st.download_button(
        label="💾 Download Markdown",
        data=md_content,
        file_name=f"agent_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown"
    )

    with st.expander("Preview Markdown"):
        st.markdown(md_content[:3000] + "..." if len(md_content) > 3000 else md_content)


def _copy_summary(state: Dict, timeline: List[Dict]):
    """Create a brief summary for clipboard."""
    request = st.session_state.get("current_request", "")

    summary_parts = [
        "=== Multi-Agent Execution Summary ===",
        f"Request: {request}",
        f"Steps: {len(timeline)}",
        f"Iterations: {state.get('iteration_count', 0)}",
    ]

    # Add visited agents
    visited = []
    for entry in timeline:
        node = entry.get("node_name")
        if node and node not in ["START", "END"] and node not in visited:
            visited.append(node)
    summary_parts.append(f"Agents: {' → '.join(visited)}")

    # Add output preview
    if state.get("writing_output"):
        preview = state["writing_output"][:100] + "..." if len(state["writing_output"]) > 100 else state["writing_output"]
        summary_parts.append(f"Output: {preview}")

    summary = "\n".join(summary_parts)

    st.text_area(
        "Summary (copy this):",
        value=summary,
        height=150,
        help="Select all and copy"
    )


def render_session_stats():
    """Render session statistics."""
    timeline = st.session_state.get("timeline", [])
    state = st.session_state.get("agent_state", {})

    if not timeline:
        return

    st.markdown("### 📊 Session Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Steps", len(timeline))

    with col2:
        llm_calls = sum(1 for t in timeline if t.get("step_type") == "llm_call")
        st.metric("LLM Calls", llm_calls)

    with col3:
        st.metric("Iterations", state.get("iteration_count", 0))

    with col4:
        errors = len(state.get("errors", []))
        st.metric("Errors", errors, delta_color="inverse" if errors else "off")
