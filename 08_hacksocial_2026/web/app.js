/**
 * ResilioNet AI - Frontend Operations Application
 * Real-time Geospatial Radar, Live NLP Parser, Bipartite Matcher & Speech Alerts
 * Built for HackSocial 2026 Hackathon
 */

// Global State
let globalGraphData = null;
let selectedNode = null;
let ttsEnabled = true;
let isAudioSimulating = false;
let mapAnimationId = null;
let radarAngle = 0;

// Geospatial Canvas Mapping Extents (Metro Disaster Grid)
const GEO_BOUNDS = {
  minLat: 37.7100,
  maxLat: 37.8200,
  minLon: -122.4600,
  maxLon: -122.3700
};

// Preset Scenarios
const PRESET_SCENARIOS = [
  {
    text: "EMERGENCY: Water rising past 2nd floor window! Family of 5 trapped including 1 newborn baby and my 78yo mother with diabetes. Insulin ruined. Location: 1420 Riverfront Ave, Sector 4 (37.7749, -122.4194). Send swiftwater boat!",
    sender: "Elena Rostova",
    zone: "ZONE-COASTAL-4"
  },
  {
    text: "Elderly retirement center without power for 18 hours. 12 residents on oxygen concentrators. Generator fuel down to 5%. Urgent diesel delivery or battery banks needed at 880 Highland Ridge Road (37.7833, -122.4167).",
    sender: "Highland Ridge Care Lead",
    zone: "ZONE-HIGHLAND-2"
  },
  {
    text: "Roof collapsed during tremor! 3 construction workers trapped under concrete debris. One has severe arterial bleeding from leg fracture. Need heavy SAR + trauma tourniquet at 505 Warehouse Row (37.7650, -122.4250).",
    sender: "Site Foreman David",
    zone: "ZONE-INDUSTRIAL-1"
  },
  {
    text: "Community shelter has taken in 45 flood evacuees. Completely out of clean drinking water and baby formula. 8 toddlers crying and dehydrated. Need water tanker and infant nutrition at Westside Gym (37.7550, -122.4350).",
    sender: "Westside Shelter Director",
    zone: "ZONE-WESTSIDE-3"
  },
  {
    text: "Extreme cold (-8C). Homeless shelter overflow, 30 people shivering under highway overpass at 12th & Market St. High hypothermia risk. Need thermal emergency blankets and hot MRE rations (37.7720, -122.4150).",
    sender: "Outreach Worker Sam",
    zone: "ZONE-DOWNTOWN-1"
  }
];

// Initialize on DOM Load
document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  initCanvas();
  refreshAllData();

  // Polling loop for live telemetry updates every 3.5 seconds
  setInterval(() => {
    refreshAllData(false);
  }, 3500);
});

function initEventListeners() {
  // TTS Voice Toggle
  const ttsBtn = document.getElementById("ttsVoiceToggle");
  if (ttsBtn) {
    ttsBtn.addEventListener("click", () => {
      ttsEnabled = !ttsEnabled;
      ttsBtn.classList.toggle("muted", !ttsEnabled);
      document.getElementById("ttsIcon").textContent = ttsEnabled ? "\u{1F50A}" : "\u{1F507}";
      document.getElementById("ttsLabel").textContent = ttsEnabled ? "Voice Alerts: ON" : "Voice Alerts: OFF";
      showToast(ttsEnabled ? "Voice Speech Alerts Enabled" : "Voice Speech Alerts Muted");
    });
  }

  // Live NLP Debounce in Triage Input
  const sosInput = document.getElementById("sosInputText");
  let debounceTimeout = null;
  if (sosInput) {
    sosInput.addEventListener("input", (e) => {
      clearTimeout(debounceTimeout);
      debounceTimeout = setTimeout(() => {
        runLivePreviewTriage(e.target.value);
      }, 250);
    });
  }
}

// Navigation Tabs
function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
  });
  document.querySelectorAll(".tab-panel").forEach(panel => {
    panel.classList.toggle("active", panel.id === `panel-${tabId}`);
  });

  if (tabId === "map") {
    requestAnimationFrame(renderDisasterMap);
  }
}

// Data Fetching & Sync
async function refreshAllData(showToastAlert = false) {
  try {
    const [summaryRes, graphRes, zonesRes, directivesRes, depotsRes] = await Promise.all([
      fetch("/api/analytics/dashboard_summary").then(r => r.json()),
      fetch("/api/matching/bipartite_graph").then(r => r.json()),
      fetch("/api/analytics/zones").then(r => r.json()),
      fetch("/api/analytics/situational_assessment").then(r => r.json()),
      fetch("/api/resources/hubs").then(r => r.json())
    ]);

    updateHUD(summaryRes);
    globalGraphData = graphRes;
    renderLiveDistressStream(graphRes.nodes.demands);
    renderMatchedConvoys(graphRes.edges);
    renderDepots(depotsRes);
    renderDirectives(directivesRes);
    renderZones(zonesRes);
    renderDisasterMap();

    if (showToastAlert) {
      showToast("Operations Grid Data Refreshed", "success");
    }
  } catch (err) {
    console.error("Data refresh failed:", err);
  }
}

// Update Top KPI HUD
function updateHUD(summary) {
  document.getElementById("kpiCriticalCount").textContent = summary.critical_life_safety_count || 0;
  document.getElementById("kpiActiveSOS").textContent = summary.total_active_sos || 0;
  document.getElementById("kpiFulfillmentRate").textContent = `${summary.fulfillment_rate_pct || 0}%`;
  document.getElementById("kpiGiniIndex").textContent = Number(summary.gini_equity_index || 0).toFixed(3);
  document.getElementById("kpiSuppliesInStock").textContent = (summary.total_supplies_in_stock || 0).toLocaleString();

  const streamCountBadge = document.getElementById("streamCountBadge");
  if (streamCountBadge) streamCountBadge.textContent = `${summary.total_active_sos || 0} Signals`;

  const matchCountBadge = document.getElementById("matchCountBadge");
  if (matchCountBadge) matchCountBadge.textContent = `${summary.matched_and_dispatched || 0} Convoys`;
}

// Canvas Geospatial Radar Engine
function initCanvas() {
  const canvas = document.getElementById("disasterMapCanvas");
  if (!canvas) return;

  // Handle High DPI displays
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;

  canvas.addEventListener("click", handleCanvasClick);
  startRadarLoop();
}

function startRadarLoop() {
  function loop() {
    radarAngle = (radarAngle + 0.02) % (Math.PI * 2);
    renderDisasterMap();
    mapAnimationId = requestAnimationFrame(loop);
  }
  mapAnimationId = requestAnimationFrame(loop);
}

function projectToCanvas(lat, lon, width, height) {
  const x = ((lon - GEO_BOUNDS.minLon) / (GEO_BOUNDS.maxLon - GEO_BOUNDS.minLon)) * width;
  const y = height - (((lat - GEO_BOUNDS.minLat) / (GEO_BOUNDS.maxLat - GEO_BOUNDS.minLat)) * height);
  return { x: Math.max(20, Math.min(width - 20, x)), y: Math.max(20, Math.min(height - 20, y)) };
}

function projectFromCanvas(x, y, width, height) {
  const lon = GEO_BOUNDS.minLon + (x / width) * (GEO_BOUNDS.maxLon - GEO_BOUNDS.minLon);
  const lat = GEO_BOUNDS.minLat + ((height - y) / height) * (GEO_BOUNDS.maxLat - GEO_BOUNDS.minLat);
  return { lat, lon };
}

function renderDisasterMap() {
  const canvas = document.getElementById("disasterMapCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  // 1. Draw Grid Lines
  ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
  ctx.lineWidth = 1;
  const gridSize = 40;
  for (let x = 0; x < w; x += gridSize) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }
  for (let y = 0; y < h; y += gridSize) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  // 2. Draw Radar Sweep Line from center
  const cx = w / 2;
  const cy = h / 2;
  const radarRadius = Math.sqrt(cx * cx + cy * cy);
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.arc(cx, cy, radarRadius, radarAngle, radarAngle + 0.35);
  ctx.closePath();
  const grad = ctx.createRadialGradient(cx, cy, 10, cx, cy, radarRadius);
  grad.addColorStop(0, "rgba(0, 229, 255, 0.15)");
  grad.addColorStop(1, "rgba(0, 229, 255, 0.0)");
  ctx.fillStyle = grad;
  ctx.fill();
  ctx.restore();

  if (!globalGraphData) return;

  const { demands, hubs } = globalGraphData.nodes;
  const edges = globalGraphData.edges;

  // 3. Draw Allocation Edges (Dispatched Aid Convoys)
  edges.forEach((edge, i) => {
    const hub = hubs.find(h => h.id === edge.source_hub_id);
    const dem = demands.find(d => d.id === edge.target_request_id);
    if (!hub || !dem) return;

    const p1 = projectToCanvas(hub.lat, hub.lon, w, h);
    const p2 = projectToCanvas(dem.lat, dem.lon, w, h);

    ctx.save();
    ctx.strokeStyle = "rgba(0, 229, 255, 0.4)";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();

    // Moving Convoy Dot animation along the vector
    const animOffset = (Date.now() / 2000 + (i * 0.2)) % 1.0;
    const dotX = p1.x + (p2.x - p1.x) * animOffset;
    const dotY = p1.y + (p2.y - p1.y) * animOffset;

    ctx.fillStyle = "#00e5ff";
    ctx.beginPath();
    ctx.arc(dotX, dotY, 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  });

  // 4. Draw Supply Hubs
  hubs.forEach(hub => {
    const p = projectToCanvas(hub.lat, hub.lon, w, h);
    ctx.save();

    // Hub Outer Ring
    ctx.strokeStyle = hub.status === "OFFLINE" ? "#ef4444" : "#3b82f6";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 14, 0, Math.PI * 2);
    ctx.stroke();

    // Hub Center
    ctx.fillStyle = hub.status === "OFFLINE" ? "rgba(239, 68, 68, 0.3)" : "rgba(59, 130, 246, 0.4)";
    ctx.fill();

    // Hub Icon symbol
    ctx.fillStyle = "#ffffff";
    ctx.font = "10px monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("H", p.x, p.y);

    // Label
    ctx.font = "10px sans-serif";
    ctx.fillStyle = "#93c5fd";
    ctx.fillText(hub.name.split(" ")[0], p.x, p.y + 22);

    ctx.restore();
  });

  // 5. Draw SOS Beacons
  const now = Date.now();
  demands.forEach(dem => {
    const p = projectToCanvas(dem.lat, dem.lon, w, h);
    const isCritical = dem.urgency >= 8.5;
    const isUrgent = dem.urgency >= 6.5 && dem.urgency < 8.5;
    const color = isCritical ? "#ff3366" : (isUrgent ? "#ffaa00" : "#00e5ff");

    ctx.save();

    // Pulsing Beacon Waves
    const pulsePhase = (now / 1000 + (dem.urgency * 0.3)) % 1.5;
    const pulseRadius = 6 + pulsePhase * 16;
    const pulseAlpha = Math.max(0, 1 - (pulsePhase / 1.5));

    ctx.strokeStyle = color;
    ctx.globalAlpha = pulseAlpha;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(p.x, p.y, pulseRadius, 0, Math.PI * 2);
    ctx.stroke();

    // Solid Node Core
    ctx.globalAlpha = 1.0;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
    ctx.fill();

    // Selected indicator ring
    if (selectedNode && selectedNode.id === dem.id) {
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 10, 0, Math.PI * 2);
      ctx.stroke();
    }

    ctx.restore();
  });
}

function handleCanvasClick(e) {
  const canvas = document.getElementById("disasterMapCanvas");
  const rect = canvas.getBoundingClientRect();
  const clickX = (e.clientX - rect.left) * (canvas.width / rect.width);
  const clickY = (e.clientY - rect.top) * (canvas.height / rect.height);

  if (!globalGraphData) return;

  const { demands, hubs } = globalGraphData.nodes;
  let clickedTarget = null;
  let minDist = 20;

  // Check Demands
  demands.forEach(dem => {
    const p = projectToCanvas(dem.lat, dem.lon, canvas.width, canvas.height);
    const dist = Math.hypot(clickX - p.x, clickY - p.y);
    if (dist < minDist) {
      minDist = dist;
      clickedTarget = { type: "DEMAND", data: dem };
    }
  });

  // Check Hubs
  hubs.forEach(hub => {
    const p = projectToCanvas(hub.lat, hub.lon, canvas.width, canvas.height);
    const dist = Math.hypot(clickX - p.x, clickY - p.y);
    if (dist < minDist) {
      minDist = dist;
      clickedTarget = { type: "HUB", data: hub };
    }
  });

  if (clickedTarget) {
    selectedNode = clickedTarget.data;
    inspectNode(clickedTarget);
  }
}

function resetMapView() {
  selectedNode = null;
  const inspector = document.getElementById("inspectorContent");
  if (inspector) {
    inspector.innerHTML = `
      <div class="inspector-placeholder">
        <div class="placeholder-icon">&#128065;</div>
        <p>Click any SOS beacon or Supply Depot on the radar to inspect live metadata, triage diagnostics, and route allocations.</p>
      </div>
    `;
  }
  showToast("Grid map centered");
}

function inspectNode(target) {
  const inspector = document.getElementById("inspectorContent");
  if (!inspector) return;

  if (target.type === "DEMAND") {
    const d = target.data;
    const isCritical = d.urgency >= 8.5;
    const edge = globalGraphData ? globalGraphData.edges.find(e => e.target_request_id === d.id) : null;

    inspector.innerHTML = `
      <div class="stream-header mb-2">
        <span class="stream-id">&#128680; ${d.id}</span>
        <span class="stream-urgency ${isCritical ? 'urgency-high' : 'urgency-med'}">URGENCY ${d.urgency}/10</span>
      </div>
      <p><strong>Requester:</strong> ${d.name}</p>
      <p><strong>Category:</strong> <span class="badge badge-accent">${d.category}</span></p>
      <p><strong>Headcount:</strong> ${d.headcount} individual(s)</p>
      <p><strong>Zone:</strong> ${d.zone_id}</p>
      <p><strong>Coordinates:</strong> ${d.lat.toFixed(4)}, ${d.lon.toFixed(4)}</p>
      ${edge ? `
        <div class="mt-3" style="background: rgba(0,229,255,0.08); padding: 8px; border-radius: 4px; border: 1px solid #00e5ff;">
          <strong>⚡ Assigned Aid Convoy:</strong> ${edge.match_id} from ${edge.source_hub_id}<br>
          <strong>Distance:</strong> ${edge.distance_km} km &bull; <strong>ETA:</strong> ${edge.transit_minutes} mins<br>
          <strong>Status:</strong> <span class="badge">${edge.status}</span>
        </div>
      ` : '<div class="mt-2 text-danger">⚠️ Unserviced: Awaiting Depot Supply Dispatch</div>'}
    `;
  } else if (target.type === "HUB") {
    const h = target.data;
    inspector.innerHTML = `
      <div class="stream-header mb-2">
        <span class="stream-id">&#127973; ${h.id}</span>
        <span class="badge ${h.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}">${h.status}</span>
      </div>
      <p><strong>Depot Name:</strong> ${h.name}</p>
      <p><strong>Available Vehicles:</strong> ${h.available_vehicles} fleets</p>
      <p><strong>Total Inventory Units:</strong> ${h.stock_count}</p>
      <p><strong>Location:</strong> ${h.lat.toFixed(4)}, ${h.lon.toFixed(4)}</p>
    `;
  }
}

// Live Stream List Render
function renderLiveDistressStream(demands) {
  const container = document.getElementById("mapLiveStreamList");
  if (!container) return;

  const sorted = [...demands].sort((a, b) => b.urgency - a.urgency);
  container.innerHTML = sorted.map(d => {
    const isCritical = d.urgency >= 8.5;
    const isUrgent = d.urgency >= 6.5 && d.urgency < 8.5;
    const urgencyClass = isCritical ? 'urgency-high' : (isUrgent ? 'urgency-med' : 'urgency-low');

    return `
      <div class="stream-item" onclick="selectDemandById('${d.id}')">
        <div class="stream-header">
          <span class="stream-id">${d.id}</span>
          <span class="stream-urgency ${urgencyClass}">${d.urgency}/10</span>
        </div>
        <div class="stream-text">[${d.category}] ${d.name} &bull; ${d.headcount} people in ${d.zone_id}</div>
      </div>
    `;
  }).join("");
}

function selectDemandById(demandId) {
  if (!globalGraphData) return;
  const target = globalGraphData.nodes.demands.find(d => d.id === demandId);
  if (target) {
    selectedNode = target;
    inspectNode({ type: "DEMAND", data: target });
  }
}

// Live NLP Triage Preview Engine
async function runLivePreviewTriage(text) {
  if (!text || text.trim().length < 3) {
    resetTriagePreview();
    return;
  }

  try {
    const res = await fetch(`/api/triage/parse_preview?message_text=${encodeURIComponent(text)}`, {
      method: "POST"
    }).then(r => r.json());

    document.getElementById("previewUrgencyScore").textContent = `${res.urgency_score.toFixed(1)} / 10.0`;
    document.getElementById("previewUrgencyBar").style.width = `${(res.urgency_score / 10.0) * 100}%`;
    document.getElementById("previewConfidenceBadge").textContent = `CONFIDENCE ${(res.confidence * 100).toFixed(0)}%`;
    document.getElementById("previewPrimaryCat").textContent = res.primary_category;

    document.getElementById("previewHeadcount").textContent = res.entities.headcount;
    document.getElementById("previewInfants").textContent = res.entities.vulnerable_infants;
    document.getElementById("previewElderly").textContent = res.entities.vulnerable_elderly;
    document.getElementById("previewStressScore").textContent = res.sentiment_stress_score.toFixed(2);

    const medEl = document.getElementById("previewMedicalList");
    medEl.textContent = res.entities.medical_conditions.length > 0 ? res.entities.medical_conditions.join(", ") : "None Detected";

    const supEl = document.getElementById("previewSuppliesList");
    supEl.textContent = res.entities.specific_supplies_needed.length > 0 ? res.entities.specific_supplies_needed.join(", ") : "Standard Aid";

    document.getElementById("previewKitType").textContent = res.recommended_kit_type;
    document.getElementById("previewActionableSummary").textContent = res.actionable_summary;

    // Speech Alert Trigger if High Urgency and not typing too fast
    if (ttsEnabled && res.urgency_score >= 8.5) {
      triggerSpeechAlert(`High urgency distress classified: ${res.primary_category}`);
    }
  } catch (err) {
    console.error("Preview triage error:", err);
  }
}

function resetTriagePreview() {
  document.getElementById("previewUrgencyScore").textContent = "0.0 / 10.0";
  document.getElementById("previewUrgencyBar").style.width = "0%";
  document.getElementById("previewConfidenceBadge").textContent = "CONFIDENCE 0%";
  document.getElementById("previewPrimaryCat").textContent = "AWAITING INPUT";
  document.getElementById("previewHeadcount").textContent = "0";
  document.getElementById("previewInfants").textContent = "0";
  document.getElementById("previewElderly").textContent = "0";
  document.getElementById("previewStressScore").textContent = "0.00";
  document.getElementById("previewMedicalList").textContent = "None";
  document.getElementById("previewSuppliesList").textContent = "None";
  document.getElementById("previewKitType").textContent = "KIT-STANDARD";
  document.getElementById("previewActionableSummary").textContent = "Start typing an SOS distress message to see real-time NLP parsing.";
}

// Preset Scenario Loader
function loadPresetSOS(index) {
  const scenario = PRESET_SCENARIOS[index];
  if (!scenario) return;

  document.getElementById("sosInputText").value = scenario.text;
  document.getElementById("sosSenderName").value = scenario.sender;
  document.getElementById("sosZoneSelect").value = scenario.zone;
  runLivePreviewTriage(scenario.text);
}

// Submit Live SOS
async function submitLiveSOS() {
  const text = document.getElementById("sosInputText").value;
  const sender = document.getElementById("sosSenderName").value || "Anonymous Citizen";
  const zone = document.getElementById("sosZoneSelect").value || "ZONE-DEFAULT";

  if (!text || text.trim().length < 5) {
    showToast("Please enter a valid SOS message", "danger");
    return;
  }

  try {
    const btn = document.getElementById("btnSubmitSOS");
    btn.disabled = true;
    btn.innerHTML = `<span class="icon">&#8987;</span> Ingesting to Grid...`;

    const res = await fetch("/api/triage/submit_sos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message_text: text,
        sender_name: sender,
        zone_id: zone
      })
    }).then(r => r.json());

    showToast(`SOS Ingested: Priority ${res.urgency_score}/10 [${res.primary_category}]`, "success");

    if (ttsEnabled) {
      triggerSpeechAlert(`SOS ingested for ${sender}. Urgency ${res.urgency_score}. Recommended kit ${res.recommended_kit_type}`);
    }

    // Clear form
    document.getElementById("sosInputText").value = "";
    document.getElementById("sosSenderName").value = "";
    resetTriagePreview();

    // Refresh telemetry & switch to map
    await refreshAllData(false);
    switchTab("map");
  } catch (err) {
    showToast("SOS submission failed", "danger");
    console.error(err);
  } finally {
    const btn = document.getElementById("btnSubmitSOS");
    btn.disabled = false;
    btn.innerHTML = `<span class="icon">&#128680;</span> Broadcast SOS to Network`;
  }
}

// Audio Mic Simulator
function simulateVoiceMicRecording() {
  if (isAudioSimulating) return;
  isAudioSimulating = true;

  showToast("🎙️ Listening to acoustic distress audio input...", "info");
  const randomScenario = PRESET_SCENARIOS[Math.floor(Math.random() * PRESET_SCENARIOS.length)];

  let currentText = "";
  const words = randomScenario.text.split(" ");
  let wordIdx = 0;

  const interval = setInterval(() => {
    if (wordIdx < words.length) {
      currentText += (wordIdx > 0 ? " " : "") + words[wordIdx];
      document.getElementById("sosInputText").value = currentText;
      runLivePreviewTriage(currentText);
      wordIdx++;
    } else {
      clearInterval(interval);
      isAudioSimulating = false;
      document.getElementById("sosSenderName").value = randomScenario.sender;
      document.getElementById("sosZoneSelect").value = randomScenario.zone;
      showToast("🎙️ Audio transcript ingestion complete", "success");
    }
  }, 120);
}

// Speech Alert Synthesizer
let lastSpokenText = "";
let lastSpokenTime = 0;
function triggerSpeechAlert(text) {
  if (!ttsEnabled || !window.speechSynthesis) return;
  const now = Date.now();
  if (text === lastSpokenText && now - lastSpokenTime < 5000) return; // Prevent loop

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.05;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
  lastSpokenText = text;
  lastSpokenTime = now;
}

// Optimizer & Sliders
function updateOptimizerSliders() {
  const fw = document.getElementById("fairnessWeightSlider").value;
  const dp = document.getElementById("distancePenaltySlider").value;
  document.getElementById("valFairnessWeight").textContent = Number(fw).toFixed(2);
  document.getElementById("valDistancePenalty").textContent = Number(dp).toFixed(2);
}

async function reoptimizeAllocations() {
  const fw = parseFloat(document.getElementById("fairnessWeightSlider").value);
  const dp = parseFloat(document.getElementById("distancePenaltySlider").value);

  try {
    const plan = await fetch("/api/matching/reoptimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        fairness_weight: fw,
        distance_penalty_weight: dp
      })
    }).then(r => r.json());

    document.getElementById("optTotalDemands").textContent = plan.total_demands;
    document.getElementById("optMatchedDemands").textContent = plan.matched_demands;
    document.getElementById("optUnservicedDemands").textContent = plan.unfulfilled_demands;
    document.getElementById("optFulfillmentRate").textContent = `${plan.fulfillment_rate_percent}%`;
    document.getElementById("optGiniScore").textContent = plan.gini_equity_index.toFixed(3);

    const bList = document.getElementById("bottleneckList");
    if (bList) {
      bList.innerHTML = plan.critical_bottlenecks.map(b => `<li>${b}</li>`).join("") || "<li>No immediate supply deficits detected.</li>";
    }

    renderMatchedConvoys(plan.matches);
    await refreshAllData(false);
    showToast("Optimization Complete: Solved Bipartite Resource Network", "success");
  } catch (err) {
    showToast("Optimization failed", "danger");
    console.error(err);
  }
}

// Matched Convoys Render
function renderMatchedConvoys(matches) {
  const container = document.getElementById("matchedConvoysList");
  if (!container) return;

  container.innerHTML = matches.map(m => {
    const statusClass = m.dispatch_status === 'DELIVERED' ? 'status-delivered' : (m.dispatch_status === 'DISPATCHED' ? 'status-dispatched' : 'status-pending');
    const itemsStr = Object.entries(m.items_allocated || {}).map(([k, v]) => `${v}x ${k.replace(/_/g, " ")}`).join(", ");

    return `
      <div class="match-card">
        <div class="match-card-header">
          <span class="match-title">&#128666; ${m.match_id} &rarr; ${m.request_id}</span>
          <span class="match-status-badge ${statusClass}">${m.dispatch_status}</span>
        </div>
        <div class="match-details-grid">
          <div><strong>Source Hub:</strong> ${m.hub_name}</div>
          <div><strong>Distance:</strong> ${m.distance_km} km</div>
          <div><strong>Estimated Transit:</strong> ${m.estimated_transit_minutes} mins</div>
          <div><strong>Priority Score:</strong> ${m.urgency_weighted_score}</div>
        </div>
        <div class="mb-2 text-sm">
          <strong>Cargo Supplies:</strong> <span class="text-secondary">${itemsStr || 'Standard Relief Aid'}</span>
        </div>
        <div class="btn-group-actions">
          ${m.dispatch_status === 'PENDING_DISPATCH' ? `
            <button class="btn btn-sm btn-primary" onclick="advanceDispatchStatus('${m.match_id}', 'DISPATCHED')">
              &#128663; Dispatch Aid Convoy
            </button>
          ` : (m.dispatch_status === 'DISPATCHED' ? `
            <button class="btn btn-sm btn-success" onclick="advanceDispatchStatus('${m.match_id}', 'DELIVERED')">
              &#9989; Confirm Field Delivery
            </button>
          ` : '<span class="text-success text-sm">&#10004; Delivery Confirmed & Audited</span>')}
        </div>
      </div>
    `;
  }).join("");
}

async function advanceDispatchStatus(matchId, newStatus) {
  try {
    await fetch(`/api/matching/dispatch/${matchId}?new_status=${newStatus}`, { method: "POST" });
    showToast(`Convoy ${matchId} marked as ${newStatus}`, "success");
    await refreshAllData(false);
  } catch (err) {
    showToast("Status update failed", "danger");
  }
}

// Depots Render
function renderDepots(hubs) {
  const container = document.getElementById("depotsGridContainer");
  if (!container) return;

  container.innerHTML = hubs.map(hub => {
    const isOffline = hub.operational_status === "OFFLINE";
    const inventoryRows = Object.entries(hub.inventory || {}).map(([k, item]) => `
      <tr>
        <td>${item.name}</td>
        <td><strong>${item.quantity}</strong> ${item.unit}</td>
        <td><span class="badge ${item.is_perishable ? 'badge-danger' : ''}">${item.is_perishable ? 'PERISHABLE' : 'STABLE'}</span></td>
      </tr>
    `).join("");

    return `
      <div class="depot-card" style="${isOffline ? 'opacity: 0.6; border-color: #ef4444;' : ''}">
        <div class="depot-header">
          <div>
            <div class="depot-name">&#127973; ${hub.name}</div>
            <div class="text-sm text-secondary">${hub.hub_id} &bull; ${hub.available_vehicles} Vehicles Available</div>
          </div>
          <span class="badge ${isOffline ? 'badge-danger' : 'badge-success'}">${hub.operational_status}</span>
        </div>

        <table class="inventory-table">
          <thead>
            <tr>
              <th>Item</th>
              <th>Qty</th>
              <th>Type</th>
            </tr>
          </thead>
          <tbody>
            ${inventoryRows || '<tr><td colspan="3">No inventory</td></tr>'}
          </tbody>
        </table>

        <div class="btn-group-actions mt-3">
          <button class="btn btn-sm btn-secondary" onclick="toggleHubStatus('${hub.hub_id}', '${isOffline ? 'ACTIVE' : 'OFFLINE'}')">
            ${isOffline ? '&#9654; Reactivate Hub' : '&#9940; Mark Node Offline'}
          </button>
        </div>
      </div>
    `;
  }).join("");
}

async function toggleHubStatus(hubId, newStatus) {
  try {
    await fetch(`/api/resources/hubs/${hubId}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ operational_status: newStatus })
    });
    showToast(`Hub ${hubId} status changed to ${newStatus}`, "info");
    await refreshAllData(false);
  } catch (err) {
    showToast("Status change failed", "danger");
  }
}

// Mesh & Ledger
async function simulateMeshBroadcast() {
  try {
    const res = await fetch("/api/mesh/broadcast", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        payload_type: "PEER_SYNC_PING",
        payload_data: { ping_source: "COMMAND_OPERATIONS_WEB", timestamp: Date.now() },
        max_hops: 7
      })
    }).then(r => r.json());

    showToast(`Mesh Packet Broadcasted: ${res.packet_id} (HMAC Verified)`, "success");
    await loadMeshPackets();
    await loadLedgerBlocks();
  } catch (err) {
    showToast("Mesh broadcast error", "danger");
  }
}

async function loadMeshPackets() {
  const container = document.getElementById("meshPacketsList");
  if (!container) return;

  try {
    const packets = await fetch("/api/mesh/packets").then(r => r.json());
    container.innerHTML = packets.map(p => `
      <div class="packet-card">
        <div class="packet-top">
          <span class="text-accent">&#128246; ${p.packet_id}</span>
          <span class="badge badge-success">&#10004; HMAC-VERIFIED (Hops: ${p.hop_count}/${p.max_hops})</span>
        </div>
        <div><strong>Type:</strong> ${p.payload_type} &bull; <strong>Sender:</strong> ${p.sender_node_id}</div>
        <div class="hash-preview mt-1">Sig: ${p.signature_hmac.substring(0, 32)}...</div>
      </div>
    `).join("");
  } catch (err) {
    console.error(err);
  }
}

async function loadLedgerBlocks() {
  const container = document.getElementById("ledgerChainContainer");
  if (!container) return;

  try {
    const blocks = await fetch("/api/mesh/ledger/blocks").then(r => r.json());
    container.innerHTML = blocks.map(b => `
      <div class="block-card">
        <div class="block-top">
          <span>&#128274; Block #${b.block_index} [${b.event_type}]</span>
          <span class="badge badge-accent">IMMUTABLE</span>
        </div>
        <div><strong>Block Hash:</strong> <span class="hash-preview">${b.block_hash.substring(0, 32)}...</span></div>
        <div><strong>Prev Hash:</strong> <span class="text-muted">${b.previous_hash.substring(0, 24)}...</span></div>
      </div>
    `).join("");
  } catch (err) {
    console.error(err);
  }
}

async function verifyLedgerIntegrity() {
  try {
    const res = await fetch("/api/mesh/ledger/verify").then(r => r.json());
    if (res.is_intact) {
      showToast(`Ledger Validated: ${res.total_blocks} Blocks 100% Intact`, "success");
    } else {
      showToast("Ledger Tamper Detected!", "danger");
    }
  } catch (err) {
    showToast("Ledger verification error", "danger");
  }
}

// Directives & HRVI Zones Render
function renderDirectives(assessment) {
  const container = document.getElementById("commanderDirectivesContainer");
  const badge = document.getElementById("commanderStatusBadge");
  if (!container) return;

  if (badge) badge.textContent = `STATUS: ${assessment.overall_crisis_status}`;

  container.innerHTML = assessment.actionable_directives.map(d => `
    <div class="directive-card ${d.severity === 'CRITICAL' ? 'sev-critical' : 'sev-high'}">
      <div class="directive-title">[${d.severity}] ${d.title}</div>
      <div class="text-sm text-secondary">${d.description}</div>
      <div class="directive-action"><strong>Required Action:</strong> ${d.recommended_action}</div>
    </div>
  `).join("");
}

function renderZones(zones) {
  const container = document.getElementById("zonesTableWrapper");
  if (!container) return;

  container.innerHTML = zones.map(z => {
    const tierClass = z.risk_tier === 'CRITICAL_RED' ? 'tier-critical' : (z.risk_tier === 'HIGH_ORANGE' ? 'tier-high' : 'tier-moderate');

    return `
      <div class="zone-card ${tierClass}">
        <div class="zone-header">
          <strong>${z.zone_name} (${z.zone_id})</strong>
          <span class="badge ${z.risk_tier === 'CRITICAL_RED' ? 'badge-danger' : 'badge-accent'}">HRVI ${z.composite_hrvi.toFixed(3)} [${z.risk_tier}]</span>
        </div>
        <div class="text-sm text-secondary">
          Demographic Risk: ${(z.demographic_risk * 100).toFixed(0)}% &bull; Infrastructure Risk: ${(z.infrastructure_risk * 100).toFixed(0)}% &bull; Medical Isolation: ${(z.medical_isolation_risk * 100).toFixed(0)}%
        </div>
        ${z.priority_intervention_notes.length > 0 ? `
          <div class="mt-2 text-sm" style="color: #fca5a5;">
            &#9888; ${z.priority_intervention_notes[0]}
          </div>
        ` : ''}
      </div>
    `;
  }).join("");
}

// Toast Helper
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}
