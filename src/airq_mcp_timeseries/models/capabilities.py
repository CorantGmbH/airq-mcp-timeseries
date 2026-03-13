"""Capability model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CapabilitySet:
    """Describe which features a provider instance supports."""

    latest_values: bool = True
    historical_values: bool = False
    configuration: bool = False
    control: bool = False
    max_lookback_days: int | None = None
