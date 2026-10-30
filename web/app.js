/* Junson Capital — AID Research Panel (frontend)
   Routes:  #/                 dashboard
            #/s/<sector>       opens the latest report of that sector in the current language
            #/r/<id>[/anchor]  report reader
   Only full reports in the current UI language are ever listed.
*/
(function(){
'use strict';

const $ = (id) => document.getElementById(id);
const state = {
  lang: 'en', docLang: 'en',
  sectors: [], reports: [],
  meta: {current_year: new Date().getFullYear(), current_quarter: Math.floor(new Date().getMonth()/3)+1},
  view: 'dash', sectorId: null, reportId: null, report: null,
  exhibits: [], lbIndex: -1, zoom: {s:1, tx:0, ty:0, fit:1},
  editing: null,
};

/* ---------------------------------------------------------------- helpers */
function el(tag, cls, text){
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined && text !== null) n.textContent = text;
  return n;
}
function t(key, vars){
  const dict = window.I18N[state.lang] || window.I18N.en;
  let s = dict[key] !== undefined ? dict[key] : (window.I18N.en[key] !== undefined ? window.I18N.en[key] : key);
  if (vars) Object.keys(vars).forEach(k => { s = s.split('{' + k + '}').join(vars[k]); });
  return s;
}
function toast(msg){
  const n = $('toast');
  n.textContent = msg; n.classList.add('show');
  clearTimeout(n._tm); n._tm = setTimeout(() => n.classList.remove('show'), 2000);
}
async function api(path, opts){
  const r = await fetch(path, opts);
  if (r.status === 401){
    location.href = '/login.html?next=' + encodeURIComponent(location.hash);
    throw new Error('login required');
  }
  let data = null;
  try { data = await r.json(); } catch (e) { data = null; }
  if (!r.ok) throw new Error((data && data.error) || (r.status + ' ' + r.statusText));
  return data;
}
function fmtDate(iso){
  if (!iso) return '—';
  try { return new Date(iso).toLocaleDateString(state.lang === 'cn' ? 'zh-CN' : 'en-US', {year:'numeric', month:'short', day:'numeric'}); }
  catch (e) { return iso; }
}
function sectorName(s){ return (state.lang === 'cn' ? (s.name_cn || s.name_en) : (s.name_en || s.name_cn)) || s.id; }
function sectorCoverage(s){ const c = state.lang === 'cn' ? (s.coverage_cn && s.coverage_cn.length ? s.coverage_cn : s.coverage_en) : (s.coverage_en && s.coverage_en.length ? s.coverage_en : s.coverage_cn); return (c || []).join(' / '); }
function sectorById(id){ return state.sectors.find(s => s.id === id) || null; }
function periodKey(p){ const m = /^(\d)Q(\d{4})$/.exec(p || ''); return m ? (+m[2])*10 + (+m[1]) : 0; }
function langLabel(l){ return t(l === 'cn' ? 'cn' : 'en'); }
function otherLang(){ return state.docLang === 'cn' ? 'en' : 'cn'; }
function nav(hash){ if (location.hash === hash) route(); else location.hash = hash; window.scrollTo({top:0}); }
function hashReport(id, anchor){ return '#/r/' + id + (anchor ? '/' + anchor : ''); }
function hashSector(id){ return '#/s/' + id; }
function escapeHtml(s){ return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function byUploaded(a, b){ return (b.uploaded_at || '').localeCompare(a.uploaded_at || ''); }
function nReports(n){ return n === 1 && state.lang === 'en' ? '1 report' : t('reports_in_lang', {n}); }
function nQuarters(n){ return n === 1 && state.lang === 'en' ? '1 quarter' : n + ' ' + t('quarters'); }

/* full reports in the current report language (state.docLang follows the UI language unless switched in the reader) */
function langReports(lang){ return state.reports.filter(r => r.nature === 'full' && r.language === (lang || state.docLang)); }
function findReport(sector, period, lang, nature){ return state.reports.find(r => r.sector === sector && r.period === period && r.language === lang && r.nature === nature) || null; }
function sectorReports(sectorId, lang){ return langReports(lang).filter(r => r.sector === sectorId); }
function latestOf(list){ return list.slice().sort(byUploaded)[0] || null; }

/* ---------------------------------------------------------------- i18n + theme */
function applyI18n(){
  document.documentElement.lang = state.lang === 'cn' ? 'zh-CN' : 'en';
  document.querySelectorAll('[data-i18n]').forEach(n => { n.textContent = t(n.getAttribute('data-i18n')); });
  document.querySelectorAll('[data-ph]').forEach(n => { n.placeholder = t(n.getAttribute('data-ph')); });
  document.querySelectorAll('[data-title]').forEach(n => { n.title = t(n.getAttribute('data-title')); });
  setToggle('langToggle', state.lang === 'cn', false);
}
/* a flip switch: `right` selects the second option; disabled when the other option is unavailable */
function setToggle(id, right, disabled){
  const tg = $(id);
  tg.classList.toggle('right', !!right);
  const spans = tg.querySelectorAll('span');
  spans[0].classList.toggle('on', !right);
  spans[1].classList.toggle('on', !!right);
  tg.disabled = !!disabled;
}
/* interface language only; the report language is switched inside the reader */
function setLang(l){
  if (l === state.lang) return;
  state.lang = l;
  try { localStorage.setItem('aid_lang', l); } catch (e) {}
  applyI18n();
  route();
}
/* switch the report language only (the in-page EN / 中文 switch) */
function setDocLang(l){
  state.docLang = l;
  try { localStorage.setItem('aid_doclang', l); } catch (e) {}
  if (state.view === 'art' && state.sectorId){
    const cur = state.report && state.report.meta;
    const twin = cur ? (findReport(cur.sector, cur.period, l, cur.nature) || findReport(cur.sector, cur.period, l, 'full')) : null;
    if (twin) nav(hashReport(twin.id)); else nav(hashSector(state.sectorId));
    return;
  }
  route();
}

/* ---------------------------------------------------------------- data */
async function loadAll(){
  const [sectors, reports, meta] = await Promise.all([api('/api/sectors'), api('/api/reports'), api('/api/meta')]);
  state.sectors = sectors; state.reports = reports; state.meta = meta;
  $('logoutBtn').hidden = !meta.auth;
  buildNav();
}

/* ---------------------------------------------------------------- nav */
function buildNav(){
  const n = $('mainnav');
  n.innerHTML = '';
  const dash = el('button', state.view === 'dash' ? 'active' : '', t('dashboard'));
  dash.type = 'button'; dash.addEventListener('click', () => nav('#/'));
  n.appendChild(dash);
  state.sectors.forEach(s => {
    const b = el('button', (state.view !== 'dash' && state.sectorId === s.id) ? 'active' : '');
    b.type = 'button';
    b.appendChild(document.createTextNode(sectorName(s)));
    const cnt = sectorReports(s.id).length;
    if (cnt) b.appendChild(el('em', null, String(cnt)));
    b.addEventListener('click', () => nav(hashSector(s.id)));
    n.appendChild(b);
  });
  const up = el('button', 'right'); up.type = 'button';
  up.textContent = '⬆ ' + t('upload_report');
  up.addEventListener('click', () => openUpload(state.sectorId));
  n.appendChild(up);
}

/* ---------------------------------------------------------------- dashboard */
function renderDash(){
  showView('dash');
  state.sectorId = null; state.reportId = null; state.report = null;
  buildNav();
  const grid = $('sectorCards');
  grid.innerHTML = '';
  state.sectors.forEach(s => {
    const mine = sectorReports(s.id);
    const latest = mine.slice().sort((a, b) => b.period_key - a.period_key)[0];
    const periods = new Set(mine.map(r => r.period));
    const card = el('button', 'scard'); card.type = 'button';
    const top = el('div', 'sc-top');
    top.appendChild(el('span', 'sc-code', s.code || s.id.slice(0,3).toUpperCase()));
    top.appendChild(el('span', 'sc-q', latest ? (latest.period + ' ' + t('latest')) : t('no_reports_yet')));
    card.appendChild(top);
    card.appendChild(el('b', null, sectorName(s)));
    const cov = sectorCoverage(s);
    card.appendChild(el('span', 'sc-cov', (state.lang === 'cn' ? (s.name_en || '') : (s.name_cn || '')) + (cov ? ' · ' + cov : '')));
    const bd = el('div', 'sc-badges');
    if (latest){
      Array.from(periods).sort((a, b) => periodKey(b) - periodKey(a)).slice(0, 4).forEach(p => bd.appendChild(el('span', 'bdg', p)));
    } else bd.appendChild(el('span', 'bdg', t('coming_soon')));
    card.appendChild(bd);
    card.appendChild(el('span', 'sc-go', (mine.length ? (t('enter') + ' · ' + nReports(mine.length) + ' · ' + nQuarters(periods.size)) : t('upload_first')) + ' ›'));
    card.addEventListener('click', () => nav(hashSector(s.id)));
    grid.appendChild(card);
  });
  const ph = el('button', 'scard ph'); ph.type = 'button';
  ph.appendChild(el('div', 'plus', '+'));
  ph.appendChild(el('b', null, t('manage_sectors')));
  ph.addEventListener('click', openSectorManager);
  grid.appendChild(ph);
  renderRecent(langReports().sort(byUploaded).slice(0, 6));
  document.title = t('dash_title') + ' | Junson Capital';
}
function renderRecent(list){
  const box = $('dashRecent');
  box.innerHTML = '';
  if (!list.length){ box.appendChild(el('div', 'empty', t('no_reports_yet'))); return; }
  list.forEach(m => {
    const s = sectorById(m.sector);
    const c = el('button', 'more-item'); c.type = 'button';
    const k = el('span', 'mi-k');
    k.appendChild(el('span', 'bdg period', m.period));
    k.appendChild(document.createTextNode((s ? sectorName(s) : m.sector)));
    c.appendChild(k);
    c.appendChild(el('span', 'mi-t', m.title));
    c.appendChild(el('span', 'mi-d', fmtDate(m.uploaded_at) + ' · ' + (m.source_name || '')));
    c.addEventListener('click', () => nav(hashReport(m.id)));
    box.appendChild(c);
  });
}

/* ---------------------------------------------------------------- sector → latest report */
function openSector(id){
  const s = sectorById(id);
  if (!s){ nav('#/'); return; }
  const latest = latestOf(sectorReports(id));
  if (latest){ history.replaceState(null, '', hashReport(latest.id)); renderReport(latest.id, null); return; }
  renderEmpty(s, null);
}
function renderEmpty(s, period){
  state.sectorId = s.id; state.reportId = null; state.report = null; state.exhibits = [];
  showView('art');
  buildNav();
  $('crumbPath').textContent = sectorName(s);
  buildPickers(s, null);
  buildSegs(null, s);
  $('titleRow').hidden = true; $('toolbar').hidden = true; $('docGrid').hidden = true;
  $('emptyReader').hidden = false;
  const n = $('emptyNotice'); n.innerHTML = '';
  n.appendChild(el('b', null, period ? t('no_report_period', {sector: sectorName(s), period}) : t('no_report_lang', {sector: sectorName(s)})));
  const alt = $('emptyAlt');
  const other = latestOf(sectorReports(s.id, otherLang()).filter(r => !period || r.period === period));
  const latestMine = period ? latestOf(sectorReports(s.id)) : null;
  alt.hidden = !(other || latestMine);
  if (latestMine){ alt.textContent = t('open_latest') + ' (' + latestMine.period + ')'; alt.onclick = () => nav(hashReport(latestMine.id)); }
  else if (other){ alt.textContent = t('open_other_lang'); alt.onclick = () => { setLang(otherLang()); }; }
  $('emptyUpload').onclick = () => openUpload(s.id);
  document.title = sectorName(s) + ' — AID Research | Junson Capital';
}

/* ---------------------------------------------------------------- report reader */
async function renderReport(id, anchor){
  let data;
  try { data = await api('/api/reports/' + encodeURIComponent(id)); }
  catch (e) { toast(e.message); nav('#/'); return; }
  const meta = data.meta, content = data.content;
  state.docLang = meta.language;
  try { localStorage.setItem('aid_doclang', state.docLang); } catch (e) {}
  state.report = data; state.reportId = id; state.sectorId = meta.sector; state.exhibits = [];
  showView('art');
  buildNav();
  const s = sectorById(meta.sector) || {id: meta.sector, name_en: meta.sector};
  $('titleRow').hidden = false; $('toolbar').hidden = false; $('docGrid').hidden = false; $('emptyReader').hidden = true;

  // crumbs + pickers
  const cp = $('crumbPath'); cp.innerHTML = '';
  cp.appendChild(document.createTextNode(sectorName(s)));
  if (s.region){ cp.appendChild(el('i', null, '|')); cp.appendChild(document.createTextNode(s.region)); }
  buildPickers(s, meta);
  buildSegs(meta, s);

  // title / meta / tags
  $('docTitle').textContent = meta.title;
  $('qBadge').textContent = meta.period;
  const dm = $('docMeta'); dm.innerHTML = '';
  const add = (txt, bold) => { const sp = el('span'); if (bold) sp.appendChild(el('b', null, txt)); else sp.textContent = txt; dm.appendChild(sp); };
  const sep = () => dm.appendChild(el('span', 'sep', '|'));
  if (meta.publish_date){ add(t('published') + ' ' + meta.publish_date, true); sep(); }
  if (meta.masthead){ add(meta.masthead); sep(); }
  add(t('uploaded') + ' ' + fmtDate(meta.uploaded_at)); sep();
  add(t('source_file') + ': ' + (meta.source_name || '—'));
  const tr = $('tagRow'); tr.innerHTML = '';
  tr.appendChild(el('span', 'lbl', t('keywords')));
  (meta.keywords || []).forEach(k => tr.appendChild(el('span', 'tag', k)));
  document.querySelectorAll('.doc-sub').forEach(n => n.remove());
  if (meta.subtitle) tr.parentNode.insertBefore(el('div', 'doc-sub', meta.subtitle), tr);

  // body
  const art = $('art'); art.innerHTML = '';
  headingCounter = 0;
  renderBlocks(content.blocks, art);
  renderExhibitIndex(content, art);
  buildRail(content.blocks);
  buildSideExhibits(content);
  $('exBtnLabel').textContent = t('exhibits') + (state.exhibits.length ? ' (' + state.exhibits.length + ')' : '');
  startSpy();
  doSearch();
  document.title = meta.title + ' ' + meta.period + ' — AID Research | Junson Capital';
  if (anchor) requestAnimationFrame(() => { const n = document.getElementById(anchor); if (n) n.scrollIntoView(); });
}
function opt(v, label){ const o = el('option', null, label); o.value = v; return o; }
function buildSegs(meta, s){
  const sector = meta ? meta.sector : s.id;
  const period = meta ? meta.period : null;
  // full / summary: flips to the other edition of the same sector, quarter and language
  const otherNature = meta && meta.nature === 'summary' ? 'full' : 'summary';
  const typeTarget = period ? findReport(sector, period, state.docLang, otherNature) : null;
  setToggle('typeToggle', !!(meta && meta.nature === 'summary'), !typeTarget);
  $('typeToggle').onclick = () => { if (typeTarget) nav(hashReport(typeTarget.id)); };
  // EN / 中文: flips the report language
  const other = otherLang();
  const langAvailable = period
    ? !!(findReport(sector, period, other, meta.nature) || findReport(sector, period, other, 'full'))
    : sectorReports(sector, other).length > 0;
  setToggle('docLangToggle', state.docLang === 'cn', !langAvailable);
  $('docLangToggle').onclick = () => { if (langAvailable) setDocLang(other); };
}
function buildPickers(s, meta){
  const mine = sectorReports(s.id);
  const years = Array.from(new Set(mine.map(r => r.year))).sort((a, b) => b - a);
  const py = $('pYear'), pq = $('pQuarter');
  py.innerHTML = ''; pq.innerHTML = '';
  if (!years.length){ py.appendChild(opt('', '—')); pq.appendChild(opt('', '—')); py.disabled = pq.disabled = true; $('pickCount').textContent = ''; return; }
  py.disabled = pq.disabled = false;
  years.forEach(y => py.appendChild(opt(String(y), String(y))));
  const curYear = meta ? meta.year : years[0];
  py.value = String(curYear);
  const fillQ = (year) => {
    pq.innerHTML = '';
    const qs = Array.from(new Set(mine.filter(r => r.year === year).map(r => r.quarter))).sort((a, b) => b - a);
    qs.forEach(q => pq.appendChild(opt(String(q), 'Q' + q + ' · ' + q + 'Q' + year)));
    return qs;
  };
  const qs = fillQ(curYear);
  pq.value = String(meta ? meta.quarter : qs[0]);
  $('pickCount').textContent = nReports(mine.length);
  py.onchange = () => {
    const y = +py.value; const q2 = fillQ(y); pq.value = String(q2[0]);
    const r = latestOf(mine.filter(x => x.year === y && x.quarter === q2[0]));
    if (r) nav(hashReport(r.id));
  };
  pq.onchange = () => {
    const r = latestOf(mine.filter(x => x.year === +py.value && x.quarter === +pq.value));
    if (r) nav(hashReport(r.id));
  };
}
function imgUrl(name){ return '/api/reports/' + encodeURIComponent(state.reportId) + '/images/' + encodeURIComponent(name); }
const CAPTION_LABEL_RE = /^\s*((?:exhibit|figure|fig\.?|chart|table|graph)\s*\d+[A-Za-z]?|(?:图表|图|表|附图|附表)\s*\d+)/i;
function exhibitLabel(b){
  const m = CAPTION_LABEL_RE.exec(b.caption || '');
  if (m) return m[1].replace(/\s+/g, ' ').trim();
  return (b.type === 'table' ? t('table') : t('exhibit')) + ' ' + b.exhibit;
}
function indexLabel(e){ return e.label || ((e.type === 'table' ? t('table') : t('exhibit')) + ' ' + e.n); }
function captionText(b){
  return (b.caption || '').replace(/^\s*(?:(?:exhibit|figure|fig\.?|chart|table|graph)\s*\d+[A-Za-z]?|(?:图表|图|表|附图|附表)\s*\d+)\s*[:：.．\-—–]?\s*/i, '');
}
let headingCounter = 0;
function renderBlocks(blocks, target){
  blocks.forEach(b => {
    if (b.type === 'heading'){
      const tag = b.level === 1 ? 'h2' : (b.level === 2 ? 'h3' : 'h4');
      const h = el(tag, 'h' + b.level, b.text);
      h.id = 'h-' + (++headingCounter); h.dataset.anchor = h.id;
      target.appendChild(h);
    } else if (b.type === 'paragraph'){
      const p = el('p', b.style === 'note' ? 'note' : (b.style === 'caption' ? 'caption' : (b.style === 'lede' ? 'lede' : null)));
      p.innerHTML = b.html || escapeHtml(b.text || '');
      target.appendChild(p);
    } else if (b.type === 'list'){
      const l = el(b.ordered ? 'ol' : 'ul');
      b.items.forEach(it => { const li = el('li'); li.innerHTML = it; l.appendChild(li); });
      target.appendChild(l);
    } else if (b.type === 'callout'){
      const c = el('div', 'callout'); c.innerHTML = escapeHtml(b.text).replace(/\n/g, '<br>'); target.appendChild(c);
    } else if (b.type === 'layout'){
      const wrap = el('div', b.cols === 2 ? 'pair' : 'gridwrap');
      b.cells.forEach(cell => { const cd = el('div'); renderBlocks(cell, cd); wrap.appendChild(cd); });
      target.appendChild(wrap);
    } else if (b.type === 'image'){
      target.appendChild(renderFigure(b));
    } else if (b.type === 'table'){
      target.appendChild(renderTable(b));
    } else if (b.type === 'pagebreak'){
      target.appendChild(el('hr', 'pb'));
    }
  });
}
function pushExhibit(b, cap){
  state.exhibits.push({block: b, src: b.src || null, caption: cap, label: exhibitLabel(b), note: b.note || '', anchor: b.anchor || ('ex-' + b.exhibit)});
  return state.exhibits.length - 1;
}
function renderFigure(b){
  const fig = el('figure', 'fig'); fig.id = b.anchor || ('ex-' + b.exhibit);
  const head = el('div', 'fig-head');
  head.appendChild(el('span', 'fig-no', exhibitLabel(b)));
  const cap = captionText(b);
  if (cap) head.appendChild(el('span', 'fig-cap', cap));
  fig.appendChild(head);
  const idx = pushExhibit(b, cap);
  if (b.unsupported){
    fig.appendChild(el('div', 'unsupported', t('unsupported_img')));
  } else {
    const im = document.createElement('img');
    im.loading = 'lazy'; im.src = imgUrl(b.src); im.alt = cap || exhibitLabel(b);
    if (b.width && b.width < 900) im.style.maxWidth = Math.round(b.width) + 'px';
    im.addEventListener('click', () => openLb(idx));
    fig.appendChild(im);
  }
  if (b.note) fig.appendChild(el('div', 'fig-note', b.note));
  return fig;
}
function renderTable(b){
  const frag = document.createDocumentFragment();
  const head = el('div', 'tbl-head'); head.id = b.anchor || ('ex-' + b.exhibit);
  head.appendChild(el('span', 'fig-no', exhibitLabel(b)));
  const cap = captionText(b);
  if (cap) head.appendChild(el('span', 'fig-cap', cap));
  const idx = pushExhibit(b, cap);
  if (b.src){
    const z = el('button', 'tbl-zoom', '⤢'); z.type = 'button'; z.title = t('exhibits');
    z.addEventListener('click', () => openLb(idx));
    head.appendChild(z);
  }
  frag.appendChild(head);
  const wrap = el('div', 'tbl-wrap');
  const tb = el('table', 'data');
  const rows = b.rows || [];
  if (rows.length && b.header !== false){
    const thead = el('thead'); const trh = el('tr');
    rows[0].forEach(c => trh.appendChild(el('th', null, c)));
    thead.appendChild(trh); tb.appendChild(thead);
  }
  const tbody = el('tbody');
  rows.slice(b.header === false ? 0 : 1).forEach(r => {
    const tr = el('tr');
    r.forEach(c => { const td = el('td'); td.innerHTML = escapeHtml(c).replace(/\n/g, '<br>'); tr.appendChild(td); });
    tbody.appendChild(tr);
  });
  tb.appendChild(tbody); wrap.appendChild(tb); frag.appendChild(wrap);
  if (b.note) frag.appendChild(el('p', 'note', b.note));
  return frag;
}
function exhibitIndexOf(e){ return state.exhibits.findIndex(x => x.block.exhibit === e.n); }
function renderExhibitIndex(content, target){
  const exs = content.exhibits || [];
  if (!exs.length) return;
  const sec = el('section', 'exindex'); sec.id = 'exhibit-index';
  sec.appendChild(el('h2', null, t('exhibit_index')));
  sec.appendChild(el('p', 'sub', t('exhibit_index_sub') + ' · ' + exs.length));
  const grid = el('div', 'ex-grid');
  exs.forEach(e => {
    const item = el('div', 'ex-item');
    if (e.src){
      const im = document.createElement('img'); im.className = 'thumb'; im.loading = 'lazy'; im.src = imgUrl(e.src); im.alt = e.caption;
      im.style.cursor = 'zoom-in';
      im.addEventListener('click', () => openLb(exhibitIndexOf(e)));
      item.appendChild(im);
    } else item.appendChild(el('div', 'thumb tbl', '▦'));
    const d = el('div');
    d.appendChild(el('b', null, indexLabel(e) + ' · '));
    d.appendChild(document.createTextNode(e.caption || '—'));
    item.appendChild(d);
    const links = el('div', 'ex-links');
    const a = el('a', null, t('view_in_text') + ' ↑'); a.href = '#' + e.anchor;
    a.addEventListener('click', ev => { ev.preventDefault(); const n = document.getElementById(e.anchor); if (n) n.scrollIntoView({block:'center'}); });
    links.appendChild(a);
    item.appendChild(links);
    grid.appendChild(item);
  });
  sec.appendChild(grid);
  target.appendChild(sec);
}
function flattenHeadings(blocks, out){
  blocks.forEach(b => {
    if (b.type === 'heading') out.push(b);
    else if (b.type === 'layout') b.cells.forEach(c => flattenHeadings(c, out));
  });
  return out;
}
function buildRail(blocks){
  const tree = $('railTree'); tree.innerHTML = '';
  let hn = 0;
  flattenHeadings(blocks, []).forEach(b => {
    hn++;
    const id = 'h-' + hn;
    const a = el('a', 'l' + Math.min(3, b.level), b.text);
    a.href = '#' + id; a.dataset.anchor = id;
    a.addEventListener('click', ev => {
      ev.preventDefault();
      const n = document.getElementById(id); if (n) n.scrollIntoView();
      history.replaceState(null, '', hashReport(state.reportId, id));
      if (window.innerWidth <= 820) $('rail').classList.remove('open');
    });
    tree.appendChild(a);
  });
  if (state.exhibits.length){
    const a = el('a', 'l1', t('exhibit_index') + ' (' + state.exhibits.length + ')');
    a.href = '#exhibit-index'; a.dataset.anchor = 'exhibit-index';
    a.addEventListener('click', ev => { ev.preventDefault(); const n = $('exhibit-index'); if (n) n.scrollIntoView(); });
    tree.appendChild(a);
  }
  if (!hn && !state.exhibits.length) tree.appendChild(el('div', 'nores', '—'));
}
function buildSideExhibits(content){
  const se = $('sideExhibits'); se.innerHTML = '';
  (content.exhibits || []).forEach(e => {
    const a = el('a'); a.href = '#' + e.anchor;
    a.appendChild(el('b', null, indexLabel(e)));
    a.appendChild(document.createTextNode(e.caption || '—'));
    a.addEventListener('click', ev => {
      ev.preventDefault();
      const i = exhibitIndexOf(e);
      if (i >= 0 && state.exhibits[i].src) openLb(i);
      else { const n = document.getElementById(e.anchor); if (n) n.scrollIntoView({block:'center'}); }
    });
    se.appendChild(a);
  });
  if (!(content.exhibits || []).length) se.appendChild(el('div', 'nores', t('no_exhibits')));
}
let spy = null;
function startSpy(){
  if (spy) spy.disconnect();
  const links = {};
  document.querySelectorAll('#railTree a').forEach(a => { links[a.dataset.anchor] = a; });
  let current = null;
  spy = new IntersectionObserver(entries => {
    entries.forEach(en => {
      if (en.isIntersecting && links[en.target.id]){
        if (current) current.classList.remove('now');
        current = links[en.target.id]; current.classList.add('now');
      }
    });
  }, {rootMargin: '-15% 0px -70% 0px'});
  document.querySelectorAll('#art h2, #art h3, #art h4, #art section.exindex').forEach(h => { if (h.id) spy.observe(h); });
}

/* ---------------------------------------------------------------- search (filters the contents rail) */
function doSearch(){
  const q = $('q').value.trim().toLowerCase();
  if (state.view !== 'art') return null;
  const links = document.querySelectorAll('#railTree a');
  let first = null;
  links.forEach(a => {
    const hit = !q || a.textContent.toLowerCase().indexOf(q) >= 0;
    a.style.display = hit ? '' : 'none';
    if (hit && q && !first) first = a;
  });
  const old = $('railNoRes'); if (old) old.remove();
  if (q && !first){ const n = el('div', 'nores', t('nores', {q})); n.id = 'railNoRes'; $('railTree').appendChild(n); }
  return first;
}

/* ---------------------------------------------------------------- lightbox with zoom + pan + arrows */
const lbImg = () => $('lbImg');
function applyZoom(){
  const z = state.zoom;
  lbImg().style.transform = 'translate(' + z.tx + 'px,' + z.ty + 'px) scale(' + z.s + ')';
  $('lbZoom').textContent = Math.round(z.s * 100) + '%';
}
function fitImage(){
  const stage = $('lbStage').getBoundingClientRect();
  const im = lbImg();
  const iw = im.naturalWidth || 1, ih = im.naturalHeight || 1;
  const pad = 70;
  const s = Math.min((stage.width - pad * 2) / iw, (stage.height - 20) / ih, 1.5);
  state.zoom = {s, tx: (stage.width - iw * s) / 2, ty: (stage.height - ih * s) / 2, fit: s};
  applyZoom();
}
function zoomAt(factor, cx, cy){
  const z = state.zoom;
  const s2 = Math.min(8, Math.max(z.fit * 0.25, z.s * factor));
  if (cx === undefined){ const r = $('lbStage').getBoundingClientRect(); cx = r.width / 2; cy = r.height / 2; }
  z.tx = cx - (cx - z.tx) * (s2 / z.s);
  z.ty = cy - (cy - z.ty) * (s2 / z.s);
  z.s = s2;
  applyZoom();
}
function viewable(){ return state.exhibits.map((e, i) => e.src ? i : -1).filter(i => i >= 0); }
function openLb(i){
  const v = viewable();
  if (!v.length) { toast(t('no_exhibits')); return; }
  if (i === undefined || i < 0) i = v[0];
  if (v.indexOf(i) < 0){ const next = v.find(x => x > i); i = next !== undefined ? next : v[0]; }
  state.lbIndex = i;
  const ex = state.exhibits[i];
  const im = lbImg();
  im.style.transform = 'scale(0)';
  im.onload = fitImage;
  im.src = imgUrl(ex.src); im.alt = ex.caption || '';
  if (im.complete && im.naturalWidth) fitImage();
  $('lbCap').textContent = ex.label + (ex.caption ? ' · ' + ex.caption : '') + (ex.note ? '  —  ' + ex.note : '');
  $('lbCount').textContent = t('lb_of', {i: v.indexOf(i) + 1, n: v.length});
  $('lb').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function stepLb(dir){
  const v = viewable();
  if (!v.length) return;
  const pos = v.indexOf(state.lbIndex);
  openLb(v[(pos + dir + v.length) % v.length]);
}
function closeLb(){ $('lb').classList.remove('open'); unlockScroll(); }
function unlockScroll(){
  if (!$('lb').classList.contains('open') && !document.querySelector('.overlay.open')) document.body.style.overflow = '';
}
function wireLightbox(){
  const stage = $('lbStage');
  stage.addEventListener('wheel', e => {
    e.preventDefault();
    const r = stage.getBoundingClientRect();
    zoomAt(e.deltaY < 0 ? 1.15 : 1 / 1.15, e.clientX - r.left, e.clientY - r.top);
  }, {passive: false});
  let drag = null;
  stage.addEventListener('pointerdown', e => {
    if (e.button !== 0 || e.target.classList.contains('lb-arrow')) return;
    drag = {x: e.clientX, y: e.clientY, tx: state.zoom.tx, ty: state.zoom.ty, moved: false};
    stage.classList.add('dragging'); stage.setPointerCapture(e.pointerId);
  });
  stage.addEventListener('pointermove', e => {
    if (!drag) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 3) drag.moved = true;
    state.zoom.tx = drag.tx + dx; state.zoom.ty = drag.ty + dy; applyZoom();
  });
  const end = e => {
    if (!drag) return;
    const moved = drag.moved; drag = null; stage.classList.remove('dragging');
    if (!moved && e.target === stage) closeLb();
  };
  stage.addEventListener('pointerup', end); stage.addEventListener('pointercancel', end);
  stage.addEventListener('dblclick', e => {
    if (e.target.classList.contains('lb-arrow')) return;
    const r = stage.getBoundingClientRect();
    if (state.zoom.s > state.zoom.fit * 1.05) fitImage(); else zoomAt(2, e.clientX - r.left, e.clientY - r.top);
  });
  $('lbZoomIn').addEventListener('click', () => zoomAt(1.25));
  $('lbZoomOut').addEventListener('click', () => zoomAt(1 / 1.25));
  $('lbFit').addEventListener('click', fitImage);
  $('lbPrev').addEventListener('click', e => { e.stopPropagation(); stepLb(-1); });
  $('lbNext').addEventListener('click', e => { e.stopPropagation(); stepLb(1); });
  $('lbClose').addEventListener('click', closeLb);
  $('lbGoto').addEventListener('click', () => {
    const ex = state.exhibits[state.lbIndex];
    closeLb();
    if (ex){ const n = document.getElementById(ex.anchor); if (n) n.scrollIntoView({block:'center'}); }
  });
  window.addEventListener('resize', () => { if ($('lb').classList.contains('open')) fitImage(); });
}

/* ---------------------------------------------------------------- header hide / show on scroll */
function wireHeader(){
  let lastY = window.scrollY, hidden = false;
  const hdr = $('hdr');
  const setHidden = (h) => {
    if (h === hidden) return;
    hidden = h;
    hdr.classList.toggle('hide', h);
    document.documentElement.classList.toggle('hdr-hidden', h);
  };
  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    if (y < 80) setHidden(false);
    else if (y > lastY + 6) setHidden(true);
    else if (y < lastY - 6) setHidden(false);
    lastY = y;
  }, {passive: true});
}

/* ---------------------------------------------------------------- upload / edit */
function fillSelect(sel, opts, cur){ sel.innerHTML = ''; opts.forEach(o => sel.appendChild(opt(o[0], o[1]))); if (cur !== undefined) sel.value = cur; }
function openUpload(sectorId, editMeta){
  state.editing = editMeta || null;
  const isEdit = !!editMeta;
  $('upTitle').textContent = isEdit ? t('edit_report') : t('upload_report');
  $('drop').hidden = isEdit;
  $('upFile').value = ''; $('dropFile').textContent = '';
  fillSelect($('upSector'), state.sectors.map(s => [s.id, sectorName(s)]), isEdit ? editMeta.sector : (sectorId || (state.sectors[0] && state.sectors[0].id)));
  fillSelect($('upQuarter'), [1,2,3,4].map(q => [String(q), 'Q' + q]), String(isEdit ? editMeta.quarter : state.meta.current_quarter));
  fillSelect($('upNature'), [['full', t('full')], ['summary', t('summary')]], isEdit ? editMeta.nature : 'full');
  fillSelect($('upLang'), [['en', t('en')], ['cn', t('cn')], ['', t('auto_detect')]], isEdit ? editMeta.language : state.docLang);
  $('upYear').value = isEdit ? editMeta.year : state.meta.current_year;
  $('upTitleIn').value = isEdit ? editMeta.title : '';
  $('upKeywords').value = isEdit ? (editMeta.keywords || []).join(', ') : '';
  $('upSubmit').textContent = isEdit ? t('save') : t('upload');
  $('upSubmit').disabled = false;
  const msg = $('upMsg'); msg.textContent = ''; msg.className = 'form-msg';
  $('upOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeUpload(){ $('upOverlay').classList.remove('open'); unlockScroll(); }
async function submitUpload(ev){
  ev.preventDefault();
  const msg = $('upMsg');
  const btn = $('upSubmit');
  const sector = $('upSector').value, year = $('upYear').value, quarter = $('upQuarter').value;
  const language = $('upLang').value, nature = $('upNature').value;
  const title = $('upTitleIn').value.trim(), keywords = $('upKeywords').value.trim();
  try {
    btn.disabled = true;
    if (state.editing){
      msg.className = 'form-msg'; msg.textContent = '…';
      const m = await api('/api/reports/' + encodeURIComponent(state.editing.id), {
        method: 'PUT', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({sector, year: +year, quarter: +quarter, language, nature, title, keywords}),
      });
      closeUpload(); toast(t('save')); await loadAll();
      nav(hashReport(m.id)); route();
      return;
    }
    const f = $('upFile').files[0];
    if (!f){ msg.className = 'form-msg err'; msg.textContent = t('choose_file'); btn.disabled = false; return; }
    msg.className = 'form-msg'; msg.textContent = t('uploading');
    const fd = new FormData();
    fd.append('file', f); fd.append('sector', sector); fd.append('year', year); fd.append('quarter', quarter);
    fd.append('nature', nature); fd.append('language', language); fd.append('title', title); fd.append('keywords', keywords);
    const m = await api('/api/upload', {method: 'POST', body: fd});
    closeUpload(); toast(t('upload_ok'));
    await loadAll();
    nav(hashReport(m.id)); route();
  } catch (e) {
    msg.className = 'form-msg err'; msg.textContent = e.message;
  } finally { btn.disabled = false; }
}
function wireUpload(){
  const drop = $('drop'), file = $('upFile');
  file.addEventListener('change', () => { $('dropFile').textContent = file.files[0] ? file.files[0].name : ''; });
  ['dragenter', 'dragover'].forEach(evn => drop.addEventListener(evn, e => { e.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(evn => drop.addEventListener(evn, e => { e.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', e => { if (e.dataTransfer.files.length){ file.files = e.dataTransfer.files; $('dropFile').textContent = file.files[0].name; } });
  $('upForm').addEventListener('submit', submitUpload);
  $('upClose').addEventListener('click', closeUpload);
  $('upCancel').addEventListener('click', closeUpload);
  $('upOverlay').addEventListener('click', e => { if (e.target === $('upOverlay')) closeUpload(); });
  $('uploadBtn').addEventListener('click', () => openUpload(state.sectorId));
}

/* ---------------------------------------------------------------- sector manager (add / edit / remove) */
function openSectorManager(editSector){
  renderSectorList();
  fillSectorForm(editSector || null);
  $('secMsg').textContent = ''; $('secMsg').className = 'form-msg';
  $('secOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeSectorManager(){ $('secOverlay').classList.remove('open'); unlockScroll(); }
function fillSectorForm(s){
  $('sId').value = s ? s.id : '';
  $('secFormTitle').textContent = s ? t('edit_sector') + ' · ' + sectorName(s) : t('add_sector');
  $('sNameEn').value = s ? (s.name_en || '') : '';
  $('sNameCn').value = s ? (s.name_cn || '') : '';
  $('sCode').value = s ? (s.code || '') : '';
  $('sRegion').value = s ? (s.region || '') : '';
  $('sCovEn').value = s ? (s.coverage_en || []).join(', ') : '';
  $('sCovCn').value = s ? (s.coverage_cn || []).join(', ') : '';
  $('secSubmit').textContent = s ? t('save') : t('add_sector');
  $('secCancelEdit').hidden = !s;
}
function renderSectorList(){
  const list = $('secList'); list.innerHTML = '';
  const saveOrder = async () => {
    const ids = Array.from(list.querySelectorAll('.sec-row')).map(r => r.dataset.id);
    try {
      await api('/api/sectors-order', {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({order: ids})});
      await loadAll(); renderSectorList(); if (state.view === 'dash') renderDash(); else buildNav();
      toast(t('order_saved'));
    } catch (e) { toast(e.message); renderSectorList(); }
  };
  let dragging = null;
  const clearMarks = () => list.querySelectorAll('.sec-row').forEach(r => r.classList.remove('drop-before', 'drop-after'));
  state.sectors.forEach((s, idx) => {
    const row = el('div', 'sec-row');
    row.dataset.id = s.id; row.draggable = true;
    const grip = el('span', 'grip', '⋮⋮'); grip.title = t('drag_hint');
    row.appendChild(grip);
    row.addEventListener('dragstart', e => {
      dragging = row; row.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      try { e.dataTransfer.setData('text/plain', s.id); } catch (err) {}
    });
    row.addEventListener('dragend', () => { row.classList.remove('dragging'); clearMarks(); dragging = null; });
    row.addEventListener('dragover', e => {
      if (!dragging || dragging === row) return;
      e.preventDefault(); e.dataTransfer.dropEffect = 'move';
      const r = row.getBoundingClientRect();
      const before = (e.clientY - r.top) < r.height / 2;
      clearMarks();
      row.classList.add(before ? 'drop-before' : 'drop-after');
    });
    row.addEventListener('dragleave', () => row.classList.remove('drop-before', 'drop-after'));
    row.addEventListener('drop', e => {
      if (!dragging || dragging === row) return;
      e.preventDefault();
      const r = row.getBoundingClientRect();
      const before = (e.clientY - r.top) < r.height / 2;
      clearMarks();
      list.insertBefore(dragging, before ? row : row.nextSibling);
      dragging.classList.remove('dragging'); dragging = null;
      saveOrder();
    });
    row.appendChild(el('span', 'sc-code', s.code));
    const nm = el('span', 'nm'); nm.textContent = s.name_en; nm.appendChild(el('span', null, s.name_cn + (s.report_count ? ' · ' + s.report_count + ' ' + t('reports') : '')));
    const cov = sectorCoverage(s); if (cov) nm.appendChild(el('span', 'cov', cov));
    row.appendChild(nm);
    const ed = el('button', null, t('edit')); ed.type = 'button';
    ed.addEventListener('click', () => { fillSectorForm(s); $('sNameEn').focus(); });
    row.appendChild(ed);
    const rm = el('button', 'rm', t('remove')); rm.type = 'button';
    rm.disabled = !!s.report_count; if (s.report_count) rm.title = t('sector_has_reports');
    rm.addEventListener('click', async () => {
      if (!confirm(t('confirm_remove_sector'))) return;
      try { await api('/api/sectors/' + encodeURIComponent(s.id), {method: 'DELETE'}); await loadAll(); renderSectorList(); if (state.view === 'dash') renderDash(); }
      catch (e) { toast(e.message); }
    });
    row.appendChild(rm);
    list.appendChild(row);
  });
}
function wireSectorManager(){
  $('manageSectorsBtn').addEventListener('click', openSectorManager);
  $('secClose').addEventListener('click', closeSectorManager);
  $('secOverlay').addEventListener('click', e => { if (e.target === $('secOverlay')) closeSectorManager(); });
  $('secCancelEdit').addEventListener('click', () => fillSectorForm(null));
  $('secEditBtn').addEventListener('click', () => { const s = sectorById(state.sectorId); if (s) openSectorManager(s); });
  $('secForm').addEventListener('submit', async ev => {
    ev.preventDefault();
    const split = v => v.split(/[,，;；/／]/).map(x => x.trim()).filter(Boolean);
    const covEn = split($('sCovEn').value), covCn = split($('sCovCn').value);
    const payload = {
      name_en: $('sNameEn').value.trim(), name_cn: $('sNameCn').value.trim(), code: $('sCode').value.trim().toUpperCase(),
      region: $('sRegion').value.trim(), coverage_en: covEn.length ? covEn : covCn, coverage_cn: covCn.length ? covCn : covEn,
    };
    const id = $('sId').value;
    try {
      if (id) await api('/api/sectors/' + encodeURIComponent(id), {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
      else await api('/api/sectors', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
      $('secMsg').className = 'form-msg ok'; $('secMsg').textContent = t('sector_saved');
      await loadAll(); renderSectorList(); fillSectorForm(null);
      if (state.view === 'dash') renderDash(); else route();
    } catch (e) { $('secMsg').className = 'form-msg err'; $('secMsg').textContent = e.message; }
  });
}

/* ---------------------------------------------------------------- views + routing */
function showView(v){
  state.view = v;
  $('view-dash').hidden = v !== 'dash';
  $('view-art').hidden = v !== 'art';
  $('searchWrap').style.visibility = v === 'dash' ? 'hidden' : '';
}
function parseHash(){
  const h = decodeURIComponent(location.hash.replace(/^#\/?/, ''));
  if (!h) return {view: 'dash'};
  const p = h.split('/');
  if (p[0] === 's' && p[1]) return {view: 'sector', id: p[1]};
  if (p[0] === 'r' && p[1]) return {view: 'art', id: p[1], anchor: p.slice(2).join('/') || null};
  return {view: 'dash'};
}
async function route(){
  const h = parseHash();
  try {
    if (h.view === 'dash') renderDash();
    else if (h.view === 'sector') openSector(h.id);
    else if (h.view === 'art'){
      if (state.view === 'art' && state.reportId === h.id && h.anchor){ const n = document.getElementById(h.anchor); if (n) n.scrollIntoView(); return; }
      await renderReport(h.id, h.anchor);
    }
  } catch (e) { toast(e.message); console.error(e); }
}

/* ---------------------------------------------------------------- wire up */
function wire(){
  $('brandBtn').addEventListener('click', () => nav('#/'));
  $('backBtn').addEventListener('click', () => nav('#/'));
  $('langToggle').addEventListener('click', () => setLang(state.lang === 'cn' ? 'en' : 'cn'));
  $('logoutBtn').addEventListener('click', async () => { try { await fetch('/api/logout', {method: 'POST'}); } catch (e) {} location.href = '/login.html'; });
  $('q').addEventListener('input', doSearch);
  const jump = () => { const f = doSearch(); if (f) f.click(); };
  $('q').addEventListener('keydown', e => { if (e.key === 'Enter') jump(); });
  $('qbtn').addEventListener('click', jump);
  $('exBtn').addEventListener('click', () => openLb());
  $('tocBtn').addEventListener('click', () => $('rail').classList.toggle('open'));
  $('topBtn2').addEventListener('click', () => window.scrollTo({top: 0}));
  $('copyBtn').addEventListener('click', () => {
    const url = location.href;
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(() => toast(t('link_copied')), () => toast(url));
    else toast(url);
  });
  $('dlBtn').addEventListener('click', () => { if (state.reportId) window.open('/api/reports/' + encodeURIComponent(state.reportId) + '/source', '_blank'); });
  $('printBtn').addEventListener('click', () => window.print());
  $('editBtn').addEventListener('click', () => { if (state.report) openUpload(state.sectorId, state.report.meta); });
  $('delBtn').addEventListener('click', async () => {
    if (!state.report || !confirm(t('confirm_delete'))) return;
    try { await api('/api/reports/' + encodeURIComponent(state.reportId), {method: 'DELETE'}); toast(t('deleted')); await loadAll(); nav(hashSector(state.sectorId)); route(); }
    catch (e) { toast(e.message); }
  });
  document.addEventListener('keydown', e => {
    const lbOpen = $('lb').classList.contains('open');
    if (e.key === 'Escape'){ if (lbOpen) closeLb(); else { closeUpload(); closeSectorManager(); } }
    if (lbOpen && e.key === 'ArrowLeft') stepLb(-1);
    if (lbOpen && e.key === 'ArrowRight') stepLb(1);
    if (lbOpen && (e.key === '+' || e.key === '=')) zoomAt(1.25);
    if (lbOpen && e.key === '-') zoomAt(1 / 1.25);
    if (lbOpen && e.key === '0') fitImage();
  });
  wireLightbox(); wireUpload(); wireSectorManager(); wireHeader();
  window.addEventListener('hashchange', () => route());
}

async function init(){
  try { const l = localStorage.getItem('aid_lang'); if (l === 'en' || l === 'cn') state.lang = l; } catch (e) {}
  state.docLang = state.lang;
  try { const d = localStorage.getItem('aid_doclang'); if (d === 'en' || d === 'cn') state.docLang = d; } catch (e) {}
  applyI18n();
  wire();
  try { await loadAll(); }
  catch (e) { toast(e.message); }
  route();
}
init();
})();
