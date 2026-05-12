from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class DataEntry:
    data_type: str
    host: str | None
    location: str | None
    lineage_hash: str | None
    amstrax_version: str | None
    raw: dict[str, Any]


@dataclass
class RunSummary:
    number: int
    mode: str | None
    start: datetime | None
    end: datetime | None
    processing_status: str | None


@dataclass
class RunDetails:
    number: int
    mode: str | None
    start: datetime | None
    end: datetime | None
    tags: list[dict[str, Any]]
    comments: list[dict[str, Any]]
    processing_status: dict[str, Any] | None
    data_entries: list[DataEntry]
    raw_doc: dict[str, Any]
