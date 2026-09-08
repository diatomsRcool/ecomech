"""Base class and shared utilities for cross-database ingestion."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class IngestRecord:
    """A structured record fetched from an external database."""

    def __init__(
        self,
        source: str,
        source_id: str,
        name: str,
        description: str = "",
        url: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.source = source
        self.source_id = source_id
        self.name = name
        self.description = description
        self.url = url
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "source_id": self.source_id,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return f"IngestRecord(source={self.source!r}, id={self.source_id!r}, name={self.name!r})"


class BaseIngester(ABC):
    """Abstract base class for all cross-database ingesters."""

    source_name: str = "unknown"

    @abstractmethod
    def search(self, query: str, limit: int = 20) -> list[IngestRecord]:
        """Search the external database and return matching records."""
        ...

    @abstractmethod
    def fetch(self, record_id: str) -> IngestRecord | None:
        """Fetch a single record by its source-specific ID."""
        ...

    def save(self, records: list[IngestRecord], output_path: Path) -> None:
        """Save records as JSON lines to output_path."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps(r.to_dict()) + "\n")
