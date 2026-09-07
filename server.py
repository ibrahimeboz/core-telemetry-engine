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

PORT = 5000
BASE_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = BASE_DIR / "config.json"
WORKFLOW_PATH = BASE_DIR / ".github" / "workflows" / "auto-commit.yml"
WEB_DIR = BASE_DIR / "web"
LOG_FILE_PATH = BASE_DIR / "activity.log"

# -----------------------------------------------------------------------------
# STEALTH MESAJ HAVUZU (80+ Gerçekçi Conventional Commit)
# Tarih, döngü (#1), bot veya otomasyon gibi ele verici hiçbir kelime içermez.
# -----------------------------------------------------------------------------
STEALTH_COMMIT_MESSAGES = [
    # Refactoring & Cleanup
    "refactor: optimize internal loop execution and data flow",
    "refactor: decouple configuration loader from core modules",
    "refactor: simplify modular helper utilities",
    "refactor: clean up redundant conditional checks",
    "refactor: streamline error propagation across service layer",
    "refactor: eliminate duplicate data mapping logic",
    "refactor: modularize event handlers for better maintainability",
    "refactor: standardize internal response parsing methods",
    "refactor: reorganize utility scripts and helper references",
    "refactor: clean up deprecated function arguments",
    # Bug Fixes
    "fix: resolve potential race condition in worker event queue",
    "fix: correct boundary condition when parsing empty payloads",
    "fix: prevent unexpected null reference on missing configuration",
    "fix: handle transient network timeout with retry fallback",
    "fix: correct edge-case in retry policy backoff interval",
    "fix: sanitize input arguments to avoid unexpected type mismatch",
    "fix: handle unhandled exception on stream termination",
    "fix: ensure proper resource cleanup on thread exit",
    "fix: correct subtle off-by-one index calculation",
    "fix: patch edge case in timestamp normalization",
    # Performance & Optimization
    "perf: improve caching mechanism for static lookup tables",
    "perf: reduce redundant memory allocations in hot paths",
    "perf: streamline payload serialization routines",
    "perf: optimize buffer pooling during batch processing",
    "perf: reduce idle CPU overhead in background polling loop",
    "perf: index lookups to reduce sequential search overhead",
    "perf: fine-tune async execution cadence to lower latency",
    # Documentation & Annotations
    "docs: update setup instructions and development notes",
    "docs: improve inline architecture and lifecycle annotations",
    "docs: clarify environment configuration requirements",
    "docs: add explanatory notes for error handling edge-cases",
    "docs: refine docstrings and parameter type specifications",
    "docs: document edge conditions in workflow execution",
    # Code Style & Linting
    "style: format codebase in accordance with project linter",
    "style: remove trailing whitespaces and fix indentation",
    "style: organize imports alphabetically and remove unused references",
    "style: align naming conventions across module interfaces",
    "style: polish code formatting for improved readability",
    # Testing & Verification
    "test: expand unit test assertions for corner cases",
    "test: update mock expectations for worker scheduler",
    "test: add regression tests for payload boundary validation",
    "test: verify telemetry logging output consistency",
    "test: increase test coverage for failure fallback logic",
    # Chores & Maintenance
    "chore: routine dependency check and lockfile sync",
    "chore: update internal telemetry dependencies",
    "chore: minor codebase cleanup and maintenance patch",
    "chore: synchronize project environment variables and defaults",
    "chore: update build script metadata and release flags",
    "chore: periodic sync of runtime diagnostic configurations",
    # CI & Build Setup
    "ci: adjust automated health check parameters",
    "ci: optimize build runner cache hit ratio",
    "ci: fine-tune step execution timeouts in pipeline",
    "ci: update verification workflow triggers and steps",
    # Feature Enhancements
    "feat: enhance logging granularity for service diagnostics",
    "feat: support granular configuration overrides via local file",
    "feat: add lightweight health check probe endpoint",
    "feat: expand diagnostic event telemetry schema"
]

LOG_COMPONENTS = [
    ("core_worker", "worker pool state nominal, active threads: 4"),
    ("telemetry_sync", "metrics packet transmitted successfully"),
    ("cache_engine", "index verification complete, latency: 8ms"),
    ("scheduler", "next execution window validated against policy"),
    ("health_probe", "all runtime health probes reporting healthy"),
    ("data_pipeline", "batch buffer flushed cleanly, 0 drops"),
    ("config_watcher", "configuration hash verified unchanged"),
    ("net_listener", "keep-alive ping acknowledged from upstream node")
]


def load_config():
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


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


def get_stealth_log_entry(timestamp_str):
    component, msg = random.choice(LOG_COMPONENTS)
    latency = random.randint(4, 28)
    return f"[{timestamp_str}] [INFO] {component}: {msg} (latency: {latency}ms)\n"


def get_commit_message(used_messages=None):
    pool = STEALTH_COMMIT_MESSAGES
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
        return False, "Workflow dosyası bulunamadı."

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

        return True, "Workflow kimlik bilgileri senkronize edildi."
    except Exception as e:
        return False, str(e)


def fetch_account_created_at(username):
    """
    GitHub API'sinden kullanıcının hesap açılış tarihini çeker.
    Hesap açılışından öncesine commit atılmasını KESİNLİKLE engeller.
    """
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
        print(f"[!] Hesap acilis tarihi alinamadi: {e}")
    return None


def fetch_account_history_gaps(username):
    """
    Kullanıcının hesap açılış tarihinden bugüne kadar olan GitHub katkı takvimini çeker.
    Boş günleri (data-level == 0) ve dolu günleri (data-level > 0) tespit eder.
    Hesap açılışından önceki günleri KESİNLİKLE LİSTEYE ALMAZ.
    """
    if not username:
        raise ValueError("GitHub kullanıcı adı bulunamadı.")

    account_created_dt = fetch_account_created_at(username)
    if not account_created_dt:
        # Fallback: En fazla 365 gün geriye git
        account_created_dt = datetime.now() - timedelta(days=365)

    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"GitHub katkı takvimi çekilemedi: {e}")

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


def run_one_time_gap_fill(config, density="ultra_sparse", custom_ratio=0.25, max_per_day=1, max_total=35, skip_weekends=True):
    """
    Hesap açılış tarihinden bugüne kadar olan boş günleri 'ultra-seyrek' veya 'dengeli'
    şekilde bir seferlik doldurur. Dolu günlere asla dokunmaz.
    """
    username = config.get("github", {}).get("username", "").strip()
    email = config.get("github", {}).get("email", "").strip() or "dev@noreply.github.com"
    git_exe = get_git_executable()

    subprocess.run([git_exe, "config", "user.name", username], cwd=str(BASE_DIR))
    subprocess.run([git_exe, "config", "user.email", email], cwd=str(BASE_DIR))

    empty_days, active_days, total_days, account_created_dt = fetch_account_history_gaps(username)

    if not empty_days:
        return "[i] Tebrikler! Hesap açılışınızdan bu yana hiç boş gün bulunmuyor."

    # Yoğunluk (Density) Kuralları
    if density == "ultra_sparse":
        ratio = 0.20  # Boş günlerin sadece %20'si
        per_day = 1
        limit = min(max_total, 30)
        skip_w = True
    elif density == "sparse":
        ratio = 0.35  # Boş günlerin %35'i
        per_day = 1
        limit = min(max_total, 45)
        skip_w = True
    elif density == "moderate":
        ratio = 0.50
        per_day = min(max_per_day, 2)
        limit = min(max_total, 60)
        skip_w = skip_weekends
    else:  # custom
        ratio = max(0.10, min(custom_ratio, 0.70))
        per_day = max(1, min(max_per_day, 3))
        limit = max(1, min(max_total, 80))
        skip_w = skip_weekends

    # Hafta sonu filtrelemesi
    candidate_days = []
    for d_str in empty_days:
        dt = datetime.strptime(d_str, "%Y-%m-%d")
        if skip_w and dt.weekday() in (5, 6):
            continue
        candidate_days.append(d_str)

    if not candidate_days:
        candidate_days = empty_days

    # Doğal seyrek dağılım: Rastgele günleri seç
    target_count = int(len(candidate_days) * ratio)
    target_count = max(1, min(target_count, limit // per_day if limit >= per_day else limit))

    selected_days = random.sample(candidate_days, min(target_count, len(candidate_days)))
    selected_days.sort()  # Geçmişten bugüne KRONOLOJİK sırala!

    total_commits = 0
    filled_report = []

    for date_str in selected_days:
        if total_commits >= limit:
            break

        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        commits_today = per_day
        if total_commits + commits_today > limit:
            commits_today = limit - total_commits

        # Saat sıralaması (09:30 - 22:15)
        day_times = []
        for _ in range(commits_today):
            r_hour = random.randint(9, 22)
            r_min = random.randint(0, 59)
            r_sec = random.randint(0, 59)
            day_times.append((r_hour, r_min, r_sec))
        day_times.sort()

        used_for_day = set()

        for hour, minute, sec in day_times:
            commit_dt = target_date.replace(hour=hour, minute=minute, second=sec)
            iso_date_str = commit_dt.strftime("%Y-%m-%d %H:%M:%S")

            with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(get_stealth_log_entry(iso_date_str))

            msg = get_commit_message(used_for_day)

            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = iso_date_str
            env["GIT_COMMITTER_DATE"] = iso_date_str

            subprocess.run([git_exe, "add", "activity.log"], cwd=str(BASE_DIR))
            subprocess.run(
                [git_exe, "-c", f"user.name={username}", "-c", f"user.email={email}", "commit", "--date", iso_date_str, "-m", msg],
                cwd=str(BASE_DIR),
                env=env,
                capture_output=True
            )
            total_commits += 1

        filled_report.append(f"- {date_str}: {commits_today} commit")

    # Push
    push_res = subprocess.run([git_exe, "push", "-u", "origin", "main"], cwd=str(BASE_DIR), capture_output=True, text=True, encoding="utf-8")
    push_out = (push_res.stdout or "") + (push_res.stderr or "")

    summary = (
        f"[✓] Tek Seferlik Geçmiş Doldurma Tamamlandı!\n"
        f"Kapsam: Hesap Açılışı ({account_created_dt.strftime('%d.%m.%Y')}) -> Bugün ({total_days} gün incelendi)\n"
        f"  • Zaten Dolu Günler (Dokunulmadı): {len(active_days)}\n"
        f"  • Boş Günler: {len(empty_days)}\n"
        f"  • Seçilen Seyrek Günler: {len(selected_days)} gün (Doluluk: %{int(ratio*100)})\n"
        f"  • Üretilen Toplam Commit: {total_commits} adet (Güvenli kota: {limit})\n\n"
        f"Son Doldurulan Günler:\n" + "\n".join(filled_report[-5:] if filled_report else ["(Doldurulan gün yok)"]) +
        f"\n\n$ git push -u origin main\n{push_out.strip()}"
    )
    return summary


def run_single_test_commit(config):
    """
    Kullanıcının sistemi test etmesi için anlık 1 adet doğal commit üretip pushlar.
    """
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    git_exe = get_git_executable()
    username = config.get("github", {}).get("username", "").strip() or "developer"
    email = config.get("github", {}).get("email", "").strip() or "dev@noreply.github.com"

    subprocess.run([git_exe, "config", "user.name", username], cwd=str(BASE_DIR))
    subprocess.run([git_exe, "config", "user.email", email], cwd=str(BASE_DIR))

    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(get_stealth_log_entry(now_utc))

    msg = get_commit_message()
    subprocess.run([git_exe, "add", "activity.log"], cwd=str(BASE_DIR))
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

    return f"[*] Test Commit Atıldı: {msg}\n{commit_out}\n\n$ git push -u origin main\n{push_out.strip()}"


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
                last_commit = log_res.stdout.strip() if log_res.returncode == 0 else "Henüz commit yok."
            except Exception:
                last_commit = "Git bulunamadı."

            status_data = {
                "lastCommit": last_commit,
                "workflowExists": WORKFLOW_PATH.exists(),
                "logFileExists": LOG_FILE_PATH.exists()
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
                    "message": "Ayarlar kaydedildi.",
                    "workflowSync": {"success": ok, "detail": msg}
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        if parsed.path == "/api/trigger-test":
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

        if parsed.path == "/api/analyze-lifetime-gaps":
            cfg = load_config()
            username = cfg.get("github", {}).get("username", "").strip()
            try:
                empty_days, active_days, total_days, account_created_dt = fetch_account_history_gaps(username)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "accountCreatedAt": account_created_dt.strftime("%d.%m.%Y") if account_created_dt else "Bilinmiyor",
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

        if parsed.path == "/api/fill-lifetime-gaps":
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
    print(f"[+] Web Paneli başlatılıyor: http://localhost:{PORT}")
    server = http.server.HTTPServer(("127.0.0.1", PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Sunucu kapatıldı.")


if __name__ == "__main__":
    run()
