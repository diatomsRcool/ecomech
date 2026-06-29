# Contributing to EcoMech

EcoMech is a community knowledge base of ecological process mechanisms. Contributions of new process entries, improvements to existing entries, and tooling enhancements are all welcome.

## Getting Started

```bash
git clone https://github.com/your-org/ecomech
cd ecomech
just install
just install-hooks
```

## What to Contribute

- **New ecological process entries** in `kb/processes/`
- **Mechanism modules** in `kb/modules/` (conserved, reusable process components)
- **Process groupings** in `kb/groupings/`
- **Tooling improvements** in `src/ecomech/`
- **Bug reports and schema suggestions** via GitHub Issues

## Curating a New Process Entry

### Step 1: Choose an ENVO Term

Every entry must bind to a term from the **ENVO ecosystem process branch** (ENVO:02500000).

```bash
just oak-envo-ecosystem-processes        # browse the full hierarchy
just oak-search-envo "primary production"  # search by keyword
```

### Step 2: Draft the YAML

Create `kb/processes/YourProcessName.yaml`. Follow the structure in `CLAUDE.md`
and use `kb/processes/Nitrogen_Cycling.yaml` as a template.

Key requirements:
- `id`: ENVO term CURIE
- `name`: human-readable name
- `process_term`: ENVO term with id and canonical label
- `description`: concise free-text description
- All mechanistic claims backed by evidence with PMID references

### Step 3: Validate Ontology Terms

```bash
just validate-terms-file kb/processes/YourProcessName.yaml
```

Fix any unresolved term IDs before proceeding.

### Step 4: Cache and Validate References

```bash
# For each PMID in your file:
just fetch-reference PMID:XXXX

# Validate all snippets are exact verbatim quotes:
just validate-references kb/processes/YourProcessName.yaml
```

**Never** manually create files in `references_cache/`. Only `just fetch-reference` creates valid cache files.

### Step 5: Run Full QC

```bash
just qc
```

All checks must pass before submitting a PR.

### Step 6: Submit a Pull Request

- Open PRs from `origin`, not forks (required for automated validation)
- PR title: `Add [Process Name] entry`
- PR body: summarize what was added, which ontology terms were used, and key references

## Evidence Quality Standards

| Tier | Source | Description |
|------|--------|-------------|
| 1 | `FIELD_STUDY` | In situ ecological measurement in natural systems |
| 1 | `LONG_TERM_MONITORING` | Long-term ecological research datasets |
| 2 | `MESOCOSM` | Outdoor enclosures, mesocosms, or microcosms |
| 2 | `META_ANALYSIS` | Cross-study synthesis |
| 3 | `LABORATORY` | Controlled lab experiments |
| 3 | `COMPUTATIONAL` | Models and simulations |
| 4 | `REVIEW` | Narrative reviews |
| 4 | `EXPERT_OPINION` | Expert consensus |

Prefer Tier 1 evidence. All evidence requires a `snippet` that is an **exact verbatim quote** from the reference.

## Schema Changes

Propose schema changes via GitHub Issues before implementing. Schema changes require:

1. Updating `src/ecomech/schema/ecomech.yaml`
2. Regenerating the datamodel: `just gen-all`
3. Updating affected KB files if existing slots change
4. Updating tests and documentation

## Code Style

- Python: ruff formatting and linting (`just lint`)
- YAML: yamllint compliant (`just lint-yaml`)
- Commit messages: present tense, imperative ("Add nitrogen cycling entry")

## Questions?

Open a GitHub Issue or Discussion for questions about ontology term selection,
schema design, or evidence quality.
