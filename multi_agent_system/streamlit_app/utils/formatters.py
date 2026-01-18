"""
Formatting Utilities for Display

Helper functions to format various data types for
display in the Streamlit UI.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime


def format_json(data: Any, indent: int = 2) -> str:
    """
    Format data as pretty-printed JSON.

    Args:
        data: Data to format
        indent: Indentation level

    Returns:
        Formatted JSON string
    """
    try:
        return json.dumps(data, indent=indent, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(data)


def format_code(code: str, language: str = "python") -> str:
    """
    Format code for display with syntax highlighting markers.

    Args:
        code: The code to format
        language: Programming language for syntax highlighting

    Returns:
        Code wrapped in markdown code fence
    """
    return f"```{language}\n{code}\n```"


def format_state_diff(old_state: Optional[Dict], new_state: Dict) -> Dict[str, Any]:
    """
    Compute and format the difference between two states.

    Args:
        old_state: Previous state (can be None for initial state)
        new_state: Current state

    Returns:
        Dictionary with "added", "removed", "changed", and "unchanged" keys
    """
    if old_state is None:
        return {
            "added": new_state,
            "removed": {},
            "changed": {},
            "unchanged": {}
        }

    diff = {
        "added": {},
        "removed": {},
        "changed": {},
        "unchanged": {}
    }

    all_keys = set(old_state.keys()) | set(new_state.keys())

    for key in all_keys:
        old_val = old_state.get(key)
        new_val = new_state.get(key)

        if key not in old_state:
            diff["added"][key] = new_val
        elif key not in new_state:
            diff["removed"][key] = old_val
        elif old_val != new_val:
            diff["changed"][key] = {
                "from": _truncate_value(old_val),
                "to": _truncate_value(new_val)
            }
        else:
            diff["unchanged"][key] = _truncate_value(new_val)

    return diff


def _truncate_value(value: Any, max_length: int = 100) -> Any:
    """Truncate long values for display."""
    if isinstance(value, str) and len(value) > max_length:
        return value[:max_length] + "..."
    if isinstance(value, list) and len(value) > 5:
        return value[:5] + ["... ({} more)".format(len(value) - 5)]
    if isinstance(value, dict) and len(value) > 5:
        truncated = dict(list(value.items())[:5])
        truncated["..."] = f"({len(value) - 5} more keys)"
        return truncated
    return value


def format_timestamp(iso_timestamp: str) -> str:
    """
    Format ISO timestamp for display.

    Args:
        iso_timestamp: ISO format timestamp string

    Returns:
        Human-readable timestamp
    """
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%H:%M:%S.%f")[:-3]  # HH:MM:SS.mmm
    except (ValueError, TypeError):
        return iso_timestamp


def format_duration(duration_ms: Optional[float]) -> str:
    """
    Format duration in milliseconds for display.

    Args:
        duration_ms: Duration in milliseconds

    Returns:
        Human-readable duration string
    """
    if duration_ms is None:
        return "N/A"

    if duration_ms < 1000:
        return f"{duration_ms:.0f}ms"
    elif duration_ms < 60000:
        return f"{duration_ms / 1000:.2f}s"
    else:
        minutes = int(duration_ms // 60000)
        seconds = (duration_ms % 60000) / 1000
        return f"{minutes}m {seconds:.1f}s"


def format_tokens(tokens_used: Optional[Dict]) -> str:
    """
    Format token usage for display.

    Args:
        tokens_used: Dictionary with input_tokens, output_tokens

    Returns:
        Formatted token usage string
    """
    if not tokens_used:
        return "N/A"

    input_tokens = tokens_used.get("input_tokens", 0)
    output_tokens = tokens_used.get("output_tokens", 0)
    total = input_tokens + output_tokens

    return f"In: {input_tokens:,} | Out: {output_tokens:,} | Total: {total:,}"


def format_agent_output(agent_name: str, output: Any) -> str:
    """
    Format agent-specific output for display.

    Different agents produce different output structures,
    so we format them appropriately.

    Args:
        agent_name: Name of the agent
        output: The output from the agent

    Returns:
        Formatted output string (may include markdown)
    """
    if output is None:
        return "_No output_"

    if agent_name == "writing":
        # Writing output is typically just text
        return str(output)

    elif agent_name == "code":
        # Code output is a structured dict
        if isinstance(output, dict):
            parts = []
            if "code" in output:
                lang = output.get("language", "python")
                parts.append(f"**Code ({lang}):**\n```{lang}\n{output['code']}\n```")
            if "explanation" in output:
                parts.append(f"**Explanation:** {output['explanation']}")
            if "usage_example" in output:
                parts.append(f"**Usage:**\n```python\n{output['usage_example']}\n```")
            if "dependencies" in output and output["dependencies"]:
                parts.append(f"**Dependencies:** {', '.join(output['dependencies'])}")
            return "\n\n".join(parts) if parts else format_json(output)
        return str(output)

    elif agent_name == "research":
        # Research output has findings, sources, etc.
        if isinstance(output, dict):
            parts = []
            if "query" in output:
                parts.append(f"**Query:** {output['query']}")
            if "findings" in output:
                parts.append(f"**Findings:**\n{output['findings']}")
            if "sources" in output and output["sources"]:
                sources_list = "\n".join(f"- {s}" for s in output["sources"])
                parts.append(f"**Sources:**\n{sources_list}")
            if "confidence" in output:
                parts.append(f"**Confidence:** {output['confidence']:.0%}")
            if "limitations" in output and output["limitations"]:
                lim_list = "\n".join(f"- {l}" for l in output["limitations"])
                parts.append(f"**Limitations:**\n{lim_list}")
            return "\n\n".join(parts) if parts else format_json(output)
        return str(output)

    elif agent_name == "data":
        # Data analysis output
        if isinstance(output, dict):
            parts = []
            if "analysis_type" in output:
                parts.append(f"**Analysis Type:** {output['analysis_type']}")
            if "results" in output:
                parts.append(f"**Results:**\n```json\n{format_json(output['results'])}\n```")
            if "insights" in output and output["insights"]:
                insights_list = "\n".join(f"- {i}" for i in output["insights"])
                parts.append(f"**Insights:**\n{insights_list}")
            if "visualizations" in output and output["visualizations"]:
                viz_list = "\n".join(f"- {v}" for v in output["visualizations"])
                parts.append(f"**Suggested Visualizations:**\n{viz_list}")
            return "\n\n".join(parts) if parts else format_json(output)
        return str(output)

    elif agent_name == "delegator":
        # Delegation decision
        if isinstance(output, dict):
            parts = []
            if "selected_agent" in output:
                parts.append(f"**Selected Agent:** `{output['selected_agent']}`")
            if "reasoning" in output:
                parts.append(f"**Reasoning:** {output['reasoning']}")
            if "confidence" in output:
                parts.append(f"**Confidence:** {output['confidence']:.0%}")
            if "instructions" in output:
                parts.append(f"**Instructions:** {output['instructions']}")
            return "\n\n".join(parts) if parts else format_json(output)
        return str(output)

    else:
        # Generic formatting
        if isinstance(output, dict):
            return format_json(output)
        return str(output)


def truncate_prompt(prompt: str, max_lines: int = 20, max_chars: int = 2000) -> str:
    """
    Truncate a prompt for preview display.

    Args:
        prompt: The prompt text
        max_lines: Maximum number of lines
        max_chars: Maximum characters

    Returns:
        Truncated prompt with indicator if truncated
    """
    lines = prompt.split("\n")
    truncated_lines = False
    truncated_chars = False

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated_lines = True

    result = "\n".join(lines)

    if len(result) > max_chars:
        result = result[:max_chars]
        truncated_chars = True

    if truncated_lines or truncated_chars:
        result += "\n\n... (truncated)"

    return result


# Agent colors for visualization
AGENT_COLORS = {
    "delegator": "#FF6B6B",      # Red - Decision maker
    "writing": "#4ECDC4",        # Teal - Creative
    "code": "#45B7D1",           # Blue - Technical
    "data": "#96CEB4",           # Green - Analytical
    "research": "#FFEAA7",       # Yellow - Information
    "synthesis": "#DDA0DD",      # Plum - Combination
    "analyze_request": "#778899", # Slate - Analysis
    "START": "#90EE90",          # Light green
    "END": "#FFB6C1",            # Light pink
}


def get_agent_color(agent_name: str) -> str:
    """Get the color associated with an agent."""
    return AGENT_COLORS.get(agent_name, "#CCCCCC")


# Step type icons for timeline
STEP_TYPE_ICONS = {
    "node_enter": "▶️",
    "node_exit": "⏹️",
    "llm_call": "🤖",
    "llm_response": "💬",
    "tool_call": "🔧",
    "validation": "✅",
    "state_update": "📝",
    "routing": "🔀",
    "error": "❌",
}


def get_step_icon(step_type: str) -> str:
    """Get the icon for a step type."""
    return STEP_TYPE_ICONS.get(step_type, "•")
