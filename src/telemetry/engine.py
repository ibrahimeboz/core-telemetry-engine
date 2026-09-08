import math
from typing import List, Dict, Any


class TelemetryEngine:
    """Processes raw metric samples, computes statistical distributions and health scores."""

    def __init__(self, sample_capacity: int = 100):
        self.sample_capacity = sample_capacity
        self.history: List[Dict[str, Any]] = []

    def ingest(self, sample: Dict[str, Any]) -> None:
        """Ingests a telemetry sample and maintains rolling buffer capacity."""
        self.history.append(sample)
        if len(self.history) > self.sample_capacity:
            self.history.pop(0)

    def calculate_latency_percentiles(self, custom_latencies: List[float] = None) -> Dict[str, float]:
        """Calculates p50, p95, and p99 latency distributions."""
        latencies = custom_latencies
        if latencies is None:
            latencies = [
                s["metrics"]["event_loop_latency_ms"]
                for s in self.history
                if "metrics" in s and "event_loop_latency_ms" in s["metrics"]
            ]

        if not latencies:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

        sorted_vals = sorted(latencies)
        n = len(sorted_vals)

        def get_p(pct: float) -> float:
            idx = max(0, min(n - 1, math.ceil((pct / 100.0) * n) - 1))
            return round(sorted_vals[idx], 3)

        return {
            "p50": get_p(50),
            "p95": get_p(95),
            "p99": get_p(99),
        }

    def evaluate_health(self, latest_sample: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates overall system operational status from metrics."""
        metrics = latest_sample.get("metrics", {})
        cpu = metrics.get("cpu_load_pct", 0.0)
        latency = metrics.get("event_loop_latency_ms", 0.0)

        if cpu > 90.0 or latency > 50.0:
            score = "CRITICAL"
        elif cpu > 75.0 or latency > 20.0:
            score = "WARNING"
        else:
            score = "OPTIMAL"

        return {
            "score": score,
            "inspected_nodes": 1,
            "anomalies_detected": 0 if score == "OPTIMAL" else 1,
        }
