/**
 * BioVeil ZK — Midnight Network Block Explorer & Compact Playground Module
 */

const ExplorerModule = {
  compactSources: {},

  async init() {
    await this.loadRecentBlocks();
    await this.loadCompactSources();
    this.setupCompactButtons();
  },

  async loadRecentBlocks() {
    try {
      const res = await fetch('/api/network/blocks?limit=15');
      const blocks = await res.json();
      const tbody = document.getElementById('explorer-blocks-tbody');
      if (!tbody) return;

      tbody.innerHTML = '';
      blocks.reverse().forEach(b => this.prependBlockRow(b, tbody));
    } catch (err) {
      console.error('Failed to load recent blocks:', err);
    }
  },

  prependBlockRow(block, tbody = null) {
    if (!tbody) {
      tbody = document.getElementById('explorer-blocks-tbody');
    }
    if (!tbody) return;

    const tx = block.transactions[0] || {};
    const row = document.createElement('tr');
    
    row.innerHTML = `
      <td style="font-weight:700; color:#fff;">#${block.block_height.toLocaleString()}</td>
      <td class="code-font" style="color:#c4b5fd;">${block.block_hash.slice(0, 12)}...</td>
      <td style="color:#67e8f9; font-weight:600;">${tx.contract_target || 'System'}</td>
      <td><span class="biomarker-pill" style="font-size:0.75rem;">${tx.circuit_invoked || 'consensusBlock'}</span></td>
      <td style="font-size:0.75rem; color:#94a3b8;">${(tx.public_disclosures || []).join(', ') || 'None'}</td>
      <td class="code-font" style="color:#fde68a;">${(tx.dust_fee_consumed || 1000).toLocaleString()} DUST</td>
      <td><span class="live-pulse-badge" style="font-size:0.7rem;"><span class="dot"></span> CONFIRMED</span></td>
    `;

    tbody.insertBefore(row, tbody.firstChild);

    // Keep table size limited to 25 rows
    while (tbody.children.length > 25) {
      tbody.removeChild(tbody.lastChild);
    }
  },

  async loadCompactSources() {
    try {
      const res = await fetch('/api/contracts/compact-source');
      this.compactSources = await res.json();
      
      const codeDisplay = document.getElementById('compact-code-display');
      if (codeDisplay && this.compactSources['BioVeilZK.compact']) {
        codeDisplay.textContent = this.compactSources['BioVeilZK.compact'];
      }
    } catch (err) {
      console.error('Failed to load Compact contract sources:', err);
    }
  },

  setupCompactButtons() {
    const btns = document.querySelectorAll('.contract-file-btn');
    btns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        btns.forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        const filename = e.target.getAttribute('data-file');
        const codeDisplay = document.getElementById('compact-code-display');
        if (codeDisplay && this.compactSources[filename]) {
          codeDisplay.textContent = this.compactSources[filename];
        }
      });
    });
  }
};
