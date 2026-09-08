import argparse
import random
import sys
import time
from pathlib import Path

from .collector import SystemMetricsCollector
from .engine import TelemetryEngine
from .storage import TelemetryStorage


def run_diagnostics(node_id: str = "node-main") -> dict:
    """Collects system telemetry and prints diagnostics table."""
    collector = SystemMetricsCollector(node_id=node_id)
    engine = TelemetryEngine()
    storage = TelemetryStorage()

    sample = collector.collect()
    engine.ingest(sample)
    health = engine.evaluate_health(sample)

    storage.write_snapshot({
        "metadata": {
            "node_id": node_id,
            "version": "1.2.4",
            "last_synced_utc": sample["timestamp"],
            "operational_status": health["score"],
        },
        "system": sample["platform"],
        "metrics": sample["metrics"],
    })
    return sample


def run_benchmark(iterations: int = 50) -> dict:
    """Runs a latency calibration benchmark loop and saves results."""
    collector = SystemMetricsCollector()
    engine = TelemetryEngine()
    storage = TelemetryStorage()

    latencies = []
    for _ in range(iterations):
        lat = collector.measure_event_loop_latency(iterations=25)
        latencies.append(lat)

    percentiles = engine.calculate_latency_percentiles(latencies)
    sample = collector.collect()

    benchmark_entry = {
        "timestamp": sample["timestamp"],
        "iterations": iterations,
        "percentiles": percentiles,
        "throughput_qps": sample["metrics"]["throughput_qps"],
        "memory_mb": sample["metrics"]["memory_usage_mb"],
    }

    storage.append_benchmark_record(benchmark_entry)
    return benchmark_entry


def execute_sync_cycle(node_id: str = "node-ci") -> dict:
    """
    Executes a full diagnostic and benchmark synchronization cycle.
    Updates both snapshot and benchmark registers with atomic integrity.
    """
    diag_sample = run_diagnostics(node_id=node_id)
    bench_result = run_benchmark(iterations=30)
    return {
        "diagnostics": diag_sample,
        "benchmark": bench_result,
    }


def main():
    parser = argparse.ArgumentParser(description="Core Telemetry Engine CLI Runner")
    parser.add_argument("--diagnostics", action="store_true", help="Run runtime diagnostics collection")
    parser.add_argument("--benchmark", action="store_true", help="Execute latency calibration benchmark")
    parser.add_argument("--sync-report", action="store_true", help="Synchronize telemetry snapshots and registers")
    parser.add_argument("--node-id", type=str, default="node-local", help="Node identifier")

    args = parser.parse_args()

    if args.sync_report:
        result = execute_sync_cycle(node_id=args.node_id)
        print(f"[OK] Telemetry sync completed at {result['diagnostics']['timestamp']}")
        print(f"     Status: {result['diagnostics']['status']} | Throughput: {result['benchmark']['throughput_qps']} QPS")
        sys.exit(0)
    elif args.benchmark:
        result = run_benchmark()
        print(f"[OK] Benchmark completed: p50={result['percentiles']['p50']}ms, p95={result['percentiles']['p95']}ms")
        sys.exit(0)
    else:
        sample = run_diagnostics(node_id=args.node_id)
        print(f"Node: {sample['node_id']} [{sample['status']}]")
        print(f"CPU Load: {sample['metrics']['cpu_load_pct']}% | Memory: {sample['metrics']['memory_usage_mb']} MB")
        print(f"Latency: {sample['metrics']['event_loop_latency_ms']} ms | QPS: {sample['metrics']['throughput_qps']}")
        sys.exit(0)


if __name__ == "__main__":
    main()
