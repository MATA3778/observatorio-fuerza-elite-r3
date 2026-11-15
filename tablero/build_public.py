import re, sys
D=sys.argv[1] if len(sys.argv)>1 else '.'
page=open(f'{D}/index.html').read().replace('<meta name="dash-one-writer">\n','')
page=re.sub(r"\.attr\('(fill|stroke)', (\(?[^)]*?)?'var\(", lambda m: m.group(0).replace(".attr(", ".style(",1), page)
page=page.replace(".attr('fill', (p) => p.v === top && top > 0 ? dash.colors[0] : 'var(--cds-chart-muted)')", ".style('fill', (p) => p.v === top && top > 0 ? dash.colors[0] : 'var(--cds-chart-muted)')")
cortes=open(f'{D}/cortes_por_hora.json').read().replace('</','<\\/')
general=open(f'{D}/general.json').read().replace('</','<\\/')
import os
hechos=open(f'{D}/hechos.json').read().replace('</','<\\/') if os.path.exists(f'{D}/hechos.json') else '[]'
head='''<title>Observatorio R3 Público</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Public+Sans:wght@400;500;600&display=swap">
<style>
  /* Tablero de una columna: encabezado, filtros, cifras, gráficas y tablas en tarjetas. */
  :root {
    --color-bg: #f6f7f9; --color-panel: #ffffff; --color-fg: #17202b; --color-fg-muted: #5b6676;
    --color-border-line: #dde1e7; --color-ok: #1d7a46; --accent: #1b3350; --gold: #c9a227; --color-bad: #b42318;
    --cds-chart-grid: #e8ebef; --cds-chart-axis: #b7bec8; --cds-chart-muted: #c7d0dc;
    --cds-surface-popover: #ffffff; --cds-border: #d3d8df; --cds-text-secondary: #5b6676;
    --cds-shadow-popover: 0 4px 16px rgba(20, 30, 45, .12);
    --font-anthropic-sans: "Public Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    --font-anthropic-serif: "Source Serif 4", Georgia, "Times New Roman", serif;
    --cds-font-size-caption: .8125rem; --cds-font-size-body: .9375rem; --cds-font-size-heading: 1.0625rem; --cds-font-size-title: 1.75rem;
    --cds-font-weight-medium: 500; --cds-radius: 6px;
    --cds-gap-xs: 4px; --cds-gap-sm: 8px; --cds-gap-md: 12px; --cds-gap-lg: 24px;
    --cds-pad-xs: 4px; --cds-pad-sm: 8px; --cds-pad-md: 12px; --cds-pad-lg: 18px; --cds-dur-slow: .3s;
  }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
    --color-bg: #0f141b; --color-panel: #161d27; --color-fg: #e7ebf0; --color-fg-muted: #9aa5b4;
    --color-border-line: #283242; --color-ok: #5cc98a; --accent: #7fa8e6; --gold: #e0b93f; --color-bad: #ff8a80;
    --cds-chart-grid: #222b38; --cds-chart-axis: #3a4555; --cds-chart-muted: #3b4a60;
    --cds-surface-popover: #1c2430; --cds-border: #2f3a4b; --cds-text-secondary: #9aa5b4;
    --cds-shadow-popover: 0 4px 16px rgba(0, 0, 0, .5); color-scheme: dark; } }
  :root[data-theme="dark"] {
    --color-bg: #0f141b; --color-panel: #161d27; --color-fg: #e7ebf0; --color-fg-muted: #9aa5b4;
    --color-border-line: #283242; --color-ok: #5cc98a; --accent: #7fa8e6; --gold: #e0b93f; --color-bad: #ff8a80;
    --cds-chart-grid: #222b38; --cds-chart-axis: #3a4555; --cds-chart-muted: #3b4a60;
    --cds-surface-popover: #1c2430; --cds-border: #2f3a4b; --cds-text-secondary: #9aa5b4;
    --cds-shadow-popover: 0 4px 16px rgba(0, 0, 0, .5); color-scheme: dark; }
  body { background: var(--color-bg); color: var(--color-fg); font-family: var(--font-anthropic-sans); }
  #dash-root { max-width: 1180px; margin-inline: auto; padding-block: 24px 40px;
    padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
  .dash-select { font: inherit; font-size: var(--cds-font-size-caption); color: var(--color-fg); background-color: var(--color-panel);
    border: 1px solid var(--color-border-line); border-radius: var(--cds-radius); padding: var(--cds-pad-xs) var(--cds-pad-sm); }
  .ob b { font-weight: 600; }
  .ob-tablewrap:focus-visible, .dash-select:focus-visible, .ob-date:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<script type="application/json" id="data-cortes">'''+cortes+'''</script>
<script type="application/json" id="data-general">'''+general+'''</script>
<script type="application/json" id="data-hechos">'''+hechos+'''</script>
<script>
  window.dash = (() => {
    const store = {};
    ['cortes', 'general', 'hechos'].forEach((id) => { try { store[id] = JSON.parse(document.getElementById('data-' + id).textContent); } catch (e) { store[id] = []; } });
    const defaults = { rango: '7', grupo: 'Acciones operativas', metrica: 'Personas investigadas', corte: '' };
    let params = { ...defaults };
    const listeners = [], draws = {};
    let started = false, queued = false;
    const colors = [];
    const readColors = () => { colors.length = 0; colors.push(getComputedStyle(document.documentElement).getPropertyValue('--accent').trim() || '#1f4e8c'); };
    const render = () => {
      queued = false; readColors();
      listeners.forEach((f) => { try { f(); } catch (e) { console.error(e); } });
      Object.entries(draws).forEach(([name, fn]) => document.querySelectorAll('[data-draw="' + name + '"]').forEach((el) => { if (!el.getClientRects().length) return; try { fn(el); } catch (e) { console.error(e); } }));
    };
    const schedule = () => { if (started && !queued) { queued = true; requestAnimationFrame(render); } };
    return {
      colors,
      data: (id) => ({ status: 'ok', data: store[id] || [], refreshing: false, meta: [] }),
      onData: (fn) => { listeners.push(fn); },
      draw: (name, fn) => { if (fn) draws[name] = fn; else schedule(); },
      params: () => ({ ...params }),
      setParams: (o) => { Object.entries(o).forEach(([k, v]) => { if (v === null || v === undefined) delete params[k]; else params[k] = v; }); schedule(); },
      resetParams: () => { params = { ...defaults }; schedule(); },
      setLink: (n) => { try { history.replaceState(null, '', '#' + n); } catch (e) {} },
      refresh: () => {},
      _start: () => {
        started = true; render();
        let w = window.innerWidth;
        window.addEventListener('resize', () => { if (window.innerWidth !== w) { w = window.innerWidth; schedule(); } });
        try { window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', schedule); } catch (e) {}
        try { new MutationObserver(schedule).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] }); } catch (e) {}
      },
    };
  })();
</script>
<div id="dash-root">
'''
tail='''
</div>
<script>dash._start();</script>
'''
open(f'{D}/observatorio_publico.html','w').write(head+page+tail)
print('ok')
