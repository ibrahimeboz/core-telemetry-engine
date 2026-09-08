import http.server
import json
import os
import random
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.telemetry.collector import SystemMetricsCollector
from src.telemetry.engine import TelemetryEngine
from src.telemetry.storage import TelemetryStorage

PORT = 5000
BASE_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = BASE_DIR / "config.json"
WORKFLOW_PATH = BASE_DIR / ".github" / "workflows" / "ci.yml"
WEB_DIR = BASE_DIR / "web"

STORAGE = TelemetryStorage(root_dir=BASE_DIR)
COLLECTOR = SystemMetricsCollector(node_id="node-main")
ENGINE = TelemetryEngine()

CONVENTIONAL_COMMIT_MESSAGES = [
    "perf(profiler): calibrate event loop latency thresholds",
    "test(engine): update metric validation and boundary assertions",
    "chore(benchmarks): sync telemetry diagnostic snapshot",
    "refactor(storage): streamline atomic snapshot persistence",
    "fix(collector): normalize system thread count metrics",
    "docs(telemetry): update diagnostic snapshot specifications",
    "perf(engine): optimize percentile computation in latency buffer",
    "chore(deps): verify runtime integrity and dependency tree",
    "ci(diagnostics): calibrate periodic health check thresholds",
    "feat(telemetry): expand platform hardware probe diagnostics",
    "refactor(collector): decouple platform probing routines",
    "fix(engine): handle zero-sample edge condition in percentiles",
    "style(telemetry): align parameter type annotations with schema",
    "perf(collector): reduce buffer allocation overhead in hot path",
    "chore(registry): update diagnostic cycle sequence index",
    "refactor(engine): simplify rolling window buffer retention",
    "perf(storage): minimize file descriptor overhead in snapshot writer",
    "fix(collector): correct disk usage rounding precision",
    "test(storage): add regression coverage for concurrent atomic writes",
    "docs(architecture): clarify telemetry collection lifecycle"
]


def load_config():
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_git_executable():
    git_path = shutil.which("git")
    if git_path:
        return git_path
    fallback = Path(r"C:\Program Files\Git\cmd\git.exe")
    if fallback.exists():
        return str(fallback)
    return "git"


def get_commit_message(used_messages=None):
    pool = CONVENTIONAL_COMMIT_MESSAGES
    if used_messages is not None:
        available = [m for m in pool if m not in used_messages]
        if available:
            pool = available

    msg = random.choice(pool)
    if used_messages is not None:
        used_messages.add(msg)
    return msg


def sync_workflow_file(config):
    if not WORKFLOW_PATH.exists():
        return False, "CI workflow file not found."

    try:
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        username = config.get("github", {}).get("username", "developer")
        content = re.sub(
            r'git config --global user\.name\s+"[^"]*"',
            f'git config --global user.name "{username}"',
            content
        )

        email = config.get("github", {}).get("email", "")
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


def fetch_account_created_at(username):
    if not username:
        return None
    url = f"https://api.github.com/users/{username}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            created_str = data.get("created_at")
            if created_str:
                return datetime.strptime(created_str[:10], "%Y-%m-%d")
    except Exception as e:
        print(f"Failed to fetch account creation date: {e}")
    return None


def fetch_account_history_gaps(username):
    if not username:
        raise ValueError("GitHub username is required.")

    account_created_dt = fetch_account_created_at(username)
    if not account_created_dt:
        account_created_dt = datetime.now() - timedelta(days=365)

    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"Unable to retrieve GitHub contributions graph: {e}")

    cells = re.findall(r'<td[^>]*class=[\"\']ContributionCalendar-day[\"\'][^>]*>', html)
    date_level_map = {}
    for cell in cells:
        m_date = re.search(r'data-date=[\"\'](\d{4}-\d{2}-\d{2})[\"\']', cell)
        m_level = re.search(r'data-level=[\"\'](\d+)[\"\']', cell)
        if m_date and m_level:
            date_level_map[m_date.group(1)] = int(m_level.group(1))

    today = datetime.now()
    days_total = (today - account_created_dt).days

    empty_days = []
    active_days = []

    for d in range(days_total, -1, -1):
        target_dt = today - timedelta(days=d)
        if target_dt < account_created_dt:
            continue

        d_str = target_dt.strftime("%Y-%m-%d")
        lvl = date_level_map.get(d_str, 0)
        if lvl == 0:
            empty_days.append(d_str)
        else:
            active_days.append(d_str)

    return empty_days, active_days, days_total + 1, account_created_dt


def generate_synthetic_historical_snapshot(timestamp_str, node_id="node-historical"):
    """Produces realistic metrics matching a historical timestamp for archival sync."""
    sample = COLLECTOR.collect()
    sample["timestamp"] = timestamp_str + "Z"
    sample["node_id"] = node_id
    sample["metrics"]["cpu_load_pct"] = round(random.uniform(18.0, 44.0), 2)
    sample["metrics"]["event_loop_latency_ms"] = round(random.uniform(0.35, 1.85), 3)
    sample["metrics"]["throughput_qps"] = round(random.uniform(920.0, 2150.0), 1)

    STORAGE.write_snapshot({
        "metadata": {
            "node_id": node_id,
            "version": "1.2.4",
            "last_synced_utc": sample["timestamp"],
            "operational_status": "OPTIMAL",
        },
        "system": sample["platform"],
        "metrics": sample["metrics"],
    })

    STORAGE.append_benchmark_record({
        "timestamp": sample["timestamp"],
        "iterations": random.randint(25, 40),
        "percentiles": {
            "p50": round(sample["metrics"]["event_loop_latency_ms"] * 0.9, 3),
            "p95": sample["metrics"]["event_loop_latency_ms"],
            "p99": round(sample["metrics"]["event_loop_latency_ms"] * 1.15, 3),
        },
        "throughput_qps": sample["metrics"]["throughput_qps"],
        "memory_mb": sample["metrics"]["memory_usage_mb"],
    })


def run_one_time_gap_fill(config, density="ultra_sparse", custom_ratio=0.25, max_per_day=1, max_total=35, skip_weekends=True):
    username = config.get("github", {}).get("username", "").strip()
    email = config.get("github", {}).get("email", "").strip() or "dev@noreply.github.com"
    git_exe = get_git_executable()

    subprocess.run([git_exe, "config", "user.name", username], cwd=str(BASE_DIR))
    subprocess.run([git_exe, "config", "user.email", email], cwd=str(BASE_DIR))

    empty_days, active_days, total_days, account_created_dt = fetch_account_history_gaps(username)

    if not empty_days:
        return "[i] No unrecorded telemetry intervals found since repository creation."

    if density == "ultra_sparse":
        ratio = 0.20
        per_day = 1
        limit = min(max_total, 30)
        skip_w = True
    elif density == "sparse":
        ratio = 0.35
        per_day = 1
        limit = min(max_total, 45)
        skip_w = True
    elif density == "moderate":
        ratio = 0.50
        per_day = min(max_per_day, 2)
        limit = min(max_total, 60)
        skip_w = skip_weekends
    else:
        ratio = max(0.10, min(custom_ratio, 0.70))
        per_day = max(1, min(max_per_day, 3))
        limit = max(1, min(max_total, 80))
        skip_w = skip_weekends

    candidate_days = []
    for d_str in empty_days:
        dt = datetime.strptime(d_str, "%Y-%m-%d")
        if skip_w and dt.weekday() in (5, 6):
            continue
        candidate_days.append(d_str)

    if not candidate_days:
        candidate_days = empty_days

    target_count = int(len(candidate_days) * ratio)
    target_count = max(1, min(target_count, limit // per_day if limit >= per_day else limit))

    selected_days = random.sample(candidate_days, min(target_count, len(candidate_days)))
    selected_days.sort()

    total_commits = 0
    filled_report = []

    for date_str in selected_days:
        if total_commits >= limit:
            break

        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        commits_today = per_day
        if total_commits + commits_today > limit:
            commits_today = limit - total_commits

        day_times = []
        for _ in range(commits_today):
            r_hour = random.randint(9, 21)
            r_min = random.randint(0, 59)
            r_sec = random.randint(0, 59)
            day_times.append((r_hour, r_min, r_sec))
        day_times.sort()

        used_for_day = set()

        for hour, minute, sec in day_times:
            commit_dt = target_date.replace(hour=hour, minute=minute, second=sec)
            iso_date_str = commit_dt.strftime("%Y-%m-%dT%H:%M:%S")

            generate_synthetic_historical_snapshot(iso_date_str)
            msg = get_commit_message(used_for_day)

            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = iso_date_str
            env["GIT_COMMITTER_DATE"] = iso_date_str

            subprocess.run(
                [git_exe, "add", "reports/telemetry_snapshot.json", "benchmarks/benchmark_results.json"],
                cwd=str(BASE_DIR)
            )
            subprocess.run(
                [git_exe, "-c", f"user.name={username}", "-c", f"user.email={email}", "commit", "--date", iso_date_str, "-m", msg],
                cwd=str(BASE_DIR),
                env=env,
                capture_output=True
            )
            total_commits += 1

        filled_report.append(f"- {date_str}: {commits_today} telemetry sync")

    push_res = subprocess.run([git_exe, "push", "-u", "origin", "main"], cwd=str(BASE_DIR), capture_output=True, text=True, encoding="utf-8")
    push_out = (push_res.stdout or "") + (push_res.stderr or "")

    summary = (
        f"[✓] Historical Telemetry Archival Sync Complete.\n"
        f"Timeline: Creation Date ({account_created_dt.strftime('%d.%m.%Y')}) -> Present ({total_days} days analyzed)\n"
        f"  • Existing Active Windows: {len(active_days)}\n"
        f"  • Available Archival Slots: {len(empty_days)}\n"
        f"  • Synchronized Sampling Days: {len(selected_days)} days (Ratio: {int(ratio*100)}%)\n"
        f"  • Telemetry Snapshots Recorded: {total_commits} records (Safe limit: {limit})\n\n"
        f"Recent Synchronized Days:\n" + "\n".join(filled_report[-5:] if filled_report else ["(None)"]) +
        f"\n\n$ git push -u origin main\n{push_out.strip()}"
    )
    return summary


def run_single_test_commit(config):
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    git_exe = get_git_executable()
    username = config.get("github", {}).get("username", "").strip() or "developer"
    email = config.get("github", {}).get("email", "").strip() or "dev@noreply.github.com"

    subprocess.run([git_exe, "config", "user.name", username], cwd=str(BASE_DIR))
    subprocess.run([git_exe, "config", "user.email", email], cwd=str(BASE_DIR))

    generate_synthetic_historical_snapshot(now_utc.replace("Z", ""), node_id="node-diagnostic")
    msg = get_commit_message()

    subprocess.run(
        [git_exe, "add", "reports/telemetry_snapshot.json", "benchmarks/benchmark_results.json"],
        cwd=str(BASE_DIR)
    )
    res = subprocess.run(
        [git_exe, "-c", f"user.name={username}", "-c", f"user.email={email}", "commit", "-m", msg],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    commit_out = res.stdout.strip() if res.returncode == 0 else res.stderr.strip()

    push_res = subprocess.run([git_exe, "push", "-u", "origin", "main"], cwd=str(BASE_DIR), capture_output=True, text=True, encoding="utf-8")
    push_out = (push_res.stdout or "") + (push_res.stderr or "")

    return f"[*] Diagnostic Telemetry Snapshot Recorded: {msg}\n{commit_out}\n\n$ git push -u origin main\n{push_out.strip()}"


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/config":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            cfg = load_config()
            self.wfile.write(json.dumps(cfg).encode("utf-8"))
            return

        if parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()

            try:
                log_res = subprocess.run(
                    ["git", "log", "-1", "--pretty=format:%h - %an: %s (%cr)"],
                    cwd=str(BASE_DIR),
                    capture_output=True,
                    text=True,
                    encoding="utf-8"
                )
                last_commit = log_res.stdout.strip() if log_res.returncode == 0 else "Initial repository baseline"
            except Exception:
                last_commit = "Git unavailable"

            latest_snap = STORAGE.read_latest_snapshot()
            status_data = {
                "lastCommit": last_commit,
                "workflowExists": WORKFLOW_PATH.exists(),
                "snapshotExists": STORAGE.snapshot_file.exists(),
                "latestMetrics": latest_snap.get("metrics", {})
            }
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/config":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                new_config = json.loads(body)
                save_config(new_config)
                ok, msg = sync_workflow_file(new_config)

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "message": "Settings saved successfully.",
                    "workflowSync": {"success": ok, "detail": msg}
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        if parsed.path in ("/api/trigger-test", "/api/trigger-diagnostic"):
            cfg = load_config()
            log_output = run_single_test_commit(cfg)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "output": log_output
            }).encode("utf-8"))
            return

        if parsed.path in ("/api/analyze-lifetime-gaps", "/api/analyze-history"):
            cfg = load_config()
            username = cfg.get("github", {}).get("username", "").strip()
            try:
                empty_days, active_days, total_days, account_created_dt = fetch_account_history_gaps(username)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "accountCreatedAt": account_created_dt.strftime("%d.%m.%Y") if account_created_dt else "Unknown",
                    "totalDays": total_days,
                    "emptyCount": len(empty_days),
                    "activeCount": len(active_days),
                    "sampleEmpty": empty_days[:5],
                    "sampleActive": active_days[:5]
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        if parsed.path in ("/api/fill-lifetime-gaps", "/api/sync-history"):
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                params = json.loads(body) if body else {}
                cfg = load_config()
                density = params.get("density", "ultra_sparse")
                custom_ratio = float(params.get("customRatio", 0.25))
                max_per_day = int(params.get("maxPerDay", 1))
                max_total = int(params.get("maxTotalCommits", 35))
                skip_w = bool(params.get("skipWeekends", True))

                log_output = run_one_time_gap_fill(cfg, density, custom_ratio, max_per_day, max_total, skip_w)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "output": log_output
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


def run():
    print(f"[+] Core Telemetry Studio running at http://localhost:{PORT}")
    server = http.server.HTTPServer(("127.0.0.1", PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Studio server terminated.")


if __name__ == "__main__":
    run()
