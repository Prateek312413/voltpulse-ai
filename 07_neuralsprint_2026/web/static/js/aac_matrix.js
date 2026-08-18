/**
 * AAC Matrix Grid & Adaptive Switch/Gaze Controller
 * Professional Clinical SVG Icons, Keyboard Scanning, and Gaze Dwell Selection.
 */
class AACMatrixController {
  constructor(containerId, onSelectCallback) {
    this.container = document.getElementById(containerId);
    this.onSelect = onSelectCallback;
    this.vocabulary = [];
    this.activeCategory = "essentials";
    
    // Switch-access scanning state
    this.isScanning = false;
    this.scanIndex = 0;
    this.scanInterval = null;
    this.scanSpeedMs = 1400;

    // Gaze dwell-time state
    this.dwellTimeout = null;
    this.dwellDurationMs = 1200;

    this.svgIcons = {
      alert: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
      water: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path></svg>`,
      pain: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>`,
      doctor: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"></path><path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"></path><circle cx="20" cy="10" r="2"></circle></svg>`,
      tired: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`,
      food: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8h1a4 4 0 0 1 0 8h-1"></path><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"></path><line x1="6" y1="1" x2="6" y2="4"></line><line x1="10" y1="1" x2="10" y2="4"></line><line x1="14" y1="1" x2="14" y2="4"></line></svg>`,
      medicine: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="4"></rect><line x1="9" y1="12" x2="15" y2="12"></line><line x1="12" y1="9" x2="12" y2="15"></line></svg>`,
      restroom: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"></path><path d="M5 21V7l8-4v18"></path><path d="M19 21V11l-6-3"></path><circle cx="9" cy="12" r="1"></circle></svg>`,
      family: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>`,
      thanks: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>`,
      check: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
      cancel: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`
    };

    this.initKeyboardListeners();
  }

  setVocabulary(categories) {
    this.vocabulary = categories;
    this.render();
  }

  setCategory(categoryId) {
    this.activeCategory = categoryId;
    this.scanIndex = 0;
    this.render();
  }

  render() {
    if (!this.container) return;
    const category = this.vocabulary.find(c => c.id === this.activeCategory) || this.vocabulary[0];
    if (!category) return;

    this.container.innerHTML = '';
    category.symbols.forEach((sym, idx) => {
      const cell = document.createElement('div');
      cell.className = `aac-cell ${this.isScanning && idx === this.scanIndex ? 'scanning-active' : ''}`;
      cell.id = `aac-item-${sym.id}`;
      cell.setAttribute('role', 'button');
      cell.setAttribute('tabindex', '0');
      cell.setAttribute('aria-label', `${sym.label}, ARPABET phonemes: ${sym.phonemes.join(' ')}`);

      const iconSvg = this.svgIcons[sym.icon] || `<div class="aac-icon-fallback">${sym.label.charAt(0)}</div>`;

      cell.innerHTML = `
        <div class="aac-icon-badge" data-category="${sym.category}">
          ${iconSvg}
        </div>
        <div class="aac-label">${sym.label}</div>
        <div class="aac-phoneme-badge">
          <span class="phoneme-tag">ARPABET</span>
          <span class="phoneme-seq">/${sym.phonemes.join('·')}/</span>
        </div>
        <div class="dwell-progress" id="dwell-${sym.id}"></div>
      `;

      // Click & Keyboard selection
      cell.onclick = () => this.handleSelection(sym);
      cell.onkeydown = (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.handleSelection(sym);
        }
      };

      // Gaze dwell simulation on mouse hover
      cell.onmouseenter = () => this.startGazeDwell(sym.id, sym);
      cell.onmouseleave = () => this.cancelGazeDwell(sym.id);

      this.container.appendChild(cell);
    });
  }

  handleSelection(symbol) {
    if (this.onSelect) {
      this.onSelect(symbol);
    }
  }

  startGazeDwell(symId, symbol) {
    const bar = document.getElementById(`dwell-${symId}`);
    if (bar) bar.style.width = '100%';

    this.dwellTimeout = setTimeout(() => {
      this.handleSelection(symbol);
      this.cancelGazeDwell(symId);
    }, this.dwellDurationMs);
  }

  cancelGazeDwell(symId) {
    if (this.dwellTimeout) {
      clearTimeout(this.dwellTimeout);
      this.dwellTimeout = null;
    }
    const bar = document.getElementById(`dwell-${symId}`);
    if (bar) bar.style.width = '0%';
  }

  toggleAutoScan() {
    this.isScanning = !this.isScanning;
    if (this.isScanning) {
      this.scanIndex = 0;
      this.updateScanHighlight();
      this.scanInterval = setInterval(() => {
        const category = this.vocabulary.find(c => c.id === this.activeCategory) || this.vocabulary[0];
        if (!category) return;
        this.scanIndex = (this.scanIndex + 1) % category.symbols.length;
        this.updateScanHighlight();
      }, this.scanSpeedMs);
    } else {
      if (this.scanInterval) clearInterval(this.scanInterval);
      this.clearScanHighlight();
    }
    return this.isScanning;
  }

  selectCurrentScannedItem() {
    if (!this.isScanning) return;
    const category = this.vocabulary.find(c => c.id === this.activeCategory) || this.vocabulary[0];
    if (!category || category.symbols.length === 0) return;
    const selectedSymbol = category.symbols[this.scanIndex];
    if (selectedSymbol) {
      this.handleSelection(selectedSymbol);
    }
  }

  updateScanHighlight() {
    const cells = this.container.querySelectorAll('.aac-cell');
    cells.forEach((cell, idx) => {
      if (idx === this.scanIndex) {
        cell.classList.add('scanning-active');
        cell.focus();
      } else {
        cell.classList.remove('scanning-active');
      }
    });
  }

  clearScanHighlight() {
    const cells = this.container.querySelectorAll('.aac-cell');
    cells.forEach(cell => cell.classList.remove('scanning-active'));
  }

  initKeyboardListeners() {
    window.addEventListener('keydown', (e) => {
      // Spacebar triggers selection in active scanning mode
      if (e.code === 'Space' && this.isScanning && e.target === document.body) {
        e.preventDefault();
        this.selectCurrentScannedItem();
      }
    });
  }
}
