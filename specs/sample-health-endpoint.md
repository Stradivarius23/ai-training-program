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
