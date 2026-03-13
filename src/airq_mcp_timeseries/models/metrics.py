"""Metric metadata."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricInfo:
    key: str
    label: str
    unit: str | None = None
    aliases: tuple[str, ...] = ()
