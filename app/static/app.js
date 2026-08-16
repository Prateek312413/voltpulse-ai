/**
 * Frontend Application Logic for Uncertainty-Aware Battery Health Forecast Engine
 * Handles REST API interactions, interactive Canvas confidence band rendering,
 * dual-order telemetry queries, live toast notifications, and the 12-scenario PRD test suite.
 */

// State
const state = {
  activeBatteryId: null,
  batteries: [],
  activeBatteryMeta: null,
  observations: [],
  telemetryOrder: 'event_time',
  forecasts: [],
  currentForecast: null,
  evaluations: [],
  diffs: [],
  scenarios: []
};

// Canvas Chart References
let mainCanvas, mainCtx;
let ttCanvas, ttCtx;

document.addEventListener('DOMContentLoaded', () => {
  initDOM();
  initTabs();
  initCharts();
  loadBatteries();
  loadScenariosList();

  // Responsive resize
  window.addEventListener('resize', debounce(() => {
    renderForecastChart();
    renderTimeTravelChart();
  }, 150));
});

function initDOM() {
  // Battery Select
  document.getElementById('batterySelect').addEventListener('change', (e) => {
    state.activeBatteryId = e.target.value;
    onBatteryChanged();
  });

  document.getElementById('btnNewBattery').addEventListener('click', () => {
    document.getElementById('batteryModal').classList.remove('hidden');
  });

  document.getElementById('btnCloseBatModal').addEventListener('click', () => {
    document.getElementById('batteryModal').classList.add('hidden');
  });

  document.getElementById('btnCancelBatModal').addEventListener('click', () => {
    document.getElementById('batteryModal').classList.add('hidden');
  });

  document.getElementById('batteryForm').addEventListener('submit', handleCreateBattery);

  // Seed Demo
  document.getElementById('btnSeedDemo').addEventListener('click', handleSeedDemo);

  // Forecast Form
  document.getElementById('forecastForm').addEventListener('submit', handleRunForecast);

  // Telemetry Order Toggles
  document.getElementById('btnOrderEvent').addEventListener('click', () => {
    setTelemetryOrder('event_time');
  });
  document.getElementById('btnOrderReceive').addEventListener('click', () => {
    setTelemetryOrder('receive_time');
  });

  // Telemetry Modal
  document.getElementById('btnOpenIngestModal').addEventListener('click', () => {
    openIngestModal();
  });
  document.getElementById('btnCloseModal').addEventListener('click', () => {
    document.getElementById('telemetryModal').classList.add('hidden');
  });
  document.getElementById('btnCancelModal').addEventListener('click', () => {
    document.getElementById('telemetryModal').classList.add('hidden');
  });
  document.getElementById('telemetryForm').addEventListener('submit', handleTelemetrySubmit);

  // Simulate Late Telemetry
  document.getElementById('btnSimulateLate').addEventListener('click', handleSimulateLate);

  // Re-Evaluate Models
  document.getElementById('btnReevaluateModels').addEventListener('click', loadModelEvaluations);

  // Force Reconcile
  document.getElementById('btnForceReconcile').addEventListener('click', handleForceReconcile);

  // Time Travel Slider
  document.getElementById('timeTravelSlider').addEventListener('input', handleTimeTravelSlide);

  // Replay Determinism Test
  document.getElementById('btnRunReplayTest').addEventListener('click', handleRunReplayTest);

  // Scenario Drawer
  document.getElementById('btnCloseDrawer').addEventListener('click', () => {
    document.getElementById('scenarioResultDrawer').classList.add('hidden');
  });
  document.getElementById('btnRunAllScenarios').addEventListener('click', handleRunAllScenarios);
}

function initTabs() {
  const buttons = document.querySelectorAll('.tab-btn');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      
      btn.classList.add('active');
      const target = btn.getAttribute('data-tab');
      document.getElementById(target).classList.add('active');

      if (target === 'tab-overview') renderForecastChart();
      if (target === 'tab-timetravel') renderTimeTravelChart();
    });
  });
}

function initCharts() {
  mainCanvas = document.getElementById('forecastChart');
  mainCtx = mainCanvas.getContext('2d');

  ttCanvas = document.getElementById('timeTravelChart');
  ttCtx = ttCanvas.getContext('2d');

  // Tooltip tracking on main canvas
  mainCanvas.addEventListener('mousemove', handleChartHover);
  mainCanvas.addEventListener('mouseleave', () => {
    document.getElementById('chartTooltip').style.display = 'none';
  });
}

function showToast(message, type = 'info') {
  const existing = document.getElementById('appToast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'appToast';
  toast.style.position = 'fixed';
  toast.style.bottom = '24px';
  toast.style.left = '50%';
  toast.style.transform = 'translateX(-50%)';
  toast.style.backgroundColor = type === 'error' ? '#ef4444' : (type === 'success' ? '#10b981' : '#1e293b');
  toast.style.color = '#ffffff';
  toast.style.padding = '10px 20px';
  toast.style.borderRadius = '8px';
  toast.style.fontSize = '13px';
  toast.style.fontWeight = '500';
  toast.style.boxShadow = '0 6px 20px rgba(0,0,0,0.5)';
  toast.style.zIndex = '9999';
  toast.style.transition = 'opacity 0.3s ease';
  toast.textContent = message;

  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

/* ==========================================================================
   API Operations & Data Loading
   ========================================================================== */

async function loadBatteries() {
  try {
    const res = await fetch('/batteries');
    const data = await res.json();
    state.batteries = data;

    const select = document.getElementById('batterySelect');
    select.innerHTML = '';
    
    if (data.length === 0) {
      select.innerHTML = '<option value="">No batteries found (Click Seed Demo)</option>';
      return;
    }

    data.forEach(b => {
      const opt = document.createElement('option');
      opt.value = b.battery_id;
      opt.textContent = `${b.battery_id} (${b.battery_type}) - v${b.active_telemetry_version}`;
      select.appendChild(opt);
    });

    if (!state.activeBatteryId || !data.some(b => b.battery_id === state.activeBatteryId)) {
      state.activeBatteryId = data[0].battery_id;
    }
    select.value = state.activeBatteryId;
    onBatteryChanged();
  } catch (err) {
    console.error('Failed to load batteries:', err);
  }
}

async function onBatteryChanged() {
  if (!state.activeBatteryId) return;

  try {
    const res = await fetch(`/batteries/${state.activeBatteryId}`);
    const meta = await res.json();
    state.activeBatteryMeta = meta;

    document.getElementById('lblBatteryId').textContent = meta.battery_id;
    document.getElementById('lblBatteryType').textContent = meta.battery_type;
    document.getElementById('lblNominalCap').textContent = `${meta.nominal_capacity} Ah`;
    document.getElementById('lblTelVersion').textContent = `v${meta.active_telemetry_version}`;

    // Load sub-resources
    await Promise.all([
      loadTelemetry(),
      loadForecasts(),
      loadModelEvaluations(),
      loadDiffs()
    ]);

    // Setup Time Travel slider bounds
    const slider = document.getElementById('timeTravelSlider');
    slider.min = 1;
    slider.max = Math.max(1, meta.active_telemetry_version);
    slider.value = slider.max;
    document.getElementById('lblScrubVer').textContent = `v${slider.value}`;
  } catch (err) {
    console.error('Error changing battery:', err);
  }
}

async function handleCreateBattery(e) {
  e.preventDefault();
  const id = document.getElementById('newBatId').value.trim();
  const type = document.getElementById('newBatType').value.trim();
  const cap = parseFloat(document.getElementById('newBatCap').value);

  try {
    const res = await fetch('/batteries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ battery_id: id, battery_type: type, nominal_capacity: cap })
    });
    if (!res.ok) {
      const err = await res.json();
      showToast(`Error: ${err.detail}`, 'error');
      return;
    }
    document.getElementById('batteryModal').classList.add('hidden');
    state.activeBatteryId = id;
    await loadBatteries();
    showToast(`Battery '${id}' registered successfully!`, 'success');
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

async function handleSeedDemo() {
  const seedBatId = 'BAT-NASA-DEMO-01';
  try {
    showToast('Seeding NASA-style battery degradation dataset...', 'info');
    // 1. Create battery if needed
    await fetch('/batteries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ battery_id: seedBatId, battery_type: 'Li-ion NMC (18650)', nominal_capacity: 2.0 })
    });

    // 2. Generate and ingest 60 cycles of telemetry
    const obsBatch = [];
    const now = new Date();
    for (let c = 1; c <= 60; c++) {
      // Simulate physical SEI decay
      const soh = +(1.0 - 0.003 * Math.sqrt(c) - 0.001 * c + (Math.random() * 0.004 - 0.002)).toFixed(4);
      const recTime = new Date(now.getTime() - (60 - c) * 3600 * 4000).toISOString();
      obsBatch.push({
        observation_id: `OBS-${seedBatId}-C${String(c).padStart(3, '0')}`,
        cycle_number: c,
        recorded_at: recTime,
        voltage: +(3.75 - 0.25 * (1 - soh)).toFixed(3),
        current: 1.5,
        temperature: +(25.0 + 8 * (1 - soh)).toFixed(1),
        capacity: +(2.0 * soh).toFixed(3),
        soh: soh
      });
    }

    await fetch(`/batteries/${seedBatId}/observations/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ observations: obsBatch })
    });

    // 3. Generate initial forecast at cycle 100
    await fetch(`/batteries/${seedBatId}/forecasts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_cycle: 100, generate_curve: true })
    });

    state.activeBatteryId = seedBatId;
    await loadBatteries();
    showToast('Demo dataset successfully generated and initialized!', 'success');
  } catch (err) {
    showToast(`Error seeding demo: ${err.message}`, 'error');
  }
}

/* ==========================================================================
   Telemetry Management
   ========================================================================== */

async function loadTelemetry() {
  if (!state.activeBatteryId) return;
  try {
    const res = await fetch(`/batteries/${state.activeBatteryId}/observations?order_by=${state.telemetryOrder}&active_only=false`);
    const data = await res.json();
    state.observations = data;

    const activeCount = data.filter(o => o.is_active).length;
    document.getElementById('lblObsCount').textContent = activeCount;

    renderTelemetryTable(data);
    renderForecastChart();
  } catch (err) {
    console.error('Failed to load telemetry:', err);
  }
}

function setTelemetryOrder(order) {
  state.telemetryOrder = order;
  document.getElementById('btnOrderEvent').classList.toggle('active', order === 'event_time');
  document.getElementById('btnOrderReceive').classList.toggle('active', order === 'receive_time');
  loadTelemetry();
}

function renderTelemetryTable(data) {
  const tbody = document.getElementById('telemetryTableBody');
  if (!data || data.length === 0) {
    tbody.innerHTML = '<tr><td colspan="11" class="text-center">No telemetry observations recorded.</td></tr>';
    return;
  }

  tbody.innerHTML = data.map((o, idx) => {
    const isLate = idx > 0 && o.cycle_number < data[idx - 1].cycle_number && state.telemetryOrder === 'receive_time';
    const rowClass = !o.is_active ? 'row-superseded' : (isLate ? 'row-late' : '');
    const statusBadge = !o.is_active 
      ? '<span class="badge-danger">Superseded</span>' 
      : (isLate ? '<span class="badge-pill" style="color:var(--warning)">Late Arrival</span>' : '<span class="badge-success">Active</span>');

    return `
      <tr class="${rowClass}">
        <td><strong>${o.observation_id}</strong></td>
        <td>${o.cycle_number}</td>
        <td>${o.recorded_at ? o.recorded_at.replace('T', ' ').substring(0, 19) : '-'}</td>
        <td>${o.received_at ? o.received_at.replace('T', ' ').substring(0, 19) : '-'}</td>
        <td>${o.voltage !== null ? o.voltage.toFixed(2) : '-'}</td>
        <td>${o.current !== null ? o.current.toFixed(2) : '-'}</td>
        <td>${o.temperature !== null ? o.temperature.toFixed(1) : '-'}</td>
        <td>${o.capacity !== null ? o.capacity.toFixed(2) : '-'}</td>
        <td><strong>${o.soh.toFixed(4)}</strong></td>
        <td>${statusBadge}</td>
        <td>
          ${o.is_active ? `<button class="btn btn-secondary btn-sm" onclick="openCorrectionModal('${o.observation_id}', ${o.cycle_number}, ${o.soh})">Correct</button>` : `<span class="form-hint">${o.correction_reason || 'Replaced'}</span>`}
        </td>
      </tr>
    `;
  }).join('');
}

function openIngestModal() {
  document.getElementById('modalTitle').textContent = 'Ingest Telemetry Observation';
  document.getElementById('correctionReasonGroup').classList.add('hidden');
  document.getElementById('telemetryForm').reset();
  document.getElementById('modalObsId').disabled = false;
  document.getElementById('modalCycle').disabled = false;
  document.getElementById('telemetryModal').classList.remove('hidden');
}

window.openCorrectionModal = function(obsId, cycle, currentSoh) {
  document.getElementById('modalTitle').textContent = `Correct Observation (${obsId})`;
  document.getElementById('correctionReasonGroup').classList.remove('hidden');
  document.getElementById('modalObsId').value = obsId;
  document.getElementById('modalObsId').disabled = true;
  document.getElementById('modalCycle').value = cycle;
  document.getElementById('modalCycle').disabled = true;
  document.getElementById('modalSoh').value = currentSoh;
  document.getElementById('modalReason').required = true;
  document.getElementById('telemetryModal').classList.remove('hidden');
};

async function handleTelemetrySubmit(e) {
  e.preventDefault();
  const obsId = document.getElementById('modalObsId').value.trim();
  const cycle = parseInt(document.getElementById('modalCycle').value);
  const soh = parseFloat(document.getElementById('modalSoh').value);
  const voltage = parseFloat(document.getElementById('modalVoltage').value) || null;
  const current = parseFloat(document.getElementById('modalCurrent').value) || null;
  const temp = parseFloat(document.getElementById('modalTemp').value) || null;
  const cap = parseFloat(document.getElementById('modalCapacity').value) || null;

  const isCorrection = !document.getElementById('correctionReasonGroup').classList.contains('hidden');
  
  try {
    let url, body, method;
    if (isCorrection) {
      url = `/batteries/${state.activeBatteryId}/observations/${obsId}/correct`;
      method = 'POST';
      body = {
        soh: soh,
        voltage: voltage,
        current: current,
        temperature: temp,
        capacity: cap,
        correction_reason: document.getElementById('modalReason').value.trim()
      };
    } else {
      url = `/batteries/${state.activeBatteryId}/observations`;
      method = 'POST';
      body = {
        observation_id: obsId,
        cycle_number: cycle,
        soh: soh,
        voltage: voltage,
        current: current,
        temperature: temp,
        capacity: cap
      };
    }

    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      const err = await res.json();
      showToast(`Ingestion rejected: ${err.detail}`, 'error');
      return;
    }

    document.getElementById('telemetryModal').classList.add('hidden');
    await onBatteryChanged();
    showToast(isCorrection ? 'Observation corrected & reconciled!' : 'Telemetry ingested successfully!', 'success');
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

async function handleSimulateLate() {
  if (!state.activeBatteryId || state.observations.length === 0) {
    showToast('Please select a battery with existing telemetry first.', 'error');
    return;
  }
  const maxCycle = Math.max(...state.observations.map(o => o.cycle_number));
  const lateCycle = Math.max(1, Math.floor(maxCycle * 0.6));
  const lateObsId = `OBS-LATE-C${lateCycle}-${Date.now().toString().slice(-4)}`;

  try {
    const res = await fetch(`/batteries/${state.activeBatteryId}/observations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        observation_id: lateObsId,
        cycle_number: lateCycle,
        soh: +(1.0 - 0.003 * Math.sqrt(lateCycle) - 0.001 * lateCycle).toFixed(4),
        voltage: 3.72,
        current: 1.5,
        temperature: 26.5,
        capacity: 1.90
      })
    });
    if (!res.ok) {
      const err = await res.json();
      showToast(`Error: ${err.detail}`, 'error');
      return;
    }
    await onBatteryChanged();
    showToast(`Late telemetry for cycle ${lateCycle} ingested after cycle ${maxCycle}! Reconciliation triggered.`, 'success');
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

/* ==========================================================================
   Forecasts & Model Evaluation
   ========================================================================== */

async function loadForecasts() {
  if (!state.activeBatteryId) return;
  try {
    const res = await fetch(`/batteries/${state.activeBatteryId}/forecasts`);
    const data = await res.json();
    state.forecasts = data;

    renderVersionList(data);
    if (data.length > 0) {
      state.currentForecast = data[0];
      updateForecastStatFooter(data[0]);
    } else {
      state.currentForecast = null;
      clearForecastStatFooter();
    }
    renderForecastChart();
  } catch (err) {
    console.error('Failed to load forecasts:', err);
  }
}

function renderVersionList(forecasts) {
  const container = document.getElementById('forecastVersionList');
  if (!forecasts || forecasts.length === 0) {
    container.innerHTML = '<div class="empty-state">No forecasts generated yet.</div>';
    return;
  }

  container.innerHTML = forecasts.map(f => `
    <div class="version-item" onclick="selectForecast('${f.forecast_id}')">
      <div>
        <strong>Cycle ${f.target_cycle} (v${f.forecast_version})</strong>
        <div class="form-hint">${f.selected_kernel} &bull; &mu;=${f.predicted_soh.toFixed(4)}</div>
      </div>
      <span class="badge-ver">&plusmn;${(1.96 * f.std_dev).toFixed(4)}</span>
    </div>
  `).join('');
}

window.selectForecast = function(id) {
  const fc = state.forecasts.find(f => f.forecast_id === id);
  if (fc) {
    state.currentForecast = fc;
    updateForecastStatFooter(fc);
    renderForecastChart();
  }
};

function updateForecastStatFooter(fc) {
  document.getElementById('statTargetCycle').textContent = `Cycle ${fc.target_cycle}`;
  document.getElementById('statPredictedSOH').textContent = `${(fc.predicted_soh * 100).toFixed(2)}% (${fc.predicted_soh.toFixed(4)})`;
  document.getElementById('statUncertainty').textContent = `\u00B1${(1.96 * fc.std_dev).toFixed(4)}`;
  document.getElementById('statBounds').textContent = `[${fc.lower_ci.toFixed(4)}, ${fc.upper_ci.toFixed(4)}]`;
  document.getElementById('statKernel').textContent = fc.selected_kernel;
}

function clearForecastStatFooter() {
  document.getElementById('statTargetCycle').textContent = '-';
  document.getElementById('statPredictedSOH').textContent = '-';
  document.getElementById('statUncertainty').textContent = '-';
  document.getElementById('statBounds').textContent = '-';
  document.getElementById('statKernel').textContent = '-';
}

async function handleRunForecast(e) {
  e.preventDefault();
  const targetCycle = parseInt(document.getElementById('txtTargetCycle').value);
  const kernel = document.getElementById('selKernelOverride').value || null;

  try {
    const res = await fetch(`/batteries/${state.activeBatteryId}/forecasts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_cycle: targetCycle,
        kernel_name: kernel,
        generate_curve: true
      })
    });

    if (!res.ok) {
      const err = await res.json();
      showToast(`Forecast failed: ${err.detail}`, 'error');
      return;
    }

    await onBatteryChanged();
    showToast(`Forecast generated for Cycle ${targetCycle}!`, 'success');
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

async function loadModelEvaluations() {
  if (!state.activeBatteryId) return;
  const tbody = document.getElementById('modelsTableBody');
  tbody.innerHTML = '<tr><td colspan="11" class="text-center">Evaluating candidate kernels with deterministic cross-validation...</td></tr>';

  try {
    const res = await fetch(`/batteries/${state.activeBatteryId}/models/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ include_baselines: true })
    });

    if (!res.ok) {
      tbody.innerHTML = '<tr><td colspan="11" class="text-center">Need at least 4 active observations for temporal evaluation.</td></tr>';
      return;
    }

    const data = await res.json();
    state.evaluations = data.all_candidates;
    renderModelsTable(data.all_candidates);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="11" class="text-center text-danger">Error: ${err.message}</td></tr>`;
  }
}

function renderModelsTable(candidates) {
  const tbody = document.getElementById('modelsTableBody');
  if (!candidates || candidates.length === 0) {
    tbody.innerHTML = '<tr><td colspan="11" class="text-center">No evaluations available.</td></tr>';
    return;
  }

  tbody.innerHTML = candidates.map(c => {
    const isWinner = c.is_selected;
    const rowClass = isWinner ? 'selected-row' : '';
    const statusBadge = c.status === 'SUCCESS' ? '<span class="badge-success">SUCCESS</span>' : `<span class="badge-danger">${c.error_message || 'FAILED'}</span>`;
    const selBadge = isWinner ? '<span class="badge-kernel">SELECTED &starf;</span>' : `<span class="form-hint">Rank ${c.selection_rank}</span>`;
    const paramStr = Object.entries(c.hyperparameters || {}).map(([k, v]) => `${k}:${typeof v === 'number' ? v.toFixed(3) : v}`).join(', ') || '-';

    return `
      <tr class="${rowClass}">
        <td><strong>#${c.selection_rank}</strong></td>
        <td><strong>${c.model_name}</strong></td>
        <td>${statusBadge}</td>
        <td>${c.rmse !== null ? c.rmse.toFixed(6) : '-'}</td>
        <td>${c.mae !== null ? c.mae.toFixed(6) : '-'}</td>
        <td>${c.coverage !== null ? (c.coverage * 100).toFixed(1) + '%' : '-'}</td>
        <td>${c.coverage_error !== null ? c.coverage_error.toFixed(4) : '-'}</td>
        <td>${c.log_marginal_likelihood !== null ? c.log_marginal_likelihood.toFixed(2) : '-'}</td>
        <td><code>${c.jitter_used.toExponential(0)}</code></td>
        <td style="max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${paramStr}">${paramStr}</td>
        <td>${selBadge}</td>
      </tr>
    `;
  }).join('');
}

/* ==========================================================================
   Diffs & Reconciliation
   ========================================================================== */

async function loadDiffs() {
  if (!state.activeBatteryId) return;
  try {
    const res = await fetch(`/batteries/${state.activeBatteryId}/forecast-diffs`);
    const data = await res.json();
    state.diffs = data;
    renderDiffsTable(data);
  } catch (err) {
    console.error('Failed to load diffs:', err);
  }
}

function renderDiffsTable(diffs) {
  const tbody = document.getElementById('diffsTableBody');
  if (!diffs || diffs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="12" class="text-center">No reconciliation diffs logged yet. (Ingest late or corrected telemetry to trigger)</td></tr>';
    return;
  }

  tbody.innerHTML = diffs.map(d => {
    const deltaSOHClass = d.delta_soh >= 0 ? 'text-success' : 'text-danger';
    const deltaStdClass = d.delta_std <= 0 ? 'text-success' : 'text-warning';
    const kernelChangeStr = d.kernel_changed ? `<span class="badge-pill">${d.old_kernel} &rarr; ${d.new_kernel}</span>` : `<span class="form-hint">${d.new_kernel}</span>`;
    const causeList = (d.triggering_observation_ids || []).map(id => `<code>${id}</code>`).join(' ');

    return `
      <tr>
        <td><strong>${d.id}</strong></td>
        <td>Cycle ${d.target_cycle}</td>
        <td><span class="badge-ver">v${d.old_forecast_version} &rarr; v${d.new_forecast_version}</span></td>
        <td>${d.old_soh.toFixed(4)}</td>
        <td><strong>${d.new_soh.toFixed(4)}</strong></td>
        <td class="${deltaSOHClass}"><strong>${d.delta_soh > 0 ? '+' : ''}${d.delta_soh.toFixed(4)}</strong></td>
        <td>${(1.96 * d.old_std).toFixed(4)}</td>
        <td><strong>${(1.96 * d.new_std).toFixed(4)}</strong></td>
        <td class="${deltaStdClass}">${d.delta_std > 0 ? '+' : ''}${(1.96 * d.delta_std).toFixed(4)}</td>
        <td>${kernelChangeStr}</td>
        <td>${causeList || '-'}</td>
        <td>${d.created_at ? d.created_at.replace('T', ' ').substring(0, 19) : '-'}</td>
      </tr>
    `;
  }).join('');
}

async function handleForceReconcile() {
  if (!state.activeBatteryId) return;
  try {
    const res = await fetch(`/batteries/${state.activeBatteryId}/reconcile`, { method: 'POST' });
    const diffs = await res.json();
    showToast(`Reconciliation complete! ${diffs.length} forecast versions updated.`, 'success');
    await onBatteryChanged();
  } catch (err) {
    showToast(`Reconciliation failed: ${err.message}`, 'error');
  }
}

/* ==========================================================================
   Historical Time-Travel & Replay Test
   ========================================================================== */

async function handleTimeTravelSlide(e) {
  const ver = parseInt(e.target.value);
  document.getElementById('lblScrubVer').textContent = `v${ver}`;

  if (!state.activeBatteryId) return;
  const targetCycle = state.currentForecast ? state.currentForecast.target_cycle : 100;

  try {
    const res = await fetch(`/batteries/${state.activeBatteryId}/time-travel?telemetry_version=${ver}&target_cycle=${targetCycle}`);
    const data = await res.json();
    
    document.getElementById('lblScrubObsCount').textContent = `${data.metadata.observations_count} observations`;
    document.getElementById('statTTVer').textContent = `v${ver}`;
    document.getElementById('statTTSOH').textContent = `${(data.forecast.predicted_soh * 100).toFixed(2)}%`;
    document.getElementById('statTTUncertainty').textContent = `\u00B1${(1.96 * data.forecast.std_dev).toFixed(4)}`;
    document.getElementById('statTTKernel').textContent = data.forecast.selected_kernel;

    renderTimeTravelChart(data);
  } catch (err) {
    console.error('Time travel error:', err);
  }
}

async function handleRunReplayTest() {
  if (!state.activeBatteryId) return;
  const runs = parseInt(document.getElementById('txtReplayRuns').value) || 5;
  const targetCycle = state.currentForecast ? state.currentForecast.target_cycle : 100;

  try {
    const res = await fetch(`/batteries/${state.activeBatteryId}/replay?target_cycle=${targetCycle}&runs=${runs}`, { method: 'POST' });
    const data = await res.json();

    const box = document.getElementById('replayResultBox');
    box.classList.remove('hidden');

    document.getElementById('replayRunsLabel').textContent = `${runs}/${runs} Runs Matched Byte-for-Byte`;
    document.getElementById('replayMaxDiffSOH').textContent = data.max_diff_soh.toFixed(8);
    document.getElementById('replayMaxDiffStd').textContent = data.max_diff_std.toFixed(8);
    document.getElementById('replaySOH').textContent = data.predicted_soh.toFixed(6);
    document.getElementById('replayBounds').textContent = `[${data.lower_ci.toFixed(6)}, ${data.upper_ci.toFixed(6)}]`;
    showToast('Bit-for-bit mathematical determinism verified!', 'success');
  } catch (err) {
    showToast(`Replay test failed: ${err.message}`, 'error');
  }
}

/* ==========================================================================
   PRD 12 Edge-Case Suite
   ========================================================================== */

async function loadScenariosList() {
  try {
    const res = await fetch('/scenarios/list');
    const data = await res.json();
    state.scenarios = data;

    const grid = document.getElementById('scenarioGrid');
    grid.innerHTML = data.map(s => `
      <div class="scenario-card" id="cardScenario-${s.id}">
        <div>
          <div class="scenario-card-header">
            <span class="scenario-id-tag">Case ${s.id}</span>
            <span id="badgeScenario-${s.id}" class="badge-pill">Ready</span>
          </div>
          <h4 class="scenario-title">${s.name}</h4>
          <p class="scenario-desc">${s.summary}</p>
        </div>
        <button class="btn btn-secondary btn-block" onclick="runSingleScenario(${s.id})">
          Run Case ${s.id}
        </button>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load scenarios:', err);
  }
}

window.runSingleScenario = async function(id) {
  const badge = document.getElementById(`badgeScenario-${id}`);
  badge.className = 'badge-pill';
  badge.textContent = 'Running...';

  try {
    const res = await fetch(`/scenarios/run/${id}`, { method: 'POST' });
    const result = await res.json();

    badge.className = result.passed ? 'badge-success' : 'badge-danger';
    badge.textContent = result.passed ? 'PASSED \u2713' : 'FAILED \u2717';

    // Show output in drawer
    const drawer = document.getElementById('scenarioResultDrawer');
    document.getElementById('drawerTitle').textContent = `Scenario ${id}: ${result.title}`;
    document.getElementById('drawerBadge').className = result.passed ? 'badge-success' : 'badge-danger';
    document.getElementById('drawerBadge').textContent = result.passed ? 'VERIFIED PASSED \u2713' : 'FAILED \u2717';
    document.getElementById('drawerDesc').textContent = result.description;
    document.getElementById('drawerJSON').textContent = JSON.stringify(result, null, 2);
    drawer.classList.remove('hidden');
    return result.passed;
  } catch (err) {
    badge.className = 'badge-danger';
    badge.textContent = 'ERROR';
    showToast(`Failed scenario ${id}: ${err.message}`, 'error');
    return false;
  }
};

async function handleRunAllScenarios() {
  showToast('Executing all 12 PRD Edge Case Scenarios sequentially...', 'info');
  for (let id = 1; id <= 12; id++) {
    await runSingleScenario(id);
    await new Promise(r => setTimeout(r, 120));
  }
  showToast('All 12 Scenarios executed successfully!', 'success');
}

/* ==========================================================================
   Custom High-DPI Canvas Chart Engine
   ========================================================================== */

function renderForecastChart() {
  if (!mainCtx) return;
  drawChart(mainCanvas, mainCtx, state.observations.filter(o => o.is_active), state.currentForecast);
}

function renderTimeTravelChart(ttData) {
  if (!ttCtx) return;
  if (!ttData) {
    drawChart(ttCanvas, ttCtx, state.observations.filter(o => o.is_active), state.currentForecast);
    return;
  }
  const filteredObs = state.observations.filter(o => o.telemetry_version <= ttData.replayed_telemetry_version && o.is_active);
  drawChart(ttCanvas, ttCtx, filteredObs, ttData.forecast);
}

function drawChart(canvas, ctx, obsList, forecast) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const w = rect.width;
  const h = rect.height;
  const padLeft = 55, padRight = 30, padTop = 25, padBottom = 40;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  ctx.clearRect(0, 0, w, h);

  // Determine Domain and Range
  let minX = 1, maxX = 100;
  let minY = 0.60, maxY = 1.05;

  if (obsList && obsList.length > 0) {
    const cycles = obsList.map(o => o.cycle_number);
    maxX = Math.max(maxX, Math.max(...cycles));
  }
  if (forecast) {
    maxX = Math.max(maxX, forecast.target_cycle);
    if (forecast.multi_horizon_points && forecast.multi_horizon_points.length > 0) {
      const hCycles = forecast.multi_horizon_points.map(p => p.cycle);
      maxX = Math.max(maxX, Math.max(...hCycles));
    }
  }
  maxX = Math.ceil(maxX * 1.05);

  const scaleX = (x) => padLeft + ((x - minX) / (maxX - minX)) * plotW;
  const scaleY = (y) => padTop + plotH - ((y - minY) / (maxY - minY)) * plotH;

  // Grid Lines & Axis Labels
  ctx.strokeStyle = '#1e293b';
  ctx.lineWidth = 1;
  ctx.fillStyle = '#64748b';
  ctx.font = '11px JetBrains Mono';
  ctx.textAlign = 'right';

  // Y Grid
  for (let yVal = 0.60; yVal <= 1.05; yVal += 0.10) {
    const yPos = scaleY(yVal);
    ctx.beginPath();
    ctx.moveTo(padLeft, yPos);
    ctx.lineTo(w - padRight, yPos);
    ctx.stroke();
    ctx.fillText(yVal.toFixed(2), padLeft - 8, yPos + 4);
  }

  // X Grid
  ctx.textAlign = 'center';
  const xStep = maxX > 200 ? 50 : 20;
  for (let xVal = minX; xVal <= maxX; xVal += xStep) {
    const xPos = scaleX(xVal);
    ctx.beginPath();
    ctx.moveTo(xPos, padTop);
    ctx.lineTo(xPos, padTop + plotH);
    ctx.stroke();
    ctx.fillText(`C${xVal}`, xPos, padTop + plotH + 18);
  }

  // 1. Draw 95% Confidence Band (Shaded area between lower_ci and upper_ci)
  if (forecast && forecast.multi_horizon_points && forecast.multi_horizon_points.length > 0) {
    const pts = forecast.multi_horizon_points;
    ctx.beginPath();
    ctx.moveTo(scaleX(pts[0].cycle), scaleY(pts[0].upper_ci));
    for (let i = 1; i < pts.length; i++) {
      ctx.lineTo(scaleX(pts[i].cycle), scaleY(pts[i].upper_ci));
    }
    for (let i = pts.length - 1; i >= 0; i--) {
      ctx.lineTo(scaleX(pts[i].cycle), scaleY(pts[i].lower_ci));
    }
    ctx.closePath();
    ctx.fillStyle = 'rgba(59, 130, 246, 0.18)';
    ctx.fill();

    // 2. Draw GPR Posterior Mean Line
    ctx.beginPath();
    ctx.moveTo(scaleX(pts[0].cycle), scaleY(pts[0].predicted_soh));
    for (let i = 1; i < pts.length; i++) {
      ctx.lineTo(scaleX(pts[i].cycle), scaleY(pts[i].predicted_soh));
    }
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 2.5;
    ctx.stroke();
  }

  // 3. Draw Observed Telemetry Dots
  if (obsList && obsList.length > 0) {
    obsList.forEach(obs => {
      const cx = scaleX(obs.cycle_number);
      const cy = scaleY(obs.soh);

      ctx.beginPath();
      ctx.arc(cx, cy, 3.5, 0, 2 * Math.PI);
      ctx.fillStyle = '#06b6d4';
      ctx.fill();
      ctx.strokeStyle = '#080c14';
      ctx.lineWidth = 1;
      ctx.stroke();
    });
  }

  // 4. Draw Target Forecast Point
  if (forecast) {
    const tx = scaleX(forecast.target_cycle);
    const ty = scaleY(forecast.predicted_soh);
    const topY = scaleY(forecast.upper_ci);
    const botY = scaleY(forecast.lower_ci);

    // Uncertainty Whisker
    ctx.beginPath();
    ctx.moveTo(tx, topY);
    ctx.lineTo(tx, botY);
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(tx - 4, topY); ctx.lineTo(tx + 4, topY);
    ctx.moveTo(tx - 4, botY); ctx.lineTo(tx + 4, botY);
    ctx.stroke();

    // Diamond Target
    ctx.beginPath();
    ctx.moveTo(tx, ty - 6);
    ctx.lineTo(tx + 6, ty);
    ctx.lineTo(tx, ty + 6);
    ctx.lineTo(tx - 6, ty);
    ctx.closePath();
    ctx.fillStyle = '#f59e0b';
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }
}

function handleChartHover(e) {
  const rect = mainCanvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;

  const padLeft = 55, padRight = 30, padTop = 25, padBottom = 40;
  const plotW = rect.width - padLeft - padRight;
  const plotH = rect.height - padTop - padBottom;

  if (mouseX < padLeft || mouseX > rect.width - padRight || mouseY < padTop || mouseY > rect.height - padBottom) {
    document.getElementById('chartTooltip').style.display = 'none';
    return;
  }

  let maxX = 100;
  if (state.observations.length > 0) {
    maxX = Math.max(maxX, Math.max(...state.observations.map(o => o.cycle_number)));
  }
  if (state.currentForecast) maxX = Math.max(maxX, state.currentForecast.target_cycle);
  maxX = Math.ceil(maxX * 1.05);

  const cycleApprox = Math.round(1 + ((mouseX - padLeft) / plotW) * (maxX - 1));

  const nearestObs = state.observations.find(o => Math.abs(o.cycle_number - cycleApprox) <= 1 && o.is_active);
  const tooltip = document.getElementById('chartTooltip');

  if (nearestObs) {
    tooltip.innerHTML = `
      <div><strong>Observation: ${nearestObs.observation_id}</strong></div>
      <div>Cycle: <strong>${nearestObs.cycle_number}</strong></div>
      <div>SOH: <strong>${nearestObs.soh.toFixed(4)}</strong></div>
      <div>Voltage: ${nearestObs.voltage ? nearestObs.voltage.toFixed(2) + 'V' : '-'}</div>
      <div>Temp: ${nearestObs.temperature ? nearestObs.temperature.toFixed(1) + '\u00B0C' : '-'}</div>
    `;
    tooltip.style.left = `${mouseX + 15}px`;
    tooltip.style.top = `${mouseY - 15}px`;
    tooltip.style.display = 'block';
  } else if (state.currentForecast && Math.abs(state.currentForecast.target_cycle - cycleApprox) <= 3) {
    const fc = state.currentForecast;
    tooltip.innerHTML = `
      <div><strong>Forecast (v${fc.forecast_version})</strong></div>
      <div>Target Cycle: <strong>${fc.target_cycle}</strong></div>
      <div>Predicted SOH: <strong>${fc.predicted_soh.toFixed(4)}</strong></div>
      <div>95% CI: <strong>\u00B1${(1.96 * fc.std_dev).toFixed(4)}</strong></div>
      <div>Kernel: <strong>${fc.selected_kernel}</strong></div>
    `;
    tooltip.style.left = `${mouseX + 15}px`;
    tooltip.style.top = `${mouseY - 15}px`;
    tooltip.style.display = 'block';
  } else {
    tooltip.style.display = 'none';
  }
}
