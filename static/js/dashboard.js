const heatmapEl = document.getElementById("heatmap");
const alertsEl = document.getElementById("alert-list");
const hoursEl = document.getElementById("hours-filter");
const patientEl = document.getElementById("patient-filter");
const refreshBtn = document.getElementById("refresh-btn");
const commentsEl = document.getElementById("comments-container");
const submitCommentBtn = document.getElementById("submit-comment");
const newCommentEl = document.getElementById("new-comment");
const windowNoteEl = document.getElementById("window-note");
const insightListEl = document.getElementById("insight-list");

let ppiChart;
let contactChart;
let riskChart;
let contextData;

function colorForPressure(value) {
  const ratio = Math.min(value / 4095, 1);
  const r = Math.floor(255 * ratio);
  const g = Math.floor(255 * (1 - ratio));
  return `rgb(${r},${g},60)`;
}

function renderHeatmap(matrix) {
  heatmapEl.innerHTML = "";
  matrix.flat().forEach((v) => {
    const div = document.createElement("div");
    div.className = "heat-cell";
    div.style.backgroundColor = colorForPressure(v);
    div.title = String(v);
    heatmapEl.appendChild(div);
  });
}

function renderAlerts(items) {
  alertsEl.innerHTML = items
    .map((a) => `<p class="${a.severity.toLowerCase()}">[${a.severity}] ${a.message}</p>`)
    .join("");
}

function renderChart(canvasId, existing, label, series, color) {
  const ctx = document.getElementById(canvasId);
  if (existing) existing.destroy();
  return new Chart(ctx, {
    type: "line",
    data: {
      labels: series.map((x) => new Date(x.t).toLocaleTimeString()),
      datasets: [{ label, data: series.map((x) => x.v), borderColor: color, fill: false }],
    },
    options: { responsive: true, maintainAspectRatio: false },
  });
}

function setText(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = String(value);
}

function renderKpis(kpis = {}) {
  setText("kpi-latest-ppi", kpis.latest_ppi ?? 0);
  setText("kpi-latest-contact", kpis.latest_contact ?? 0);
  setText("kpi-avg-ppi", kpis.avg_ppi ?? 0);
  setText("kpi-stability", `${kpis.posture_stability_score ?? 0}%`);
  setText("kpi-high-alerts", kpis.alerts_high ?? 0);
}

function renderInsights(kpis = {}) {
  const insights = [];
  const ppi = Number(kpis.latest_ppi || 0);
  const contact = Number(kpis.latest_contact || 0);
  const stability = Number(kpis.posture_stability_score || 0);
  if (ppi > 3000) {
    insights.push("High pressure detected. Recommend posture change and micro-breaks every 20 minutes.");
  } else if (ppi > 1500) {
    insights.push("Moderate pressure load observed. Monitor pressure redistribution over the next hour.");
  } else {
    insights.push("Pressure profile is currently in a safer range.");
  }
  if (contact < 15) {
    insights.push("Low contact area suggests concentrated loading. Encourage weight shifting.");
  } else {
    insights.push("Contact area distribution is acceptable for current session.");
  }
  if (stability < 55) {
    insights.push("Frequent pressure variability detected. Consider assisted posture coaching.");
  } else {
    insights.push("Posture stability trend is positive.");
  }
  insightListEl.innerHTML = insights.map((item) => `<li>${item}</li>`).join("");
}

function getSelectedUserId() {
  if (!patientEl || !patientEl.value) return null;
  return patientEl.value;
}

async function loadContext() {
  const res = await fetch("/data/api/context/");
  contextData = await res.json();
  if (patientEl) {
    patientEl.innerHTML = (contextData.users || [])
      .map((u) => `<option value="${u.id}">${u.name || u.email} (${u.email})</option>`)
      .join("");
    if (contextData.default_user_id) {
      patientEl.value = String(contextData.default_user_id);
    }
    if ((contextData.role || "").toUpperCase() === "PATIENT") {
      patientEl.disabled = true;
    }
  }
  setText("kpi-patients", contextData.kpi_total_patients ?? 0);
  setText("kpi-alerts24", contextData.kpi_alerts_24h ?? 0);
  setText("kpi-comments24", contextData.kpi_comments_24h ?? 0);
}

async function loadSummary() {
  const hours = hoursEl.value;
  const targetUser = getSelectedUserId();
  const query = new URLSearchParams({ hours });
  if (targetUser) query.set("user_id", targetUser);
  const res = await fetch(`/data/api/summary/?${query.toString()}`);
  const data = await res.json();
  renderHeatmap(data.heatmap || Array.from({ length: 32 }, () => Array(32).fill(0)));
  renderAlerts(data.alerts || []);
  renderKpis(data.kpis || {});
  renderInsights(data.kpis || {});
  windowNoteEl.textContent = data.using_fallback_window
    ? "No records in selected time window. Showing the most recent available patient data."
    : "";
  ppiChart = renderChart("ppiChart", ppiChart, "PPI", data.ppi_series || [], "#b91c1c");
  contactChart = renderChart("contactChart", contactChart, "Contact Area %", data.contact_series || [], "#1d4ed8");
  riskChart = renderChart("riskChart", riskChart, "Risk Score", data.risk_series || [], "#f59e0b");
}

async function loadComments() {
  const targetUser = getSelectedUserId();
  const query = targetUser ? `?user_id=${encodeURIComponent(targetUser)}` : "";
  const res = await fetch(`/data/api/comments/${query}`);
  const data = await res.json();
  commentsEl.innerHTML = (data.items || [])
    .map((c) => {
      const replies = c.replies.map((r) => `<li>${r.reply_text}</li>`).join("");
      return `<div class="card"><p>${c.comment_text}</p><ul>${replies}</ul></div>`;
    })
    .join("");
}

submitCommentBtn?.addEventListener("click", async () => {
  const commentText = newCommentEl.value.trim();
  if (!commentText) return;
  await fetch("/data/api/comments/", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrfToken() },
    body: JSON.stringify({ comment_text: commentText }),
  });
  newCommentEl.value = "";
  loadComments();
});

refreshBtn?.addEventListener("click", loadSummary);
patientEl?.addEventListener("change", () => {
  loadSummary();
  loadComments();
});

function getCsrfToken() {
  const cookie = document.cookie.split("; ").find((row) => row.startsWith("csrftoken="));
  return cookie ? cookie.split("=")[1] : "";
}

async function initDashboard() {
  await loadContext();
  await loadSummary();
  await loadComments();
}

initDashboard();
