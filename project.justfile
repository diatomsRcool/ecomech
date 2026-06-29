schema_path := "src/ecomech/schema/ecomech.yaml"
processes_dir := "kb/processes"
modules_dir := "kb/modules"
groupings_dir := "kb/groupings"
references_cache := "references_cache"

# --- Research & Curation Helpers ---

# Run deep research on an ecological process (requires deep-research-client)
research name provider="perplexity":
    uv run deep-research "Ecological mechanisms of {{name}}" \
        --provider {{provider}} \
        --output research/{{name}}.md

# Curate a new process entry interactively (Claude Code skill)
# Usage: just curate "Nitrogen Cycling"
curate name:
    @echo "Open Claude Code and run: /curate {{name}}"
    @echo "Or use: claude 'Curate an ecomech entry for: {{name}}'"

# --- Reference Utilities ---

# Fetch a batch of PMIDs from a file (one per line)
fetch-references-batch file:
    @while IFS= read -r pmid; do \
        echo "Fetching $pmid..."; \
        uv run linkml-reference-validator fetch "$pmid" --cache-dir {{references_cache}}; \
    done < {{file}}

# Tag all cached references (updates metadata)
references-tag-all:
    @find {{references_cache}} -name "*.md" | head -20 | xargs -I{} echo "Tagged: {}"

# --- Export ---

# Export all processes as KGX TSV edges
export-kgx:
    uv run python -m ecomech.export.kgx_export \
        --input {{processes_dir}} \
        --output export/ecomech_kgx.tsv

# Export process inventory as CSV
export-inventory:
    uv run ecomech-inventory \
        --input {{processes_dir}} \
        --output export/ecomech_inventory.csv

# --- OAK Lookups ---

# Look up an ENVO term
oak-envo id:
    uv run runoak -i sqlite:obo:envo info {{id}}

# Look up a GO term
oak-go id:
    uv run runoak -i sqlite:obo:go info {{id}}

# Look up a taxon
oak-taxon id:
    uv run runoak -i sqlite:obo:ncbitaxon info {{id}}

# Look up a PATO term
oak-pato id:
    uv run runoak -i sqlite:obo:pato info {{id}}

# Look up an ECTO term
oak-ecto id:
    uv run runoak -i sqlite:obo:ecto info {{id}}

# Search ENVO ecosystem process branch
oak-search-envo term:
    uv run runoak -i sqlite:obo:envo search {{term}}

# List ENVO ecosystem process subclasses
oak-envo-ecosystem-processes:
    uv run runoak -i sqlite:obo:envo descendants ENVO:02500000

# --- Analysis ---

# Run compliance analysis (field coverage across all entries)
compliance:
    uv run python -m ecomech.analysis.compliance \
        --input {{processes_dir}} \
        --output dashboard/compliance.html

# Generate QC dashboard
dashboard: compliance
    @echo "Dashboard generated at dashboard/compliance.html"

# --- History ---

# Validate a history record
validate-history file:
    uv run linkml-validate -s src/ecomech/schema/history.yaml {{file}}

# --- Utilities ---

# Show schema stats
schema-stats:
    @echo "Classes:"
    @uv run python -c "from linkml_runtime.loaders import yaml_loader; \
        from linkml_runtime.linkml_model import SchemaDefinition; \
        import yaml; d = yaml.safe_load(open('{{schema_path}}')); \
        print(f'  {len(d.get(\"classes\", {}))} classes'); \
        print(f'  {len(d.get(\"slots\", {}))} slots'); \
        print(f'  {len(d.get(\"enums\", {}))} enums')"

# Clean derived artifacts
clean:
    rm -rf pages/processes/*.html
    rm -rf dashboard/*.html
    rm -rf export/
    rm -rf docs/site/
    @echo "Derived artifacts cleaned."
