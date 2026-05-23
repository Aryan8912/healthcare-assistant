"""
graph/workflow.py — LangGraph multi-agent workflow with multilingual support.
"""
import asyncio
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from backend.agents.router_agent import route
from backend.agents import appointment_agent, rag_agent, summary_agent, document_agent
from backend.agents.general_response import get_general_response
from backend.modules.memory_manager import memory_manager


# ── State ─────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    message:    str
    session_id: Optional[str]
    intent:     Optional[str]
    response:   Optional[str]
    agent_used: Optional[str]
    tool_calls: list
    file_id:    Optional[str]


# ── Nodes ─────────────────────────────────────────────────────────────────────

async def router_node(state: AgentState) -> AgentState:
    result = await route(state["message"])
    return {**state, "intent": result["intent"]}


async def appointment_node(state: AgentState) -> AgentState:
    result = await appointment_agent.run(
        message    = state["message"],
        session_id = state.get("session_id"),
    )
    return {**state, "response": result["response"], "agent_used": "appointment_agent", "tool_calls": result["tool_calls"]}


async def rag_node(state: AgentState) -> AgentState:
    result = await rag_agent.run(
        message    = state["message"],
        session_id = state.get("session_id"),
    )
    return {**state, "response": result["response"], "agent_used": "rag_agent", "tool_calls": result["tool_calls"]}


async def summary_node(state: AgentState) -> AgentState:
    result = await summary_agent.run(
        message    = state["message"],
        session_id = state.get("session_id"),
    )
    return {**state, "response": result["response"], "agent_used": "summary_agent", "tool_calls": result["tool_calls"]}


async def document_node(state: AgentState) -> AgentState:
    result = await document_agent.run(
        message    = state["message"],
        session_id = state.get("session_id"),
        file_id    = state.get("file_id"),
    )
    return {**state, "response": result["response"], "agent_used": "document_agent", "tool_calls": result["tool_calls"]}


async def general_node(state: AgentState) -> AgentState:
    """Handle general queries with multilingual support."""
    response = await get_general_response(state["message"])
    return {**state, "response": response, "agent_used": "general", "tool_calls": []}


# ── Router ────────────────────────────────────────────────────────────────────

def route_intent(state: AgentState) -> str:
    intent = state.get("intent", "general")
    routes = {
        "appointment": "appointment_node",
        "rag":         "rag_node",
        "summary":     "summary_node",
        "document":    "document_node",
        "general":     "general_node",
    }
    return routes.get(intent, "general_node")


# ── Build Graph ───────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("router_node",      router_node)
    graph.add_node("appointment_node", appointment_node)
    graph.add_node("rag_node",         rag_node)
    graph.add_node("summary_node",     summary_node)
    graph.add_node("document_node",    document_node)
    graph.add_node("general_node",     general_node)

    graph.set_entry_point("router_node")

    graph.add_conditional_edges(
        "router_node",
        route_intent,
        {
            "appointment_node": "appointment_node",
            "rag_node":         "rag_node",
            "summary_node":     "summary_node",
            "document_node":    "document_node",
            "general_node":     "general_node",
        }
    )

    graph.add_edge("appointment_node", END)
    graph.add_edge("rag_node",         END)
    graph.add_edge("summary_node",     END)
    graph.add_edge("document_node",    END)
    graph.add_edge("general_node",     END)

    return graph.compile()


workflow = build_graph()


# ── Main Run Function ─────────────────────────────────────────────────────────

async def run_workflow(
    message:    str,
    session_id: Optional[str] = None,
    file_id:    Optional[str] = None,
) -> dict:
    if session_id:
        await memory_manager.save_message(session_id, "user", message)

    initial_state = AgentState(
        message    = message,
        session_id = session_id,
        intent     = None,
        response   = None,
        agent_used = None,
        tool_calls = [],
        file_id    = file_id,
    )

    result = await workflow.ainvoke(initial_state)

    if session_id and result.get("response"):
        await memory_manager.save_message(
            session_id = session_id,
            role       = "assistant",
            content    = result["response"],
            agent_used = result.get("agent_used"),
        )

    return {
        "response":   result.get("response", ""),
        "agent_used": result.get("agent_used", "general"),
        "tool_calls": result.get("tool_calls", []),
        "intent":     result.get("intent", "general"),
    }