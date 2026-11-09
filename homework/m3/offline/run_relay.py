"""Run one homework task with the relay model instead of the .env provider.

  python -u offline/run_relay.py [--header] task2
  python -u offline/run_relay.py task1 "My name is Alex" --thread 1
  python -u offline/run_relay.py task6 --task terraform --strict

Everything after the task name is passed to that task's main().
"""
import builtins
import os
import shutil
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.dirname(HERE), os.path.join(os.path.dirname(HERE), "homework")]

import relay_llm  # noqa: E402

HEADER = """\
════════════════════════════════════════════════════════════════════════════
OFFLINE RUN: no API key was available, so this is not a run against the
workshop model (MODEL in .env).
- The graph code is the real homework code, unchanged.
- Only common.get_llm() was replaced by offline/relay_llm.py. Every LLM call
  (prompt, tools, structured-output schema) was relayed to Claude in the coding
  session, and Claude wrote each model answer from the real prompt.
- Human answers at interrupt() pauses were also typed through the relay.
- Tests, routing, reducers, checkpoints and interrupts ran for real.
- It does not show how the workshop model itself behaves on these prompts.
════════════════════════════════════════════════════════════════════════════
"""


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] == "--header":
        print(HEADER)
        args = args[1:]
    task, task_args = args[0], args[1:]

    shutil.rmtree(relay_llm.RELAY_DIR, ignore_errors=True)   # request numbers restart in every process
    relay_llm.install()
    builtins.input = relay_llm.relay_input

    shown = " ".join(f'"{a}"' if " " in a else a for a in task_args)
    print(f"\n$ python homework/{task}.py {shown}".rstrip())
    try:
        module = __import__(task)
        if hasattr(module, "main"):
            module.main(task_args)
        else:                                                 # task2 has run(), plus --mermaid
            if "--mermaid" in task_args:
                print(module.build_graph().get_graph().draw_mermaid())
            else:
                module.run()
    except Exception:
        traceback.print_exc(file=sys.stdout)
    finally:
        relay_llm.RELAY_DIR.mkdir(parents=True, exist_ok=True)
        (relay_llm.RELAY_DIR / "done").write_text("done")


if __name__ == "__main__":
    main()
