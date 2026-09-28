# AGENTS.md

Canonical instructions for any AI coding agent working in this repository.
These rules apply to every agent and every tool. Tool-specific files (like
`CLAUDE.md`) only point here.

## Project purpose

This repository is an AI-ready project foundation. It defines how humans and
AI agents propose, approve, build, validate, and review changes. It has
**no technology stack yet**. A stack is chosen only in an approved spec.

## Folder map

| Path | Contents |
|------|----------|
| `AGENTS.md` | This file. Agent rules. |
| `README.md` | Human overview. |
| `CONTRIBUTING.md` | Step-by-step change workflow. |
| `constitution.md` | Seven guiding principles. |
| `docs/standards.md` | Naming, submission, docs, dependency, security, testing rules. |
| `docs/decisions.md` | Decision log. |
| `specs/` | Specifications. `TEMPLATE.md` plus one file per feature. |
| `plans/` | Implementation plans for approved specs. |
| `tasks/` | Task lists for approved plans. |
| `skills/<name>/SKILL.md` | Reusable AI skills. |
| `skill-runs/<name>.md` | Recorded run of each skill. |
| `review/change-template.md` | Review checklist for every change. |
| `scripts/validate.sh` | Repository validation. |
| `src/` | Application code. Empty until a spec is Approved. |
| `tests/` | Tests. Empty until a spec is Approved. |

## Governance documents

- [README.md](README.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [constitution.md](constitution.md)
- [docs/standards.md](docs/standards.md)
- [docs/decisions.md](docs/decisions.md)
- [specs/TEMPLATE.md](specs/TEMPLATE.md)
- [plans/TEMPLATE.md](plans/TEMPLATE.md)
- [tasks/TEMPLATE.md](tasks/TEMPLATE.md)
- [review/change-template.md](review/change-template.md)
- [skills/spec-generator/SKILL.md](skills/spec-generator/SKILL.md)
- [skills/pr-reviewer/SKILL.md](skills/pr-reviewer/SKILL.md)
- [skills/test-plan-generator/SKILL.md](skills/test-plan-generator/SKILL.md)

## Workflow

request → specification → human approval → plan → tasks → implementation →
validation → review

Details: [CONTRIBUTING.md](CONTRIBUTING.md).

## Validation commands

Run from the repository root before every submission:

```sh
bash scripts/validate.sh
```

Expected last line on success: `VALIDATION PASSED`.
When an approved spec adds a stack, its plan must add the exact test and lint
commands here (a protected-path change that needs approval).

## Required rules

Each rule is answered Yes or No. Every answer must be Yes before you submit.

1. Is there an approved spec (`Status: Approved`, human name and date) for any
   feature code you wrote? No feature implementation without an approved spec.
2. Did you run applicable validation, and did it pass, before submitting?
3. Did you keep all secrets out of files, logs, and output, and leave security
   controls and tests at least as strong as before?
4. Did you leave protected paths unchanged, or get explicit human approval?
5. When a requirement was unclear, did you stop and ask instead of guessing?
6. Did you leave approval fields empty for a human? An agent never approves
   its own spec.

## Protected paths

Do not create, edit, rename, or delete these without explicit human approval
recorded in the change description:

- `AGENTS.md`, `CLAUDE.md`, `constitution.md`, `CONTRIBUTING.md`
- `docs/standards.md`, `review/change-template.md`
- `specs/TEMPLATE.md`, `plans/TEMPLATE.md`, `tasks/TEMPLATE.md`
- `skills/*/SKILL.md`
- `scripts/`, `.github/`
- The `Status` and `Human approval` sections of any spec
- Any `.env*` file, key, or credential file

## Secret handling

- Never write a real secret (password, token, API key, private key,
  connection string with credentials) into any file, commit, log, or reply.
- Read secrets only from environment variables named in an approved spec.
- Commit only placeholder examples such as `.env.example` with empty values.
- If you find a secret, stop, do not copy it, and tell a human.

## Stop and ask a human when

- A requirement, acceptance criterion, or scope boundary is unclear.
- A spec has open questions, or is not `Approved`.
- A technology, framework, language, or dependency is not named in an approved spec.
- A change would touch a protected path.
- A change would weaken security, delete or skip tests, or lower validation.
- Documents conflict with each other or with the request.
- Validation fails and the fix is outside approved scope.

When you stop, list the exact questions and wait. Do not continue with guesses.
