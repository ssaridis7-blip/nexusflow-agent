"""
NexusFlow Agent — LangGraph Graph Definition
The heart of the agent: defines the state, nodes, and edges.
"""

from typing import TypedDict, Annotated, Any
from langgraph.graph import StateGraph, END
import operator

from agent.nodes import monitor_node, decide_node, report_node


# ─────────────────────────────────────────────
# STATE DEFINITION
# ─────────────────────────────────────────────

class AgentState(TypedDict):
    """
    The full state that flows through the agent graph.
    Every node can read from and write to this state.
    
    Using Annotated[list, operator.add] for messages so that
    each node appends to the list rather than replacing it.
    """
    messages: Annotated[list, operator.add]   # Full conversation history
    phase: str                                 # Current agent phase
    cycle_start: str                           # ISO timestamp when cycle began
    monitoring_results: list                   # Raw results from monitoring tools
    actions_taken: list                        # Actions the agent took
    decision_reasoning: str                    # Agent's plain-English reasoning
    final_report: dict                         # Complete cycle summary


# ─────────────────────────────────────────────
# GRAPH CONSTRUCTION
# ─────────────────────────────────────────────

def build_agent_graph() -> StateGraph:
    """
    Builds and compiles the NexusFlow LangGraph agent.
    
    Flow:
        START → monitor → decide → report → END
    
    Phase 1: Linear flow (monitor → decide → report)
    Phase 5+: Add conditional edges (e.g. skip decide if nothing found,
              loop back if more monitoring is needed)
    """
    
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("monitor", monitor_node)
    graph.add_node("decide", decide_node)
    graph.add_node("report", report_node)
    
    # Set entry point
    graph.set_entry_point("monitor")
    
    # Add edges (Phase 1: linear)
    graph.add_edge("monitor", "decide")
    graph.add_edge("decide", "report")
    graph.add_edge("report", END)
    
    # Compile the graph
    compiled = graph.compile()
    
    return compiled


# ─────────────────────────────────────────────
# INITIAL STATE FACTORY
# ─────────────────────────────────────────────

def get_initial_state() -> AgentState:
    """Returns a clean initial state for a new agent cycle."""
    return AgentState(
        messages=[],
        phase="start",
        cycle_start="",
        monitoring_results=[],
        actions_taken=[],
        decision_reasoning="",
        final_report={}
    )


# ─────────────────────────────────────────────
# CONVENIENCE RUNNER
# ─────────────────────────────────────────────

def run_agent_cycle() -> dict:
    """
    Run one full agent cycle: monitor → decide → report.
    Returns the final state including the report.
    
    Called by:
    - scheduler/runner.py (automated hourly runs)
    - main.py (manual test runs)
    """
    graph = build_agent_graph()
    initial_state = get_initial_state()
    
    final_state = graph.invoke(initial_state)
    return final_state