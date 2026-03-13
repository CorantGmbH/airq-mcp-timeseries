"""Tabular export models."""

from dataclasses import dataclass
from typing import Literal

ExportFormat = Literal["csv", "xlsx"]


@dataclass(frozen=True, slots=True)
class ExportResult:
    output_format: ExportFormat
    mime_type: str
    payload: bytes | str
