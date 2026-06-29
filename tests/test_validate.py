"""Basic tests for EcoMech schema and KB entries."""

from pathlib import Path

import pytest
import yaml


KB_PROCESSES = Path("kb/processes")
SCHEMA_PATH = Path("src/ecomech/schema/ecomech.yaml")
REQUIRED_TOP_LEVEL = {"id", "name", "process_term", "description"}
REQUIRED_EVIDENCE = {"reference", "supports", "evidence_source"}


def process_files():
    return list(KB_PROCESSES.glob("*.yaml"))


def all_evidence_items(data: dict) -> list[dict]:
    """Recursively extract all evidence items from a YAML dict."""
    items = []
    if isinstance(data, dict):
        if "reference" in data and "supports" in data:
            items.append(data)
        for v in data.values():
            items.extend(all_evidence_items(v))
    elif isinstance(data, list):
        for item in data:
            items.extend(all_evidence_items(item))
    return items


@pytest.mark.parametrize("filepath", process_files())
def test_required_fields_present(filepath):
    """Each process YAML must have all required top-level fields."""
    data = yaml.safe_load(filepath.read_text())
    missing = REQUIRED_TOP_LEVEL - set(data.keys())
    assert not missing, f"{filepath.name} missing required fields: {missing}"


@pytest.mark.parametrize("filepath", process_files())
def test_process_term_has_id_and_label(filepath):
    """process_term must have both id and label."""
    data = yaml.safe_load(filepath.read_text())
    pt = data.get("process_term", {})
    assert "id" in pt, f"{filepath.name}: process_term missing 'id'"
    assert "label" in pt, f"{filepath.name}: process_term missing 'label'"


@pytest.mark.parametrize("filepath", process_files())
def test_process_term_id_is_envo(filepath):
    """process_term id must be an ENVO CURIE."""
    data = yaml.safe_load(filepath.read_text())
    term_id = data.get("process_term", {}).get("id", "")
    assert term_id.startswith("ENVO:"), (
        f"{filepath.name}: process_term id '{term_id}' is not an ENVO CURIE"
    )


@pytest.mark.parametrize("filepath", process_files())
def test_all_evidence_has_required_fields(filepath):
    """Every evidence item must have reference, supports, and evidence_source."""
    data = yaml.safe_load(filepath.read_text())
    for ev in all_evidence_items(data):
        missing = REQUIRED_EVIDENCE - set(ev.keys())
        assert not missing, (
            f"{filepath.name}: evidence item for '{ev.get('reference', '?')}' "
            f"missing fields: {missing}"
        )


@pytest.mark.parametrize("filepath", process_files())
def test_creation_date_format(filepath):
    """creation_date, if present, must be ISO 8601 UTC format."""
    import re

    data = yaml.safe_load(filepath.read_text())
    date = data.get("creation_date")
    if date:
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        assert re.match(pattern, str(date)), (
            f"{filepath.name}: creation_date '{date}' is not ISO 8601 UTC format"
        )


def test_schema_file_exists():
    """The LinkML schema file must exist."""
    assert SCHEMA_PATH.exists(), f"Schema not found at {SCHEMA_PATH}"


def test_schema_is_valid_yaml():
    """The schema must be valid YAML."""
    data = yaml.safe_load(SCHEMA_PATH.read_text())
    assert isinstance(data, dict)
    assert "classes" in data
    assert "slots" in data
    assert "enums" in data
