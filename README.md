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

Copy the skill into your project's `.claude/skills/` directory:

```
your-project/
  .claude/
    skills/
      cost-estimate/
        SKILL.md
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

LOC is treated as a proxy (corrected by quality signals, churn, and DRYness), not truth. Overheads compound multiplicatively, not additively. Rates come from WebSearch with versioned fallbacks. Claude-hour ROI uses real `~/.claude/projects/*.jsonl` token usage when available (ground-truth API cost) and git-churn session clustering when not. Every dollar figure is paired with P10/P50/P90. Every strong claim is paired with an assumption the reader can override.

## Credit

This skill is an expanded version of the original idea by **Todd Saunders** ([@toddsaunders](https://x.com/toddsaunders) on Twitter/X).

## License

MIT
