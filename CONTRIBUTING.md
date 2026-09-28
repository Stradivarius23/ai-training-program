# Contributing

Every change follows one flow:

request → specification → human approval → plan → tasks → implementation →
validation → review

Rules for agents: [AGENTS.md](AGENTS.md). Conventions:
[docs/standards.md](docs/standards.md).

## 1. Write and approve a specification

1. Copy [specs/TEMPLATE.md](specs/TEMPLATE.md) to `specs/<feature-slug>.md`,
   or use the [spec-generator](skills/spec-generator/SKILL.md) skill.
2. Set `Status: Draft`. Fill Problem, Scope, Out of Scope, Requirements,
   Given/When/Then criteria, Security and dependencies.
3. Write every unclear point under Open Questions. Do not guess answers.
4. Set `Status: In Review` and ask a human to review.
5. A human answers open questions, then sets `Status: Approved` (or
   `Rejected`) and fills the approval name and date.
6. An agent never sets `Approved` and never fills the approval fields.

A spec is approved only if: Status is `Approved`, the approval name and date
are filled by a human, and Open Questions says `None` or lists only resolved items.

## 2. Create a plan and tasks

1. Copy [plans/TEMPLATE.md](plans/TEMPLATE.md) to `plans/<feature-slug>.md`.
   Link the approved spec. Describe the approach using only approved technology.
2. Copy [tasks/TEMPLATE.md](tasks/TEMPLATE.md) to `tasks/<feature-slug>.md`.
   Split the plan into small tasks, each linked to a requirement.
3. Optionally run [test-plan-generator](skills/test-plan-generator/SKILL.md)
   to map criteria to tests.

## 3. Implement and test approved scope

1. Work task by task. Change only files the plan lists.
2. Write a test for every acceptance criterion.
3. If something is not covered by the spec, stop and ask. Do not extend scope.

## 4. Validate and submit a change

1. Run `bash scripts/validate.sh` and any test commands listed in `AGENTS.md`.
   Every command must pass.
2. Copy [review/change-template.md](review/change-template.md) into the change
   description and answer every question with Yes, No, or Not applicable plus
   evidence.
3. Optionally run [pr-reviewer](skills/pr-reviewer/SKILL.md) on the change.
4. Submit on a branch. A human reviews and merges.
