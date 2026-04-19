# /cost-estimate — Claude Code Skill

A custom [Claude Code](https://docs.anthropic.com/en/docs/claude-code) slash command that estimates the **replacement cost to rebuild** any codebase with a traditional human team — no AI, just developers, designers, PMs, and meetings.

Open Claude Code in any project, run `/cost-estimate`, and get a full breakdown: P10/P50/P90 ranges, a four-way cross-check (bottom-up × COCOMO II × Function Point × LOCOMO), real Claude token cost from session logs, current market rates, realistic team costs, and external anchors from Harvard (Hoffmann-Nagle-Zhou 2024) and IFPUG (Capers Jones). Prints the full report to the terminal and saves a copy plus a machine-readable `cost-estimate.json` to a temp directory (never the project — safer against accidental commits).

> ⚠ **Read "How to read the report" below before quoting any number.** Replacement cost to rebuild ≠ market value ≠ what it actually cost to build. Three different numbers, often orders of magnitude apart.

## Example Output

![Cost estimate report screenshot](screenshot-claude-code-skill-cost-estimate.png)

## What It Does

The skill acts as a senior software engineering consultant. It:

1. **Measures the codebase properly** — prefers `cloc` / `tokei` / `scc` (fast, accurate language breakdown) and falls back to filtered `find + wc`. Explicitly excludes vendored deps, generated code, minified bundles, and lockfiles.
2. **Detects quality signals** — test ratio, type coverage, docs, CI maturity, observability — applied as a quality multiplier on per-LOC value.
3. **Categorizes code by complexity** — 15 categories with productivity *ranges* (low/mid/high), from simple CRUD to GPU/shader code, compiler tooling, real-time systems, and embedded.
4. **Cross-checks with COCOMO II** — the industry-validated top-down model. If bottom-up and COCOMO disagree by more than 2x, investigates before reporting.
5. **Compounds overhead multipliers correctly** — architecture, debugging, testing, etc. multiply sequentially (not additively), with an explicit formula.
6. **Researches current market rates** — regional breakdowns (global remote, US remote, SF/NYC onsite, specialists).
7. **Accounts for real-world overhead** — meetings, code reviews, Slack, context switching, sprint ceremonies, mapped to realistic coding efficiency by company stage.
8. **Estimates full team cost** — not just engineering, but PM, design, QA, DevOps, tech writing, management, staffed according to company stage.
9. **Computes churn-aware Claude ROI** — uses `git log --numstat` for actual additions/deletions, clusters commits into sessions, computes value per Claude hour and speed multiplier vs. a human team.
10. **Does sensitivity analysis** — surfaces the 2-3 assumptions that move the estimate most.
11. **States limitations loudly** — every report includes confidence level, assumptions, and what's not counted.

### Output Includes

- TL;DR at the top (LOC, hours, cost, calendar time, Claude ROI — in five lines)
- Codebase metrics with excluded-LOC breakdown and a quality multiplier
- Engineering hours as P10/P50/P90 ranges
- COCOMO II cross-check with divergence analysis
- Calendar time across four company types (solo → enterprise)
- Market rate research with regional breakdown
- Full team cost with role-by-role breakdown
- Claude ROI: speed multiplier, cost savings, value per Claude hour, ROI multiple
- Sensitivity analysis (which assumption drives the number)
- Explicit assumptions and limitations
- Machine-readable `cost-estimate.json` artifact

## Installation

Copy the skill into your project's `.claude/skills/` directory. The skill follows [Anthropic's progressive-disclosure layout](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — a slim `SKILL.md` (< 500 lines) plus `scripts/`, `references/`, and `assets/` that load only when the relevant step runs:

```
your-project/
  .claude/
    skills/
      cost-estimate/
        SKILL.md                 # orchestrator (346 lines)
        scripts/                 # executable helpers (LOC count, git signals, Claude token cost, …)
        references/              # methodology tables loaded on demand (COCOMO II, FP, LOCOMO, …)
        assets/                  # report template + JSON artifact schema
```

Or clone this repo and copy the skill folder:

```bash
git clone https://github.com/jbarbier/claude-code-cost-estimate.git
cp -r claude-code-cost-estimate/.claude/skills/cost-estimate your-project/.claude/skills/
```

To install it globally (available in all projects), place it in your home directory:

```bash
cp -r claude-code-cost-estimate/.claude/skills/cost-estimate ~/.claude/skills/
```

### Recommended (optional)

For faster, more accurate LOC counting, install one of:

```bash
# macOS
brew install cloc tokei scc

# Debian/Ubuntu
sudo apt install cloc

# cargo (tokei)
cargo install tokei
```

The skill gracefully falls back to `find + wc -l` if none are installed.

## Usage

Inside Claude Code, simply run:

```
/cost-estimate
```

Claude will analyze the current project and print the full report to your terminal. It also saves a Markdown copy and a machine-readable `cost-estimate.json` to a temp directory — **never to the project directory itself**, so you can't accidentally `git add` and commit a report containing rates, costs, or team numbers.

Output file locations (auto-detected):

- **Linux**: `/tmp/cost-estimate/<project-name>/`
- **macOS**: `/var/folders/…/T/cost-estimate/<project-name>/` (resolved via `tempfile.gettempdir()`)
- **Windows**: `%TEMP%\cost-estimate\<project-name>\`

If you explicitly want the report in the project directory, say "write it here" — otherwise the default is always the temp dir.

## How to read the report

The skill produces a range, not a quote. Before you quote any figure, make sure you understand these four things.

### 1. What the headline number means

**"Replacement cost to rebuild"** — what a traditional human team would spend today to recreate the codebase from scratch, assuming specs already exist.

It is **NOT**:

| Confusion | What it actually is |
|---|---|
| Market value / sale price | Value is what a buyer will pay — could be 10× this or 0 |
| What it cost to build | AI-assisted builds can cost a fraction of the replacement number |
| Total cost of ownership | Build is ~40–50% of 5-year TCO (the report gives a `lifetime_cost_5y` line) |
| A quote you can send a client | Every number has ±30–50% uncertainty baked in |

If a non-technical stakeholder asks "what's our codebase worth?" and you hand them this number, you've just created a misunderstanding. Point them at the *replacement cost* framing, the range, and the "What this does NOT include" block at the top of the report.

### 2. Why you see four different hour estimates

Each cross-checks the others. When they agree, confidence is high. When they disagree, the report tells you which is likely wrong and why.

| Method | What it's good at | What it's bad at |
|---|---|---|
| **Bottom-up** (category × rate) | Handles stack-specific productivity nuance | Anchored on LOC — under-counts dense code, over-counts boilerplate |
| **COCOMO II** | Industry-validated top-down; good for large projects | 17 effort multipliers collapsed to 5 buckets in our version |
| **Function Point backfiring** | User-facing feature density, language-agnostic | Noisy below ~5k LOC |
| **LOCOMO** | What an LLM would cost to regenerate the code today | Assumes a complete spec; undercounts safety-critical domains |

If the four methods agree within ±30%, the report marks confidence **high**. If one is an outlier, it's named. If they all disagree, the report says **low confidence — reconcile first** — don't publish.

### 3. Flags that change how you read the number

Watch for these in the report header — they change the *interpretation* of everything else:

- **`ai_authored_flag: clear`** — the project was built with heavy AI assistance (>2,000 LOC/day net churn). The $X figure is the *hypothetical human rebuild cost*, not what was actually spent. Frame it as "here's what this would cost a human team; here's what Claude actually cost" — never as "we saved $X."
- **`speed_multiplier sanity: implausible`** — we're claiming Claude was >20× faster than a human team. GitHub Copilot's peer-reviewed 2024 study measured 1.55×. If our number is 60×, something is wrong (usually: uncounted review time, inflated bottom-up, or missed sessions). The report disclaims the number automatically — you should too.
- **`harvard_flag: too_high` / `too_low`** — our P50 diverges from the Harvard supply-side anchor (3.5× naive LOC × $0.15) by more than expected. Usually means excluded code leaked back in, or a wrong company-stage multiplier.
- **Three-way / four-way `agreement: low`** — the cross-checks disagree. Fix this before quoting. Don't average four numbers and pretend that's rigor.

### 4. What the number is missing, always

Even a "high confidence" estimate excludes large real costs:

- Discovery, user research, PMF iteration, failed experiments
- Institutional knowledge — what the team learned while building it
- Customer-support-driven edge cases and decisions
- Marketing, sales, legal, compliance, hosting
- Post-delivery maintenance (partially covered by the 5-year TCO line)

The report prints this list front and center. Don't scroll past it.

### Methodology in one paragraph

LOC* is treated as a proxy (corrected by quality signals, churn, and DRYness*), not truth. Overheads compound multiplicatively, not additively. Rates come from WebSearch with versioned fallbacks. Claude-hour ROI* uses real `~/.claude/projects/*.jsonl` token usage when available (ground-truth API cost) and git-churn session clustering when not. Every dollar figure is paired with P10/P50/P90*. Every strong claim is paired with an assumption the reader can override.

## Glossary

Acronyms and jargon used in this README and in the generated report:

- **LOC** — *Lines of Code.* Raw source-line count, excluding comments/blanks/vendored/generated.
- **KSLOC** — *Thousand Lines of Code* (= LOC ÷ 1000). Input unit for COCOMO II.
- **ULOC** — *Unique Lines of Code.* Distinct lines across the codebase, used to measure DRYness.
- **DRYness** — Ratio `ULOC / LOC`. A DRYness of 1.0 means no duplication; 0.6 means 40% of lines are copy-paste.
- **P10 / P50 / P90** — *Percentiles.* P10 = optimistic (only 10% of scenarios come in cheaper), P50 = median, P90 = pessimistic (90% come in cheaper). Standard software-estimation banding.
- **COCOMO II** — *COnstructive COst MOdel II* (Barry Boehm, 1995). Industry-standard parametric top-down model that converts KSLOC into person-months using scale factor `E` and an EAF.
- **EAF** — *Effort Adjustment Factor.* COCOMO II's product of 17 effort multipliers (collapsed to 5 buckets in this skill).
- **Function Points (FP)** — Size metric based on user-visible features, language-agnostic. "Backfiring" converts LOC → FP via the QSM language-specific ratio (C=148, Java=53, Python=21, etc.).
- **LOCOMO** — *LLM cOst MOdel.* Counterfactual: "what would it cost an LLM to re-generate this code today?" (tokens × published API rates + human review time). Popularised by `scc`.
- **SPACE framework** — GitHub's 2024 *Satisfaction, Performance, Activity, Communication, Efficiency* study on Copilot. Produced the peer-reviewed **1.55×** speed-multiplier baseline we sanity-check against.
- **ROI** — *Return on Investment.* Here: `(human rebuild cost − actual Claude cost) ÷ actual Claude cost`.
- **TCO** — *Total Cost of Ownership.* Build + 5 years of maintenance (Capers Jones data: build ≈ 40-50% of 5-year TCO).
- **IFPUG** — *International Function Point Users Group.* Source of the function-point industry benchmarks.
- **QSM** — *Quantitative Software Management.* Publishes the language-to-function-point conversion table backfiring relies on.
- **PMF** — *Product-Market Fit.* The iteration that happens before a codebase even exists; excluded from replacement cost.
- **JSONL** — *JSON Lines* (one JSON object per line). Format of Claude Code's session transcripts at `~/.claude/projects/<hash>/*.jsonl`.
- **Max / Pro / API** — Anthropic subscription tiers. *Max* = $200/mo flat, *Pro* = $20/mo flat, *API* = pay-per-token.
- **Opus / Sonnet / Haiku** — Claude model tiers. Each has its own per-token rate, pulled from Anthropic's published pricing.
- **AI-authored flag** — Derived from `net_LOC / calendar_day`. Over ~2,000 LOC/day is physically impossible for a solo human, so the skill reframes the estimate as a counterfactual ("what humans *would* have cost") rather than elapsed spend.
- **Harvard supply-side anchor** — From Hoffmann, Nagle, Zhou (SSRN 4693148, 2024). Supply-side value of OSS-like codebases averages ~**3.5×** a naive `LOC × $0.15` calculation. Used as a reality check on our P50.
- **Replacement cost to rebuild** — What it would cost a human team to recreate the codebase today given specs. **Not** market value, **not** what it actually cost to build, **not** TCO.

## Credit

This skill is an expanded version of the original idea by **Todd Saunders** ([@toddsaunders](https://x.com/toddsaunders) on Twitter/X).

## Upstream

This skill is structured to conform to [Anthropic's official Agent Skill best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices): `SKILL.md` stays under 500 lines, detailed methodology lives in `references/`, executable helpers live in `scripts/`, and output templates live in `assets/`. If you'd like to see it in the [anthropics/skills](https://github.com/anthropics/skills) repository, upvote or comment on the submission PR.

## License

MIT
