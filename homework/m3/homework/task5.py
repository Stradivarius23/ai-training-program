"""Task 5. Parallel candidates with Send (map-reduce), fallback to the reflect loop.

Based on workshop/solution.py.

          ┌→ generate_one (simplest possible) ─┐
  START ──┼→ generate_one (use regex)         ─┼→ pick_best ──a candidate passed──→ END
          └→ generate_one (parse char by char) ┘       │none passed
                                                       ↓
                                  generate ← reflect ← ┘   (the old loop)
                                     └→ test ──ok──→ END, fail → reflect (attempts < MAX)

Run:  python homework/task5.py            (add --mermaid for the graph)
"""
import operator
import os
import sys
import traceback
from typing import Annotated, Literal, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel, Field

from common import get_llm

MAX_ATTEMPTS = 4   # the parallel round counts as attempt 1
HINTS = ["simplest possible", "use regex", "parse char by char"]

TASK = """Write a function parse_duration(s: str) -> int that converts a duration
string such as '1h30m', '45s' or '2h' into a number of seconds."""

TESTS = """
assert parse_duration("45s") == 45
assert parse_duration("2h") == 7200
assert parse_duration("1h30m") == 5400
assert parse_duration("1h0m5s") == 3605
assert parse_duration("90m") == 5400, "minutes may exceed 59"
assert parse_duration(" 1H 30M ") == 5400, "whitespace and case must be ignored"
for bad in ["", "abc", "10", "5x", "h1"]:
    try:
        parse_duration(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(f"expected ValueError for {bad!r}")
"""


# ── State ────────────────────────────────────────────────────────────────────
class Candidate(TypedDict):
    index: int
    hint: str
    code: str


class AgentState(TypedDict, total=False):
    task: str
    # three generate_one tasks write here in the SAME step: without a reducer the last
    # write would win (LangGraph actually raises InvalidUpdateError); operator.add merges them
    candidates: Annotated[list[Candidate], operator.add]
    winner: str | None
    code: str
    error: str | None
    reflection: str | None
    attempts: int


class CandidateInput(TypedDict):
    """What each Send delivers to generate_one: its own private input, not the graph state."""
    task: str
    hint: str
    index: int


class Solution(BaseModel):
    """Structured model output."""
    explanation: str = Field(description="One or two sentences on how the solution works")
    code: str = Field(description="Python code with the function only, no ```markdown``` fences, concise: no docstring, no comments, under 30 lines")


llm = get_llm()
coder = llm.with_structured_output(Solution).with_retry(stop_after_attempt=3)


# ── Map: three candidates in parallel ────────────────────────────────────────
def fan_out(state: AgentState) -> list[Send]:
    return [Send("generate_one", {"task": state["task"], "hint": h, "index": i}) for i, h in enumerate(HINTS)]


def generate_one(inp: CandidateInput) -> dict:
    solution = coder.invoke(
        f"Task:\n{inp['task']}\n\nApproach: {inp['hint']}.\n"
        "Return the complete function code. Keep it short: no docstring, no comments."
    )
    print(f"🛠  generate_one [{inp['hint']}]: {solution.explanation}")
    return {"candidates": [{"index": inp["index"], "hint": inp["hint"], "code": solution.code}]}


def run_tests(code: str) -> str | None:
    namespace: dict = {}
    try:
        # ⚠️ exec of LLM-written code — demo only. In production: sandbox / container / timeout.
        exec(code, namespace)
        exec(TESTS, namespace)
    except Exception:
        return traceback.format_exc(limit=1)
    return None


# ── Reduce: test every candidate, keep the first that passes ─────────────────
def pick_best(state: AgentState) -> dict:
    candidates = sorted(state["candidates"], key=lambda c: c["index"])
    print(f"\n🧪 pick_best: testing {len(candidates)} candidates")
    first_failure = None
    for c in candidates:
        err = run_tests(c["code"])
        print(f"   [{c['hint']}] {'✅ passed' if err is None else '❌ ' + err.strip().splitlines()[-1]}")
        print("   " + c["code"].replace("\n", "\n   "))
        if err is None:
            print(f"🏆 winner: {c['hint']}")
            return {"winner": c["hint"], "code": c["code"], "error": None, "attempts": 1}
        first_failure = first_failure or (c, err)
    c, err = first_failure
    print(f"🏳  no candidate passed — falling back to reflect → generate, starting from [{c['hint']}]")
    return {"winner": None, "code": c["code"], "error": err, "attempts": 1}


# ── The old loop (fallback) ──────────────────────────────────────────────────
def generate(state: AgentState) -> dict:
    prompt = (f"Task:\n{state['task']}\n\nPrevious version of the code:\n{state['code']}\n"
              f"\nThe tests failed with this error:\n{state['error']}\n"
              f"\nAnalysis of the error:\n{state.get('reflection')}\n"
              "\nReturn the complete, corrected function code. Keep it short: no docstring, no comments.")
    solution = coder.invoke(prompt)
    attempt = state.get("attempts", 0) + 1
    print(f"\n🛠  generate (attempt {attempt}): {solution.explanation}")
    return {"code": solution.code, "attempts": attempt}


def test(state: AgentState) -> dict:
    err = run_tests(state["code"])
    print("✅ test: all tests passed" if err is None else f"❌ test: {err.strip().splitlines()[-1]}")
    return {"error": err}


def reflect(state: AgentState) -> dict:
    msg = llm.invoke(
        "Briefly (2-3 bullet points) explain why the code failed the test and what to fix.\n\n"
        f"Code:\n{state['code']}\n\nError:\n{state['error']}"
    )
    print(f"🤔 reflect: {msg.text[:200]}")
    return {"reflection": msg.text}


def after_test(state: AgentState) -> Literal["reflect", "__end__"]:
    if state.get("error") is None:
        return END
    if state.get("attempts", 0) >= MAX_ATTEMPTS:
        print(f"🏳  giving up after {MAX_ATTEMPTS} attempts")
        return END
    return "reflect"


builder = StateGraph(AgentState)
builder.add_node("generate_one", generate_one)
builder.add_node("pick_best", pick_best)
builder.add_node("reflect", reflect)
builder.add_node("generate", generate)
builder.add_node("test", test)
builder.add_conditional_edges(START, fan_out, ["generate_one"])
builder.add_edge("generate_one", "pick_best")        # runs once, after all three finished
builder.add_conditional_edges("pick_best", after_test)
builder.add_edge("reflect", "generate")
builder.add_edge("generate", "test")
builder.add_conditional_edges("test", after_test)
graph = builder.compile()


if __name__ == "__main__":
    if "--mermaid" in sys.argv:
        print(graph.get_graph().draw_mermaid())
        sys.exit()
    result = graph.invoke({"task": TASK, "candidates": [], "attempts": 0}, {"recursion_limit": 50})
    status = "passed ✅" if result.get("error") is None else "failed the tests ❌"
    how = f"winner: {result['winner']}" if result.get("winner") else "after the fallback loop"
    print(f"\nResult: code {status} ({how}), candidates: {len(result['candidates'])}, attempts: {result.get('attempts')}")
    print("─" * 60 + f"\n{result.get('code')}\n" + "─" * 60)
