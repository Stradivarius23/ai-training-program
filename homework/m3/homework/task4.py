"""Task 4. Your own agent with real tools: a notes assistant for a folder of .md files.

  START → agent ──no tool calls──→ END
            ↑   ├─only safe tools (list_notes, read_note)──→ tools ─┐
            │   └─write_note in the calls──→ approve (interrupt) ───┤ yes → tools
            │                                       │ rejected      │
            └───────────────────────────────────────┴───────────────┘

Files are confined to homework/notes/: tool arguments are file names, never paths.

Run:
  python homework/task4.py "What notes do I have about Kafka?"
  python homework/task4.py "Add a summary of all Kafka notes to kafka-summary.md"
  python homework/task4.py                       # interactive chat, one thread
"""
import os
import sys
from pathlib import Path
from typing import Annotated, Literal, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt

from common import get_llm

NOTES_DIR = (Path(__file__).parent / "notes").resolve()
MAX_READ = 8000


def note_path(name: str) -> Path:
    """Map a note name to a file inside NOTES_DIR. Never trust a path from the model."""
    name = name.strip()
    if not name.endswith(".md"):
        name += ".md"
    if Path(name).name != name or name.startswith("."):
        raise ValueError(f"{name!r} is not a plain note name; use a file name like 'kafka.md'")
    path = (NOTES_DIR / name).resolve()
    if path.parent != NOTES_DIR:
        raise ValueError(f"{name!r} is outside the notes folder")
    return path


@tool
def list_notes(query: str = "") -> str:
    """List the notes in the notes folder with their title line.
    If `query` is given, only notes whose name or text contains it (case-insensitive) are listed.
    Use this first to find which notes exist before reading them."""
    rows = []
    for p in sorted(NOTES_DIR.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        if query and query.lower() not in (p.name + text).lower():
            continue
        title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.strip()), "")
        rows.append(f"{p.name} — {title}")
    return "\n".join(rows) or "No matching notes."


@tool
def read_note(name: str) -> str:
    """Return the full Markdown text of one note. `name` is a file name from list_notes, e.g. 'kafka-basics.md'."""
    path = note_path(name)
    if not path.exists():
        raise ValueError(f"No note named {path.name}. Call list_notes to see what exists.")
    return path.read_text(encoding="utf-8")[:MAX_READ]


@tool
def write_note(name: str, text: str) -> str:
    """Create or overwrite a note with the complete Markdown `text`.
    This is a dangerous action: a human approves the exact text before it is written.
    `name` is a plain file name such as 'kafka-summary.md'."""
    path = note_path(name)
    path.write_text(text, encoding="utf-8")
    return f"Wrote {len(text)} characters to {path.name}."


SAFE_TOOLS = [list_notes, read_note]
DANGEROUS = {"write_note"}
TOOLS = [*SAFE_TOOLS, write_note]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}

SYSTEM = SystemMessage(
    "You are a notes assistant for a folder of Markdown notes. "
    "Use list_notes and read_note to answer questions; never guess note contents. "
    "To create or change a note, write the complete final Markdown yourself and call write_note right away. "
    "Do not ask the user to confirm in plain text: a human approval step runs automatically before any write. "
    "If the human rejects a write, rewrite the text according to their feedback and call write_note again."
)


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


llm = get_llm().bind_tools(TOOLS)


def agent(state: State) -> dict:
    return {"messages": [llm.invoke([SYSTEM, *state["messages"]])]}


def route(state: State) -> Literal["tools", "approve", "__end__"]:
    calls = getattr(state["messages"][-1], "tool_calls", None) or []
    if not calls:
        return END
    if any(c["name"] in DANGEROUS for c in calls):
        return "approve"
    return "tools"


def approve(state: State) -> Command[Literal["tools", "agent"]]:
    calls = state["messages"][-1].tool_calls
    writes = [c for c in calls if c["name"] in DANGEROUS]
    answer = interrupt({
        "question": "Write these notes? (yes / what to change)",
        "writes": [{"name": c["args"].get("name"), "text": c["args"].get("text", "")} for c in writes],
    })
    if str(answer).strip().lower() in {"yes", "y"}:
        return Command(goto="tools")
    # every tool_call needs a ToolMessage: run the safe ones, reject the writes
    replies = []
    for c in calls:
        if c["name"] in DANGEROUS:
            replies.append(ToolMessage(content=f"The human rejected this write: {answer}",
                                       name=c["name"], tool_call_id=c["id"]))
        else:
            replies.append(TOOLS_BY_NAME[c["name"]].invoke(c))
    return Command(goto="agent", update={"messages": replies})


builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_node("approve", approve)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", route)
builder.add_edge("tools", "agent")
graph = builder.compile(checkpointer=InMemorySaver())


def say(text: str, cfg: dict) -> None:
    print(f"\nUSER: {text}")
    seen = len(graph.get_state(cfg).values.get("messages", []))
    result = graph.invoke({"messages": [("user", text)]}, cfg)
    while True:
        for m in result["messages"][seen:]:
            if getattr(m, "tool_calls", None):
                print("[agent] calls: " + ", ".join(
                    f"{c['name']}({c['args'].get('name') or c['args'].get('query') or ''})" for c in m.tool_calls))
            elif m.type == "tool":
                print(f"[tool] {m.name}: {m.content[:120].replace(chr(10), ' | ')}")
        seen = len(result["messages"])
        if "__interrupt__" not in result:
            break
        payload = result["__interrupt__"][0].value
        print(f"⏸  {payload['question']}")
        for w in payload["writes"]:
            print(f"    → {w['name']}\n    " + "─" * 50)
            for line in str(w["text"]).splitlines():
                print(f"    {line}")
            print("    " + "─" * 50)
        answer = input("    your answer > ")
        result = graph.invoke(Command(resume=answer), cfg)
    print(f"AI: {result['messages'][-1].text}")


if __name__ == "__main__":
    if "--mermaid" in sys.argv:
        print(graph.get_graph().draw_mermaid())
        sys.exit()
    cfg = {"configurable": {"thread_id": "notes"}, "recursion_limit": 40}
    if len(sys.argv) > 1:
        say(" ".join(sys.argv[1:]), cfg)
    else:
        print(f"Notes folder: {NOTES_DIR}  (empty line to quit)")
        while text := input("\nyou > ").strip():
            say(text, cfg)
