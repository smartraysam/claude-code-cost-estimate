#!/usr/bin/env python3
"""Extract ground-truth Claude token usage + equivalent API cost.

Reads every message.usage block from this project's Claude Code session
transcripts at ~/.claude/projects/<project-hash>/*.jsonl and sums input /
cache-write / cache-read / output tokens, then multiplies by each model
tier's published per-token rate.

The resulting `cost_usd` is the *counterfactual* API spend — what the
tokens would have cost if billed per-token. It is NOT necessarily what
the user paid: Max ($200/mo) and Pro ($20/mo) plans are flat.

Rates below reflect published Anthropic pricing at the skill's last
refresh; update `RATES` if pricing changes.

Usage: python3 scripts/claude_token_cost.py
Output: JSON on stdout with tokens + cost_usd + message count.
"""
import glob
import json
import os
import sys

# Per-1M-token rates (USD). Refresh when Anthropic updates pricing.
RATES = {
    "opus":   {"in": 15.00, "cache_write": 18.75, "cache_read": 1.50, "out": 75.00},
    "sonnet": {"in":  3.00, "cache_write":  3.75, "cache_read": 0.30, "out": 15.00},
    "haiku":  {"in":  0.80, "cache_write":  1.00, "cache_read": 0.08, "out":  4.00},
}

proj_hash = os.getcwd().replace("/", "-")
sessions_dir = os.path.expanduser(f"~/.claude/projects/{proj_hash}")

totals = {
    "input_tokens": 0,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "output_tokens": 0,
    "cost_usd": 0.0,
    "messages": 0,
    "sessions_dir": sessions_dir,
    "sessions_found": 0,
}

files = glob.glob(f"{sessions_dir}/*.jsonl")
totals["sessions_found"] = len(files)

for f in files:
    try:
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = d.get("message", {})
                u = msg.get("usage")
                if not u:
                    continue
                model = msg.get("model", "")
                tier = "opus" if "opus" in model else ("haiku" if "haiku" in model else "sonnet")
                r = RATES[tier]
                ti  = u.get("input_tokens", 0)
                tcw = u.get("cache_creation_input_tokens", 0)
                tcr = u.get("cache_read_input_tokens", 0)
                to  = u.get("output_tokens", 0)
                cost = (ti*r["in"] + tcw*r["cache_write"] + tcr*r["cache_read"] + to*r["out"]) / 1_000_000
                totals["input_tokens"]               += ti
                totals["cache_creation_input_tokens"] += tcw
                totals["cache_read_input_tokens"]     += tcr
                totals["output_tokens"]               += to
                totals["cost_usd"]                    += cost
                totals["messages"]                    += 1
    except OSError:
        continue

json.dump(totals, sys.stdout, indent=2)
print()
