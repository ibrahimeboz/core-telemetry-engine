import unittest
from src.telemetry.collector import SystemMetricsCollector
from src.telemetry.engine import TelemetryEngine
from src.telemetry.storage import TelemetryStorage
from src.telemetry.ledger import TelemetryLedger


class TestTelemetryEngine(unittest.TestCase):
    def setUp(self):
        self.collector = SystemMetricsCollector(node_id="test-node")
        self.engine = TelemetryEngine()
        self.storage = TelemetryStorage()
        self.ledger = TelemetryLedger(node_id="test-node")

    def test_collector_output_structure(self):
        sample = self.collector.collect()
        self.assertEqual(sample["node_id"], "test-node")
        self.assertIn("timestamp", sample)
        self.assertIn("platform", sample)
        self.assertIn("metrics", sample)
        self.assertIn("cpu_load_pct", sample["metrics"])
        self.assertIn("event_loop_latency_ms", sample["metrics"])

    def test_engine_percentiles(self):
        sample_latencies = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        percentiles = self.engine.calculate_latency_percentiles(sample_latencies)
        self.assertAlmostEqual(percentiles["p50"], 5.0, delta=0.5)
        self.assertGreaterEqual(percentiles["p99"], 9.0)

    def test_engine_health_evaluation(self):
        optimal_sample = {"metrics": {"cpu_load_pct": 25.0, "event_loop_latency_ms": 2.5}}
        health = self.engine.evaluate_health(optimal_sample)
        self.assertEqual(health["score"], "OPTIMAL")

        critical_sample = {"metrics": {"cpu_load_pct": 96.0, "event_loop_latency_ms": 65.0}}
        critical_health = self.engine.evaluate_health(critical_sample)
        self.assertEqual(critical_health["score"], "CRITICAL")

    def test_storage_snapshot_io(self):
        test_data = {"test_run": True, "status": "OK"}
        path = self.storage.write_snapshot(test_data)
        self.assertTrue(path.exists())
        loaded = self.storage.read_latest_snapshot()
        self.assertEqual(loaded.get("test_run"), True)

    def test_ledger_message_synthesis(self):
        msg = self.ledger.synthesize_diagnostic_message()
        self.assertTrue(any(msg.startswith(prefix) for prefix in ["perf(", "test(", "chore(", "refactor(", "fix(", "docs(", "ci(", "feat(", "style("]))
        self.assertIn("): ", msg)


if __name__ == "__main__":
    unittest.main()
