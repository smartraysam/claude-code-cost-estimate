# [Project Name] — Development Cost Estimate

**Generated**: [date] · **Stack**: [one-line] · **Strategy**: [micro/small/normal/macro] · **Confidence**: [low/medium/high]

## What this number is — and what it isn't

**This is the *replacement cost to rebuild***, not the codebase's market value. It measures what a traditional human team would spend to recreate this code from scratch, starting with specs in hand. It does NOT include:

- Discovery, user research, PMF iteration
- Failed experiments and dead branches not represented in the final code
- Institutional knowledge (what the team learned while building it)
- Customer support feedback loops that shaped edge cases
- Sales, marketing, legal, compliance, infrastructure hosting
- Maintenance past delivery (see 5-year TCO section)

Quoting this number as "what the code is worth" is a category error that has burned people before. If a potential acquirer or investor asks, point them at the range and the *replacement cost* framing — never the single number.

## TL;DR

- **Counted LOC**: [N] ([N] excluded)
- **Human-team hours (P50)**: [N] · P10: [N] · P90: [N]
- **Pre-AI rebuild cost — engineering only (P50)**: **$[X]** at $[rate]/hr
- **Pre-AI rebuild cost — full human team (Growth Co, P50)**: **$[X]**
- **Calendar time if a human team rebuilt it (Lean startup)**: ~[X] months
- **Actual cash paid to Anthropic**: **$[Y]** (based on plan: Max=$200/mo, Pro=$20/mo, API=metered)
- **Equivalent API spend** (counterfactual, from token usage): **$[Z]** — *what the same tokens would have cost at per-token API rates; NOT what you paid if on a subscription plan*
- **Pre-AI ÷ actual-AI cost ratio**: [X]× (*i.e. what a human team would have charged vs what Claude actually spent*)

## Codebase Metrics

- **Total counted LOC**: [N]
  - [Language 1]: [N] · [Language 2]: [N] · …
  - Tests: [N] ([ratio] of source) · IaC/config: [N]
- **Excluded**: [N] (generated: [N], vendored: [N], minified: [N], lockfiles: [N])
- **Quality multiplier**: [X.XX] — [signals: + tests, + types, − no docs, …]
- **Specialized domains**: [list]

## Process Signals (git)

- Project duration: [X] days · Commits: [N] · Contributors: [N]
- Churn: +[adds] / −[dels] (net +[net]) · churn_ratio: [X.XX]
- Process-only estimate (cross-check): ~[N] hours

## Engineering Hours

### Bottom-up (category × rate)

| Category | LOC | Rate (mid) | Hours (P10 / P50 / P90) |
|---|---|---|---|
| … | … | … | … |
| **Base coding** | **[N]** | | **[A] / [B] / [C]** |

### Overhead (compounded, double-counting avoided)

| Factor | Value | Running total |
|---|---|---|
| Base coding | — | [N] hrs |
| × Arch/design (1.15) | +15% | [N] |
| × Debugging (1.28) | +28% | [N] |
| × … | | |
| × Quality multiplier | [X.XX] | [N] |
| **Total engineering** | | **[N] hrs (P50)** |

### Cross-checks

- COCOMO II: KSLOC [N], E [V], EAF [V] → **[N] hours**
- Function Point backfiring: [N] FP × [X] hrs/FP → **[N] hours**
- LOCOMO (LLM regen + review): **[N] hours / $[N]** — the human-premium floor
- Process-signal (git): [N] hours
- Divergence vs bottom-up: **[X]%** → [reconciled number]
- **Agreement**: [high/medium/low]

## Calendar Time

| Company type | Efficiency | Calendar months |
|---|---|---|
| Solo / founder | 70% | [X] |
| Lean startup | 60% | [X] |
| Growth co | 50% | [X] |
| Enterprise | 40% | [X] |

## Market Rates

| Region | Low | Avg | High |
|---|---|---|---|
| Remote (global) | … | … | … |
| Remote (US) | … | … | … |
| SF/NYC onsite | … | … | … |
| [Specialty] | … | … | … |

**Recommended rate**: **$[X]/hr** — [justification]

## Cost Estimate

### Engineering only

| Scenario | Hours | Rate | Cost |
|---|---|---|---|
| P10 (optimistic) | [N] | $[X] | **$[X]** |
| P50 (median) | [N] | $[X] | **$[X]** |
| P90 (pessimistic) | [N] | $[X] | **$[X]** |

### Full team (at P50 engineering)

| Stage | Multiplier | Total cost |
|---|---|---|
| Solo / founder | 1.0× | **$[X]** |
| Lean startup | 1.45× | **$[X]** |
| Growth company | 2.2× | **$[X]** |
| Enterprise | 2.65× | **$[X]** |

## Claude ROI

- **Measurement method**: [session_logs / git_clustering / loc_estimate] — confidence [high/medium/low]
- **Project timeline**: [first] → [last] ([X] days)
- **Git churn**: +[adds] / −[dels] (net +[net])
- **Sessions detected**: [N] · **Peak concurrent windows**: [N] · **Avg concurrency**: [X.XX]×
- **Claude compute hours** (sum, capped 6h/session): [N]
- **Operator hours** (wall-clock union — real keyboard time): [N]
- **Reviewer hours** ([ratio]× operator — tuned for [peak]-window parallel usage): [N]
- **Plan**: [max / pro / api / unknown]
- **Equivalent API spend** (counterfactual, published per-token rates × 11,587 `message.usage` blocks): $[X] — *NOT what you paid if on Max/Pro.*
- **Actual cash paid to Anthropic**: $[X] — flat subscription if on a plan, metered bill if on API
- **Effective plan savings** (equivalent API − actual cash): $[X] — positive = subscription paid off
- **Value produced (P50 full-team)**: $[X]
- **Value per Claude compute hour**: **$[X,XXX]/hr**
- **Value per operator hour**: **$[X,XXX]/hr**
- **Speed multiplier (compute)**: **[X]×** · **Speed multiplier (operator)**: **[Y]×** — sanity: [plausible/suspicious/implausible]
- **Total Claude investment** (actual cash + reviewer time): $[X]
- **ROI**: **[X]×** — every $1 you actually spent → $[X] of human-equivalent value

> *Claude ran ~[compute_h] hours of AI work across ~[operator_h] wall-clock hours of your time at the keyboard (avg [avg_conc]× parallel). Combined output: ~$[X] of professional development value — **$[X,XXX] per operator hour**.*

### Parallel Execution Profile

*Fill this whenever `peak_concurrent_sessions >= 2`. The numbers tell the user how they compare to the rest of the Claude Code market.*

This project was built with **[peak] Claude Code windows concurrently at peak** (avg **[avg_concurrency]×** simultaneous), spending **[operator_hours_union]** real keyboard hours to produce **[active_hours_capped6]** hours of Claude compute work. For context:

| Workflow | Typical speed multiplier | Description |
|---|---|---|
| GitHub Copilot baseline (SPACE 2024) | 1.55× | Solo developer, inline autocomplete, reviewing every suggestion |
| Single-window Claude Code (autonomous) | 3 – 10× | Developer letting Claude run tool-use loops between reviews |
| **Power-user (2 – 4 parallel)** | **10 – 40×** | Developer as traffic controller, spot-reviewing multiple streams |
| Advanced orchestrator (5 – 7 parallel) | 40 – 80× | Most cognitive work is queue management |
| Top-percentile expert (8 – 10 parallel) | 80 – 150× | Observed in the highest-productivity Claude Code users |

This user's **operator-hour speed multiplier of [X]×** sits in the **[tier]** band — [contextual sentence: "exactly where a [tier] user should be" / "higher than the typical [tier] range, worth spot-checking" / "extraordinary — this is how the 99th-percentile workflow looks"].

## Sensitivity

Top 3 drivers of uncertainty:
1. **[Assumption]**: swing [X→Y] → P50 changes by ±$[Z]
2. **[Assumption]**: …
3. **[Assumption]**: …

## External anchors

- **Harvard supply-side ratio** (Hoffmann-Nagle-Zhou 2024): [X.X]× — flag: [normal/too_low/too_high]
- **5-year TCO** (Capers Jones): $[X] — build is ~[X]% of lifetime

## Spot-check (read before trusting the number)

Three things the reader should verify, with a copy-pasteable command for each:

1. **Biggest category is classified correctly.** Show the top-hours category and the files in it — does the label fit?
   ```bash
   find . -name "*.rs" -not -path "*/target/*" | head -20
   ```
   Commonly over-classified: "systems programming" when it's really just `unsafe` wrappers; "ML/AI" when it's pandas glue.

2. **Excluded-vs-counted ratio is sane.** If `excluded_loc > 3 × counted_loc`, the codebase is mostly vendored/generated — re-run after tightening exclusions.
   ```bash
   du -sh node_modules vendor dist build target .venv 2>/dev/null | sort -h
   ```

3. **Process-vs-code signals agree.** If bottom-up is >2× process estimate, one side is wrong.
   ```bash
   git log --oneline | wc -l
   git log --format="%an" | sort -u | wc -l
   git log --format="%ai" | head -1 && git log --format="%ai" | tail -1
   ```

## Assumptions & Limitations

- Rates reflect current market; drift within ~6 months.
- Excludes: marketing, sales, legal, compliance, hosting/infra, ongoing maintenance.
- LOC undercounts dense/complex code and overcounts boilerplate.
- Claude active-hour estimate from [method]; may be off by ±[30%/2×].
- Reviewer time assumed 0.5× Claude hours; your ratio may differ.
- COCOMO EAF collapsed from 17 multipliers to 5 buckets; approximate.
- Full-team costs assume standard org structures.

---

*This report was generated with the `/cost-estimate` Claude Code skill, created by **Julien Barbier**. Find the skill and follow for updates: https://github.com/jbarbier/claude-code-cost-estimate*

<!-- This footer ships in the saved .md file and cost-estimate.json only — strip it from the terminal print. -->
