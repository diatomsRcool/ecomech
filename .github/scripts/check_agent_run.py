#!/usr/bin/env python3
"""Parse a Claude Code Action execution log and surface errors to GitHub Actions.

Usage:
    python check_agent_run.py <execution_file> [label]
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def write_summary(text: str) -> None:
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a") as fh:
            fh.write(text + "\n")
    else:
        print(text)


def main() -> None:
    exec_file = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "EXECUTION_FILE",
        os.path.join(os.environ.get("RUNNER_TEMP", "/tmp"), "claude-execution-output.json"),
    )
    label = sys.argv[2] if len(sys.argv) > 2 else "Agent"

    path = Path(exec_file)
    if not path.exists():
        print(f"Error: execution file not found: {exec_file}", file=sys.stderr)
        sys.exit(1)

    events = json.loads(path.read_text())
    if not isinstance(events, list):
        events = [events]

    result = next(
        (e for e in reversed(events) if e.get("type") == "result"),
        None,
    )

    if result is None:
        write_summary(f"## {label} — no result event found")
        print("Error: no result event in execution log", file=sys.stderr)
        sys.exit(1)

    subtype = result.get("subtype", "unknown")
    turns = result.get("num_turns", "?")
    cost = result.get("cost_usd")
    cost_str = f"${cost:.4f}" if cost is not None else "unknown"

    write_summary(f"## {label}\n\nturns={turns} cost={cost_str} subtype={subtype}")
    print(f"turns={turns} cost={cost_str} subtype={subtype}")

    if subtype == "success":
        return

    error_text = str(result.get("error", ""))
    error_lower = error_text.lower()

    if any(p in error_lower for p in ["out of credit", "payment required"]):
        msg = f"{label} failed: billing issue. Check ANTHROPIC_API_KEY credits."
    elif any(p in error_lower for p in ["usage limit", "rate limit"]):
        msg = f"{label} failed: rate limited. Wait and retry, or reduce max_turns."
    elif "max turns" in error_lower or subtype == "max_turns":
        msg = f"{label} hit max turns. Increase max_turns in .github/agent-config.yaml."
    elif subtype == "cancelled":
        msg = f"{label} was cancelled."
    else:
        msg = f"{label} failed (subtype={subtype}): {error_text}"

    write_summary(f"\n**Error:** {msg}")
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
