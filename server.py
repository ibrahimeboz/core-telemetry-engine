"""
Core Telemetry Engine - Diagnostic Studio Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lightweight zero-dependency HTTP server providing real-time telemetry
diagnostics, timeseries benchmark exploration, and versioned ledger synchronization.
"""

import http.server
import json
import re
import urllib.parse
from pathlib import Path

from src.telemetry.collector import SystemMetricsCollector
from src.telemetry.engine import TelemetryEngine
from src.telemetry.storage import TelemetryStorage
from src.telemetry.ledger import TelemetryLedger

PORT = 5000
BASE_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = BASE_DIR / "config.json"
WORKFLOW_PATH = BASE_DIR / ".github" / "workflows" / "ci.yml"
WEB_DIR = BASE_DIR / "web"

STORAGE = TelemetryStorage(root_dir=BASE_DIR)
COLLECTOR = SystemMetricsCollector(node_id="node-main")
ENGINE = TelemetryEngine()
LEDGER = TelemetryLedger(root_dir=BASE_DIR, node_id="node-studio")


def load_config() -> dict:
    """Loads node configuration from disk."""
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(data: dict) -> None:
    """Persists node configuration to disk."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def sync_workflow_identity(config: dict) -> tuple[bool, str]:
    """Synchronizes committer identity with CI diagnostic workflow."""
    if not WORKFLOW_PATH.exists():
        return False, "CI workflow file not found."

    try:
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        github_cfg = config.get("github") or config.get("node", {})
        username = github_cfg.get("username") or github_cfg.get("identity", "developer")
        email = github_cfg.get("email") or github_cfg.get("contact", "")

        content = re.sub(
            r'git config --global user\.name\s+"[^"]*"',
            f'git config --global user.name "{username}"',
            content
        )
        content = re.sub(
            r'git config --global user\.email\s+"[^"]*"',
            f'git config --global user.email "{email}"',
            content
        )

        with open(WORKFLOW_PATH, "w", encoding="utf-8") as f:
            f.write(content)

        return True, "Workflow identity synchronized."
    except Exception as e:
        return False, str(e)


class DiagnosticStudioHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler for Telemetry Diagnostic Studio."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def _send_json(self, data: dict, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/config":
            self._send_json(load_config())
            return

        if parsed.path == "/api/status":
            code, out, _ = LEDGER._execute_vcs(["log", "-1", "--pretty=format:%h - %an: %s (%cr)"])
            last_commit = out if code == 0 else "Initial repository baseline"
            latest_snap = STORAGE.read_latest_snapshot()

            self._send_json({
                "lastCommit": last_commit,
                "workflowExists": WORKFLOW_PATH.exists(),
                "snapshotExists": STORAGE.snapshot_file.exists(),
                "latestMetrics": latest_snap.get("metrics", {})
            })
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else ""

        if parsed.path == "/api/config":
            try:
                new_config = json.loads(body)
                save_config(new_config)
                ok, msg = sync_workflow_identity(new_config)
                self._send_json({
                    "success": True,
                    "message": "Configuration saved successfully.",
                    "workflowSync": {"success": ok, "detail": msg}
                })
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
            return

        if parsed.path in ("/api/trigger-test", "/api/trigger-diagnostic"):
            try:
                res = LEDGER.record_diagnostic_cycle(node_id="node-diagnostic", sync_vcs=True)
                summary = (
                    f"[*] Telemetry Diagnostic Cycle Executed\n"
                    f"Node: {res['sample']['node_id']}\n"
                    f"Operational Health: {res['health']['score']}\n"
                    f"VCS Ledger: {res['vcs_status']}"
                )
                self._send_json({"success": True, "output": summary})
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
            return

        if parsed.path in ("/api/analyze-lifetime-gaps", "/api/analyze-history"):
            cfg = load_config()
            github_cfg = cfg.get("github") or cfg.get("node", {})
            identity = github_cfg.get("username") or github_cfg.get("identity", "")
            try:
                report = LEDGER.inspect_timeline_coverage(identity)
                self._send_json({
                    "success": True,
                    "accountCreatedAt": report["baselineDate"],
                    "totalDays": report["totalDays"],
                    "emptyCount": report["emptyCount"],
                    "activeCount": report["activeCount"],
                    "sampleEmpty": report["sampleEmpty"],
                    "sampleActive": report["sampleActive"]
                })
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
            return

        if parsed.path in ("/api/fill-lifetime-gaps", "/api/sync-history"):
            try:
                params = json.loads(body) if body else {}
                cfg = load_config()
                github_cfg = cfg.get("github") or cfg.get("node", {})
                identity = github_cfg.get("username") or github_cfg.get("identity", "")
                email = github_cfg.get("email") or github_cfg.get("contact", "")

                density = params.get("density", "ultra_sparse")
                custom_ratio = float(params.get("customRatio", 0.25))
                max_per_day = int(params.get("maxPerDay", 1))
                max_total = int(params.get("maxTotalCommits", 35))
                skip_w = bool(params.get("skipWeekends", True))

                log_output = LEDGER.synchronize_historical_timeline(
                    identity=identity,
                    email=email,
                    density=density,
                    custom_ratio=custom_ratio,
                    max_per_day=max_per_day,
                    max_total=max_total,
                    skip_weekends=skip_w
                )
                self._send_json({"success": True, "output": log_output})
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
            return

        self.send_response(404)
        self.end_headers()


def run():
    print(f"[+] Core Telemetry Studio running at http://localhost:{PORT}")
    server = http.server.HTTPServer(("127.0.0.1", PORT), DiagnosticStudioHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Studio server terminated.")


if __name__ == "__main__":
    run()
