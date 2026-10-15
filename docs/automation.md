# EcoMech Automation

EcoMech is designed to be largely self-running. Claude agents handle literature
discovery, curation, and quality review automatically. Human attention is needed
only at a small number of decision gates.

---

## The autonomous loop

```
Weekly cron (Monday 07:00 UTC)
  │
  ▼
literature-scan.yaml
  ├─ build-packet ── just build-literature-packet
  │                  → queries Europe PMC for recent ecology papers
  │                  → writes literature_packet.json
  │
  ├─ scan ────────── Claude (haiku) reads packet
  │                  → selects promising leads
  │                  → writes scan_output.json
  │
  └─ publish ─────── creates GitHub Issues
                     labelled: curation + low_effort / high_effort

Issue with @claude mention
  │
  ▼
claude.yaml ─────── Claude (opus) runs /curate skill
                    → finds ENVO term, fetches PMIDs, drafts YAML
                    → validates schema + terms + snippets
                    → branches and opens a PR

PR touching kb/
  │
  ▼
review.yaml ─────── Claude (opus) reviews the PR
                    → runs just validate, just validate-terms-file
                    → checks snippet–claim alignment, term specificity,
                       taxon resolution, scope
                    → posts APPROVE or REQUEST_CHANGES comment

Human
  │
  ▼
  ├─ reads review comment
  └─ clicks Merge  ────────────── only required human action

PR merged
  │
  ▼
static.yml (existing)
  └─ regenerates pages/, deploys to GitHub Pages
```

New issues are also labelled automatically by **triage.yaml** (haiku agent)
within a few minutes of being opened.

---

## Human intervention points

| Situation | What to do |
|-----------|------------|
| PR opened | Read the automated review comment; merge if approved |
| ENVO term is ambiguous | Claude stops and comments with options; reply to choose one |
| Literature scan files irrelevant issues | Close them |
| Agent PR has errors | The review will flag them; close or push fixes |
| Process is out of scope | Close the curation issue with a note |

Everything else happens without intervention.

---

## Triggering curation manually

### Via a GitHub issue

Open a new issue and mention `@claude`:

```
Title: Curate: Riparian Denitrification
Body: @claude please curate an entry for riparian denitrification.
```

Claude will pick it up, run the full `/curate` workflow, and open a PR.

### Via the literature scan

Run the workflow manually from the **Actions** tab:

- **source**: `MED` (PubMed), `PPR` (preprints), or `ALL`
- **days**: lookback window
- **max_issues**: cap on issues filed
- **create_issues**: set to `false` for a dry run (no issues created)

### Via the command line

```bash
# Build a packet and inspect it locally
just build-literature-packet MED 14

# Curate a specific process directly
# (open Claude Code and run the skill)
just curate "Riparian Denitrification"
```

---

## Workflow reference

| Workflow | File | Trigger | Model | Max turns |
|----------|------|---------|-------|-----------|
| Claude | `claude.yaml` | `@claude` in issue / PR / review | opus | 80 |
| Review | `review.yaml` | PR opened / synchronised / `/review` comment | opus | 60 |
| Literature scan | `literature-scan.yaml` | Monday 07:00 UTC / manual | haiku | 30 |
| Triage | `triage.yaml` | Issue opened / manual | haiku | 10 |
| QC | `qc.yml` | PR / push to main | — | — |
| Pages | `static.yml` | Push to main | — | — |

Model assignments are in `.github/agent-config.yaml` and can be changed without
editing workflow files.

---

## Repository secrets required

| Secret | Required | Purpose |
|--------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | All Claude agent workflows |
| `CLAUDE_CODE_OAUTH_TOKEN` | Fallback | Used only if `ANTHROPIC_API_KEY` is unset |
| `EOL_API_TOKEN` | Optional | TraitBank lookups during `/curate` |
| `GBIF_API_TOKEN` | Optional | GBIF species resolution during `/curate` |

---

## One-time setup

1. Install the [Claude GitHub App](https://github.com/apps/claude) on this
   repository — this is what allows `@claude` mentions to trigger the agent.
2. Add `ANTHROPIC_API_KEY` under **Settings → Secrets and variables → Actions**.
3. Optionally add `EOL_API_TOKEN` and `GBIF_API_TOKEN` for richer curation.

---

## Security model

The automated workflows follow the principle of least privilege:

- **`claude.yaml`** — only OWNER, MEMBER, and COLLABORATOR accounts can summon
  the agent via `@claude`. Anonymous users cannot trigger it.
- **`review.yaml`** — fork PRs are rejected; the default branch (trusted tools
  and prompts) is checked out separately from the PR data files. The agent
  cannot execute scripts from the PR.
- **`literature-scan.yaml`** — the scan agent has read-only tools; a separate
  job creates the issues. Paper abstracts are explicitly treated as data, not
  instructions.
- **`triage.yaml`** — the triage agent has no write access; a separate job
  applies labels from an allowlist.

A human must approve every PR before it merges. Claude cannot merge its own work.

---

## File map

```
.github/
  agent-config.yaml              # model + max-turns per workflow
  actions/
    setup-agent/action.yaml      # composite: install deps, warm caches, resolve config
  scripts/
    agent_config.py              # reads agent-config.yaml → GITHUB_OUTPUT
    render_prompt.py             # substitutes PROMPT_* vars into prompt templates
    check_agent_run.py           # parses Claude execution log, surfaces errors
    literature-publish.js        # creates GitHub issues from scan leads
    review-publish.js            # posts PR review comment (APPROVE / REQUEST_CHANGES)
  prompts/
    literature-scan.md           # agent instructions for the scan job
    review.md                    # agent instructions for PR review
    triage.md                    # agent instructions for issue labelling
  workflows/
    claude.yaml                  # @claude responder
    review.yaml                  # PR auto-review
    literature-scan.yaml         # weekly Europe PMC scan
    triage.yaml                  # issue auto-labelling

src/ecomech/ingest/
  literature_packet.py           # fetches papers from Europe PMC API
```
