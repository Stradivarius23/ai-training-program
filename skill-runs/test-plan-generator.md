# Skill run: test-plan-generator

- Date: 2026-09-26
- Skill: [skills/test-plan-generator/SKILL.md](../skills/test-plan-generator/SKILL.md)

## Input

- Spec: [specs/sample-health-endpoint.md](../specs/sample-health-endpoint.md)
- Status: Draft
- Test framework: not named in the spec (open question Q6).

## Output

```
Test plan for specs/sample-health-endpoint.md — Provisional
Framework: not decided — blocked by open question Q6
| ID  | AC  | Test name                          | Given               | When                                  | Then                              | Type        |
|-----|-----|------------------------------------|---------------------|---------------------------------------|-----------------------------------|-------------|
| TP1 | AC1 | test_health_returns_200            | service is running  | client requests the health endpoint   | response status code is 200       | integration |
| TP2 | AC2 | test_health_response_has_status_ok | service is running  | client requests the health endpoint   | response contains status value OK | integration |
Blocked:
- TP1, TP2: endpoint path (Q2) and method (Q3) unknown; test type depends on Q6.
- TP2: exact body and content-type assertion depends on Q4.
Questions:
- Q2, Q3, Q4, Q6 from the spec must be answered before tests are written.
- No negative cases added: the spec states no failure behavior (see Q8).
```

## Quality checks

| Check | Answer |
|-------|--------|
| Does every AC have at least one test case? | Yes (AC1 → TP1, AC2 → TP2) |
| Is every case traceable to exactly one AC? | Yes |
| Are test names behavior-based? | Yes |
| Is the framework left undecided when the spec does not name it? | Yes |
| Is the plan marked Provisional when the spec is not Approved? | Yes |
| Were zero test code files created? | Yes (`tests/` holds only `.gitkeep`) |
