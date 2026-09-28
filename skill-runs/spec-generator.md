# Skill run: spec-generator

- Date: 2026-09-26
- Skill: [skills/spec-generator/SKILL.md](../skills/spec-generator/SKILL.md)
- Purpose of run: smoke test, phase 1 (before approval).

## Input

- Request: "Add a health endpoint that returns HTTP 200 with status OK."
- Slug: `sample-health-endpoint` (file name required by the foundation brief).
- Docs read: `AGENTS.md`, `constitution.md`, `docs/standards.md`.

## Output

### File written: `specs/sample-health-endpoint.md`

```markdown
# Spec: Health endpoint

Status: Draft
<!-- One of: Draft, In Review, Approved, Rejected. Only a human sets Approved or Rejected. -->

## Problem

Operators and tools need a way to check that the service is running. The
request: "Add a health endpoint that returns HTTP 200 with status OK."

## Scope

- One HTTP endpoint that reports the service is running.
- The endpoint returns HTTP status 200 and the status value `OK`.
- Tests that prove the acceptance criteria.

## Out of Scope

- Checks of databases, queues, or other downstream dependencies.
- Metrics, logging, dashboards, or alerting.
- Authentication or rate limiting (unless Q5 decides otherwise).
- Any other endpoint or application feature.

## Requirements

- R1: The service exposes a health endpoint over HTTP.
- R2: A request to the health endpoint returns HTTP status 200.
- R3: The response carries the status value `OK`.

## Acceptance Criteria

- AC1 (R1, R2): Given the service is running, when a client sends a request to
  the health endpoint, then the response status code is 200.
- AC2 (R3): Given the service is running, when a client sends a request to the
  health endpoint, then the response contains the status value `OK`.

## Security and Dependencies

- Security: The endpoint must expose no secrets, versions, hostnames, or
  internal details. Access control not decided — see Q5.
- Dependencies: Not decided — see Q1 and Q6. No dependency may be added until
  this spec is Approved.

## Open Questions

- Q1: Which language, runtime, and HTTP framework should the service use?
  The repository has no stack yet.
- Q2: What is the endpoint path (for example `/health`, `/healthz`, `/status`)?
- Q3: Which HTTP method(s) must it accept (`GET` only, or also `HEAD`)?
- Q4: What is the exact response body and content type — JSON
  `{"status": "OK"}` or plain text `OK`?
- Q5: Must the endpoint be public, or require authentication?
- Q6: Which test framework should be used, and must tests start a real server
  or may they call the handler in-process?
- Q7: Which port and host should the service listen on, and how is it started
  locally?
- Q8: Should "OK" ever change (for example to a failure status), or is the
  response always `OK` while the process is running?

## Human Approval

- Approved by:
- Date:
```

### Reply to the human

> Draft spec written: `specs/sample-health-endpoint.md` (Status: Draft).
> I did not choose a technology stack and did not write code, tests, a plan,
> or tasks. Please answer these open questions:
>
> 1. Q1: Language, runtime, and HTTP framework?
> 2. Q2: Endpoint path?
> 3. Q3: Allowed HTTP method(s)?
> 4. Q4: Exact response body and content type?
> 5. Q5: Public or authenticated?
> 6. Q6: Test framework, and real server or in-process tests?
> 7. Q7: Port, host, and local start command?
> 8. Q8: Is the response always `OK`, or can it report failure?
>
> After answering, please set `Status: Approved` and fill the approval name
> and date. I will stop here until then.

## Quality checks

| Check | Answer |
|-------|--------|
| Is `Status` set to `Draft`? | Yes |
| Is every template section present? | Yes |
| Does every requirement have a Given/When/Then criterion? | Yes (R1, R2 → AC1; R3 → AC2) |
| Is every unstated detail an Open Question rather than a choice? | Yes (Q1–Q8) |
| Is the technology stack left undecided unless the request names it? | Yes |
| Are Human Approval fields blank? | Yes |
| Were zero files outside `specs/` created or changed? | Yes (only `specs/sample-health-endpoint.md`) |
