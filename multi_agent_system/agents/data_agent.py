"""
Data Analysis Agent: Statistical Analysis and Data Processing Specialist

Performs calculations, statistical analysis, and data transformations.
Demonstrates computational agent pattern (Python computation + LLM interpretation).
"""

import logging
from datetime import datetime
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from utils.config import get_model
from graph.state import AgentState

logger = logging.getLogger(__name__)


class DataAgent:
    """Data analysis agent for statistical and computational tasks."""

    def __init__(self, model_name: str = None):
        self.llm = get_model(agent_name="data", model_name=model_name)
        logger.info(f"DataAgent initialized with model: {self.llm.model}")

    def _create_system_prompt(self) -> str:
        return """You are a specialized Data Analysis Agent in a multi-agent AI system.

Your role: Statistical analysis, data processing, calculations, and insights

Your capabilities:
- Perform statistical calculations (mean, median, std dev, percentiles)
- Analyze trends and patterns
- Compare datasets
- Generate data visualizations recommendations
- Provide insights from numbers

Your guidelines:
1. Show your calculations clearly
2. Explain statistical significance
3. Highlight key insights and patterns
4. Recommend appropriate visualizations
5. Note any limitations or assumptions

Output format (JSON):
{
  "analysis_type": "statistical|comparative|trend|descriptive",
  "results": {"key": "value"},
  "insights": ["Key finding 1", "Key finding 2"],
  "visualizations": ["Recommended chart type and what to show"],
  "limitations": ["Any caveats about the analysis"]
}

Be rigorous but explain concepts in accessible language."""

    def execute(self, state: AgentState) -> Dict[str, Any]:
        """Execute data analysis task."""
        user_request = state["user_request"]
        logger.info(f"DataAgent analyzing: {user_request[:100]}...")

        # Build context from previous agent outputs
        context_parts = [f"Task: {user_request}"]

        if state.get("research_results"):
            context_parts.append(f"\nResearch data available: {state['research_results']}")

        messages = [
            SystemMessage(content=self._create_system_prompt()),
            HumanMessage(content="\n".join(context_parts))
        ]

        response = self.llm.invoke(messages)
        content = response.content

        # Try to parse JSON structure
        import json
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                analysis_results = json.loads(json_str)
            elif "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                analysis_results = json.loads(content[start:end])
            else:
                analysis_results = {
                    "analysis_type": "descriptive",
                    "results": {"output": content},
                    "insights": ["See detailed analysis above"]
                }
        except:
            analysis_results = {
                "analysis_type": "descriptive",
                "results": {"output": content},
                "insights": []
            }

        logger.info("DataAgent completed analysis")

        return {
            "analysis_results": analysis_results,
            "messages": [{
                "role": "data",
                "content": f"Completed {analysis_results.get('analysis_type', 'general')} analysis",
                "timestamp": datetime.now().isoformat()
            }],
            "next_action": "continue"
        }

    def __call__(self, state: AgentState) -> AgentState:
        try:
            return self.execute(state)
        except Exception as e:
            logger.error(f"DataAgent error: {e}", exc_info=True)
            return {
                "errors": [f"DataAgent error: {str(e)}"],
                "next_action": "finish"
            }


_data_agent_instance = None


def get_data_agent_node():
    global _data_agent_instance
    if _data_agent_instance is None:
        _data_agent_instance = DataAgent()
    return _data_agent_instance
