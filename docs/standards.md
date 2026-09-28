# Engineering Standards

Every rule is a Yes/No question. A change passes only if every applicable
answer is Yes.

## Naming

- Are spec, plan, and task files named with the same kebab-case slug
  (`specs/<slug>.md`, `plans/<slug>.md`, `tasks/<slug>.md`)?
- Are skill folders kebab-case and named for what they do?
- Are branches named `<type>/<slug>` where type is `feat`, `fix`, `docs`, or `chore`?

Good: `specs/user-login.md`, `plans/user-login.md`, branch `feat/user-login`
Bad: `specs/Login Spec v2 FINAL.md`, branch `my-changes`

## Change submission

- Does the change link one approved spec (or state "docs/config only")?
- Does the change description contain the completed
  [review checklist](../review/change-template.md)?
- Does each commit message have an imperative summary of 72 characters or fewer?

Good: `Add health endpoint per specs/health-endpoint.md`
Bad: `stuff`, `WIP fixes and also refactor everything`

## Documentation

- Is each document focused on one topic and short enough to read in five minutes?
- Are relative links used, and do they resolve (checked by `scripts/validate.sh`)?
- Are behavior changes reflected in the related spec, README, or AGENTS.md?

Good: "Run `bash scripts/validate.sh`. Expect `VALIDATION PASSED`."
Bad: "Run the usual checks and make sure it works."

## Dependencies

- Is every new dependency named in an approved spec with a reason?
- Is the version pinned?
- Was a standard-library or existing option rejected for a written reason?

Good: spec states "`pytest==8.3.2` — test runner; stdlib `unittest` rejected
because the team already uses pytest fixtures."
Bad: adding a package to a manifest with no spec entry and no version.

## Security

- Are secrets absent from files, commits, logs, and outputs?
- Are secrets read only from environment variables named in the spec?
- Are existing security checks and tests unchanged or stronger?

Good: `token = os.environ["SERVICE_TOKEN"]` with `SERVICE_TOKEN=` in `.env.example`
Bad: `token = "<real token pasted here>"` committed in source

## Testing

- Does every Given/When/Then criterion have at least one test?
- Is each test named after the behavior it checks?
- Do all tests pass locally with the commands in `AGENTS.md`?
- Were zero tests deleted, skipped, or weakened to make validation pass?

Good: `test_health_returns_200_with_status_ok`
Bad: `test1`, or marking a failing test as skipped to get a green run
