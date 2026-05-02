const fileInput = document.getElementById("csvFile");
const uploadZone = document.getElementById("uploadZone");
const requiredCols = document.getElementById("requiredCols");
const toggle = document.getElementById("toggleCols");
const stepper = document.getElementById("stepper");
const step1 = document.getElementById("step1");
const step2 = document.getElementById("step2");
const step3 = document.getElementById("step3");
const runBatchBtn = document.getElementById("runBatch");
const batchProgress = document.getElementById("batchProgress");

let sessionId = null;
/** @type {any[]} */
let allRecords = [];
let pageSize = 20;
let currentPage = 1;
/** @type {Record<string, number[]>} */
let yieldsByCrop = {};
let lastCharts = null;
/** @type {any | null} */
let lastBatchResponse = null;

const REQUIRED_LIST = [
  "Crop_Type",
  "Season",
  "State",
  "Irrigation_Method",
  "Fertilizer_Type",
  "Avg_Temp_C",
  "Max_Temp_C",
  "Min_Temp_C",
  "Rainfall_mm",
  "Humidity_Pct",
  "Water_Stress_Index",
  "Solar_Radiation_MJm2",
  "Wind_Speed_kmh",
  "Soil_Type",
  "Soil_pH",
  "Soil_Moisture_Pct",
  "Organic_Carbon_Pct",
  "Bulk_Density_gcm3",
  "N_kgha",
  "P_kgha",
  "K_kgha",
  "Sulfur_kgha",
  "Zinc_ppm",
  "Iron_ppm",
  "NDVI",
  "Pest_Incidence",
  "Disease_Incidence",
];

function setStep(n) {
  step1.classList.toggle("hidden", n !== 1);
  step2.classList.toggle("hidden", n !== 2);
  step3.classList.toggle("hidden", n !== 3);
  document.querySelectorAll("#stepper .step").forEach((el) => {
    el.classList.toggle("active", el.dataset.step === String(n));
  });
}

toggle.onclick = () => {
  requiredCols.classList.toggle("hidden");
  requiredCols.textContent = REQUIRED_LIST.join(", ");
};

uploadZone.addEventListener("click", () => fileInput.click());
uploadZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadZone.classList.add("dragover");
});
uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("dragover"));
uploadZone.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadZone.classList.remove("dragover");
  if (e.dataTransfer.files.length) {
    fileInput.files = e.dataTransfer.files;
    fileInput.dispatchEvent(new Event("change"));
  }
});

fileInput.addEventListener("change", async () => {
  const f = fileInput.files[0];
  if (!f) return;
  const fd = new FormData();
  fd.append("file", f);
  const up = await fetch("/api/batch/upload", { method: "POST", body: fd });
  const upJson = await up.json();
  if (!up.ok) {
    alert(upJson.detail || "Upload failed");
    return;
  }
  sessionId = upJson.session_id;
  const val = await fetch(`/api/batch/validate?session_id=${sessionId}`);
  const v = await val.json();
  setStep(2);
  document.getElementById("statCards").innerHTML = `
    <div class="metricCard"><div class="metricVal">${v.stats.total_rows}</div><div class="metricLbl">Total rows</div></div>
    <div class="metricCard"><div class="metricVal">${v.stats.total_columns}</div><div class="metricLbl">Total columns</div></div>
    <div class="metricCard"><div class="metricVal">${v.stats.missing_values}</div><div class="metricLbl">Missing values</div></div>
    <div class="metricCard"><div class="metricVal">${(v.stats.file_size / 1024).toFixed(1)} KB</div><div class="metricLbl">File size</div></div>`;

  const issuesHtml =
    v.issues && v.issues.length
      ? `<ul class="issueList">${v.issues.map((i) => `<li>${i}</li>`).join("")}</ul>`
      : "";
  document.getElementById("validationBox").innerHTML = `${issuesHtml}<p class="valSummary">${v.ready_message || ""}</p>`;

  runBatchBtn.disabled = !v.ready;

  const prev = v.preview || [];
  const cols = prev.length ? Object.keys(prev[0]) : [];
  document.getElementById("previewHead").innerHTML = `<tr>${cols.map((c) => `<th>${c}</th>`).join("")}</tr>`;
  document.getElementById("previewBody").innerHTML = prev
    .map((row) => `<tr>${cols.map((c) => `<td>${row[c]}</td>`).join("")}</tr>`)
    .join("");
});

runBatchBtn.onclick = async () => {
  batchProgress.classList.remove("hidden");
  runBatchBtn.disabled = true;
  const res = await fetch(`/api/batch/predict?session_id=${sessionId}`, { method: "POST" });
  const r = await res.json();
  batchProgress.classList.add("hidden");
  runBatchBtn.disabled = false;
  if (!res.ok) {
    alert(r.detail || "Batch failed");
    return;
  }
  setStep(3);
  lastBatchResponse = r;
  allRecords = r.records || [];
  yieldsByCrop = r.yields_by_crop || {};
  lastCharts = r.charts;
  currentPage = 1;

  const counts = r.counts || {};
  const low = counts.Low || 0;
  const med = counts.Medium || 0;
  const high = counts.High || 0;
  const total = r.rows || 1;
  const pct = (n) => ((100 * n) / total).toFixed(1);

  document.getElementById("resultSummary").innerHTML = `<p class="bigSummary"><strong>${r.rows}</strong> predictions completed in <strong>${r.elapsed_sec}</strong> seconds.</p>`;
  if (r.truncated) {
    document.getElementById("resultSummary").innerHTML += `<p class="warnInline">Table shows first ${allRecords.length} rows in-browser; download CSV for the full file.</p>`;
  }

  document.getElementById("metricCards").innerHTML = `
    <div class="metricCard lowCard"><div class="metricVal">${low}</div><div class="metricLbl">🔴 Low (${pct(low)}%)</div></div>
    <div class="metricCard medCard"><div class="metricVal">${med}</div><div class="metricLbl">🟡 Medium (${pct(med)}%)</div></div>
    <div class="metricCard highCard"><div class="metricVal">${high}</div><div class="metricLbl">🟢 High (${pct(high)}%)</div></div>
    <div class="metricCard"><div class="metricVal">${Math.round(r.avg_yield)}</div><div class="metricLbl">📊 Avg yield (kg/ha)</div></div>`;

  const cg = document.getElementById("chartGrid");
  cg.innerHTML = `<div id="cDonut"></div><div id="cHist"></div><div id="cCrop"></div><div id="cMap"></div>`;
  Plotly.newPlot("cDonut", r.charts.donut.data, r.charts.donut.layout, { responsive: true, displayModeBar: false });
  Plotly.newPlot("cHist", r.charts.histogram.data, r.charts.histogram.layout, { responsive: true, displayModeBar: false });
  Plotly.newPlot("cCrop", r.charts.crop_bars.data, r.charts.crop_bars.layout, { responsive: true, displayModeBar: false });
  Plotly.newPlot("cMap", r.charts.state_map.data, r.charts.state_map.layout, { responsive: true, displayModeBar: false });

  const sel = document.getElementById("histCropFilter");
  const keys = Object.keys(yieldsByCrop);
  sel.innerHTML =
    `<option value="__ALL__">All crops combined</option>` +
    keys.map((c) => `<option value="${c}">${c}</option>`).join("");
  sel.onchange = () => redrawHistogram();
  redrawHistogram();

  document.getElementById("downloadBtn").href = `/api/batch/download?session_id=${sessionId}`;
  renderResultTablePage();
};

function redrawHistogram() {
  const batchResponse = lastBatchResponse;
  if (!batchResponse) return;
  const crop = document.getElementById("histCropFilter").value;
  let yields = [];
  if (crop === "__ALL__") {
    yields = allRecords.map((x) => Number(x.Predicted_Yield_kg_ha)).filter((x) => Number.isFinite(x));
  } else {
    yields = yieldsByCrop[crop] || [];
  }
  const byCrop = batchResponse.national_avg_by_crop || {};
  const nat =
    crop === "__ALL__"
      ? Number(batchResponse.national_avg_line) || 0
      : Number(byCrop[crop] ?? batchResponse.national_avg_line) || 0;
  const figData = [
    {
      type: "histogram",
      x: yields.length ? yields : batchResponse.avg_yield ? [batchResponse.avg_yield] : [0],
      marker: { color: "#4CAF50", opacity: 0.85 },
      name: "Fields",
    },
  ];
  const titleCrop = crop === "__ALL__" ? "all crops" : crop;
  const natLabel = crop === "__ALL__" ? "Dominant crop national avg" : `${crop} national avg`;
  const layout = {
    title: { text: `Predicted Yield Distribution — ${titleCrop}`, font: { size: 14 } },
    xaxis: { title: "kg/ha" },
    yaxis: { title: "Count" },
    shapes: [
      {
        type: "line",
        x0: nat,
        x1: nat,
        y0: 0,
        y1: 1,
        yref: "paper",
        line: { color: "#d32f2f", dash: "dash" },
      },
    ],
    annotations: [
      {
        x: nat,
        y: 1,
        xref: "x",
        yref: "paper",
        text: natLabel,
        showarrow: false,
        yanchor: "bottom",
      },
    ],
    margin: { l: 48, r: 24, t: 48, b: 48 },
  };
  Plotly.react("cHist", figData, layout, { displayModeBar: false });
}

function renderResultTablePage() {
  if (!allRecords.length) return;
  const cols = Object.keys(allRecords[0]);
  document.getElementById("resultHead").innerHTML = `<tr>${cols.map((c) => `<th>${c}</th>`).join("")}</tr>`;
  const total = allRecords.length;
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (currentPage > pages) currentPage = pages;
  const start = (currentPage - 1) * pageSize;
  const slice = allRecords.slice(start, start + pageSize);
  document.getElementById("resultBody").innerHTML = slice
    .map((row) => {
      return `<tr>${cols
        .map((c) => {
          let cls = "";
          if (c === "Yield_Category") {
            const v = String(row[c] || "").toLowerCase();
            if (v.includes("low")) cls = "cellLow";
            else if (v.includes("high")) cls = "cellHigh";
            else cls = "cellMed";
          }
          return `<td class="${cls}">${row[c]}</td>`;
        })
        .join("")}</tr>`;
    })
    .join("");

  const pag = document.getElementById("pagination");
  pag.innerHTML = `<button type="button" ${currentPage <= 1 ? "disabled" : ""} id="pgPrev">← Prev</button>
    <span>Page ${currentPage} / ${pages}</span>
    <button type="button" ${currentPage >= pages ? "disabled" : ""} id="pgNext">Next →</button>`;
  document.getElementById("pgPrev").onclick = () => {
    currentPage--;
    renderResultTablePage();
  };
  document.getElementById("pgNext").onclick = () => {
    currentPage++;
    renderResultTablePage();
  };
}

setStep(1);
