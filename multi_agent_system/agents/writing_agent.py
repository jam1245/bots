"""
Writing Agent: Content Creation Specialist

WHAT THIS AGENT DOES:
Generates written content including summaries, articles, creative writing,
editing, and formatting. This is the simplest agent in the system - it takes
a request and uses an LLM to produce text.

WHY THIS AGENT EXISTS:
Many user requests involve content creation without requiring external tools
or complex computation. The writing agent handles these cases efficiently.

KEY LEARNING CONCEPTS:
- Single-purpose agent design (does one thing well)
- Role-based prompting (giving the LLM a specialized role)
- Structured output from LLMs
- Error handling in agent execution

WHEN TO USE THIS AGENT:
- "Write a summary of..."
- "Create an article about..."
- "Edit this text..."
- "Format this content as..."
- "Explain X in simple terms..."

PATTERN DEMONSTRATED:
This is a "Generative Agent" - uses LLM's generative capabilities without
external tools. Simplest agent pattern, perfect for learning.

Example:
    from agents.writing_agent import WritingAgent
    from graph.state import create_initial_state

    agent = WritingAgent()
    state = create_initial_state("Write a haiku about coding")
    result = agent(state)
    print(result["writing_output"])
"""

import logging
from datetime import datetime
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser

# Import from our modules
from utils.config import get_model
from graph.state import AgentState

# Set up logging
logger = logging.getLogger(__name__)


class WritingAgent:
    """
    Content creation agent for summaries, articles, editing, and formatting.

    ARCHITECTURE:
    - LLM: Claude (via config)
    - Pattern: System prompt + user request → text output
    - No external tools needed
    - Focuses on quality written content

    WHY THIS CLASS EXISTS:
    Encapsulates all writing-related logic in one place. Makes it easy to:
    1. Modify prompts without touching workflow code
    2. Test the agent independently
    3. Track writing-specific metrics
    4. Swap out LLM models if needed

    Attributes:
        llm: The language model instance (ChatAnthropic)
        parser: Converts LLM output to string
    """

    def __init__(self, model_name: str = None):
        """
        Initialize the writing agent with an LLM.

        Args:
            model_name: Optional model override. If None, uses config default
                       or WRITING_AGENT_MODEL from environment

        Example:
            >>> agent = WritingAgent()  # Uses default/config model
            >>> agent = WritingAgent("claude-opus-4-5-20251101")  # Specific model
        """
        # Get model from config (supports agent-specific model override)
        self.llm = get_model(agent_name="writing", model_name=model_name)

        # String parser for LLM output
        self.parser = StrOutputParser()

        logger.info(f"WritingAgent initialized with model: {self.llm.model}")

    def _create_system_prompt(self) -> str:
        """
        Create the system prompt that defines the agent's role and behavior.

        WHY THIS METHOD EXISTS:
        Separating prompt creation from execution:
        1. Makes prompts easy to modify and test
        2. Allows dynamic prompt generation (e.g., based on state)
        3. Keeps execution logic clean

        Returns:
            System prompt string

        LEARNING POINT: Effective System Prompts
        Good system prompts:
        - Define the role clearly ("You are a...")
        - Specify capabilities and limitations
        - Set tone and style expectations
        - Provide output format guidelines
        """
        return """You are a specialized Writing Agent in a multi-agent AI system.

Your role: Content creation, summarization, editing, and formatting

Your capabilities:
- Write clear, engaging summaries
- Create well-structured articles and documents
- Edit and improve existing text
- Format content for readability
- Explain complex topics in simple terms
- Adapt writing style to audience needs

Your guidelines:
1. Be concise but complete - don't omit important information
2. Use clear, accessible language unless technical terminology is needed
3. Structure content logically with appropriate headings/sections
4. Proofread for grammar, clarity, and flow
5. If the request is ambiguous, make reasonable assumptions and note them

Output format:
- Provide the written content directly
- If you make assumptions, note them at the end
- Use markdown formatting when appropriate (headers, lists, etc.)

Remember: You're part of a multi-agent system. Focus on your specialty
(writing) and do it exceptionally well. Other agents handle research, coding,
and data analysis."""

    def _create_user_message(self, state: AgentState) -> str:
        """
        Create the user message from the current state.

        WHY THIS METHOD EXISTS:
        Allows context from previous agents to inform writing. For example,
        if research agent ran first, we can include its findings.

        Args:
            state: Current agent state

        Returns:
            User message string incorporating context

        LEARNING POINT: Context-Aware Prompts
        Better than just passing user_request:
        - Includes results from previous agents
        - Provides relevant background
        - Enables multi-agent collaboration
        """
        user_request = state["user_request"]

        # Start with base request
        message_parts = [f"Task: {user_request}"]

        # Add context from other agents if available
        context_added = False

        if state.get("research_results"):
            context_added = True
            message_parts.append(
                f"\nContext from Research Agent:\n{state['research_results']}"
            )

        if state.get("analysis_results"):
            context_added = True
            message_parts.append(
                f"\nContext from Data Analysis Agent:\n{state['analysis_results']}"
            )

        if state.get("code_output"):
            context_added = True
            code_info = state["code_output"]
            message_parts.append(
                f"\nContext from Code Agent:\n"
                f"Language: {code_info.get('language', 'Unknown')}\n"
                f"Code: {code_info.get('code', '')}"
            )

        if context_added:
            message_parts.append(
                "\nPlease incorporate the above context into your written output."
            )

        return "\n".join(message_parts)

    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the writing agent's task.

        This is the core logic: take state, generate content, return updates.

        Args:
            state: Current agent state with user_request and optional context

        Returns:
            Dictionary of state updates:
            - writing_output: The generated content
            - messages: Log of what this agent did
            - next_action: Signal to continue or finish

        Raises:
            Exception: If LLM call fails (caught by __call__ wrapper)

        LEARNING POINT: State Update Pattern
        Return only the fields you want to update - LangGraph merges them.
        Don't return the full state, just your changes.
        """
        user_request = state["user_request"]
        logger.info(f"WritingAgent executing for request: {user_request[:100]}...")

        # Build messages for LLM
        messages = [
            SystemMessage(content=self._create_system_prompt()),
            HumanMessage(content=self._create_user_message(state))
        ]

        # Call LLM
        logger.debug("Calling LLM for content generation...")
        response = self.llm.invoke(messages)

        # Parse output
        content = self.parser.invoke(response)

        logger.info(f"WritingAgent produced {len(content)} characters of content")

        # Return state updates
        return {
            "writing_output": content,
            "messages": [{
                "role": "writing",
                "content": f"Generated written content ({len(content)} chars)",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "model": self.llm.model,
                    "temperature": self.llm.temperature
                }
            }],
            "next_action": "continue"  # Let synthesis decide if we're done
        }

    def __call__(self, state: AgentState) -> AgentState:
        """
        Make the agent callable as a LangGraph node.

        WHY THIS METHOD EXISTS:
        LangGraph nodes are functions that take state and return state updates.
        This __call__ method makes our class instance act like a function,
        adding error handling and logging around the core execute() logic.

        Args:
            state: Current agent state

        Returns:
            State updates (merged by LangGraph)

        PATTERN: Callable Classes as Nodes
        Instead of:
            def writing_agent_node(state): ...

        We use:
            agent = WritingAgent()
            # agent is now callable: agent(state)

        Benefits:
        - Encapsulation (state in __init__)
        - Easier testing (mock the class)
        - Consistent error handling
        - Reusability
        """
        try:
            logger.info("WritingAgent node invoked")

            # Execute the agent's core logic
            updates = self.execute(state)

            logger.info("WritingAgent completed successfully")
            return updates

        except Exception as e:
            # Graceful error handling
            logger.error(f"WritingAgent error: {str(e)}", exc_info=True)

            # Return error state instead of crashing
            return {
                "errors": [f"WritingAgent error: {str(e)}"],
                "messages": [{
                    "role": "writing",
                    "content": f"Error occurred: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }],
                "next_action": "finish"  # Stop workflow on error
            }


# ============================================================================
# CONVENIENCE FUNCTION FOR GRAPH
# ============================================================================

# Global instance for use in graph (created once, reused many times)
_writing_agent_instance = None


def get_writing_agent_node():
    """
    Get or create the global WritingAgent instance for use in LangGraph.

    WHY THIS FUNCTION EXISTS:
    LangGraph nodes should be stateless functions or callable objects.
    This pattern creates a singleton agent instance that's reused across
    graph invocations, avoiding repeated initialization overhead.

    Returns:
        Callable WritingAgent instance

    Example:
        from langgraph.graph import StateGraph
        from agents.writing_agent import get_writing_agent_node

        workflow = StateGraph(AgentState)
        workflow.add_node("writing", get_writing_agent_node())
    """
    global _writing_agent_instance

    if _writing_agent_instance is None:
        _writing_agent_instance = WritingAgent()
        logger.info("Created global WritingAgent instance")

    return _writing_agent_instance


# ============================================================================
# KEY CONCEPT: Agent Design Patterns
# ============================================================================
"""
╔════════════════════════════════════════════════════════════════════════╗
║ KEY CONCEPT: Single-Purpose Agent Pattern                              ║
╠════════════════════════════════════════════════════════════════════════╣
║                                                                         ║
║ PRINCIPLE: Each agent should do ONE thing exceptionally well           ║
║                                                                         ║
║ Writing Agent:                                                         ║
║   ✅ Content creation (its specialty)                                  ║
║   ❌ Web research (delegate to research agent)                         ║
║   ❌ Data analysis (delegate to data agent)                            ║
║   ❌ Code generation (delegate to code agent)                          ║
║                                                                         ║
║ WHY THIS MATTERS:                                                      ║
║   1. Clearer prompts → better outputs                                  ║
║   2. Easier to test and debug                                          ║
║   3. Can use different models per agent (cheap for simple, powerful    ║
║      for complex)                                                       ║
║   4. Parallel execution opportunities                                  ║
║   5. Easier to add/remove agents                                       ║
║                                                                         ║
║ ANTI-PATTERN: "God Agent" that does everything                         ║
║   • Unclear prompts                                                    ║
║   • Inconsistent behavior                                              ║
║   • Hard to optimize                                                   ║
║   • Difficult to debug                                                 ║
║                                                                         ║
║ REAL-WORLD ANALOGY:                                                    ║
║   Writing Agent = Professional writer                                  ║
║   Don't ask them to also be a researcher, programmer, and statistician ║
║   Let them focus on writing well!                                      ║
║                                                                         ║
╚════════════════════════════════════════════════════════════════════════╝
"""


if __name__ == "__main__":
    # Test the writing agent independently
    print("Testing WritingAgent...")

    from graph.state import create_initial_state

    try:
        # Create agent
        agent = WritingAgent()
        print(f"Created WritingAgent with model: {agent.llm.model}")

        # Create test state
        state = create_initial_state(
            "Write a 2-paragraph summary of the benefits of microservices architecture"
        )

        # Execute agent
        print("\nExecuting agent...")
        result = agent(state)

        # Show results
        if "writing_output" in result:
            print("\n✅ Writing Agent Output:")
            print("=" * 80)
            print(result["writing_output"])
            print("=" * 80)
        else:
            print(f"\n❌ No output generated")

        if result.get("errors"):
            print(f"\n⚠️ Errors: {result['errors']}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
