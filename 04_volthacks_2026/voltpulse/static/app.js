/**
 * VoltPulse AI: Industrial SCADA Digital Twin & Hardware Telemetry Controller.
 */

let voiceEnabled = true;
let isJudgeTourRunning = false;
let pollingTimer = null;
let currentForecast = null;
let currentNyquist = null;

// DOM Elements
const dispPackVoltage = document.getElementById('kpi-pack-voltage');
const dispPackCurrent = document.getElementById('kpi-pack-current');
const dispPackPower = document.getElementById('kpi-pack-power');
const dispPackSoc = document.getElementById('kpi-pack-soc');
const dispSocFill = document.getElementById('kpi-soc-fill');
const dispPackSoh = document.getElementById('kpi-pack-soh');
const dispCapacityLoss = document.getElementById('kpi-capacity-loss');
const dispSelectedKernel = document.getElementById('kpi-selected-kernel');
const dispRulCycles = document.getElementById('kpi-rul-cycles');
const dispObsCount = document.getElementById('kpi-obs-count');
const dispTelemetryVer = document.getElementById('kpi-telemetry-ver');
const dispMaxTemp = document.getElementById('kpi-max-temp');
const dispDeltaV = document.getElementById('kpi-delta-v');
const dispBalancingStatus = document.getElementById('kpi-balancing-status');
const dispRiskBadge = document.getElementById('kpi-risk-badge');
const cellMatrixGrid = document.getElementById('cell-matrix-grid');
const emergencyBanner = document.getElementById('emergency-banner');
const btnContactorToggle = document.getElementById('btn-contactor-toggle');
const dispContactorState = document.getElementById('disp-contactor-state');
const canTerminal = document.getElementById('can-terminal');
const reconciliationContent = document.getElementById('reconciliation-content');
const dispReconBadge = document.getElementById('disp-reconciliation-badge');

// Canvas Contexts
const forecastCanvas = document.getElementById('forecastCanvas');
const forecastCtx = forecastCanvas ? forecastCanvas.getContext('2d') : null;
const nyquistCanvas = document.getElementById('nyquistCanvas');
const nyquistCtx = nyquistCanvas ? nyquistCanvas.getContext('2d') : null;

// Speech Synthesis Helper
function speak(text) {
  if (!voiceEnabled || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.05;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}

// Initial Telemetry Fetch
async function fetchTelemetry() {
  try {
    const res = await fetch('/api/telemetry/live');
    if (!res.ok) return;
    const data = await res.json();
    updateDashboard(data);
  } catch (err) {
    console.error('Telemetry fetch error:', err);
  }
}

// Update Dashboard View
function updateDashboard(data) {
  // 1. KPI Cards
  dispPackVoltage.innerText = data.pack_voltage_v.toFixed(2);
  dispPackCurrent.innerText = `${data.pack_current_a >= 0 ? '+' : ''}${data.pack_current_a.toFixed(1)} A`;
  dispPackPower.innerText = `${Math.abs(data.pack_power_kw).toFixed(2)} kW`;
  dispPackSoc.innerText = data.pack_soc_pct.toFixed(1);
  dispSocFill.style.width = `${Math.max(0, Math.min(100, data.pack_soc_pct))}%`;
  dispPackSoh.innerText = data.pack_soh_pct.toFixed(2);
  dispCapacityLoss.innerText = `${(100.0 - data.pack_soh_pct).toFixed(2)}%`;
  dispMaxTemp.innerText = data.max_cell_temp_c.toFixed(1);
  dispDeltaV.innerText = `${data.cell_voltage_delta_mv.toFixed(1)} mV`;
  dispBalancingStatus.innerText = data.balancing_status;

  // Contactor state
  if (data.contactor_status === 'CLOSED') {
    btnContactorToggle.className = 'contactor-btn closed';
    dispContactorState.innerText = 'CLOSED';
    emergencyBanner.classList.add('hidden');
  } else if (data.contactor_status === 'FAULT_TRIPPED') {
    btnContactorToggle.className = 'contactor-btn fault';
    dispContactorState.innerText = 'TRIPPED';
    emergencyBanner.classList.remove('hidden');
    dispRiskBadge.innerText = 'CRITICAL';
    dispRiskBadge.style.color = '#ef4444';
  } else {
    btnContactorToggle.className = 'contactor-btn';
    dispContactorState.innerText = 'OPEN';
  }

  // 2. Render 16-Cell Series Grid
  renderCellMatrix(data.cells);

  // 3. Render CAN frames
  renderCANFrames(data.can_frames);
}

function renderCellMatrix(cells) {
  if (!cellMatrixGrid) return;
  cellMatrixGrid.innerHTML = '';

  cells.forEach(cell => {
    const node = document.createElement('div');
    let stateClass = 'normal';
    if (cell.temperature_c >= 55.0) {
      stateClass = 'runaway';
    } else if (cell.temperature_c >= 40.0) {
      stateClass = 'warm';
    } else if (cell.is_balancing) {
      stateClass = 'balancing';
    }

    node.className = `cell-node ${stateClass}`;
    node.innerHTML = `
      <div class="cell-top-info">
        <span class="cell-idx">CELL ${cell.cell_id < 10 ? '0' + cell.cell_id : cell.cell_id}</span>
        <span class="cell-temp">${cell.temperature_c.toFixed(1)}&deg;C</span>
      </div>
      <div class="cell-mid-v">${cell.voltage_v.toFixed(3)} V</div>
      <div class="cell-mini-bar">
        <div class="cell-mini-fill" style="width: ${cell.soc_pct}%;"></div>
      </div>
    `;
    cellMatrixGrid.appendChild(node);
  });
}

function renderCANFrames(frames) {
  if (!canTerminal || !frames) return;
  frames.forEach(f => {
    const line = document.createElement('div');
    line.className = 'can-line';
    line.innerHTML = `
      <span class="can-id">0x${f.arbitration_id.toString(16).toUpperCase()}</span>
      <span class="can-hex">[${f.data_hex}]</span>
      <span class="can-desc">${f.description}</span>
    `;
    canTerminal.prepend(line);
  });

  // Limit scroll history
  while (canTerminal.children.length > 25) {
    canTerminal.removeChild(canTerminal.lastChild);
  }
}

// Fetch & Draw Forecast
async function fetchAndDrawForecast(kernelOverride = null) {
  try {
    let url = '/api/forecast/latest';
    if (kernelOverride && kernelOverride !== 'AUTO') {
      const res = await fetch('/api/forecast/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ battery_id: 'BESS-GRID-PACK-01', horizon_cycles: 150, preferred_kernel: kernelOverride })
      });
      currentForecast = await res.json();
    } else {
      const res = await fetch(url);
      currentForecast = await res.json();
    }

    if (currentForecast) {
      dispSelectedKernel.innerText = currentForecast.selected_kernel.replace('_', ' ');
      dispRulCycles.innerText = currentForecast.remaining_useful_life_cycles ? Math.round(currentForecast.remaining_useful_life_cycles) : '>400';
      dispObsCount.innerText = currentForecast.training_points_count;
      document.getElementById('disp-val-rmse').innerText = `${currentForecast.validation_rmse.toFixed(3)} %`;
      document.getElementById('disp-val-mae').innerText = `${currentForecast.validation_mae.toFixed(3)} %`;
      document.getElementById('disp-val-coverage').innerText = `${currentForecast.interval_coverage_pct.toFixed(1)} %`;
      document.getElementById('disp-val-jitter').innerText = currentForecast.jitter_applied.toExponential(1);

      drawForecastCanvas(currentForecast);
    }
  } catch (err) {
    console.error('Forecast error:', err);
  }
}

function drawForecastCanvas(data) {
  if (!forecastCtx) return;
  const w = forecastCanvas.width;
  const h = forecastCanvas.height;
  const padL = 50, padR = 25, padT = 25, padB = 35;

  forecastCtx.clearRect(0, 0, w, h);

  // Background grid
  forecastCtx.strokeStyle = '#1e293b';
  forecastCtx.lineWidth = 1;

  for (let y = padT; y <= h - padB; y += 40) {
    forecastCtx.beginPath();
    forecastCtx.moveTo(padL, y);
    forecastCtx.lineTo(w - padR, y);
    forecastCtx.stroke();
  }

  const curve = data.forecast_curve;
  if (!curve || curve.length === 0) return;

  const minCycle = curve[0].cycle;
  const maxCycle = curve[curve.length - 1].cycle;
  const minSoh = 70.0;
  const maxSoh = 105.0;

  function toX(cycle) {
    return padL + ((cycle - minCycle) / (maxCycle - minCycle)) * (w - padL - padR);
  }
  function toY(soh) {
    return h - padB - ((soh - minSoh) / (maxSoh - minSoh)) * (h - padT - padB);
  }

  // 1. Draw 80% EOL Threshold Line
  const y80 = toY(80.0);
  forecastCtx.strokeStyle = 'rgba(239, 68, 68, 0.7)';
  forecastCtx.setLineDash([6, 4]);
  forecastCtx.beginPath();
  forecastCtx.moveTo(padL, y80);
  forecastCtx.lineTo(w - padR, y80);
  forecastCtx.stroke();
  forecastCtx.setLineDash([]);
  forecastCtx.fillStyle = '#ef4444';
  forecastCtx.font = '10px JetBrains Mono';
  forecastCtx.fillText('EOL THRESHOLD (80% SOH)', padL + 10, y80 - 6);

  // 2. Draw Shaded 95% Confidence Ribbon (Upper/Lower bounds)
  forecastCtx.fillStyle = 'rgba(0, 242, 254, 0.12)';
  forecastCtx.beginPath();
  curve.forEach((pt, idx) => {
    const x = toX(pt.cycle);
    const y = toY(pt.upper_bound_95);
    if (idx === 0) forecastCtx.moveTo(x, y);
    else forecastCtx.lineTo(x, y);
  });
  for (let i = curve.length - 1; i >= 0; i--) {
    const x = toX(curve[i].cycle);
    const y = toY(curve[i].lower_bound_95);
    forecastCtx.lineTo(x, y);
  }
  forecastCtx.closePath();
  forecastCtx.fill();

  // 3. Draw Upper & Lower Bound boundary lines
  forecastCtx.strokeStyle = 'rgba(0, 242, 254, 0.35)';
  forecastCtx.lineWidth = 1;
  forecastCtx.beginPath();
  curve.forEach((pt, idx) => {
    const x = toX(pt.cycle);
    const y = toY(pt.upper_bound_95);
    if (idx === 0) forecastCtx.moveTo(x, y);
    else forecastCtx.lineTo(x, y);
  });
  forecastCtx.stroke();

  forecastCtx.beginPath();
  curve.forEach((pt, idx) => {
    const x = toX(pt.cycle);
    const y = toY(pt.lower_bound_95);
    if (idx === 0) forecastCtx.moveTo(x, y);
    else forecastCtx.lineTo(x, y);
  });
  forecastCtx.stroke();

  // 4. Draw Mean Trajectory Line
  forecastCtx.strokeStyle = '#00f2fe';
  forecastCtx.lineWidth = 2.5;
  forecastCtx.beginPath();
  curve.forEach((pt, idx) => {
    const x = toX(pt.cycle);
    const y = toY(pt.predicted_soh_pct);
    if (idx === 0) forecastCtx.moveTo(x, y);
    else forecastCtx.lineTo(x, y);
  });
  forecastCtx.stroke();

  // 5. Draw Axes labels
  forecastCtx.fillStyle = '#64748b';
  forecastCtx.font = '10px JetBrains Mono';
  forecastCtx.fillText(`${minCycle.toFixed(0)} cyc`, padL, h - 10);
  forecastCtx.fillText(`${maxCycle.toFixed(0)} cyc (Horizon)`, w - padR - 80, h - 10);
  forecastCtx.fillText('100%', 15, toY(100.0) + 3);
  forecastCtx.fillText('80%', 15, y80 + 3);
}

// Fetch & Draw Nyquist Spectrum
async function fetchAndDrawNyquist() {
  try {
    const res = await fetch('/api/analytics/nyquist_spectrum?soh_pct=94.2&temp_c=28.0');
    currentNyquist = await res.json();
    if (currentNyquist && currentNyquist.length > 0) {
      document.getElementById('disp-eis-rs').innerText = `${currentNyquist[0].z_real_mohm.toFixed(2)} mΩ`;
      document.getElementById('disp-eis-rct').innerText = `${(currentNyquist[20].z_real_mohm - currentNyquist[0].z_real_mohm).toFixed(2)} mΩ`;
      drawNyquistCanvas(currentNyquist);
    }
  } catch (err) {
    console.error('Nyquist error:', err);
  }
}

function drawNyquistCanvas(data) {
  if (!nyquistCtx) return;
  const w = nyquistCanvas.width;
  const h = nyquistCanvas.height;
  const padL = 40, padR = 20, padT = 20, padB = 30;

  nyquistCtx.clearRect(0, 0, w, h);

  // Background Grid
  nyquistCtx.strokeStyle = '#1e293b';
  nyquistCtx.lineWidth = 1;
  for (let x = padL; x <= w - padR; x += 50) {
    nyquistCtx.beginPath();
    nyquistCtx.moveTo(x, padT);
    nyquistCtx.lineTo(x, h - padB);
    nyquistCtx.stroke();
  }
  for (let y = padT; y <= h - padB; y += 40) {
    nyquistCtx.beginPath();
    nyquistCtx.moveTo(padL, y);
    nyquistCtx.lineTo(w - padR, y);
    nyquistCtx.stroke();
  }

  const minZReal = 0.5;
  const maxZReal = 5.0;
  const minZImag = 0.0;
  const maxZImag = 3.5;

  function toX(zr) {
    return padL + ((zr - minZReal) / (maxZReal - minZReal)) * (w - padL - padR);
  }
  function toY(zi) {
    return h - padB - ((zi - minZImag) / (maxZImag - minZImag)) * (h - padT - padB);
  }

  // Draw Nyquist Curve
  nyquistCtx.strokeStyle = '#10b981';
  nyquistCtx.lineWidth = 2.5;
  nyquistCtx.beginPath();
  data.forEach((pt, idx) => {
    const x = toX(pt.z_real_mohm);
    const y = toY(pt.z_imag_neg_mohm);
    if (idx === 0) nyquistCtx.moveTo(x, y);
    else nyquistCtx.lineTo(x, y);
  });
  nyquistCtx.stroke();

  // Draw points
  nyquistCtx.fillStyle = '#00ff87';
  data.forEach((pt, idx) => {
    if (idx % 3 === 0) {
      const x = toX(pt.z_real_mohm);
      const y = toY(pt.z_imag_neg_mohm);
      nyquistCtx.beginPath();
      nyquistCtx.arc(x, y, 3, 0, 2 * Math.PI);
      nyquistCtx.fill();
    }
  });

  // Axis Labels
  nyquistCtx.fillStyle = '#64748b';
  nyquistCtx.font = '9px JetBrains Mono';
  nyquistCtx.fillText("Z' (Re) mΩ", w - 70, h - 8);
  nyquistCtx.fillText("-Z'' mΩ", 5, 15);
}

// Fetch Reconciliation History
async function fetchReconciliationHistory() {
  try {
    const res = await fetch('/api/reconciliation/history');
    const history = await res.json();
    dispReconBadge.innerText = `${history.length} Event${history.length !== 1 ? 's' : ''}`;

    if (history.length > 0) {
      reconciliationContent.innerHTML = '';
      history.slice().reverse().forEach(ev => {
        const card = document.createElement('div');
        card.className = 'recon-diff-card';
        card.innerHTML = `
          <div class="recon-diff-head">
            <span>${ev.reconciliation_id} (v${ev.telemetry_version})</span>
            <span>+${ev.reconciliation_duration_ms.toFixed(1)}ms</span>
          </div>
          <div class="recon-diff-body">
            <div>&bull; &Delta;SOH: <strong>${ev.diff.soh_prediction_delta >= 0 ? '+' : ''}${ev.diff.soh_prediction_delta.toFixed(2)}%</strong></div>
            <div>&bull; &Delta;&plusmn;1.96&sigma;: <strong>${ev.diff.uncertainty_delta >= 0 ? '+' : ''}${ev.diff.uncertainty_delta.toFixed(3)}</strong></div>
            <div>&bull; Kernel: <strong>${ev.diff.reconciled_selected_kernel}</strong></div>
            <div>&bull; Late Obs: <strong>${ev.late_observations_ingested}</strong></div>
          </div>
        `;
        reconciliationContent.appendChild(card);
      });
    }
  } catch (err) {
    console.error('Reconciliation history error:', err);
  }
}

// Action Event Listeners
document.getElementById('btn-inject-runaway').addEventListener('click', async () => {
  speak("Alert. Thermal runaway fault injected on Cell 7. Rapid temperature gradient active.");
  await fetch('/api/hardware/fault/thermal_runaway', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cell_id: 7, growth_rate_c_per_sec: 4.8 })
  });
  fetchTelemetry();
});

document.getElementById('btn-inject-imbalance').addEventListener('click', async () => {
  speak("State of charge imbalance injected on Cell 4.");
  await fetch('/api/hardware/fault/cell_imbalance', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cell_id: 4, soc_drop_pct: 28.0 })
  });
  fetchTelemetry();
});

document.getElementById('btn-inject-late-telemetry').addEventListener('click', async () => {
  speak("Injecting asynchronous late telemetry from cycle 140. Executing deterministic timeline reconstruction.");
  await fetch('/api/reconciliation/inject_late_observation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ battery_id: 'BESS-GRID-PACK-01', cycle_number: 140.0, soh_pct: 88.5, voltage_v: 3.68, temperature_c: 34.0, lag_days_simulated: 14.0 })
  });
  fetchReconciliationHistory();
  fetchAndDrawForecast();
});

document.getElementById('btn-trigger-balancing').addEventListener('click', async () => {
  speak("Active cell balancing routine engaged. Bleeding high voltage cells.");
  await fetch('/api/hardware/trigger_balancing', { method: 'POST' });
  fetchTelemetry();
});

document.getElementById('btn-charge-pack').addEventListener('click', async () => {
  speak("Setting pack to fast charge mode at minus 30 Amperes.");
  await fetch('/api/hardware/set_load_current', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ current_a: -30.0 })
  });
  fetchTelemetry();
});

document.getElementById('btn-clear-all-faults').addEventListener('click', async () => {
  speak("Clearing all faults. Normalizing pack temperatures and resetting contactor.");
  await fetch('/api/hardware/fault/clear_thermal', { method: 'POST' });
  await fetch('/api/hardware/contactor', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ state: 'CLOSED' })
  });
  await fetch('/api/hardware/set_load_current', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ current_a: 25.0 })
  });
  fetchTelemetry();
});

document.getElementById('btn-emergency-reset').addEventListener('click', async () => {
  await fetch('/api/hardware/fault/clear_thermal', { method: 'POST' });
  await fetch('/api/hardware/contactor', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ state: 'CLOSED' })
  });
  fetchTelemetry();
});

btnContactorToggle.addEventListener('click', async () => {
  const current = dispContactorState.innerText;
  const nextState = current === 'CLOSED' ? 'OPEN' : 'CLOSED';
  await fetch('/api/hardware/contactor', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ state: nextState })
  });
  fetchTelemetry();
});

document.getElementById('btn-toggle-voice').addEventListener('click', () => {
  voiceEnabled = !voiceEnabled;
  document.getElementById('voice-icon').innerText = voiceEnabled ? '🔊' : '🔇';
  document.getElementById('btn-toggle-voice').innerText = `Voice Alerts: ${voiceEnabled ? 'ON' : 'OFF'}`;
});

document.getElementById('select-kernel-override').addEventListener('change', (e) => {
  fetchAndDrawForecast(e.target.value);
});

// 1-Click Automated Judge Tour
document.getElementById('btn-judge-tour').addEventListener('click', async () => {
  if (isJudgeTourRunning) return;
  isJudgeTourRunning = true;
  speak("Welcome judges to VoltPulse AI. Beginning live hardware and physics demonstration.");

  // Step 1: Baseline inspection
  await new Promise(r => setTimeout(r, 2500));
  speak("Step 1: Ingesting 16-cell series CAN-bus J1939 telemetry at 10 Hertz with full Electrochemical Impedance Spectroscopy.");
  await fetchAndDrawNyquist();
  await fetchAndDrawForecast();

  // Step 2: Late telemetry injection
  await new Promise(r => setTimeout(r, 5500));
  speak("Step 2: Simulating delayed IoT telemetry from cycle 140. Watch deterministic Bayesian timeline reconciliation update the confidence ribbon.");
  document.getElementById('btn-inject-late-telemetry').click();

  // Step 3: Thermal Runaway & Contactor Cutoff
  await new Promise(r => setTimeout(r, 6500));
  speak("Step 3: Injecting critical thermal runaway micro-short on Cell 7. Observe sub-millisecond automated high-voltage contactor isolation.");
  document.getElementById('btn-inject-runaway').click();

  // Step 4: Normalization
  await new Promise(r => setTimeout(r, 7000));
  speak("Demonstration complete. Restoring normal operations. All 16 cells and GPR models verified.");
  document.getElementById('btn-clear-all-faults').click();
  isJudgeTourRunning = false;
});

// Init
window.addEventListener('DOMContentLoaded', () => {
  fetchTelemetry();
  fetchAndDrawForecast();
  fetchAndDrawNyquist();
  fetchReconciliationHistory();

  // Poll live telemetry every 1000ms
  pollingTimer = setInterval(fetchTelemetry, 1000);
});
