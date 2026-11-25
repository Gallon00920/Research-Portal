/* Junson Capital — AID Research Panel (frontend)
   Routes:  #/                 research dashboard
            #/s/<sector>       opens the latest report of that sector in the current language
            #/portfolio        portfolio management dashboard (the same page for the portfolio funds)
            #/portfolio/s/<id> opens the latest report of that fund
            #/macro[/<topic>]           Macro / Market: macro analysis, weekly updates and special topics, dated reports (macro/web/macro.js)
            #/r/<id>[/anchor]  report reader (any space; the space follows the report's sector)
   Only full reports in the current UI language are ever listed.
   Two "spaces" share this code (see SPACES): the research sectors (space "research", the
   default) and the portfolio funds ("portfolio"). A sector's `space` field says which dashboard
   lists it.
*/
(function(){
'use strict';

const $ = (id) => document.getElementById(id);
const state = {
  lang: 'cn', docLang: 'cn',  // Chinese unless the visitor switched (aid_lang2 in localStorage; the old aid_lang key is ignored so the default applies once)
  sectors: [], reports: [],
  meta: {current_year: new Date().getFullYear(), current_quarter: Math.floor(new Date().getMonth()/3)+1},
  view: 'dash', space: 'research', section: 'internal', sectorId: null, reportId: null, report: null,
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
const DL = window.DataLayer;
/* AI (local server only): config from /api/ai/config, the upload dialog's mode, the running
   generation job, and one chat thread per report */
const AI = {config: null, mode: 'file', space: null, files: [], dir: null, job: null, timer: null, threads: {}};
function aiOn(){ return DL.mode === 'api' && !!(AI.config && AI.config.enabled); }
/* a write in static mode lands as a commit; the site shows it after the workflow rebuilds */
function afterWrite(res){
  if (res && res.pending){
    const n = $('toast'); n.innerHTML = '';
    n.appendChild(document.createTextNode(t('pending_saved') + ' '));
    const a = el('a', null, t('view_actions')); a.href = DL.actionsUrl(); a.target = '_blank'; a.style.color = '#9FC4F0';
    n.appendChild(a);
    n.classList.add('show'); clearTimeout(n._tm); n._tm = setTimeout(() => n.classList.remove('show'), 9000);
    return true;
  }
  return false;
}
function handleErr(e){
  if (e && e.needLogin){ if (e.redirect) location.href = e.redirect + '?next=' + encodeURIComponent(location.hash); else showLogin(); return; }
  toast(e.message || String(e));
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
function otherLang(){ return state.docLang === 'cn' ? 'en' : 'cn'; }
function nav(hash){ if (location.hash === hash) route(); else location.hash = hash; window.scrollTo({top:0}); }
function hashReport(id, anchor){ return '#/r/' + id + (anchor ? '/' + anchor : ''); }
/* spaces: which dashboard a sector belongs to. Each has its own routes and strings; the order
   here is the order of the parts of data/sectors.json (the tab order is set in buildNav) */
const SPACES = {
  research:  {hash: '#/research',  sectorHash: '#/s/',           title: 'dash_title', sub: 'dash_sub', sectors: 'sectors',    nav: 'nav_panel'},
  // the portfolio space has two sub-sectors (the tabs of every fund's page); every portfolio report carries one in meta.section
  portfolio: {hash: '#/portfolio', sectorHash: '#/portfolio/s/', title: 'pm_title',   sub: 'pm_sub',   sectors: 'pm_sectors', nav: 'nav_portfolio', sections: ['internal', 'quarterly']},
  // the Macro / Market weekly updates are reports of the sector "macro_weekly"; the macro view
  // lists them (#/macro/weekly) and the reader opens them like any report
  macro:     {hash: '#/macro/weekly', sectorHash: '#/macro/weekly', title: 'mk_title', sub: 'mk_sub', sectors: 'nav_macro', nav: 'nav_macro'},
};
const SPACE_IDS = Object.keys(SPACES);
function spaceOf(sectorId){ const s = sectorById(sectorId); return (s && SPACES[s.space]) ? s.space : 'research'; }
function spaceSectors(space){ const sp = space || state.space; return state.sectors.filter(s => ((SPACES[s.space] ? s.space : 'research') === sp)); }
function spaceTitle(space){ return t(SPACES[space || state.space].title); }
function sections(space){ return SPACES[space || state.space].sections || null; }
function sectionName(sec){ return t('sec_' + sec); }
function hashDash(space){ return SPACES[space || state.space].hash; }
/* a fund's page: #/portfolio[/<section>]/s/<id>. Without a section the fund opens on its first tab that has a report */
/* the Macro / Market sectors each have a tab of the macro view */
const MACRO_TOPIC_OF = {macro_analysis: 'analysis', macro_weekly: 'weekly', macro_topics: 'topics'};
function hashSector(id, section){
  const sp = spaceOf(id);
  if (sp === 'macro') return '#/macro/' + (MACRO_TOPIC_OF[id] || 'weekly');
  return SPACES[sp].hash.replace(/\/$/, '') + (sections(sp) && section ? '/' + section : '') + '/s/' + id;
}
/* in a space with sub-sectors (portfolio management) every report belongs to one: its `section`
   (AID analysis or quarterly updates; reports saved without one count as the first). The funds
   themselves belong to the space as a whole, and a fund's page has one tab per sub-sector. */
function sectionOfReport(r){ const secs = sections(spaceOf(r.sector)); return secs ? (secs.includes(r.section) ? r.section : secs[0]) : ''; }
function inSection(r){ return !sections() || sectionOfReport(r) === state.section; }
/* a fund's full reports in every sub-sector: the dashboard card, and which tab the fund opens on */
function fundReports(sectorId){ return state.reports.filter(r => r.sector === sectorId && r.nature === 'full'); }
function escapeHtml(s){ return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function byUploaded(a, b){ return (b.uploaded_at || '').localeCompare(a.uploaded_at || ''); }
function nReports(n){ return n === 1 && state.lang === 'en' ? '1 report' : t('reports_in_lang', {n}); }

/* full reports in the current report language (state.docLang follows the UI language unless switched
   in the reader); in the current sub-sector, or, with all, in every sub-sector (the dashboard) */
function langReports(lang, all){ return state.reports.filter(r => (all || inSection(r)) && r.nature === 'full' && r.language === (lang || state.docLang)); }
function findReport(sector, period, lang, nature){ return state.reports.find(r => inSection(r) && r.sector === sector && r.period === period && r.language === lang && r.nature === nature) || null; }
/* a fund's reports come in one language (whatever the manager sends), so a portfolio fund whose
   reports are not in the current report language falls back to the language it has; research
   sectors keep the EN / 中文 editions apart */
function sectorReports(sectorId, lang, all){
  const mine = langReports(lang, all).filter(r => r.sector === sectorId);
  if (mine.length || lang || spaceOf(sectorId) !== 'portfolio') return mine;
  return state.reports.filter(r => (all || inSection(r)) && r.nature === 'full' && r.sector === sectorId);
}
function latestOf(list){ return list.slice().sort(byUploaded)[0] || null; }
/* the same report in the other language: its translation or the original it was translated from;
   else the edition uploaded in that language (the same quarter and type; for a weekly update,
   the same date; special topics and macro analyses are told apart only by the translation link) */
function twinOf(meta, lang){
  if (!meta) return null;
  const linked = state.reports.find(r => r.id !== meta.id && r.language === lang && (r.translated_from === meta.id
    || r.id === meta.translated_from || (meta.translated_from && r.translated_from === meta.translated_from)));
  if (linked) return linked;
  if (meta.date){
    if (meta.sector !== 'macro_weekly') return null;
    return state.reports.find(r => r.sector === meta.sector && r.date === meta.date && r.language === lang && r.nature === meta.nature) || null;
  }
  return findReport(meta.sector, meta.period, lang, meta.nature) || findReport(meta.sector, meta.period, lang, 'full');
}
/* the switch asked for a language the report does not have yet: Claude translates it now */
let translating = false;
async function translateNow(meta){
  if (translating) return;
  translating = true;
  toast(t('translating'));
  try {
    const twin = await DL.translate(meta.id);
    await loadAll();
    state.docLang = twin.language;
    try { localStorage.setItem('aid_doclang', state.docLang); } catch (e) {}
    nav(hashReport(twin.id));
  } catch (e) { if (e.needLogin) handleErr(e); else toast(t('translate_failed') + ': ' + e.message); }
  finally { translating = false; }
}
function canTranslate(){ return DL.mode === 'api' && typeof DL.translate === 'function'; }
/* a sector's report count = number of quarters it covers; languages and full/summary editions of one quarter count once */
function sectorQuarters(sectorId, all){ return new Set(state.reports.filter(r => (all || inSection(r)) && r.sector === sectorId).map(r => r.year + '-' + r.quarter)).size; }
/* a fund marked as exited sits in the grey section below the grid */
function isExited(s){ return s.status === 'exited'; }

/* ---------------------------------------------------------------- i18n + theme */
function applyI18n(){
  document.documentElement.lang = state.lang === 'cn' ? 'zh-CN' : 'en';
  // the news tracker (news.js) translates its own labels; only its hero uses panel keys
  document.querySelectorAll('[data-i18n]').forEach(n => {
    const k = n.getAttribute('data-i18n');
    if (n.closest('#view-news') && !(k in window.I18N.en)) return;
    n.textContent = t(k);
  });
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
  try { localStorage.setItem('aid_lang2', l); } catch (e) {}
  applyI18n();
  if (window.NewsTracker) window.NewsTracker.setLanguage(l);
  if (window.FundFactors) window.FundFactors.setLanguage(l);
  if (window.MacroMarket) window.MacroMarket.setLanguage(l);
  route();
}
/* switch the report language only (the in-page EN / 中文 switch) */
function setDocLang(l){
  state.docLang = l;
  try { localStorage.setItem('aid_doclang', l); } catch (e) {}
  if (state.view === 'art' && state.sectorId){
    const cur = state.report && state.report.meta;
    const twin = twinOf(cur, l);
    if (twin) nav(hashReport(twin.id));
    else if (cur && canTranslate()) translateNow(cur);
    else nav(hashSector(state.sectorId, state.section));
    return;
  }
  route();
}

/* ---------------------------------------------------------------- data */
async function loadAll(){
  const {sectors, reports, meta} = await DL.load();
  state.sectors = sectors; state.reports = reports; state.meta = meta;
  state.loadedAt = Date.now();
  // the Macro / Market view keeps its own list of the dated reports: it reloads it on its next showing
  if (window.MacroMarket && window.MacroMarket.invalidate) window.MacroMarket.invalidate();
  $('logoutBtn').hidden = !meta.auth;
  $('tokenBtn').hidden = DL.mode !== 'static';
  $('dlBtn').hidden = !DL.canDownload();
  if (DL.aiConfig && !AI.config){ try { AI.config = await DL.aiConfig(); } catch (e) { AI.config = null; } }
  $('aiFab').hidden = !aiOn();
  buildNav();
}

/* ---------------------------------------------------------------- nav */
function buildNav(){
  const n = $('mainnav');
  n.innerHTML = '';
  // tab order: fund key factors, portfolio management, the news tracker, the research panel
  // (dashboard + sector reports), then macro / market (slide briefs); sectors are opened from
  // the cards on the dashboard
  const isPanel = state.view !== 'news' && state.view !== 'factors' && state.view !== 'macro';
  const tab = (label, active, hash) => {
    const b = el('button', active ? 'active' : '', label);
    b.type = 'button'; b.addEventListener('click', () => nav(hash));
    n.appendChild(b);
  };
  const spaceBtn = (sp) => tab(t(SPACES[sp].nav), isPanel && state.space === sp, SPACES[sp].hash);
  tab(t('nav_factors'), state.view === 'factors', '#/factors');
  spaceBtn('portfolio');
  tab(t('nav_news'), state.view === 'news', '#/news');
  spaceBtn('research');
  SPACE_IDS.filter(sp => sp !== 'research' && sp !== 'portfolio' && sp !== 'macro').forEach(spaceBtn);
  tab(t('nav_macro'), state.view === 'macro' || (isPanel && state.space === 'macro'), '#/macro');
  // "Upload report" sits on the dashboard beside the sector list and in a report page's crumb bar
}

/* ---------------------------------------------------------------- dashboard */
function renderDash(space){
  showView('dash');
  state.space = space || state.space || 'research';
  state.sectorId = null; state.reportId = null; state.report = null;
  buildNav();
  // the hero and the section title name the space (research sectors, portfolio funds, ...)
  const sp = SPACES[state.space];
  $('dashTitle').textContent = spaceTitle();
  $('dashSub').textContent = t(sp.sub);
  $('dashSectorsH').textContent = t(sp.sectors);
  // the sub-sectors (portfolio management) are the tabs of each fund's page, not of the dashboard
  const secs = sections();
  $('dashTabs').hidden = true;
  const grid = $('sectorCards');
  grid.innerHTML = '';
  const exitedBox = $('exitedFunds'), exitedGrid = $('exitedCards');
  exitedGrid.innerHTML = '';
  // every fund of the space (a new fund shows at once, with "Upload the first report"); exited funds go below
  const shown = spaceSectors();
  const active = shown.filter(s => !isExited(s));
  if (active.some(s => s.category)){
    // funds grouped by strategy category, all on one page: one labelled band of cards per category
    const groups = categoryGroups(active);
    groups.forEach(g => {
      const head = el('div', 'cat-head');
      head.style.setProperty('--cat', g.color);
      head.appendChild(el('b', null, g.label));
      head.appendChild(el('span', 'cat-n', nFunds(g.sectors.length)));
      grid.appendChild(head);
      g.sectors.forEach(s => { const c = sectorCard(s, false); c.classList.add('cat'); c.style.setProperty('--cat', g.color); grid.appendChild(c); });
    });
  } else {
    active.forEach(s => grid.appendChild(sectorCard(s, false)));
  }
  if (secs && !active.length) grid.appendChild(el('div', 'empty-note', t('no_funds_section')));
  const ph = el('button', 'scard ph'); ph.type = 'button';
  ph.appendChild(el('div', 'plus', '+'));
  ph.appendChild(el('b', null, t('manage_sectors')));
  ph.addEventListener('click', () => openSectorManager());
  grid.appendChild(ph);
  const exited = secs ? shown.filter(isExited) : [];
  exitedBox.hidden = !exited.length;
  exited.forEach(s => exitedGrid.appendChild(sectorCard(s, true)));
  renderRecent(langReports(null, true).filter(r => spaceOf(r.sector) === state.space).sort(byUploaded).slice(0, 6));
  document.title = spaceTitle() + ' | Junson Capital';
}
/* the strategy categories of portfolio funds, in display order (all bands in the site blue); a
   category not listed here still gets a band, a fund without one goes under "Other" */
const CATEGORIES = [
  ['Private Credit', 'cat_private_credit', '#0C2B4E'],
  ['ABF', 'cat_abf', '#0C2B4E'],
  ['Structure Credit', 'cat_structure_credit', '#0C2B4E'],
  ['Alternative Yield', 'cat_alt_yield', '#0C2B4E'],
  ['Real Asset', 'cat_real_asset', '#0C2B4E'],
  ['Real Estate', 'cat_real_estate', '#0C2B4E'],
];
function categoryLabel(name){ const c = CATEGORIES.find(x => x[0] === name); return c ? t(c[1]) : (name || t('cat_other')); }
function categoryGroups(sectors){
  const by = new Map();
  sectors.forEach(s => { const k = s.category || ''; if (!by.has(k)) by.set(k, []); by.get(k).push(s); });
  const order = CATEGORIES.map(c => c[0]).concat(Array.from(by.keys()).filter(k => k && !CATEGORIES.some(c => c[0] === k)), ['']);
  return order.filter(k => by.has(k)).map(k => {
    const c = CATEGORIES.find(x => x[0] === k);
    return {key: k, label: categoryLabel(k), color: '#0C2B4E', sectors: by.get(k)};
  });
}
function nFunds(n){ return n === 1 && state.lang === 'en' ? '1 fund' : t('n_funds', {n}); }
/* one sector / fund card. In the portfolio space it carries a small action: mark the fund as
   exited (it moves to the grey section below) or, on a grey card, set it active again */
function sectorCard(s, exited){
  const mine = sectorReports(s.id, null, true);
  const latest = mine.slice().sort((a, b) => b.period_key - a.period_key)[0];
  const periods = new Set(mine.map(r => r.period));
  const card = el('button', 'scard' + (exited ? ' exited' : '')); card.type = 'button';
  const top = el('div', 'sc-top');
  top.appendChild(el('span', 'sc-code', s.code || s.id.slice(0,3).toUpperCase()));
  top.appendChild(el('span', 'sc-q', latest ? (latest.period + ' ' + t('latest')) : t('no_reports_yet')));
  card.appendChild(top);
  card.appendChild(el('b', null, sectorName(s)));
  const cov = sectorCoverage(s);
  // the other-language name, unless it is the same (fund names stay as they are)
  const other = state.lang === 'cn' ? (s.name_en || '') : (s.name_cn || '');
  card.appendChild(el('span', 'sc-cov', [other !== sectorName(s) ? other : '', cov].filter(Boolean).join(' · ')));
  const bd = el('div', 'sc-badges');
  if (latest){
    Array.from(periods).sort((a, b) => periodKey(b) - periodKey(a)).slice(0, 4).forEach(p => bd.appendChild(el('span', 'bdg', p)));
  } else bd.appendChild(el('span', 'bdg', t('coming_soon')));
  card.appendChild(bd);
  const nq = sectorQuarters(s.id, true);
  const foot = el('div', 'sc-foot');
  foot.appendChild(el('span', 'sc-go', (nq ? (t('enter') + ' · ' + nReports(nq)) : t('upload_first')) + ' ›'));
  if (sections()){
    const act = el('span', 'sc-act', exited ? t('set_active') : t('mark_exited'));
    act.setAttribute('role', 'button'); act.tabIndex = 0;
    const go = ev => { ev.stopPropagation(); ev.preventDefault(); setFundStatus(s, exited ? 'active' : 'exited'); };
    act.addEventListener('click', go);
    act.addEventListener('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') go(ev); });
    foot.appendChild(act);
  }
  card.appendChild(foot);
  card.addEventListener('click', () => nav(hashSector(s.id)));
  return card;
}
async function setFundStatus(s, status){
  try {
    await commitSectors(spaceSectors().map(x => x.id === s.id ? Object.assign({}, x, {status}) : x));
    toast(t(status === 'exited' ? 'fund_exited' : 'fund_active'));
    if (state.view === 'dash') renderDash();
  } catch (e) { handleErr(e); }
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
function openSector(id, section){
  const s = sectorById(id);
  if (!s){ nav(hashDash()); return; }
  state.space = spaceOf(id);
  const secs = sections();
  if (secs){
    // the tab asked for, else the first sub-sector the fund has a report in (AID analysis before
    // quarterly updates), or the first tab when it has none
    const has = secs.filter(sec => fundReports(id).some(r => sectionOfReport(r) === sec));
    state.section = secs.includes(section) ? section : (has[0] || secs[0]);
  }
  const latest = latestOf(sectorReports(id));
  if (latest){ history.replaceState(null, '', hashReport(latest.id)); renderReport(latest.id, null); return; }
  renderEmpty(s, null);
}
/* a fund's page (portfolio management): one tab per sub-sector, with the number of quarters it
   holds; a tab opens the fund's newest report there, or the empty reader with its upload button */
function buildFundTabs(s){
  const secs = sections(), tabs = $('fundTabs');
  tabs.innerHTML = ''; tabs.hidden = !secs;
  if (!secs) return;
  secs.forEach(sec => {
    const n = new Set(state.reports.filter(r => r.sector === s.id && sectionOfReport(r) === sec).map(r => r.year + '-' + r.quarter)).size;
    const b = el('button', sec === state.section ? 'on' : '', sectionName(sec)); b.type = 'button';
    if (n) b.appendChild(el('span', 'cnt', String(n)));
    b.addEventListener('click', () => { if (sec !== state.section) nav(hashSector(s.id, sec)); });
    tabs.appendChild(b);
  });
}
function renderEmpty(s, period){
  state.sectorId = s.id; state.reportId = null; state.report = null; state.exhibits = [];
  showView('art');
  buildNav();
  buildFundTabs(s);
  $('crumbPath').textContent = sectorName(s);
  buildPickers(s, null);
  buildSegs(null, s);
  $('titleRow').hidden = true; $('toolbar').hidden = true; $('docGrid').hidden = true;
  $('emptyReader').hidden = false;
  const n = $('emptyNotice'); n.innerHTML = '';
  // a sub-sector with nothing for this fund yet, else the quarter or the language that is missing
  const noneHere = sections() && !state.reports.some(r => r.sector === s.id && inSection(r));
  n.appendChild(el('b', null, period ? t('no_report_period', {sector: sectorName(s), period})
    : (noneHere ? t('no_report_section', {sector: sectorName(s), section: sectionName(state.section)}) : t('no_report_lang', {sector: sectorName(s)}))));
  const alt = $('emptyAlt');
  const other = latestOf(sectorReports(s.id, otherLang()).filter(r => !period || r.period === period));
  const latestMine = period ? latestOf(sectorReports(s.id)) : null;
  alt.hidden = !(other || latestMine);
  if (latestMine){ alt.textContent = t('open_latest') + ' (' + latestMine.period + ')'; alt.onclick = () => nav(hashReport(latestMine.id)); }
  else if (other){ alt.textContent = t('open_other_lang'); alt.onclick = () => { setLang(otherLang()); }; }
  $('emptyUpload').onclick = () => openUpload(s.id);
  document.title = sectorName(s) + ' — ' + spaceTitle() + ' | Junson Capital';
}

/* ---------------------------------------------------------------- report reader */
async function renderReport(id, anchor){
  let data;
  try { data = await DL.report(id); }
  catch (e) { if (e.needLogin){ handleErr(e); return; } toast(e.message); nav(hashDash()); return; }
  const meta = data.meta, content = data.content;
  state.docLang = meta.language;
  try { localStorage.setItem('aid_doclang', state.docLang); } catch (e) {}
  state.report = data; state.reportId = id; state.sectorId = meta.sector; state.exhibits = [];
  state.space = spaceOf(meta.sector);
  if (sections()) state.section = sectionOfReport(meta);
  showView('art');
  buildNav();
  const s = sectorById(meta.sector) || {id: meta.sector, name_en: meta.sector};
  buildFundTabs(s);
  $('titleRow').hidden = false; $('toolbar').hidden = false; $('docGrid').hidden = false; $('emptyReader').hidden = true;

  // crumbs + pickers
  const cp = $('crumbPath'); cp.innerHTML = '';
  cp.appendChild(document.createTextNode(sectorName(s)));
  if (s.region){ cp.appendChild(el('i', null, '|')); cp.appendChild(document.createTextNode(s.region)); }
  buildPickers(s, meta);
  buildSegs(meta, s);

  renderAiChat();

  // title / meta / tags
  $('docTitle').textContent = meta.title;
  // a dated report (a weekly update) is labelled by the date it was uploaded for
  $('qBadge').textContent = meta.date ? fmtDate(meta.date) : meta.period;
  const dm = $('docMeta'); dm.innerHTML = '';
  const add = (txt, bold) => { const sp = el('span'); if (bold) sp.appendChild(el('b', null, txt)); else sp.textContent = txt; dm.appendChild(sp); };
  const sep = () => dm.appendChild(el('span', 'sep', '|'));
  if (meta.publish_date){ add(t('published') + ' ' + meta.publish_date, true); sep(); }
  if (meta.masthead){ add(meta.masthead); sep(); }
  add(t('uploaded') + ' ' + fmtDate(meta.uploaded_at)); sep();
  add(t('source_file') + ': ' + (meta.source_name || '—'));
  if (meta.translated_from){
    // a translation: says so, with the way to the original
    sep();
    const sp = el('span', 'translated');
    sp.appendChild(document.createTextNode(t('translated_note', {lang: t(meta.language === 'en' ? 'cn' : 'en')}) + ' '));
    const a = el('a', null, t('see_original')); a.href = hashReport(meta.translated_from);
    sp.appendChild(a); dm.appendChild(sp);
  }
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
  document.title = meta.title + ' ' + (meta.date ? fmtDate(meta.date) : meta.period) + ' — ' + spaceTitle() + ' | Junson Capital';
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
  // a report without the other language yet can have Claude translate it (on the server)
  const langAvailable = meta
    ? !!twinOf(meta, other) || canTranslate()
    : sectorReports(sector, other).length > 0;
  setToggle('docLangToggle', state.docLang === 'cn', !langAvailable);
  $('docLangToggle').onclick = () => { if (langAvailable) setDocLang(other); };
}
/* the edition to open for a quarter: same type and language as the current report when
   possible, then the same type in another language, then the full report, then anything */
function bestEdition(list, meta){
  if (!list.length) return null;
  const nature = meta ? meta.nature : 'full';
  const prefs = [
    r => r.nature === nature && r.language === state.docLang,
    r => r.nature === 'full' && r.language === state.docLang,
    r => r.nature === nature,
    r => r.nature === 'full',
  ];
  for (const ok of prefs){ const hit = latestOf(list.filter(ok)); if (hit) return hit; }
  return latestOf(list);
}
/* a dated report (a weekly update): the week of its month, 1 to 5 (days 1-7 are week 1) */
function weekOfMonth(date){ return Math.ceil(Number(date.slice(8, 10)) / 7); }
function monthName(y, m){ return new Date(y, m - 1, 1).toLocaleDateString(state.lang === 'cn' ? 'zh-CN' : 'en-US', {month: 'long'}); }
function buildPickers(s, meta){
  // every quarter the sector has (in this sub-sector), in any language and of either type
  const all = state.reports.filter(r => inSection(r) && r.sector === s.id);
  const dated = all.length > 0 && all.every(r => r.date);
  $('pQuarterLbl').textContent = t(dated ? 'f_month' : 'f_quarter');
  $('pWeekRow').hidden = !dated;
  if (dated){ buildDatedPickers(all, meta); return; }
  const years = Array.from(new Set(all.map(r => r.year))).sort((a, b) => b - a);
  const py = $('pYear'), pq = $('pQuarter');
  py.innerHTML = ''; pq.innerHTML = '';
  if (!years.length){ py.appendChild(opt('', '—')); pq.appendChild(opt('', '—')); py.disabled = pq.disabled = true; $('pickCount').textContent = ''; return; }
  py.disabled = pq.disabled = false;
  years.forEach(y => py.appendChild(opt(String(y), String(y))));
  const curYear = meta ? meta.year : years[0];
  py.value = String(curYear);
  const fillQ = (year) => {
    pq.innerHTML = '';
    const qs = Array.from(new Set(all.filter(r => r.year === year).map(r => r.quarter))).sort((a, b) => b - a);
    qs.forEach(q => pq.appendChild(opt(String(q), 'Q' + q + ' · ' + q + 'Q' + year)));
    return qs;
  };
  const qs = fillQ(curYear);
  pq.value = String(meta ? meta.quarter : qs[0]);
  $('pickCount').textContent = nReports(sectorQuarters(s.id));
  const open = (y, q) => { const r = bestEdition(all.filter(x => x.year === y && x.quarter === q), meta); if (r) nav(hashReport(r.id)); };
  py.onchange = () => { const y = +py.value; const q2 = fillQ(y); pq.value = String(q2[0]); open(y, q2[0]); };
  pq.onchange = () => open(+py.value, +pq.value);
}
/* the pickers of a dated sector (the weekly updates): year, month and week of the month, each
   listing only what exists; a choice opens the update of that week */
function buildDatedPickers(all, meta){
  const py = $('pYear'), pm = $('pQuarter'), pw = $('pWeek');
  const ym = (r) => r.date.slice(0, 7);
  const years = Array.from(new Set(all.map(r => r.date.slice(0, 4)))).sort().reverse();
  py.innerHTML = ''; pm.innerHTML = ''; pw.innerHTML = '';
  py.disabled = pm.disabled = pw.disabled = false;
  years.forEach(y => py.appendChild(opt(y, y)));
  const cur = meta && meta.date ? meta.date : all.slice().sort((a, b) => b.date.localeCompare(a.date))[0].date;
  const fillM = (y) => {
    pm.innerHTML = '';
    const months = Array.from(new Set(all.filter(r => r.date.startsWith(y + '-')).map(ym))).sort().reverse();
    months.forEach(m => pm.appendChild(opt(m, monthName(+m.slice(0, 4), +m.slice(5, 7)))));
    return months;
  };
  const fillW = (m) => {
    pw.innerHTML = '';
    const weeks = Array.from(new Set(all.filter(r => ym(r) === m).map(r => weekOfMonth(r.date)))).sort((a, b) => b - a);
    weeks.forEach(w => {
      const dates = all.filter(r => ym(r) === m && weekOfMonth(r.date) === w).map(r => r.date).sort();
      pw.appendChild(opt(String(w), t('week_n', {n: w}) + ' · ' + fmtDate(dates[dates.length - 1])));
    });
    return weeks;
  };
  py.value = cur.slice(0, 4); fillM(cur.slice(0, 4)); pm.value = cur.slice(0, 7); fillW(cur.slice(0, 7)); pw.value = String(weekOfMonth(cur));
  // a report and its translation count once
  $('pickCount').textContent = nReports(all.filter(r => !(r.translated_from && all.some(o => o.id === r.translated_from))).length);
  const open = (m, w) => { const hits = all.filter(r => ym(r) === m && weekOfMonth(r.date) === w); const r = bestEdition(hits, meta); if (r) nav(hashReport(r.id)); };
  py.onchange = () => { const ms = fillM(py.value); pm.value = ms[0]; const ws = fillW(ms[0]); pw.value = String(ws[0]); open(ms[0], ws[0]); };
  pm.onchange = () => { const ws = fillW(pm.value); pw.value = String(ws[0]); open(pm.value, ws[0]); };
  pw.onchange = () => open(pm.value, +pw.value);
}
function imgUrl(name){ return DL.imageUrl(state.reportId, name); }
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
  const fig = el('figure', b.slide ? 'fig slide' : 'fig'); fig.id = b.anchor || ('ex-' + b.exhibit);
  const head = el('div', 'fig-head');
  head.appendChild(el('span', 'fig-no', exhibitLabel(b)));
  const cap = captionText(b);
  if (cap) head.appendChild(el('span', 'fig-cap', cap));
  if (!b.slide) fig.appendChild(head);  // an uploaded picture is the slide itself: no exhibit header
  const idx = pushExhibit(b, cap);
  if (b.unsupported){
    fig.appendChild(el('div', 'unsupported', t('unsupported_img')));
  } else {
    const im = document.createElement('img');
    im.loading = 'lazy'; im.src = imgUrl(b.src); im.alt = cap || exhibitLabel(b);
    if (b.width && b.width < 900) im.style.maxWidth = 'min(100%, ' + Math.round(b.width) + 'px)';  // never wider than the column
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
  const first = b.header === false ? 0 : 1;
  // cells the source sets apart (a heat map's tinted cells, a highlighted scenario): [row, col, mark]
  const marks = {};
  (b.marks || []).forEach(m => { marks[m[0] + ':' + m[1]] = m[2]; });
  rows.slice(first).forEach((r, i) => {
    const tr = el('tr');
    r.forEach((c, j) => {
      const td = el('td'); td.innerHTML = escapeHtml(c).replace(/\n/g, '<br>');
      const mk = marks[(i + first) + ':' + j];
      if (mk) td.classList.add('mk-' + mk);
      tr.appendChild(td);
    });
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
  state.lbSingle = false; setLbBrowsing(true);
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
/* one image that is not a report exhibit (the Fund key factors source image): the same viewer
   with zoom and pan, without the previous / next / "view in text" controls */
function setLbBrowsing(on){ ['lbPrev', 'lbNext', 'lbGoto', 'lbCount'].forEach(id => { $(id).hidden = !on; }); }
function openLbImage(src, caption){
  state.lbSingle = true; setLbBrowsing(false);
  const im = lbImg();
  im.style.transform = 'scale(0)';
  im.onload = fitImage;
  im.src = src; im.alt = caption || '';
  if (im.complete && im.naturalWidth) fitImage();
  $('lbCap').textContent = caption || '';
  $('lbCount').textContent = '';
  $('lb').classList.add('open');
  document.body.style.overflow = 'hidden';
}
window.AIDLightbox = {open: openLbImage};
function stepLb(dir){
  if (state.lbSingle) return;
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
  // the dark area around the image closes it (the stage handles its own clicks above, so a drag
  // to pan does not); so do the empty parts of the top bar and the hint line
  $('lb').addEventListener('click', e => {
    const c = e.target.classList;
    if (e.target === $('lb') || c.contains('lb-top') || c.contains('lb-hint')) closeLb();
  });
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
  $('upFile').value = ''; state.upFiles = []; paintChosenFiles();
  // the sub-sector (portfolio management only): the report's own, else the tab on screen
  const upSpace = isEdit ? spaceOf(editMeta.sector) : (sectorId ? spaceOf(sectorId) : state.space);
  const secs = sections(upSpace);
  state.upSpace = upSpace;
  $('upSectionLbl').hidden = !secs;
  if (secs) fillSelect($('upSection'), secs.map(sec => [sec, sectionName(sec)]), isEdit ? sectionOfReport(editMeta) : (secs.includes(state.section) ? state.section : secs[0]));
  paintUploadTypes();
  fillUploadSectors(upSpace, isEdit ? editMeta.sector : sectorId);
  fillSelect($('upQuarter'), [1,2,3,4].map(q => [String(q), 'Q' + q]), String(isEdit ? editMeta.quarter : state.meta.current_quarter));
  fillSelect($('upNature'), [['full', t('full')], ['summary', t('summary')]], isEdit ? editMeta.nature : 'full');
  fillSelect($('upLang'), [['en', t('en')], ['cn', t('cn')], ['', t('auto_detect')]], isEdit ? editMeta.language : state.docLang);
  $('upYear').value = isEdit ? editMeta.year : state.meta.current_year;
  $('upTitleIn').value = isEdit ? editMeta.title : '';
  $('upKeywords').value = isEdit ? (editMeta.keywords || []).join(', ') : '';
  $('upSubmit').textContent = isEdit ? t('save') : t('upload');
  $('upSubmit').disabled = false;
  const msg = $('upMsg'); msg.textContent = ''; msg.className = 'form-msg';
  // "Generate with AI" is offered when the server can call Claude and a sector of the space has a
  // skill (the research panel, the Macro / Market weekly updates); a new report only
  // opened for a Macro / Market sector, the AI mode is offered only when that sector has a skill
  // (the weekly updates do, special topics do not)
  const canAi = aiOn() && !isEdit && (sectorId && upSpace === 'macro'
    ? !!(AI.config.sectors || {})[sectorId]
    : spaceSectors(upSpace).some(s => (AI.config.sectors || {})[s.id]));
  $('upModes').hidden = !canAi;
  AI.space = upSpace;
  $('upDate').value = isEdit && editMeta.date ? editMeta.date : todayIso();
  $('aiWeekYear').value = '';  // the week pickers follow the date until changed
  setUploadMode('file', sectorId);
  $('upOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}
/* what the file picker takes: Word and PDF everywhere (read for text, tables and figures); a
   portfolio fund's AID analysis and a Macro / Market special topic also take a PowerPoint deck
   or pictures, read slide by slide: text as text, tables as tables, charts kept whole */
const REPORT_EXTS = ['.docx', '.pdf'];
const DECK_EXTS = ['.pptx', '.ppt'];
const IMAGE_EXTS = ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'];
function imagesAllowed(){
  return (state.upSpace === 'portfolio' && $('upSection').value === 'internal') || ['macro_analysis', 'macro_topics'].includes($('upSector').value);
}
function uploadExts(){ return imagesAllowed() ? REPORT_EXTS.concat(DECK_EXTS, IMAGE_EXTS) : REPORT_EXTS; }
function fileExt(name){ const m = /\.[^.]+$/.exec(name || ''); return m ? m[0].toLowerCase() : ''; }
function paintUploadTypes(){
  const img = imagesAllowed();
  $('upFile').accept = uploadExts().join(',');
  $('upFile').multiple = img;  // several pictures: one report, a slide each
  $('dropTypes').dataset.i18n = img ? 'drop_types_img' : 'drop_types';  // kept through a language switch
  $('dropTypes').textContent = t($('dropTypes').dataset.i18n);
  const keep = (state.upFiles || []).filter(x => uploadExts().includes(fileExt(x.file.name)));
  if (keep.length !== (state.upFiles || []).length){ state.upFiles = keep; paintChosenFiles(); }
}
const isImage = f => IMAGE_EXTS.includes(fileExt(f.name));
/* the files chosen for the upload, in order: a Word or PDF report alone, or one or more
   pictures. Pictures picked, dropped or pasted are added after those already chosen. */
function addUpFiles(files, pasted){
  const msg = $('upMsg'); msg.textContent = ''; msg.className = 'form-msg';
  files = files.filter(f => uploadExts().includes(fileExt(f.name)));
  if (!files.length) return false;
  const pics = files.filter(isImage);
  if (pics.length === files.length && imagesAllowed()){
    if (!pasted) pics.sort((a, b) => a.name.localeCompare(b.name, undefined, {numeric: true}));  // 1, 2, ..., 10
    const before = (state.upFiles || []).filter(x => isImage(x.file));
    state.upFiles = before.concat(pics.map(f => ({file: f, pasted: !!pasted})));
  } else {
    const doc = files.find(f => !isImage(f)) || files[0];
    state.upFiles = [{file: doc, pasted: !!pasted}];
  }
  paintChosenFiles();
  return true;
}
/* under the drop zone: the chosen file's name, or the pictures as numbered thumbnails (slide
   order), each with a button that takes it out */
function paintChosenFiles(){
  const list = state.upFiles || [], box = $('upFiles');
  box.querySelectorAll('img').forEach(im => URL.revokeObjectURL(im.src));
  box.innerHTML = '';
  const pics = list.filter(x => isImage(x.file));
  $('dropFile').textContent = !list.length ? '' : (pics.length > 1 ? t('n_images', {n: pics.length})
    : (list[0].pasted ? t('pasted_image') : list[0].file.name));
  pics.forEach((x, i) => {
    const card = el('div', 'up-thumb');
    const im = document.createElement('img'); im.src = URL.createObjectURL(x.file); im.alt = x.file.name;
    card.appendChild(im);
    card.appendChild(el('span', 'up-thumb-no', String(i + 1)));
    const rm = el('button', 'up-thumb-rm', '×'); rm.type = 'button'; rm.title = t('remove');
    rm.addEventListener('click', () => { state.upFiles = list.filter(y => y !== x); paintChosenFiles(); });
    card.appendChild(rm);
    box.appendChild(card);
  });
  box.hidden = !pics.length;
}
/* Ctrl+V in the upload dialog: a copied picture (a screenshot, an image copied from a page or a
   slide) is added as the next slide; a file copied in Explorer is chosen like a picked one.
   Pictures only where pictures are taken (a portfolio fund's AID analysis); a text paste into
   a field is left alone. */
function onUploadPaste(e){
  if (!$('upOverlay').classList.contains('open') || state.editing || AI.mode === 'ai') return;
  const cd = e.clipboardData; if (!cd) return;
  const files = Array.from(cd.files || []);
  const named = files.filter(f => uploadExts().includes(fileExt(f.name)) && !/^image\.[a-z]+$/i.test(f.name));
  if (named.length){ e.preventDefault(); addUpFiles(named, false); return; }
  const item = Array.from(cd.items || []).find(it => it.kind === 'file' && /^image\//.test(it.type));
  const blob = item ? item.getAsFile() : files.find(f => /^image\//.test(f.type));
  if (!blob){
    if (files.length){ e.preventDefault(); const msg = $('upMsg'); msg.className = 'form-msg err'; msg.textContent = t(imagesAllowed() ? 'choose_file_img' : 'choose_file'); }
    return;  // text: let it paste into the field
  }
  e.preventDefault();
  if (!imagesAllowed()){ const msg = $('upMsg'); msg.className = 'form-msg err'; msg.textContent = t('paste_img_not_here'); return; }
  const ext = ({'image/jpeg': '.jpg', 'image/webp': '.webp', 'image/gif': '.gif', 'image/bmp': '.bmp'})[blob.type] || '.png';
  // named after the fund and tab: the report's title when Claude finds none on the picture
  addUpFiles([new File([blob], pastedName() + ext, {type: blob.type || 'image/png'})], true);
}
/* a pasted picture has no file name: the fund and the tab give one (the reader shows the
   quarter beside the title) */
function pastedName(){
  const s = sectorById($('upSector').value);
  return [s ? sectorName(s) : '', state.upSpace === 'portfolio' ? sectionName('internal') : ''].filter(Boolean).join(' ').replace(/[\/:*?"<>|]/g, ' ') || 'pasted-image';
}
function todayIso(){ const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
/* a dated sector (the weekly updates): the dialog asks for the date of the update, not a year and quarter */
function datedUpload(){ return spaceOf($('upSector').value) === 'macro'; }
function applyDated(){
  const dated = datedUpload();
  $('upDateLbl').hidden = !dated; $('upYearLbl').hidden = dated; $('upQuarterLbl').hidden = dated;
  if (dated){ const d = $('upDate').value || todayIso(); $('upDate').value = d; $('upYear').value = d.slice(0, 4); $('upQuarter').value = String(Math.floor((+d.slice(5, 7) - 1) / 3) + 1); }
  if (AI.mode === 'ai'){ $('upLangLbl').parentElement.hidden = dated; $('aiNote').textContent = t(dated ? 'ai_note_weekly' : 'ai_note'); }
  else $('upLangLbl').parentElement.hidden = false;
  $('aiWeekRow').hidden = !(dated && AI.mode === 'ai');
  if (dated && AI.mode === 'ai' && !$('aiWeekYear').value) setAiWeekFromDate($('upDate').value);
  if (dated && AI.mode === 'ai') paintAiWeek();
}
/* the week of the update that Claude writes ("Weekly Market Update YYYYMM WeekN"): weeks run
   Monday to Sunday and week 1 is the week that contains the 1st, the weekly-market-update
   Skill's own rule; the pickers start from the date given and can be changed */
function mondayWeekOfMonth(y, m, d){ const first = new Date(y, m - 1, 1).getDay(); const offset = (first + 6) % 7; return Math.floor((d - 1 + offset) / 7) + 1; }
function weeksInMonth(y, m){ const days = new Date(y, m, 0).getDate(); return mondayWeekOfMonth(y, m, days); }
function setAiWeekFromDate(iso){
  const y = +iso.slice(0, 4), m = +iso.slice(5, 7), d = +iso.slice(8, 10);
  $('aiWeekYear').value = y;
  fillSelect($('aiWeekMonth'), Array.from({length: 12}, (_, i) => [String(i + 1), monthName(y, i + 1)]), String(m));
  fillSelect($('aiWeekWeek'), Array.from({length: weeksInMonth(y, m)}, (_, i) => [String(i + 1), t('week_n', {n: i + 1})]), String(mondayWeekOfMonth(y, m, d)));
}
function aiWeekKey(){ const y = $('aiWeekYear').value, m = String($('aiWeekMonth').value).padStart(2, '0'), w = $('aiWeekWeek').value; return y && m && w ? y + m + ' Week' + w : ''; }
function paintAiWeek(){
  const y = +$('aiWeekYear').value, m = +$('aiWeekMonth').value;
  if (y && m){
    const cur = $('aiWeekWeek').value;
    fillSelect($('aiWeekWeek'), Array.from({length: weeksInMonth(y, m)}, (_, i) => [String(i + 1), t('week_n', {n: i + 1})]), cur);
    if (!$('aiWeekWeek').value) $('aiWeekWeek').value = '1';
  }
  $('aiWeekLabel').textContent = aiWeekKey() ? 'Weekly Market Update ' + aiWeekKey() + ' · ' + t('ai_week_hint') : '';
}
/* for the other views (the Macro / Market page): open the upload dialog on a sector */
window.AIDPanel = {
  openUpload(sectorId){ openUpload(sectorId); },
};
/* the sector list of the upload dialog: the space's sectors (every fund, whichever sub-sector is chosen) */
function fillUploadSectors(space, want){
  const choices = spaceSectors(space);
  const cur = want || $('upSector').value;
  fillSelect($('upSector'), choices.map(s => [s.id, sectorName(s)]), choices.some(s => s.id === cur) ? cur : (choices[0] && choices[0].id));
  paintUploadTypes();  // a special topic takes decks and pictures, a weekly update does not
}
/* the upload dialog's two modes: a hand-picked file, or a report that Claude generates with the
   sector's skill from source files dropped into the dialog */
function setUploadMode(mode, sectorId){
  AI.mode = mode;
  const ai = mode === 'ai', isEdit = !!state.editing;
  $('modeFile').classList.toggle('on', !ai); $('modeAi').classList.toggle('on', ai);
  $('drop').hidden = ai || isEdit;
  $('upNatureLbl').hidden = ai; $('upKeywordsLbl').hidden = ai;
  $('upSectionLbl').hidden = ai || !sections();
  $('aiFields').hidden = !ai;
  $('upLangLbl').textContent = t(ai ? 'ai_lang' : 'u_lang');
  $('upSubmit').textContent = ai ? t('ai_generate') : (isEdit ? t('save') : t('upload'));
  const cur = $('upSector').value || sectorId;
  if (ai){
    const able = spaceSectors(AI.space || state.space).filter(s => AI.config.sectors[s.id]);
    fillSelect($('upSector'), able.map(s => [s.id, sectorName(s)]), able.some(s => s.id === cur) ? cur : (able[0] && able[0].id));
    fillSelect($('upLang'), [['en', t('en')], ['cn', t('cn')]], state.docLang === 'cn' ? 'cn' : 'en');
    renderAiFiles(); renderAiDir();
    $('aiProgress').hidden = !AI.job; if (AI.job) renderAiJob(AI.job);
  } else {
    fillUploadSectors(AI.space || state.space, cur);
    fillSelect($('upLang'), [['en', t('en')], ['cn', t('cn')], ['', t('auto_detect')]], isEdit ? state.editing.language : state.docLang);
  }
  applyDated();
}
/* the source files dropped or chosen so far (File objects); dropping more adds to the list */
function addAiFiles(list){
  Array.from(list || []).forEach(f => { if (!AI.files.some(x => x.name === f.name && x.size === f.size)) AI.files.push(f); });
  renderAiFiles();
}
function renderAiFiles(){
  const box = $('aiFiles'); box.innerHTML = '';
  box.hidden = !AI.files.length;
  AI.files.forEach((f, i) => {
    const row = el('label');
    row.appendChild(el('span', null, f.name));
    row.appendChild(el('span', 'sz', Math.max(1, Math.round(f.size / 1024)) + ' KB'));
    const rm = el('button', 'rm', '✕'); rm.type = 'button'; rm.title = t('remove');
    rm.addEventListener('click', () => { AI.files.splice(i, 1); renderAiFiles(); });
    row.appendChild(rm);
    box.appendChild(row);
  });
}
/* the folder the generated documents are saved to: picked with the browser's folder dialog
   (Chrome / Edge on https or localhost); elsewhere the files are downloaded instead */
function canPickDir(){ return typeof window.showDirectoryPicker === 'function'; }
function renderAiDir(){
  $('aiPickDir').disabled = !canPickDir();
  $('aiDirName').textContent = AI.dir ? AI.dir.name : t(canPickDir() ? 'ai_dir_none' : 'ai_dir_unsupported');
}
async function pickAiDir(){
  try { AI.dir = await window.showDirectoryPicker({mode: 'readwrite'}); }
  catch (e) { if (e && e.name !== 'AbortError') toast(e.message); }
  renderAiDir();
}
/* after a job: write the generated documents into the picked folder, or download them */
async function saveAiOutputs(job){
  const outputs = job.outputs || [];
  if (!outputs.length) return;
  if (AI.dir){
    let n = 0;
    for (const o of outputs){
      try {
        const r = await fetch(DL.aiJobFileUrl(job.id, o.name)); if (!r.ok) throw new Error(r.status + ' ' + o.name);
        const fh = await AI.dir.getFileHandle(o.name, {create: true});
        const w = await fh.createWritable(); await w.write(await r.blob()); await w.close();
        n++;
      } catch (e) { toast(e.message); }
    }
    toast(t('ai_saved', {n, dir: AI.dir.name}));
  } else {
    for (const o of outputs){
      const a = document.createElement('a'); a.href = DL.aiJobFileUrl(job.id, o.name); a.download = o.name;
      document.body.appendChild(a); a.click(); a.remove();
      await new Promise(res => setTimeout(res, 600));
    }
    toast(t('ai_downloaded'));
  }
}
function renderAiJob(job){
  const box = $('aiProgress'); box.hidden = false;
  box.textContent = (job.log || []).join('\n') || '…';
  box.scrollTop = box.scrollHeight;
}
/* start a generation job and follow it until it ends; the dialog may be closed meanwhile */
async function aiGenerateSubmit(){
  const msg = $('upMsg'), btn = $('upSubmit');
  if (!AI.files.length){ msg.className = 'form-msg err'; msg.textContent = t('ai_no_files'); return; }
  const fd = new FormData();
  AI.files.forEach(f => fd.append('files', f, f.name));
  if (datedUpload()) applyDated();
  fd.append('sector', $('upSector').value); fd.append('year', $('upYear').value); fd.append('quarter', $('upQuarter').value);
  fd.append('language', $('upLang').value); fd.append('title', $('upTitleIn').value.trim());
  if (datedUpload()){ fd.append('date', $('upDate').value); fd.append('week', aiWeekKey()); }
  btn.disabled = true; msg.className = 'form-msg'; msg.textContent = '…';
  try {
    const res = await DL.aiGenerate(fd);
    AI.job = {id: res.job, state: 'queued', log: []};
    AI.files = []; renderAiFiles();
    msg.textContent = t('ai_started');
    renderAiJob(AI.job);
    pollAiJob();
  } catch (e) { msg.className = 'form-msg err'; msg.textContent = e.message; btn.disabled = false; }
}
function pollAiJob(){
  clearTimeout(AI.timer);
  if (!AI.job) return;
  AI.timer = setTimeout(async () => {
    try {
      const job = await DL.aiJob(AI.job.id);
      AI.job = job;
      if (!$('aiProgress').hidden || $('upOverlay').classList.contains('open')) renderAiJob(job);
      if (job.state === 'done' || job.state === 'error'){
        const done = job.state === 'done';
        AI.job = null; $('upSubmit').disabled = false;
        const msg = $('upMsg'); msg.className = 'form-msg ' + (done ? 'ok' : 'err'); msg.textContent = done ? t('ai_done') : (t('ai_failed') + ': ' + (job.error || ''));
        if (done){
          toast(t('ai_done'));
          await saveAiOutputs(job);
          await loadAll();
          const first = (job.reports || [])[0];
          closeUpload();
          if (first) nav(hashReport(first.id)); else route();
        } else toast(t('ai_failed') + ': ' + (job.error || ''));
        return;
      }
    } catch (e) { /* the server may be busy; keep polling */ }
    pollAiJob();
  }, 3000);
}

/* ---------------------------------------------------------------- AI chat: edits the report on screen */
function aiThread(){ return state.reportId ? (AI.threads[state.reportId] = AI.threads[state.reportId] || []) : null; }
function renderAiChat(){
  if ($('aiChat').hidden) return;
  $('aiCtx').textContent = state.reportId && state.report ? t('ai_ctx', {title: state.report.meta.title}) : t('ai_ctx_none');
  const box = $('aiMsgs'); box.innerHTML = '';
  (aiThread() || []).forEach(m => box.appendChild(el('div', 'ai-msg ' + (m.role === 'user' ? 'user' : 'bot' + (m.error ? ' err' : '')), m.content)));
  if (AI.waiting) box.appendChild(el('div', 'ai-msg bot wait', t('ai_thinking')));
  box.scrollTop = box.scrollHeight;
  $('aiInput').disabled = !state.reportId || !!AI.waiting; $('aiSend').disabled = !state.reportId || !!AI.waiting;
}
async function sendAiMessage(){
  const text = $('aiInput').value.trim();
  const th = aiThread();
  if (!text || !th || AI.waiting) return;
  const id = state.reportId;
  th.push({role: 'user', content: text});
  $('aiInput').value = ''; AI.waiting = true; renderAiChat();
  try {
    const res = await DL.aiChat(id, th.filter(m => !m.error));
    th.push({role: 'assistant', content: res.reply || (res.changed ? t('ai_changed') : '…')});
    if (res.changed){
      toast(t('ai_changed'));
      // the report on screen is the one that changed (the user may have navigated meanwhile)
      if (state.reportId === id) await renderReport(id, null);
    }
  } catch (e) { th.push({role: 'assistant', content: e.message, error: true}); }
  AI.waiting = false; renderAiChat();
}
function wireAi(){
  $('modeFile').addEventListener('click', () => setUploadMode('file'));
  $('modeAi').addEventListener('click', () => setUploadMode('ai'));
  const drop = $('aiDrop'), file = $('aiFile');
  file.addEventListener('change', () => { addAiFiles(file.files); file.value = ''; });
  ['dragenter', 'dragover'].forEach(evn => drop.addEventListener(evn, e => { e.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(evn => drop.addEventListener(evn, e => { e.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', e => addAiFiles(e.dataTransfer.files));
  $('aiPickDir').addEventListener('click', pickAiDir);
  $('aiFab').addEventListener('click', () => { const c = $('aiChat'); c.hidden = !c.hidden; renderAiChat(); if (!c.hidden) $('aiInput').focus(); });
  $('aiClose').addEventListener('click', () => { $('aiChat').hidden = true; });
  $('aiForm').addEventListener('submit', e => { e.preventDefault(); sendAiMessage(); });
  $('aiInput').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); sendAiMessage(); } });
}
function closeUpload(){ $('upOverlay').classList.remove('open'); unlockScroll(); }
async function submitUpload(ev){
  ev.preventDefault();
  const msg = $('upMsg');
  const btn = $('upSubmit');
  const sector = $('upSector').value, year = $('upYear').value, quarter = $('upQuarter').value;
  const language = $('upLang').value, nature = $('upNature').value;
  const title = $('upTitleIn').value.trim(), keywords = $('upKeywords').value.trim();
  const section = sections(spaceOf(sector)) ? $('upSection').value : '';
  if (AI.mode === 'ai' && !state.editing){ await aiGenerateSubmit(); return; }
  try {
    btn.disabled = true;
    if (state.editing){
      msg.className = 'form-msg'; msg.textContent = '…';
      const m = await DL.updateReport(state.editing.id, {sector, year: +year, quarter: +quarter, language, nature, title, keywords, section});
      closeUpload();
      if (afterWrite(m)) return;
      toast(t('save')); await loadAll();
      nav(hashReport(m.id)); route();
      return;
    }
    const files = (state.upFiles || []).map(x => x.file).filter(f => uploadExts().includes(fileExt(f.name)));
    if (!files.length){ msg.className = 'form-msg err'; msg.textContent = t(imagesAllowed() ? 'choose_file_img' : 'choose_file'); btn.disabled = false; return; }
    msg.className = 'form-msg'; msg.textContent = t('uploading');
    if (datedUpload()) applyDated();
    const fields = {sector, year: $('upYear').value, quarter: $('upQuarter').value, nature, language, title, keywords, section};
    if (datedUpload()) fields.date = $('upDate').value;
    const m = await DL.upload(fields, files.length > 1 ? files : files[0]);
    closeUpload();
    if (afterWrite(m)) return;
    toast((m.replaced && m.replaced.length ? t('upload_replaced') : t('upload_ok'))
      + (m.translating ? ' · ' + t('upload_translating', {lang: t(m.language === 'en' ? 'cn' : 'en')}) : ''));
    await loadAll();
    nav(hashReport(m.id)); route();
  } catch (e) {
    if (e.needLogin){ closeUpload(); handleErr(e); return; }
    msg.className = 'form-msg err'; msg.textContent = e.message;
  } finally { btn.disabled = false; }
}
function wireUpload(){
  const drop = $('drop'), file = $('upFile');
  file.addEventListener('change', () => { addUpFiles(Array.from(file.files), false); file.value = ''; });
  document.addEventListener('paste', onUploadPaste);
  ['dragenter', 'dragover'].forEach(evn => drop.addEventListener(evn, e => { e.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(evn => drop.addEventListener(evn, e => { e.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', e => { if (e.dataTransfer.files.length && !addUpFiles(Array.from(e.dataTransfer.files), false)){ const msg = $('upMsg'); msg.className = 'form-msg err'; msg.textContent = t(imagesAllowed() ? 'choose_file_img' : 'choose_file'); } });
  $('upForm').addEventListener('submit', submitUpload);
  $('upClose').addEventListener('click', closeUpload);
  $('upCancel').addEventListener('click', closeUpload);
  $('upOverlay').addEventListener('click', e => { if (e.target === $('upOverlay')) closeUpload(); });
  $('uploadBtn').addEventListener('click', () => openUpload(state.sectorId));
  $('upSector').addEventListener('change', () => { applyDated(); paintUploadTypes(); });
  $('upDate').addEventListener('change', () => { if (datedUpload()) setAiWeekFromDate($('upDate').value); applyDated(); });
  ['aiWeekYear', 'aiWeekMonth', 'aiWeekWeek'].forEach(id => $(id).addEventListener('change', paintAiWeek));
  // the dashboard's upload button: the sector picker lists the current space's sectors
  $('dashUploadBtn').addEventListener('click', () => openUpload(null));
  // choosing the other sub-sector switches the fund list to that sub-sector's funds
  $('upSection').addEventListener('change', () => { fillUploadSectors(state.editing ? spaceOf(state.editing.sector) : state.space, null); paintUploadTypes(); });
}

/* ---------------------------------------------------------------- sector manager (add / edit / remove) */
const SECTOR_KEYS = ['id', 'code', 'name_en', 'name_cn', 'region', 'coverage_en', 'coverage_cn', 'status', 'space', 'category'];
function cleanSector(s){ const o = {}; SECTOR_KEYS.forEach(k => { if (s[k] !== undefined) o[k] = s[k]; }); if (!o.status) o.status = 'active'; return o; }
function slugId(name){ return name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '') || ('sector_' + Date.now().toString(36)); }
/* persist the sector list of the current space (static mode commits data/sectors.json; API mode
   diffs) and refresh state. The file holds every space, in SPACES order (research sectors
   first); only the current space's part is replaced. */
async function commitSectors(spaceList){
  const part = (sp) => sp !== state.space ? spaceSectors(sp) : spaceList;
  const clean = SPACE_IDS.map(part).flat().map(cleanSector);
  const res = await DL.saveSectors(clean);
  if (res && res.pending){
    // keep report counts/periods from the current state until the rebuild
    state.sectors = clean.map(s => Object.assign({}, sectorById(s.id) || {}, s));
    afterWrite(res);
  } else {
    await loadAll();
  }
}
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
  // the strategy category (portfolio funds only): the known ones, plus the fund's own if it is not listed
  const catRow = $('sCategoryRow'), cat = $('sCategory');
  catRow.hidden = state.space !== 'portfolio';
  cat.innerHTML = '';
  cat.appendChild(opt('', '—'));
  const known = CATEGORIES.map(c => c[0]);
  known.concat(s && s.category && !known.includes(s.category) ? [s.category] : []).forEach(k => cat.appendChild(opt(k, categoryLabel(k))));
  cat.value = s ? (s.category || '') : '';
  $('sCovEn').value = s ? (s.coverage_en || []).join(', ') : '';
  $('sCovCn').value = s ? (s.coverage_cn || []).join(', ') : '';
  $('secSubmit').textContent = s ? t('save') : t('add_sector');
  $('secCancelEdit').hidden = !s;
}
function renderSectorList(){
  const list = $('secList'); list.innerHTML = '';
  const saveOrder = async () => {
    const ids = Array.from(list.querySelectorAll('.sec-row')).map(r => r.dataset.id);
    const ordered = ids.map(id => sectorById(id)).filter(Boolean);
    try {
      await commitSectors(ordered);
      renderSectorList(); if (state.view === 'dash') renderDash(); else buildNav();
      toast(t('order_saved'));
    } catch (e) { handleErr(e); renderSectorList(); }
  };
  let dragging = null;
  const clearMarks = () => list.querySelectorAll('.sec-row').forEach(r => r.classList.remove('drop-before', 'drop-after'));
  spaceSectors().forEach((s, idx) => {
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
    const nq = sectorQuarters(s.id);
    const nm = el('span', 'nm'); nm.textContent = s.name_en;
    // the Chinese name, unless it is the same (fund names stay as they are)
    nm.appendChild(el('span', null, [s.name_cn !== s.name_en ? s.name_cn : '', nq ? nReports(nq) : ''].filter(Boolean).join(' · ')));
    const cov = sectorCoverage(s); if (cov) nm.appendChild(el('span', 'cov', cov));
    row.appendChild(nm);
    const ed = el('button', null, t('edit')); ed.type = 'button';
    ed.addEventListener('click', () => { fillSectorForm(s); $('sNameEn').focus(); });
    row.appendChild(ed);
    const rm = el('button', 'rm', t('remove')); rm.type = 'button';
    rm.disabled = nq > 0; if (nq > 0) rm.title = t('sector_has_reports');
    rm.addEventListener('click', async () => {
      if (!confirm(t('confirm_remove_sector'))) return;
      try { await commitSectors(spaceSectors().filter(x => x.id !== s.id)); renderSectorList(); if (state.view === 'dash') renderDash(); else buildNav(); }
      catch (e) { handleErr(e); }
    });
    row.appendChild(rm);
    list.appendChild(row);
  });
}
function wireSectorManager(){
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
      category: state.space === 'portfolio' ? $('sCategory').value : undefined,
    };
    const id = $('sId').value;
    if (!payload.name_en){ $('secMsg').className = 'form-msg err'; $('secMsg').textContent = t('s_name_en'); return; }
    try {
      let list;
      if (id) list = spaceSectors().map(s => s.id === id ? Object.assign({}, s, payload) : s);
      else {
        const nid = slugId(payload.name_en);
        if (sectorById(nid)) throw new Error('sector exists');
        const extra = {id: nid, status: 'active', space: state.space};
        list = spaceSectors().concat([Object.assign(extra, payload, {code: payload.code || payload.name_en.split(/\s+/).map(w => w[0]).join('').toUpperCase().slice(0, 4), name_cn: payload.name_cn || payload.name_en, region: payload.region || (state.space === 'research' ? 'Global' : '')})]);
      }
      await commitSectors(list);
      $('secMsg').className = 'form-msg ok'; $('secMsg').textContent = t('sector_saved');
      renderSectorList(); fillSectorForm(null);
      if (state.view === 'dash') renderDash(); else { buildNav(); route(); }
    } catch (e) { if (e.needLogin) handleErr(e); $('secMsg').className = 'form-msg err'; $('secMsg').textContent = e.message; }
  });
}

/* ---------------------------------------------------------------- views + routing */
function showView(v){
  state.view = v;
  $('view-dash').hidden = v !== 'dash';
  $('view-art').hidden = v !== 'art';
  $('view-news').hidden = v !== 'news';
  $('view-factors').hidden = v !== 'factors';
  $('view-macro').hidden = v !== 'macro';
  $('searchWrap').style.visibility = v === 'art' ? '' : 'hidden';
  renderAiChat();
}
/* news tracker: the Credit News Radar module (news.js) renders into #view-news and follows the UI language */
function renderNews(){
  showView('news');
  state.sectorId = null; state.reportId = null; state.report = null;
  buildNav();
  if (window.NewsTracker) window.NewsTracker.mount(state.lang);
  document.title = t('news_title') + ' | Junson Capital';
}
/* fund key factors: factors.js renders into #view-factors (sub-tab and month come from the address) */
function renderFactors(tab, ym){
  showView('factors');
  state.sectorId = null; state.reportId = null; state.report = null;
  buildNav();
  if (window.FundFactors) window.FundFactors.mount(state.lang, tab, ym);
  document.title = t('factors_title') + ' | Junson Capital';
}
/* macro / market: macro.js renders into #view-macro (the month comes from the address) */
function renderMacro(topic, ym){
  showView('macro');
  state.sectorId = null; state.reportId = null; state.report = null;
  buildNav();
  if (window.MacroMarket) window.MacroMarket.mount(state.lang, topic, ym);
  document.title = t('mk_title') + ' | Junson Capital';
}
function parseHash(){
  const h = decodeURIComponent(location.hash.replace(/^#\/?/, ''));
  if (!h) return {view: 'factors', tab: null, ym: null};  // home: the latest Investment performance
  const p = h.split('/');
  if (p[0] === 'news') return {view: 'news'};
  if (p[0] === 'factors') return {view: 'factors', tab: p[1] || null, ym: p[2] || null};
  if (p[0] === 'macro') return {view: 'macro', topic: p[1] || null, ym: p[2] || null};  // #/macro/<topic>[/<YYYY-MM>]
  if (SPACES[p[0]]){
    // #/research[/s/<id>], #/portfolio[/<section>][/s/<id>] (the section is a tab of the fund's page)
    const secs = SPACES[p[0]].sections || [];
    let i = 1, section = null;
    if (secs.includes(p[i])){ section = p[i]; i++; }
    if (p[i] === 's' && p[i + 1]) return {view: 'sector', id: p[i + 1], section};
    return {view: 'dash', space: p[0]};
  }
  if (p[0] === 's' && p[1]) return {view: 'sector', id: p[1]};
  if (p[0] === 'r' && p[1]) return {view: 'art', id: p[1], anchor: p.slice(2).join('/') || null};
  return {view: 'dash', space: 'research'};
}
/* A dashboard or fund page shows the reports as they are now: an upload made in another tab, on
   another computer or on the server since the list was loaded appears without refreshing the page
   (the list is reloaded when it is more than 30 seconds old; this tab's own uploads reload it at once). */
const RELOAD_AFTER_MS = 30000;
async function freshen(){
  if (DL.mode !== 'api' || Date.now() - (state.loadedAt || 0) < RELOAD_AFTER_MS) return;
  try { await loadAll(); } catch (e) { /* keep the list we have; the next visit tries again */ }
}
async function route(){
  const h = parseHash();
  try {
    if (h.view === 'dash' || h.view === 'sector') await freshen();
    if (h.view === 'dash') renderDash(h.space);
    else if (h.view === 'news') renderNews();
    else if (h.view === 'factors') renderFactors(h.tab, h.ym);
    else if (h.view === 'macro') renderMacro(h.topic, h.ym);
    else if (h.view === 'sector') openSector(h.id, h.section || null);
    else if (h.view === 'art'){
      if (state.view === 'art' && state.reportId === h.id && h.anchor){ const n = document.getElementById(h.anchor); if (n) n.scrollIntoView(); return; }
      await renderReport(h.id, h.anchor);
    }
  } catch (e) { toast(e.message); console.error(e); }
}

/* ---------------------------------------------------------------- wire up */
function wire(){
  $('brandBtn').addEventListener('click', () => nav('#/'));
  $('backBtn').addEventListener('click', () => nav(state.space === 'macro' && state.sectorId ? hashSector(state.sectorId) : hashDash()));
  $('langToggle').addEventListener('click', () => setLang(state.lang === 'cn' ? 'en' : 'cn'));
  $('logoutBtn').addEventListener('click', async () => { await DL.logout(); if (DL.mode === 'api') location.href = '/login.html?logout=1'; else location.reload(); });
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
  $('dlBtn').addEventListener('click', () => { if (state.reportId && DL.sourceUrl) window.open(DL.sourceUrl(state.reportId, state.report && state.report.meta), '_blank'); });
  $('printBtn').addEventListener('click', () => window.print());
  $('editBtn').addEventListener('click', () => { if (state.report) openUpload(state.sectorId, state.report.meta); });
  $('delBtn').addEventListener('click', async () => {
    if (!state.report || !confirm(t('confirm_delete'))) return;
    try {
      const res = await DL.deleteReport(state.reportId);
      if (afterWrite(res)) return;
      toast(t('deleted')); await loadAll(); nav(hashSector(state.sectorId, state.section)); route();
    } catch (e) { handleErr(e); }
  });
  // password prompt (static encrypted mode)
  $('loginForm').addEventListener('submit', async ev => {
    ev.preventDefault();
    const msg = $('loginMsg'); msg.className = 'form-msg'; msg.textContent = '…'; $('loginSubmit').disabled = true;
    try { await DL.login($('loginPw').value); $('loginOverlay').classList.remove('open'); unlockScroll(); await loadAll(); route(); }
    catch (e) { msg.className = 'form-msg err'; msg.textContent = t('wrong_password'); }
    finally { $('loginSubmit').disabled = false; }
  });
  // GitHub token prompt (static mode writes)
  let tokenResolve = null;
  DL.setTokenPrompt(() => new Promise(resolve => { tokenResolve = resolve; $('tokenInput').value = ''; $('tokenMsg').textContent = ''; $('tokenOverlay').classList.add('open'); $('tokenInput').focus(); }));
  const closeToken = (val) => { $('tokenOverlay').classList.remove('open'); unlockScroll(); if (tokenResolve){ tokenResolve(val || ''); tokenResolve = null; } };
  $('tokenForm').addEventListener('submit', async ev => {
    ev.preventDefault();
    const v = $('tokenInput').value.trim(); if (!v) return;
    const msg = $('tokenMsg'); msg.className = 'form-msg'; msg.textContent = '…';
    try { if (DL.checkToken) await DL.checkToken(v); DL.setToken(v); msg.textContent = ''; closeToken(v); }
    catch (e) { msg.className = 'form-msg err'; msg.textContent = e.message; }
  });
  if (DL.tokenUrl){ const a = $('tokenNewLink'); if (a){ a.href = DL.tokenUrl(); a.hidden = false; } }
  $('tokenClose').addEventListener('click', () => closeToken(''));
  $('tokenBtn').addEventListener('click', () => { $('tokenInput').value = DL.token ? DL.token() : ''; $('tokenMsg').textContent = ''; $('tokenOverlay').classList.add('open'); });
  document.addEventListener('keydown', e => {
    const lbOpen = $('lb').classList.contains('open');
    if (e.key === 'Escape'){ if (lbOpen) closeLb(); else { closeUpload(); closeSectorManager(); if ($('tokenOverlay').classList.contains('open')) closeToken(''); } }
    if (lbOpen && e.key === 'ArrowLeft') stepLb(-1);
    if (lbOpen && e.key === 'ArrowRight') stepLb(1);
    if (lbOpen && (e.key === '+' || e.key === '=')) zoomAt(1.25);
    if (lbOpen && e.key === '-') zoomAt(1 / 1.25);
    if (lbOpen && e.key === '0') fitImage();
  });
  wireLightbox(); wireUpload(); wireSectorManager(); wireHeader(); wireAi();
  window.addEventListener('hashchange', () => route());
}

function showLogin(){
  $('loginOverlay').classList.add('open'); document.body.style.overflow = 'hidden';
  setTimeout(() => $('loginPw').focus(), 50);
}
async function init(){
  try { const l = localStorage.getItem('aid_lang2'); if (l === 'en' || l === 'cn') state.lang = l; } catch (e) {}
  state.docLang = state.lang;
  try { const d = localStorage.getItem('aid_doclang'); if (d === 'en' || d === 'cn') state.docLang = d; } catch (e) {}
  applyI18n();
  wire();
  await DL.init();
  if (DL.needsLogin()){ showLogin(); return; }
  try { await loadAll(); }
  catch (e) { handleErr(e); if (e.needLogin) return; }
  route();
}
init();
})();
