# Constitution

Seven principles that override convenience. If a document conflicts with this
page, this page wins and a human resolves the conflict.

## 1. Specification before implementation

No feature code is written until a human approves a specification.
In practice, this means an agent writes a Draft spec, stops, and starts a plan
only after the spec shows `Status: Approved` with a human name and date.

## 2. Simplicity

The smallest solution that meets the approved requirements is the right one.
In practice, this means no extra features, layers, or dependencies beyond what
the spec requires, and short files with one purpose each.

## 3. Verifiable quality

A change is done only when evidence proves it works.
In practice, this means every acceptance criterion maps to a test, and
`bash scripts/validate.sh` passes before submission.

## 4. Security by default

Every change keeps the system at least as secure as it was.
In practice, this means no secrets in the repository, no weakened checks or
tests, and every new dependency justified in the spec.

## 5. Documented decisions

Every decision that is not obvious is written down where others will find it.
In practice, this means recording choices in the spec, plan, or
`docs/decisions.md`, with the reason and the approver.

## 6. Human control of ambiguity

Humans, not agents, resolve unclear requirements.
In practice, this means an agent records each ambiguity as an open question,
stops, and asks instead of guessing.

## 7. Focused changes

Each change does one approved thing.
In practice, this means a change touches only files needed for its approved
scope and never edits protected paths without explicit approval.
