"""
Research Agent: Information Gathering and Web Search Specialist

Searches for information, synthesizes findings, and provides sourced results.
Demonstrates tool-augmented agent pattern (LLM + external APIs).
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from utils.config import get_model, get_config
from graph.state import AgentState

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Research agent for information gathering and web search."""

    def __init__(self, model_name: str = None):
        self.llm = get_model(agent_name="research", model_name=model_name)
        self.search_tool = self._setup_search_tool()
        logger.info(f"ResearchAgent initialized with model: {self.llm.model}")

    def _setup_search_tool(self) -> Optional[Any]:
        """Setup web search tool (Tavily or DuckDuckGo)."""
        try:
            # Try Tavily first (better for production)
            tavily_key = get_config("TAVILY_API_KEY")
            if tavily_key:
                from tavily import TavilyClient
                logger.info("Using Tavily for web search")
                return TavilyClient(api_key=tavily_key)
        except:
            logger.warning("Tavily not available")

        try:
            # Fallback to DuckDuckGo (free, no API key)
            from duckduckgo_search import DDGS
            logger.info("Using DuckDuckGo for web search")
            return DDGS()
        except:
            logger.warning("DuckDuckGo not available")

        logger.warning("No search tool available - research agent will use LLM knowledge only")
        return None

    def _search_web(self, query: str, max_results: int = 5) -> list:
        """Perform web search using available tool."""
        if not self.search_tool:
            return [{
                "title": "Search unavailable",
                "snippet": "Web search tools not configured. Using LLM knowledge only.",
                "url": ""
            }]

        try:
            # Try Tavily
            if hasattr(self.search_tool, 'search'):
                results = self.search_tool.search(query, max_results=max_results)
                return [
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("content", ""),
                        "url": r.get("url", "")
                    }
                    for r in results.get("results", [])
                ]
        except:
            pass

        try:
            # Try DuckDuckGo
            if hasattr(self.search_tool, 'text'):
                results = list(self.search_tool.text(query, max_results=max_results))
                return [
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("link", "")
                    }
                    for r in results
                ]
        except:
            pass

        return [{"title": "Search failed", "snippet": "Could not retrieve results", "url": ""}]

    def _create_system_prompt(self) -> str:
        return """You are a specialized Research Agent in a multi-agent AI system.

Your role: Information gathering, web search, fact-finding, and synthesis

Your capabilities:
- Search the web for current information
- Synthesize findings from multiple sources
- Fact-check and verify information
- Provide sourced, reliable information
- Identify knowledge gaps

Your guidelines:
1. Cite sources when available
2. Distinguish between facts and opinions
3. Note information currency (how recent)
4. Highlight conflicting information if found
5. Be transparent about limitations

Output format (JSON):
{
  "query": "What was searched",
  "findings": "Comprehensive summary of findings",
  "sources": ["URL1", "URL2"],
  "confidence": 0.8,
  "limitations": ["Any caveats"],
  "last_updated": "Recency of information"
}

Provide accurate, well-sourced information."""

    def execute(self, state: AgentState) -> Dict[str, Any]:
        """Execute research task."""
        user_request = state["user_request"]
        logger.info(f"ResearchAgent researching: {user_request[:100]}...")

        # Perform web search if available
        search_results = []
        if self.search_tool:
            try:
                search_results = self._search_web(user_request)
                logger.info(f"Found {len(search_results)} search results")
            except Exception as e:
                logger.error(f"Search error: {e}")

        # Build context for LLM
        context = f"Task: {user_request}\n\n"

        if search_results and search_results[0].get("title") != "Search unavailable":
            context += "Web search results:\n"
            for i, result in enumerate(search_results[:5], 1):
                context += f"{i}. {result['title']}\n   {result['snippet']}\n   Source: {result['url']}\n\n"
            context += "Synthesize these findings into a comprehensive response."
        else:
            context += "Web search unavailable. Use your knowledge to provide the best possible answer, noting any limitations."

        messages = [
            SystemMessage(content=self._create_system_prompt()),
            HumanMessage(content=context)
        ]

        response = self.llm.invoke(messages)
        content = response.content

        # Parse response
        import json
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                research_results = json.loads(json_str)
            elif "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                research_results = json.loads(content[start:end])
            else:
                research_results = {
                    "query": user_request,
                    "findings": content,
                    "sources": [r["url"] for r in search_results if r.get("url")],
                    "confidence": 0.7 if search_results else 0.5
                }
        except:
            research_results = {
                "query": user_request,
                "findings": content,
                "sources": [r["url"] for r in search_results if r.get("url")],
                "confidence": 0.7
            }

        logger.info("ResearchAgent completed research")

        return {
            "research_results": research_results,
            "messages": [{
                "role": "research",
                "content": f"Completed research on: {user_request[:50]}...",
                "timestamp": datetime.now().isoformat()
            }],
            "next_action": "continue"
        }

    def __call__(self, state: AgentState) -> AgentState:
        try:
            return self.execute(state)
        except Exception as e:
            logger.error(f"ResearchAgent error: {e}", exc_info=True)
            return {
                "errors": [f"ResearchAgent error: {str(e)}"],
                "next_action": "finish"
            }


_research_agent_instance = None


def get_research_agent_node():
    global _research_agent_instance
    if _research_agent_instance is None:
        _research_agent_instance = ResearchAgent()
    return _research_agent_instance
