#!/usr/bin/env bash
# Repository validation. Usage: bash scripts/validate.sh
# Needs only bash, grep, find, sed. Exits non-zero on any failure.
set -u
cd "$(dirname "$0")/.." || exit 1

fail=0
err() { echo "FAIL: $*"; fail=1; }
ok() { echo "ok:   $*"; }

# 1. Required files exist.
required="AGENTS.md README.md CONTRIBUTING.md constitution.md docs/standards.md
docs/decisions.md specs/TEMPLATE.md specs/sample-health-endpoint.md
plans/TEMPLATE.md tasks/TEMPLATE.md review/change-template.md"
for f in $required; do [ -f "$f" ] || err "missing $f"; done
for d in src tests; do [ -d "$d" ] || err "missing directory $d/"; done
ok "required files checked"

# 2. AGENTS.md links every governance document and every skill.
for f in README.md CONTRIBUTING.md constitution.md docs/standards.md docs/decisions.md \
  specs/TEMPLATE.md plans/TEMPLATE.md tasks/TEMPLATE.md review/change-template.md \
  skills/*/SKILL.md; do
  grep -q "($f)" AGENTS.md || err "AGENTS.md does not link $f"
done
ok "AGENTS.md governance links checked"

# 3. Relative markdown links resolve (placeholders with < > are skipped).
tmp=$(mktemp)
while IFS= read -r md; do
  dir=$(dirname "$md")
  grep -o '\]([^)]*)' "$md" | sed 's/^](//; s/)$//; s/#.*//' | while IFS= read -r link; do
    case "$link" in ''|http*|mailto:*|*'<'*) continue ;; esac
    [ -e "$dir/$link" ] || echo "FAIL: broken link in $md -> $link"
  done
done < <(find . -name '*.md' -not -path './.git/*') > "$tmp"
if [ -s "$tmp" ]; then cat "$tmp"; fail=1; fi
rm -f "$tmp"
ok "markdown links checked"

# 4. Specs have a valid status; Approved specs have a human name and date.
approved=0
for s in specs/*.md; do
  [ "$s" = specs/TEMPLATE.md ] && continue
  status=$(sed -n 's/^Status: *//p' "$s" | head -1)
  case "$status" in
    Draft|"In Review"|Rejected) ;;
    Approved)
      grep -Eq '^- Approved by: *[^ <]' "$s" || err "$s Approved without a name"
      grep -Eq '^- Date: *[0-9]{4}-[0-9]{2}-[0-9]{2}' "$s" || err "$s Approved without a date"
      approved=1 ;;
    *) err "$s has invalid Status '$status'" ;;
  esac
  for h in "## Problem" "## Scope" "## Out of Scope" "## Requirements" \
    "## Acceptance Criteria" "## Security and Dependencies" "## Open Questions" "## Human Approval"; do
    grep -q "^$h" "$s" || err "$s missing section '$h'"
  done
  { grep -Eq '^- AC[0-9]+.*Given ' "$s" && grep -q ' when ' "$s" && grep -q ' then ' "$s"; } \
    || err "$s has no Given/When/Then criterion"
done
ok "spec status and sections checked"

# 5. No feature code or tests before an approved spec.
if [ "$approved" -eq 0 ]; then
  extra=$(find src tests -type f ! -name .gitkeep | head -5)
  [ -z "$extra" ] || err "src/ or tests/ has files but no spec is Approved: $extra"
fi
ok "src/ and tests/ gate checked"

# 6. Skills have required sections and a recorded run.
for sk in skills/*/SKILL.md; do
  name=$(basename "$(dirname "$sk")")
  for h in "## Purpose and when to use" "## Required inputs" "## Steps" \
    "## Stop conditions" "## Output format" "## Quality checks (Yes/No)" "## Example"; do
    grep -q "^$h" "$sk" || err "$sk missing section '$h'"
  done
  [ -f "skill-runs/$name.md" ] || err "missing skill-runs/$name.md"
done
for need in spec-generator pr-reviewer test-plan-generator; do
  [ -f "skills/$need/SKILL.md" ] || err "missing skills/$need/SKILL.md"
done
ok "skills checked"

# 7. Review checklist questions match between template and pr-reviewer.
for q in "Is an approved specification linked?" "Is the change within scope?" \
  "Are acceptance criteria covered by tests?" "Did validation pass?" \
  "Are secrets absent?" "Are dependencies justified?" \
  "Are protected paths unchanged or approved?" "Are relevant documents updated?"; do
  grep -qF "$q" review/change-template.md || err "change-template missing: $q"
  grep -qF "$q" skills/pr-reviewer/SKILL.md || err "pr-reviewer missing: $q"
done
ok "review checklist consistency checked"

# 8. Constitution has seven principles, each with "In practice, this means".
n=$(grep -c '^## [0-9]' constitution.md)
p=$(grep -c 'In practice, this means' constitution.md)
[ "$n" -eq 7 ] && [ "$p" -eq 7 ] || err "constitution.md needs 7 principles with 'In practice, this means' (found $n/$p)"
ok "constitution checked"

# 9. No obvious secrets committed.
pattern='(-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|sk-[A-Za-z0-9]{32,}|xox[baprs]-[A-Za-z0-9-]{10,})'
hits=$(grep -rEIl "$pattern" --exclude-dir=.git --exclude=validate.sh . || true)
[ -z "$hits" ] || err "possible secret in: $hits"
envs=$(find . -name '.env*' ! -name '.env.example' -not -path './.git/*')
[ -z "$envs" ] || err "environment file committed: $envs"
ok "secret scan checked"

if [ "$fail" -ne 0 ]; then echo "VALIDATION FAILED"; exit 1; fi
echo "VALIDATION PASSED"
