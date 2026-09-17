"""
AIVOA — LangGraph Workflow Wiring

Builds and compiles the AIVOA Copilot StateGraph.

The graph is compiled once and reused across requests (§5.6: "Graph
compiled once at startup, reused per request").

build_graph() accepts an optional LLM provider for extraction. In
production, this is a GroqLLMProvider; in tests, a FakeLLMProvider.
"""

from __future__ import annotations

from typing import Optional

from langgraph.graph import END, START, StateGraph

from app.graph.nodes.completeness import completeness_node
from app.graph.nodes.compose_response import compose_response_node
from app.graph.nodes.duplicate import duplicate_node
from app.graph.nodes.extraction import make_extraction_node
from app.graph.nodes.merge import merge_node
from app.graph.nodes.risk_capa import risk_capa_node
from app.graph.nodes.router import router_node
from app.graph.state import CopilotState
from app.llm.base import LLMProvider


def build_graph(
    llm_provider: Optional[LLMProvider] = None,
    extraction_model: str = "",
):
    """
    Build and compile the AIVOA Copilot workflow graph.

    Args:
        llm_provider: LLM provider for extraction. If None, uses a
            minimal fallback that returns empty extraction (useful for
            structural tests that don't need extraction behavior).
        extraction_model: Model identifier for extraction calls.

    Returns:
        Compiled LangGraph StateGraph.
    """
    # Create the extraction node — bound to the provider
    if llm_provider is not None:
        extraction = make_extraction_node(llm_provider, extraction_model)
    else:
        # Fallback for backward compatibility / structural tests:
        # return empty extraction so the rest of the graph still runs.
        def extraction(state: CopilotState) -> dict:
            return {"extracted_fields": {}}

    builder = StateGraph(CopilotState)

    # Add nodes
    builder.add_node("router", router_node)
    builder.add_node("extraction", extraction)
    builder.add_node("merge", merge_node)
    builder.add_node("completeness", completeness_node)
    builder.add_node("duplicate", duplicate_node)
    builder.add_node("risk_capa", risk_capa_node)
    builder.add_node("compose_response", compose_response_node)

    # Wire the linear flow
    builder.add_edge(START, "router")
    builder.add_edge("router", "extraction")
    builder.add_edge("extraction", "merge")
    builder.add_edge("merge", "completeness")
    builder.add_edge("completeness", "duplicate")
    builder.add_edge("duplicate", "risk_capa")
    builder.add_edge("risk_capa", "compose_response")
    builder.add_edge("compose_response", END)

    return builder.compile()


def build_production_graph():
    """
    Build the production graph with real Groq provider.

    Reads configuration from settings. Fails clearly if GROQ_API_KEY
    is not set.
    """
    from app.core.config import settings
    from app.llm.groq_provider import GroqLLMProvider

    provider = GroqLLMProvider(api_key=settings.GROQ_API_KEY)
    return build_graph(
        llm_provider=provider,
        extraction_model=settings.EXTRACTION_MODEL,
    )


# Pre-compiled graph for import convenience.
# Uses no-provider fallback so existing imports don't break when
# GROQ_API_KEY is not set (e.g., during test collection).
# Production code should call build_production_graph() instead.
copilot_graph = build_graph()
