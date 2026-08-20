/**
 * BioVeil ZK — Sponsor & Pharma Hub Module
 */

const SponsorPortal = {
  async init() {
    await this.renderSponsorTrials();
    this.setupEventListeners();
  },

  async renderSponsorTrials() {
    const container = document.getElementById('sponsor-trials-list');
    if (!container) return;

    try {
      const res = await fetch('/api/trials');
      const trials = await res.json();
      
      container.innerHTML = '';
      trials.forEach(t => {
        const percent = Math.min(100, Math.round((t.enrolled_count / t.max_participants) * 100));
        const card = document.createElement('div');
        card.className = 'card glass-card mb-4';
        card.style.padding = '1.2rem';
        card.style.background = 'rgba(7, 9, 19, 0.7)';

        card.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.6rem;">
            <div>
              <span style="font-size:0.75rem; color:#818cf8; font-weight:700; text-transform:uppercase;">${t.phase} &bull; ${t.therapeutic_area}</span>
              <h4 style="font-size:1.05rem; color:#fff; margin-top:0.15rem;">${t.title}</h4>
              <span style="font-size:0.78rem; color:#94a3b8;">Sponsor: ${t.sponsor_name}</span>
            </div>
            <span class="badge-status-pill success" style="font-size:0.75rem;">${t.status}</span>
          </div>

          <div style="margin:0.85rem 0;">
            <div style="display:flex; justify-content:space-between; font-size:0.78rem; margin-bottom:0.3rem;">
              <span style="color:#94a3b8;">Cohort Enrollment Progress</span>
              <span style="color:#fff; font-weight:700;">${t.enrolled_count} / ${t.max_participants} (${percent}%)</span>
            </div>
            <div style="background:rgba(255,255,255,0.08); height:6px; border-radius:3px; overflow:hidden;">
              <div style="background:linear-gradient(90deg, #6366f1, #10b981); height:100%; width:${percent}%;"></div>
            </div>
          </div>

          <div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:0.5rem; background:rgba(255,255,255,0.03); padding:0.6rem; border-radius:6px; font-size:0.78rem;">
            <div>
              <span style="color:#64748b;">Escrow Locked:</span>
              <span style="color:#c4b5fd; font-weight:700; margin-left:0.3rem;">${t.escrow_deposit_night.toLocaleString()} NIGHT</span>
            </div>
            <div>
              <span style="color:#64748b;">Per-Patient Reward:</span>
              <span style="color:#6ee7b7; font-weight:700; margin-left:0.3rem;">${t.milestone_reward_night.toLocaleString()} NIGHT</span>
            </div>
          </div>

          <div style="margin-top:0.75rem; font-family:var(--font-mono); font-size:0.7rem; color:#64748b;">
            Contract: <span style="color:#94a3b8;">${t.contract_address}</span> | ID: <span>${t.trial_id.slice(0, 14)}...</span>
          </div>
        `;
        container.appendChild(card);
      });
    } catch (err) {
      console.error('Failed to render sponsor trials:', err);
    }
  },

  setupEventListeners() {
    const form = document.getElementById('create-trial-form');
    if (form) {
      form.addEventListener('submit', (e) => this.handleCreateTrial(e));
    }
  },

  async handleCreateTrial(e) {
    e.preventDefault();
    const statusMsg = document.getElementById('create-trial-status');
    statusMsg.textContent = 'Compiling Compact constraints & deploying to Midnight...';
    statusMsg.style.color = '#38bdf8';

    const payload = {
      title: document.getElementById('form-trial-title').value.trim(),
      sponsor_name: document.getElementById('form-sponsor-name').value.trim(),
      therapeutic_area: document.getElementById('form-therapeutic-area').value.trim(),
      required_biomarker: document.getElementById('form-biomarker').value.trim(),
      phase: document.getElementById('form-phase').value.trim(),
      min_age: parseInt(document.getElementById('form-min-age').value),
      max_age: parseInt(document.getElementById('form-max-age').value),
      min_egfr_level: parseInt(document.getElementById('form-min-egfr').value),
      max_blood_pressure_systolic: parseInt(document.getElementById('form-max-bp').value),
      max_participants: parseInt(document.getElementById('form-max-participants').value),
      milestone_reward_night: parseInt(document.getElementById('form-milestone-reward').value)
    };

    try {
      const res = await fetch('/api/trials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (res.ok) {
        statusMsg.style.color = '#10b981';
        statusMsg.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${data.message} (Tx: ${data.tx.tx_hash.slice(0, 16)}...)`;
        await this.renderSponsorTrials();
        if (window.PatientPortal) {
          await PatientPortal.loadActiveTrials();
        }
      } else {
        statusMsg.style.color = '#f43f5e';
        statusMsg.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> ${data.detail || 'Creation failed'}`;
      }
    } catch (err) {
      statusMsg.style.color = '#f43f5e';
      statusMsg.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> Error: ${err.message}`;
    }
  }
};
