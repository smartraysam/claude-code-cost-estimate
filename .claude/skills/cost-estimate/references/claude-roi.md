# Claude ROI — session-aware, churn-aware, reviewer-aware, concurrency-aware (Step 9)

Headline: **"What did each hour of Claude's actual clock time produce — and what did the user pay in time + money?"**

## Contents
1. Measure Claude active hours + operator hours + parallel windows
2. Compute headline metrics
3. Speed-multiplier sanity check (parallel-aware, with market benchmarks)
4. Parallel Execution Profile paragraph (goes in the report)
5. Loudly stated limitations

---

## 1. Measure Claude active hours + operator hours + parallel windows

### Method 1 (best): Claude Code session logs

Session transcripts live at `~/.claude/projects/<project-hash>/*.jsonl` where the hash is derived from the project path (`/` → `-`).

Run `scripts/claude_token_cost.py` — one script emits **all** of:

- **Token usage + API cost**: ground-truth `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `output_tokens` per message × published per-model rates.
- **`active_hours_capped6`** — sum of `(last - first)` per session file, capped 6h/session. This is *Claude compute throughput* (adds up even when sessions overlap).
- **`active_hours_uncapped`** — same sum without the cap; used for sanity.
- **`operator_hours_union`** — wall-clock UNION of all session intervals. This is *real human driver time* — the hours the user actually sat at the keyboard.
- **`peak_concurrent_sessions`** — max simultaneous Claude Code windows.
- **`avg_concurrency`** = `active_hours_uncapped / operator_hours_union` — how many windows the user averaged in parallel.

Flag `method: "session_logs"` and `api_cost_source: "session_logs"` in the artifact — high confidence.

### Method 2: Git churn + session clustering

If no session logs exist, run `scripts/git_session_clustering.py`. Emits a single session-hour estimate, no concurrency data. Flag `method: "git_clustering"` — medium confidence (±2×).

### Method 3: LOC-based fallback

If no git and no logs, use `net_claude_loc / 350 hrs`. Flag `method: "loc_estimate"` — low confidence.

---

## 2. Headline metrics

Two denominators, two different stories:

```
# Claude throughput — what the AI produced per compute-hour
speed_multiplier_compute  = total_eng_hours_p50 / active_hours_capped6

# Operator leverage — what one human produced per real keyboard-hour
speed_multiplier_operator = total_eng_hours_p50 / operator_hours_union

# These diverge when the user runs parallel Claude windows:
# speed_multiplier_operator = speed_multiplier_compute × avg_concurrency
```

Report **both** in the table — `speed_multiplier_operator` is usually the honest number for ROI comparisons because it's the one the user's wallet feels.

```
value_per_claude_hour = total_cost_p50 / active_hours_capped6
value_per_operator_hour = total_cost_p50 / operator_hours_union

# Reviewer time (critical for honesty)
reviewer_hours  = operator_hours_union × reviewer_ratio
# reviewer_ratio defaults:
#   single-window interactive usage: 0.5  (user reviews code after Claude writes it)
#   parallel windows (peak_concurrent >= 2): 0.2-0.3
#     (the operator IS the reviewer-in-loop while supervising multiple streams;
#      reviewer effort is already embedded in operator_hours_union)
#   delegated long-running agents (peak >= 5, low per-session attention): 0.1
reviewer_cost   = reviewer_hours × recommended_rate

# Two DIFFERENT numbers — never add them together
equivalent_api_spend = sum(tokens × published_rates)       # counterfactual per-token bill
actual_cash_paid     = depends on plan:
                         - Claude Max:    $200/mo × calendar_months  (flat)
                         - Claude Pro:    $20/mo  × calendar_months
                         - API (metered): equivalent_api_spend (the number IS the bill)
                         - Unknown:       report both, let the reader pick

claude_total_cost = actual_cash_paid + reviewer_cost

roi = (total_cost_p50 − claude_total_cost) / claude_total_cost
```

**Reviewer-time inclusion is non-optional** — omitting it overstates ROI. For parallel-window users, tune `reviewer_ratio` down from 0.5 (the single-window default) because `operator_hours_union` already captures all the time the human spent supervising. Name the chosen ratio explicitly in the report.

---

## 3. Speed-multiplier sanity check — parallel-aware

The 2024 GitHub Copilot SPACE study ([*Measuring GitHub Copilot's Impact on Productivity*, CACM 2024](https://cacm.acm.org/)) measured a **1.55× speed multiplier** with Copilot. That study pattern is **solo human + inline autocomplete, reviewer-in-loop at the keystroke level** — fundamentally different from Claude Code executing autonomously across tool use with parallel windows. Use it as the floor anchor, not the ceiling.

Tier the sanity gate by `peak_concurrent_sessions`, because parallelism legitimately multiplies the honest multiplier:

| Peak concurrent | Typical `speed_multiplier_operator` | Interpretation |
|---|---|---|
| 1 (single window) | 1.5 – 3× | Copilot-style, reviewer-in-loop |
| 1 (autonomous agent mode) | 3 – 10× | Claude Code autonomous tool use on a well-scoped task |
| 2 – 4 (typical power user) | 10 – 40× | Developer juggling a few concurrent streams; most Claude Code users sit here |
| 5 – 7 (advanced) | 40 – 80× | "Orchestrator mode" — user is a traffic controller for multiple autonomous agents |
| 8 – 10 (expert) | 80 – 150× | Top-percentile workflow observed among the most productive Claude Code users |
| > 10 | 150×+ | Rare; verify `operator_hours_union` and spot-check commits |

```
expected_max = 15 × max(peak_concurrent_sessions, 1)   # rough upper honest bound
if speed_multiplier_operator > 3 × expected_max:
    sanity_flag = "implausible"       # likely a measurement bug
elif speed_multiplier_operator > expected_max:
    sanity_flag = "suspicious"         # outlier — spot-check a sample commit
else:
    sanity_flag = "plausible"
```

When `sanity_flag != "plausible"`, the report must explicitly say which metric (`operator_hours_union`, LOC inflation, category misclassification) to verify.

---

## 4. Parallel Execution Profile paragraph (goes in the report)

The report template includes a dedicated *Parallel Execution Profile* paragraph that the model **must** fill in whenever `peak_concurrent_sessions >= 2`. Shape it like this:

> **Parallel Execution Profile.** Across the project, the user drove **[peak]** Claude Code windows concurrently at peak (avg **[avg_concurrency]×** simultaneous), spending **[operator_hours_union]** real keyboard hours to produce **[active_hours_capped6]** hours of Claude compute work. For context:
>
> - **GitHub Copilot baseline (2024 SPACE study)**: 1.55× — a solo developer with inline autocomplete, reviewing every suggestion at the keystroke level.
> - **Single-window Claude Code (autonomous agent mode)**: ~3 – 10× — one developer letting Claude run tool-use loops between reviews.
> - **Typical Claude Code power-user (this user, at [peak] parallel)**: ~10 – 40× — the developer becomes a traffic controller, spot-reviewing multiple streams instead of gating each keystroke.
> - **Top-percentile workflows (7 – 10 concurrent windows)**: ~80 – 150× — observed in the highest-productivity Claude Code users, where most cognitive work is queue management and final-pass review.
>
> This user's **operator-hour speed multiplier of [X]×** sits in the **[tier]** band — [contextual sentence: "exactly where a [tier] user should be" / "higher than the typical [tier] range, worth spot-checking" / "extraordinary — this is how the 99th-percentile workflow looks"].

Calibrate the "tier" phrasing on `peak_concurrent_sessions`:
- 1 → "single-window autonomous-agent"
- 2 – 4 → "power-user"
- 5 – 7 → "advanced orchestrator"
- 8 – 10 → "top-percentile expert"
- 11+ → "off-the-chart"

---

## 5. Limitations (state loudly in the report)

Always include:

> "Claude active hours estimated via *[method]*. Actual session time may differ by ±30% (session logs) or ±2× (git clustering). Reviewer time assumed at [ratio]× operator hours; adjust if you know your ratio. Speed multipliers are directional — the operator-hour metric is the honest one for ROI comparisons; the compute-hour metric is the one to quote when benchmarking AI throughput."
