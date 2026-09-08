import json
import os
from pathlib import Path
from typing import Dict, Any


class TelemetryStorage:
    """Manages persistent telemetry reports and benchmark snapshot registries."""

    def __init__(self, root_dir: Path = None):
        if root_dir is None:
            self.root_dir = Path(__file__).resolve().parent.parent.parent
        else:
            self.root_dir = Path(root_dir)

        self.reports_dir = self.root_dir / "reports"
        self.benchmarks_dir = self.root_dir / "benchmarks"

        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.benchmarks_dir.mkdir(parents=True, exist_ok=True)

        self.snapshot_file = self.reports_dir / "telemetry_snapshot.json"
        self.benchmark_file = self.benchmarks_dir / "benchmark_results.json"

    def write_snapshot(self, data: Dict[str, Any]) -> Path:
        """Atomically writes telemetry diagnostic snapshot to disk."""
        tmp_file = self.snapshot_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp_file.replace(self.snapshot_file)
        return self.snapshot_file

    def append_benchmark_record(self, benchmark_entry: Dict[str, Any]) -> Path:
        """Updates benchmark results registry with the latest execution run."""
        records = []
        if self.benchmark_file.exists():
            try:
                with open(self.benchmark_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
                    if not isinstance(records, list):
                        records = []
            except Exception:
                records = []

        records.append(benchmark_entry)
        # Keep trailing 50 records for historical trend analysis
        if len(records) > 50:
            records = records[-50:]

        tmp_file = self.benchmark_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        tmp_file.replace(self.benchmark_file)
        return self.benchmark_file

    def read_latest_snapshot(self) -> Dict[str, Any]:
        """Reads the most recent telemetry snapshot if available."""
        if not self.snapshot_file.exists():
            return {}
        try:
            with open(self.snapshot_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
