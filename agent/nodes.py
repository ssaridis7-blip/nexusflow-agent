"""
NexusFlow Agent — Graph Nodes
Each node is a step in the agent's reasoning loop.
"""

import json
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from agent.prompts import AGENT_SYSTEM_PROMPT, MONITOR_PROMPT, DECISION_PROMPT, REPORT_PROMPT
from agent.tools import (
    get_overdue_invoices,
    get_stale_deals,
    get_unengaged_leads,
    draft_followup_email,
    schedule_followup,
    flag_for_human_review,
    generate_weekly_report,
    search_knowledge_base,
)

ALL_TOOLS = [
    get_overdue_invoices,
    get_stale_deals,
    get_unengaged_leads,
    draft_followup_email,
    schedule_followup,
    flag_for_human_review,
    generate_weekly_report,
    search_knowledge_base,
]

TOOL_MAP = {tool.name: tool for tool in ALL_TOOLS}


def get_llm(with_tools: bool = True):
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    if with_tools:
        return llm.bind_tools(ALL_TOOLS)
    return llm


def execute_tool_calls(response):
    """
    Executes every tool call the LLM requested and returns
    a list of ToolMessage objects — which is what OpenAI requires
    before you can send another assistant message.
    """
    tool_messages = []
    tool_results = []

    if not hasattr(response, "tool_calls") or not response.tool_calls:
        return tool_messages, tool_results

    for tool_call in response.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_call_id = tool_call["id"]

        print(f"[AGENT] 🔧 Calling tool: {tool_name}({tool_args})")

        if tool_name in TOOL_MAP:
            result = TOOL_MAP[tool_name].invoke(tool_args)
        else:
            result = json.dumps({"error": f"Unknown tool: {tool_name}"})

        tool_messages.append(
            ToolMessage(content=result, tool_call_id=tool_call_id)
        )

        tool_results.append({
            "tool": tool_name,
            "args": tool_args,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

    return tool_messages, tool_results


def monitor_node(state: dict) -> dict:
    print("\n[AGENT] 🔍 Starting monitoring cycle...")

    llm = get_llm(with_tools=True)

    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPT),
        HumanMessage(content=MONITOR_PROMPT),
    ]

    response = llm.invoke(messages)
    tool_messages, tool_results = execute_tool_calls(response)

    all_messages = messages + [response] + tool_messages

    return {
        **state,
        "messages": all_messages,
        "monitoring_results": tool_results,
        "phase": "monitor_complete",
        "cycle_start": datetime.now().isoformat(),
    }


def decide_node(state: dict) -> dict:
    print("\n[AGENT] 🧠 Making decisions...")

    llm = get_llm(with_tools=True)

    messages = state.get("messages", []) + [
        HumanMessage(content=DECISION_PROMPT)
    ]

    response = llm.invoke(messages)
    tool_messages, actions_taken = execute_tool_calls(response)

    all_messages = messages + [response] + tool_messages

    return {
        **state,
        "messages": all_messages,
        "actions_taken": actions_taken,
        "decision_reasoning": response.content if response.content else "",
        "phase": "decide_complete",
    }


def report_node(state: dict) -> dict:
    print("\n[AGENT] 📋 Generating cycle report...")

    llm = get_llm(with_tools=False)

    context = f"""
Monitoring found:
{json.dumps(state.get('monitoring_results', []), indent=2)}

Actions taken:
{json.dumps(state.get('actions_taken', []), indent=2)}

Agent reasoning:
{state.get('decision_reasoning', 'No reasoning captured.')}

Cycle started: {state.get('cycle_start', 'unknown')}
Cycle ending: {datetime.now().isoformat()}
"""

    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPT),
        HumanMessage(content=REPORT_PROMPT + "\n\nCYCLE DATA:\n" + context)
    ]

    response = llm.invoke(messages)

    report = {
        "cycle_id": f"CYCLE-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "cycle_start": state.get("cycle_start"),
        "cycle_end": datetime.now().isoformat(),
        "monitoring_results": state.get("monitoring_results", []),
        "actions_taken": state.get("actions_taken", []),
        "summary": response.content,
        "phase": "complete"
    }

    print(f"\n{'='*60}")
    print("AGENT REPORT:")
    print('='*60)
    print(response.content)
    print('='*60)

    return {
        **state,
        "messages": messages + [response],
        "final_report": report,
        "phase": "complete",
    }