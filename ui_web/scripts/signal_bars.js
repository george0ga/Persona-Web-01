class SignalBars extends HTMLElement {
  static get observedAttributes() { return ['total','active','color','empty','size','state']; }
  constructor(){ super(); this.attachShadow({mode:'open'}); }
  connectedCallback(){ this.render(); }
  attributeChangedCallback(){ this.render(); }

  get total(){ return Math.max(1, parseInt(this.getAttribute('total') || '5', 10)); }
  get active(){ return Math.min(this.total, Math.max(0, parseInt(this.getAttribute('active') || '0', 10))); }
  get state(){ return (this.getAttribute('state') || '').toLowerCase(); }

  _getHostColorFallback() {
    // 1) CSS-переменная --signal-color → 2) CSS color → 3) null
    const cs = getComputedStyle(this);
    const varColor = cs.getPropertyValue('--signal-color').trim();
    if (varColor) return varColor;
    const cssColor = cs.color?.trim();
    return cssColor || null;
  }
  _getHostEmptyFallback() {
    const cs = getComputedStyle(this);
    const varEmpty = cs.getPropertyValue('--signal-empty').trim();
    return varEmpty || 'rgba(0,0,0,0.2)';
  }

  resolveColor() {
    // атрибут color (если не пустой)
    let explicit = this.getAttribute('color');
    if (explicit != null) {
      explicit = explicit.trim();
      if (explicit.length > 0) {
        // можно указать 'currentColor'
        return explicit;
      }
    }

    // palette по state
    const palette = { bad: '#ef4444', medium: '#f59e0b', good: '#22c55e', unknown: '#9ca3af' };
    if (['bad','medium','good','unknown'].includes(this.state)) {
      return palette[this.state];
    }

    // авто по доле
    const ratio = this.active / this.total;
    if (ratio < 0.34) return palette.bad;
    if (ratio < 0.67) return palette.medium;

    // если ни атрибута, ни state → пытаемся взять цвет с хоста
    return this._getHostColorFallback() || palette.good;
  }

  render(){
    const total = this.total;
    const active = this.active;
    const state  = this.state;

    const filled = this.resolveColor();
    // empty: атрибут → CSS var --signal-empty → дефолт
    const emptyAttr = (this.getAttribute('empty') || '').trim();
    const empty = emptyAttr || this._getHostEmptyFallback();

    const size   = Math.max(12, parseInt(this.getAttribute('size') || '24', 10));

    const barW = 3, gap = 2, maxH = 20, minH = 6;
    const viewW = total * barW + (total - 1) * gap;
    const viewH = maxH;

    let bars = '';
    for (let i = 0; i < total; i++) {
      const h = Math.round(minH + (maxH - minH) * (i / Math.max(1, total - 1)));
      const x = i * (barW + gap);
      const y = viewH - h;
      const useFill = (state === 'unknown') ? (filled || 'currentColor') : (i < active ? (filled || 'currentColor') : empty);
      bars += `<rect x="${x}" y="${y}" width="${barW}" height="${h}" rx="1" ry="1" fill="${useFill}"/>`;
    }

    // перечёркивание при unknown
    if (state === 'unknown') {
      bars += `<line x1="0" y1="0" x2="${viewW}" y2="${viewH}" stroke="currentColor" stroke-width="1" stroke-linecap="round"/>`;
    }

    const aspect = Math.max(viewW / viewH, 1);
    const pxW = Math.round(size * aspect);

    this.shadowRoot.innerHTML = `
      <style>
        :host { display:inline-block; line-height:0; vertical-align:middle; }
        svg { min-width:${size}px; }
      </style>
      <svg xmlns="http://www.w3.org/2000/svg"
           width="${pxW}" height="${size}"
           viewBox="0 0 ${viewW} ${viewH}"
           aria-label="Signal strength: ${state==='unknown'?'unknown':active+'/'+total}">
        ${bars}
      </svg>
    `;
  }
}
customElements.define('signal-bars', SignalBars);
