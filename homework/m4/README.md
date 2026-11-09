# Module 4 homework: MCP in a DevOps workflow

Success criteria: User request → AGENTS.md → Skill → MCP Tool #1 → MCP Tool #2 → Result

| Step | Where | Evidence |
|------|-------|----------|
| User request | Goal only, no tool names | [skill run: prompt](../../skill-runs/devops-investigate.md#prompt-given-to-the-agent) |
| AGENTS.md | `## MCP Tool Usage`: 5 given rules + 5 own rules, routes deployment problems to the skill | [AGENTS.md](../../AGENTS.md#mcp-tool-usage) |
| Skill | Search tracker → second server → correlate → recommend | [skills/devops-investigate/SKILL.md](../../skills/devops-investigate/SKILL.md) |
| MCP Tool #1 | GitHub: `actions_list`, `get_job_logs`, `list_issues`, `list_pull_requests` | [skill run: tools table](../../skill-runs/devops-investigate.md#tools-selected-and-what-they-returned) |
| MCP Tool #2 | Microsoft 365: `chat_message_search`, `sharepoint_search`, `outlook_email_search` | same table |
| Result | Not tracked; bump `actions/checkout` v4 → v5 (needs approval: `.github/` is protected) | [skill run: output](../../skill-runs/devops-investigate.md#output) |

## Task checklist

1. Connect MCP servers: GitHub and Microsoft 365 are connected as claude.ai
   connectors, not repository files. `get_me` on both succeeded (2026-11-09).
2. MCP rules in AGENTS.md: added, with five rules of our own.
3. MCP skill: `skills/devops-investigate` uses tools from both servers in one task.
4. Agent test: recorded in [skill-runs/devops-investigate.md](../../skill-runs/devops-investigate.md).

## Rerun

In a Claude Code session with both connectors on, send:

> Investigate this deployment problem. Check whether it is already tracked,
> find relevant technical information, and recommend the next action.
