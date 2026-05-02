document.addEventListener('DOMContentLoaded', async () => {
    // 1. Initialize Filters
    const cropSelect = document.getElementById('filterCrop');
    const seasonSelect = document.getElementById('filterSeason');
    const stateSelect = document.getElementById('filterState');
    const trendCropsDiv = document.getElementById('trendCrops');
    const recordCount = document.getElementById('recordCount');

    // Fetch Meta for dropdowns
    let cats = {};
    try {
        const metaResp = await fetch('/meta/form');
        if (!metaResp.ok) throw new Error(`Meta fetch failed: ${metaResp.status}`);
        const meta = await metaResp.json();
        cats = meta.category_values || {};

        const populate = (select, options) => {
            select.innerHTML = '<option value="All">All</option>';
            if (!options || !Array.isArray(options)) return;
            options.sort().forEach(opt => {
                const el = document.createElement('option');
                el.value = opt;
                el.textContent = opt;
                select.appendChild(el);
            });
        };

        populate(cropSelect, cats.Crop_Type);
        populate(seasonSelect, cats.Season);
        populate(stateSelect, cats.State);

        // Trend crop checkboxes
        const crops = cats.Crop_Type || [];
        const defaultTrendCrops = crops.slice(0, 5);
        trendCropsDiv.innerHTML = '';
        crops.forEach(crop => {
            const lbl = document.createElement('label');
            lbl.style.cssText = 'display:flex;align-items:center;gap:5px;font-size:0.8rem;cursor:pointer;';
            lbl.innerHTML = `<input type="checkbox" name="trendCrop" value="${crop}" ${defaultTrendCrops.includes(crop) ? 'checked' : ''}> ${crop}`;
            trendCropsDiv.appendChild(lbl);
        });
    } catch (err) {
        console.error("Critical error loading analytics meta:", err);
        recordCount.innerHTML = `<span style="color:#ef4444;">Error loading data. Please refresh the page.</span>`;
        return;
    }

    // 2. Helper to safely fetch JSON
    async function safeFetch(url) {
        try {
            const resp = await fetch(url);
            if (!resp.ok) {
                console.warn(`Fetch failed for ${url}: ${resp.status}`);
                return null;
            }
            return await resp.json();
        } catch (e) {
            console.warn(`Fetch error for ${url}:`, e);
            return null;
        }
    }

    // 3. Global Refresh Function
    const refresh = async () => {
        const crop = cropSelect.value;
        const season = seasonSelect.value;
        const state = stateSelect.value;

        // Build params for chart endpoints (use crop/season/state)
        const chartParams = `crop=${encodeURIComponent(crop)}&season=${encodeURIComponent(season)}&state=${encodeURIComponent(state)}`;
        // Build params for summary endpoint (uses crop_type/season/state, and null instead of All)
        const summaryParams = new URLSearchParams();
        if (crop !== 'All') summaryParams.set('crop_type', crop);
        if (season !== 'All') summaryParams.set('season', season);
        if (state !== 'All') summaryParams.set('state', state);

        // Fetch all data in parallel
        const [summary, npkData, rainData, heatData, pestData, trendData] = await Promise.all([
            safeFetch(`/analytics/summary?${summaryParams}`),
            safeFetch(`/analytics/npk-impact?${chartParams}&nutrient=${document.querySelector('input[name="npkNutrient"]:checked').value}`),
            safeFetch(`/analytics/rainfall-yield?${chartParams}`),
            safeFetch(`/analytics/heatmap?${chartParams}`),
            safeFetch(`/analytics/pest-disease-impact?${chartParams}`),
            (() => {
                const selectedCrops = Array.from(document.querySelectorAll('input[name="trendCrop"]:checked')).map(i => i.value);
                const tp = new URLSearchParams();
                if (state !== 'All') tp.set('state', state);
                selectedCrops.forEach(c => tp.append('crops', c));
                return safeFetch(`/analytics/yield-trend?${tp}`);
            })()
        ]);

        // Update record count & handle zero results
        const matchCount = summary ? summary.selected_count : null;
        const noData = matchCount === 0;

        if (summary) {
            if (noData) {
                recordCount.innerHTML = `<span style="color:#FB8C00;font-weight:600;">⚠️ No records match this filter combination.</span> Try changing the Crop, Season, or State.`;
            } else {
                recordCount.textContent = `Showing ${matchCount.toLocaleString()} records based on current filters`;
            }
        }

        // Render charts (each is independent — one failing won't block others)
        if (!noData && npkData) renderNPK(npkData); else Plotly.purge('chartNPK');
        if (!noData && rainData) renderRainfall(rainData, crop); else Plotly.purge('chartRainfall');
        if (!noData && heatData) renderHeatmap(heatData); else Plotly.purge('chartHeatmap');
        if (!noData && pestData) renderPestDisease(pestData); else { Plotly.purge('chartPest'); Plotly.purge('chartDisease'); }
        if (!noData && trendData) renderTrend(trendData); else { Plotly.purge('chartTrend'); document.getElementById('metricsTrend').innerHTML = ''; }

        // Feature importance (static, load once)
        if (!window.importanceLoaded) {
            const impData = await safeFetch('/analytics/feature-importance');
            if (impData) {
                renderImportance(impData);
                window.importanceLoaded = true;
            }
        }
    };

    // 4. Render Functions
    function renderNPK(data) {
        if (!data.series || !data.series.length) {
            Plotly.purge('chartNPK');
            return;
        }
        const crops = [...new Set(data.series.map(d => d.crop))];
        const tiers = ["Low", "Medium", "High"];
        const colors = { "Low": "#E53935", "Medium": "#FB8C00", "High": "#43A047" };

        const traces = tiers.map(tier => ({
            name: tier,
            x: crops,
            y: crops.map(c => data.series.find(d => d.crop === c && d.tier === tier)?.yield || 0),
            type: 'bar',
            marker: { color: colors[tier] }
        }));

        Plotly.newPlot('chartNPK', traces, {
            barmode: 'group',
            paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
            margin: { t: 30, b: 80, l: 60, r: 20 },
            font: { color: '#888' },
            xaxis: { title: 'Crop Type' }, yaxis: { title: 'Avg Yield (kg/ha)' }
        }, { responsive: true });

        const insightEl = document.getElementById('insightNPK');
        if (data.insight) {
            insightEl.innerHTML = `💡 <strong>Key Insight:</strong> ${data.insight}`;
            insightEl.style.display = 'block';
        } else {
            insightEl.style.display = 'none';
        }
    }

    function renderRainfall(data, crop) {
        if (!data.series || !data.series.length) {
            Plotly.purge('chartRainfall');
            return;
        }
        const trace = {
            x: data.series.map(d => d.Rainfall_mm),
            y: data.series.map(d => d.Crop_Yield_kg_ha),
            mode: 'markers', type: 'scatter',
            marker: {
                color: data.series.map(d => ({ 'Low': '#E53935', 'Medium': '#FB8C00', 'High': '#43A047' }[d.Yield_Category] || '#888')),
                opacity: 0.5, size: 6
            },
            hovertemplate: 'Rainfall: %{x:.0f}mm<br>Yield: %{y:,.0f} kg/ha<extra></extra>'
        };

        const shapes = [];
        if (data.optimal_range) {
            shapes.push({
                type: 'rect', xref: 'x', yref: 'paper',
                x0: data.optimal_range[0], x1: data.optimal_range[1],
                y0: 0, y1: 1,
                fillcolor: '#43A047', opacity: 0.1, line: { width: 0 }
            });
        }

        Plotly.newPlot('chartRainfall', [trace], {
            paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
            margin: { t: 30, b: 50, l: 60, r: 20 },
            font: { color: '#888' },
            xaxis: { title: 'Annual Rainfall (mm)' }, yaxis: { title: 'Yield (kg/ha)' },
            shapes
        }, { responsive: true });

        const insightEl = document.getElementById('insightRainfall');
        if (data.insight) {
            insightEl.innerHTML = `💡 <strong>Key Insight:</strong> ${data.insight}`;
            insightEl.style.display = 'block';
        } else {
            insightEl.style.display = 'none';
        }
    }

    function renderHeatmap(data) {
        if (!data.z || !data.z.length) {
            Plotly.purge('chartHeatmap');
            return;
        }
        const trace = {
            z: data.z, x: data.x, y: data.y,
            type: 'heatmap',
            colorscale: [[0, '#FFFFFF'], [0.3, '#C8E6C9'], [0.6, '#4CAF50'], [1.0, '#1B5E20']],
            showscale: true,
            hovertemplate: 'State: %{y}<br>Season: %{x}<br>Avg Yield: %{z:,.0f} kg/ha<extra></extra>'
        };

        Plotly.newPlot('chartHeatmap', [trace], {
            paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
            margin: { t: 30, b: 50, l: 120, r: 20 },
            font: { color: '#888' },
            xaxis: { title: 'Season' }, yaxis: { title: 'State' }
        }, { responsive: true });

        const insightEl = document.getElementById('insightHeatmap');
        if (data.insight) {
            insightEl.innerHTML = `✅ <strong>${data.insight}</strong>`;
            insightEl.style.display = 'block';
        } else {
            insightEl.style.display = 'none';
        }
    }

    function renderPestDisease(data) {
        const colors = { "None": "#43A047", "Low": "#FDD835", "Moderate": "#FB8C00", "High": "#E53935" };

        if (data.pest && data.pest.length) {
            Plotly.newPlot('chartPest', [{
                x: data.pest.map(d => d.level), y: data.pest.map(d => d.yield),
                type: 'bar', marker: { color: data.pest.map(d => colors[d.level]) },
                text: data.pest.map(d => Math.round(d.yield).toLocaleString()), textposition: 'outside'
            }], {
                paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
                margin: { t: 30, b: 50, l: 50, r: 20 }, font: { color: '#888' },
                xaxis: { title: 'Pest Level' }, yaxis: { title: 'Avg Yield' }
            }, { responsive: true });
        }

        if (data.disease && data.disease.length) {
            Plotly.newPlot('chartDisease', [{
                x: data.disease.map(d => d.level), y: data.disease.map(d => d.yield),
                type: 'bar', marker: { color: data.disease.map(d => colors[d.level]) },
                text: data.disease.map(d => Math.round(d.yield).toLocaleString()), textposition: 'outside'
            }], {
                paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
                margin: { t: 30, b: 50, l: 50, r: 20 }, font: { color: '#888' },
                xaxis: { title: 'Disease Level' }, yaxis: { title: 'Avg Yield' }
            }, { responsive: true });
        }

        const pestInsight = document.getElementById('insightPest');
        const disInsight = document.getElementById('insightDisease');
        pestInsight.style.display = data.pest_loss_insight ? 'block' : 'none';
        if (data.pest_loss_insight) pestInsight.textContent = '🔴 ' + data.pest_loss_insight;
        disInsight.style.display = data.disease_loss_insight ? 'block' : 'none';
        if (data.disease_loss_insight) disInsight.textContent = '🔴 ' + data.disease_loss_insight;
    }

    function renderImportance(data) {
        if (!data.series || !data.series.length) return;
        const colors = data.series.map(d => {
            const f = d.feature;
            if (f.includes('Potassium') || f.includes('Nitrogen') || f.includes('Phosphorus')) return '#1B5E20';
            if (f.includes('Rainfall') || f.includes('Temperature') || f.includes('Season')) return '#1565C0';
            return '#FB8C00';
        });

        Plotly.newPlot('chartImportance', [{
            y: data.series.map(d => d.feature), x: data.series.map(d => d.importance),
            type: 'bar', orientation: 'h', marker: { color: colors },
            text: data.series.map(d => d.importance.toFixed(2) + '%'), textposition: 'outside'
        }], {
            paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
            margin: { t: 30, b: 50, l: 200, r: 50 }, font: { color: '#888' },
            xaxis: { title: 'Importance (%)', range: [0, 35] }
        }, { responsive: true });
    }

    function renderTrend(data) {
        if (!data.series || !data.series.length) {
            Plotly.purge('chartTrend');
            document.getElementById('metricsTrend').innerHTML = '';
            return;
        }
        const crops = [...new Set(data.series.map(d => d.Crop_Type))];
        const traces = crops.map(crop => {
            const cropData = data.series.filter(d => d.Crop_Type === crop);
            return {
                name: crop,
                x: cropData.map(d => d.Year), y: cropData.map(d => d.Crop_Yield_kg_ha),
                mode: 'lines+markers', type: 'scatter'
            };
        });

        Plotly.newPlot('chartTrend', traces, {
            paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
            margin: { t: 30, b: 50, l: 60, r: 20 }, font: { color: '#888' },
            xaxis: { title: 'Year' }, yaxis: { title: 'Avg Yield (kg/ha)' },
            hovermode: 'closest'
        }, { responsive: true });

        const metricsDiv = document.getElementById('metricsTrend');
        metricsDiv.innerHTML = '';
        (data.metrics || []).forEach(m => {
            const el = document.createElement('div');
            el.className = 'metric';
            const arrow = m.change > 0 ? '📈' : '📉';
            const cls = m.change > 0 ? 'up' : 'down';
            el.innerHTML = `
                <div class="metric-label">${m.crop}</div>
                <div class="metric-val">${Math.round(m.yield).toLocaleString()} kg/ha</div>
                <div class="metric-delta ${cls}">${arrow} ${m.change.toFixed(1)}% since 2000</div>
            `;
            metricsDiv.appendChild(el);
        });
    }

    // 5. Event Listeners
    [cropSelect, seasonSelect, stateSelect].forEach(s => s.addEventListener('change', refresh));
    document.querySelectorAll('input[name="npkNutrient"]').forEach(r => r.addEventListener('change', refresh));
    trendCropsDiv.addEventListener('change', refresh);

    // Initial load
    refresh();
});
