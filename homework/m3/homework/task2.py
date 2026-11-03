"""Task 2. Replace the human reviewer with an AI reviewer (human stays as a safety net).

Based on workshop/solution.py.

  START → generate → test ──ok──→ reviewer ──approved──→ END
              ↑  ↑       │fail        │changes requested (rejections < 2)
              │  └ reflect ←┘          └──→ generate (comments as feedback)
              │                         │rejected twice
              └────── feedback ── human_review (interrupt) ──yes──→ END

The coder is told "no docstring, no comments" by default, the reviewer demands a docstring
and type hints — so at least one review round is almost guaranteed.

Run:  python homework/task2.py            (add --mermaid for the graph)
"""
import os
import sys
import traceback
from typing import Literal, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field

from common import get_llm

MAX_ATTEMPTS = 6        # generate calls in total: test fixes + review fixes
MAX_REJECTIONS = 2      # reviewer rejections before a human decides

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
class AgentState(TypedDict, total=False):
    task: str
    code: str
    error: str | None
    reflection: str | None
    feedback: str | None          # comment from the AI reviewer or the human
    attempts: int
    review_ok: bool
    review_comments: str | None
    review_rejections: int


class Solution(BaseModel):
    """Structured model output."""
    explanation: str = Field(description="One or two sentences on how the solution works")
    code: str = Field(description="Python code with the function only, no ```markdown``` fences, under 40 lines")


class Review(BaseModel):
    """Structured reviewer verdict."""
    approved: bool = Field(description="True only if the code meets every review rule")
    comments: str = Field(description="Concrete list of what to change, or a short approval note")


llm = get_llm()
# retry: providers occasionally return malformed structured output (e.g. long code breaks the JSON)
coder = llm.with_structured_output(Solution).with_retry(stop_after_attempt=3)
reviewer_llm = llm.with_structured_output(Review).with_retry(stop_after_attempt=3)


# ── Nodes ────────────────────────────────────────────────────────────────────
def generate(state: AgentState) -> dict:
    prompt = f"Task:\n{state['task']}\n"
    if state.get("code"):
        prompt += f"\nPrevious version of the code:\n{state['code']}\n"
    if state.get("error"):
        prompt += f"\nThe tests failed with this error:\n{state['error']}\n"
    if state.get("reflection"):
        prompt += f"\nAnalysis of the error:\n{state['reflection']}\n"
    prompt += "\nReturn the complete, corrected function code. Keep it short: no docstring, no comments."
    if state.get("feedback"):
        prompt += (f"\n\nReview comments you MUST apply (they override the style rules above):\n"
                   f"{state['feedback']}\n")

    solution = coder.invoke(prompt)
    attempt = state.get("attempts", 0) + 1
    print(f"\n🛠  generate (attempt {attempt}): {solution.explanation}")
    return {"code": solution.code, "attempts": attempt, "feedback": None}


def test(state: AgentState) -> dict:
    namespace: dict = {}
    try:
        # ⚠️ exec of LLM-written code — demo only. In production: sandbox / container / timeout.
        exec(state["code"], namespace)
        exec(TESTS, namespace)
    except Exception:
        err = traceback.format_exc(limit=1)
        print(f"❌ test: {err.strip().splitlines()[-1]}")
        return {"error": err}
    print("✅ test: all tests passed")
    return {"error": None}


def reflect(state: AgentState) -> dict:
    msg = llm.invoke(
        "Briefly (2-3 bullet points) explain why the code failed the test and what to fix.\n\n"
        f"Code:\n{state['code']}\n\nError:\n{state['error']}"
    )
    print(f"🤔 reflect: {msg.text[:200]}")
    return {"reflection": msg.text}


def reviewer(state: AgentState) -> dict:
    review = reviewer_llm.invoke(
        "You are a strict senior Python reviewer. The code already passes its unit tests.\n"
        "Approve ONLY if ALL rules hold:\n"
        "1. The function has a docstring that explains the accepted format and the ValueError cases.\n"
        "2. Every parameter and the return value have type hints.\n"
        "3. The code solves the task as written, with no special-casing of specific inputs.\n"
        "Otherwise set approved=false and list exactly what to change.\n\n"
        f"Task:\n{state['task']}\n\nCode:\n{state['code']}"
    )
    if review.approved:
        print(f"🔍 reviewer: approved ✅ — {review.comments[:200]}")
        return {"review_ok": True, "review_comments": review.comments}

    rejections = state.get("review_rejections", 0) + 1
    print(f"🔍 reviewer: changes requested ✏️ ({rejections}/{MAX_REJECTIONS}) — {review.comments[:200]}")
    return {"review_ok": False, "review_comments": review.comments, "review_rejections": rejections,
            "feedback": review.comments, "error": None, "reflection": None}


def human_review(state: AgentState) -> Command[Literal["generate", "__end__"]]:
    answer = interrupt({
        "code": state["code"],
        "comments": state.get("review_comments"),
        "question": f"The AI reviewer rejected this code {state.get('review_rejections')} times. "
                    "Accept it anyway? (yes / your feedback)",
    })
    if str(answer).strip().lower() in {"yes", "y"}:
        return Command(goto=END, update={"review_ok": True})
    # the human's feedback starts a fresh round with the AI reviewer
    return Command(goto="generate", update={"feedback": answer, "error": None, "reflection": None,
                                            "review_rejections": 0})


# ── Edges ────────────────────────────────────────────────────────────────────
def after_test(state: AgentState) -> Literal["reviewer", "reflect", "__end__"]:
    if state.get("error") is None:
        return "reviewer"
    if state.get("attempts", 0) >= MAX_ATTEMPTS:
        print(f"🏳  giving up after {MAX_ATTEMPTS} attempts")
        return END
    return "reflect"


def after_review(state: AgentState) -> Literal["generate", "human_review", "__end__"]:
    if state.get("review_ok"):
        return END
    if state.get("review_rejections", 0) >= MAX_REJECTIONS:
        return "human_review"
    if state.get("attempts", 0) >= MAX_ATTEMPTS:
        return "human_review"   # out of attempts: still a human call, not a silent stop
    return "generate"


def build_graph(checkpointer=None):
    builder = StateGraph(AgentState)
    builder.add_node("generate", generate)
    builder.add_node("test", test)
    builder.add_node("reflect", reflect)
    builder.add_node("reviewer", reviewer)
    builder.add_node("human_review", human_review)
    builder.add_edge(START, "generate")
    builder.add_edge("generate", "test")
    builder.add_conditional_edges("test", after_test)
    builder.add_edge("reflect", "generate")
    builder.add_conditional_edges("reviewer", after_review)
    return builder.compile(checkpointer=checkpointer or InMemorySaver())


# ── Runner ───────────────────────────────────────────────────────────────────
def resume_until_done(graph, result: dict, cfg: dict) -> dict:
    """Answer interrupt() pauses from the keyboard until the graph finishes."""
    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print("\n" + "─" * 60 + f"\n{payload['code']}\n" + "─" * 60)
        if payload.get("comments"):
            print(f"Reviewer said: {payload['comments']}")
        answer = input(f"{payload['question']} > ")
        result = graph.invoke(Command(resume=answer), cfg)
    return result


def print_result(result: dict) -> None:
    passed = result.get("error") is None
    approved = result.get("review_ok")
    status = "accepted ✅" if passed and approved else "failed the tests ❌" if not passed else "not approved ❌"
    print(f"\nResult: code {status}, attempts: {result.get('attempts')}")
    print("─" * 60 + f"\n{result.get('code')}\n" + "─" * 60)


def run() -> None:
    graph = build_graph()
    cfg = {"configurable": {"thread_id": "task2"}, "recursion_limit": 50}
    result = graph.invoke({"task": TASK, "attempts": 0, "review_rejections": 0}, cfg)
    print_result(resume_until_done(graph, result, cfg))


if __name__ == "__main__":
    if "--mermaid" in sys.argv:
        print(build_graph().get_graph().draw_mermaid())
    else:
        run()
