"""Metric metadata."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricInfo:
    """Describe a metric key, display label and optional aliases."""

    key: str
    label: str
    unit: str | None = None
    aliases: tuple[str, ...] = ()
