set shell := ["bash", "-c"]

schema_name := "ecomech"
schema_dir := "src/ecomech/schema"
schema_path := schema_dir + "/" + schema_name + ".yaml"
kb_dir := "kb"
processes_dir := kb_dir + "/processes"
modules_dir := kb_dir + "/modules"
groupings_dir := kb_dir + "/groupings"
src_dir := "src/ecomech"
gen_dir := src_dir + "/datamodel"
references_cache := "references_cache"

# --- Setup ---

# Install all dependencies
install:
    uv sync --all-groups
    @echo "EcoMech dependencies installed."

# Install pre-commit hooks
install-hooks:
    uv run pre-commit install

# --- Schema ---

# Generate Python datamodel from LinkML schema
gen-python:
    mkdir -p {{gen_dir}}
    uv run gen-python {{schema_path}} > {{gen_dir}}/ecomech.py

# Generate Pydantic model from LinkML schema
gen-pydantic:
    mkdir -p {{gen_dir}}
    uv run gen-pydantic {{schema_path}} > {{gen_dir}}/ecomech_pydantic.py

# Generate all datamodel artifacts
gen-all: gen-python gen-pydantic

# --- Validation ---

# Validate a single process YAML file against the schema
validate file:
    uv run linkml-validate -s {{schema_path}} -C EcologicalProcess {{file}}

# Validate all process YAML files
validate-all:
    @for f in {{processes_dir}}/*.yaml; do \
        echo "Validating $f..."; \
        uv run linkml-validate -s {{schema_path}} -C EcologicalProcess "$f" || exit 1; \
    done
    @echo "All process entries valid."

# Validate a grouping YAML file
validate-grouping file:
    uv run linkml-validate -s {{schema_path}} -C Grouping {{file}}

# Validate all grouping files
validate-groupings:
    @for f in {{groupings_dir}}/*.yaml; do \
        echo "Validating grouping $f..."; \
        uv run linkml-validate -s {{schema_path}} -C Grouping "$f" || exit 1; \
    done

# Validate a module YAML file
validate-module file:
    uv run linkml-validate -s {{schema_path}} -C EcologicalModule {{file}}

# Validate all module files
validate-modules:
    @for f in {{modules_dir}}/*.yaml; do \
        echo "Validating module $f..."; \
        uv run linkml-validate -s {{schema_path}} -C EcologicalModule "$f" || exit 1; \
    done

# --- Term Validation ---

# Validate ontology terms in all process files
validate-terms:
    uv run linkml-term-validator validate {{processes_dir}}/*.yaml \
        -s {{schema_path}} \
        -c conf/oak_config.yaml

# Validate ontology terms in a single file
validate-terms-file file:
    uv run linkml-term-validator validate {{file}} \
        -s {{schema_path}} \
        -c conf/oak_config.yaml

# --- Reference Validation ---

# Fetch and cache a PubMed reference
fetch-reference ref:
    uv run linkml-reference-validator cache reference {{ref}} \
        -c {{references_cache}}

# Validate references in a single file
validate-references file:
    uv run linkml-reference-validator validate data {{file}} \
        -s {{schema_path}} \
        -t EcologicalProcess \
        -c {{references_cache}} \
        --config .linkml-reference-validator.yaml

# Validate references in all process files
validate-references-all:
    @for f in {{processes_dir}}/*.yaml; do \
        echo "Validating references in $f..."; \
        uv run linkml-reference-validator validate data "$f" \
            -s {{schema_path}} \
            -t EcologicalProcess \
            -c {{references_cache}} \
            --config .linkml-reference-validator.yaml || exit 1; \
    done

# --- Quality Control ---

# Run full QC (schema + term + reference validation)
qc: validate-all validate-terms validate-references-all
    @echo "QC complete."

# Run schema + term validation only (faster, no network)
qc-fast: validate-all validate-terms
    @echo "Fast QC complete."

# --- Rendering ---

# Render HTML for a single process entry
render file:
    uv run python -m ecomech.render.render {{file}}

# Render all process HTML pages
render-all:
    mkdir -p pages/processes
    @for f in {{processes_dir}}/*.yaml; do \
        uv run python -m ecomech.render.render "$f"; \
    done

# --- Process Management ---

# List all curated processes
list-processes:
    @ls {{processes_dir}}/*.yaml | xargs -I{} basename {} .yaml | sort

# Count curated processes
count-processes:
    @ls {{processes_dir}}/*.yaml 2>/dev/null | wc -l | tr -d ' '

# --- Documentation ---

# Build and serve documentation locally
docs-serve:
    uv run mkdocs serve

# Build documentation
docs-build:
    uv run mkdocs build

# Deploy documentation to GitHub Pages
docs-deploy:
    uv run mkdocs gh-deploy

# --- Testing ---

# Run test suite
test:
    uv run pytest tests/ -v

# --- Linting ---

# Run YAML linting
lint-yaml:
    uv run yamllint {{processes_dir}}/

# Run all linters
lint: lint-yaml
    uv run codespell .
    uv run ruff check src/

# Import project-specific recipes
import 'project.justfile'
