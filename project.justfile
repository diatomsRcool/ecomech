
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

# Export all processes as KGX TSV (writes _nodes.tsv and _edges.tsv)
export-kgx:
    mkdir -p export
    uv run python -m ecomech.export.kgx_export \
        --input {{processes_dir}} \
        --output export/ecomech_kgx.tsv

# Export process inventory as CSV
export-inventory:
    uv run ecomech-inventory \
        --input {{processes_dir}} \
        --output export/ecomech_inventory.csv

# --- Coverage Dashboard ---

# Generate HTML coverage browser (dashboard/coverage.html)
coverage:
    uv run python -m ecomech.analysis.coverage

# Generate coverage report as JSON
coverage-json:
    uv run python -m ecomech.analysis.coverage --json

# --- Similarity Explorer ---

# Generate HTML process similarity heatmap (dashboard/similarity.html)
similarity:
    uv run python -m ecomech.analysis.embedding

# Generate similarity explorer with CSV output
similarity-csv:
    uv run python -m ecomech.analysis.embedding \
        --csv export/similarity.csv

# --- Cross-database Ingestion ---

# Search GBIF for taxon records matching a name
# Usage: just gbif-search "Rhizobium leguminosarum"
gbif-search query:
    uv run python -m ecomech.ingest.gbif search "{{query}}"

# Search LTER-EDI for long-term monitoring datasets
# Usage: just lter-search "nitrogen cycling"
lter-search query:
    uv run python -m ecomech.ingest.lter search "{{query}}"

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

ecocore_owl := "conf/ecocore.owl"
# Path to a local ECOCORE git checkout if present (used by update-ecocore)
ecocore_local := env_var_or_default("ECOCORE_LOCAL", env_var_or_default("HOME", "") + "/ecocore/ecocore.owl")

# Copy ECOCORE OWL from a local checkout (faster than downloading).
# Falls back to downloading from purl.obolibrary.org if no local copy exists.
# Set ECOCORE_LOCAL=/path/to/ecocore/ecocore.owl to override the default location.
update-ecocore:
    #!/usr/bin/env bash
    if [ -f "{{ecocore_local}}" ]; then
        cp "{{ecocore_local}}" "{{ecocore_owl}}"
        echo "Copied from {{ecocore_local}} → {{ecocore_owl}}"
    else
        echo "No local checkout found at {{ecocore_local}}, downloading..."
        curl -L -o "{{ecocore_owl}}" http://purl.obolibrary.org/obo/ecocore.owl
        echo "ECOCORE OWL saved to {{ecocore_owl}}"
    fi

# Look up an ECOCORE term (requires conf/ecocore.owl — run: just download-ecocore)
oak-ecocore id:
    uv run runoak -i pronto:{{ecocore_owl}} info {{id}}

# Search ECOCORE for a term by keyword (requires conf/ecocore.owl)
# Uses label-match syntax (l~) to find terms whose labels contain the keyword
oak-search-ecocore term:
    uv run runoak -i pronto:{{ecocore_owl}} search "l~{{term}}"

# List all ECOCORE ecological process terms (requires conf/ecocore.owl)
oak-ecocore-processes:
    uv run runoak -i pronto:{{ecocore_owl}} descendants ECOCORE:00000001

# Show ancestors of an ECOCORE term (requires conf/ecocore.owl)
oak-ecocore-ancestors id:
    uv run runoak -i pronto:{{ecocore_owl}} ancestors {{id}}

# --- Analysis ---

# Run compliance analysis (field coverage across all entries)
compliance:
    uv run python -m ecomech.analysis.compliance

# Run compliance analysis with JSON output
compliance-json:
    uv run python -m ecomech.analysis.compliance --json

# Run compliance on a single file
compliance-file file:
    uv run python -m ecomech.analysis.compliance {{file}}

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
    rm -rf dashboard/
    rm -rf export/
    rm -rf docs/site/
    @echo "Derived artifacts cleaned."
