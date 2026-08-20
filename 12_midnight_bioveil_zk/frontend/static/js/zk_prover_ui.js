/**
 * BioVeil ZK — Zero-Knowledge Prover UI Renderer
 */

const ZKProverUI = {
  renderConstraints(constraints, containerEl) {
    containerEl.innerHTML = '';
    
    constraints.forEach(c => {
      const card = document.createElement('div');
      card.className = `constraint-card ${c.evaluated_truth ? 'valid' : 'invalid'}`;
      
      card.innerHTML = `
        <div class="constraint-header">
          <span class="constraint-title">${c.name}</span>
          <span class="constraint-status-tag ${c.evaluated_truth ? 'pass' : 'fail'}">
            ${c.evaluated_truth ? '<i class="fa-solid fa-circle-check"></i> SATISFIED' : '<i class="fa-solid fa-circle-xmark"></i> VIOLATED'}
          </span>
        </div>
        <div class="constraint-expr">Circuit: <code>${c.circuit_expression}</code></div>
        <div style="font-size:0.75rem; color:#94a3b8; margin-bottom:0.25rem;">${c.description}</div>
        <div class="constraint-blinded">
          <span>Private Witness: <em>${c.private_value_blinded}</em></span>
        </div>
      `;
      containerEl.appendChild(card);
    });
  },

  updateProofSummary(proofData) {
    const resultsPanel = document.getElementById('zk-proof-results-panel');
    const badge = document.getElementById('proof-status-badge');
    const timeEl = document.getElementById('proof-synthesis-time');
    const nullifierEl = document.getElementById('proof-nullifier-val');
    const commitEl = document.getElementById('proof-commitment-val');
    const bytesEl = document.getElementById('proof-bytes-val');
    const submitBtn = document.getElementById('btn-submit-to-midnight');

    resultsPanel.classList.remove('hidden');

    if (proofData.verification_status) {
      badge.className = 'badge-status-pill success';
      badge.innerHTML = '<i class="fa-solid fa-shield-check"></i> ALL ZK CONSTRAINTS MET (ELIGIBLE)';
      submitBtn.disabled = false;
      submitBtn.className = 'btn btn-success btn-lg';
    } else {
      badge.className = 'badge-status-pill danger';
      badge.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> INELIGIBLE: CONSTRAINTS FAILED';
      submitBtn.disabled = true;
      submitBtn.className = 'btn btn-secondary btn-lg';
    }

    timeEl.textContent = `${proofData.proving_time_ms} ms (Halo2 Circuit Synthesis)`;
    nullifierEl.textContent = proofData.nullifier_hash;
    commitEl.textContent = proofData.public_commitment;
    bytesEl.textContent = proofData.proof_bytes_hex;

    // Fill the claim nullifier field as well for easy testing
    const claimInput = document.getElementById('claim-nullifier-input');
    if (claimInput) {
      claimInput.value = proofData.nullifier_hash;
    }
  }
};
