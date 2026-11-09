# Skill run: devops-investigate

- Date: 2026-11-09
- Skill: [skills/devops-investigate/SKILL.md](../skills/devops-investigate/SKILL.md)
- Purpose of run: show that a goal-only prompt makes the agent select tools
  from two MCP servers (GitHub and Microsoft 365) and correlate the results.

## Prompt given to the agent

> Investigate this deployment problem. Check whether it is already tracked,
> find relevant technical information, and recommend the next action.

No tool names were given. The agent chose every tool below.

## Chain

User request → `AGENTS.md` (MCP Tool Usage routes deployment problems to the
skill) → `skills/devops-investigate` → MCP tool #1: GitHub `get_job_logs`
(the evidence) → MCP tool #2: Microsoft 365 `chat_message_search` (internal
knowledge) → Result: not tracked, one recommended next action (see Output).

## Connection check

| Server | Tool | Result |
|--------|------|--------|
| GitHub | `get_me` | Connected as `Stradivarius23`. |
| Microsoft 365 | `get_me` | Connected as the main contributor (DevOps Engineer). |

## Tools selected and what they returned

| # | Server | Tool | Query or ID | Result | How the agent used it |
|---|--------|------|-------------|--------|-----------------------|
| 1 | GitHub | `actions_list` (`list_workflow_runs`) | repo `Stradivarius23/ai-training-program` | 16 runs; newest 10 all `success`. | No red run, so it looked for warnings inside the newest run. |
| 2 | GitHub | `list_issues` | all states | 0 issues. | Nothing tracked yet. |
| 3 | Microsoft 365 | `chat_message_search` | `deployment OR deploy failed`, since 2026-09-01 | No results. | No team discussion of a broken deploy. |
| 4 | Microsoft 365 | `sharepoint_search` | `deployment runbook` | 37 hits; first 10 are training and partner documents, none about this pipeline. | No runbook for this repo. |
| 5 | GitHub | `actions_list` (`list_workflow_jobs`) | run 42596699734 | 1 job `validate` (id 129090972588), all steps `success`. | Picked the job for log reading. |
| 6 | GitHub | `get_job_logs` | job 129090972588, last 60 lines | `VALIDATION PASSED`, then `##[warning]Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4.` | This warning became the problem under investigation. |
| 7 | GitHub (search API via `gh`) | `search/issues` | `node` with `is:issue`, then `is:pull-request` | First call failed (HTTP 422: query needs `is:issue` or `is:pull-request`); retried: 0 and 0. | Failure reported, query fixed, result recorded. |
| 8 | GitHub | `list_pull_requests` | all states | 3 PRs, all merged; none about Node or checkout. | Confirms not tracked in PRs. |
| 9 | Microsoft 365 | `chat_message_search` | `"Node.js 20" OR "actions/checkout" OR "node20"` | No results. | Not discussed in Teams. |
| 10 | Microsoft 365 | `sharepoint_search` | `GitHub Actions Node.js 20 deprecation actions/checkout` | 3 hits, none related. | No internal guidance exists. |
| 11 | Microsoft 365 | `outlook_email_search` | `"Node.js 20" deprecation GitHub Actions` | No results. | No email notice received. |

Verification at the source (web fetch, not MCP, because the GitHub MCP
session is scoped to this repository only):

| Source | Result |
|--------|--------|
| `github.blog` changelog linked in the warning | Failed: host not allowed by the session network policy. Reported, not assumed. |
| `actions/checkout` `v4/action.yml` | `using: node20` |
| `actions/checkout` `v5/action.yml` | `using: node24` |
| `actions/checkout` releases page | Newest major is v7 (v7.0.1). |

## Output

**Problem:** the `validate` workflow passes, but every run warns that
`actions/checkout@v4` targets the deprecated Node.js 20 runtime
(job 129090972588, run 42596699734).

**Already tracked?** No. Issues: 0. Pull requests: 0 (query `node`; 3 merged
PRs listed, none related). Teams: 0. Outlook: 0. SharePoint: no related document.

**Technical facts**

- `.github/workflows/validate.yml` uses `actions/checkout@v4` (repository file).
- `checkout@v4` declares `node20`; `checkout@v5` declares `node24` (action.yml at each tag).
- The runner already forces Node.js 24 on v4 (job log, item 6).

**Correlation**

- The pipeline is green today, so this is a future break, not an outage.
- The warning comes from one action in one workflow; nothing else runs Node.
- Nobody has tracked or discussed it, so no fix is in progress.
- `v5` is the smallest jump that removes the warning; v6 and v7 changes were
  not checked, so they are not recommended without reading their notes.

**Next action:** change `actions/checkout@v4` to `actions/checkout@v5` in
`.github/workflows/validate.yml` and confirm the next run has no warning.
Owner: repository maintainer. Approval needed: Yes, `.github/` is a protected
path. Optional: open a GitHub issue to track it (write action, needs approval).

## Quality checks

| Check | Answer |
|-------|--------|
| Were tools from at least two MCP servers used? | Yes (GitHub: 6 calls, Microsoft 365: 5 calls) |
| Is every fact cited with a server and an ID or URL? | Yes |
| Is every empty search shown with its exact query? | Yes |
| Were zero write actions taken without human approval? | Yes |
| Is there exactly one recommended next action? | Yes |
