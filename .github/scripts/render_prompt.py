#!/usr/bin/env python3
"""Render a prompt template, substituting PROMPT_* environment variables.

Only run-time facts go in via substitution (repository path, PR number, file
names, scan parameters).  External text — issue bodies, PR diffs, user comments
— is never pasted into the prompt; the agent accesses those through tool calls.
"""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path
from string import Template


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: render_prompt.py <name>", file=sys.stderr)
        sys.exit(1)

    name = sys.argv[1]
    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_file = prompts_dir / f"{name}.md"

    if not prompt_file.exists():
        print(f"Error: prompt not found: {prompt_file}", file=sys.stderr)
        sys.exit(1)

    template_text = prompt_file.read_text()

    substitutions = {
        k.removeprefix("PROMPT_"): v
        for k, v in os.environ.items()
        if k.startswith("PROMPT_")
    }

    rendered = Template(template_text).safe_substitute(substitutions)

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        delimiter = f"PROMPT_{secrets.token_hex(8)}"
        with open(github_output, "a") as fh:
            fh.write(f"prompt<<{delimiter}\n{rendered}\n{delimiter}\n")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
