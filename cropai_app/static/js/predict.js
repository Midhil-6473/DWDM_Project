const form = document.getElementById("predictForm");
const panel = document.getElementById("resultPanel");
const cropSel = document.getElementById("Crop_Type");
const seasonSel = document.getElementById("Season");
const fillBtn = document.getElementById("fillOptimal");
const warning = document.getElementById("seasonWarning");
const compareBtn = document.getElementById("runCompare");
const compareCropSel = document.getElementById("compareCrop");
let baseYield = null;
let simTimer = null;
/** @type {object | null} */
let lastFullResult = null;

function serializeForm() {
  const fd = new FormData(form);
  const out = {};
  fd.forEach((v, k) => {
    out[k] = isNaN(Number(v)) || v === "" ? v : Number(v);
  });
  return out;
}

function formatRangeTip(featureKey, crop) {
  const OR = window.OPTIMAL_RANGES || {};
  const preset = window.CROP_CONSTANTS[crop] || {};
  const v = Number(document.querySelector(`[name='${featureKey}']`)?.value || 0);
  const unit =
    featureKey.includes("Rainfall") || featureKey.includes("mm")
      ? "mm"
      : featureKey === "Soil_pH"
        ? ""
        : featureKey.includes("N_") || featureKey.includes("P_") || featureKey.includes("K_") || featureKey.includes("kgha")
          ? "kg/ha"
          : "";

  if (OR[featureKey] && OR[featureKey][crop]) {
    const [lo, hi] = OR[featureKey][crop];
    let status = "✅ within optimal";
    if (v < lo) status = `⚠️ Below optimal (${lo}–${hi}${unit ? " " + unit : ""})`;
    else if (v > hi) status = `⚠️ Above optimal (${lo}–${hi}${unit ? " " + unit : ""})`;
    const label =
      featureKey === "N_kgha"
        ? "Nitrogen (N)"
        : featureKey === "Rainfall_mm"
          ? "Rainfall"
          : featureKey === "Soil_pH"
            ? "Soil pH"
            : featureKey === "K_kgha"
              ? "Potassium (K)"
              : featureKey;
    const u = featureKey === "Soil_pH" ? "" : ` ${unit}`.trim();
    return `Optimal ${label} for ${crop}: ${lo}–${hi}${u ? u : ""} | Your input: ${v}${u ? u : ""} ${status}`;
  }
  if (preset[featureKey] !== undefined) {
    const p = Number(preset[featureKey]);
    const status = Math.abs(v - p) / Math.max(1e-6, Math.abs(p)) < 0.2 ? "✅" : v < p ? "⚠️ Below typical target" : "⚠️ Above typical target";
    return `Typical target for ${crop}: ${p} | Your value: ${v} ${status}`;
  }
  return "";
}

function updateSliderText() {
  const crop = cropSel.value;
  document.querySelectorAll(".slider").forEach((s) => {
    const span = s.nextElementSibling;
    if (span && span.classList.contains("value")) span.textContent = s.value;
    const tip = s.parentElement.querySelector(".tip");
    if (tip) tip.textContent = formatRangeTip(s.name, crop);
  });
}

function seasonWarn() {
  const crop = cropSel.value;
  const season = seasonSel.value;
  const key = `${crop}|${season}`;
  const detail = window.SEASON_WARN_DETAIL && window.SEASON_WARN_DETAIL[key];
  const rule = window.SEASON_RULES[crop];
  if (detail) {
    warning.textContent = `⚠️ ${detail}`;
    warning.classList.remove("hidden");
  } else if (rule && rule.warn.includes(season)) {
    warning.textContent = `⚠️ ${crop} is mainly grown in ${rule.primary.join(" / ")}. ${season} can be challenging — review calendar and inputs.`;
    warning.classList.remove("hidden");
  } else {
    warning.classList.add("hidden");
  }
}

function categoryBadge(catRaw) {
  const c = String(catRaw || "").toLowerCase();
  if (c.includes("low")) return `<span class="badge low">🔴 LOW</span>`;
  if (c.includes("high")) return `<span class="badge high">🟢 HIGH</span>`;
  return `<span class="badge medium">🟡 MEDIUM</span>`;
}

function healthBadge(score) {
  const s = Number(score) || 0;
  if (s >= 90) return `<span class="healthPill excellent">🟢 Excellent — ${s}%</span>`;
  if (s >= 70) return `<span class="healthPill good">🟡 Good — ${s}%</span>`;
  if (s >= 50) return `<span class="healthPill fair">🟠 Fair — ${s}%</span>`;
  return `<span class="healthPill poor">🔴 Needs attention — ${s}%</span>`;
}

function renderResult(r, crop) {
  lastFullResult = r;
  const cls = String(r.predicted_category || "").toLowerCase();
  const pctRange = Math.round((r.yield_progress || 0) * 100);
  const progressColor = cls.includes("low") ? "#d32f2f" : cls.includes("medium") ? "#f59e0b" : "#2e7d32";
  const above = r.delta_from_national_pct >= 0;
  const state = serializeForm().State || "";

  panel.innerHTML = `
  <div class="block mainPred">
    <div class="bigYield">${Math.round(r.predicted_yield_kg_ha).toLocaleString()} kg/ha</div>
    <div class="badgeRow">${categoryBadge(r.predicted_category)}</div>
    <div class="progressWrap"><div class="progressBar" style="width:${pctRange}%;background:${progressColor}"></div></div>
    <small class="progressCaption">${pctRange}% of maximum yield for ${crop}</small>
  </div>
  <div class="block">
    <h3>Field health score</h3>
    ${healthBadge(r.field_health_score)}
    <p class="healthLabel">${r.field_health_label}</p>
  </div>
  <div class="block">
    <h3>Yield context</h3>
    <table class="ctxTable">
      <tr><td>Your predicted yield</td><td class="value">${Math.round(r.predicted_yield_kg_ha).toLocaleString()} kg/ha</td></tr>
      <tr><td>National average</td><td class="value">${Math.round(r.national_average).toLocaleString()} kg/ha</td></tr>
      <tr><td>Best recorded yield (reference)</td><td class="value">${Math.round(r.max_yield).toLocaleString()} kg/ha</td></tr>
    </table>
    <p class="deltaLine">${above ? "✅" : "⚠️"} You are <strong>${Math.abs(r.delta_from_national_pct).toFixed(1)}%</strong> ${above ? "above" : "below"} the national average for ${crop}.</p>
  </div>
  <div class="block miniCharts"><div id="gauge"></div><div id="radar"></div><div id="npk"></div></div>
  <div class="block"><h3>💡 Recommendations</h3><ul class="recList">${r.recommendations.map((x) => `<li>${x}</li>`).join("")}</ul></div>
  <div class="block calendarCard"><h3>📅 ${crop} crop calendar — ${state}</h3>
    <p><strong>Sowing window:</strong> ${r.calendar.sowing}<br/>
    <strong>Harvest window:</strong> ${r.calendar.harvest}<br/>
    <strong>Days to maturity (typical):</strong> ${r.calendar.days_to_maturity}</p>
  </div>`;

  Plotly.newPlot("gauge", r.charts.gauge.data, r.charts.gauge.layout, { responsive: true, displayModeBar: false });
  Plotly.newPlot("radar", r.charts.radar.data, r.charts.radar.layout, { responsive: true, displayModeBar: false });
  Plotly.newPlot("npk", r.charts.npk.data, r.charts.npk.layout, { responsive: true, displayModeBar: false });

  const store = { ...serializeForm(), ...r };
  localStorage.setItem("last_prediction", JSON.stringify(store));
  localStorage.setItem("prediction_made", "true");
}

async function runCompare() {
  if (!lastFullResult) return;
  const data = serializeForm();
  const currentCrop = data.Crop_Type;
  const curYield = Math.round(lastFullResult.predicted_yield_kg_ha);
  const curCat = lastFullResult.predicted_category;
  data.Crop_Type = compareCropSel.value;
  const res = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data }),
  });
  const out = await res.json();
  const div = document.getElementById("compareResult");
  if (!res.ok) {
    div.innerHTML = `<span class="errTxt">${out.detail || "Compare failed"}</span>`;
    return;
  }
  div.innerHTML = `<div class="compareGrid">
    <div><strong>${currentCrop}</strong><br/>${curYield.toLocaleString()} kg/ha<br/>${categoryBadge(curCat)}</div>
    <div><strong>${data.Crop_Type}</strong><br/>${Math.round(out.predicted_yield_kg_ha).toLocaleString()} kg/ha<br/>${categoryBadge(out.predicted_category)}</div>
  </div>
  <small>Both predictions use identical field conditions — only the crop type is changed.</small>`;
}

async function runPredict(isSimulator = false) {
  const data = serializeForm();
  const res = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data }),
  });
  const r = await res.json();
  if (!res.ok) {
    if (!isSimulator) {
      panel.innerHTML = `<div class="placeholder errBox"><strong>Prediction could not complete</strong><br/>${r.detail || res.statusText}</div>`;
    }
    return;
  }
  if (!Number.isFinite(Number(r.predicted_yield_kg_ha))) {
    if (!isSimulator) {
      panel.innerHTML = `<div class="placeholder errBox">Unexpected server response.</div>`;
    }
    return;
  }
  if (!isSimulator) {
    baseYield = r.predicted_yield_kg_ha;
    renderResult(r, data.Crop_Type);
  } else if (baseYield !== null) {
    const delta = r.predicted_yield_kg_ha - baseYield;
    const el = document.getElementById("liveYield");
    if (el) {
      const arrow = delta >= 0 ? "↑" : "↓";
      const col = delta >= 0 ? "#2e7d32" : "#c62828";
      el.innerHTML = `Base yield: <strong>${Math.round(baseYield)}</strong> kg/ha &nbsp;|&nbsp; Current: <strong>${Math.round(r.predicted_yield_kg_ha)}</strong> kg/ha <span style="color:${col}">${arrow} ${delta >= 0 ? "+" : ""}${Math.round(delta)} kg/ha</span>`;
    }
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  await runPredict(false);
});
fillBtn.addEventListener("click", () => {
  const c = cropSel.value;
  const vals = window.CROP_CONSTANTS[c] || {};
  Object.entries(vals).forEach(([k, v]) => {
    const el = form.querySelector(`[name='${k}']`);
    if (el) el.value = v;
  });
  updateSliderText();
});
document.querySelectorAll(".slider").forEach((s) =>
  s.addEventListener("input", () => {
    updateSliderText();
    clearTimeout(simTimer);
    simTimer = setTimeout(() => runPredict(true).catch(() => {}), 300);
  }),
);
cropSel.addEventListener("change", () => {
  updateSliderText();
  seasonWarn();
});
seasonSel.addEventListener("change", seasonWarn);
compareBtn.addEventListener("click", () => runCompare().catch(() => {}));
updateSliderText();
seasonWarn();
