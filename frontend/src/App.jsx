import { useEffect, useMemo, useState } from "react";
import {
  Cell,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import {
  getCategoryCounts,
  getConditionDiagnostics,
  getFormMetadata,
  getSummary,
  getTopCropsByConditions,
  getYieldDistribution,
  predictBoth
} from "./api";

const CROP_AI_BASE = import.meta.env.VITE_CROP_AI_BASE_URL || "http://127.0.0.1:8005";

const CHART_GREEN = "#1b5e20";
const COLORS = ["#1b5e20", "#4caf50", "#8bc34a", "#2e7d32", "#33691e"];

function badgeClassForCategory(cat) {
  const s = String(cat || "").toLowerCase();
  if (s.includes("low")) return "badge low";
  if (s.includes("high")) return "badge high";
  return "badge medium";
}

function Shell({ children, darkMode, setDarkMode }) {
  return (
    <div className="appShell">
      <aside className="sidebar">
        <div className="brand">🌾 <span>CropCast</span></div>
        <span className="navItem active">🔍 <span>Predict</span></span>
        <a className="navItem externalHint" href={`${CROP_AI_BASE}/analytics-view`} target="_blank" rel="noreferrer">
          📊 <span>Analytics</span>
        </a>
        <a className="navItem externalHint" href={`${CROP_AI_BASE}/batch`} target="_blank" rel="noreferrer">
          📂 <span>Batch Predict</span>
        </a>
        <a className="navItem externalHint" href={`${CROP_AI_BASE}/chat`} target="_blank" rel="noreferrer">
          🤖 <span>Ask AI</span>
        </a>

        <div className="themeToggle">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.85rem', color: 'rgba(255,255,255,0.7)' }}>
            <span>{darkMode ? '🌙 Dark' : '☀️ Light'}</span>
            <label className="switch">
              <input type="checkbox" checked={darkMode} onChange={() => setDarkMode(!darkMode)} />
              <span className="slider"></span>
            </label>
          </div>
        </div>
      </aside>
      <main className="mainContent">{children}</main>
    </div>
  );
}

function RangeInputWithWarning({ col, value, onChange, minRef, maxRef }) {
  const range = maxRef - minRef || 1;
  const sliderMin = minRef - range * 0.2;
  const sliderMax = maxRef + range * 0.2;
  const displayVal = value !== "" && value !== undefined ? Number(value) : (minRef + maxRef) / 2;

  let warning = null;
  if (displayVal < minRef) {
    warning = (
      <div className="inputWarning low">
        <span>⚠️ Warning: value is low</span>
      </div>
    );
  } else if (displayVal > maxRef) {
    warning = (
      <div className="inputWarning high">
        <span>⚠️ Warning: higher than max value</span>
      </div>
    );
  }

  return (
    <div className="field" style={{ display: "flex", flexDirection: "column", gap: "4px", marginBottom: "12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>{col}</span>
        <span style={{ fontWeight: "bold", color: "var(--green)", fontSize: "0.95rem" }}>{displayVal.toFixed(2)}</span>
      </div>
      <input
        type="range"
        step="any"
        value={displayVal}
        onChange={(e) => onChange(Number(e.target.value))}
        min={sliderMin}
        max={sliderMax}
        style={{ width: "100%", cursor: "pointer", margin: "8px 0" }}
      />
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-muted)" }}>
        <span>Min: {minRef.toFixed(2)}</span>
        <span>Max: {maxRef.toFixed(2)}</span>
      </div>
      {warning}
    </div>
  );
}

function Landing({ onEnter }) {
  return (
    <div className="landing-page">
      <div className="landing-bg-glow g1"></div>
      <div className="landing-bg-glow g2"></div>
      <div className="landing-bg-glow g3"></div>

      {[...Array(20)].map((_, i) => (
        <div
          key={i}
          className="landing-particle"
          style={{
            left: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 6}s`,
            animationDuration: `${4 + Math.random() * 4}s`,
            width: `${2 + Math.random() * 3}px`,
            height: `${2 + Math.random() * 3}px`,
          }}
        ></div>
      ))}

      <div className="landing-card">
        <span className="landing-logo-emoji">🌾</span>
        <div className="landing-brand-name">CropCast</div>
        <p className="landing-tagline">
          Smart Crop Yield Prediction powered by Machine Learning.<br />
          Analyze 2,20,000+ agricultural records instantly.
        </p>

        <div className="landing-stats-row">
          <div className="landing-stat">
            <div className="landing-stat-val">2.2L+</div>
            <div className="landing-stat-lbl">Records</div>
          </div>
          <div className="landing-stat">
            <div className="landing-stat-val">10</div>
            <div className="landing-stat-lbl">Crops</div>
          </div>
          <div className="landing-stat">
            <div className="landing-stat-val">AI</div>
            <div className="landing-stat-lbl">Powered</div>
          </div>
        </div>

        <button onClick={onEnter} className="landing-enter-btn">
          Enter Dashboard
          <span className="arrow">→</span>
        </button>

        <div className="landing-footer-text">DWDM Mini Project · 2025</div>
      </div>
    </div>
  );
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function setCookie(name, value, days = 365) {
  const d = new Date();
  d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
  const expires = "expires=" + d.toUTCString();
  document.cookie = name + "=" + value + ";" + expires + ";path=/";
}

function App() {
  const [showDashboard, setShowDashboard] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get("dashboard") === "true";
  });
  const [darkMode, setDarkMode] = useState(() => (getCookie("app_theme") || "dark") === "dark");
  const [metadata, setMetadata] = useState(null);
  const [formValues, setFormValues] = useState({});
  const [prediction, setPrediction] = useState(null);
  const [summary, setSummary] = useState(null);
  const [yieldDist, setYieldDist] = useState([]);
  const [categoryCounts, setCategoryCounts] = useState([]);
  const [topCrops, setTopCrops] = useState([]);
  const [diagnostics, setDiagnostics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [baseYield, setBaseYield] = useState(null);
  const [simulatedYield, setSimulatedYield] = useState(null);
  const [simDelta, setSimDelta] = useState(null);
  
  const [compareCrop, setCompareCrop] = useState("");
  const [compareResult, setCompareResult] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState("");

  // Scroll Reveal Observer
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, [metadata, prediction, diagnostics, summary]);

  useEffect(() => {
    const theme = darkMode ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", theme);
    setCookie("app_theme", theme);
  }, [darkMode]);

  async function init(retries = 5) {
    if (retries === 5) setError(""); // Only clear error on first attempt
    try {
      const data = await getFormMetadata();
      setMetadata(data);
      const initial = {};
      data.categorical_columns.forEach((col) => {
        initial[col] = data.category_values[col]?.[0] ?? "";
      });
      data.numeric_columns.forEach((col) => {
        const r = data.numeric_ranges?.[col];
        initial[col] = r ? (r.min + r.max) / 2 : 0;
      });
      setFormValues(initial);
    } catch (err) {
      if (retries > 0) {
        console.warn(`Metadata load failed. Retrying in 2s... (${retries} left)`);
        setTimeout(() => init(retries - 1), 2000);
      } else {
        setError(err?.response?.data?.detail || err.message || "Failed to load metadata after multiple attempts.");
      }
    }
  }

  useEffect(() => {
    init();
  }, []);

  useEffect(() => {
    if (!baseYield || !metadata) return;
    
    const handler = setTimeout(async () => {
      try {
        const normalized = { ...formValues };
        (metadata?.numeric_columns || []).forEach((col) => {
          normalized[col] = Number(normalized[col]);
        });
        const pred = await predictBoth(normalized);
        const y = pred.predicted_yield_kg_ha;
        setSimulatedYield(y);
        setSimDelta(y - baseYield);
      } catch (err) {
        // ignore errors in simulator
      }
    }, 400); // 400ms debounce
    
    return () => clearTimeout(handler);
  }, [formValues, baseYield, metadata]);

  const filterParams = useMemo(
    () => ({
      state: formValues.State || undefined,
      crop_type: formValues.Crop_Type || undefined,
      season: formValues.Season || undefined
    }),
    [formValues]
  );

  const onInputChange = (key, value) => {
    setFormValues((prev) => ({ ...prev, [key]: value }));
  };

  const getRangeText = (col) => {
    const range = metadata?.numeric_ranges?.[col];
    if (!range) {
      return "Range: not available";
    }
    return `Range: ${range.min.toFixed(2)} to ${range.max.toFixed(2)}`;
  };

  async function fetchAnalytics(normalizedValues) {
    const [summaryRes, distRes, catRes, topCropsRes, diagRes] = await Promise.all([
      getSummary(filterParams),
      getYieldDistribution(filterParams),
      getCategoryCounts(filterParams),
      getTopCropsByConditions(normalizedValues, 5),
      getConditionDiagnostics({
        avg_temp_c: Number(normalizedValues.Avg_Temp_C),
        rainfall_mm: Number(normalizedValues.Rainfall_mm),
        humidity_pct: Number(normalizedValues.Humidity_Pct),
        water_stress_index: Number(normalizedValues.Water_Stress_Index),
        soil_ph: Number(normalizedValues.Soil_pH),
        n_kgha: Number(normalizedValues.N_kgha),
        p_kgha: Number(normalizedValues.P_kgha),
        k_kgha: Number(normalizedValues.K_kgha),
        ndvi: Number(normalizedValues.NDVI)
      })
    ]);
    setSummary(summaryRes);
    setYieldDist(distRes.series || []);
    setCategoryCounts(catRes.series || []);
    setTopCrops(topCropsRes.rows || []);
    setDiagnostics(diagRes);
  }

  async function onCompare() {
    if (!prediction || !compareCrop) return;
    setCompareLoading(true);
    setCompareError("");
    try {
      const normalized = { ...formValues, Crop_Type: compareCrop };
      (metadata?.numeric_columns || []).forEach((col) => {
        normalized[col] = Number(normalized[col]);
      });
      const pred = await predictBoth(normalized);
      setCompareResult(pred);
    } catch (err) {
      setCompareError(err?.response?.data?.detail || "Compare failed.");
    } finally {
      setCompareLoading(false);
    }
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const normalized = { ...formValues };
      (metadata?.numeric_columns || []).forEach((col) => {
        normalized[col] = Number(normalized[col]);
      });
      const pred = await predictBoth(normalized);
      setPrediction(pred);
      setBaseYield(pred.predicted_yield_kg_ha);
      setSimulatedYield(pred.predicted_yield_kg_ha);
      setSimDelta(0);
      setCompareResult(null); // Reset compare on new prediction
      
      // Save for Ask AI context (both localStorage and server-side for cross-port access)
      const predictionCtx = {
        ...normalized,
        predicted_yield_kg_ha: pred.predicted_yield_kg_ha,
        predicted_category: pred.predicted_category,
        recommended_crop: pred.recommended_crop
      };
      localStorage.setItem("last_prediction", JSON.stringify(predictionCtx));
      // Also save to backend so Ask AI (port 8005) can read it
      fetch(`${CROP_AI_BASE}/api/prediction-context`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ context: predictionCtx })
      }).catch(err => console.warn("Could not sync prediction to backend:", err));
      
      // Show results immediately
      setLoading(false);
      
      // Scroll to result
      setTimeout(() => {
        document.querySelector('.resultStack')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
      
      // Load analytics in background
      try {
        await fetchAnalytics(normalized);
      } catch (analyticsErr) {
        console.error("Analytics load failed:", analyticsErr);
      }
    } catch (err) {
      setError(err?.response?.data?.detail || "Prediction failed.");
      setLoading(false);
    }
  }

  if (!showDashboard) {
    return <Landing onEnter={() => setShowDashboard(true)} />;
  }

  if (!metadata) {
    return (
      <Shell darkMode={darkMode} setDarkMode={setDarkMode}>
        <div className="pageHead">
          <h1>🌾 Crop Yield Prediction</h1>
          <p>Loading field metadata from the API…</p>
        </div>
        {error ? (
          <div className="error glass">
            {String(error)}
            <br />
            <button 
              onClick={init} 
              className="primary" 
              style={{ marginTop: 16, padding: "8px 24px", fontSize: "0.9rem" }}
            >
              🔄 Retry Connection
            </button>
            <br /><br />
            Start the DWDM API from <code>backend</code> (e.g.{" "}
            <code>python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8005</code>), restart{" "}
            <code>npm run dev</code>, then reload. In dev, requests are proxied using{" "}
            <code>VITE_API_PROXY_TARGET</code> in <code>frontend/.env.development</code> (must match your API
            port). To call the API directly instead, set <code>VITE_API_BASE_URL</code>.
            <br />
            <small style={{ marginTop: 8, display: "block", color: "var(--text-muted)" }}>
              Batch / Ask AI use the CropYield Python app at <code>{CROP_AI_BASE}</code> — override with{" "}
              <code>VITE_CROP_AI_BASE_URL</code> if needed.
            </small>
          </div>
        ) : (
          <div className="loadingMain">Preparing dashboard…</div>
        )}
      </Shell>
    );
  }

  return (
    <Shell darkMode={darkMode} setDarkMode={setDarkMode}>
      <div className="pageHead stagger-in">
        <h1>🌾 Crop Yield Prediction</h1>
        <p>
          Enter your field details below to predict yield using the DWDM API, then review charts and condition
          diagnostics.
        </p>
      </div>

      {error && <div className="error glass">{String(error)}</div>}
      {summary?.used_fallback && (
        <div className="warnBanner glass">No exact rows for current filters — charts may use overall dataset totals.</div>
      )}

      <div className="predictLayout stagger-in">
        <section className="leftCol">
          <form onSubmit={onSubmit}>
            <details open className="glass reveal">
              <summary>{`🌱 Crop, location & season`}</summary>
              <div className="formInner">
                {metadata.categorical_columns.map((col) => (
                  <label key={col} className="field">
                    <span>{col}</span>
                    <select value={formValues[col] || ""} onChange={(e) => onInputChange(col, e.target.value)}>
                      {metadata.category_values[col]?.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </label>
                ))}
              </div>
            </details>

            {(() => {
              const categories = {
                "🌤️ Climate": ["Avg_Temp_C", "Rainfall_mm", "Humidity_Pct", "Water_Stress_Index"],
                "🪨 Soil": ["Soil_pH"],
                "🧪 Nutrients": ["N_kgha", "P_kgha", "K_kgha", "NDVI"]
              };
              const handledCols = new Set(Object.values(categories).flat());
              const otherCols = metadata.numeric_columns.filter(c => !handledCols.has(c));
              if (otherCols.length > 0) {
                categories["⚙️ Other"] = otherCols;
              }

              return Object.entries(categories).map(([categoryName, cols]) => {
                const validCols = cols.filter(c => metadata.numeric_columns.includes(c));
                if (validCols.length === 0) return null;
                return (
                  <details open key={categoryName} className="glass">
                    <summary>{categoryName}</summary>
                    <div className="formInner">
                      {validCols.map((col) => {
                        const minRef = metadata?.numeric_ranges?.[col]?.min || 0;
                        const maxRef = metadata?.numeric_ranges?.[col]?.max || 100;
                        return (
                          <RangeInputWithWarning
                            key={col}
                            col={col}
                            value={formValues[col]}
                            onChange={(val) => onInputChange(col, val)}
                            minRef={minRef}
                            maxRef={maxRef}
                          />
                        );
                      })}
                    </div>
                  </details>
                );
              });
            })()}

            <div className="btnRow">
              <button type="submit" className="primary" disabled={loading}>
                {loading ? "Predicting…" : "🔍 Predict Yield"}
              </button>
            </div>
            
            <details style={{ marginTop: "16px" }} open className="glass">
              <summary>🔬 Live Yield Simulator</summary>
              <div className="formInner" style={{ padding: "8px 0" }}>
                {baseYield === null ? (
                  <p style={{ color: "var(--text-muted)", margin: 0, fontSize: "0.9rem" }}>👈 Click Predict Yield first to enable the live simulator.</p>
                ) : (
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.9rem", background: "rgba(0,0,0,0.03)", padding: "12px", borderRadius: "12px" }}>
                    <span>Base: <strong>{Math.round(baseYield).toLocaleString()}</strong> kg/ha</span>
                    <span>
                      Current: <strong>{Math.round(simulatedYield).toLocaleString()}</strong> kg/ha
                      <span style={{ marginLeft: "8px", fontWeight: "bold", color: simDelta >= 0 ? "var(--green)" : "#ef4444" }}>
                        {simDelta >= 0 ? "↑" : "↓"} {simDelta >= 0 ? "+" : ""}{Math.round(simDelta).toLocaleString()} kg/ha
                      </span>
                    </span>
                  </div>
                )}
              </div>
            </details>

            <details style={{ marginTop: "12px" }} className="glass">
              <summary>🔄 Compare with Another Crop</summary>
              <div style={{ padding: "16px 20px" }}>
                <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", margin: "0 0 10px" }}>Uses the same field conditions — only crop type changes.</p>
                {baseYield === null ? (
                  <p style={{ color: "var(--text-muted)", margin: 0, fontSize: "0.9rem" }}>👈 Click Predict Yield first to enable crop comparison.</p>
                ) : (
                  <>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: compareResult ? "14px" : "0" }}>
                      <select 
                        value={compareCrop} 
                        onChange={(e) => setCompareCrop(e.target.value)}
                        style={{ flex: 1, maxWidth: "220px" }}
                      >
                        <option value="">Select crop...</option>
                        {metadata?.category_values?.Crop_Type?.map(c => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                      <button type="button" onClick={onCompare} disabled={compareLoading || !compareCrop} className="primary" style={{ padding: "10px 18px", fontSize: "0.9rem" }}>
                        {compareLoading ? "Comparing…" : "Compare"}
                      </button>
                    </div>
                    {compareError && <p style={{ color: "#ef4444", fontSize: "0.82rem", margin: "6px 0 0" }}>{compareError}</p>}
                    {compareResult && (
                      <>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", textAlign: "center" }}>
                          <div style={{ padding: "14px", borderRadius: "14px", border: "1px solid var(--border)", background: "var(--input-bg)" }}>
                            <strong style={{ fontSize: "0.95rem" }}>{prediction.selected_crop}</strong>
                            <div className="glow-text" style={{ fontSize: "1.3rem", fontWeight: 800, margin: "4px 0" }}>{Math.round(prediction.predicted_yield_kg_ha).toLocaleString()} <small style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>kg/ha</small></div>
                            <span className={badgeClassForCategory(prediction.predicted_category)} style={{ fontSize: "0.7rem", padding: "4px 10px" }}>{prediction.predicted_category}</span>
                          </div>
                          <div style={{ padding: "14px", borderRadius: "14px", border: "1px solid var(--border)", background: "var(--input-bg)" }}>
                            <strong style={{ fontSize: "0.95rem" }}>{compareResult.selected_crop}</strong>
                            <div className="glow-text" style={{ fontSize: "1.3rem", fontWeight: 800, margin: "4px 0" }}>{Math.round(compareResult.predicted_yield_kg_ha).toLocaleString()} <small style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>kg/ha</small></div>
                            <span className={badgeClassForCategory(compareResult.predicted_category)} style={{ fontSize: "0.7rem", padding: "4px 10px" }}>{compareResult.predicted_category}</span>
                          </div>
                        </div>
                        {(() => {
                          const diff = compareResult.predicted_yield_kg_ha - prediction.predicted_yield_kg_ha;
                          const better = diff > 0 ? compareResult.selected_crop : prediction.selected_crop;
                          const color = diff > 0 ? "var(--green)" : "#ef4444";
                          return (
                            <div style={{ textAlign: "center", marginTop: "10px", padding: "8px 12px", borderRadius: "10px", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", fontSize: "0.85rem" }}>
                              <span style={{ fontWeight: 700, color }}>{better}</span> yields <strong style={{ color }}>{Math.abs(Math.round(diff)).toLocaleString()} kg/ha</strong> more than {diff > 0 ? prediction.selected_crop : compareResult.selected_crop}
                            </div>
                          );
                        })()}
                      </>
                    )}
                  </>
                )}
              </div>
            </details>
          </form>
        </section>

        <section className="rightCol">
          {!prediction ? (
            <div className="placeholder glass">
              👈 Fill in your field details and click <strong>Predict Yield</strong> to see results here.
            </div>
          ) : (
            <div className="resultStack">
              <div className="card mainPred glass" style={{ textAlign: "center" }}>
                <h3 style={{ margin: "0 0 10px" }}>Predicted Yield</h3>
                <div className="bigYield glow-text">{Math.round(prediction.predicted_yield_kg_ha).toLocaleString()} <small>kg/ha</small></div>
                <div style={{ fontSize: "1rem", color: "var(--text-muted)", marginBottom: "15px" }}>
                  Typical average for {prediction.selected_crop}: <strong>{Math.round(prediction.typical_mean_yield).toLocaleString()} kg/ha</strong>
                </div>
                <div className="badgeRow">
                  <span className={badgeClassForCategory(prediction.predicted_category)} title={`This rating is calculated specifically for ${prediction.selected_crop}.`}>
                    {prediction.predicted_category}
                  </span>
                </div>
                {!prediction.is_typical_for_conditions && (
                  <div style={{ background: "rgba(255, 152, 0, 0.1)", padding: "12px", borderRadius: "12px", marginTop: "20px", fontSize: "0.9rem", color: "var(--amber)", border: "1px solid rgba(255,152,0,0.2)" }}>
                    ℹ️ Note: <strong>{prediction.selected_crop}</strong> is not typically grown in the selected <strong>{formValues.Season}</strong> season in <strong>{formValues.State}</strong>.
                  </div>
                )}
              </div>

              <div className="resultCards">
                <div className="card glass">
                  <h3>Best crop to plant</h3>
                  <p style={{ fontSize: '1.2rem', fontWeight: 700 }}>{prediction.recommended_crop}</p>
                  <p className="bigYield glow-text" style={{ fontSize: "1.5rem", marginTop: 6 }}>
                    {prediction.recommended_crop_predicted_yield_kg_ha.toFixed(0)}{" "}
                    <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-muted)" }}>kg/ha</span>
                  </p>
                </div>
                <div className="card glass">
                  <h3>Condition score</h3>
                  <p className="bigYield glow-text">{diagnostics?.condition_score ?? "—"}</p>
                  <small className="hint">out of 100</small>
                </div>
              </div>

              {diagnostics && (
                <div className="panel glass reveal">
                  <h3 style={{ margin: "0 0 12px", fontSize: "1rem" }}>Condition diagnostics</h3>
                  <p style={{ marginBottom: '10px' }}>
                    <strong>Nutrient check:</strong> {diagnostics.nutrient_note}
                  </p>
                  {!!diagnostics.alerts?.length ? (
                    <ul className="alertsList">
                      {diagnostics.alerts.map((item) => (
                        <li key={item} style={{ marginBottom: '6px' }}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="hint">No major risk alerts detected.</p>
                  )}
                </div>
              )}

              {!!topCrops.length && (
                <div className="card glass reveal" style={{ marginTop: '20px' }}>
                  <h3 style={{ marginBottom: '15px' }}>Top 5 crops for current conditions</h3>
                  <table className="cropTable">
                    <thead>
                      <tr>
                        <th>Rank</th>
                        <th>Crop</th>
                        <th>Predicted yield (kg/ha)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topCrops.map((row, idx) => {
                        const maxYield = topCrops[0]?.predicted_yield || 1;
                        const pct = (row.predicted_yield / maxYield) * 100;
                        return (
                          <tr key={row.crop}>
                            <td><div className="rankCircle">{idx + 1}</div></td>
                            <td><strong>{row.crop}</strong></td>
                            <td>
                              <div style={{ fontWeight: 800, color: 'var(--green)' }}>{Math.round(row.predicted_yield).toLocaleString()} kg/ha</div>
                              <div className="yieldBar">
                                <div className="yieldBarInner" style={{ width: `${pct}%` }}></div>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </Shell>
  );
}

export default App;

