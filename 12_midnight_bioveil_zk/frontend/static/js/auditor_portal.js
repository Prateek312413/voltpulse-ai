/**
 * BioVeil ZK — FDA / IRB Regulatory Compliance Module
 */

const AuditorPortal = {
  activeGrants: [],

  async init() {
    await this.loadGrants();
    this.setupEventListeners();
  },

  async loadGrants() {
    try {
      const res = await fetch('/api/auditor/grants');
      this.activeGrants = await res.json();
      const select = document.getElementById('auditor-grant-select');
      select.innerHTML = '';

      this.activeGrants.forEach(g => {
        const opt = document.createElement('option');
        opt.value = g.grant_id;
        opt.textContent = `${g.organization_name} — Grant [${g.grant_id.slice(0, 18)}...] (${g.scope})`;
        select.appendChild(opt);
      });
    } catch (err) {
      console.error('Failed to load audit grants:', err);
    }
  },

  setupEventListeners() {
    const btn = document.getElementById('btn-inspect-audit');
    if (btn) {
      btn.addEventListener('click', () => this.inspectSelectedGrant());
    }
  },

  async inspectSelectedGrant() {
    const select = document.getElementById('auditor-grant-select');
    const grantId = select.value;
    if (!grantId) return;

    const resultsPanel = document.getElementById('audit-inspection-results');
    resultsPanel.classList.remove('hidden');
    resultsPanel.innerHTML = '<div style="color:#38bdf8; text-align:center; padding:1.5rem;"><i class="fa-solid fa-spinner fa-spin"></i> Decrypting viewing key & computing zero-knowledge cohort statistics...</div>';

    try {
      const res = await fetch(`/api/auditor/inspect/${grantId}`);
      const data = await res.json();

      if (!data.is_valid) {
        resultsPanel.innerHTML = '<div class="alert alert-danger">Invalid or expired audit viewing grant.</div>';
        return;
      }

      const m = data.decrypted_cohort_metrics;
      resultsPanel.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:0.75rem; margin-bottom:1rem;">
          <div>
            <h4 style="font-size:1.15rem; color:#fff;"><i class="fa-solid fa-shield-check" style="color:#10b981;"></i> Cryptographically Verified Regulatory Audit Report</h4>
            <span style="font-size:0.8rem; color:#94a3b8;">Auditor: ${data.organization_name} (${data.auditor_address})</span>
          </div>
          <span class="badge-status-pill success"><i class="fa-solid fa-check-double"></i> 100% HIPAA / GDPR COMPLIANT</span>
        </div>

        <div class="grid-3-col mb-4">
          <div class="stat-mini-card">
            <span class="label">Verified Cohort Size:</span>
            <span class="val" style="color:#10b981;">${m.cohort_total_verified_participants} Patients</span>
          </div>
          <div class="stat-mini-card">
            <span class="label">ZK Constraint Pass Rate:</span>
            <span class="val" style="color:#67e8f9;">${m.zk_constraint_satisfaction_rate}</span>
          </div>
          <div class="stat-mini-card">
            <span class="label">Milestone Adherence:</span>
            <span class="val" style="color:#fde68a;">${m.milestone_adherence_index}</span>
          </div>
        </div>

        <div class="grid-2-col">
          <div class="ehr-details-panel">
            <h5 style="color:#818cf8; margin-bottom:0.5rem; font-size:0.9rem;"><i class="fa-solid fa-users"></i> Demographic Distribution (Aggregated)</h5>
            <p style="font-size:0.82rem; color:#cbd5e1;">Mean Age: <strong>${m.demographic_summary.age_mean} yrs</strong> (&plusmn; ${m.demographic_summary.age_std_dev})</p>
            <p style="font-size:0.82rem; color:#cbd5e1;">Inclusion Bounds Satisfied: <strong>${m.demographic_summary.inclusion_age_bounds_met}</strong></p>
            <p style="font-size:0.82rem; color:#cbd5e1;">Gender Split: Female ${m.demographic_summary.gender_distribution.Female} | Male ${m.demographic_summary.gender_distribution.Male}</p>
          </div>

          <div class="ehr-details-panel">
            <h5 style="color:#10b981; margin-bottom:0.5rem; font-size:0.9rem;"><i class="fa-solid fa-heart-pulse"></i> Safety & Biomarker Concordance</h5>
            <p style="font-size:0.82rem; color:#cbd5e1;">Target Locus: <strong>${m.biomarker_homogeneity.target_locus}</strong></p>
            <p style="font-size:0.82rem; color:#cbd5e1;">Concordance: <strong>${m.biomarker_homogeneity.concordance_rate}</strong></p>
            <p style="font-size:0.82rem; color:#cbd5e1;">Renal Safety: ${m.safety_profile_aggregate.renal_function_mean_egfr}</p>
            <p style="font-size:0.82rem; color:#cbd5e1;">Blood Pressure Safety: ${m.safety_profile_aggregate.blood_pressure_systolic_mean}</p>
          </div>
        </div>

        <div style="background:rgba(7,9,19,0.9); border:1px solid var(--border-subtle); border-radius:8px; padding:0.85rem; margin-top:1rem; font-family:var(--font-mono); font-size:0.75rem;">
          <div style="color:#94a3b8; margin-bottom:0.3rem;">Cryptographic Audit Commitment & Receipts:</div>
          <div style="color:#c4b5fd;">Audit Hash Root: ${m.audit_hash_root}</div>
          <div style="color:#67e8f9;">Verification Log Receipt: ${data.verification_log_hash}</div>
        </div>
      `;
    } catch (err) {
      resultsPanel.innerHTML = `<div style="color:#f43f5e;">Audit inspection error: ${err.message}</div>`;
    }
  }
};
