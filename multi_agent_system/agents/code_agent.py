"""
Code Agent: Code Generation and Technical Explanation Specialist

Generates code, explains technical concepts, and provides debugging guidance.
Demonstrates multi-step reasoning pattern for technical tasks.
"""

import logging
from datetime import datetime
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from utils.config import get_model
from graph.state import AgentState

logger = logging.getLogger(__name__)


class CodeAgent:
    """Code generation agent for programming tasks."""

    def __init__(self, model_name: str = None):
        self.llm = get_model(agent_name="code", model_name=model_name)
        self.parser = StrOutputParser()
        logger.info(f"CodeAgent initialized with model: {self.llm.model}")

    def _create_system_prompt(self) -> str:
        return """You are a specialized Code Agent in a multi-agent AI system.

Your role: Code generation, technical explanations, and debugging guidance

Your capabilities:
- Generate clean, well-documented code in multiple languages
- Explain technical concepts clearly
- Provide debugging suggestions
- Include error handling and edge cases
- Write production-quality code

Your guidelines:
1. Always include docstrings and comments
2. Follow language-specific best practices and conventions
3. Consider edge cases and error handling
4. Provide usage examples when appropriate
5. Explain WHY choices were made, not just WHAT the code does

Output format:
Structure your response as a JSON object with:
{
  "code": "The actual code",
  "language": "python|javascript|etc",
  "explanation": "What the code does and why",
  "usage_example": "How to use it",
  "dependencies": ["list", "of", "required", "libraries"]
}

If the request isn't code-related, provide a brief explanation and suggest asking the delegator to route to a different agent."""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse code agent response into structured format."""
        import json

        try:
            # Try to extract JSON if present
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "{" in response and "}" in response:
                # Try to find JSON object
                start = response.find("{")
                end = response.rfind("}") + 1
                return json.loads(response[start:end])
        except:
            pass

        # Fallback: extract code blocks and create structure
        code = ""
        if "```" in response:
            parts = response.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:  # Odd indices are code blocks
                    # Remove language identifier if present
                    lines = part.strip().split("\n")
                    if lines[0] in ["python", "javascript", "java", "cpp", "c", "go", "rust"]:
                        code = "\n".join(lines[1:])
                    else:
                        code = part.strip()
                    break

        return {
            "code": code if code else response,
            "language": "python",  # default
            "explanation": "See above for details",
            "usage_example": "See code comments",
            "dependencies": []
        }

    def execute(self, state: AgentState) -> Dict[str, Any]:
        """Execute code generation task."""
        user_request = state["user_request"]
        logger.info(f"CodeAgent executing for: {user_request[:100]}...")

        messages = [
            SystemMessage(content=self._create_system_prompt()),
            HumanMessage(content=f"Task: {user_request}")
        ]

        response = self.llm.invoke(messages)
        content = self.parser.invoke(response)

        # Parse into structured format
        code_output = self._parse_response(content)

        logger.info(f"CodeAgent generated {len(code_output['code'])} chars of code")

        return {
            "code_output": code_output,
            "messages": [{
                "role": "code",
                "content": f"Generated {code_output['language']} code",
                "timestamp": datetime.now().isoformat()
            }],
            "next_action": "continue"
        }

    def __call__(self, state: AgentState) -> AgentState:
        try:
            return self.execute(state)
        except Exception as e:
            logger.error(f"CodeAgent error: {e}", exc_info=True)
            return {
                "errors": [f"CodeAgent error: {str(e)}"],
                "next_action": "finish"
            }


_code_agent_instance = None


def get_code_agent_node():
    global _code_agent_instance
    if _code_agent_instance is None:
        _code_agent_instance = CodeAgent()
    return _code_agent_instance
