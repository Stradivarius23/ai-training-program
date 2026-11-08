"""Task 6. A safer supervisor: escalation to a human, an LLM-call budget, a domain task.

Based on workshop/stretch_supervisor.py (the pack had no stretch_supervisor_fixed.py).

New guards (code, not LLM), checked by the supervisor before every decision:
  budget      every LLM call is counted per agent; when the next step could go over
              BUDGET the team stops with a clear message
  escalation  the reviewer requested changes REVIEW_LIMIT times in a row → interrupt():
              the human answers continue / finish / free-text instructions for the coder

Run:
  python homework/task6.py                          # slugify, as in the workshop
  python homework/task6.py --task terraform         # a function from my own domain
  python homework/task6.py --strict                 # strict reviewer → triggers the escalation
  python homework/task6.py --budget 10              # stops on the budget
  python homework/task6.py --mermaid
"""
import argparse
import operator
import os
import sys
import traceback
from typing import Annotated, Literal, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field

from common import get_llm

MAX_TURNS = 20
BUDGET = 30          # LLM calls for the whole team; override with --budget
REVIEW_LIMIT = 3     # consecutive "changes requested" before a human decides
STRICT = False       # --strict: the reviewer also demands a docstring the coder is told not to write

TASKS = {
    "slugify": """Write a Python function slugify(title: str, max_len: int = 40) -> str that turns an article
title into a URL slug:
- lowercase; accented letters become plain ones (é → e); any other non [a-z0-9] characters are separators;
- words are joined by single hyphens, no leading or trailing hyphens;
- if the slug is longer than max_len, cut it at the last hyphen that keeps it within max_len
  (if there is no such hyphen, hard-cut at max_len).
Example from the product manager's ticket — include it in the tests as is:
  slugify('Hello, World!', max_len=8) == 'hello-wo'""",

    "terraform": """Write a Python function tf_name(project: str, env: str, component: str, index: int | None = None) -> str
that builds a cloud resource name by our Terraform naming convention:
- format <project>-<env>-<component>, plus -<NN> when index is given; all lowercase;
- env is one of dev, stg, prd; the aliases development, staging, production map to them; anything else → ValueError;
- in project and component every character outside [a-z0-9] is a separator; separators become single hyphens,
  no leading or trailing hyphens; empty after cleaning → ValueError;
- index must be 1..99 and is always written with two digits (7 → 07), otherwise ValueError;
- the full name is at most 32 characters: shorten only the component, cutting at the last hyphen that fits
  (hard cut if there is none); if it still does not fit → ValueError.
Example from the platform team's wiki — include it in the tests as is:
  tf_name('Payments API', 'production', 'Blob Storage', 3) == 'payments-api-prd-blob-storage-3'""",
}


# ── State ────────────────────────────────────────────────────────────────────
def add_counts(a: dict[str, int], b: dict[str, int]) -> dict[str, int]:
    """Reducer: sum per-agent LLM-call counters."""
    out = dict(a or {})
    for k, v in (b or {}).items():
        out[k] = out.get(k, 0) + v
    return out


class TeamState(TypedDict, total=False):
    task: str
    spec: str
    tests: str
    code: str
    test_report: str
    tests_passed: bool
    review: str
    review_ok: bool
    review_streak: int                    # consecutive "changes requested"
    human_instructions: str               # free text from the escalation, passed to the coder
    llm_calls: Annotated[dict[str, int], add_counts]
    stop_reason: str
    turns: int
    trace: Annotated[list[str], operator.add]   # route log, appended by every node


# ── Structured outputs ───────────────────────────────────────────────────────
class Plan(BaseModel):
    spec: str = Field(description="Short spec as bullet points: behaviour and edge cases")
    tests: str = Field(description="6-10 Python assert statements calling the function, one per line, "
                                   "no imports, no function definition, no markdown")


class CodeDraft(BaseModel):
    code: str = Field(description="Complete Python code of the function with any imports it needs, no markdown, under 40 lines")
    notes: str = Field(description="One sentence: what you did or changed")


class Review(BaseModel):
    approved: bool = Field(description="True if the code is correct and matches the spec")
    comments: str = Field(description="Concrete problems to fix, or a short approval note")


class Route(BaseModel):
    next: Literal["planner", "coder", "tester", "reviewer", "FINISH"]
    reason: str = Field(description="One short sentence")


llm = get_llm()
# retry: providers occasionally return malformed structured output (e.g. long code breaks the JSON)
planner_llm = llm.with_structured_output(Plan).with_retry(stop_after_attempt=3)
coder_llm = llm.with_structured_output(CodeDraft).with_retry(stop_after_attempt=3)
reviewer_llm = llm.with_structured_output(Review).with_retry(stop_after_attempt=3)
router_llm = llm.with_structured_output(Route).with_retry(stop_after_attempt=3)


def called(agent: str) -> dict:
    return {"llm_calls": {agent: 1}}


# ── Supervisor + guards ──────────────────────────────────────────────────────
def status(state: TeamState) -> str:
    def yn(v): return "yes" if v else "no"
    return (
        f"spec and tests written: {yn(state.get('spec'))}\n"
        f"code written: {yn(state.get('code'))}\n"
        f"tests run on current code: {yn(state.get('test_report'))}\n"
        f"tests passed: {yn(state.get('tests_passed'))}\n"
        f"last test report: {state.get('test_report') or '-'}\n"
        f"reviewer approved current code: {yn(state.get('review_ok'))}\n"
        f"last review: {state.get('review') or '-'}"
    )


def guard(state: TeamState, nxt: str) -> tuple[str, str | None]:
    """Deterministic rules the LLM is not allowed to break."""
    if not state.get("spec") and nxt != "planner":
        return "planner", "nothing to work on without a spec"
    if nxt in ("tester", "reviewer") and not state.get("code"):
        return "coder", "there is no code yet"
    if nxt == "FINISH" and not (state.get("tests_passed") and state.get("review_ok")):
        if not state.get("test_report"):
            return "tester", "the current code was never tested"
        if not state.get("tests_passed"):
            return "coder", "tests are failing"
        return "reviewer", "the reviewer has not approved yet"
    return nxt, None


def supervisor(state: TeamState) -> Command[Literal["planner", "coder", "tester", "reviewer", "__end__"]]:
    # ⚠️ on resume after interrupt() this node runs again from the top: no LLM calls before the interrupt
    turns = state.get("turns", 0)
    if turns >= MAX_TURNS:
        print(f"⏹  MAX_TURNS={MAX_TURNS} reached, stopping")
        return Command(goto=END, update={"trace": ["MAX_TURNS"], "stop_reason": f"MAX_TURNS={MAX_TURNS}"})

    # budget guard: the next step costs up to 2 calls (supervisor + worker)
    spent = sum(state.get("llm_calls", {}).values())
    if spent + 2 > BUDGET:
        msg = f"LLM budget: {spent} of {BUDGET} calls used, the next step could go over"
        print(f"💸 budget guard: {msg} — stopping")
        return Command(goto=END, update={"trace": ["BUDGET"], "stop_reason": msg})

    # escalation guard: the reviewer keeps rejecting → a human decides
    update: dict = {}
    if state.get("review_streak", 0) >= REVIEW_LIMIT:
        answer = str(interrupt({
            "question": f"The reviewer requested changes {state['review_streak']} times in a row.",
            "review": state.get("review"),
            "code": state.get("code"),
            "options": "continue / finish / or type instructions for the coder",
        })).strip()
        if answer.lower() == "finish":
            return Command(goto=END, update={"trace": ["👤FINISH"], "stop_reason": "human chose finish"})
        if answer.lower() != "continue":
            print(f"👤 human → coder: {answer}")
            return Command(goto="coder", update={"review_streak": 0, "human_instructions": answer,
                                                 "turns": turns + 1, "trace": ["coder👤"]})
        update["review_streak"] = 0
        print("👤 human: continue")

    decision = router_llm.invoke(
        "You are the tech lead of a small team: planner (spec + tests), coder (writes and fixes code), "
        "tester (runs the tests), reviewer (reviews code). Pick who works next.\n"
        "Typical order: planner → coder → tester → (coder again if tests fail) → reviewer "
        "→ (coder again if changes requested) → FINISH when tests pass and the review is approved.\n"
        "If the same test keeps failing after the coder tried twice, the test itself may be wrong: "
        "send it back to the planner to fix the tests.\n\n"
        f"Task:\n{state['task']}\n\nCurrent status:\n{status(state)}"
    )
    nxt, why = guard(state, decision.next)
    print(f"\n🧭 supervisor → {decision.next}: {decision.reason}")
    if why:
        print(f"🛡  guard: {decision.next} → {nxt} ({why})")

    update |= {"turns": turns + 1, "trace": [nxt if not why else f"{nxt}🛡"], **called("supervisor")}
    return Command(goto=END if nxt == "FINISH" else nxt, update=update)


# ── Workers (every worker reports back to the supervisor) ────────────────────
def planner(state: TeamState) -> Command[Literal["supervisor"]]:
    prompt = (f"Write a short spec and test cases for this task.\n\nTask:\n{state['task']}\n\n"
              "Tests must be plain assert statements with exact expected values you are sure about.")
    if state.get("tests"):   # called again: the supervisor suspects the tests are wrong
        prompt += (f"\n\nYour previous tests:\n{state['tests']}\n\nThey keep failing with:\n"
                   f"{state.get('test_report')}\nFix any test whose expected value is wrong for the task.")
    plan = planner_llm.invoke(prompt)
    n = sum(1 for line in plan.tests.splitlines() if line.strip().startswith("assert"))
    print(f"📝 planner: spec ready, {n} tests")
    # new tests → previous test result no longer applies
    return Command(goto="supervisor", update={"spec": plan.spec, "tests": plan.tests,
                                              "test_report": "", "tests_passed": False, **called("planner")})


def coder(state: TeamState) -> Command[Literal["supervisor"]]:
    prompt = f"Task:\n{state['task']}\n\nSpec:\n{state['spec']}\n\nTests it must pass:\n{state['tests']}\n"
    if state.get("code"):
        prompt += f"\nCurrent code:\n{state['code']}\n"
    if state.get("test_report") and not state.get("tests_passed"):
        prompt += f"\nTest failure:\n{state['test_report']}\n"
    if state.get("review") and not state.get("review_ok"):
        prompt += f"\nReviewer comments:\n{state['review']}\n"
    prompt += ("\nReturn the complete corrected function. Keep it short: no docstring, no comments. "
               "Follow the rules in the task; never special-case specific inputs to make a test pass.")
    if state.get("human_instructions"):
        prompt += f"\n\nInstructions from the human lead (they override everything above):\n{state['human_instructions']}"
    draft = coder_llm.invoke(prompt)
    print(f"🛠  coder: {draft.notes}")
    # new code → previous test and review results no longer apply
    return Command(goto="supervisor", update={
        "code": draft.code, "test_report": "", "tests_passed": False, "review": "", "review_ok": False,
        **called("coder")})


def tester(state: TeamState) -> Command[Literal["supervisor"]]:
    ns: dict = {}
    try:
        # ⚠️ exec of LLM-written code — demo only. In production: sandbox / container / timeout.
        exec(state["code"], ns)
        exec(state["tests"], ns)
        report, ok = "all tests passed", True
    except Exception:
        report, ok = traceback.format_exc(limit=1).strip().splitlines()[-1], False
    print(f"🧪 tester: {'✅' if ok else '❌'} {report}")
    return Command(goto="supervisor", update={"test_report": report, "tests_passed": ok})


def reviewer(state: TeamState) -> Command[Literal["supervisor"]]:
    rules = ("Be pragmatic: request changes only for real bugs or missed requirements, not for style. "
             "Reject code that special-cases specific inputs.")
    if STRICT:
        rules += " House rule: also reject any function without a docstring that lists its rules and errors."
    review = reviewer_llm.invoke(
        f"Review this function against the spec. {rules}\n\n"
        f"Spec:\n{state['spec']}\n\nCode:\n{state['code']}\n\nTest result: {state.get('test_report')}"
    )
    streak = 0 if review.approved else state.get("review_streak", 0) + 1
    verdict = "approved ✅" if review.approved else f"changes requested ✏️ ({streak} in a row)"
    print(f"🔍 reviewer: {verdict} — {review.comments[:160]}")
    return Command(goto="supervisor", update={"review": review.comments, "review_ok": review.approved,
                                              "review_streak": streak, **called("reviewer")})


# ── Graph ────────────────────────────────────────────────────────────────────
builder = StateGraph(TeamState)
builder.add_node("supervisor", supervisor)
for name, fn in [("planner", planner), ("coder", coder), ("tester", tester), ("reviewer", reviewer)]:
    builder.add_node(name, fn)
builder.add_edge(START, "supervisor")      # every other route is chosen at runtime via Command(goto=...)
graph = builder.compile(checkpointer=InMemorySaver())   # interrupt() needs a checkpointer


def print_calls(calls: dict[str, int]) -> None:
    print(f"\n{'agent':<12}{'LLM calls':>10}")
    for agent in ("supervisor", "planner", "coder", "reviewer"):
        print(f"{agent:<12}{calls.get(agent, 0):>10}")
    print(f"{'total':<12}{sum(calls.values()):>10}   (budget {BUDGET})")


def main(argv=None) -> None:
    global BUDGET, STRICT
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--task", choices=sorted(TASKS), default="slugify")
    parser.add_argument("--budget", type=int, default=BUDGET)
    parser.add_argument("--strict", action="store_true", help="strict reviewer, to see the escalation")
    parser.add_argument("--mermaid", action="store_true")
    args = parser.parse_args(argv)
    BUDGET, STRICT = args.budget, args.strict

    if args.mermaid:
        print(graph.get_graph().draw_mermaid())
        return

    task = TASKS[args.task]
    print(f"TASK: {task}\nBUDGET: {BUDGET} LLM calls · escalation after {REVIEW_LIMIT} rejections · strict={STRICT}")
    cfg = {"configurable": {"thread_id": "team"}, "recursion_limit": 80}
    result = graph.invoke({"task": task, "turns": 0, "trace": [], "review_streak": 0, "llm_calls": {}}, cfg)
    while "__interrupt__" in result:
        p = result["__interrupt__"][0].value
        print("\n" + "─" * 60 + f"\n⏸  {p['question']}\nLast review: {p['review']}\n"
              + "─" * 60 + f"\n{p['code']}\n" + "─" * 60)
        answer = input(f"{p['options']} > ")
        result = graph.invoke(Command(resume=answer), cfg)

    print("\n" + "═" * 60)
    print("Route (supervisor decides between every step, 🛡 = corrected by the guard, 👤 = human):")
    print("  " + " → ".join(result.get("trace", [])))
    done = result.get("tests_passed") and result.get("review_ok")
    reason = "" if done else f" — {result.get('stop_reason', 'unknown')}"
    print(f"Result: {'done ✅ (tests passed, review approved)' if done else 'stopped before done ❌'}{reason}")
    print_calls(result.get("llm_calls", {}))
    print("─" * 60 + f"\n{result.get('code', '(no code)')}\n" + "─" * 60)


if __name__ == "__main__":
    main()
