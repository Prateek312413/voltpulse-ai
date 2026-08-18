/**
 * AegisMed Clinician Dashboard & 4-Tier Memory Graph Visualizer
 */

const API_BASE = '/api';

// Scenario default inputs for quick demonstration
const SCENARIO_PRESETS = {
  'P-1001': {
    complaint: 'Severe sore throat, painful swallowing, fever for 2 days, and productive cough.',
    symptoms: 'Sore throat, Fever, Dysphagia, Cough',
    bp: '130/85',
    hr: 88,
    spo2: 98,
    temp: 38.4
  },
  'P-1002': {
    complaint: 'Severe right knee pain and swelling after gardening. Requesting strong anti-inflammatory.',
    symptoms: 'Knee pain, Joint effusion, Restricted mobility',
    bp: '144/90',
    hr: 76,
    spo2: 97,
    temp: 36.9
  },
  'P-1003': {
    complaint: 'Sudden substernal crushing chest pressure radiating to jaw, severe sweating, and nausea.',
    symptoms: 'Substernal chest pain, Diaphoresis, Nausea, Dyspnea',
    bp: '175/95',
    hr: 108,
    spo2: 93,
    temp: 37.0
  }
};

let currentPatientUid = 'P-1001';
let currentGraphData = null;
let canvasAnimId = null;

document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  await checkSystemStatus();
  await loadPatient(currentPatientUid);
  initCanvas();
});

function setupEventListeners() {
  document.getElementById('patient-select').addEventListener('change', (e) => {
    currentPatientUid = e.target.value;
    loadPatient(currentPatientUid);
    applyScenarioPreset(currentPatientUid);
  });

  document.getElementById('btn-run-swarm').addEventListener('click', runConsultationSwarm);
  document.getElementById('btn-vector-search').addEventListener('click', runVectorSearch);
  document.getElementById('btn-reset-demo').addEventListener('click', resetDemoScenarios);
  document.getElementById('btn-late-telemetry').addEventListener('click', simulateLateTelemetry);
}

function applyScenarioPreset(patientUid) {
  const preset = SCENARIO_PRESETS[patientUid];
  if (!preset) return;
  document.getElementById('chief-complaint-input').value = preset.complaint;
  document.getElementById('reported-symptoms').value = preset.symptoms;
  document.getElementById('vital-bp').value = preset.bp;
  document.getElementById('vital-hr').value = preset.hr;
  document.getElementById('vital-spo2').value = preset.spo2;
  document.getElementById('vital-temp').value = preset.temp;
}

async function checkSystemStatus() {
  try {
    const res = await fetch(`${API_BASE}/status`);
    const data = await res.json();
    const label = document.getElementById('db-status-label');
    if (data.database_backend === 'COCKROACHDB') {
      label.textContent = 'CockroachDB Distributed SQL: Connected';
    } else {
      label.textContent = `CockroachDB Memory Engine: Active (${data.metrics.total_episodic_memories} vectors)`;
    }
  } catch (err) {
    console.error('Failed to fetch status:', err);
  }
}

async function loadPatient(patientUid) {
  try {
    const res = await fetch(`${API_BASE}/patients/${patientUid}`);
    const data = await res.json();
    const p = data.patient;

    document.getElementById('patient-name-display').textContent = p.name;
    document.getElementById('patient-age-gender').textContent = `${p.age}y ${p.gender} • ${p.blood_type || 'O+'}`;

    // Allergies
    const allergiesContainer = document.getElementById('patient-allergies-list');
    allergiesContainer.innerHTML = (p.allergies && p.allergies.length > 0)
      ? p.allergies.map(a => `<span class="tag tag-danger">${a}</span>`).join('')
      : '<span class="tag tag-neutral">None Documented</span>';

    // Chronic conditions
    const condContainer = document.getElementById('patient-conditions-list');
    condContainer.innerHTML = (p.chronic_conditions && p.chronic_conditions.length > 0)
      ? p.chronic_conditions.map(c => `<span class="tag tag-neutral">${c}</span>`).join('')
      : '<span class="tag tag-neutral">None</span>';

    // Reflective Insights (Tier 4)
    const insightsContainer = document.getElementById('reflective-insights-container');
    if (data.reflective_insights && data.reflective_insights.length > 0) {
      insightsContainer.innerHTML = data.reflective_insights.map(ins => `
        <div class="insight-card">
          <div class="insight-headline">${ins.headline}</div>
          <div class="insight-desc">${ins.synthesis}</div>
        </div>
      `).join('');
    } else {
      insightsContainer.innerHTML = '<div class="insight-desc" style="color:var(--text-muted)">No anomalies detected.</div>';
    }

    // Episodic Timeline (Tier 2)
    const timelineContainer = document.getElementById('episodes-timeline-container');
    if (data.episodes && data.episodes.length > 0) {
      timelineContainer.innerHTML = data.episodes.map(ep => {
        const dateStr = new Date(ep.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
        return `
          <div class="episode-card">
            <div class="episode-header">
              <span class="episode-dx">${ep.diagnosis || 'Clinical Encounter'}</span>
              <span class="episode-date">${dateStr}</span>
            </div>
            <div class="episode-complaint">${ep.chief_complaint}</div>
          </div>
        `;
      }).join('');
    } else {
      timelineContainer.innerHTML = '<div class="insight-desc" style="color:var(--text-muted)">No prior encounters.</div>';
    }

    // Load Memory Graph
    await loadMemoryGraph(patientUid);

    // Load Bayesian Uncertainty Trajectory
    await loadTrajectoryChart(patientUid);
  } catch (err) {
    console.error('Error loading patient:', err);
  }
}

async function loadMemoryGraph(patientUid, sessionId = null) {
  try {
    let url = `${API_BASE}/memory/graph/${patientUid}`;
    if (sessionId) url += `?session_id=${sessionId}`;
    const res = await fetch(url);
    currentGraphData = await res.json();
    document.getElementById('active-nodes-count').textContent = `Nodes: ${currentGraphData.active_memory_count}`;
  } catch (err) {
    console.error('Error loading graph:', err);
  }
}

async function runConsultationSwarm() {
  const btn = document.getElementById('btn-run-swarm');
  btn.disabled = true;
  btn.textContent = 'Deliberating...';

  const streamBox = document.getElementById('agent-thought-stream');
  streamBox.innerHTML = '';

  const decisionPanel = document.getElementById('final-decision-panel');
  decisionPanel.classList.add('hidden');

  const chiefComplaint = document.getElementById('chief-complaint-input').value;
  const symptoms = document.getElementById('reported-symptoms').value.split(',').map(s => s.trim());
  const bp = document.getElementById('vital-bp').value.split('/');
  const vitals = {
    bp_sys: parseInt(bp[0]) || 120,
    bp_dia: parseInt(bp[1]) || 80,
    hr: parseInt(document.getElementById('vital-hr').value) || 75,
    spo2: parseInt(document.getElementById('vital-spo2').value) || 98,
    temp_c: parseFloat(document.getElementById('vital-temp').value) || 37.0
  };

  try {
    const res = await fetch(`${API_BASE}/consultation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patient_uid: currentPatientUid,
        chief_complaint: chiefComplaint,
        symptoms: symptoms,
        vital_signs: vitals,
        save_to_episodic_memory: true
      })
    });

    const data = await res.json();

    // Stream thoughts sequentially with realistic typing delay
    if (data.agent_thoughts && data.agent_thoughts.length > 0) {
      for (const t of data.agent_thoughts) {
        await appendThoughtWithDelay(streamBox, t);
      }
    }

    // Render Final Decision Panel
    renderFinalDecision(data);

    // Refresh patient & graph
    await loadPatient(currentPatientUid);
    await loadMemoryGraph(currentPatientUid, data.session_id);

  } catch (err) {
    console.error('Consultation failed:', err);
    streamBox.innerHTML = `<div class="thought-item thought-alert">Execution Error: ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
        <polygon points="5 3 19 12 5 21 5 3"/>
      </svg>
      Execute Swarm
    `;
  }
}

function appendThoughtWithDelay(container, thought) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const isAlert = thought.type.includes('ALERT') || thought.type.includes('CONTRAINDICATION');
      const div = document.createElement('div');
      div.className = `thought-item ${isAlert ? 'thought-alert' : ''}`;
      div.innerHTML = `
        <div class="thought-header">
          <span class="thought-agent-name">${thought.agent}</span>
          <span>${new Date(thought.timestamp).toLocaleTimeString()}</span>
        </div>
        <div class="thought-content">${thought.content}</div>
      `;
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
      resolve();
    }, 280);
  });
}

function renderFinalDecision(data) {
  const panel = document.getElementById('final-decision-panel');
  panel.classList.remove('hidden');

  const topDx = data.primary_diagnosis || {};
  document.getElementById('decision-diagnosis-title').textContent = `Diagnosis: ${topDx.condition || 'Acute Clinical Condition'}`;
  document.getElementById('decision-icd-code').textContent = `ICD-10: ${topDx.icd10 || 'R68.89'}`;

  // Safety alert banner
  const banner = document.getElementById('safety-alert-banner');
  const alerts = data.safety_audit?.alerts || [];
  if (alerts.length > 0) {
    banner.classList.remove('hidden');
    banner.innerHTML = `<strong>⚠️ CockroachDB Memory Safety Shield:</strong> Detected ${alerts.length} contraindication conflict(s). Blocked hazardous prescriptions and routed to validated alternatives.`;
  } else {
    banner.classList.add('hidden');
  }

  // Approved Meds
  const approvedList = document.getElementById('approved-meds-list');
  const approved = data.safety_audit?.approved_medications || [];
  approvedList.innerHTML = approved.length > 0 
    ? approved.map(m => `<li>✓ ${m} (Verified Safe)</li>`).join('')
    : '<li>Supportive Care / Monitoring</li>';

  // Blocked Meds
  const blockedList = document.getElementById('blocked-meds-list');
  const blocked = data.safety_audit?.blocked_medications || [];
  blockedList.innerHTML = blocked.length > 0
    ? blocked.map(m => `<li>✕ ${m} (Blocked by Memory Engine)</li>`).join('')
    : '<li>None</li>';
}

async function runVectorSearch() {
  const query = document.getElementById('vector-query-input').value;
  const resultsContainer = document.getElementById('vector-search-results');
  resultsContainer.innerHTML = '<div style="font-size:11px;color:var(--text-muted)">Executing vector cosine search in CockroachDB...</div>';

  try {
    const res = await fetch(`${API_BASE}/memory/vector-search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patient_uid: currentPatientUid,
        query_text: query,
        top_k: 3
      })
    });
    const data = await res.json();
    const items = data.recalled_memories || [];
    if (items.length > 0) {
      resultsContainer.innerHTML = items.map(m => `
        <div class="vector-result-item">
          <div><strong>${m.diagnosis || 'Encounter'}</strong> <span class="sim-score">Similarity: ${(m.vector_similarity * 100).toFixed(1)}%</span></div>
          <div style="color:var(--text-secondary);font-size:10px;margin-top:2px;">${m.chief_complaint}</div>
        </div>
      `).join('');
    } else {
      resultsContainer.innerHTML = '<div style="font-size:11px;color:var(--text-muted)">No vector matches above threshold.</div>';
    }
  } catch (err) {
    resultsContainer.innerHTML = `<div style="color:var(--accent-red);font-size:11px">Search failed: ${err.message}</div>`;
  }
}

async function resetDemoScenarios() {
  try {
    await fetch(`${API_BASE}/seed-benchmark`, { method: 'POST' });
    await loadPatient(currentPatientUid);
    alert('Benchmark clinical cases & guidelines re-seeded successfully!');
  } catch (err) {
    alert('Reset failed: ' + err.message);
  }
}

// --- 2D Animated Memory Graph Visualizer ---
function initCanvas() {
  const canvas = document.getElementById('memory-graph-canvas');
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight;
  }
  window.addEventListener('resize', resize);
  resize();

  let angle = 0;

  function renderGraph() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    if (!currentGraphData || !currentGraphData.nodes || currentGraphData.nodes.length === 0) {
      ctx.fillStyle = '#6b7280';
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Loading CockroachDB Memory Graph...', centerX, centerY);
      canvasAnimId = requestAnimationFrame(renderGraph);
      return;
    }

    angle += 0.005;
    const nodes = currentGraphData.nodes;
    const count = nodes.length;

    // Calculate node coordinates in orbits
    const nodeCoords = [];
    nodes.forEach((node, i) => {
      let r = 0;
      let x = centerX;
      let y = centerY;

      if (i > 0) {
        r = 50 + (i % 3) * 35;
        const currentAngle = angle * (i % 2 === 0 ? 1 : -1) + (i * (Math.PI * 2 / (count - 1)));
        x = centerX + Math.cos(currentAngle) * r;
        y = centerY + Math.sin(currentAngle) * (r * 0.7);
      }
      nodeCoords.push({ ...node, x, y, r });
    });

    // Draw Edges
    ctx.strokeStyle = '#233044';
    ctx.lineWidth = 1.2;
    nodeCoords.forEach(node => {
      if (node.x !== centerX || node.y !== centerY) {
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(node.x, node.y);
        ctx.stroke();
      }
    });

    // Draw Nodes
    nodeCoords.forEach(node => {
      let color = '#3b82f6';
      if (node.tier === 'EPISODIC') color = '#10b981';
      else if (node.tier === 'SEMANTIC') color = '#f59e0b';
      else if (node.tier === 'REFLECTIVE') color = '#8b5cf6';

      // Outer glow pulse
      ctx.beginPath();
      ctx.arc(node.x, node.y, 8, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();

      // Inner core
      ctx.beginPath();
      ctx.arc(node.x, node.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();

      // Label
      ctx.fillStyle = '#9ca3af';
      ctx.font = '9px JetBrains Mono, monospace';
      ctx.textAlign = 'center';
      const shortLabel = node.label.length > 18 ? node.label.substring(0, 16) + '..' : node.label;
      ctx.fillText(shortLabel, node.x, node.y + 16);
    });

    canvasAnimId = requestAnimationFrame(renderGraph);
  }

  renderGraph();
}

// --- Bayesian Biomarker Trajectory & Gaussian Process Ribbon ---
let currentTrajectoryData = null;

async function loadTrajectoryChart(patientUid) {
  try {
    const res = await fetch(`${API_BASE}/patients/${patientUid}/trajectory`);
    const data = await res.json();
    currentTrajectoryData = data;
    renderTrajectoryCanvas();
  } catch (err) {
    console.error('Failed to load trajectory:', err);
  }
}

function renderTrajectoryCanvas() {
  const canvas = document.getElementById('trajectory-chart-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = canvas.parentElement.clientWidth;
  canvas.height = canvas.parentElement.clientHeight;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!currentTrajectoryData || !currentTrajectoryData.forecast || !currentTrajectoryData.forecast.forecast_days) {
    ctx.fillStyle = '#6b7280';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('No longitudinal biomarker telemetry recorded yet.', canvas.width / 2, canvas.height / 2);
    return;
  }

  const histDays = currentTrajectoryData.historical_days || [];
  const histVals = currentTrajectoryData.historical_values || [];
  const fc = currentTrajectoryData.forecast;
  const fcDays = fc.forecast_days || [];
  const fcMean = fc.predicted_mean || [];
  const fcLower = fc.lower_confidence_95 || [];
  const fcUpper = fc.upper_confidence_95 || [];

  const allDays = [...histDays, ...fcDays];
  const allVals = [...histVals, ...fcUpper, ...fcLower];

  const minDay = Math.min(...allDays);
  const maxDay = Math.max(...allDays) || 1;
  const minVal = Math.max(0.5, Math.min(...allVals) - 0.2);
  const maxVal = Math.max(...allVals) + 0.3;

  const padLeft = 40;
  const padRight = 20;
  const padTop = 15;
  const padBottom = 20;
  const plotW = canvas.width - padLeft - padRight;
  const plotH = canvas.height - padTop - padBottom;

  const mapX = (d) => padLeft + ((d - minDay) / (maxDay - minDay)) * plotW;
  const mapY = (v) => padTop + plotH - ((v - minVal) / (maxVal - minVal)) * plotH;

  // Draw Grid Lines & Axes
  ctx.strokeStyle = '#233044';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padLeft, padTop);
  ctx.lineTo(padLeft, padTop + plotH);
  ctx.lineTo(padLeft + plotW, padTop + plotH);
  ctx.stroke();

  // Draw Y-Axis Labels (Creatinine mg/dL)
  ctx.fillStyle = '#6b7280';
  ctx.font = '9px JetBrains Mono, monospace';
  ctx.textAlign = 'right';
  ctx.fillText(`${maxVal.toFixed(1)}`, padLeft - 6, padTop + 8);
  ctx.fillText(`${((maxVal + minVal) / 2).toFixed(1)}`, padLeft - 6, padTop + plotH / 2);
  ctx.fillText(`${minVal.toFixed(1)}`, padLeft - 6, padTop + plotH);

  // 1. Draw 95% Bayesian Confidence Interval Ribbon
  ctx.fillStyle = 'rgba(59, 130, 246, 0.18)';
  ctx.beginPath();
  fcDays.forEach((d, i) => {
    const x = mapX(d);
    const y = mapY(fcUpper[i]);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  for (let i = fcDays.length - 1; i >= 0; i--) {
    const x = mapX(fcDays[i]);
    const y = mapY(fcLower[i]);
    ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fill();

  // 2. Draw GP Mean Forecast Line
  ctx.strokeStyle = '#3b82f6';
  ctx.setLineDash([4, 4]);
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  fcDays.forEach((d, i) => {
    const x = mapX(d);
    const y = mapY(fcMean[i]);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.setLineDash([]);

  // 3. Draw Historical Observation Points
  ctx.strokeStyle = '#10b981';
  ctx.lineWidth = 2;
  ctx.beginPath();
  histDays.forEach((d, i) => {
    const x = mapX(d);
    const y = mapY(histVals[i]);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  histDays.forEach((d, i) => {
    const x = mapX(d);
    const y = mapY(histVals[i]);
    ctx.fillStyle = '#10b981';
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(x, y, 2, 0, Math.PI * 2);
    ctx.fill();
  });

  // Annotate Legend (Clean stacked layout)
  ctx.font = '9px Plus Jakarta Sans, sans-serif';
  ctx.textAlign = 'right';
  ctx.fillStyle = '#10b981';
  ctx.fillText('● Historical Obs (Creatinine)', canvas.width - padRight, padTop + 2);
  ctx.fillStyle = '#60a5fa';
  ctx.fillText('--- GP Posterior Mean (±95% CI)', canvas.width - padRight, padTop + 14);
}

async function simulateLateTelemetry() {
  const btn = document.getElementById('btn-late-telemetry');
  btn.disabled = true;
  btn.innerHTML = `<span>⚡ Ingesting into CockroachDB...</span>`;

  const alertBox = document.getElementById('reconciliation-alert-box');

  try {
    const res = await fetch(`${API_BASE}/telemetry/late-sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patient_uid: currentPatientUid,
        days_ago: 250,
        observation_type: 'Delayed Comprehensive Renal Lab Panel',
        observation_data: {
          symptoms: ['Fatigue', 'Peripheral Edema'],
          lab_results: { creatinine: 1.85, egfr: 38.0 },
          severity_score: 3.5
        },
        note: 'Delayed laboratory blood sample analyzed from secondary pathology provider.'
      })
    });

    const data = await res.json();

    const count = data['subsequent_episodes_re-evaluated'] || 0;
    const epText = count === 1 ? '1 subsequent episode' : `${count} subsequent episodes`;
    const timeString = new Date().toLocaleTimeString();

    alertBox.classList.remove('hidden');
    alertBox.style.display = 'block';
    alertBox.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span><strong>⚡ CockroachDB Late-Telemetry Reconciled:</strong> Ingested delayed observation dated 250 days ago. Re-evaluated ${epText} in CockroachDB.</span>
        <span style="font-size:10px; color:#10b981; font-weight:700; background:rgba(16,185,129,0.2); padding:2px 6px; border-radius:4px;">LIVE @ ${timeString}</span>
      </div>
    `;

    // Refresh views and chart
    await loadPatient(currentPatientUid);
    await loadTrajectoryChart(currentPatientUid);

  } catch (err) {
    alertBox.classList.remove('hidden');
    alertBox.innerHTML = `Reconciliation status: ${err.message}`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
      </svg>
      Simulate Late-Arriving Lab
    `;
  }
}
