async function fetchData(url, params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${url}${query ? "?" + query : ""}`);
  return res.json();
}

async function updateDashboard() {
  const state = document.getElementById("stateFilter").value;
  const crop = document.getElementById("cropFilter").value;
  const season = document.getElementById("seasonFilter").value;

  const params = {};
  if (state) params.state = state;
  if (crop) params.crop_type = crop;
  if (season) params.season = season;

  // 1. Summary
  const summary = await fetchData("/analytics/summary", params);
  document.getElementById("meanYield").textContent = Math.round(summary.mean_yield).toLocaleString();
  document.getElementById("recordCount").textContent = summary.selected_count.toLocaleString();
  document.getElementById("yieldStability").textContent = `${Math.round(summary.min_yield).toLocaleString()} - ${Math.round(summary.max_yield).toLocaleString()}`;

  // 2. Yield Distribution
  const dist = await fetchData("/analytics/yield_distribution", params);
  const distData = [
    {
      x: dist.series.map((s) => s.label),
      y: dist.series.map((s) => s.count),
      type: "bar",
      marker: { color: "#4caf50" },
    },
  ];
  Plotly.newPlot("yieldDistChart", distData, {
    margin: { t: 20, b: 40, l: 40, r: 20 },
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { color: "#fff" },
    xaxis: { title: "Yield (kg/ha)", gridcolor: "rgba(255,255,255,0.1)" },
    yaxis: { title: "Count", gridcolor: "rgba(255,255,255,0.1)" },
  }, { responsive: true, displayModeBar: false });

  // 3. Category Pie
  const cats = await fetchData("/analytics/category_counts", params);
  const pieData = [
    {
      labels: cats.series.map((s) => s.label),
      values: cats.series.map((s) => s.count),
      type: "pie",
      hole: 0.4,
      marker: { colors: ["#d32f2f", "#f59e0b", "#2e7d32"] },
    },
  ];
  Plotly.newPlot("catPieChart", pieData, {
    margin: { t: 0, b: 0, l: 0, r: 0 },
    paper_bgcolor: "transparent",
    font: { color: "#fff" },
    legend: { orientation: "h", y: -0.1 },
  }, { responsive: true, displayModeBar: false });

  // 4. Top Crops
  const top = await fetchData("/analytics/top_crops", { ...params, limit: 10 });
  const topData = [
    {
      x: top.rows.map((r) => r.crop),
      y: top.rows.map((r) => r.avg_yield),
      type: "bar",
      marker: { color: top.rows.map((_, i) => `rgba(76, 175, 80, ${1 - i * 0.08})`) },
    },
  ];
  Plotly.newPlot("topCropsChart", topData, {
    margin: { t: 20, b: 100, l: 60, r: 20 },
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { color: "#fff" },
    yaxis: { title: "Avg Yield (kg/ha)", gridcolor: "rgba(255,255,255,0.1)" },
  }, { responsive: true, displayModeBar: false });
}

document.getElementById("applyFilters").onclick = updateDashboard;

// Initialize
updateDashboard();
