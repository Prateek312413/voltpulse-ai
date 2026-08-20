/**
 * BioVeil ZK — Main Application Orchestrator & Live Telemetry
 */

document.addEventListener('DOMContentLoaded', async () => {
  initParticleBackground();
  initTabNavigation();
  initWebSocket();

  // Initialize all child modules
  if (window.PatientPortal) await PatientPortal.init();
  if (window.SponsorPortal) await SponsorPortal.init();
  if (window.AuditorPortal) await AuditorPortal.init();
  if (window.ExplorerModule) await ExplorerModule.init();

  // Fetch initial network stats
  await updateNetworkStats();
});

function initTabNavigation() {
  const tabs = document.querySelectorAll('.nav-tab');
  const panes = document.querySelectorAll('.tab-pane');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      panes.forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const targetId = tab.getAttribute('data-tab');
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add('active');
      }
    });
  });
}

function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/blocks`;

  try {
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'NEW_MIDNIGHT_BLOCK' || data.type === 'INITIAL_SNAPSHOT') {
          if (data.network_stats) {
            applyNetworkStats(data.network_stats);
          }
          if (data.block && window.ExplorerModule) {
            ExplorerModule.prependBlockRow(data.block);
          }
        } else if (data.type === 'NEW_ZK_ENROLLMENT') {
          if (window.SponsorPortal) {
            SponsorPortal.renderSponsorTrials();
          }
        }
      } catch (err) {
        console.error('Error handling WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      // Reconnect after 4s
      setTimeout(initWebSocket, 4000);
    };
  } catch (err) {
    console.error('WebSocket connection failed:', err);
  }
}

async function updateNetworkStats() {
  try {
    const res = await fetch('/api/network/stats');
    const stats = await res.json();
    applyNetworkStats(stats);
  } catch (err) {
    console.error('Failed to update network stats:', err);
  }
}

function applyNetworkStats(stats) {
  const blockEl = document.getElementById('nav-block-height');
  const escrowEl = document.getElementById('stat-total-escrow');
  const proofsEl = document.getElementById('stat-total-proofs');
  const disbursedEl = document.getElementById('stat-total-disbursed');

  if (blockEl) blockEl.textContent = `Block #${stats.current_block_height.toLocaleString()}`;
  if (escrowEl) escrowEl.textContent = `${stats.total_locked_night_escrow.toLocaleString()} NIGHT`;
  if (proofsEl) proofsEl.textContent = stats.total_shielded_proofs.toString();
  if (disbursedEl) disbursedEl.textContent = `${stats.total_disbursed_night.toLocaleString()} NIGHT`;
}

function initParticleBackground() {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const particles = [];
  const count = 45;

  for (let i = 0; i < count; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      radius: Math.random() * 2 + 1,
      color: i % 3 === 0 ? 'rgba(139, 92, 246, 0.4)' : i % 3 === 1 ? 'rgba(16, 185, 129, 0.35)' : 'rgba(6, 182, 212, 0.35)'
    });
  }

  function render() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < count; i++) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.fill();

      for (let j = i + 1; j < count; j++) {
        const p2 = particles[j];
        const dx = p.x - p2.x;
        const dy = p.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = `rgba(99, 102, 241, ${0.15 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(render);
  }

  render();
}
