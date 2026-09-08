// Core Telemetry Engine - Diagnostic Studio Controller

const state = {
  config: null,
  accountCreatedAt: "05.09.2025",
  selectedDensity: "ultra_sparse"
};

// DOM Elements
const navUsername = document.getElementById("nav-username");
const navCreatedAt = document.getElementById("nav-created-at");
const cfgUsernameInput = document.getElementById("cfg-username");
const cfgEmailInput = document.getElementById("cfg-email");
const cfgMinCommitsInput = document.getElementById("cfg-min-commits");
const cfgMaxCommitsInput = document.getElementById("cfg-max-commits");
const cfgSkipWeekendsToggle = document.getElementById("cfg-skip-weekends");
const dailyForm = document.getElementById("daily-settings-form");
const btnSaveCfg = document.getElementById("btn-save-cfg");
const btnTriggerTest = document.getElementById("btn-trigger-test");

// Historical Elements
const densityCards = document.querySelectorAll(".density-card");
const customDrawer = document.getElementById("custom-density-drawer");
const customRatioInput = document.getElementById("custom-ratio");
const customMaxPerDayInput = document.getElementById("custom-max-per-day");
const customMaxTotalInput = document.getElementById("custom-max-total");
const btnAnalyzeLifetime = document.getElementById("btn-analyze-lifetime");
const btnFillLifetime = document.getElementById("btn-fill-lifetime");

// Console & Toast
const consoleStream = document.getElementById("console-stream");
const btnClearConsole = document.getElementById("btn-clear-console");
const toast = document.getElementById("toast");
const toastText = document.getElementById("toast-text");

function showToast(msg, isError = false) {
  toastText.textContent = msg;
  toast.style.borderColor = isError ? "#ef4444" : "var(--indigo)";
  toast.classList.remove("hidden");

  setTimeout(() => {
    toast.classList.add("hidden");
  }, 3500);
}

function logToConsole(title, content) {
  const time = new Date().toLocaleTimeString();
  const entry = `\n[${time}] === ${title} ===\n${content}\n`;
  consoleStream.textContent += entry;
  consoleStream.scrollTop = consoleStream.scrollHeight;
}

densityCards.forEach(card => {
  card.addEventListener("click", () => {
    densityCards.forEach(c => c.classList.remove("selected"));
    card.classList.add("selected");

    const radio = card.querySelector("input[type='radio']");
    if (radio) {
      radio.checked = true;
      state.selectedDensity = radio.value;
    }

    if (state.selectedDensity === "custom") {
      customDrawer.classList.remove("hidden");
    } else {
      customDrawer.classList.add("hidden");
    }
  });
});

async function fetchConfig() {
  try {
    const res = await fetch("/api/config");
    if (!res.ok) throw new Error("Unable to retrieve config");
    const data = await res.json();
    state.config = data;

    if (data.github) {
      cfgUsernameInput.value = data.github.username || "";
      cfgEmailInput.value = data.github.email || "";
      navUsername.textContent = data.github.username || "Developer";
    }

    const tel = data.telemetry || data.automation;
    if (tel) {
      cfgMinCommitsInput.value = tel.minCycles || tel.minCommits || 1;
      cfgMaxCommitsInput.value = tel.maxCycles || tel.maxCommits || 3;
      cfgSkipWeekendsToggle.checked = tel.skipWeekends !== false;
    }

    const arch = data.archivalSync || data.gapFiller;
    if (arch) {
      const mode = arch.density || "ultra_sparse";
      const targetCard = document.getElementById(`card-${mode.replace("_", "-")}`);
      if (targetCard) targetCard.click();
    }
  } catch (err) {
    logToConsole("Connection Status", "Configuration fetch failed: " + err.message);
  }
}

async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return;
    const data = await res.json();
    if (data.lastCommit) {
      logToConsole("Telemetry Status", `Last Commit: ${data.lastCommit}\nCI Workflow: ${data.workflowExists ? "Active" : "Pending"}\nSnapshot File: ${data.snapshotExists ? "Indexed" : "Not Found"}`);
    }
  } catch (err) {
    console.error("Status error:", err);
  }
}

dailyForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    github: {
      username: cfgUsernameInput.value.trim(),
      email: cfgEmailInput.value.trim()
    },
    telemetry: {
      enabled: true,
      minCycles: parseInt(cfgMinCommitsInput.value, 10) || 1,
      maxCycles: parseInt(cfgMaxCommitsInput.value, 10) || 3,
      skipWeekends: cfgSkipWeekendsToggle.checked
    },
    archivalSync: {
      density: state.selectedDensity,
      customRatio: (parseInt(customRatioInput.value, 10) || 25) / 100,
      maxPerDay: parseInt(customMaxPerDayInput.value, 10) || 1,
      maxTotalSnapshots: parseInt(customMaxTotalInput.value, 10) || 35,
      skipWeekends: true
    }
  };

  btnSaveCfg.disabled = true;
  btnSaveCfg.innerHTML = `<span>Saving...</span>`;

  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    if (result.success) {
      showToast("Configuration saved and workflow synchronized.");
      navUsername.textContent = payload.github.username;
      const telCfg = payload.telemetry || {};
      logToConsole("Configuration Update", `Committer: ${payload.github.username} <${payload.github.email}>\nCycles: ${telCfg.minCycles || 1} - ${telCfg.maxCycles || 3}\nWeekend Policy: ${telCfg.skipWeekends ? "Active" : "Disabled"}`);
    } else {
      showToast("Error: " + result.error, true);
    }
  } catch (err) {
    showToast("Server communication error", true);
  } finally {
    btnSaveCfg.disabled = false;
    btnSaveCfg.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
        <polyline points="17 21 17 13 7 13 7 21"></polyline>
        <polyline points="7 3 7 8 15 8"></polyline>
      </svg>
      <span>Save & Sync Configuration</span>
    `;
  }
});

btnTriggerTest.addEventListener("click", async () => {
  if (!confirm("Execute an immediate telemetry diagnostic cycle and synchronize snapshot?")) {
    return;
  }

  btnTriggerTest.disabled = true;
  btnTriggerTest.innerHTML = `<span>Running Cycle...</span>`;
  logToConsole("Diagnostic Execution", "Running local telemetry diagnostic cycle and atomic snapshot sync...");

  try {
    const res = await fetch("/api/trigger-test", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      logToConsole("Execution Output", data.output);
      showToast("Diagnostic cycle completed successfully.");
      fetchStatus();
    } else {
      logToConsole("Error", data.error || "Execution error");
      showToast("Execution failed", true);
    }
  } catch (err) {
    logToConsole("Communication Error", err.message);
    showToast("Server error", true);
  } finally {
    btnTriggerTest.disabled = false;
    btnTriggerTest.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      <span>Execute Diagnostic Cycle</span>
    `;
  }
});

btnAnalyzeLifetime.addEventListener("click", async () => {
  const username = cfgUsernameInput.value.trim();
  if (!username) {
    showToast("Please specify committer username first.", true);
    return;
  }

  btnAnalyzeLifetime.disabled = true;
  btnAnalyzeLifetime.innerHTML = `<span>Querying Registry...</span>`;
  logToConsole("Timeline Analysis", `Querying repository activity timeline for '${username}'...`);

  try {
    const res = await fetch("/api/analyze-lifetime-gaps", { method: "POST" });
    const data = await res.json();

    if (data.success) {
      if (data.accountCreatedAt) {
        state.accountCreatedAt = data.accountCreatedAt;
        navCreatedAt.textContent = data.accountCreatedAt;
      }

      const sampleEmpty = data.sampleEmpty ? data.sampleEmpty.join(", ") : "";
      const sampleActive = data.sampleActive ? data.sampleActive.join(", ") : "";

      const report = `Timeline Inspection Summary:
• Repository Baseline: ${data.accountCreatedAt}
• Total Scope Analyzed: ${data.totalDays} days
• Existing Active Snapshots: ${data.activeCount} intervals ${data.activeCount > 0 ? `(${sampleActive}...)` : ""}
• Unindexed Intervals: ${data.emptyCount} intervals ${data.emptyCount > 0 ? `(${sampleEmpty}...)` : ""}
• Target Sampling Profile: ${state.selectedDensity.toUpperCase()}

Proceed with Step 2 to backfill calibrated telemetry snapshots for selected sampling intervals.`;

      logToConsole("Analysis Report", report);
      showToast(`Timeline query completed: ${data.emptyCount} intervals found.`);
    } else {
      logToConsole("Analysis Failed", data.error || "Unknown response");
      showToast("Analysis query failed", true);
    }
  } catch (err) {
    logToConsole("Request Error", err.message);
    showToast("Unable to communicate with server", true);
  } finally {
    btnAnalyzeLifetime.disabled = false;
    btnAnalyzeLifetime.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
      <span>1. Inspect Timeline Coverage</span>
    `;
  }
});

btnFillLifetime.addEventListener("click", async () => {
  const username = cfgUsernameInput.value.trim();
  if (!username) {
    showToast("Please specify committer username first.", true);
    return;
  }

  const confirmMsg = `Synchronize historical telemetry snapshots using profile: ${state.selectedDensity.toUpperCase()}?\nCalibrated records will be pushed to the repository.`;
  if (!confirm(confirmMsg)) return;

  btnFillLifetime.disabled = true;
  btnFillLifetime.innerHTML = `<span>Synchronizing Archive...</span>`;
  logToConsole("Archival Synchronization", "Executing historical snapshot generation and git sync...");

  const payload = {
    density: state.selectedDensity,
    customRatio: (parseInt(customRatioInput.value, 10) || 25) / 100,
    maxPerDay: parseInt(customMaxPerDayInput.value, 10) || 1,
    maxTotalCommits: parseInt(customMaxTotalInput.value, 10) || 35,
    skipWeekends: true
  };

  try {
    const res = await fetch("/api/fill-lifetime-gaps", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (data.success) {
      logToConsole("Synchronization Result", data.output);
      showToast("Historical telemetry backfill completed.");
      fetchStatus();
    } else {
      logToConsole("Synchronization Failed", data.error || "Error occurred");
      showToast("Backfill failed", true);
    }
  } catch (err) {
    logToConsole("Network Error", err.message);
    showToast("Failed to reach server", true);
  } finally {
    btnFillLifetime.disabled = false;
    btnFillLifetime.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
      </svg>
      <span>2. Synchronize Historical Snapshots</span>
    `;
  }
});

btnClearConsole.addEventListener("click", () => {
  consoleStream.textContent = "Telemetry runtime event stream cleared.\n";
});

// Initialization
fetchConfig();
fetchStatus();
