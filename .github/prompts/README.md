# Agent Prompts

Prompt templates for EcoMech's automated workflows.

Templates use `${NAME}` placeholders filled by `render_prompt.py` from
`PROMPT_NAME` environment variables set in each workflow step.

**Security rule:** Only run-time facts go in via substitution — repository
path, PR number, file names, scan parameters.  External text (issue bodies,
PR diffs, user comments, paper titles) is never pasted directly into a prompt;
the agent accesses those through tool calls after launch.
