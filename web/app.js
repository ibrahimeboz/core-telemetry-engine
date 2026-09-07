// ==========================================================================
// Telemetry & Activity Control Center - Client Controller
// ==========================================================================

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

// Lifetime Gap Elements
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

// Helper: Toast Notification
function showToast(msg, isError = false) {
  toastText.textContent = msg;
  toast.style.borderColor = isError ? "#ef4444" : "var(--indigo)";
  toast.classList.remove("hidden");

  setTimeout(() => {
    toast.classList.add("hidden");
  }, 3500);
}

// Helper: Append to Live Console
function logToConsole(title, content) {
  const time = new Date().toLocaleTimeString();
  const entry = `\n[${time}] === ${title} ===\n${content}\n`;
  consoleStream.textContent += entry;
  consoleStream.scrollTop = consoleStream.scrollHeight;
}

// Setup Density Card Selection
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

// Fetch Initial Config
async function fetchConfig() {
  try {
    const res = await fetch("/api/config");
    if (!res.ok) throw new Error("Ayar verisi alinamadi");
    const data = await res.json();
    state.config = data;

    if (data.github) {
      cfgUsernameInput.value = data.github.username || "";
      cfgEmailInput.value = data.github.email || "";
      navUsername.textContent = data.github.username || "Geliştirici";
    }

    if (data.automation) {
      cfgMinCommitsInput.value = data.automation.minCommits || 1;
      cfgMaxCommitsInput.value = data.automation.maxCommits || 3;
      cfgSkipWeekendsToggle.checked = data.automation.skipWeekends !== false;
    }

    if (data.gapFiller) {
      const mode = data.gapFiller.density || "ultra_sparse";
      const targetCard = document.getElementById(`card-${mode.replace("_", "-")}`);
      if (targetCard) targetCard.click();
    }
  } catch (err) {
    logToConsole("Bağlantı Hatası", "Konfigürasyon okunamadı: " + err.message);
  }
}

// Fetch Status Info
async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return;
    const data = await res.json();
    if (data.lastCommit) {
      logToConsole("Mevcut Durum", `Son Commit: ${data.lastCommit}\nWorkflow Hazır: ${data.workflowExists ? "Evet" : "Hayır"}`);
    }
  } catch (err) {
    console.error("Status error:", err);
  }
}

// Save Daily Automation Settings
dailyForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    github: {
      username: cfgUsernameInput.value.trim(),
      email: cfgEmailInput.value.trim()
    },
    automation: {
      enabled: true,
      minCommits: parseInt(cfgMinCommitsInput.value, 10) || 1,
      maxCommits: parseInt(cfgMaxCommitsInput.value, 10) || 3,
      skipWeekends: cfgSkipWeekendsToggle.checked
    },
    gapFiller: {
      density: state.selectedDensity,
      customRatio: (parseInt(customRatioInput.value, 10) || 25) / 100,
      maxPerDay: parseInt(customMaxPerDayInput.value, 10) || 1,
      maxTotalCommits: parseInt(customMaxTotalInput.value, 10) || 35,
      skipWeekends: true
    }
  };

  btnSaveCfg.disabled = true;
  btnSaveCfg.innerHTML = `<span>Kaydediliyor...</span>`;

  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    if (result.success) {
      showToast("Ayarlar kaydedildi ve workflow senkronize edildi!");
      navUsername.textContent = payload.github.username;
      logToConsole("Ayar Güncelleme", `Yeni Parametreler:\n• Kullanıcı: ${payload.github.username} <${payload.github.email}>\n• Günlük Min-Max: ${payload.automation.minCommits} - ${payload.automation.maxCommits} commit\n• Hafta Sonu Tatili: ${payload.automation.skipWeekends ? "Aktif" : "Kapalı"}`);
    } else {
      showToast("Hata: " + result.error, true);
    }
  } catch (err) {
    showToast("Sunucuya ulaşılamadı!", true);
  } finally {
    btnSaveCfg.disabled = false;
    btnSaveCfg.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
        <polyline points="17 21 17 13 7 13 7 21"></polyline>
        <polyline points="7 3 7 8 15 8"></polyline>
      </svg>
      <span>Ayarları Kaydet & Senkronize Et</span>
    `;
  }
});

// Trigger 1 Single Test Commit
btnTriggerTest.addEventListener("click", async () => {
  if (!confirm("Anlık olarak 1 adet doğal test commit üretilip GitHub'a pushlanacak. Onaylıyor musun?")) {
    return;
  }

  btnTriggerTest.disabled = true;
  btnTriggerTest.innerHTML = `<span>Commit Atılıyor...</span>`;
  logToConsole("Test Tetikleme", "Yerel tekil test commit süreci yürütülüyor...");

  try {
    const res = await fetch("/api/trigger-test", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      logToConsole("İşlem Başarılı", data.output);
      showToast("Doğal test commit'i pushlandı!");
      fetchStatus();
    } else {
      logToConsole("Hata", data.error || "Bilinmeyen hata");
      showToast("Hata oluştu!", true);
    }
  } catch (err) {
    logToConsole("İletişim Hatası", err.message);
    showToast("Sunucu hatası!", true);
  } finally {
    btnTriggerTest.disabled = false;
    btnTriggerTest.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      <span>Tekil Test Commit At</span>
    `;
  }
});

// 1. Analyze Lifetime Gaps (Preview)
btnAnalyzeLifetime.addEventListener("click", async () => {
  const username = cfgUsernameInput.value.trim();
  if (!username) {
    showToast("Lütfen önce GitHub kullanıcı adınızı kaydedin!", true);
    return;
  }

  btnAnalyzeLifetime.disabled = true;
  btnAnalyzeLifetime.innerHTML = `<span>GitHub Taranıyor...</span>`;
  logToConsole("Hesap Geçmişi Analizi", `Kullanıcı '${username}' için hesap açılışından bugüne canlı takvim taranıyor...`);

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

      const report = `[✓] Hesap Geçmişi Canlı Analiz Raporu:
• 🛡️ Hesap Açılış Tarihi: ${data.accountCreatedAt} (Öncesine ASLA dokunulamaz)
• İncelenen Toplam Gün: ${data.totalDays} gün (${data.accountCreatedAt} -> Bugün)
• Zaten Dolu Olan Günler (Dokunulmayacak): ${data.activeCount} gün
  ${data.activeCount > 0 ? `(Örnek: ${sampleActive}...)` : "(Dolu gün yok)"}
• Boş Tespit Edilen Günler: ${data.emptyCount} gün
  ${data.emptyCount > 0 ? `(Örnek: ${sampleEmpty}...)` : "(Tüm günler zaten dolu)"}

Seçili Doldurma Modu: ${state.selectedDensity.toUpperCase()}
Bilgi: 2. butona bastığınızda sistem bu ${data.emptyCount} boş gün arasından organik olarak yalnızca seyrek günleri seçip güvenle dolduracaktır.`;

      logToConsole("Analiz Özeti", report);
      showToast(`Analiz tamamlandı: ${data.emptyCount} boş gün bulundu!`);
    } else {
      logToConsole("Analiz Hatası", data.error);
      showToast("Analiz başarısız!", true);
    }
  } catch (err) {
    logToConsole("Bağlantı Hatası", err.message);
    showToast("Sunucuya ulaşılamadı!", true);
  } finally {
    btnAnalyzeLifetime.disabled = false;
    btnAnalyzeLifetime.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
      <span>1. Hesap Geçmişini Canlı Analiz Et</span>
    `;
  }
});

// 2. Fill Lifetime Gaps (One-Time Execution)
btnFillLifetime.addEventListener("click", async () => {
  const density = state.selectedDensity;
  let desc = "";

  if (density === "ultra_sparse") {
    desc = "Çok Seyrek Mod (%20 Doluluk, gün başına 1 commit, hafta sonları %100 kapalı, maks 30 commit)";
  } else if (density === "sparse") {
    desc = "Dengeli Seyrek Mod (%35 Doluluk, gün başına 1 commit, maks 45 commit)";
  } else {
    desc = `Özel Mod (%${customRatioInput.value} Doluluk, maks ${customMaxTotalInput.value} commit)`;
  }

  const confirmMsg = `Hesap açılışınızdan (${state.accountCreatedAt}) bugüne kadarki boş günler doldurulacak:\n\n` +
    `• Seçilen Mod: ${desc}\n` +
    `• Hesap Açılışından Öncesine: ASLA DOKUNULMAZ\n` +
    `• Dolu Günlere: ASLA DOKUNULMAZ\n` +
    `• Mesaj Havuzu: 80+ Conventional Commit (Stealth)\n\n` +
    `İşlem yürütülüp GitHub'a pushlansın mı?`;

  if (!confirm(confirmMsg)) {
    return;
  }

  btnFillLifetime.disabled = true;
  btnFillLifetime.innerHTML = `<span>Seyrek Dolduruluyor...</span>`;
  logToConsole("Tek Seferlik Doldurma", `Hesap açılışından bu yana boş günler ${density} modunda mühürleniyor...`);

  try {
    const payload = {
      density: density,
      customRatio: (parseInt(customRatioInput.value, 10) || 25) / 100,
      maxPerDay: parseInt(customMaxPerDayInput.value, 10) || 1,
      maxTotalCommits: parseInt(customMaxTotalInput.value, 10) || 35,
      skipWeekends: true
    };

    const res = await fetch("/api/fill-lifetime-gaps", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (data.success) {
      logToConsole("Doldurma Raporu", data.output);
      showToast("Tebrikler! Hesap geçmişi doğal ve seyrek ritimle dolduruldu!");
      fetchStatus();
    } else {
      logToConsole("Doldurma Hatası", data.error);
      showToast("Hata oluştu!", true);
    }
  } catch (err) {
    logToConsole("Bağlantı Hatası", err.message);
    showToast("Sunucu hatası!", true);
  } finally {
    btnFillLifetime.disabled = false;
    btnFillLifetime.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
      </svg>
      <span>2. Boş Günleri Seyrek Doldur ve Pushla</span>
    `;
  }
});

// Clear Console
btnClearConsole.addEventListener("click", () => {
  consoleStream.textContent = "Konsol temizlendi. Sistem hazır.\n";
});

// Init
fetchConfig();
fetchStatus();
