# core-telemetry-engine

[![CI](https://github.com/ibrahimeboz/core-telemetry-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/ibrahimeboz/core-telemetry-engine/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

A zero-dependency runtime telemetry aggregator, latency profiler, and benchmark recorder designed for distributed Python services.

---

## Features

- **Resource Profiling:** Platform metrics collector capturing CPU load, memory usage, disk utilization, and active thread counts.
- **Latency Distribution:** High-precision event loop calibration with p50, p95, and p99 percentile calculations.
- **Atomic Persistence:** Thread-safe JSON snapshots and benchmark registries with automated verification.
- **Zero External Dependencies:** Built entirely with Python standard libraries (`platform`, `time`, `shutil`, `unittest`).
- **Continuous Diagnostics:** Native CI automation workflow for scheduled calibration runs and health diagnostics.

---

## Architecture

```
src/telemetry/
├── __init__.py       # Package exports and version metadata
├── collector.py      # SystemMetricsCollector (hardware & event loop metrics)
├── engine.py         # TelemetryEngine (percentiles, rolling buffer, health scoring)
├── storage.py        # TelemetryStorage (atomic snapshot writes & benchmark log)
└── runner.py         # CLI entry point for diagnostics and calibration
```

---

## Quickstart

### Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/ibrahimeboz/core-telemetry-engine.git
cd core-telemetry-engine
pip install -e .
```

### Basic Usage

```python
from src.telemetry import SystemMetricsCollector, TelemetryEngine, TelemetryStorage

# 1. Collect system metrics
collector = SystemMetricsCollector(node_id="worker-01")
metrics = collector.collect()
print(f"Node Status: {metrics['status']} (Latency: {metrics['metrics']['event_loop_latency_ms']}ms)")

# 2. Ingest into engine and score health
engine = TelemetryEngine()
engine.ingest(metrics)
health = engine.evaluate_health(metrics)
print(f"System Health: {health['score']}")

# 3. Persist snapshot
storage = TelemetryStorage()
storage.write_snapshot(metrics)
```

---

## Command Line Interface (CLI)

The module provides a CLI runner for system diagnostics and benchmark runs:

```bash
# Print runtime diagnostics table
python -m src.telemetry.runner --diagnostics

# Run latency benchmark calibration
python -m src.telemetry.runner --benchmark

# Execute full diagnostic sync and persist report
python -m src.telemetry.runner --sync-report --node-id node-ci
```

---

## Testing

Run the test suite via `unittest`:

```bash
python -m unittest discover tests
```

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.
