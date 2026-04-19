---
name: cost-estimate
description: Estimate what a codebase would have cost to build with a traditional human team. Combines LOC analysis, git-process signals, COCOMO II cross-check, market rates, organizational overhead, and Claude-session-aware ROI. Produces P10/P50/P90 ranges with explicit assumptions, spot-check guidance, and a machine-readable artifact.
---

# Cost Estimate Command

You are a senior software engineering consultant producing a defensible cost estimate for the current codebase.

## Philosophy (read first, do not skip)

**This skill estimates "replacement cost to rebuild"** — what it would cost a traditional human team to recreate this codebase from scratch today, starting from specs that already exist. It is NOT market value. It is NOT a quote. It does NOT capture discovery time, failed experiments, PMF iteration, institutional knowledge, or the customer-support feedback loop that shaped what's in the code.

Say this explicitly in the report — in the TL;DR, not buried. Readers (especially non-technical ones) will mistake the number for "what this codebase is worth," and the difference between those two things can be an order of magnitude in either direction.

This skill produces a *range*, not a quote. Internalize these rules:

1. **LOC is a proxy.** Ten lines of dense regex ≠ ten lines of boilerplate. Cross-validate with process signals (git history) and a top-down model (COCOMO II).
2. **Exclude anything humans didn't write.** Generated code, vendored deps, minified bundles, lockfiles, binary blobs — filter before counting.
3. **Every number gets a range.** P10 (optimistic) / P50 (median) / P90 (pessimistic). Single-point estimates misrepresent confidence.
4. **Two kinds of signals.** *Code signals* = LOC + complexity + quality. *Process signals* = commits, contributors, duration, churn. Use both; when they disagree, investigate.
5. **Don't double-count.** A well-tested codebase earns a quality bump *or* a smaller integration-test overhead — not both. The checklist below enforces this.
6. **Compound overheads.** Architecture, debugging, review, docs multiply sequentially on base coding time — they don't sum.
7. **Size-aware.** Micro projects (<500 LOC) don't need 10-page reports. Macro projects (>500k LOC) need monorepo decomposition.
8. **State your limits.** Every report must list what's counted, what's excluded, what's fragile, and what the reader should spot-check.

If you catch yourself writing a single dollar figure without a range, stop and add one. If you find yourself reporting four significant figures of precision, drop to two — overly precise numbers signal false confidence.

---

## Step 0: Pick a strategy (size-aware)

Before measuring, decide which playbook applies. Run a size sniff — try counters first, fall back to filtered `wc`:

```bash
# Try cloc, tokei, or scc for a fast language-aware total
cloc --vcs=git --quiet . 2>/dev/null | awk '/SUM:/ {print $NF}' && exit 0
tokei --output=json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['Total']['code'])" && exit 0
scc --format=json 2>/dev/null | python3 -c "import sys,json; print(sum(l['Code'] for l in json.load(sys.stdin)))" && exit 0

# Fallback: count LINES (not files) in common source types, with exclusions
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.py" \
  -o -name "*.go" -o -name "*.rs" -o -name "*.java" -o -name "*.rb" \
  -o -name "*.php" -o -name "*.swift" -o -name "*.kt" -o -name "*.c" \
  -o -name "*.cpp" -o -name "*.h" -o -name "*.hpp" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*" \
  -not -path "*/dist/*" -not -path "*/build/*" -not -path "*/vendor/*" \
  -not -path "*/.venv/*" -not -path "*/__pycache__/*" -not -path "*/target/*" \
  -print0 | xargs -0 wc -l 2>/dev/null | awk 'END{print $1}'
```

| Project size | Strategy | Report shape |
|---|---|---|
| **Micro** (<500 LOC) | Nominal estimate only | One paragraph + one line item. Skip Steps 4 (COCOMO), 8 (full team), 10 (sensitivity). Output: "~X days of senior dev work; ~$Y-Z at typical rates; confidence: low." |
| **Small** (500-10k LOC) | Full methodology, short report | Keep all steps; drop Step 8 role-by-role table (keep stage totals only); single-sentence sensitivity. |
| **Normal** (10k-500k LOC) | Full skill, full report | All steps, all tables. Default. |
| **Macro** (>500k LOC) | Decompose first | Break by top-level directory/service; run the full skill per subsystem; sum and report per-subsystem + aggregate. Don't categorize 500k lines in one pass. |

State which strategy you chose and why at the top of the report.

---

## Step 1: Measure the codebase (code signals)

### 1a. Prefer a real counter

Try these tools in order — each is fast and handles exclusions properly:

```bash
cloc --vcs=git .                           # best: language + comment/blank split
tokei --exclude '**/node_modules/**' .     # very fast Rust alternative
scc .                                       # similar, with built-in complexity estimate
```

If none is installed, fall back to a filtered `find + wc`:

```bash
find . -type f \
  \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \
     -o -name "*.py" -o -name "*.go" -o -name "*.rs" -o -name "*.java" \
     -o -name "*.rb" -o -name "*.php" -o -name "*.swift" -o -name "*.kt" \
     -o -name "*.cpp" -o -name "*.cc" -o -name "*.c" -o -name "*.h" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*" \
  -not -path "*/dist/*" -not -path "*/build/*" \
  -not -path "*/vendor/*" -not -path "*/.venv/*" \
  -not -path "*/__pycache__/*" -not -path "*/target/*" \
  -not -path "*/.next/*" \
  | xargs wc -l
```

### 1b. DRYness / ULOC (copy-paste deflator)

Dense repos with copy-pasted blocks inflate LOC by 10-30%. If `scc` is available it reports ULOC (unique lines of code) in JSON; use the ratio:

```bash
scc --format=json . 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
total = sum(l['Code'] for l in d)
uniq  = sum(l.get('ULOC', l['Code']) for l in d)  # ULOC = unique LOC across files
print(f'SLOC:{total} ULOC:{uniq} DRYness:{uniq/total:.2f}')
"
```

Apply a deflator to base hours:
```
dryness_deflator = 1 - (1 - DRYness) * 0.5       # DRYness=1.0 → no deflate; 0.6 → 0.80×
```
If DRYness can't be computed (no `scc`), skip — don't invent a number. Note it in the report.

### 1c. Explicit exclusions (do NOT count)

Report these separately as "excluded LOC" for transparency:

- **Vendored deps**: `node_modules/`, `vendor/`, `.venv/`, `third_party/`, `target/`, `dist/`, `build/`
- **Generated code**: `*.pb.go`, `*_pb2.py`, `*.g.dart`, `*.freezed.dart`, `*_generated.*`, OpenAPI-generated clients, Prisma client, `schema.graphql` types. Detect by header tags: `// Code generated by …`, `@generated`, `DO NOT EDIT`.
- **Minified / bundles**: `*.min.js`, `*.min.css`, sourcemaps, webpack chunks
- **Lockfiles**: `package-lock.json`, `yarn.lock`, `Cargo.lock`, `poetry.lock`, `go.sum`, `Gemfile.lock`
- **Binary / assets**: images, fonts, PDFs, videos, `*.wasm`
- **Framework auto-migrations** (count intent, not verbosity)

### 1d. Detect quality signals (quality_multiplier, 0.7-1.3)

Applied to *per-LOC value*, not to hours. Max one bump per signal; sum capped at +30% / -30%.

| Signal | How to detect | Effect |
|---|---|---|
| Test coverage ratio | `test_LOC / source_LOC > 0.5` | +10% |
| Type safety | TS strict, mypy strict, Go, Rust, Kotlin | +5% |
| Documentation | README >1k chars, inline docs, ADRs | +5% |
| CI/CD maturity | `.github/workflows/` with actual jobs | +5% |
| Observability | logging/tracing/metrics libs | +5% |
| Security hardening | auth, secrets mgmt, input validation | +5% |
| No tests / untyped / no CI | per-signal | -5% each, floor 0.7 |

### 1e. Detect the stack

Examine: `package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, `Gemfile`, `pom.xml`, `build.gradle`, `Dockerfile`, `docker-compose.yml`, `.github/workflows/`, `terraform/`, `k8s/`, framework configs.

Output a one-paragraph stack summary before moving on.

---

## Step 2: Gather process signals (git history)

Process signals cross-validate LOC and reveal where effort actually went. If the project has no git history, note that and skip to Step 3 with lowered confidence.

### 2a. Commit activity

```bash
# Project duration and commit count
git log --format="%ai" | sort | awk 'NR==1{first=$0} END{print "first:", first, "last:", $0, "count:", NR}'

# Unique contributors
git log --format="%ae" | sort -u | wc -l

# Churn totals (gross additions / deletions / net)
git log --numstat --pretty=tformat: \
  | awk '{adds += $1; dels += $2} END {printf "added:%d deleted:%d net:%d churn_ratio:%.2f\n", adds, dels, adds-dels, (dels>0?adds/dels:0)}'
```

Record:
- `first_commit_date`, `last_commit_date`, `project_duration_days`
- `commit_count`, `contributor_count`
- `gross_adds`, `gross_dels`, `net_adds`, `churn_ratio = adds/dels`

### 2b. What the signals mean

| Signal | Interpretation |
|---|---|
| `churn_ratio` > 2.0 | Heavy rework — add 15% to Total hours to reflect iteration cost the LOC count misses |
| `contributor_count` >= 3 | Real team; coordination overhead already implicit — don't inflate further |
| `commit_count` < 10 with >5k LOC | Likely a one-shot import; LOC may overstate bespoke work |
| `project_duration_days` short vs LOC | Heavy AI/automation assist — flag for ROI step |

### 2c. AI-authored detector

When net LOC added per calendar day is impossibly high, the project was written with heavy AI assistance. This radically changes how to *interpret* the human-cost estimate:

```
loc_per_day = net_adds / max(project_duration_days, 1)
```

| `loc_per_day` | Interpretation | Effect on report |
|---|---|---|
| < 100 | Normal human pace | No flag |
| 100-500 | Productive / small team | No flag |
| 500-2000 | Likely AI-assisted | Flag: "human-cost is a counterfactual, not elapsed time" |
| 2000+ | Clearly AI-assisted / one-shot import | Flag strongly; Claude ROI section leads the report |

**Crucial distinction**: when AI-authored, the bottom-up / COCOMO / FP numbers are **hypothetical human rebuild costs**, not what the project took in calendar time. The report must explicitly say: *"This codebase was built in [X] calendar days with AI assistance. The $[Y] figure is what a human team *would* cost to rebuild it from scratch — the actual cost-to-build was a fraction."*

Without this framing, readers mistake the cost estimate for elapsed spend, generating either false shock ("I didn't pay $500k!") or false precision ("we saved exactly $Y"). Frame it correctly.

### 2d. Process signals cross-check

A standalone "process-only" sanity estimate:

```
process_hours ≈ commit_count × avg_commit_hours
  where avg_commit_hours ≈ 0.5 (small commits) to 3.0 (large rewrites)
```

Use this only as a *bounds check*: if your Step 4 total is <0.3× or >3× the process estimate, something is off (likely misclassification or excluded/generated code leaked in).

---

## Step 3: Categorize code & calculate base hours (with ranges)

A senior dev (5+ years) ships this many meaningful lines per hour:

| Category | Low (→ P90 hrs) | Mid (P50) | High (→ P10 hrs) | Examples |
|---|---|---|---|---|
| Simple CRUD/boilerplate | 30 | 40 | 50 | REST endpoints, form handlers, basic UI |
| Standard business logic | 20 | 25 | 30 | Services, controllers, data flow |
| Complex algorithms/state | 15 | 20 | 25 | Search, optimization, workflows |
| Frontend UI/UX | 20 | 28 | 35 | Components, layouts, interactions |
| API integrations | 15 | 20 | 25 | SDK wrappers, OAuth, webhooks |
| Database/ORM | 20 | 25 | 30 | Migrations, queries, schema |
| Systems programming | 10 | 15 | 20 | OS-level, drivers, memory mgmt |
| GPU/shader | 10 | 15 | 20 | CUDA, Metal, Vulkan, compute |
| Compiler/language tooling | 8 | 12 | 15 | Parsers, ASTs, codegen |
| Real-time/streaming | 10 | 15 | 20 | WebSocket, audio/video, events |
| Security/crypto | 10 | 15 | 20 | Auth, encryption, certs |
| ML/AI pipeline | 10 | 15 | 20 | Training, data pipelines, inference |
| Infrastructure as Code | 15 | 20 | 25 | Terraform, k8s, CI/CD |
| Embedded/firmware | 8 | 12 | 15 | Hardware, RTOS, bare-metal |
| Comprehensive tests | 25 | 32 | 40 | Unit, integration, e2e |

**Formula per category**:
```
hours_P50 = LOC / rate_mid
hours_P10 = LOC / rate_high   (optimistic → fewer hours)
hours_P90 = LOC / rate_low    (pessimistic → more hours)
```

Sum across categories → **Base Coding Hours (P10 / P50 / P90)**.

When reporting, show which files/directories fell into each category so the reader can audit the classification.

### Step 3b: Per-feature / per-directory breakdown (user-asked, high signal)

Users asked for this repeatedly (scc #698, Faros/Workweave ROI posts): "what did the checkout flow cost?" not just "what did the whole repo cost?".

For any top-level directory with >5% of total counted LOC, compute a sub-estimate and report it alongside the aggregate:

```bash
# Per-top-level-directory LOC
for d in */; do
  count=$(find "$d" -type f \( -name "*.ts" -o -name "*.py" -o -name "*.go" \) \
    -not -path "*/node_modules/*" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
  echo "$d $count"
done | sort -k2 -n -r | head -15
```

Report a per-feature table with its own hours/cost, still showing the P50 range:

| Directory | LOC | % of total | Hours (P50) | Cost (P50) |
|---|---|---|---|---|
| `src/checkout/` | 8,400 | 24% | 420 | $40k |
| `src/inventory/` | 6,100 | 17% | 305 | $29k |
| ... | | | | |

### Step 3c: Scoped mode (`--since <commit>` or `--path <dir>`)

When the user invokes `/cost-estimate` with an argument like `--since abc123` or `--path src/checkout/`, restrict the entire analysis to that slice:

- `--since <commit>`: use `git log <commit>..HEAD --numstat` and `git diff <commit>..HEAD --numstat` to scope LOC + churn to changes since that commit
- `--path <dir>`: restrict Steps 1-3 to that subdirectory; still apply full overhead + rates

This unlocks "what did this quarter cost?" and "what did this feature cost?" use cases that competitors don't deliver. Preserve every other step — the report reads the same, just for a subset.

---

## Step 4: COCOMO II cross-check

Industry-validated top-down sanity check.

```
Effort_person_months = A × (KSLOC)^E × EAF
  A     = 2.94
  E     = 0.91-1.23 (use 1.0 nominal)
  EAF   = product of 17 effort multipliers (simplified below)
  KSLOC = source LOC / 1000 (excluding generated/vendored)

hours = person_months × 152
```

**Quick EAF table** (collapsed from 17 multipliers into 4 buckets):

| Project type | E | EAF |
|---|---|---|
| Simple CRUD web app | 0.95 | 0.7 |
| Standard SaaS product | 1.00 | 1.0 |
| Platform / infrastructure | 1.10 | 1.5 |
| Systems / compiler / crypto-heavy | 1.15 | 2.0 |
| Safety-critical / regulated | 1.20 | 2.5 |

Compare COCOMO to Step 3:

- **Within 30%** → good; report Step 3 number
- **30-100% divergence** → report both; take geometric mean: `sqrt(bottom_up × cocomo)`
- **>2x divergence** → **stop and investigate** before reporting. Likely causes: wrong category weighting, generated code leaked in, wrong E/EAF. Do not publish mismatched numbers.

---

## Step 4a: Function Point backfiring (fourth cross-check)

Function Points (FP) size software by user-visible functionality, independent of programming language. *Backfiring* reverses the calculation: convert LOC → FP using QSM's language-specific ratio, then apply an FP-per-hour productivity to get hours.

```
LOC_per_FP        # language-specific (QSM table)
Function_Points   = KSLOC × 1000 / LOC_per_FP
hours_per_FP      = 8-12 (industry average; domain-adjusted below)
FP_hours          = Function_Points × hours_per_FP
```

**QSM language conversion table** (abbreviated — see qsm.com/resources/function-point-languages-table for full list):

| Language | LOC per FP | Notes |
|---|---|---|
| Assembly | 320 | |
| C | 148 | |
| C++ | 59 | |
| C# | 59 | |
| Java | 53 | |
| Go | 38 | modern, concise |
| JavaScript | 47 | |
| TypeScript | 43 | types compress some |
| Python | 21 | very expressive |
| Ruby | 25 | |
| Rust | 39 | expressive + safe |
| Swift | 38 | |
| Kotlin | 43 | |
| SQL | 13 | declarative |
| HTML/CSS (treated as FP proxy) | 34 | |

**Hours-per-FP by domain**:
- Data entry / simple CRUD: 6-8 hrs/FP
- Typical business app: 8-12 hrs/FP
- Real-time / embedded: 12-18 hrs/FP
- Systems / safety-critical: 15-25 hrs/FP

Backfiring gives a **fourth independent number**. Convert FP_hours to P10/P50/P90 by varying `hours_per_FP` at the bracket ends.

**Why this helps**: COCOMO anchors on LOC with scale drivers; Function Points anchor on *user-facing features*. Disagreement between the two reveals whether the codebase has lots of internal plumbing (low FP per LOC) or lots of user-facing features (high FP per LOC) — useful diagnostic information for the spot-check.

---

## Step 4b: LOCOMO — LLM-regeneration cost (counterfactual)

COCOMO answers "what did humans cost to build this?". LOCOMO (popularised by `scc`) answers the counterfactual: **"what would it cost an LLM to re-generate this from spec today?"** — a useful floor for Claude-ROI discussions.

```
tokens_per_loc        ≈ 4           # empirical: ~4 tokens per line of code for generation
iteration_factor      = 3           # typical: 3 generation passes before acceptance
input_prompt_overhead = 2           # spec + context tokens per code token
regen_tokens          = SLOC × tokens_per_loc × (1 + input_prompt_overhead) × iteration_factor

# Claude rates (Opus 4.7, 2026-04): input $15/Mtok, output $75/Mtok; assume 10% input / 90% output
api_cost = regen_tokens × (0.1 × 15 + 0.9 × 75) / 1_000_000   # ≈ $0.069 per token mix

# Human review time to accept LLM output
review_hours          = SLOC / 1000   # ~1 hr per KLOC to read/accept generated code
review_cost           = review_hours × recommended_rate

locomo_cost_usd       = api_cost + review_cost
locomo_hours          = review_hours          # the only *human* hours LOCOMO implies
```

**Report three numbers side by side** in the final output:

| Method | Hours | USD | Interpretation |
|---|---|---|---|
| COCOMO II (top-down, human) | [H1] | [$1] | Traditional human build cost |
| Bottom-up (Step 3+5) | [H2] | [$2] | Category-rate, human build cost |
| **LOCOMO (LLM regen + review)** | [H3] | [$3] | **Floor: what re-generating costs today** |

The ratio `COCOMO_cost / LOCOMO_cost` is a "human premium" multiple. If a codebase costs $500k by COCOMO and $15k by LOCOMO, the **33× human premium** is where Claude ROI actually comes from; flag it explicitly in the Claude ROI section.

Caveats: LOCOMO assumes a complete spec exists (it usually doesn't); it ignores novel-problem effort; it undercounts domains where correctness is load-bearing (crypto, embedded, safety-critical). Never publish LOCOMO *alone* — only alongside COCOMO and bottom-up.

---

## Step 5: Overhead multipliers (compounding, no double-count)

Apply **multiplicatively** and follow this rule: **if a quality signal already bumped per-LOC value in Step 1c, reduce the related overhead rate to the low end** to avoid double counting.

```
Total_Eng_Hours = Base_Coding_Hours
                × (1 + arch_design)       // 0.15-0.20
                × (1 + debugging)          // 0.25-0.30
                × (1 + code_review)        // 0.10-0.15
                × (1 + documentation)      // 0.10-0.15   ← use low end if quality bonus for docs
                × (1 + integration_test)   // 0.20-0.25   ← use low end if quality bonus for tests
                × (1 + learning_curve)     // 0.10-0.20 (only for specialized stacks)
                × (1 + devops_setup)       // 0.05-0.10   ← use low end if quality bonus for CI
                × (1 + churn_adjustment)   // 0 by default;
                                           // +0.15 if churn_ratio > 2.0 AND contributor_count < 3
                                           // (skip when churn is normal team iteration, not rework)
                × quality_multiplier       // 0.7 - 1.3 from Step 1c
```

Apply to P10/P50/P90 each → **Total Engineering Hours (P10 / P50 / P90)**.

Sanity check: the stacked overhead (before `quality_multiplier`) typically falls **1.8×-2.6×** base. Outside that range → investigate.

---

## Step 6: Market rates

Use WebSearch for **current-year** rates. Rotate queries; adapt to detected stack:

- `"senior [primary_language] developer hourly rate 2026"`
- `"senior [framework] contractor rate 2026 United States"`
- `"[specialist_domain] developer freelance rate 2026"`
- `"software engineer hourly rate [city] 2026"` for regional anchor

Collect 3-5 data points. Report regionally:

| Region | Low | Avg | High | Notes |
|---|---|---|---|---|
| Remote (global) | | | | LATAM, Eastern Europe, SE Asia |
| Remote (US) | | | | Mid-tier US markets |
| SF/NYC onsite | | | | Premium markets |
| Specialist (e.g. Rust, CUDA, Solidity) | | | | Niche premium |

**Fallback** (if WebSearch unavailable or returns obvious rot): use these 2026 anchors and note "rates from skill defaults, not live search":

- Generalist senior: $75-150/hr (US remote), $150-250/hr (SF/NYC), $35-75/hr (offshore)
- Specialist (Rust, ML infra, GPU, crypto): +30-50%

Pick a **Recommended Rate** with one-sentence justification.

---

## Step 7: Organizational overhead → calendar time

Developers do not code 40 hours per week.

| Company type | Coding efficiency | Focused coding hrs/week |
|---|---|---|
| Solo / founder | 65-75% | 26-30 |
| Lean startup | 55-65% | 22-26 |
| Growth company | 45-55% | 18-22 |
| Enterprise | 35-45% | 14-18 |
| Large bureaucracy | 25-35% | 10-14 |

```
calendar_weeks  = Total_Eng_Hours / (40 × efficiency)
calendar_months = calendar_weeks / 4.33
```

Report across all five company types.

---

## Step 8: Full team cost

Engineering doesn't ship alone. Role ratios (fraction of engineering hours) and rates:

| Role | Ratio | Typical Rate |
|---|---|---|
| Product Management | 0.25-0.40 | $125-200/hr |
| UX/UI Design | 0.20-0.35 | $100-175/hr |
| Engineering Management | 0.12-0.20 | $150-225/hr |
| QA/Testing | 0.15-0.25 | $75-125/hr |
| Project/Program Mgmt | 0.08-0.15 | $100-150/hr |
| Technical Writing | 0.05-0.10 | $75-125/hr |
| DevOps/Platform | 0.10-0.20 | $125-200/hr |

Team composition by stage (approx. engineering-cost multipliers):

| Stage | Multiplier | Staffed roles |
|---|---|---|
| Solo/founder | 1.0× | Eng only |
| Lean startup | ~1.45× | Eng + light PM/design/DevOps |
| Growth company | ~2.2× | Core team, no program mgmt |
| Enterprise | ~2.65× | All roles |

Compute full-team cost at engineering P50 for each stage.

---

## Step 9: Claude ROI (session-aware, churn-aware, reviewer-aware)

The headline: **"What did each hour of Claude's actual clock time produce — and what did the user pay in time + money?"**

### 9a. Measure Claude active hours (best signal first)

**Method 1 (best): Claude Code session logs.** If the project was built with Claude Code, session transcripts live at `~/.claude/projects/<project-hash>/*.jsonl` (the hash is derived from the project path, usually `-<path-with-dashes>`).

```bash
# Find the project's Claude session directory
PROJ_HASH=$(echo "$PWD" | sed 's|/|-|g')
SESSIONS_DIR=~/.claude/projects/${PROJ_HASH}
ls -la "$SESSIONS_DIR" 2>/dev/null

# Compute total session duration from transcript timestamps
find "$SESSIONS_DIR" -name "*.jsonl" -exec sh -c '
  head -1 "$1" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get(\"timestamp\",\"\"))"
  tail -1 "$1" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get(\"timestamp\",\"\"))"
' _ {} \; 2>/dev/null
```

If session logs exist, compute `claude_active_hours` as the sum of (last - first timestamp) per session file, capped per session at 6 hours to avoid counting idle time. Flag `method: "session_logs"` in the JSON artifact with high confidence.

**Also extract real token usage and cost** (preferred over heuristics). Each assistant message in the JSONL has a `message.usage` object with `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `output_tokens`:

```bash
python3 <<'PY'
import glob, json, os
PROJ_HASH = os.getcwd().replace('/', '-')
SESSIONS_DIR = os.path.expanduser(f'~/.claude/projects/{PROJ_HASH}')
# Published rates as of 2026-04 (Opus 4.7), per 1M tokens
RATES = {
    'opus':    {'in': 15.00, 'cache_write': 18.75, 'cache_read': 1.50, 'out': 75.00},
    'sonnet':  {'in':  3.00, 'cache_write':  3.75, 'cache_read': 0.30, 'out': 15.00},
    'haiku':   {'in':  0.80, 'cache_write':  1.00, 'cache_read': 0.08, 'out':  4.00},
}
totals = {'in':0, 'cache_write':0, 'cache_read':0, 'out':0, 'cost_usd':0.0, 'messages':0}
for f in glob.glob(f'{SESSIONS_DIR}/*.jsonl'):
    for line in open(f):
        try: d = json.loads(line)
        except: continue
        msg = d.get('message', {})
        u = msg.get('usage')
        if not u: continue
        model = msg.get('model', '')
        tier = 'opus' if 'opus' in model else ('haiku' if 'haiku' in model else 'sonnet')
        r = RATES[tier]
        ti = u.get('input_tokens', 0)
        tcw = u.get('cache_creation_input_tokens', 0)
        tcr = u.get('cache_read_input_tokens', 0)
        to = u.get('output_tokens', 0)
        cost = (ti*r['in'] + tcw*r['cache_write'] + tcr*r['cache_read'] + to*r['out']) / 1_000_000
        totals['in'] += ti; totals['cache_write'] += tcw
        totals['cache_read'] += tcr; totals['out'] += to
        totals['cost_usd'] += cost; totals['messages'] += 1
print(json.dumps(totals, indent=2))
PY
```

This produces ground-truth API cost instead of the `$0.50 × commit_count` heuristic. Use it for `api_cost` in Step 9b; flag `api_cost_source: "session_logs"` with high confidence. Fall back to the heuristic only if session logs are absent.

**Method 2: Git churn + session clustering.** If no session logs, cluster commits within a 4-hour window:

```bash
git log --format="%at" --reverse | python3 -c "
import sys
times = [int(t) for t in sys.stdin.read().split()]
if not times: exit()
sessions, current = [], [times[0]]
for t in times[1:]:
    if t - current[-1] <= 4*3600:
        current.append(t)
    else:
        sessions.append(current); current = [t]
sessions.append(current)

# Estimate session duration from commit density + span
total_h = 0
for s in sessions:
    span_h = (s[-1] - s[0]) / 3600
    by_span = max(0.5, min(4, span_h + 0.5))  # span + 30min buffer, clamped 0.5-4h
    by_density = min(4, 0.5 + 0.3 * len(s))   # 0.5h base + 18min per commit, capped 4h
    total_h += max(by_span, by_density)

print(f'sessions:{len(sessions)} est_hours:{total_h:.1f}')
"
```

Flag `method: "git_clustering"` with medium confidence.

**Method 3: LOC-based fallback.** If no git and no logs, use `net_claude_loc / 350 hrs`. Flag `method: "loc_estimate"` with low confidence.

### 9b. Compute headline metrics

```
value_per_claude_hour = total_cost_p50 / claude_active_hours
speed_multiplier      = total_eng_hours_p50 / claude_active_hours

# Honest Claude cost includes USER TIME reviewing/iterating
reviewer_hours         = claude_active_hours × 0.5    (default; adjust per user)
reviewer_cost          = reviewer_hours × recommended_rate

# Two DIFFERENT numbers — never add them together
equivalent_api_spend   = sum(tokens × published_rates) from ~/.claude/projects/*.jsonl
                         # what the tokens WOULD have cost at API per-token rates
actual_cash_paid       = depends on user's plan (ask or default):
                           - Claude Max:    $200/mo × calendar_months  (flat; ignores equivalent_api_spend)
                           - Claude Pro:    $20/mo  × calendar_months
                           - API (metered): equivalent_api_spend (the number IS the bill)
                           - Unknown:       report both, let the reader pick

effective_plan_savings = equivalent_api_spend − actual_cash_paid
                         # positive = subscription paid off; negative = API would have been cheaper
claude_total_cost      = actual_cash_paid + reviewer_cost   # use ACTUAL cash, not equivalent

roi                    = (total_cost_p50 − claude_total_cost) / claude_total_cost
```

The **reviewer-time inclusion is non-optional** — omitting it overstates ROI by 2-5×. Name the assumption explicitly: "reviewer_time = 0.5× Claude active hours (typical range 0.3-1.0×)."

### 9c. Speed-multiplier sanity check (Copilot SPACE anchor)

GitHub Copilot's 2024 randomized study (Measuring GitHub Copilot's Impact on Productivity, CACM 2024) measured a **1.55× speed multiplier** with Copilot (55% faster task completion, from baseline). Use this as the industry benchmark for honest AI speed-ups.

If your computed `speed_multiplier` is:
- **< 1.5×**: believable, maybe even conservative for Claude on greenfield code
- **1.5×-3×**: typical for Claude Code on well-scoped tasks
- **3×-8×**: plausible for code-heavy tasks with strong specs
- **8×-20×**: suspicious — verify by spot-checking a sample commit
- **> 20×**: almost certainly wrong — likely causes: hours denominator too small (sessions uncounted), gross LOC inflation (tests/generated leaked in), or bottom-up estimate over-inflated

```
if speed_multiplier > 20:
    sanity_flag = "implausible"
elif speed_multiplier > 8:
    sanity_flag = "suspicious"
else:
    sanity_flag = "plausible"
```

When `sanity_flag != "plausible"`, the report must explicitly say: *"Speed multiplier of [X]× exceeds Copilot's published 1.55× baseline by [Y]×. Treat with skepticism — review Step 9a for measurement errors before quoting."*

This prevents the most common lie people tell with cost-estimate tools: claiming a 50× speed multiplier that is actually 3× once reviewer time and uncounted sessions are included.

### 9d. State limitations loudly

In the report, always include:

> "Claude active hours estimated via *[method]*. Actual session time may differ by ±30% (session logs) or ±2× (git clustering). Reviewer time assumed at 0.5× Claude hours; adjust if you know your ratio. Speed multiplier is directional, not benchmark-grade."

---

## Step 10: Sensitivity & cross-validation

### 10a. Sensitivity analysis — which assumption moves the number most?

Vary each input one at a time, ±1 standard bucket, and record `p50_impact_usd`:

- Quality multiplier: 0.7 → 1.3
- Recommended rate: ±50%
- Company stage team multiplier: 1.0 → 2.65×
- Specialized-category LOC share: ±20%
- COCOMO EAF bucket: nearest-neighbor shift

Sort descending. Report the **top 3 drivers**.

### 10b. External anchors (reality checks against published benchmarks)

Two independent sanity checks drawn from peer-reviewed research:

**1. Harvard supply-side anchor (Hoffmann, Nagle, Zhou 2024).** For OSS-like codebases, the supply-side value (what it cost to produce) averages ~**3.5× a naive `LOC × generic_rate`** calculation. Compute the naive number, compare to our P50:

```
naive_supply_side = source_LOC × $0.15/line  (rough 2024 median, from SSRN 4693148)
harvard_ratio     = p50_cost / naive_supply_side
```

If `harvard_ratio` is far from 3.5× (say, <1.5× or >6×), flag it. Typical causes:
- <1.5× → we're under-counting complexity or rates too low
- >6× → over-priced; excluded code probably leaked in, or company-stage multiplier too high

**2. Capers Jones 5-year total cost of ownership.** Initial build is 25-35% of 5-year lifecycle. Report `lifetime_cost_5y`:

```
annual_maint_rate = 0.20   # industry default; range 0.15-0.30
lifetime_cost_5y  = build_cost × (1 + annual_maint_rate × 5)
                  = build_cost × 2.0   (default)
```

Important framing: *"build cost" above is ~40-50% of the 5-year TCO.* Clients often mistake the build number for total ownership; call it out.

### 10c. Cross-check (three-way if possible, two-way if no git)

| Method | Hours | Notes |
|---|---|---|
| Bottom-up (Step 3+5) | | Category × rate, with overheads |
| COCOMO II (Step 4) | | Top-down, calibrated constants |
| Process signal (Step 2c) | | `commits × avg_commit_hours` (skip if no git) |

Rules:
- **Three signals available** (git present): all agree within 30% → confidence **high**; two agree, one outlier → confidence **medium** (name the outlier); all three disagree → confidence **low**, reconcile before publishing.
- **Two signals only** (no git): bottom-up + COCOMO. Within 30% → **medium**; >30% divergence → **low**. Never report **high** confidence without a process signal.

---

## Step 11: Generate the report

Lead with TL;DR. Detail follows. Caveats + spot-check close.

---

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

### COCOMO II cross-check

- KSLOC [N], E [V], EAF [V] → **[N] hours**
- Divergence vs bottom-up: **[X]%** → [reconciled number]
- Process-signal estimate: [N] hours
- **Three-way confidence**: [high/medium/low]

## Calendar Time

| Company type | Efficiency | Calendar months |
|---|---|---|
| Solo / founder | 70% | [X] |
| Lean startup | 60% | [X] |
| Growth co | 50% | [X] |
| Enterprise | 40% | [X] |

## Market Rates ([year])

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
- **Sessions detected**: [N]
- **Claude active hours**: [N]
- **Reviewer hours (0.5× assumed)**: [N]
- **Plan**: [max / pro / api / unknown]
- **Claude tokens cost (if it were done via API)**: $[X] — *counterfactual only; computed from `message.usage` × published per-token rates. If you're on Max/Pro, this is NOT what you paid.*
- **Actual cash paid to Anthropic**: $[X] — flat subscription if on a plan, metered bill if on API
- **Effective plan savings** (equivalent API − actual cash): $[X] — positive = subscription paid off
- **Value produced (P50 full-team)**: $[X]
- **Value per Claude hour**: **$[X,XXX]/hr**
- **Speed multiplier vs human team**: **[X]×**
- **Total Claude investment** (actual cash + reviewer time): $[X]
- **ROI**: **[X]×** — every $1 you actually spent → $[X] of human-equivalent value

> *Claude worked ~[X] hours; user reviewed ~[X] hours. Combined, they produced ~$[X] of professional development value — roughly **$[X,XXX] per Claude hour**.*

## Sensitivity

Top 3 drivers of uncertainty:
1. **[Assumption]**: swing [X→Y] → P50 changes by ±$[Z]
2. **[Assumption]**: …
3. **[Assumption]**: …

## Spot-check (read before trusting the number)

Three things the reader should verify, with a copy-pasteable command for each:

1. **Biggest category is classified correctly.** Show the top-hours category and the files in it — does the label fit?
   ```bash
   # Example: if "systems programming" dominated, list those files
   find . -name "*.rs" -not -path "*/target/*" | head -20
   ```
   Commonly over-classified: "systems programming" when it's really just `unsafe` wrappers; "ML/AI" when it's pandas glue.

2. **Excluded-vs-counted ratio is sane.** If `excluded_loc > 3 × counted_loc`, the codebase is mostly vendored/generated — re-run after tightening exclusions.
   ```bash
   # Reveal what's big but excluded
   du -sh node_modules vendor dist build target .venv 2>/dev/null | sort -h
   ```

3. **Process-vs-code signals agree.** If bottom-up is >2× process estimate, one side is wrong (short git history hides rework, or a one-shot import inflates LOC).
   ```bash
   # Show commit density — squash-merged or single-commit imports are red flags
   git log --oneline | wc -l                     # total commits
   git log --format="%an" | sort -u | wc -l       # unique contributors
   git log --format="%ai" | head -1 && git log --format="%ai" | tail -1  # span
   ```

## Assumptions & Limitations

- Rates reflect [year] market; drift within ~6 months.
- Excludes: marketing, sales, legal, compliance, hosting/infra, ongoing maintenance.
- LOC undercounts dense/complex code and overcounts boilerplate.
- Claude active-hour estimate from [method]; may be off by ±[30%/2×].
- Reviewer time assumed 0.5× Claude hours; your ratio may differ.
- COCOMO EAF collapsed from 17 multipliers to 5 buckets; approximate.
- Full-team costs assume standard org structures.

---

## Step 12: Write the machine-readable artifact (to a temp directory, never the repo)

**Never write output files into the user's working directory.** Someone could `git add .` and commit them by accident — reports may contain sensitive numbers (rates, Claude costs, team composition) that don't belong in the project's git history.

Use a platform-appropriate temp directory, namespaced by project to avoid cross-project clobbering:

```bash
# Derive OUTDIR — works on Linux, macOS, and Windows (Git Bash / WSL / native Python)
python3 -c "
import os, tempfile, pathlib
proj = pathlib.Path(os.getcwd()).name or 'unknown'
out = pathlib.Path(tempfile.gettempdir()) / 'cost-estimate' / proj
out.mkdir(parents=True, exist_ok=True)
print(out)
"
```

Typical paths produced:
- **Linux**: `/tmp/cost-estimate/<project-name>/`
- **macOS**: `/var/folders/…/T/cost-estimate/<project-name>/` (or `/tmp/…` if `$TMPDIR` is set)
- **Windows**: `%TEMP%\cost-estimate\<project-name>\` (e.g. `C:\Users\<you>\AppData\Local\Temp\cost-estimate\<project-name>\`)

Write two files into that directory:

- `cost-estimate-report.md` — the full Markdown report from Step 11
- `cost-estimate.json` — the machine-readable artifact below

**Also print the full Markdown report to stdout (the terminal)** so the user sees it without opening any file. After printing, end with a one-line pointer to where the files were written, e.g.:

> *Report also saved to `/tmp/cost-estimate/my-project/cost-estimate-report.md` and `cost-estimate.json`. Not written to the current directory (safer — won't accidentally land in a commit).*

If the user explicitly asks for output in the current directory (e.g. "write it here"), honor the request, but show the *"not written to the working directory"* note without it — the default is always the temp dir.

JSON artifact schema:

```json
{
  "schema_version": "1.1",
  "generated_at": "ISO-8601",
  "strategy": "micro|small|normal|macro",
  "confidence": "low|medium|high",
  "project": {
    "name": "...",
    "stack": ["..."],
    "first_commit": "YYYY-MM-DD",
    "last_commit": "YYYY-MM-DD"
  },
  "codebase": {
    "counted_loc": 0,
    "excluded_loc": { "generated": 0, "vendored": 0, "minified": 0, "lockfiles": 0 },
    "by_language": {},
    "test_ratio": 0.0,
    "quality_multiplier": 1.0,
    "quality_signals": ["..."]
  },
  "process": {
    "project_duration_days": 0,
    "commit_count": 0,
    "contributor_count": 0,
    "gross_adds": 0,
    "gross_dels": 0,
    "net_adds": 0,
    "churn_ratio": 0.0,
    "process_only_hours_estimate": 0,
    "loc_per_day": 0,
    "ai_authored_flag": "no|suspected|clear"
  },
  "engineering": {
    "base_coding_hours": { "p10": 0, "p50": 0, "p90": 0 },
    "overhead_multiplier": 1.0,
    "total_hours": { "p10": 0, "p50": 0, "p90": 0 },
    "cocomo_ii_hours": 0,
    "function_point_count": 0,
    "function_point_hours": 0,
    "divergence_pct_bottom_up_vs_cocomo": 0.0,
    "agreement": "high|medium|low"
  },
  "locomo": {
    "regen_tokens": 0,
    "api_cost_usd": 0,
    "review_hours": 0,
    "review_cost_usd": 0,
    "locomo_cost_usd": 0,
    "human_premium_multiple": 0.0
  },
  "rates": {
    "recommended_usd_per_hour": 0,
    "justification": "...",
    "source": "websearch|skill_defaults"
  },
  "cost_engineering_usd": { "p10": 0, "p50": 0, "p90": 0 },
  "cost_full_team_usd": {
    "solo": 0, "lean_startup": 0, "growth": 0, "enterprise": 0
  },
  "calendar_months": {
    "solo": 0, "lean_startup": 0, "growth": 0, "enterprise": 0
  },
  "claude_roi": {
    "method": "session_logs|git_clustering|loc_estimate",
    "method_confidence": "high|medium|low",
    "claude_active_hours": 0,
    "reviewer_hours": 0,
    "plan": "max|pro|api|unknown",
    "actual_cash_paid_usd": 0,
    "equivalent_api_spend_usd": 0,
    "equivalent_api_source": "session_logs|heuristic",
    "effective_plan_savings_usd": 0,
    "token_usage": {
      "input_tokens": 0,
      "cache_creation_input_tokens": 0,
      "cache_read_input_tokens": 0,
      "output_tokens": 0,
      "messages": 0
    },
    "claude_total_cost_usd": 0,
    "value_per_claude_hour_usd": 0,
    "speed_multiplier": 0,
    "roi_multiple": 0
  },
  "external_anchors": {
    "naive_supply_side_usd": 0,
    "harvard_ratio": 0.0,
    "harvard_flag": "normal|too_low|too_high",
    "annual_maint_rate": 0.20,
    "lifetime_cost_5y_usd": 0
  },
  "sensitivity_drivers": [
    { "assumption": "...", "p50_impact_usd": 0 }
  ],
  "spot_check_items": ["...", "...", "..."],
  "low_confidence_fields": ["..."]
}
```

`low_confidence_fields` is a list of JSON paths (e.g. `["claude_roi.reviewer_hours", "rates.recommended_usd_per_hour"]`) that downstream consumers should display with a warning icon.

---

## Notes to self

- **Show your math.** Every number in the report must be traceable to a LOC count and a rate.
- **Never publish a single dollar figure without its range.**
- **Two-sig-figs rule**: round to two significant figures unless you can defend more.
- **Degrade gracefully.** Missing git? Note it, lower confidence, continue. Missing WebSearch? Use skill defaults, note it.
- **Decompose macros.** For monorepos, estimate each service separately and sum.
- **Don't double-count.** Quality bonuses and overhead reductions live on the same axis — pick one or split them.
