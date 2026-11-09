"""Task 1. Memory that survives a restart: SqliteSaver instead of InMemorySaver.

Based on demos/03_memory_and_hitl.py. Every run is a new process; the conversation
lives in memory.db, keyed by thread_id.

Run:
  python homework/task1.py "My name is Alex"
  python homework/task1.py "What's my name?"                 # → Alex
  python homework/task1.py "What's my name?" --thread 2      # new thread → doesn't know
  rm homework/memory.db && python homework/task1.py "What's my name?"   # forgot again
"""
import argparse
import os
import sqlite3
import sys
from typing import Annotated, Literal, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt

from common import get_llm

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.db")


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email. `body` must be the complete, ready-to-send email text.
    This is a dangerous action: a human approves it before it runs."""
    return f"Email to {to} with subject '{subject}' sent."


TOOLS = [send_email]


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


SYSTEM = SystemMessage(
    "You are a helpful assistant. You can also write and send emails with the send_email tool; "
    "a human approval step runs automatically before any email is sent. "
    "Answer questions about the conversation from the earlier messages."
)


def build_graph(llm, checkpointer):
    llm = llm.bind_tools(TOOLS)

    def agent(state: State) -> dict:
        return {"messages": [llm.invoke([SYSTEM, *state["messages"]])]}

    def human_approval(state: State) -> Command[Literal["tools", "agent"]]:
        last = state["messages"][-1]
        answer = interrupt({
            "question": "Run these tool calls? (yes / reason for rejecting)",
            "tool_calls": [{"name": c["name"], "args": c["args"]} for c in last.tool_calls],
        })
        if str(answer).strip().lower() in {"yes", "y"}:
            return Command(goto="tools")
        rejected = [
            ToolMessage(content=f"The human rejected this call: {answer}", tool_call_id=c["id"])
            for c in last.tool_calls
        ]
        return Command(goto="agent", update={"messages": rejected})

    builder = StateGraph(State)
    builder.add_node("agent", agent)
    builder.add_node("human_approval", human_approval)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition, {"tools": "human_approval", END: END})
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=checkpointer)


def say(graph, text: str, thread_id: str) -> str:
    cfg = {"configurable": {"thread_id": thread_id}}
    before = len(graph.get_state(cfg).values.get("messages", []))
    print(f"[thread {thread_id}] history from {os.path.basename(DB_PATH)}: {before} messages")
    print(f"[thread {thread_id}] USER: {text}")
    result = graph.invoke({"messages": [("user", text)]}, cfg)

    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print(f"⏸  {payload['question']}")
        for c in payload["tool_calls"]:
            print(f"    {c['name']}({c['args']})")
        answer = input("    your answer > ")
        result = graph.invoke(Command(resume=answer), cfg)

    reply = result["messages"][-1].text
    print(f"[thread {thread_id}] AI: {reply}")
    return reply


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("message", nargs="?", default="What's my name?")
    parser.add_argument("--thread", default="1", help="thread_id (default: 1)")
    parser.add_argument("--mermaid", action="store_true")
    args = parser.parse_args(argv)

    # check_same_thread=False: LangGraph may touch the connection from worker threads
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        graph = build_graph(get_llm(), SqliteSaver(conn))
        if args.mermaid:
            print(graph.get_graph().draw_mermaid())
            return
        say(graph, args.message, args.thread)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
