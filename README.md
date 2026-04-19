# /cost-estimate — Claude Code Skill

A custom [Claude Code](https://docs.anthropic.com/en/docs/claude-code) slash command that analyzes any codebase and estimates what it would have cost to build with a traditional human team — no AI, just developers, designers, PMs, and meetings.

Open Claude Code in any project, run `/cost-estimate`, and get a full breakdown — with ranged estimates (P10/P50/P90), a COCOMO II cross-check, current market rates, realistic team costs, and a churn-aware Claude ROI number. Also writes a machine-readable `cost-estimate.json` artifact.

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

Claude will analyze the current project and produce a detailed cost report plus a `cost-estimate.json` artifact.

## Methodology Notes

This skill produces a **range**, not a quote. LOC is treated as a proxy — corrected by quality signals and cross-checked against COCOMO II. Every number is ranged. Every strong claim is paired with an explicit assumption.

Limitations it acknowledges in every report:
- Rates drift over time
- Excludes marketing, sales, legal, compliance, hosting, and ongoing maintenance
- Dense/complex code is undercounted by LOC; boilerplate is overcounted
- Claude's active-hour estimate from commit clustering may be off by 2-3x

## Credit

This skill is an expanded version of the original idea by **Todd Saunders** ([@toddsaunders](https://x.com/toddsaunders) on Twitter/X).

Original post: [https://x.com/toddsaunders/status/2029594318361571497](https://x.com/toddsaunders/status/2029594318361571497?s=20)

## License

MIT
