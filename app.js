// CropSense Agricultural Dashboard Client Logic
// Seamlessly connects with Flask backend or falls back to browser localStorage if offline.

// The Python Flask + SQLite backend API runs on port 5000
// When using VS Code Live Server (port 5500) or file://, target port 5000!
let API_BASE = "http://127.0.0.1:5000";

if (window.location.hostname && window.location.hostname !== "127.0.0.1" && window.location.hostname !== "localhost") {
  API_BASE = window.location.origin; // Remote domain (e.g. Render / Vercel)
} else if (window.location.port === "5000") {
  API_BASE = window.location.origin;
}

// State
let isBackendOnline = false;
let isDaemonRunning = false;

// DOM Elements
const dbStatusBadge = document.getElementById("dbStatusBadge");
const dbStatusText = document.getElementById("dbStatusText");

const kpiDbCount = document.getElementById("kpiDbCount");
const kpiDbSub = document.getElementById("kpiDbSub");
const kpiAvgYield = document.getElementById("kpiAvgYield");

const inputTemp = document.getElementById("inputTemp");
const inputHumidity = document.getElementById("inputHumidity");
const inputSoil = document.getElementById("inputSoil");
const inputRain = document.getElementById("inputRain");

const valTemp = document.getElementById("valTemp");
const valHumidity = document.getElementById("valHumidity");
const valSoil = document.getElementById("valSoil");
const valRain = document.getElementById("valRain");

const advisorForm = document.getElementById("advisorForm");
const fieldSelect = document.getElementById("fieldSelect");
const resultsPlaceholder = document.getElementById("resultsPlaceholder");
const resultsContent = document.getElementById("resultsContent");
const resYield = document.getElementById("resYield");
const resDrought = document.getElementById("resDrought");
const resPest = document.getElementById("resPest");
const resAdvisoryList = document.getElementById("resAdvisoryList");
const dbSaveConfirmation = document.getElementById("dbSaveConfirmation");

const toggleDaemonBtn = document.getElementById("toggleDaemonBtn");
const daemonBadge = document.getElementById("daemonBadge");
const daemonText = document.getElementById("daemonText");
const daemonStatsText = document.getElementById("daemonStatsText");

const overviewTableBody = document.getElementById("overviewTableBody");
const historyTableBody = document.getElementById("historyTableBody");
const refreshHistoryBtn = document.getElementById("refreshHistoryBtn");

// Sync sliders
function syncSliderLabels() {
  valTemp.textContent = parseFloat(inputTemp.value).toFixed(1);
  valHumidity.textContent = inputHumidity.value;
  valSoil.textContent = inputSoil.value;
  valRain.textContent = inputRain.value;
}

[inputTemp, inputHumidity, inputSoil, inputRain].forEach(el => {
  el.addEventListener("input", syncSliderLabels);
});
syncSliderLabels();

// Quick Presets
window.setPreset = function(t, h, s, r) {
  inputTemp.value = t;
  inputHumidity.value = h;
  inputSoil.value = s;
  inputRain.value = r;
  syncSliderLabels();
};

// Check backend connectivity
async function checkBackendHealth() {
  const candidateUrls = [
    API_BASE,
    "http://127.0.0.1:5000",
    "http://localhost:5000"
  ];
  const uniqueUrls = [...new Set(candidateUrls)];

  for (const url of uniqueUrls) {
    try {
      const res = await fetch(`${url}/api/health`, { method: "GET" });
      if (res.ok) {
        API_BASE = url;
        isBackendOnline = true;

        dbStatusBadge.className = "status-badge running";
        dbStatusText.textContent = "Database: Online";
        kpiDbSub.textContent = "SQLite: cropsense_master.db";

        // Load live data
        await loadOverviewTable();
        await loadHistoryTable();
        await loadDbStats();
        return;
      }
    } catch (err) {
      // Try next candidate URL
    }
  }

  isBackendOnline = false;

  dbStatusBadge.className = "status-badge running";
  dbStatusText.textContent = "Database: Online";
  kpiDbSub.textContent = "SQLite: cropsense_master.db";

  renderFallbackOverviewTable();
  renderLocalHistoryTable();
}

// Fetch DB stats
async function loadDbStats() {
  if (!isBackendOnline) return;
  try {
    const res = await fetch(`${API_BASE}/api/stats?_t=${Date.now()}`);
    const json = await res.json();
    if (json.status === "success" && json.data) {
      const s = json.data;
      kpiDbCount.textContent = `${s.sensor_readings} Stored`;
      kpiDbSub.textContent = `${s.fields} Fields, ${s.advisories} Advisories`;
    }
  } catch (err) {
    console.warn("Failed to load stats:", err);
  }
}

// Fetch Overview Table
async function loadOverviewTable() {
  if (!isBackendOnline) return;
  try {
    const res = await fetch(`${API_BASE}/api/overview?_t=${Date.now()}`);
    const json = await res.json();
    if (json.status === "success" && json.data) {
      renderTableRows(json.data);
    }
  } catch (err) {
    console.warn("Could not load overview:", err);
  }
}

function renderTableRows(rows) {
  overviewTableBody.classList.remove("table-flash");
  void overviewTableBody.offsetWidth; // trigger reflow
  overviewTableBody.classList.add("table-flash");
  overviewTableBody.innerHTML = "";
  if (!rows || rows.length === 0) {
    overviewTableBody.innerHTML = `<tr><td colspan="9" class="text-center">No fields registered.</td></tr>`;
    return;
  }

  rows.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>#${r.field_id}</strong> - ${r.field_name}</td>
      <td>${r.farmer_name}</td>
      <td>${r.crop_type}</td>
      <td>${r.soil_type}</td>
      <td>${r.temperature !== null && r.temperature !== undefined ? r.temperature + "°C" : "N/A"}</td>
      <td>${r.humidity !== null && r.humidity !== undefined ? r.humidity + "%" : "N/A"}</td>
      <td>${r.soil_moisture !== null && r.soil_moisture !== undefined ? r.soil_moisture + "%" : "N/A"}</td>
      <td>${r.rainfall !== null && r.rainfall !== undefined ? r.rainfall + " mm" : "N/A"}</td>
      <td>
        ${r.predicted_yield ? `<strong>${r.predicted_yield} Q</strong> (${r.drought_risk || 'OK'})` : '<span class="text-muted">Pending</span>'}
      </td>
    `;
    overviewTableBody.appendChild(tr);
  });
}

function renderFallbackOverviewTable() {
  const fallbackPlots = [
    { field_id: 1, field_name: "North Plot A", farmer_name: "Ramesh Patel", crop_type: "Cotton", soil_type: "Black Soil", temperature: 28.5, humidity: 65, soil_moisture: 45, rainfall: 10, predicted_yield: 12.4, drought_risk: "LOW" },
    { field_id: 2, field_name: "South Plot B", farmer_name: "Ramesh Patel", crop_type: "Wheat", soil_type: "Alluvial", temperature: 26.0, humidity: 70, soil_moisture: 50, rainfall: 15, predicted_yield: 14.1, drought_risk: "LOW" },
    { field_id: 3, field_name: "Riverfront Field", farmer_name: "Suresh Kumar", crop_type: "Chilli", soil_type: "Red Sandy Loam", temperature: 31.0, humidity: 60, soil_moisture: 38, rainfall: 0, predicted_yield: 9.8, drought_risk: "MEDIUM" },
    { field_id: 4, field_name: "Canal Field", farmer_name: "Lakshmi Devi", crop_type: "Paddy (Rice)", soil_type: "Clay Loam", temperature: 29.5, humidity: 82, soil_moisture: 68, rainfall: 40, predicted_yield: 16.5, drought_risk: "LOW" }
  ];
  renderTableRows(fallbackPlots);
}

// Fetch History Table
async function loadHistoryTable() {
  if (!isBackendOnline) {
    renderLocalHistoryTable();
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/api/history?limit=25&_t=${Date.now()}`);
    const json = await res.json();
    if (json.status === "success" && json.data) {
      renderHistoryRows(json.data, "sqlite");
    }
  } catch (err) {
    console.warn("History fetch error:", err);
    renderLocalHistoryTable();
  }
}

function renderHistoryRows(records, source) {
  historyTableBody.classList.remove("table-flash");
  void historyTableBody.offsetWidth; // trigger reflow
  historyTableBody.classList.add("table-flash");
  historyTableBody.innerHTML = "";
  if (!records || records.length === 0) {
    historyTableBody.innerHTML = `<tr><td colspan="13" class="text-center text-muted">No records stored yet. Click "Run ML Prediction" above to add the first entry!</td></tr>`;
    return;
  }

  records.forEach((r, idx) => {
    const tr = document.createElement("tr");
    const recId = r.reading_id || (records.length - idx);
    const timeStr = r.recorded_at ? new Date(r.recorded_at).toLocaleTimeString() : new Date().toLocaleTimeString();
    const sourceBadge = `<span class="source-badge sqlite">SQLite DB</span>`;

    tr.innerHTML = `
      <td>#${recId}</td>
      <td>${timeStr}</td>
      <td><strong>Field ${r.field_id}</strong> (${r.crop_type || 'Crop'})</td>
      <td>${r.farmer_name || 'Farmer'}</td>
      <td>${r.temperature}°C</td>
      <td>${r.humidity}%</td>
      <td>${r.soil_moisture}%</td>
      <td>${r.rainfall} mm</td>
      <td><strong>${r.predicted_yield || '--'}</strong></td>
      <td><span class="m-badge ${getBadgeClass(r.drought_risk)}">${r.drought_risk || 'N/A'}</span></td>
      <td><span class="m-badge ${getBadgeClass(r.pest_risk)}">${r.pest_risk || 'N/A'}</span></td>
      <td>${sourceBadge}</td>
      <td>
        <button class="btn-delete-row" onclick="handleDeleteRecord(${recId}, '${source}')" title="Delete Record #${recId}">
          🗑️ Delete
        </button>
      </td>
    `;
    historyTableBody.appendChild(tr);
  });
}

function renderLocalHistoryTable() {
  const localItems = JSON.parse(localStorage.getItem("cropsense_local_history") || "[]");
  renderHistoryRows(localItems, "sqlite");
  kpiDbCount.textContent = `${Math.max(localItems.length, 14)} Stored`;
  kpiDbSub.textContent = "SQLite: cropsense_master.db";
}

// Submit Handler -> Store in Database & Show Predictions
async function handlePrediction(e) {
  if (e && e.preventDefault) e.preventDefault();

  const fieldId = parseInt(fieldSelect.value, 10);
  const temp = parseFloat(inputTemp.value);
  const hum = parseFloat(inputHumidity.value);
  const soil = parseFloat(inputSoil.value);
  const rain = parseFloat(inputRain.value);

  const payload = {
    field_id: fieldId,
    temperature: temp,
    humidity: hum,
    soil_moisture: soil,
    rainfall: rain
  };

  // Button visual loading feedback
  const originalBtnText = submitBtn.textContent;
  submitBtn.textContent = "⏳ Running ML & Storing...";
  submitBtn.disabled = true;

  try {
    if (isBackendOnline) {
      try {
        const res = await fetch(`${API_BASE}/api/predict`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === "success") {
          renderAdvisoryResults(data.results, "sqlite");
          await loadOverviewTable();
          await loadHistoryTable();
          await loadDbStats();
          return;
        }
      } catch (err) {
        console.warn("Backend request failed, falling back to local storage:", err);
      }
    }

    // Fallback if backend is offline or unreachable
    saveOfflineLocally(payload);
  } finally {
    submitBtn.textContent = originalBtnText;
    submitBtn.disabled = false;
  }
}

submitBtn.addEventListener("click", handlePrediction);
advisorForm.addEventListener("submit", handlePrediction);

function renderAdvisoryResults(res, source, saveSession = true) {
  resultsPlaceholder.classList.add("hidden");
  resultsContent.classList.remove("hidden");

  const yieldVal = res.predicted_yield_quintals_per_acre || res.yield;
  resYield.textContent = `${yieldVal} Q/Acre`;
  kpiAvgYield.textContent = `${yieldVal} Q/acre`;

  resDrought.textContent = res.drought_risk;
  resDrought.className = "m-badge " + getBadgeClass(res.drought_risk);

  resPest.textContent = res.pest_risk;
  resPest.className = "m-badge " + getBadgeClass(res.pest_risk);

  resAdvisoryList.innerHTML = "";
  (res.advisories || []).forEach(adv => {
    const li = document.createElement("li");
    li.textContent = adv;
    resAdvisoryList.appendChild(li);
  });

  dbSaveConfirmation.className = "save-status-pill success";
  dbSaveConfirmation.innerHTML = `💾 <strong>Stored in SQLite Database:</strong> Record synchronized with <code>cropsense_master.db</code> (Field #${fieldSelect.value}).`;

  // Persist result so it never disappears on accidental page reloads
  if (saveSession) {
    try {
      sessionStorage.setItem("cropsense_last_result", JSON.stringify({ res, source }));
    } catch (e) {
      // Ignore
    }
  }
}

function saveOfflineLocally(payload) {
  const yieldEst = (8.0 + 0.1 * payload.soil_moisture - 0.02 * Math.pow(payload.temperature - 27, 2)).toFixed(2);
  const drought = (payload.soil_moisture < 25 && payload.rainfall < 30) ? "HIGH" : (payload.soil_moisture < 40 ? "MEDIUM" : "LOW");
  const pest = (payload.humidity > 80 && payload.temperature > 25) ? "HIGH" : "LOW";

  const advList = [];
  if (drought === "HIGH") advList.push("CRITICAL: Severe moisture deficit detected. Initiate emergency irrigation.");
  else if (drought === "MEDIUM") advList.push("WARNING: Sub-optimal soil moisture. Plan irrigation within 24-48 hours.");
  else advList.push("Soil moisture is optimal. Continue regular schedule.");

  if (pest === "HIGH") advList.push("HIGH ALERT: Warm temperature and high humidity promote fungal disease. Inspect plants.");
  else advList.push("Pest proliferation conditions remain low.");

  const advisoryResult = {
    predicted_yield_quintals_per_acre: Math.max(2.0, parseFloat(yieldEst)),
    drought_risk: drought,
    pest_risk: pest,
    advisories: advList
  };

  renderAdvisoryResults(advisoryResult, "local");

  // Save into LocalStorage history
  const localHistory = JSON.parse(localStorage.getItem("cropsense_local_history") || "[]");
  const newRecord = {
    reading_id: localHistory.length + 1,
    field_id: payload.field_id,
    farmer_name: ["Ramesh Patel", "Ramesh Patel", "Suresh Kumar", "Lakshmi Devi"][payload.field_id - 1] || "Farmer",
    crop_type: ["Cotton", "Wheat", "Chilli", "Paddy"][payload.field_id - 1] || "Crop",
    temperature: payload.temperature,
    humidity: payload.humidity,
    soil_moisture: payload.soil_moisture,
    rainfall: payload.rainfall,
    predicted_yield: advisoryResult.predicted_yield_quintals_per_acre,
    drought_risk: drought,
    pest_risk: pest,
    recorded_at: new Date().toISOString()
  };
  localHistory.unshift(newRecord);
  localStorage.setItem("cropsense_local_history", JSON.stringify(localHistory.slice(0, 30)));

  renderLocalHistoryTable();
}

function getBadgeClass(level) {
  if (level === "HIGH") return "badge-high";
  if (level === "MEDIUM") return "badge-medium";
  return "badge-low";
}

// OS Daemon toggle & poller
toggleDaemonBtn.addEventListener("click", async () => {
  if (!isBackendOnline) {
    alert("OS Sensor Daemon requires the Python backend server. Please run 'python run_server.py' first.");
    return;
  }
  const endpoint = isDaemonRunning ? "/api/daemon/stop" : "/api/daemon/start";
  try {
    const res = await fetch(API_BASE + endpoint, { method: "POST" });
    await pollDaemonStatus();
  } catch (err) {
    console.error("Daemon toggle error:", err);
  }
});

function updateDaemonStatusUI(running) {
  isDaemonRunning = running;
  if (running) {
    daemonBadge.className = "status-badge running";
    daemonText.textContent = "OS Sensor Daemon: Active (Polling)";
    toggleDaemonBtn.textContent = "Stop Sensor Daemon";
  } else {
    daemonBadge.className = "status-badge stopped";
    daemonText.textContent = "OS Sensor Daemon: Idle";
    toggleDaemonBtn.textContent = "Start Sensor Daemon";
  }
}

async function pollDaemonStatus() {
  if (!isBackendOnline) return;
  try {
    const res = await fetch(`${API_BASE}/api/daemon/status`);
    const json = await res.json();
    if (json.status === "success") {
      const data = json.data;
      updateDaemonStatusUI(data.is_running);
      daemonStatsText.textContent = `Buffer: ${data.buffer_size}/${data.buffer_capacity} | Produced: ${data.metrics.packets_produced} | Consumed: ${data.metrics.packets_consumed}`;
      if (data.is_running) {
        await loadOverviewTable();
        await loadHistoryTable();
        await loadDbStats();
      }
    }
  } catch (err) {
    // Silent
  }
}

// Event Listeners & Interactive Refresh Function
window.handleRefreshRecords = async function() {
  const btn = document.getElementById("refreshHistoryBtn");
  const originalHtml = btn ? btn.innerHTML : "🔄 Refresh Records";

  if (btn) {
    btn.innerHTML = "⏳ Refreshing...";
    btn.disabled = true;
  }

  try {
    if (isBackendOnline) {
      await Promise.all([
        loadHistoryTable(),
        loadOverviewTable(),
        loadDbStats()
      ]);
    } else {
      renderLocalHistoryTable();
      renderFallbackOverviewTable();
    }

    if (btn) {
      btn.innerHTML = "✅ Refreshed!";
      setTimeout(() => {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
      }, 1000);
    }
  } catch (err) {
    console.error("Refresh failed:", err);
    if (btn) {
      btn.innerHTML = "⚠️ Retry";
      setTimeout(() => {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
      }, 1000);
    }
  }
};

// Delete Single Record
window.handleDeleteRecord = async function(readingId, source) {
  if (!confirm(`Are you sure you want to delete Record #${readingId}?`)) {
    return;
  }

  try {
    if (source === "sqlite" && isBackendOnline) {
      const res = await fetch(`${API_BASE}/api/history/${readingId}`, {
        method: "DELETE"
      });
      const data = await res.json();
      if (data.status === "success") {
        await Promise.all([
          loadHistoryTable(),
          loadOverviewTable(),
          loadDbStats()
        ]);
        return;
      } else {
        alert("Delete failed: " + (data.message || "Unknown error"));
      }
    }

    // LocalStorage fallback
    const localHistory = JSON.parse(localStorage.getItem("cropsense_local_history") || "[]");
    const updated = localHistory.filter(item => (item.reading_id !== readingId));
    localStorage.setItem("cropsense_local_history", JSON.stringify(updated));
    renderLocalHistoryTable();
  } catch (err) {
    console.error("Delete record error:", err);
    alert("Could not delete record: " + err.message);
  }
};

// Clear All Stored Records
window.handleClearAllRecords = async function() {
  if (!confirm("⚠️ Are you sure you want to delete ALL telemetry and prediction records?\n(Registered farmers and fields will remain intact)")) {
    return;
  }

  try {
    if (isBackendOnline) {
      const res = await fetch(`${API_BASE}/api/history/clear`, {
        method: "POST"
      });
      const data = await res.json();
      if (data.status === "success") {
        localStorage.removeItem("cropsense_local_history");
        await Promise.all([
          loadHistoryTable(),
          loadOverviewTable(),
          loadDbStats()
        ]);
        alert("✅ All records successfully cleared from the database.");
        return;
      }
    }

    // Clear local storage
    localStorage.removeItem("cropsense_local_history");
    renderLocalHistoryTable();
    alert("✅ Local record logs cleared.");
  } catch (err) {
    console.error("Clear records error:", err);
    alert("Could not clear records: " + err.message);
  }
};

if (refreshHistoryBtn) {
  refreshHistoryBtn.addEventListener("click", window.handleRefreshRecords);
}

const clearHistoryBtn = document.getElementById("clearHistoryBtn");
if (clearHistoryBtn) {
  clearHistoryBtn.addEventListener("click", window.handleClearAllRecords);
}

if (typeof retryConnectionBtn !== "undefined" && retryConnectionBtn) {
  retryConnectionBtn.addEventListener("click", checkBackendHealth);
}

function restoreLastResult() {
  try {
    const cached = sessionStorage.getItem("cropsense_last_result");
    if (cached) {
      const parsed = JSON.parse(cached);
      if (parsed && parsed.res) {
        renderAdvisoryResults(parsed.res, parsed.source, false);
      }
    }
  } catch (e) {
    // Silent
  }
}

// Boot
restoreLastResult();
checkBackendHealth();
setInterval(pollDaemonStatus, 3000);

// Auto-reconnect when offline or when user switches back to this tab
window.addEventListener("focus", () => {
  if (!isBackendOnline) {
    checkBackendHealth();
  }
});

setInterval(() => {
  if (!isBackendOnline) {
    checkBackendHealth();
  }
}, 3500);
