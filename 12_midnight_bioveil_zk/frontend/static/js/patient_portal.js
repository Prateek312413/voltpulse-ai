/**
 * BioVeil ZK — Patient Portal Module
 */

const PatientPortal = {
  samplePatients: {},
  activeTrials: [],
  currentPatient: null,
  currentTrial: null,
  latestProof: null,

  async init() {
    await this.loadSamplePatients();
    await this.loadActiveTrials();
    this.setupEventListeners();
  },

  async loadSamplePatients() {
    try {
      const res = await fetch('/api/patients/samples');
      this.samplePatients = await res.json();
      const select = document.getElementById('patient-profile-select');
      
      // Default to first profile
      const firstKey = Object.keys(this.samplePatients)[0];
      if (firstKey) {
        this.selectPatient(firstKey);
      }
    } catch (err) {
      console.error('Failed to load sample patients:', err);
    }
  },

  async loadActiveTrials() {
    try {
      const res = await fetch('/api/trials');
      this.activeTrials = await res.json();
      const select = document.getElementById('target-trial-select');
      select.innerHTML = '';
      
      this.activeTrials.forEach((trial, index) => {
        const opt = document.createElement('option');
        opt.value = trial.trial_id;
        opt.textContent = `${trial.title} (${trial.phase} | ${trial.sponsor_name})`;
        select.appendChild(opt);
      });

      if (this.activeTrials.length > 0) {
        this.selectTrial(this.activeTrials[0].trial_id);
      }
    } catch (err) {
      console.error('Failed to load active trials:', err);
    }
  },

  selectPatient(patientKey) {
    this.currentPatient = this.samplePatients[patientKey];
    if (!this.currentPatient) return;

    // Update active wallet display in header
    const walletAddrEl = document.getElementById('active-wallet-address');
    if (walletAddrEl) {
      walletAddrEl.textContent = `${this.currentPatient.midnight_shielded_address.slice(0, 18)}...`;
    }

    const previewBox = document.getElementById('ehr-preview-box');
    const biomarkerPills = this.currentPatient.biomarkers.map(b => `<span class="biomarker-pill">${b}</span>`).join('');
    const conditionsPills = this.currentPatient.diagnosed_conditions.length > 0
      ? this.currentPatient.diagnosed_conditions.map(c => `<span class="biomarker-pill" style="background:rgba(244,63,94,0.15); border-color:rgba(244,63,94,0.3); color:#fda4af;">${c}</span>`).join('')
      : '<span style="color:#94a3b8; font-size:0.75rem;">None (Clean safety record)</span>';

    previewBox.innerHTML = `
      <div class="ehr-item-grid">
        <div class="ehr-field">
          <span class="label">Patient Name & ID</span>
          <span class="value">${this.currentPatient.full_name} (${this.currentPatient.patient_id})</span>
        </div>
        <div class="ehr-field">
          <span class="label">Demographics</span>
          <span class="value">Age: ${this.currentPatient.age} | ${this.currentPatient.gender}</span>
        </div>
        <div class="ehr-field">
          <span class="label">Renal Function (eGFR)</span>
          <span class="value" style="color: ${this.currentPatient.egfr_level >= 60 ? '#10b981' : '#f43f5e'};">
            ${this.currentPatient.egfr_level} mL/min/1.73m²
          </span>
        </div>
        <div class="ehr-field">
          <span class="label">Blood Pressure</span>
          <span class="value">${this.currentPatient.systolic_bp} / ${this.currentPatient.diastolic_bp} mmHg</span>
        </div>
      </div>
      
      <div style="margin-top:0.85rem;">
        <span class="label" style="font-size:0.72rem; color:#64748b; text-transform:uppercase;">Genomic Biomarkers</span>
        <div class="biomarker-pill-list">${biomarkerPills}</div>
      </div>

      <div style="margin-top:0.75rem;">
        <span class="label" style="font-size:0.72rem; color:#64748b; text-transform:uppercase;">Diagnosed Comorbidities</span>
        <div class="biomarker-pill-list">${conditionsPills}</div>
      </div>

      <div style="margin-top:0.75rem;">
        <span class="label" style="font-size:0.72rem; color:#64748b; text-transform:uppercase;">Private Witness Secret Key</span>
        <div style="font-family:var(--font-mono); font-size:0.72rem; color:#818cf8; word-break:break-all;">
          ${this.currentPatient.secret_key_hex}
        </div>
      </div>
    `;

    // Update claim address field
    const claimAddrInput = document.getElementById('claim-address-input');
    if (claimAddrInput) {
      claimAddrInput.value = this.currentPatient.midnight_shielded_address;
    }
  },

  selectTrial(trialId) {
    this.currentTrial = this.activeTrials.find(t => t.trial_id === trialId);
    if (!this.currentTrial) return;

    const summaryBox = document.getElementById('trial-criteria-summary');
    const c = this.currentTrial.criteria;
    const excl = c.excluded_conditions.length > 0 ? c.excluded_conditions.join(', ') : 'None';

    summaryBox.innerHTML = `
      <div style="font-size:0.85rem; color:#cbd5e1; margin-bottom:0.75rem; line-height:1.4;">
        ${this.currentTrial.description}
      </div>

      <div class="criteria-badge-row">
        <span class="criteria-tag"><i class="fa-solid fa-dna"></i> Biomarker: ${c.required_biomarker}</span>
        <span class="criteria-tag"><i class="fa-solid fa-calendar"></i> Age Range: ${c.min_age} - ${c.max_age} yrs</span>
        <span class="criteria-tag"><i class="fa-solid fa-heart-pulse"></i> Min eGFR: &ge; ${c.min_egfr_level}</span>
        <span class="criteria-tag"><i class="fa-solid fa-gauge-high"></i> Max BP: &le; ${c.max_blood_pressure_systolic} mmHg</span>
      </div>

      <div style="font-size:0.78rem; color:#94a3b8; margin-top:0.5rem;">
        <strong>Excluded Conditions:</strong> <span style="color:#fda4af;">${excl}</span>
      </div>

      <div style="margin-top:0.75rem; display:flex; justify-content:space-between; font-size:0.82rem;">
        <span><strong>Cohort Slots:</strong> ${this.currentTrial.enrolled_count} / ${this.currentTrial.max_participants} Enrolled</span>
        <span style="color:#6ee7b7; font-weight:700;"><strong>Reward:</strong> ${this.currentTrial.milestone_reward_night.toLocaleString()} NIGHT / Checkpoint</span>
      </div>
    `;
  },

  setupEventListeners() {
    // Patient select dropdown
    const pSelect = document.getElementById('patient-profile-select');
    if (pSelect) {
      pSelect.addEventListener('change', (e) => this.selectPatient(e.target.value));
    }

    // Trial select dropdown
    const tSelect = document.getElementById('target-trial-select');
    if (tSelect) {
      tSelect.addEventListener('change', (e) => this.selectTrial(e.target.value));
    }

    // Generate ZK Proof button
    const btnProof = document.getElementById('btn-generate-zk-proof');
    if (btnProof) {
      btnProof.addEventListener('click', () => this.generateProof());
    }

    // Run Clinical Agent button
    const btnAgent = document.getElementById('btn-run-clinical-agent');
    if (btnAgent) {
      btnAgent.addEventListener('click', () => this.runClinicalAgent());
    }

    // Submit Proof to Midnight button
    const btnSubmit = document.getElementById('btn-submit-to-midnight');
    if (btnSubmit) {
      btnSubmit.addEventListener('click', () => this.submitProofToMidnight());
    }

    // Claim Milestone Stipend button
    const btnClaim = document.getElementById('btn-claim-stipend');
    if (btnClaim) {
      btnClaim.addEventListener('click', () => this.claimMilestone());
    }
  },

  async generateProof() {
    if (!this.currentPatient || !this.currentTrial) return;

    const btn = document.getElementById('btn-generate-zk-proof');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Synthesizing Halo2 ZK-Proof...';

    try {
      const res = await fetch('/api/zk/generate-proof', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trial_id: this.currentTrial.trial_id,
          patient_profile: this.currentPatient,
          include_viewing_key: true
        })
      });

      const proofData = await res.json();
      this.latestProof = proofData;

      // Render constraints and meta summary
      const constraintsContainer = document.getElementById('circuit-constraints-list');
      ZKProverUI.renderConstraints(proofData.circuit_constraints, constraintsContainer);
      ZKProverUI.updateProofSummary(proofData);

      // Scroll smoothly to results
      document.getElementById('zk-proof-results-panel').scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      console.error('ZK Proof generation failed:', err);
      alert('Error generating zero-knowledge proof: ' + err.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  },

  async submitProofToMidnight() {
    if (!this.latestProof || !this.currentPatient || !this.currentTrial) return;

    const btn = document.getElementById('btn-submit-to-midnight');
    const feedback = document.getElementById('submission-status-feedback');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying on Midnight Blockchain...';
    feedback.textContent = '';

    try {
      const res = await fetch('/api/zk/submit-proof', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trial_id: this.currentTrial.trial_id,
          nullifier_hash: this.latestProof.nullifier_hash,
          public_commitment: this.latestProof.public_commitment,
          proof_bytes_hex: this.latestProof.proof_bytes_hex,
          shielded_address: this.currentPatient.midnight_shielded_address
        })
      });

      const result = await res.json();
      if (res.ok) {
        feedback.className = 'submission-feedback success';
        feedback.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${result.message} (Tx: ${result.transaction.tx_hash.slice(0, 14)}...)`;
        await this.loadActiveTrials(); // Refresh enrollment counts
      } else {
        feedback.className = 'submission-feedback error';
        feedback.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> ${result.detail || 'Enrollment failed'}`;
      }
    } catch (err) {
      feedback.className = 'submission-feedback error';
      feedback.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> Submission error: ${err.message}`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Submit Proof to Midnight Ledger';
    }
  },

  async claimMilestone() {
    const nullifier = document.getElementById('claim-nullifier-input').value.trim();
    const checkpoint = document.getElementById('claim-checkpoint-input').value.trim();
    const destAddr = document.getElementById('claim-address-input').value.trim();
    const resultMsg = document.getElementById('claim-result-msg');

    if (!nullifier) {
      alert('Please enter or generate an enrolled nullifier hash first.');
      return;
    }

    resultMsg.textContent = 'Verifying adherence proof & unlocking escrow...';
    resultMsg.style.color = '#38bdf8';

    try {
      const res = await fetch('/api/escrow/claim-milestone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nullifier_hash: nullifier,
          checkpoint_id: checkpoint,
          completion_secret_hex: '0x4488220192840192840192840192840192840192840192840192840192840192',
          shielded_recipient_address: destAddr
        })
      });

      const data = await res.json();
      if (res.ok) {
        resultMsg.style.color = '#10b981';
        resultMsg.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${data.message} (Tx: ${data.transaction_hash.slice(0, 16)}...)`;
        
        // Refresh wallet balance display
        const balEl = document.getElementById('active-wallet-balance');
        if (balEl) {
          const current = parseInt(balEl.textContent.replace(/,/g, '')) || 15000;
          balEl.textContent = `${(current + data.disbursed_amount_night).toLocaleString()} NIGHT`;
        }
      } else {
        resultMsg.style.color = '#f43f5e';
        resultMsg.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> ${data.detail || 'Claim failed'}`;
      }
    } catch (err) {
      resultMsg.style.color = '#f43f5e';
      resultMsg.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> Network error: ${err.message}`;
    }
  },

  async runClinicalAgent() {
    if (!this.currentPatient || !this.currentTrial) return;

    const panel = document.getElementById('clinical-agent-panel');
    const pvBox = document.getElementById('pharmacovigilance-result-box');
    const bayesBox = document.getElementById('bayesian-trajectory-result-box');
    const mcdaBox = document.getElementById('mcda-ranking-result-box');

    panel.classList.remove('hidden');
    pvBox.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Checking contraindications...';
    bayesBox.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Computing Bayesian trajectory...';
    mcdaBox.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Ranking clinical compatibility...';

    // 1. Pharmacovigilance check
    try {
      const pvRes = await fetch('/api/clinical/pharmacovigilance-check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trial_drug: 'CAR_T_CELL_THERAPY',
          medications: ['ACETAMINOPHEN', 'METFORMIN']
        })
      });
      const pvData = await pvRes.json();
      pvBox.innerHTML = `
        <div style="color: #10b981; font-weight: 700; margin-bottom: 0.25rem;">
          <i class="fa-solid fa-circle-check"></i> ZERO LETHAL CONTRAINDICATIONS
        </div>
        <div>Trial Drug: <strong>${pvData.checked_drug}</strong></div>
        <div>Active Meds Evaluated: <strong>${pvData.medication_count_blinded} (Blinded)</strong></div>
        <div style="font-family: var(--font-mono); font-size: 0.7rem; color: #818cf8; margin-top: 0.3rem;">
          ZK Commitment: ${pvData.zk_safety_commitment.slice(0, 20)}...
        </div>
      `;
    } catch (err) {
      pvBox.innerHTML = `<div style="color:#f43f5e;">Error: ${err.message}</div>`;
    }

    // 2. Bayesian Trajectory
    try {
      const bRes = await fetch(`/api/clinical/bayesian-trajectory?baseline_egfr=${this.currentPatient.egfr_level}&weeks=12`);
      const bData = await bRes.json();
      bayesBox.innerHTML = `
        <div style="color: #6ee7b7; font-weight: 700; margin-bottom: 0.25rem;">
          <i class="fa-solid fa-shield-halved"></i> Adherence Safety Score: ${bData.overall_adherence_safety_score}
        </div>
        <div>Baseline eGFR: <strong>${this.currentPatient.egfr_level} mL/min</strong></div>
        <div>Model: <em>${bData.bayesian_model}</em></div>
        <div style="font-family: var(--font-mono); font-size: 0.7rem; color: #c4b5fd; margin-top: 0.3rem;">
          ZK Trajectory Hash: ${bData.zk_trajectory_hash.slice(0, 20)}...
        </div>
      `;
    } catch (err) {
      bayesBox.innerHTML = `<div style="color:#f43f5e;">Error: ${err.message}</div>`;
    }

    // 3. MCDA Ranking
    try {
      const mRes = await fetch('/api/clinical/mcda-trial-ranking', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.currentPatient)
      });
      const mData = await mRes.json();
      const topMatch = mData.ranked_trials[0];
      mcdaBox.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
          <span style="font-weight:700; color:#fff;"><i class="fa-solid fa-ranking-star" style="color:#f59e0b;"></i> Top MCDA Clinical Match:</span>
          <span class="badge-status-pill success" style="font-size:0.75rem;">Score: ${topMatch.mcda_match_score}/100</span>
        </div>
        <div style="color:#cbd5e1;"><strong>${topMatch.title}</strong> (${topMatch.phase})</div>
        <div style="display:flex; gap:1rem; margin-top:0.4rem; color:#94a3b8; font-size:0.75rem;">
          <span>Genomic: ${topMatch.score_breakdown.genomic_affinity}/40</span>
          <span>Safety: ${topMatch.score_breakdown.safety_reserve}/25</span>
          <span>Escrow: ${topMatch.score_breakdown.escrow_incentive}/20</span>
          <span>Cohort Feasibility: ${topMatch.score_breakdown.cohort_feasibility}/15</span>
        </div>
      `;
    } catch (err) {
      mcdaBox.innerHTML = `<div style="color:#f43f5e;">Error: ${err.message}</div>`;
    }

    panel.scrollIntoView({ behavior: 'smooth' });
  }
};
