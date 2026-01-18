"""
Workflow Runner for Streamlit

This module runs the multi-agent workflow with hooks for
the Streamlit UI to observe and display execution details.

LEARNING POINT: Adapter Pattern
This class adapts the existing agent system to work with
Streamlit's execution model and UI requirements.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Generator
from datetime import datetime
import copy
import json

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Now import from the multi_agent_system
from graph.state import AgentState, create_initial_state
from agents.delegator import get_delegator_node, DelegationDecision
from agents.writing_agent import get_writing_agent_node
from agents.code_agent import get_code_agent_node
from agents.data_agent import get_data_agent_node
from agents.research_agent import get_research_agent_node
from utils.config import get_model, get_config

from .utils.execution_hooks import ExecutionTracker, get_tracker, reset_tracker


class StreamlitWorkflowRunner:
    """
    Runs the multi-agent workflow with detailed tracking for Streamlit UI.

    This class:
    1. Executes the workflow step by step
    2. Captures prompts, responses, and state changes
    3. Yields control back to Streamlit for UI updates
    4. Supports pausing and stepping through execution

    LEARNING POINT: Generator Pattern
    Using generators (yield) allows us to pause execution
    and update the UI between steps.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_iterations: int = 10
    ):
        self.model_name = model_name or get_config("DEFAULT_MODEL", default="claude-3-5-haiku-20241022")
        self.temperature = temperature if temperature is not None else get_config("TEMPERATURE", default=0.7, cast=float)
        self.max_iterations = max_iterations

        self.tracker = get_tracker()
        self.current_state: Optional[Dict] = None

        # Agent instances (using singleton getters)
        self._delegator = get_delegator_node()
        self._writing = get_writing_agent_node()
        self._code = get_code_agent_node()
        self._data = get_data_agent_node()
        self._research = get_research_agent_node()

    def run(self, user_request: str) -> Generator[Dict[str, Any], None, Dict[str, Any]]:
        """
        Run the workflow, yielding after each step.

        Args:
            user_request: The user's request to process

        Yields:
            Dict with step information after each step

        Returns:
            Final state when complete
        """
        # Reset tracker for new run
        reset_tracker()
        self.tracker = get_tracker()

        # Create initial state
        self.current_state = create_initial_state(user_request)

        yield {
            "step_type": "init",
            "node_name": "START",
            "message": "Workflow initialized",
            "state": copy.deepcopy(self.current_state)
        }

        # Step 1: Analyze request
        yield from self._run_analyze_request()

        # Main workflow loop
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            self.current_state["iteration_count"] = iteration

            # Step 2: Delegator decides which agent to use
            yield from self._run_delegator()

            selected_agent = self.current_state.get("selected_agent")

            # Check for FINISH
            if selected_agent == "FINISH":
                yield {
                    "step_type": "finish",
                    "node_name": "END",
                    "message": "Workflow complete - delegator returned FINISH",
                    "state": copy.deepcopy(self.current_state)
                }
                break

            # Step 3: Run selected agent
            if selected_agent == "writing":
                yield from self._run_writing()
            elif selected_agent == "code":
                yield from self._run_code()
            elif selected_agent == "data":
                yield from self._run_data()
            elif selected_agent == "research":
                yield from self._run_research()
            else:
                # Unknown agent - add error and finish
                self.current_state["errors"].append(f"Unknown agent: {selected_agent}")
                yield {
                    "step_type": "error",
                    "node_name": "workflow",
                    "message": f"Unknown agent: {selected_agent}",
                    "state": copy.deepcopy(self.current_state)
                }
                break

            # Step 4: Synthesis - decide if we need more iterations
            yield from self._run_synthesis()

            # Check if we should finish
            if self.current_state.get("next_action") == "finish":
                yield {
                    "step_type": "finish",
                    "node_name": "END",
                    "message": "Workflow complete",
                    "state": copy.deepcopy(self.current_state)
                }
                break

        # Safety: max iterations reached
        if iteration >= self.max_iterations:
            self.current_state["errors"].append(f"Max iterations ({self.max_iterations}) reached")
            yield {
                "step_type": "finish",
                "node_name": "END",
                "message": f"Max iterations reached ({self.max_iterations})",
                "state": copy.deepcopy(self.current_state)
            }

        return self.current_state

    def _run_analyze_request(self) -> Generator[Dict, None, None]:
        """Analyze the request to determine if collaboration is needed."""
        self.tracker.on_node_enter("analyze_request", self.current_state)

        yield {
            "step_type": "node_enter",
            "node_name": "analyze_request",
            "message": "Analyzing request for collaboration needs",
            "state": copy.deepcopy(self.current_state)
        }

        # Simple keyword-based analysis
        request = self.current_state["user_request"].lower()

        # Keywords that suggest multi-agent needs
        collaboration_keywords = [
            ("research", "write"),
            ("analyze", "write"),
            ("research", "summarize"),
            ("code", "explain"),
            ("code", "document"),
            ("analyze", "visualize"),
        ]

        requires_collaboration = False
        collaboration_plan = []

        for kw1, kw2 in collaboration_keywords:
            if kw1 in request and kw2 in request:
                requires_collaboration = True
                # Build a simple plan
                if "research" in request:
                    collaboration_plan.append("research")
                if "analyze" in request or "data" in request:
                    collaboration_plan.append("data")
                if "code" in request or "function" in request or "script" in request:
                    collaboration_plan.append("code")
                if "write" in request or "summarize" in request or "explain" in request or "document" in request:
                    collaboration_plan.append("writing")
                break

        # Remove duplicates while preserving order
        seen = set()
        collaboration_plan = [x for x in collaboration_plan if not (x in seen or seen.add(x))]

        self.current_state["requires_collaboration"] = requires_collaboration
        self.current_state["collaboration_plan"] = collaboration_plan if requires_collaboration else None

        self.tracker.on_node_exit("analyze_request", self.current_state, {
            "requires_collaboration": requires_collaboration,
            "collaboration_plan": collaboration_plan
        })

        yield {
            "step_type": "node_exit",
            "node_name": "analyze_request",
            "message": f"Analysis complete: {'multi-agent' if requires_collaboration else 'single-agent'} workflow",
            "details": {
                "requires_collaboration": requires_collaboration,
                "collaboration_plan": collaboration_plan
            },
            "state": copy.deepcopy(self.current_state)
        }

    def _run_delegator(self) -> Generator[Dict, None, None]:
        """Run the delegator to choose the next agent."""
        self.tracker.on_node_enter("delegator", self.current_state)

        yield {
            "step_type": "node_enter",
            "node_name": "delegator",
            "message": "Delegator analyzing request to choose agent",
            "state": copy.deepcopy(self.current_state)
        }

        # Capture the prompt that will be sent
        system_prompt = self._get_delegator_system_prompt()
        user_message = self._get_delegator_user_message()

        self.tracker.on_llm_call(
            "delegator",
            system_prompt,
            user_message,
            self.model_name,
            self.temperature
        )

        yield {
            "step_type": "llm_call",
            "node_name": "delegator",
            "message": "Sending request to LLM for routing decision",
            "details": {
                "system_prompt": system_prompt,
                "user_message": user_message,
                "model": self.model_name,
                "temperature": self.temperature
            },
            "state": copy.deepcopy(self.current_state)
        }

        # Actually run the delegator
        try:
            result = self._delegator(self.current_state)

            # Update state with result
            self.current_state.update(result)

            self.tracker.on_routing_decision(
                "delegator",
                result.get("selected_agent", "FINISH"),
                result.get("delegation_reasoning", "No reasoning provided"),
                None  # Could add confidence if available
            )

            yield {
                "step_type": "routing",
                "node_name": "delegator",
                "message": f"Routing to: {result.get('selected_agent')}",
                "details": {
                    "selected_agent": result.get("selected_agent"),
                    "reasoning": result.get("delegation_reasoning"),
                },
                "state": copy.deepcopy(self.current_state)
            }

        except Exception as e:
            self.tracker.on_error("delegator", e, "During delegation")
            self.current_state["errors"].append(f"Delegator error: {str(e)}")
            self.current_state["selected_agent"] = "FINISH"

            yield {
                "step_type": "error",
                "node_name": "delegator",
                "message": f"Error: {str(e)}",
                "state": copy.deepcopy(self.current_state)
            }

        self.tracker.on_node_exit("delegator", self.current_state)

    def _run_writing(self) -> Generator[Dict, None, None]:
        """Run the writing agent."""
        yield from self._run_agent("writing", self._writing)

    def _run_code(self) -> Generator[Dict, None, None]:
        """Run the code agent."""
        yield from self._run_agent("code", self._code)

    def _run_data(self) -> Generator[Dict, None, None]:
        """Run the data agent."""
        yield from self._run_agent("data", self._data)

    def _run_research(self) -> Generator[Dict, None, None]:
        """Run the research agent."""
        yield from self._run_agent("research", self._research)

    def _run_agent(self, agent_name: str, agent_func) -> Generator[Dict, None, None]:
        """Generic agent runner."""
        self.tracker.on_node_enter(agent_name, self.current_state)

        yield {
            "step_type": "node_enter",
            "node_name": agent_name,
            "message": f"{agent_name.title()} agent starting",
            "state": copy.deepcopy(self.current_state)
        }

        # Capture approximate prompt (agents build their own prompts)
        system_prompt = f"[{agent_name.title()} Agent System Prompt - see agent code for details]"
        user_message = self._get_agent_context_message(agent_name)

        self.tracker.on_llm_call(
            agent_name,
            system_prompt,
            user_message,
            self.model_name,
            self.temperature
        )

        yield {
            "step_type": "llm_call",
            "node_name": agent_name,
            "message": f"Sending request to LLM",
            "details": {
                "system_prompt": system_prompt,
                "user_message": user_message,
                "model": self.model_name
            },
            "state": copy.deepcopy(self.current_state)
        }

        # Run the agent
        try:
            result = agent_func(self.current_state)

            # Update state
            self.current_state.update(result)

            # Determine output key
            output_key = f"{agent_name}_output" if agent_name == "writing" else f"{agent_name}_results" if agent_name in ["research", "analysis"] else f"{agent_name}_output"
            if agent_name == "research":
                output_key = "research_results"
            elif agent_name == "data":
                output_key = "analysis_results"
            elif agent_name == "code":
                output_key = "code_output"

            output = result.get(output_key) or result.get("writing_output") or result.get("code_output") or result.get("research_results") or result.get("analysis_results")

            yield {
                "step_type": "node_exit",
                "node_name": agent_name,
                "message": f"{agent_name.title()} agent complete",
                "details": {
                    "output_preview": str(output)[:200] + "..." if output and len(str(output)) > 200 else output
                },
                "state": copy.deepcopy(self.current_state)
            }

        except Exception as e:
            self.tracker.on_error(agent_name, e, "During execution")
            self.current_state["errors"].append(f"{agent_name} error: {str(e)}")

            yield {
                "step_type": "error",
                "node_name": agent_name,
                "message": f"Error: {str(e)}",
                "state": copy.deepcopy(self.current_state)
            }

        self.tracker.on_node_exit(agent_name, self.current_state)

    def _run_synthesis(self) -> Generator[Dict, None, None]:
        """Run the synthesis step."""
        self.tracker.on_node_enter("synthesis", self.current_state)

        yield {
            "step_type": "node_enter",
            "node_name": "synthesis",
            "message": "Synthesizing results",
            "state": copy.deepcopy(self.current_state)
        }

        # Determine if we should continue or finish
        collaboration_plan = self.current_state.get("collaboration_plan", [])
        requires_collaboration = self.current_state.get("requires_collaboration", False)

        # Count completed outputs
        completed_agents = []
        if self.current_state.get("research_results"):
            completed_agents.append("research")
        if self.current_state.get("analysis_results"):
            completed_agents.append("data")
        if self.current_state.get("writing_output"):
            completed_agents.append("writing")
        if self.current_state.get("code_output"):
            completed_agents.append("code")

        # Decide next action
        if not requires_collaboration:
            # Single agent task - finish after first agent
            next_action = "finish"
        elif collaboration_plan:
            # Check if all planned agents have completed
            all_complete = all(agent in completed_agents for agent in collaboration_plan)
            next_action = "finish" if all_complete else "continue"
        else:
            # No plan but collaboration required - use heuristic
            next_action = "finish" if completed_agents else "continue"

        self.current_state["next_action"] = next_action

        # Add synthesis message
        synthesis_message = {
            "role": "synthesis",
            "content": f"Synthesis complete. Agents completed: {completed_agents}. Next action: {next_action}",
            "timestamp": datetime.now().isoformat()
        }
        self.current_state["messages"].append(synthesis_message)

        self.tracker.on_node_exit("synthesis", self.current_state, {
            "next_action": next_action,
            "completed_agents": completed_agents
        })

        yield {
            "step_type": "node_exit",
            "node_name": "synthesis",
            "message": f"Synthesis complete - next action: {next_action}",
            "details": {
                "completed_agents": completed_agents,
                "collaboration_plan": collaboration_plan,
                "next_action": next_action
            },
            "state": copy.deepcopy(self.current_state)
        }

    def _get_delegator_system_prompt(self) -> str:
        """Get the system prompt used by the delegator."""
        return """You are the Delegator - a meta-agent that routes requests to specialist agents.

AVAILABLE AGENTS:
- writing: For content creation, summaries, explanations, documentation
- code: For generating code, scripts, functions, programming tasks
- data: For data analysis, statistics, calculations, numerical tasks
- research: For information synthesis, research questions, fact-finding

RULES:
1. Analyze the user's request carefully
2. Choose the MOST appropriate agent
3. Return FINISH when the task is complete
4. Consider what outputs are already available

OUTPUT FORMAT (JSON):
{
    "selected_agent": "writing|code|data|research|FINISH",
    "reasoning": "Why you chose this agent",
    "instructions": "Specific guidance for the agent"
}"""

    def _get_delegator_user_message(self) -> str:
        """Build the user message for the delegator."""
        parts = [f"USER REQUEST: {self.current_state['user_request']}"]

        # Add available outputs
        if self.current_state.get("research_results"):
            parts.append("\nRESEARCH RESULTS AVAILABLE: Yes")
        if self.current_state.get("analysis_results"):
            parts.append("DATA ANALYSIS AVAILABLE: Yes")
        if self.current_state.get("writing_output"):
            parts.append("WRITING OUTPUT AVAILABLE: Yes")
        if self.current_state.get("code_output"):
            parts.append("CODE OUTPUT AVAILABLE: Yes")

        # Add collaboration plan if any
        if self.current_state.get("collaboration_plan"):
            parts.append(f"\nCOLLABORATION PLAN: {self.current_state['collaboration_plan']}")

        parts.append("\nSelect the next agent or FINISH if complete.")

        return "\n".join(parts)

    def _get_agent_context_message(self, agent_name: str) -> str:
        """Build context message showing what info is available to the agent."""
        parts = [f"REQUEST: {self.current_state['user_request']}"]

        if self.current_state.get("research_results"):
            parts.append(f"\nRESEARCH: {str(self.current_state['research_results'])[:500]}")
        if self.current_state.get("analysis_results"):
            parts.append(f"\nANALYSIS: {str(self.current_state['analysis_results'])[:500]}")
        if self.current_state.get("code_output"):
            parts.append(f"\nCODE: {str(self.current_state['code_output'])[:500]}")

        return "\n".join(parts)


def run_workflow_sync(
    user_request: str,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    max_iterations: int = 10
) -> Dict[str, Any]:
    """
    Run workflow synchronously (for non-streaming use).

    Args:
        user_request: The request to process
        model_name: Model to use
        temperature: Temperature setting
        max_iterations: Max loop iterations

    Returns:
        Final state dictionary
    """
    runner = StreamlitWorkflowRunner(model_name, temperature, max_iterations)

    final_state = None
    for step in runner.run(user_request):
        final_state = step.get("state")

    return final_state or {}
