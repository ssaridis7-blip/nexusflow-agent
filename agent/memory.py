"""
NexusFlow Agent — Memory & Checkpointer
Allows the agent to remember decisions across runs using LangGraph's built-in checkpointing.

Phase 1: In-memory checkpointer (resets on restart — fine for development)
Phase 3+: Switch to SqliteSaver for persistent memory across restarts
"""

from langgraph.checkpoint.memory import MemorySaver


def get_memory() -> MemorySaver:
    """
    Returns the checkpointer for the agent graph.
    
    MemorySaver stores state in RAM — great for development and testing.
    
    To upgrade to persistent memory (Phase 3):
    
        from langgraph.checkpoint.sqlite import SqliteSaver
        memory = SqliteSaver.from_conn_string("logs/agent_memory.db")
    
    The graph is compiled with memory like this:
    
        graph.compile(checkpointer=get_memory())
    
    Then each invocation needs a thread_id so LangGraph knows which
    conversation thread to resume:
    
        graph.invoke(state, config={"configurable": {"thread_id": "cycle-001"}})
    """
    return MemorySaver()


# Thread ID helpers — each agent cycle gets a unique thread
def get_cycle_thread_id(cycle_number: int = 1) -> dict:
    """Returns the LangGraph config dict for a given cycle."""
    return {"configurable": {"thread_id": f"nexusflow-cycle-{cycle_number:04d}"}}