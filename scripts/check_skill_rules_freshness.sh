#!/usr/bin/env bash
# Check age of memory/anthropic-skill-rules.md; print a reminder if stale.
# Invoked as a SessionStart hook for the cost-estimate repo so Claude notices
# the memory may be out of date and offers to refresh it from the live docs.
set -eu

MEM=/home/gordon/.claude/projects/-home-gordon-cost-estimate/memory/anthropic-skill-rules.md
STALE_DAYS=90   # quarterly refresh cadence

if [ ! -f "$MEM" ]; then
  echo "⚠ Anthropic skill rules NOT in memory yet."
  echo "  Ask Claude: 'fetch + save the Anthropic skill-authoring rules to memory'"
  exit 0
fi

# Pull last_verified from frontmatter; fall back to file mtime
verified=$(awk -F': *' '/^last_verified:/ {print $2; exit}' "$MEM" || true)
if [ -z "${verified:-}" ]; then
  # Fall back to file mtime (YYYY-MM-DD)
  verified=$(date -r "$MEM" +%Y-%m-%d)
fi

today=$(date +%Y-%m-%d)
age_days=$(python3 -c "
from datetime import date
v='$verified'; t='$today'
print((date.fromisoformat(t) - date.fromisoformat(v)).days)
" 2>/dev/null || echo 0)

if [ "${age_days:-0}" -ge "$STALE_DAYS" ]; then
  echo "⚠ Anthropic skill-authoring rules in memory are ${age_days} days old (> ${STALE_DAYS})."
  echo "  Last verified: $verified"
  echo "  Ask Claude: 'refresh the Anthropic skill rules from the live docs'"
  echo "  — it will WebFetch platform.claude.com + github.com/anthropics/skills, diff, and update memory/anthropic-skill-rules.md"
else
  echo "✓ Anthropic skill rules in memory: verified $verified ($age_days days ago, < $STALE_DAYS stale threshold)"
fi
