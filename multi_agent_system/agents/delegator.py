"""
Delegator Agent: Intelligent Request Routing Coordinator

WHAT THIS AGENT DOES:
Analyzes user requests and routes them to the appropriate specialized agent(s).
This is the "brain" of the multi-agent system - it decides WHO does WHAT.

WHY THIS AGENT EXISTS:
Different requests require different capabilities:
- "Write a summary" → Writing agent
- "Generate Python code" → Code agent
- "Analyze this data" → Data analysis agent
- "Research topic X" → Research agent

The delegator makes these routing decisions intelligently using an LLM.

KEY LEARNING CONCEPTS:
- Meta-agent pattern (an agent that manages other agents)
- LLM-powered routing (vs hardcoded rules)
- Structured output with Pydantic for validation
- Context-aware decision making
- Multi-step workflow planning

PATTERN DEMONSTRATED:
This is a "Coordinator Agent" - it doesn't do the work itself, but decides
who should do it. Common in production multi-agent systems.

Example:
    from agents.delegator import Delegator
    from graph.state import create_initial_state

    delegator = Delegator()
    state = create_initial_state("Write code to sort a list")
    result = delegator(state)
    print(result["selected_agent"])  # "code"
    print(result["delegation_reasoning"])  # Why code agent was chosen
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, ValidationError
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser

# Import from our modules
from utils.config import get_model
from graph.state import AgentState

# Set up logging
logger = logging.getLogger(__name__)


# ============================================================================
# STRUCTURED OUTPUT MODELS
# ============================================================================

class DelegationDecision(BaseModel):
    """
    Structured output from the delegator's routing decision.

    WHY USE PYDANTIC:
    LLMs can generate arbitrary JSON. Pydantic ensures:
    1. Type safety (selected_agent must be valid)
    2. Required fields (can't forget reasoning)
    3. Validation (catch malformed outputs)
    4. Easy serialization

    This is CRITICAL for reliable multi-agent systems.
    """

    selected_agent: Literal["writing", "code", "data", "research", "FINISH"]
    """
    Which agent should handle the next step.

    Using Literal ensures only valid agent names can be assigned.
    "FINISH" means all work is complete.
    """

    reasoning: str = Field(..., min_length=10)
    """
    Why this agent was chosen (for debugging and learning).

    Must be at least 10 characters to ensure meaningful explanation.
    """

    instructions: str = Field(..., min_length=5)
    """
    Specific guidance for the selected agent.

    Examples:
    - "Generate a Python function for CSV parsing with error handling"
    - "Write a 3-paragraph technical summary"
    - "Search for recent information about topic X"
    """

    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    """
    Confidence in this routing decision (0.0 to 1.0).

    Could be used for:
    - Requiring human approval for low-confidence decisions
    - Logging/metrics
    - A/B testing different prompts
    """

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "selected_agent": "code",
                "reasoning": "User needs code generation with no research required",
                "instructions": "Generate Python function to parse CSV files",
                "confidence": 0.9
            }
        }


class Delegator:
    """
    Coordinator agent that routes requests to specialized agents.

    ARCHITECTURE:
    - LLM: Claude (via config) for intelligent routing decisions
    - Pattern: System prompt + context → structured routing decision
    - Output: Pydantic model for validation
    - Stateless: Each call is independent (decision based on current state)

    WHY THIS CLASS EXISTS:
    Encapsulates routing logic separate from workflow. Makes it easy to:
    1. Modify routing strategy without changing workflow
    2. Test routing decisions independently
    3. A/B test different prompts
    4. Track routing metrics

    Attributes:
        llm: Language model for routing decisions
        parser: JSON parser for structured output
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the delegator with an LLM.

        Args:
            model_name: Optional model override. If None, uses config default
                       or DELEGATOR_MODEL from environment
        """
        # Get model (delegator might use faster/cheaper model than specialized agents)
        self.llm = get_model(agent_name="delegator", model_name=model_name)

        # JSON parser for structured output
        self.parser = JsonOutputParser(pydantic_object=DelegationDecision)

        logger.info(f"Delegator initialized with model: {self.llm.model}")

    def _create_system_prompt(self) -> str:
        """
        Create the system prompt that defines the delegator's role.

        WHY THIS METHOD EXISTS:
        Separating prompt from logic allows:
        - Easy prompt iteration and testing
        - A/B testing different routing strategies
        - Context-specific prompt modifications

        Returns:
            System prompt string

        LEARNING POINT: Effective Delegation Prompts
        Good delegation prompts:
        - Clearly describe available agents and capabilities
        - Provide decision-making criteria
        - Request structured output
        - Include examples of routing decisions
        - Emphasize choosing the BEST agent, not just ANY valid agent
        """
        return """You are the Delegation Coordinator for a multi-agent AI system.

Your role is to analyze user requests and route them to the most appropriate specialized agent.

AVAILABLE AGENTS:

1. **Writing Agent**
   Capabilities: Content creation, summaries, articles, editing, formatting
   When to use: Requests involving written content, explanations, documentation
   Examples: "Write a summary", "Explain X", "Create documentation"

2. **Code Agent**
   Capabilities: Code generation, debugging, technical explanations
   When to use: Programming tasks, code examples, technical implementations
   Examples: "Generate Python code", "Write a function", "Debug this code"

3. **Data Analysis Agent**
   Capabilities: Statistical analysis, data processing, calculations, comparisons
   When to use: Numerical analysis, data transformation, metrics calculation
   Examples: "Analyze these numbers", "Calculate statistics", "Compare data"

4. **Research Agent**
   Capabilities: Web search, information gathering, fact-finding, synthesis
   When to use: Need current information, external data, research
   Examples: "Find information about", "Research topic X", "What are the latest"

DECISION CRITERIA:

1. **Match capabilities to requirements**: Choose the agent whose specialty best fits the task
2. **Consider context**: Look at what previous agents have done (if any)
3. **Single responsibility**: Each agent should focus on its specialty
4. **Finish when done**: If the request is fully satisfied, choose "FINISH"

MULTI-STEP WORKFLOWS:

If multiple agents are needed (e.g., "Research X and write a summary"):
- Choose agents sequentially (research first, then writing)
- The system will call you again after each agent completes
- Check state.collaboration_plan for the planned sequence

OUTPUT FORMAT:

Respond with ONLY valid JSON (no markdown, no extra text):

{
  "selected_agent": "writing" | "code" | "data" | "research" | "FINISH",
  "reasoning": "Detailed explanation of why this agent is best",
  "instructions": "Specific guidance for the selected agent",
  "confidence": 0.9
}

IMPORTANT:
- Be decisive - choose the ONE best agent for the NEXT step
- Provide clear reasoning (helps debugging and learning)
- Give specific instructions to the selected agent
- If all work is complete, select "FINISH"
"""

    def _create_user_message(self, state: AgentState) -> str:
        """
        Create the user message from current state.

        WHY THIS METHOD EXISTS:
        The delegator needs context to make good routing decisions:
        - What does the user want?
        - What work has been done?
        - What's planned next?

        Args:
            state: Current agent state

        Returns:
            User message with all relevant context
        """
        parts = []

        # User's original request
        parts.append(f"USER REQUEST:\n{state['user_request']}")

        # Work completed so far
        messages = state.get("messages", [])
        if messages:
            parts.append("\nWORK COMPLETED SO FAR:")
            for msg in messages[-5:]:  # Last 5 messages for context
                parts.append(f"  - {msg.get('role', 'unknown')}: {msg.get('content', '')}")

        # Agent outputs available
        outputs = []
        if state.get("research_results"):
            outputs.append("research")
        if state.get("analysis_results"):
            outputs.append("data analysis")
        if state.get("writing_output"):
            outputs.append("writing")
        if state.get("code_output"):
            outputs.append("code")

        if outputs:
            parts.append(f"\nAVAILABLE OUTPUTS: {', '.join(outputs)}")

        # Collaboration plan
        if state.get("collaboration_plan"):
            plan = state["collaboration_plan"]
            parts.append(f"\nCOLLABORATION PLAN: {' → '.join(plan)}")
            parts.append("(Choose the next agent in this plan if work remains)")

        # Iteration count (for context)
        iteration = state.get("iteration_count", 0)
        if iteration > 0:
            parts.append(f"\nITERATION: {iteration}")

        parts.append("\nDecide which agent should handle the NEXT step, or FINISH if complete.")

        return "\n".join(parts)

    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the delegator's routing decision.

        Args:
            state: Current agent state

        Returns:
            Dictionary of state updates with routing decision

        Raises:
            Exception: If LLM call fails or output is invalid
        """
        logger.info("Delegator analyzing request for routing...")

        # Build messages for LLM
        messages = [
            SystemMessage(content=self._create_system_prompt()),
            HumanMessage(content=self._create_user_message(state))
        ]

        # Call LLM
        logger.debug("Calling LLM for routing decision...")
        response = self.llm.invoke(messages)

        # Parse and validate output
        try:
            # Extract JSON from response (in case LLM added markdown)
            content = response.content

            # Try to find JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Parse JSON
            decision_dict = json.loads(content)

            # Validate with Pydantic
            decision = DelegationDecision(**decision_dict)

            logger.info(
                f"Delegator routed to: {decision.selected_agent} "
                f"(confidence: {decision.confidence:.2f})"
            )
            logger.debug(f"Reasoning: {decision.reasoning}")

        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to parse delegator output: {e}")
            logger.debug(f"Raw output: {response.content}")

            # Fallback: try to infer from content
            content_lower = response.content.lower()
            if any(word in content_lower for word in ["write", "summary", "explain"]):
                decision = DelegationDecision(
                    selected_agent="writing",
                    reasoning="Fallback: Detected writing-related keywords",
                    instructions="Handle the user's request",
                    confidence=0.5
                )
            elif any(word in content_lower for word in ["code", "function", "program"]):
                decision = DelegationDecision(
                    selected_agent="code",
                    reasoning="Fallback: Detected code-related keywords",
                    instructions="Handle the user's request",
                    confidence=0.5
                )
            else:
                # Default to FINISH if we can't parse
                decision = DelegationDecision(
                    selected_agent="FINISH",
                    reasoning="Fallback: Unable to parse routing decision",
                    instructions="N/A",
                    confidence=0.3
                )

            logger.warning(f"Using fallback routing: {decision.selected_agent}")

        # Return state updates
        return {
            "selected_agent": decision.selected_agent,
            "delegation_reasoning": decision.reasoning,
            "messages": [{
                "role": "delegator",
                "content": f"Routed to {decision.selected_agent}: {decision.reasoning}",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "confidence": decision.confidence,
                    "instructions": decision.instructions
                }
            }],
            "iteration_count": state.get("iteration_count", 0) + 1
        }

    def __call__(self, state: AgentState) -> AgentState:
        """
        Make the delegator callable as a LangGraph node.

        Args:
            state: Current agent state

        Returns:
            State updates with routing decision
        """
        try:
            logger.info("Delegator node invoked")

            # Check iteration limit
            from utils.config import MAX_ITERATIONS
            if state.get("iteration_count", 0) >= MAX_ITERATIONS:
                logger.warning(f"Reached max iterations ({MAX_ITERATIONS}), finishing")
                return {
                    "selected_agent": "FINISH",
                    "delegation_reasoning": f"Reached maximum iterations ({MAX_ITERATIONS})",
                    "messages": [{
                        "role": "delegator",
                        "content": f"Workflow limit reached ({MAX_ITERATIONS} iterations)",
                        "timestamp": datetime.now().isoformat()
                    }]
                }

            # Execute routing logic
            updates = self.execute(state)

            logger.info("Delegator completed successfully")
            return updates

        except Exception as e:
            logger.error(f"Delegator error: {str(e)}", exc_info=True)

            # On error, finish gracefully
            return {
                "selected_agent": "FINISH",
                "delegation_reasoning": f"Error in delegation: {str(e)}",
                "errors": [f"Delegator error: {str(e)}"],
                "messages": [{
                    "role": "delegator",
                    "content": f"Error occurred: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }]
            }


# ============================================================================
# CONVENIENCE FUNCTION FOR GRAPH
# ============================================================================

_delegator_instance = None


def get_delegator_node():
    """
    Get or create the global Delegator instance for use in LangGraph.

    Returns:
        Callable Delegator instance
    """
    global _delegator_instance

    if _delegator_instance is None:
        _delegator_instance = Delegator()
        logger.info("Created global Delegator instance")

    return _delegator_instance


# ============================================================================
# KEY CONCEPT: Meta-Agent Pattern
# ============================================================================
"""
╔════════════════════════════════════════════════════════════════════════╗
║ KEY CONCEPT: Meta-Agent (Agent that Manages Agents)                    ║
╠════════════════════════════════════════════════════════════════════════╣
║                                                                         ║
║ WHAT IS A META-AGENT?                                                  ║
║   An agent whose job is to coordinate other agents, not do work itself║
║                                                                         ║
║ OUR DELEGATOR:                                                         ║
║   ❌ Doesn't write content                                             ║
║   ❌ Doesn't generate code                                             ║
║   ❌ Doesn't do research                                               ║
║   ✅ Decides WHO should do the work                                    ║
║                                                                         ║
║ WHY THIS PATTERN?                                                      ║
║   1. Separation of concerns (routing vs executing)                     ║
║   2. Flexible - easy to add new agents without changing others         ║
║   3. Intelligent - uses LLM reasoning for routing decisions            ║
║   4. Debuggable - routing logic in one place                           ║
║                                                                         ║
║ ALTERNATIVES:                                                          ║
║   • Keyword matching: "if 'code' in request: use code_agent"           ║
║     - Brittle, misses nuance                                           ║
║   • User selection: Let user choose agent                              ║
║     - More work for user, breaks flow                                  ║
║   • Embed routing in workflow: Complex conditional logic               ║
║     - Hard to maintain, test, extend                                   ║
║                                                                         ║
║ REAL-WORLD EXAMPLES:                                                   ║
║   • AutoGPT's task planning agent                                      ║
║   • Customer service routing systems                                   ║
║   • Medical triage systems                                             ║
║   • Software architecture decision tools                               ║
║                                                                         ║
╚════════════════════════════════════════════════════════════════════════╝
"""


if __name__ == "__main__":
    # Test the delegator independently
    print("Testing Delegator...")

    from graph.state import create_initial_state

    try:
        # Create delegator
        delegator = Delegator()
        print(f"Created Delegator with model: {delegator.llm.model}")

        # Test cases
        test_cases = [
            "Write a summary of microservices architecture",
            "Generate Python code to sort a list",
            "Research the latest AI trends",
            "Analyze this data: [1, 2, 3, 4, 5]"
        ]

        for request in test_cases:
            print(f"\nTest: {request}")
            state = create_initial_state(request)
            result = delegator(state)

            print(f"  → Routed to: {result['selected_agent']}")
            print(f"  → Reasoning: {result['delegation_reasoning']}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
