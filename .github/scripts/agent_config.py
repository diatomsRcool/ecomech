#!/usr/bin/env python3
"""Resolve Claude model and max-turns for a workflow from .github/agent-config.yaml.

Exits non-zero if no model resolves, so misconfiguration is caught early.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", help="Workflow name (matches key in agent-config.yaml)")
    parser.add_argument("--override", metavar="MODEL", help="Explicit model override")
    args = parser.parse_args()

    config_path = Path(__file__).parent.parent / "agent-config.yaml"
    with config_path.open() as fh:
        config = yaml.safe_load(fh)

    default_model = config.get("default_model")
    default_max_turns = config.get("default_max_turns", 40)

    workflow_cfg = config.get("workflows", {}).get(args.workflow, {})
    model = args.override or workflow_cfg.get("model") or default_model

    if not model:
        print(
            f"Error: no model resolved for workflow '{args.workflow}'. "
            "Set default_model in .github/agent-config.yaml.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Model must be a single token — no spaces/newlines
    if not re.match(r"^\S+$", model):
        print(f"Error: model '{model}' contains whitespace", file=sys.stderr)
        sys.exit(1)

    max_turns = workflow_cfg.get("max_turns", default_max_turns)

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as fh:
            fh.write(f"model={model}\n")
            fh.write(f"max-turns={max_turns}\n")
    else:
        print(f"model={model}")
        print(f"max-turns={max_turns}")


if __name__ == "__main__":
    main()
