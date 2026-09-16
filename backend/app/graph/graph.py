from langgraph.graph import StateGraph, START, END

from app.graph.state import CopilotState
from app.graph.nodes.router import router_node
from app.graph.nodes.extraction import extraction_node
from app.graph.nodes.merge import merge_node
from app.graph.nodes.completeness import completeness_node
from app.graph.nodes.duplicate import duplicate_node
from app.graph.nodes.risk_capa import risk_capa_node
from app.graph.nodes.compose_response import compose_response_node

def build_graph():
    """
    Builds and compiles the LangGraph workflow for the AIVOA Copilot.
    """
    builder = StateGraph(CopilotState)
    
    # Add nodes
    builder.add_node("router", router_node)
    builder.add_node("extraction", extraction_node)
    builder.add_node("merge", merge_node)
    builder.add_node("completeness", completeness_node)
    builder.add_node("duplicate", duplicate_node)
    builder.add_node("risk_capa", risk_capa_node)
    builder.add_node("compose_response", compose_response_node)
    
    # Wire the linear deterministic flow for Chunk 4
    builder.add_edge(START, "router")
    builder.add_edge("router", "extraction")
    builder.add_edge("extraction", "merge")
    builder.add_edge("merge", "completeness")
    builder.add_edge("completeness", "duplicate")
    builder.add_edge("duplicate", "risk_capa")
    builder.add_edge("risk_capa", "compose_response")
    builder.add_edge("compose_response", END)
    
    # Compile the graph
    graph = builder.compile()
    
    return graph

# Expose a pre-compiled graph for reuse
copilot_graph = build_graph()
