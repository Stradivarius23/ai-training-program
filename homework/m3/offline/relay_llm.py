"""Relay chat model: every LLM call is written to a file and answered by a model outside the process.

Used because no API key was available in the environment where the homework was run.
The graph code is unchanged: this only replaces common.get_llm(). Each call becomes
RELAY_DIR/req_<n>.json; the process waits for RELAY_DIR/resp_<n>.json.

Human answers at interrupt() pauses (input()) go through the same relay: {"answer": "..."}.

Response formats:
  plain call          {"content": "..."}
  with bound tools    {"content": "...", "tool_calls": [{"name": "...", "args": {...}}]}
  structured output   the schema's fields, e.g. {"approved": false, "comments": "..."}
"""
import itertools
import json
import os
import time
from pathlib import Path

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.utils.function_calling import convert_to_openai_tool

import common

RELAY_DIR = Path(os.environ.get("RELAY_DIR", Path(__file__).parent / ".relay"))
TIMEOUT_S = 1800
_counter = itertools.count(1)
_call_ids = itertools.count(1)


def _messages(prompt) -> list[dict]:
    if isinstance(prompt, str):
        return [{"role": "human", "content": prompt}]
    out = []
    for m in prompt:
        if isinstance(m, tuple):                       # ("user", "text") shorthand
            out.append({"role": m[0], "content": m[1]})
            continue
        assert isinstance(m, BaseMessage), type(m)
        item = {"role": m.type, "content": m.content}
        if getattr(m, "tool_calls", None):
            item["tool_calls"] = [{"name": c["name"], "args": c["args"]} for c in m.tool_calls]
        if m.type == "tool":
            item["tool_name"] = m.name
        out.append(item)
    return out


def exchange(request: dict) -> dict:
    """Write one request file and block until its answer file appears."""
    n = next(_counter)
    RELAY_DIR.mkdir(parents=True, exist_ok=True)
    (RELAY_DIR / f"req_{n}.json").write_text(json.dumps({"n": n, **request}, ensure_ascii=False, indent=1))
    resp_path = RELAY_DIR / f"resp_{n}.json"
    deadline = time.time() + TIMEOUT_S
    while not resp_path.exists():
        if time.time() > deadline:
            raise TimeoutError(f"no answer for relay request {n}")
        time.sleep(0.2)
    time.sleep(0.05)                                   # let the writer finish
    return json.loads(resp_path.read_text())


def relay_input(prompt: str = "") -> str:
    """Stand-in for input() at interrupt() pauses: the human answer comes through the relay too."""
    answer = exchange({"kind": "input", "prompt": prompt})["answer"]
    print(f"{prompt}{answer}")
    return answer


class RelayLLM:
    """Supports what the tasks use: invoke, bind_tools, with_structured_output, with_retry."""

    def __init__(self, tools=None, schema=None):
        self.tools, self.schema = tools, schema

    def bind_tools(self, tools):
        return RelayLLM(tools=[convert_to_openai_tool(t)["function"] for t in tools])

    def with_structured_output(self, schema):
        return RelayLLM(schema=schema)

    def with_retry(self, **kwargs):
        return self

    def invoke(self, prompt):
        request = {"kind": "llm", "messages": _messages(prompt)}
        if self.schema:
            request["structured_output"] = self.schema.model_json_schema()
        if self.tools:
            request["tools"] = self.tools
        answer = exchange(request)
        if self.schema:
            return self.schema(**answer)
        calls = [{"name": c["name"], "args": c.get("args", {}), "id": f"relay_call_{next(_call_ids)}"}
                 for c in answer.get("tool_calls", [])]
        return AIMessage(content=answer.get("content", ""), tool_calls=calls)


def install() -> None:
    """Replace common.get_llm before any task module is imported."""
    common.get_llm = lambda temperature=0: RelayLLM()
