"""Task 3. Time travel: checkpoint history, update_state, replay from a checkpoint.

Uses the graph from task2.py with a SqliteSaver, so the history outlives the process.

Run (two separate processes, same thread_id):
  python homework/task3.py run       # a normal run, every checkpoint saved to task3.db
  python homework/task3.py replay    # history → fork after the first failed test → continue
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph.checkpoint.sqlite import SqliteSaver

import task2

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "task3.db")
THREAD = {"configurable": {"thread_id": "task3"}, "recursion_limit": 50}
FEEDBACK = "Use a regular expression with re.fullmatch"

# count generate calls: build_graph() picks up task2.generate when it is called
generate_calls = 0
_generate = task2.generate


def counted_generate(state):
    global generate_calls
    generate_calls += 1
    return _generate(state)


task2.generate = counted_generate


def print_history(graph) -> list:
    history = list(graph.get_state_history(THREAD))          # newest first
    print(f"{'step':>4}  {'next':<16}{'attempts':>8}  error  checkpoint")
    for snap in reversed(history):                           # print oldest first
        v = snap.values
        print(f"{snap.metadata.get('step'):>4}  {str(snap.next or '(end)'):<16}"
              f"{v.get('attempts', '-')!s:>8}  {'yes' if v.get('error') else 'no ':<5}  "
              f"{snap.config['configurable']['checkpoint_id'][-8:]}")
    print(f"total checkpoints: {len(history)}")
    return history


def run(graph) -> None:
    result = graph.invoke({"task": task2.TASK, "attempts": 0, "review_rejections": 0}, THREAD)
    task2.print_result(task2.resume_until_done(graph, result, THREAD))
    print(f"\ngenerate calls in this run: {generate_calls}")


def replay(graph) -> None:
    history = print_history(graph)
    if not history:
        sys.exit("No history for this thread. Run `python homework/task3.py run` first.")

    # right after a failed test the graph is about to run reflect; history is newest first → take the last match
    failed = [s for s in history if s.next == ("reflect",)]
    if not failed:
        sys.exit("The tests never failed in this run — nothing to time-travel to. Run again.")
    snap = failed[-1]
    print(f"\n⏪ fork from step {snap.metadata.get('step')} "
          f"(attempts={snap.values.get('attempts')}, next={snap.next}), "
          f"checkpoint …{snap.config['configurable']['checkpoint_id'][-8:]}")
    print(f"   failing test: {snap.values['error'].strip().splitlines()[-1]}")
    print(f"   + feedback: {FEEDBACK!r}")

    # as_node="test": the update counts as written by `test`, so after_test routes again (→ reflect)
    new_cfg = graph.update_state(snap.config, {"feedback": FEEDBACK}, as_node="test")
    result = graph.invoke(None, {**new_cfg, "recursion_limit": 50})   # None = no new input, continue
    result = task2.resume_until_done(graph, result, THREAD)            # pauses resume on the new branch head
    task2.print_result(result)

    print(f"\ngenerate calls during the replay: {generate_calls} "
          f"(attempt numbers continue from {snap.values.get('attempts')}: earlier steps were not re-run)")
    print("\nHistory after the replay (the fork is a new branch from the chosen checkpoint):")
    print_history(graph)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "replay"
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        checkpointer = SqliteSaver(conn)
        if mode == "run":
            checkpointer.delete_thread("task3")    # start the thread from scratch
        graph = task2.build_graph(checkpointer)
        {"run": run, "replay": replay}.get(mode, lambda g: sys.exit(__doc__))(graph)
    finally:
        conn.close()
