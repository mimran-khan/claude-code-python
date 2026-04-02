"""
Telemetry metrics.

Counters and histograms.

Migrated from: utils/telemetry/instrumentation.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Counter:
    """A counter metric."""

    name: str
    description: str = ""
    value: int = 0
    labels: dict[str, str] = field(default_factory=dict)

    def increment(self, delta: int = 1) -> None:
        self.value += delta

    def reset(self) -> None:
        self.value = 0


@dataclass
class Histogram:
    """A histogram metric."""

    name: str
    description: str = ""
    buckets: list[float] = field(default_factory=lambda: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10])
    _values: list[float] = field(default_factory=list)

    def record(self, value: float) -> None:
        self._values.append(value)

    @property
    def count(self) -> int:
        return len(self._values)

    @property
    def sum(self) -> float:
        return sum(self._values)

    @property
    def mean(self) -> float:
        if not self._values:
            return 0.0
        return self.sum / self.count

    @property
    def min(self) -> float:
        return min(self._values) if self._values else 0.0

    @property
    def max(self) -> float:
        return max(self._values) if self._values else 0.0

    def reset(self) -> None:
        self._values.clear()


class MetricsRegistry:
    """Registry for metrics."""

    def __init__(self) -> None:
        self._counters: dict[str, Counter] = {}
        self._histograms: dict[str, Histogram] = {}

    def get_counter(
        self,
        name: str,
        description: str = "",
    ) -> Counter:
        """Get or create a counter."""
        if name not in self._counters:
            self._counters[name] = Counter(name=name, description=description)
        return self._counters[name]

    def get_histogram(
        self,
        name: str,
        description: str = "",
        buckets: list[float] | None = None,
    ) -> Histogram:
        """Get or create a histogram."""
        if name not in self._histograms:
            hist = Histogram(name=name, description=description)
            if buckets:
                hist.buckets = buckets
            self._histograms[name] = hist
        return self._histograms[name]

    def get_all_counters(self) -> dict[str, Counter]:
        """Get all counters."""
        return dict(self._counters)

    def get_all_histograms(self) -> dict[str, Histogram]:
        """Get all histograms."""
        return dict(self._histograms)

    def reset_all(self) -> None:
        """Reset all metrics."""
        for counter in self._counters.values():
            counter.reset()
        for histogram in self._histograms.values():
            histogram.reset()


# Global registry
_registry = MetricsRegistry()


def get_metrics() -> MetricsRegistry:
    """Get the global metrics registry."""
    return _registry


def increment_counter(
    name: str,
    delta: int = 1,
    labels: dict[str, str] | None = None,
) -> None:
    """Increment a counter."""
    counter = _registry.get_counter(name)
    if labels:
        counter.labels.update(labels)
    counter.increment(delta)


def record_histogram(
    name: str,
    value: float,
) -> None:
    """Record a histogram value."""
    histogram = _registry.get_histogram(name)
    histogram.record(value)


# Common metrics
def record_api_latency(model: str, duration_ms: float) -> None:
    """Record API call latency."""
    record_histogram(f"api.latency.{model}", duration_ms)


def increment_api_calls(model: str, success: bool = True) -> None:
    """Increment API call counter."""
    status = "success" if success else "error"
    increment_counter(f"api.calls.{model}.{status}")


def increment_tool_uses(tool_name: str) -> None:
    """Increment tool use counter."""
    increment_counter(f"tool.uses.{tool_name}")
