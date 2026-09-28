# AI-Ready Project Foundation

A repository foundation where humans and AI agents collaborate through a
spec-driven workflow. It contains governance, templates, validation, and
reusable AI skills. It contains no feature code until a spec is approved.

## Start here

- Agents: read [AGENTS.md](AGENTS.md).
- Humans: read [CONTRIBUTING.md](CONTRIBUTING.md) and [constitution.md](constitution.md).

## Workflow

request → specification → human approval → plan → tasks → implementation →
validation → review

## Validate

```sh
bash scripts/validate.sh
```

Needs only `bash`, `grep`, `find`, and `sed`. No application dependencies.

## Status

- Technology stack: not chosen.
- Pending spec: [specs/sample-health-endpoint.md](specs/sample-health-endpoint.md) (Draft).
