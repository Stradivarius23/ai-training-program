# Skill: pr-reviewer

## Purpose and when to use

Review a change against [review/change-template.md](../../review/change-template.md).
Use it before a human review on every change. It reports; it does not fix,
approve, or merge.

## Required inputs

- The diff or list of changed files.
- The linked spec path, or the statement "docs/config only".
- Output of `bash scripts/validate.sh` (run it if not given).

## Steps

1. Run `bash scripts/validate.sh` and keep the output.
2. Open the linked spec. Record its Status and approval fields.
3. Compare changed files with the spec Scope and the plan file list.
4. Map each acceptance criterion to a test file and test name.
5. Search the diff for secrets (keys, tokens, passwords, private keys).
6. List new dependencies and find each justification in the spec.
7. Compare changed files with the protected paths in `AGENTS.md`.
8. Check whether README, AGENTS.md, specs, or docs need updates.
9. Answer the checklist below. Each answer is Yes, No, or Not applicable, with evidence.
10. Give a verdict: `Ready for human review` only if no answer is No.

## Checklist (same as review/change-template.md)

| # | Question |
|---|----------|
| 1 | Is an approved specification linked? |
| 2 | Is the change within scope? |
| 3 | Are acceptance criteria covered by tests? |
| 4 | Did validation pass? |
| 5 | Are secrets absent? |
| 6 | Are dependencies justified? |
| 7 | Are protected paths unchanged or approved? |
| 8 | Are relevant documents updated? |

## Stop conditions

- No diff is available: stop and ask for it.
- A secret is found: stop, do not repeat it, report file and line only.
- Validation cannot run: report "No" for question 4 with the error.

## Output format

The filled checklist table (`# | Question | Answer | Evidence`), then a list
of blocking issues, then the verdict line.

## Quality checks (Yes/No)

- Are all eight questions answered?
- Is every answer exactly Yes, No, or Not applicable?
- Does every answer have evidence?
- Is the verdict `Not ready` whenever any answer is No?
- Were zero files changed by the reviewer?

## Example

Input: diff adds `src/health.py` and `tests/test_health.py`; spec
`specs/health-endpoint.md` is Draft.

Output (excerpt):

```
| 1 | Is an approved specification linked? | No | specs/health-endpoint.md shows "Status: Draft" |
Blocking: feature code exists without an approved spec.
Verdict: Not ready
```
