# Skill: spec-generator

## Purpose and when to use

Turn a feature request into a Draft spec using
[specs/TEMPLATE.md](../../specs/TEMPLATE.md). Use it for every new request
that may need code. It never writes code, tests, plans, or tasks.

## Required inputs

- The request text, exactly as given.
- A feature slug in kebab-case (derive from the request if not given).
- Current repository docs: `AGENTS.md`, `constitution.md`, `docs/standards.md`.

## Steps

1. Read the request. List every noun and verb that implies behavior.
2. Copy the template to `specs/<slug>.md`. Set `Status: Draft`.
3. Write Problem using only facts from the request.
4. Write Scope with only what the request asks for. Put everything else in
   Out of Scope.
5. Write numbered requirements (R1, R2, …) using only stated facts.
6. Write one Given/When/Then criterion per requirement, linked by ID.
7. For every detail the request does not state (technology, path, format,
   auth, dependencies, environments), add an Open Question. Do not pick one.
8. Fill Security and Dependencies. Write "Not decided — see Qn" if unknown.
9. Leave Human Approval blank.
10. Stop. Reply with the spec path, the open questions, and a request for
    human review and approval.

## Stop conditions

- The spec file is written: stop and ask for approval. Do not plan or code.
- The request is empty or contradicts `constitution.md`: stop and ask.
- A spec with the same slug exists: stop and ask whether to update it.

## Output format

1. A file `specs/<slug>.md` matching the template.
2. A reply: spec path, status, numbered open questions, approval request.

## Quality checks (Yes/No)

- Is `Status` set to `Draft`?
- Is every template section present?
- Does every requirement have a Given/When/Then criterion?
- Is every unstated detail an Open Question rather than a choice?
- Is the technology stack left undecided unless the request names it?
- Are Human Approval fields blank?
- Were zero files outside `specs/` created or changed?

## Example

Input: "Let users download their invoice as PDF."

Output (excerpt of `specs/invoice-pdf-download.md`):

```
Status: Draft
## Requirements
- R1: A user can download one of their invoices as a PDF file.
## Acceptance Criteria
- AC1 (R1): Given a signed-in user with invoice 42, when they request its PDF,
  then they receive a PDF file of invoice 42.
## Open Questions
- Q1: Which PDF library or service may be used?
- Q2: Can a user download invoices of other users in their organization?
## Human Approval
- Approved by:
- Date:
```
