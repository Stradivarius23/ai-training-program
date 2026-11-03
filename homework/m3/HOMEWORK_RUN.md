# Module 3 homework: how to run and hand in

The kit (`common.py`, `demos/`, `workshop/`) is the workshop pack as given.
`workshop/solution.py` is the facilitator solution. The homework is in `homework/task1.py` … `task6.py`.

These files are training homework. They are not product code for this repository,
so they are kept outside `src/` and `tests/`.

## Setup (local, once)

```sh
cd homework/m3
bash setup.sh                 # .venv + requirements + .env from .env.example
source .venv/bin/activate
python 00_sanity_check.py     # expect: ✅ Environment is ready
mkdir -p outputs
```

Put your key only in `homework/m3/.env`. The root `.gitignore` excludes `.env`,
`.venv/` and `*.db`.

To save a run, add `python -u … | tee outputs/taskN.txt`. The `-u` flag makes
`input()` prompts appear before you type.

## Task 1: memory that survives a restart

```sh
python -u homework/task1.py "My name is Alex"
python -u homework/task1.py "What's my name?"              # → Alex
python -u homework/task1.py "What's my name?" --thread 2   # → doesn't know
rm homework/memory.db
python -u homework/task1.py "What's my name?"              # → doesn't know
```

## Task 2: AI reviewer, human as a safety net

```sh
python -u homework/task2.py
python homework/task2.py --mermaid
```

The coder is told "no docstring" by default, and the reviewer requires a docstring and
type hints. Expect at least one `🔍 reviewer: changes requested` followed by a
`generate` that applies it. After 2 rejections the run pauses for you.

## Task 3: time travel

```sh
python -u homework/task3.py run       # normal run, checkpoints saved to homework/task3.db
python -u homework/task3.py replay    # history → fork after the first failed test → continue
```

The run must contain at least one failed test, or there is nothing to fork from.
If the first attempt passes, run `run` again. The replay prints the generate calls
it made. Attempt numbers continue from the fork.

## Task 4: notes agent

```sh
python -u homework/task4.py "What notes do I have about Kafka?"
python -u homework/task4.py      # interactive: ask for kafka-summary.md, reject once with feedback, then yes
```

Sample notes are in `homework/notes/`. Tool arguments are file names only, and paths
outside that folder are refused.

## Task 5: parallel candidates

```sh
python -u homework/task5.py
python homework/task5.py --mermaid
```

## Task 6: safer supervisor

```sh
python -u homework/task6.py --strict                    # escalation: 3 rejections in a row → you decide
python -u homework/task6.py --budget 10                 # stops on the budget
python -u homework/task6.py --task terraform            # own-domain function
python homework/task6.py --mermaid
```

The pack had no `stretch_supervisor_fixed.py`, so Task 6 builds on
`workshop/stretch_supervisor.py`. The Terraform task keeps the same kind of trap as
`slugify`: the wiki example writes index `3` as `-3`, but the rule says two digits
(`-03`). Watch who gets stuck on it and which guard would help.

## Bonus

- `--mermaid` works on every task file. Paste the output into https://mermaid.live.
- Streaming: replace `graph.invoke(...)` with
  `for u in graph.stream(inputs, cfg, stream_mode="updates"): print(u)`.

## Hand-in notes (fill in after your runs)

For each task, 2–3 sentences: what surprised you, and where the model needed a guard in code.

### Task 1

### Task 2

### Task 3

### Task 4

### Task 5

### Task 6
