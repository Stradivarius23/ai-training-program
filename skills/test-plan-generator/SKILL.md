# Skill: test-plan-generator

## Purpose and when to use

Map every acceptance criterion of a spec to concrete test cases. Use it after
a spec reaches `In Review` or `Approved`, before writing tests. It writes a
plan document only, never test code.

## Required inputs

- Path to a spec with Given/When/Then acceptance criteria.
- The spec Status.
- The approved test framework, if the spec names one.

## Steps

1. Read the spec. Record Status and every AC ID.
2. For each AC, write one positive test case.
3. Add a negative or edge case only if the spec states that behavior.
4. For each case give: ID, AC, name, Given, When, Then, type (unit/integration).
5. If the test framework is not named in the spec, write "Framework: not
   decided — blocked by open question" instead of choosing one.
6. List ACs that are untestable or depend on open questions as Blocked.
7. If Status is not `Approved`, mark the plan `Provisional`.

## Stop conditions

- The spec has no Given/When/Then criteria: stop and ask for them.
- The spec is `Rejected`: stop.
- A test would need behavior not in the spec: record it as a question; do not add it.

## Output format

```
Test plan for <spec path> — <Final | Provisional>
Framework: <name | not decided>
| ID | AC | Test name | Given | When | Then | Type |
Blocked: <list or None>
Questions: <list or None>
```

## Quality checks (Yes/No)

- Does every AC have at least one test case?
- Is every case traceable to exactly one AC?
- Are test names behavior-based (for example `test_x_returns_y`)?
- Is the framework left undecided when the spec does not name it?
- Is the plan marked Provisional when the spec is not Approved?
- Were zero test code files created?

## Example

Input: spec AC1 "Given a signed-in user with invoice 42, when they request its
PDF, then they receive a PDF of invoice 42." Status: Approved. Framework: pytest.

Output:

```
Test plan for specs/invoice-pdf-download.md — Final
Framework: pytest
| TP1 | AC1 | test_download_own_invoice_returns_pdf | user owns invoice 42 | GET invoice 42 PDF | 200, PDF content type | integration |
Blocked: None
Questions: None
```
