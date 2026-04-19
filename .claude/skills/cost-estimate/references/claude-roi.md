# Claude ROI — session-aware, churn-aware, reviewer-aware (Step 9)

Headline: **"What did each hour of Claude's actual clock time produce — and what did the user pay in time + money?"**

## Contents
1. Measure Claude active hours (three methods, best signal first)
2. Compute headline metrics
3. Speed-multiplier sanity check (Copilot SPACE anchor)
4. Loudly stated limitations

---

## 1. Measure Claude active hours

### Method 1 (best): Claude Code session logs

Session transcripts live at `~/.claude/projects/<project-hash>/*.jsonl` where the hash is derived from the project path (`/` → `-`).

**Token usage + API cost**: run `scripts/claude_token_cost.py` — it sums `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `output_tokens` per message and multiplies by published per-model rates.

**Active duration**: sum `(last_timestamp - first_timestamp)` per session file, capped at 6 hours per session to avoid counting idle time.

Flag `method: "session_logs"` and `api_cost_source: "session_logs"` in the JSON artifact — high confidence.

### Method 2: Git churn + session clustering

If no session logs exist, run `scripts/git_session_clustering.py` — clusters commits within a 4-hour window and estimates each session's duration from span + density.

Flag `method: "git_clustering"` — medium confidence (±2×).

### Method 3: LOC-based fallback

If no git and no logs, use `net_claude_loc / 350 hrs`. Flag `method: "loc_estimate"` — low confidence.

---

## 2. Headline metrics

```
value_per_claude_hour = total_cost_p50 / claude_active_hours
speed_multiplier      = total_eng_hours_p50 / claude_active_hours

# Honest Claude cost includes USER TIME reviewing/iterating
reviewer_hours  = claude_active_hours × 0.5        # default; typical range 0.3 – 1.0
reviewer_cost   = reviewer_hours × recommended_rate

# Two DIFFERENT numbers — never add them together
equivalent_api_spend = sum(tokens × published_rates)       # counterfactual per-token bill
actual_cash_paid     = depends on plan:
                         - Claude Max:    $200/mo × calendar_months  (flat)
                         - Claude Pro:    $20/mo  × calendar_months
                         - API (metered): equivalent_api_spend (the number IS the bill)
                         - Unknown:       report both, let the reader pick

effective_plan_savings = equivalent_api_spend − actual_cash_paid
                         # positive = subscription paid off; negative = API would be cheaper
claude_total_cost      = actual_cash_paid + reviewer_cost    # use ACTUAL cash, not equivalent

roi = (total_cost_p50 − claude_total_cost) / claude_total_cost
```

**Reviewer-time inclusion is non-optional** — omitting it overstates ROI by 2 – 5×. Name the assumption explicitly:

> "reviewer_time = 0.5× Claude active hours (typical range 0.3 – 1.0×)."

---

## 3. Speed-multiplier sanity check (Copilot SPACE anchor)

GitHub Copilot's randomized study (*Measuring GitHub Copilot's Impact on Productivity*, CACM 2024) measured a **1.55× speed multiplier** with Copilot (55% faster task completion from baseline). Use this as the industry benchmark for honest AI speed-ups.

| Computed `speed_multiplier` | Interpretation |
|---|---|
| < 1.5× | Believable, maybe conservative for Claude on greenfield code |
| 1.5 – 3× | Typical for Claude Code on well-scoped tasks |
| 3 – 8× | Plausible for code-heavy tasks with strong specs |
| 8 – 20× | Suspicious — verify by spot-checking a sample commit |
| > 20× | Almost certainly wrong — see failure modes below |

```
if speed_multiplier > 20: sanity_flag = "implausible"
elif speed_multiplier > 8: sanity_flag = "suspicious"
else:                      sanity_flag = "plausible"
```

When `sanity_flag != "plausible"`, the report must explicitly say:

> "Speed multiplier of [X]× exceeds Copilot's published 1.55× baseline by [Y]×. Treat with skepticism — review Step 9 for measurement errors before quoting."

Common causes of implausible multipliers:
- Hours denominator too small (sessions uncounted)
- Gross LOC inflation (tests/generated leaked in)
- Bottom-up estimate over-inflated

This check prevents the most common lie people tell with cost-estimate tools: claiming a 50× speed multiplier that is actually 3× once reviewer time and uncounted sessions are included.

---

## 4. Limitations (state loudly in the report)

Always include:

> "Claude active hours estimated via *[method]*. Actual session time may differ by ±30% (session logs) or ±2× (git clustering). Reviewer time assumed at 0.5× Claude hours; adjust if you know your ratio. Speed multiplier is directional, not benchmark-grade."
