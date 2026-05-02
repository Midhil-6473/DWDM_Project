const fileInput = document.getElementById("csvFile");
const uploadZone = document.getElementById("uploadZone");
const step1 = document.getElementById("step1");
const step2 = document.getElementById("step2");
const step3 = document.getElementById("step3");
const runBatchBtn = document.getElementById("runBatch");

let sessionId = null;

uploadZone.onclick = () => fileInput.click();

// Drag and drop support
uploadZone.ondragover = (e) => { e.preventDefault(); uploadZone.style.borderColor = 'var(--green)'; };
uploadZone.ondragleave = () => { uploadZone.style.borderColor = 'var(--border)'; };
uploadZone.ondrop = (e) => {
  e.preventDefault();
  uploadZone.style.borderColor = 'var(--border)';
  const f = e.dataTransfer.files[0];
  if (f && f.name.endsWith('.csv')) {
    fileInput.files = e.dataTransfer.files;
    fileInput.dispatchEvent(new Event('change'));
  }
};

fileInput.onchange = async () => {
  const f = fileInput.files[0];
  if (!f) return;

  // Show uploading state
  uploadZone.innerHTML = `
    <div style="font-size:40px;">⏳</div>
    <h3>Uploading ${f.name}...</h3>
    <p style="color:var(--text-muted);">${(f.size / 1024).toFixed(1)} KB</p>
  `;

  try {
    const fd = new FormData();
    fd.append("file", f);
    const up = await fetch("/api/batch/upload", { method: "POST", body: fd });
    if (!up.ok) {
      const err = await up.json();
      throw new Error(err.detail || 'Upload failed');
    }
    const upJson = await up.json();
    sessionId = upJson.session_id;

    const val = await fetch(`/api/batch/validate?session_id=${sessionId}`);
    if (!val.ok) throw new Error('Validation failed');
    const v = await val.json();

    step1.classList.add("hidden");
    step2.classList.remove("hidden");

    // Stats cards
    const readyBadge = v.ready
      ? '<span style="color:#22c55e;font-weight:700;">✅ Ready</span>'
      : '<span style="color:#ef4444;font-weight:700;">❌ Issues Found</span>';

    document.getElementById("statCards").innerHTML = `
      <div class="metricCard"><div class="metricVal">${v.stats.total_rows.toLocaleString()}</div><div class="metricLbl">Rows</div></div>
      <div class="metricCard"><div class="metricVal">${v.stats.total_columns}</div><div class="metricLbl">Columns</div></div>
      <div class="metricCard"><div class="metricVal">${readyBadge}</div><div class="metricLbl">Status</div></div>`;

    // Show issues if any
    if (v.issues && v.issues.length) {
      document.getElementById("statCards").innerHTML += `
        <div style="grid-column: 1/-1; padding: 12px; border-radius: 10px; background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.2); color: #ef4444; font-size: 0.9rem;">
          ⚠️ ${v.issues.join('<br>')}
        </div>`;
    }

    // Preview table
    const prev = v.preview || [];
    const cols = prev.length ? Object.keys(prev[0]) : [];
    document.getElementById("previewHead").innerHTML = `<tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr>`;
    document.getElementById("previewBody").innerHTML = prev.map(row =>
      `<tr>${cols.map(c => `<td>${row[c] != null ? row[c] : ''}</td>`).join("")}</tr>`
    ).join("");

    // Enable/disable run button
    runBatchBtn.disabled = !v.ready;
    if (!v.ready) {
      runBatchBtn.textContent = '❌ Fix issues above before running';
    }

  } catch (err) {
    uploadZone.innerHTML = `
      <div style="font-size:40px;">❌</div>
      <h3 style="color:#ef4444;">Upload Failed</h3>
      <p>${err.message}</p>
      <p style="margin-top:10px;color:var(--green);cursor:pointer;" onclick="location.reload()">Try Again</p>
    `;
  }
};

runBatchBtn.onclick = async () => {
  runBatchBtn.disabled = true;
  runBatchBtn.innerHTML = `<span class="batchSpinner"></span> Predicting... please wait`;

  try {
    const res = await fetch(`/api/batch/predict?session_id=${sessionId}`, { method: "POST" });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Prediction failed');
    }
    const r = await res.json();

    step2.classList.add("hidden");
    step3.classList.remove("hidden");

    // Summary with category breakdown
    const cats = r.category_counts || {};
    const catBadges = Object.entries(cats).map(([cat, count]) => {
      const color = cat === 'High' ? '#22c55e' : cat === 'Low' ? '#ef4444' : '#FB8C00';
      return `<span style="display:inline-block;padding:4px 12px;border-radius:8px;background:${color}22;color:${color};font-weight:700;font-size:0.85rem;margin:4px;">${cat}: ${count}</span>`;
    }).join('');

    document.getElementById("resultSummary").innerHTML = `
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px;">
        <div class="metricCard"><div class="metricVal">${r.rows.toLocaleString()}</div><div class="metricLbl">Predictions</div></div>
        <div class="metricCard"><div class="metricVal">${r.elapsed_sec}s</div><div class="metricLbl">Time</div></div>
        <div class="metricCard"><div class="metricVal">${Math.round(r.avg_yield || 0).toLocaleString()}</div><div class="metricLbl">Avg Yield (kg/ha)</div></div>
      </div>
      <div style="margin-bottom:16px;">${catBadges}</div>
    `;

    // Results table
    const records = r.records || [];
    const cols = records.length ? Object.keys(records[0]) : [];
    document.getElementById("resultHead").innerHTML = `<tr>${cols.map(c => {
      const highlight = (c === 'Predicted_Yield_kg_ha' || c === 'Yield_Category') ? ' style="color:var(--green);font-weight:800;"' : '';
      return `<th${highlight}>${c}</th>`;
    }).join("")}</tr>`;
    document.getElementById("resultBody").innerHTML = records.slice(0, 500).map(row => {
      return `<tr>${cols.map(c => {
        let val = row[c] != null ? row[c] : '';
        let style = '';
        if (c === 'Predicted_Yield_kg_ha') {
          val = typeof val === 'number' ? Math.round(val).toLocaleString() : val;
          style = ' style="font-weight:700;"';
        }
        if (c === 'Yield_Category') {
          const color = val === 'High' ? '#22c55e' : val === 'Low' ? '#ef4444' : '#FB8C00';
          return `<td><span style="padding:3px 10px;border-radius:6px;background:${color}22;color:${color};font-weight:700;font-size:0.85rem;">${val}</span></td>`;
        }
        return `<td${style}>${val}</td>`;
      }).join("")}</tr>`;
    }).join("");

    if (records.length > 500) {
      document.getElementById("resultBody").innerHTML += `<tr><td colspan="${cols.length}" style="text-align:center;color:var(--text-muted);padding:16px;">Showing first 500 of ${records.length} rows. Download CSV for full results.</td></tr>`;
    }

    document.getElementById("downloadBtn").href = `/api/batch/download?session_id=${sessionId}`;

  } catch (err) {
    runBatchBtn.disabled = false;
    runBatchBtn.textContent = '🚀 Run Batch Predictions';
    // Show error inline
    const errDiv = document.createElement('div');
    errDiv.style.cssText = 'padding:12px;border-radius:10px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);color:#ef4444;margin-top:12px;font-size:0.9rem;';
    errDiv.textContent = `❌ ${err.message}`;
    runBatchBtn.parentNode.appendChild(errDiv);
  }
};
