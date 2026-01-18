"""
Execution Hooks for Tracking Agent Operations

This module provides callbacks that hook into the agent execution
to capture detailed information for the educational UI.

LEARNING CONCEPT: Observer Pattern
These hooks allow us to "observe" what's happening inside the
agents without modifying their core logic. This is a clean way
to add monitoring/logging to any system.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
import json
import copy


@dataclass
class ExecutionStep:
    """Represents a single step in the execution timeline."""
    timestamp: str
    step_number: int
    step_type: str  # "node_enter", "node_exit", "llm_call", "tool_call", "state_update"
    node_name: str
    details: Dict[str, Any] = field(default_factory=dict)
    state_snapshot: Optional[Dict] = None
    duration_ms: Optional[float] = None


class ExecutionTracker:
    """
    Tracks execution of the multi-agent workflow for educational display.

    WHAT THIS CLASS DOES:
    - Captures every step of agent execution
    - Records prompts sent to the LLM
    - Stores raw LLM responses
    - Tracks state changes between steps
    - Measures timing for each operation

    WHY IT EXISTS:
    The core agents should remain focused on their task. This tracker
    acts as an observer, collecting data for visualization without
    cluttering the agent code.

    USAGE:
        tracker = ExecutionTracker()

        # Before calling an agent
        tracker.on_node_enter("delegator", current_state)

        # When making an LLM call
        tracker.on_llm_call("delegator", system_prompt, user_message)

        # After receiving LLM response
        tracker.on_llm_response("delegator", raw_response, parsed_response)

        # After agent completes
        tracker.on_node_exit("delegator", new_state)
    """

    def __init__(self):
        self.steps: List[ExecutionStep] = []
        self.current_state: Optional[Dict] = None
        self._step_start_time: Optional[datetime] = None
        self._current_node: Optional[str] = None

    def reset(self):
        """Clear all tracked data for a new execution."""
        self.steps = []
        self.current_state = None
        self._step_start_time = None
        self._current_node = None

    def _create_step(
        self,
        step_type: str,
        node_name: str,
        details: Dict[str, Any],
        state_snapshot: Optional[Dict] = None
    ) -> ExecutionStep:
        """Create a new execution step."""
        return ExecutionStep(
            timestamp=datetime.now().isoformat(),
            step_number=len(self.steps) + 1,
            step_type=step_type,
            node_name=node_name,
            details=details,
            state_snapshot=copy.deepcopy(state_snapshot) if state_snapshot else None
        )

    def on_node_enter(self, node_name: str, state: Dict[str, Any]):
        """
        Called when execution enters a node (agent).

        Args:
            node_name: Name of the node being entered
            state: Current state when entering the node
        """
        self._step_start_time = datetime.now()
        self._current_node = node_name

        step = self._create_step(
            step_type="node_enter",
            node_name=node_name,
            details={
                "message": f"Entering {node_name} node",
                "input_state_keys": list(state.keys()) if state else [],
            },
            state_snapshot=state
        )
        self.steps.append(step)

        # Update session state if available
        if hasattr(st, 'session_state'):
            st.session_state.current_node = node_name
            st.session_state.visited_nodes.add(node_name)

    def on_node_exit(self, node_name: str, state: Dict[str, Any], result: Optional[Dict] = None):
        """
        Called when execution exits a node.

        Args:
            node_name: Name of the node being exited
            state: State after node execution
            result: Optional result/output from the node
        """
        duration_ms = None
        if self._step_start_time:
            duration_ms = (datetime.now() - self._step_start_time).total_seconds() * 1000

        step = self._create_step(
            step_type="node_exit",
            node_name=node_name,
            details={
                "message": f"Exiting {node_name} node",
                "output_keys": list(result.keys()) if result else [],
                "duration_ms": duration_ms,
            },
            state_snapshot=state
        )
        step.duration_ms = duration_ms
        self.steps.append(step)

        self.current_state = copy.deepcopy(state)
        self._current_node = None

    def on_llm_call(
        self,
        node_name: str,
        system_prompt: str,
        user_message: str,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """
        Called when an LLM call is about to be made.

        This is crucial for understanding prompt engineering!

        Args:
            node_name: Name of the calling node
            system_prompt: The system prompt sent to the LLM
            user_message: The user/human message sent
            model_name: Which model is being used
            temperature: Temperature setting for this call
        """
        step = self._create_step(
            step_type="llm_call",
            node_name=node_name,
            details={
                "message": "Sending request to LLM",
                "system_prompt": system_prompt,
                "user_message": user_message,
                "model": model_name,
                "temperature": temperature,
            }
        )
        self.steps.append(step)

    def on_llm_response(
        self,
        node_name: str,
        raw_response: str,
        parsed_response: Optional[Dict] = None,
        tokens_used: Optional[Dict] = None
    ):
        """
        Called when an LLM response is received.

        Args:
            node_name: Name of the calling node
            raw_response: The raw text response from the LLM
            parsed_response: The parsed/structured response (if any)
            tokens_used: Token usage statistics
        """
        step = self._create_step(
            step_type="llm_response",
            node_name=node_name,
            details={
                "message": "Received LLM response",
                "raw_response": raw_response,
                "parsed_response": parsed_response,
                "tokens_used": tokens_used,
            }
        )
        self.steps.append(step)

    def on_tool_call(
        self,
        node_name: str,
        tool_name: str,
        tool_input: Any,
        tool_output: Optional[Any] = None
    ):
        """
        Called when a tool (like web search) is invoked.

        Args:
            node_name: Name of the calling node
            tool_name: Name of the tool being called
            tool_input: Input provided to the tool
            tool_output: Output from the tool (if available)
        """
        step = self._create_step(
            step_type="tool_call",
            node_name=node_name,
            details={
                "message": f"Calling tool: {tool_name}",
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_output": tool_output,
            }
        )
        self.steps.append(step)

    def on_validation(
        self,
        node_name: str,
        validation_type: str,
        input_data: Any,
        validation_result: bool,
        errors: Optional[List[str]] = None
    ):
        """
        Called when Pydantic or other validation occurs.

        Args:
            node_name: Name of the calling node
            validation_type: Type of validation (e.g., "DelegationDecision")
            input_data: Data being validated
            validation_result: Whether validation passed
            errors: Validation error messages (if any)
        """
        step = self._create_step(
            step_type="validation",
            node_name=node_name,
            details={
                "message": f"Validating {validation_type}",
                "validation_type": validation_type,
                "input_data": input_data,
                "passed": validation_result,
                "errors": errors or [],
            }
        )
        self.steps.append(step)

    def on_state_update(
        self,
        node_name: str,
        field_name: str,
        old_value: Any,
        new_value: Any
    ):
        """
        Called when a specific state field is updated.

        Args:
            node_name: Name of the node making the update
            field_name: Name of the state field being updated
            old_value: Previous value
            new_value: New value
        """
        step = self._create_step(
            step_type="state_update",
            node_name=node_name,
            details={
                "message": f"Updating state: {field_name}",
                "field": field_name,
                "old_value": self._safe_serialize(old_value),
                "new_value": self._safe_serialize(new_value),
            }
        )
        self.steps.append(step)

    def on_routing_decision(
        self,
        from_node: str,
        to_node: str,
        reason: str,
        confidence: Optional[float] = None
    ):
        """
        Called when a routing decision is made (especially from delegator).

        Args:
            from_node: Node making the decision
            to_node: Node being routed to
            reason: Explanation for the routing
            confidence: Confidence score (0-1)
        """
        step = self._create_step(
            step_type="routing",
            node_name=from_node,
            details={
                "message": f"Routing from {from_node} to {to_node}",
                "from_node": from_node,
                "to_node": to_node,
                "reason": reason,
                "confidence": confidence,
            }
        )
        self.steps.append(step)

        # Update edge history
        if hasattr(st, 'session_state'):
            st.session_state.edge_history.append((from_node, to_node))

    def on_error(self, node_name: str, error: Exception, context: Optional[str] = None):
        """
        Called when an error occurs.

        Args:
            node_name: Node where error occurred
            error: The exception
            context: Additional context about what was happening
        """
        step = self._create_step(
            step_type="error",
            node_name=node_name,
            details={
                "message": f"Error in {node_name}",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
            }
        )
        self.steps.append(step)

    def _safe_serialize(self, value: Any) -> Any:
        """Safely serialize a value for storage/display."""
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (list, tuple)):
            return [self._safe_serialize(v) for v in value]
        if isinstance(value, dict):
            return {k: self._safe_serialize(v) for k, v in value.items()}
        # For other types, convert to string
        try:
            return str(value)
        except:
            return "<unserializable>"

    def get_timeline(self) -> List[Dict]:
        """Get all steps as a list of dictionaries."""
        return [
            {
                "timestamp": step.timestamp,
                "step_number": step.step_number,
                "step_type": step.step_type,
                "node_name": step.node_name,
                "details": step.details,
                "state_snapshot": step.state_snapshot,
                "duration_ms": step.duration_ms,
            }
            for step in self.steps
        ]

    def get_steps_for_node(self, node_name: str) -> List[ExecutionStep]:
        """Get all steps for a specific node."""
        return [s for s in self.steps if s.node_name == node_name]

    def get_llm_calls(self) -> List[ExecutionStep]:
        """Get all LLM call steps (useful for understanding prompts)."""
        return [s for s in self.steps if s.step_type == "llm_call"]

    def get_state_changes(self) -> List[ExecutionStep]:
        """Get all state update steps."""
        return [s for s in self.steps if s.step_type == "state_update"]


# Global tracker instance for use across the app
_global_tracker: Optional[ExecutionTracker] = None


def get_tracker() -> ExecutionTracker:
    """Get or create the global execution tracker."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = ExecutionTracker()
    return _global_tracker


def reset_tracker():
    """Reset the global tracker for a new execution."""
    global _global_tracker
    if _global_tracker:
        _global_tracker.reset()
    else:
        _global_tracker = ExecutionTracker()
