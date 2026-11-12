/* Fund key factors — third view of the AID Research Panel (#/factors/<tab>/<YYYY-MM>).
   Two sub-tabs, one month on screen at a time:
     performance  the fund performance table, drawn as a real table
     budget       the budget completion slide, drawn as real charts
   The data comes from data/factors/<tab>/<YYYY-MM>.json, produced from an uploaded image by
   factors/scripts/extract_factors.py (Claude reads the image). Uploading:
     local server   POST /api/factors/upload, extracted at once
     GitHub Pages   the image is committed to factors/incoming/ and the build workflow extracts it
   Exposes window.FundFactors = { mount(lang, tab, month), setLanguage(lang) }; lang is "en" | "cn".
   Every label that comes from the data is inserted with textContent. */
(function () {
'use strict';

const TABS = ['performance', 'budget'];
const SVG_NS = 'http://www.w3.org/2000/svg';
// one blue ramp for the parts of an actual bar: dark (earliest) -> light (latest)
const RAMP = ['#104281', '#184f95', '#1c5cab', '#256abf', '#2a78d6', '#3987e5', '#5598e7', '#6da7ec', '#86b6ef'];
const C_BUDGET = '#c3c2b7', C_ACTUAL = '#2a78d6';
const MIME_EXT = {'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp', 'image/gif': 'gif'};
const MAX_BYTES = 5 * 1024 * 1024;

const STR = {
  en: {
    tab_performance: 'Fund performance', tab_budget: 'Budget completion',
    year: 'Year', month: 'Month', upload: 'Upload image',
    empty_title: 'No data for this sub-tab yet', empty_text: 'Upload an image of the monthly slide or table. Claude reads it and turns it into a real chart or table.',
    load_error: 'This month could not be loaded',
    extracted: 'Read from the uploaded image on {date}', by_model: 'by {model}', manual: 'manual transcription',
    source: 'View source image',
    warn_title: 'Check these against the source image', note_title: 'Note',
    note_explain: 'Explain with a note', note_add: 'Add a note', note_edit: 'Edit note',
    note_dlg: 'Note · {tab}, {month}', note_label: 'Note',
    note_hint: 'Shown in a blue box above the chart or table for this month. One paragraph per line. Leave it empty to remove the note.',
    en_make: 'Create English labels', en_working: 'Translating with Claude…', en_done: 'English labels added',
    move_link: 'Change date', move_dlg: 'Change date · {tab}',
    move_now: 'This data and its image are filed under {month}. Pick the date they belong to.',
    move_replace: '{month} already has data. Replace it with this one.',
    move_same: 'That is the current date. Pick a different month.',
    move_need_replace: 'That month already has data. Tick the box to replace it, or pick another month.',
    move_submit: 'Change date', move_working: 'Moving…', move_done: 'Now filed under {month}',
    move_pending: 'Saved to GitHub. The workflow applies the date change and rebuilds the site; refresh in about 2 minutes.',
    note_copy: 'Copy the note from {month}',
    note_auto: 'Already added automatically',
    note_warns: 'Warnings from the checks', note_tick: 'Tick the warnings this note explains. They are then hidden on the page, and kept in the data file.',
    note_need_text: 'Write the note that explains the ticked warning first',
    note_save: 'Save note', note_saving: 'Saving…', note_saved: 'Note saved',
    note_pending: 'Saved to GitHub. The site rebuilds in about 2 minutes; this page already shows the change.',
    budget: 'Budget', actual: 'Actual', parts: 'Actual by month', derived: 'derived',
    data_table: 'Show the numbers as a table', th_chart: 'Chart', th_item: 'Item', th_value: 'Value', th_parts: 'Breakdown',
    key_completion: 'Budget completion', key_pos2: '100% or more', key_pos1: '75% to 99%', key_neg1: 'Below 75%', key_neg2: '0%',
    up_title: 'Upload an image', up_drop: 'Drop an image here, click to choose, or paste a screenshot', up_types: 'PNG, JPEG or WebP, up to 5 MB',
    up_tab: 'Sub-tab', up_year: 'Year', up_month: 'Month',
    up_hint: 'Claude reads the image and rebuilds it as a chart or table for the month you choose.',
    up_replace: 'This month already has data. Uploading replaces it.',
    up_submit: 'Upload and read', cancel: 'Cancel', close: 'Close ✕',
    up_need_file: 'Choose an image first', up_bad_type: 'Use a PNG, JPEG or WebP image', up_too_big: 'The image is larger than 5 MB',
    up_working: 'Reading the image with Claude… this can take a minute.', up_saving: 'Saving to GitHub…',
    up_done: 'Done: {tab}, {month}',
    up_pending: 'Saved to GitHub. The workflow now reads the image and rebuilds the site; refresh in about 3 minutes.',
    view_actions: 'View progress',
  },
  cn: {
    tab_performance: '基金表现', tab_budget: '预算完成度',
    year: '年份', month: '月份', upload: '上传图片',
    empty_title: '该子页暂无数据', empty_text: '上传当月幻灯片或表格的图片，Claude 会读取并还原为真实的图表或表格。',
    load_error: '无法加载该月份的数据',
    extracted: '于 {date} 从上传图片读取', by_model: '模型 {model}', manual: '人工录入',
    source: '查看原图',
    warn_title: '请对照原图核对以下内容', note_title: '备注',
    note_explain: '添加备注说明', note_add: '添加备注', note_edit: '编辑备注',
    note_dlg: '备注 · {tab}，{month}', note_label: '备注',
    note_hint: '将显示在该月图表或表格上方的蓝色框中。每行一段；留空即删除备注。',
    en_make: '生成英文标签', en_working: 'Claude 正在翻译…', en_done: '已生成英文标签',
    move_link: '更改日期', move_dlg: '更改日期 · {tab}',
    move_now: '该数据及其图片目前归档于 {month}。请选择正确的日期。',
    move_replace: '{month} 已有数据，用本数据替换。',
    move_same: '与当前日期相同，请选择其他月份。',
    move_need_replace: '该月份已有数据。请勾选替换，或选择其他月份。',
    move_submit: '更改日期', move_working: '正在移动…', move_done: '已归档到 {month}',
    move_pending: '已保存到 GitHub。工作流将应用日期更改并重建网站，约 2 分钟后刷新即可。',
    note_copy: '复制 {month} 的备注',
    note_auto: '已自动添加',
    note_warns: '校验提示', note_tick: '勾选本备注所解释的提示。勾选后页面不再显示该提示，但数据文件中仍保留。',
    note_need_text: '请先填写用于解释所勾选提示的备注',
    note_save: '保存备注', note_saving: '正在保存…', note_saved: '备注已保存',
    note_pending: '已保存到 GitHub，网站约 2 分钟后重建；本页已显示更改。',
    budget: '预算', actual: '实际', parts: '实际分月', derived: '推算',
    data_table: '以表格显示数字', th_chart: '图表', th_item: '项目', th_value: '数值', th_parts: '分项',
    key_completion: '预算完成度', key_pos2: '100% 及以上', key_pos1: '75%–99%', key_neg1: '低于 75%', key_neg2: '0%',
    up_title: '上传图片', up_drop: '拖入图片、点击选择，或直接粘贴截图', up_types: 'PNG、JPEG 或 WebP，不超过 5 MB',
    up_tab: '子页', up_year: '年份', up_month: '月份',
    up_hint: 'Claude 会读取图片，并按所选月份还原为图表或表格。',
    up_replace: '该月份已有数据，上传后将被替换。',
    up_submit: '上传并读取', cancel: '取消', close: '关闭 ✕',
    up_need_file: '请先选择图片', up_bad_type: '请使用 PNG、JPEG 或 WebP 图片', up_too_big: '图片超过 5 MB',
    up_working: 'Claude 正在读取图片，可能需要一分钟…', up_saving: '正在保存到 GitHub…',
    up_done: '完成：{tab}，{month}',
    up_pending: '已保存到 GitHub。工作流正在读取图片并重建网站，约 3 分钟后刷新即可。',
    view_actions: '查看进度',
  },
};

const state = {lang: 'en', tab: 'performance', ym: null, index: null, doc: null, built: false, seq: 0, picked: null};
const $ = (id) => document.getElementById(id);
function t(key, vars) {
  let s = (STR[state.lang] || STR.en)[key];
  if (s === undefined) s = STR.en[key] !== undefined ? STR.en[key] : key;
  if (vars) Object.keys(vars).forEach((k) => { s = s.split('{' + k + '}').join(vars[k]); });
  return s;
}
function h(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined && text !== null) n.textContent = text;
  return n;
}
function s(tag, attrs, text) {
  const n = document.createElementNS(SVG_NS, tag);
  if (attrs) Object.keys(attrs).forEach((k) => n.setAttribute(k, attrs[k]));
  if (text !== undefined) n.textContent = text;
  return n;
}
function locale() { return state.lang === 'cn' ? 'zh-CN' : 'en-US'; }
function monthLabel(ym) {
  const [y, m] = ym.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(locale(), {year: 'numeric', month: 'long'});
}
function monthName(m) { return new Date(2000, m - 1, 1).toLocaleDateString(locale(), {month: 'long'}); }
function toast(msg, link) {
  const n = $('toast');
  if (!n) return;
  n.textContent = msg;
  if (link) { const a = h('a', null, ' ' + link.text); a.href = link.href; a.target = '_blank'; a.rel = 'noopener'; a.style.color = '#9FC4F0'; n.appendChild(a); }
  n.classList.add('show');
  clearTimeout(n._tm); n._tm = setTimeout(() => n.classList.remove('show'), link ? 9000 : 2600);
}

/* ---------------------------------------------------------------- English version of an upload
   The slides are usually Chinese. Each month's file carries "en": {original text: English},
   written by Claude when the image is read. With the interface in English every label and
   sentence from the data is looked up there; with it in Chinese the original is shown. */
const CJK = /[㐀-䶿一-鿿]/;
function english() { return state.lang === 'en' ? ((state.doc && state.doc.en) || {}) : null; }
/* a label or sentence from the data, in the interface language */
function L(text) {
  const en = english();
  return (en && text && en[text]) || text;
}
/* warnings and automatic notes are English sentences that quote a column header */
function LQ(text) {
  const en = english();
  if (!en || !text) return text;
  let out = text;
  ((state.doc && state.doc.columns) || []).forEach((c) => { if (c.label && en[c.label]) out = out.split(c.label).join(en[c.label]); });
  return en[text] || out;
}
/* an amount as printed on the slide: 万 (10,000) and 亿 (100 million) become millions in English,
   matching the translated unit in the panel title. Only once the month has its English labels. */
function V(item) {
  const text = item.text || '', en = english();
  if (!en || !Object.keys(en).length || typeof item.value !== 'number') return text;
  const unit = /(万|亿)$/.exec(text);
  if (!unit) return text;
  const millions = unit[1] === '万' ? item.value / 100 : item.value * 100;
  const size = Math.abs(millions), digits = size >= 100 ? 1 : (size >= 0.1 ? 2 : 3);
  return millions.toLocaleString('en-US', {minimumFractionDigits: digits, maximumFractionDigits: digits}) + 'M';
}
/* does this month still show Chinese that has no English yet? */
function lacksEnglish(doc) {
  const en = doc.en || {}, seen = [];
  const add = (x) => { if (typeof x === 'string' && x) seen.push(x); };
  add(doc.title); add(doc.name_header);
  (doc.columns || []).forEach((c) => { add(c.group); add(c.label); });
  (doc.rows || []).forEach((r) => add(r.name));
  (doc.footnotes || []).forEach(add);
  (doc.sections || []).forEach((sec) => {
    add(sec.title);
    (sec.blocks || []).forEach((b) => {
      (b.charts || []).forEach((c) => { add(c.title); (c.bars || []).forEach((bar) => { add(bar.group); add(bar.label); (bar.segments || []).forEach((sg) => add(sg.label)); }); });
      (b.notes || []).forEach(add);
    });
  });
  return seen.some((x) => CJK.test(x) && !en[x]);
}
async function makeEnglish() {
  const tab = state.tab, ym = state.ym;
  toast(t('en_working'));
  try {
    const r = await fetch('/api/factors/' + tab + '/' + ym + '/translate', {method: 'POST'});
    let data = null; try { data = await r.json(); } catch (e) {}
    if (r.status === 401) { location.href = '/login.html?next=' + encodeURIComponent(location.hash); return; }
    if (!r.ok) throw new Error((data && data.error) || (r.status + ' ' + r.statusText));
    toast(t('en_done'));
    if (state.tab === tab && state.ym === ym) show(tab, ym);
  } catch (e) {
    toast(e.message || String(e));
  }
}

/* ---------------------------------------------------------------- data */
async function getJson(path) {
  const r = await fetch(path, {cache: 'no-cache'});
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(r.status + ' ' + path);
  return r.json();
}
async function loadIndex(force) {
  if (state.index && !force) return state.index;
  const idx = await getJson('data/factors/index.json');
  state.index = (idx && idx.tabs) || {};
  return state.index;
}
function months(tab) { return ((state.index || {})[tab] || []).slice().sort(); }
function go(tab, ym) { location.hash = '#/factors/' + tab + (ym ? '/' + ym : ''); }

/* ---------------------------------------------------------------- shell */
function build() {
  if (state.built) return;
  const card = $('factorsCard');
  card.textContent = '';
  const bar = h('div', 'ff-bar');
  const tabs = h('nav', 'ff-tabs'); tabs.id = 'ffTabs'; tabs.setAttribute('aria-label', 'sub-tabs');
  TABS.forEach((tab) => {
    const b = h('button'); b.type = 'button'; b.dataset.tab = tab;
    b.addEventListener('click', () => go(tab, null));
    tabs.appendChild(b);
  });
  bar.appendChild(tabs);
  const ctl = h('div', 'ff-controls');
  const ly = h('label'); ly.appendChild(h('span')).id = 'ffYearLbl'; const ys = h('select'); ys.id = 'ffYear'; ly.appendChild(ys);
  const lm = h('label'); lm.appendChild(h('span')).id = 'ffMonthLbl'; const ms = h('select'); ms.id = 'ffMonth'; lm.appendChild(ms);
  const up = h('button', 'btn primary small'); up.type = 'button'; up.id = 'ffUpload';
  ctl.appendChild(ly); ctl.appendChild(lm); ctl.appendChild(up);
  bar.appendChild(ctl);
  card.appendChild(bar);
  const body = h('div', 'ff-body'); body.id = 'ffBody';
  card.appendChild(body);

  ys.addEventListener('change', () => {
    const inYear = months(state.tab).filter((m) => m.startsWith(ys.value + '-'));
    go(state.tab, inYear[inYear.length - 1] || null);
  });
  ms.addEventListener('change', () => go(state.tab, ms.value));
  up.addEventListener('click', () => openUpload());

  const tip = h('div', 'ff-tip'); tip.id = 'ffTip'; tip.hidden = true; tip.setAttribute('role', 'status');
  $('view-factors').appendChild(tip);
  buildUploadDialog();
  buildNoteDialog();
  buildMoveDialog();
  state.built = true;
}
function paintShell() {
  document.querySelectorAll('#ffTabs button').forEach((b) => {
    b.textContent = t('tab_' + b.dataset.tab);
    b.classList.toggle('on', b.dataset.tab === state.tab);
  });
  $('ffYearLbl').textContent = t('year');
  $('ffMonthLbl').textContent = t('month');
  $('ffUpload').textContent = '⬆ ' + t('upload');
  const all = months(state.tab);
  const years = Array.from(new Set(all.map((m) => m.slice(0, 4)))).sort().reverse();
  const ys = $('ffYear'), ms = $('ffMonth');
  ys.textContent = ''; ms.textContent = '';
  years.forEach((y) => { const o = h('option', null, y); o.value = y; ys.appendChild(o); });
  const year = state.ym ? state.ym.slice(0, 4) : years[0];
  if (year) ys.value = year;
  all.filter((m) => m.startsWith(year + '-')).forEach((m) => { const o = h('option', null, monthName(Number(m.slice(5)))); o.value = m; ms.appendChild(o); });
  if (state.ym) ms.value = state.ym;
  ys.disabled = years.length === 0; ms.disabled = all.length === 0;
  paintUploadDialog();
}

/* ---------------------------------------------------------------- render */
async function show(tab, ym) {
  const seq = ++state.seq;
  build();
  state.tab = TABS.includes(tab) ? tab : (TABS.includes(state.tab) ? state.tab : TABS[0]);
  const body = $('ffBody');
  body.classList.add('is-loading');
  try { await loadIndex(false); }
  catch (e) { state.index = {}; }
  if (seq !== state.seq) return;
  const all = months(state.tab);
  state.ym = all.includes(ym) ? ym : (all[all.length - 1] || null);
  // keep the address in step with what is shown, without re-routing
  const want = '#/factors/' + state.tab + (state.ym ? '/' + state.ym : '');
  if (location.hash !== want && location.hash.indexOf('#/factors') === 0) history.replaceState(null, '', want);
  paintShell();
  if (!state.ym) { state.doc = null; body.classList.remove('is-loading'); renderEmpty(body); return; }
  let doc = null, err = null;
  try { doc = await getJson('data/factors/' + state.tab + '/' + state.ym + '.json'); }
  catch (e) { err = e; }
  if (seq !== state.seq) return;
  body.classList.remove('is-loading');
  state.doc = doc;
  if (!doc) { renderEmpty(body, err ? (t('load_error') + ': ' + err.message) : t('load_error')); return; }
  renderDoc(body, doc);
}
function renderEmpty(body, message) {
  body.textContent = '';
  const box = h('div', 'ff-empty');
  box.appendChild(h('b', null, message || t('empty_title')));
  if (!message) box.appendChild(document.createTextNode(t('empty_text')));
  box.appendChild(document.createElement('br'));
  const b = h('button', 'btn primary', '⬆ ' + t('upload')); b.type = 'button';
  b.addEventListener('click', () => openUpload());
  box.appendChild(b);
  body.appendChild(box);
}
function renderDoc(body, doc) {
  body.textContent = '';
  const head = h('div', 'ff-head');
  head.appendChild(h('h2', null, L(doc.title) || t('tab_' + state.tab)));
  head.appendChild(h('span', 'ff-period', monthLabel(state.ym)));
  body.appendChild(head);
  // a warning that a note explains (listed in doc.dismissed) is no longer shown
  const dismissed = doc.dismissed || [];
  const warnings = (doc.warnings || []).filter((x) => !dismissed.includes(x));
  const action = (label, explain) => { const b = h('button', 'btn small', label); b.type = 'button'; b.addEventListener('click', () => openNote(explain)); return b; };
  if (warnings.length) {
    const w = h('div', 'ff-warn'); const inner = h('div');
    inner.appendChild(h('b', null, t('warn_title')));
    const ul = h('ul'); warnings.forEach((x) => ul.appendChild(h('li', null, LQ(x))));
    inner.appendChild(ul); w.appendChild(inner);
    w.appendChild(action(t('note_explain'), true));
    body.appendChild(w);
  }
  // notes explain something about the month's figures (for example rows the source leaves out).
  // auto_notes are written by the checks on upload (a known gap, see factors/config.json);
  // notes are written by a person in the note dialog. Both show in one box.
  const allNotes = (doc.auto_notes || []).concat((doc.notes || []).filter((x) => !(doc.auto_notes || []).includes(x)));
  if (allNotes.length) {
    const n = h('div', 'ff-note'); const inner = h('div');
    inner.appendChild(h('b', null, t('note_title')));
    allNotes.forEach((x) => inner.appendChild(h('p', null, LQ(x))));
    n.appendChild(inner);
    n.appendChild(action(t(doc.notes && doc.notes.length ? 'note_edit' : 'note_add'), false));
    body.appendChild(n);
  }
  if (state.tab === 'budget') renderBudget(body, doc); else { watchWidth(null); renderPerformance(body, doc); }
  const meta = h('div', 'ff-meta');
  let when = doc.extracted_at || '';
  try { when = new Date(doc.extracted_at).toLocaleDateString(locale(), {year: 'numeric', month: 'short', day: 'numeric'}); } catch (e) {}
  const model = doc.model === 'manual transcription' ? t('manual') : t('by_model', {model: doc.model || ''});
  meta.appendChild(h('span', null, t('extracted', {date: when}) + ' · ' + model));
  if (doc.source_image) {
    const a = h('a', null, t('source')); a.target = '_blank'; a.rel = 'noopener';
    a.href = 'data/factors/' + state.tab + '/' + encodeURIComponent(doc.source_image);
    // opens in the panel's image viewer (close with the cross, Esc, or a click outside the image);
    // a modified click, or a missing viewer, still follows the link to the image itself
    a.addEventListener('click', (ev) => {
      if (!window.AIDLightbox || ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.button !== 0) return;
      ev.preventDefault();
      window.AIDLightbox.open(a.href, (L(doc.title) || t('tab_' + state.tab)) + ' · ' + monthLabel(state.ym));
    });
    meta.appendChild(a);
  }
  const noteLink = h('a', null, doc.notes && doc.notes.length ? t('note_edit') : t('note_add'));
  noteLink.href = '#'; noteLink.setAttribute('role', 'button');
  noteLink.addEventListener('click', (ev) => { ev.preventDefault(); openNote(false); });
  meta.appendChild(noteLink);
  // a month saved before translation existed, or whose translation failed: make it now.
  // On GitHub Pages the build workflow does this by itself on its next run.
  if (state.lang === 'en' && lacksEnglish(doc) && !(window.DataLayer && window.DataLayer.mode === 'static')) {
    const enLink = h('a', null, t('en_make'));
    enLink.href = '#'; enLink.setAttribute('role', 'button');
    enLink.addEventListener('click', (ev) => { ev.preventDefault(); makeEnglish(); });
    meta.appendChild(enLink);
  }
  // uploaded under the wrong year or month: file it under the right one
  const moveLink = h('a', null, t('move_link'));
  moveLink.href = '#'; moveLink.setAttribute('role', 'button');
  moveLink.addEventListener('click', (ev) => { ev.preventDefault(); openMove(); });
  meta.appendChild(moveLink);
  body.appendChild(meta);
}

/* ---------------------------------------------------------------- performance table */
function completionClass(v) {
  if (v === null || v === undefined) return '';
  if (v >= 100) return 'c-pos2';
  if (v >= 75) return 'c-pos1';
  if (v > 0) return 'c-neg1';
  return 'c-neg2';
}
function renderPerformance(body, doc) {
  const cols = doc.columns || [], rows = doc.rows || [];
  const wrap = h('div', 'ff-tablewrap');
  const table = h('table', 'ff-table');
  const thead = h('thead'), r1 = h('tr'), r2 = h('tr');
  const first = h('th', null, L(doc.name_header) || ''); first.rowSpan = 2; first.scope = 'col';
  r1.appendChild(first);
  const groupStart = cols.map((c, j) => j === 0 || c.group !== cols[j - 1].group || !c.group);
  for (let j = 0; j < cols.length;) {
    const c = cols[j];
    if (c.group) {
      let n = 1;
      while (j + n < cols.length && cols[j + n].group === c.group) n++;
      const g = h('th', 'grp g-start', L(c.group)); g.colSpan = n; g.scope = 'colgroup';
      r1.appendChild(g);
      for (let k = 0; k < n; k++) {
        const th = h('th', 'wrap' + (k === 0 ? ' g-start' : ''), L(cols[j + k].label)); th.scope = 'col';
        r2.appendChild(th);
      }
      j += n;
    } else {
      const th = h('th', 'wrap g-start', L(c.label)); th.rowSpan = 2; th.scope = 'col';
      r1.appendChild(th);
      j += 1;
    }
  }
  thead.appendChild(r1);
  if (r2.children.length) thead.appendChild(r2);
  table.appendChild(thead);

  const tbody = h('tbody');
  rows.forEach((row) => {
    const tr = h('tr', row.total ? 'total' : '');
    const name = h('th', null, L(row.name)); name.scope = 'row';
    tr.appendChild(name);
    cols.forEach((c, j) => {
      const text = (row.text || [])[j], v = (row.cells || [])[j];
      const td = h('td', null, text === undefined || text === '' ? '-' : text);
      const cls = [];
      if (groupStart[j]) cls.push('g-start');
      if (v === null || v === undefined) cls.push('nil');
      else if (v < 0) cls.push('neg');
      if (c.style === 'completion') { cls.push('c-center'); if (!row.total) cls.push(completionClass(v)); }
      if (c.style === 'irr') cls.push('irr');
      if (c.style === 'heat' && !row.total && v !== null && v !== undefined) {
        // one hue, deeper with magnitude; a zero yield is flagged like a zero completion
        if (v <= 0) cls.push('c-neg2');
        else td.style.background = 'rgba(42,120,214,' + (0.05 + 0.33 * Math.min(1, v / 20)).toFixed(3) + ')';
      }
      td.className = cls.filter(Boolean).join(' ');
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  wrap.appendChild(table);
  body.appendChild(wrap);
  // the second header row sticks just under the first (measured now: reading the height lays the table out)
  if (r1.offsetHeight) table.style.setProperty('--ff-head1', r1.offsetHeight + 'px');

  if (cols.some((c) => c.style === 'completion')) {
    const key = h('div', 'ff-key');
    key.appendChild(h('span', 'lbl', t('key_completion')));
    [['--ff-pos-2', 'key_pos2'], ['--ff-pos-1', 'key_pos1'], ['--ff-neg-1', 'key_neg1'], ['--ff-neg-2', 'key_neg2']].forEach(([v, k]) => {
      const sp = h('span'); const i = h('i'); i.style.background = 'var(' + v + ')';
      sp.appendChild(i); sp.appendChild(document.createTextNode(t(k))); key.appendChild(sp);
    });
    body.appendChild(key);
  }
  (doc.footnotes || []).forEach((f) => body.appendChild(h('p', 'ff-foot', L(f))));
}

/* ---------------------------------------------------------------- budget charts */
/* What a part of a stacked bar is coloured by. Slides name parts by month and source
   ("6月收息", "5月流入", "同4月收息"); every part of one month gets that month's colour, so a
   quarter needs three colours however many sources it has. A label with no month is its own key.
   The colours are assigned once for the whole month's report: the same colour means the same
   month in every chart of every panel, and one legend at the top says which is which. */
function partKey(label) {
  const m = /(\d{1,2})\s*月/.exec(label || '');
  return m ? 'm' + Number(m[1]) : (label || '');
}
function partMonth(key) { return /^m\d+$/.test(key) ? Number(key.slice(1)) : NaN; }
function partColors(sections) {
  const keys = [], names = {};
  sections.forEach((section) => section.blocks.forEach((b) => b.charts.forEach((c) => c.bars.forEach((bar) => (bar.segments || []).forEach((sg) => {
    const k = partKey(sg.label);
    if (!keys.includes(k)) { keys.push(k); names[k] = sg.label; }
  })))));
  // months run dark (earliest) to light (latest); anything else keeps the order it appears in
  const ordered = keys.every((k) => !isNaN(partMonth(k))) ? keys.slice().sort((x, y) => partMonth(x) - partMonth(y)) : keys;
  const n = ordered.length, map = {};
  // the ramp holds five steps that stay distinguishable (checked with the palette validator);
  // with more the bar is drawn plain and the breakdown lives in the tooltip and the table
  if (n > 5) return {keys: [], map: {}, names, plain: true};
  ordered.forEach((k, i) => { map[k] = n <= 1 ? RAMP[RAMP.length - 1] : RAMP[Math.round(i * (RAMP.length - 1) / (n - 1))]; });
  return {keys: ordered, map, names, plain: false};
}
/* the legend entry for a colour: the month's name, or the part's own label */
function partName(colors, key) {
  const m = partMonth(key);
  return isNaN(m) ? L(colors.names[key]) : new Date(2000, m - 1, 1).toLocaleDateString(locale(), {month: 'short'});
}
/* the text beside a part of a bar. Its colour already tells the month (see the legend), so the
   month is left out and only what the month does not say stays: the source word, if the slide
   has one ("收息" / "interest"), and the amount. "同4月收息" (same as April's) keeps its wording. */
const MONTH_WORD = /(\d{1,2}\s*月|\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t|tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b\.?)/g;
function partText(sg) {
  const full = L(sg.label) || '';
  const rest = /^(同|same as)/i.test(full) ? full : full.replace(MONTH_WORD, ' ').replace(/\s+/g, ' ').trim();
  return (rest + ' ' + V(sg)).trim();
}
/* a part's amount. The slide may print none ("同4月收息"): then its size was worked out from the
   rest of the bar, and it is shown as such wherever the amount is given. */
function PV(sg, bar) {
  if (sg.text) return V(sg);
  if (typeof sg.value !== 'number') return '';
  const text = sg.value.toLocaleString('en-US') + ((bar && bar.unit) || '');
  return V({value: sg.value, text}) + ' (' + t('derived') + ')';
}
function roundedTop(x, y, w, hgt, r) {
  r = Math.max(0, Math.min(r, hgt, w / 2));
  return 'M' + x + ',' + (y + hgt) + 'V' + (y + r) + 'Q' + x + ',' + y + ' ' + (x + r) + ',' + y + 'H' + (x + w - r) + 'Q' + (x + w) + ',' + y + ' ' + (x + w) + ',' + (y + r) + 'V' + (y + hgt) + 'Z';
}
function startsGroup(bar, prev) {
  if (!prev) return false;
  if (bar.group || prev.group) return bar.group !== prev.group;
  return bar.kind === 'budget';   // an unlabelled budget bar opens the next budget / actual pair
}
function kindLabel(kind) { return kind === 'budget' ? t('budget') : t('actual'); }
function showTip(ev, bar, chartTitle, colors) {
  const tip = $('ffTip');
  tip.textContent = '';
  tip.appendChild(h('b', null, V(bar)));
  tip.appendChild(h('div', 'who', [chartTitle, bar.group, bar.label].filter(Boolean).map(L).join(' · ')));
  (bar.segments || []).slice().reverse().forEach((sg) => {
    const row = h('div', 'part'); const i = h('i'); i.style.background = colors.map[partKey(sg.label)] || C_ACTUAL;
    row.appendChild(i); row.appendChild(document.createTextNode(L(sg.label))); row.appendChild(h('em', null, PV(sg, bar)));
    tip.appendChild(row);
  });
  tip.hidden = false;
  const box = ev.currentTarget.getBoundingClientRect();
  const px = ev.clientX !== undefined && ev.type !== 'focus' ? ev.clientX : box.left + box.width / 2;
  const py = ev.clientY !== undefined && ev.type !== 'focus' ? ev.clientY : box.top + 20;
  const w = tip.offsetWidth, hh = tip.offsetHeight;
  tip.style.left = Math.max(8, Math.min(window.innerWidth - w - 8, px + 14)) + 'px';
  tip.style.top = Math.max(8, Math.min(window.innerHeight - hh - 8, py - hh - 10)) + 'px';
}
function hideTip() { const tip = $('ffTip'); if (tip) tip.hidden = true; }

/* geometry. The width of one bar slot is worked out from the space on screen and is the same for
   every chart on the tab, so bars are the same size in every panel and a panel is exactly as
   wide as its charts need. The panels share one row, as on the slide, down to a slot of
   SIDE_BY_SIDE_MIN (a tablet-width window); narrower than that each panel takes a full row.
   Below COMPACT the labels are set a size smaller so they still fit over their bars. Fixed parts: the breakdown list beside a stacked bar, the gap
   between groups of bars, the gaps between charts and between blocks. */
const G = {SIDE: 90, SIDE_MAX: 190, GAP: 20, PAD: 4, CHART_GAP: 28, BLOCK_GAP: 30, MIN_SLOT: 46, MAX_SLOT: 110, SIDE_BY_SIDE_MIN: 46, COMPACT: 62};
/* room for the breakdown listed beside a stacked bar: as wide as its longest line in the
   language on screen (English labels run longer than the Chinese ones), within limits */
let measurer = null;
function textWidth(text) {
  if (!measurer) measurer = document.createElement('canvas').getContext('2d');
  measurer.font = '12px ' + getComputedStyle(document.body).fontFamily;
  return measurer.measureText(text).width;
}
function sideWidth(bar) {
  const lines = (bar.segments || []).map(partText);
  const widest = Math.max.apply(null, lines.map(textWidth).concat([0]));
  return Math.max(G.SIDE, Math.min(G.SIDE_MAX, Math.ceil(widest) + 30));
}
function chartFixed(chart, colors) {
  let w = 2 * G.PAD;
  chart.bars.forEach((bar, i) => {
    if (startsGroup(bar, chart.bars[i - 1])) w += G.GAP;
    if (!colors.plain && (bar.segments || []).length > 1) w += sideWidth(bar);
  });
  return w;
}
function sectionMetrics(section, colors) {
  let bars = 0, fixed = 0;
  const blocks = section.blocks.map((block) => {
    let bBars = 0, bFixed = 0;
    block.charts.forEach((chart, i) => { bBars += chart.bars.length; bFixed += chartFixed(chart, colors) + (i ? G.CHART_GAP : 0); });
    bars += bBars; fixed += bFixed;
    return {bars: bBars, fixed: bFixed};
  });
  fixed += Math.max(0, blocks.length - 1) * G.BLOCK_GAP;
  return {bars, fixed, blocks};
}

function drawChart(chart, max, colors, slot) {
  const compact = slot < G.COMPACT;
  const BAR = Math.round(Math.max(18, Math.min(40, slot * 0.42)));
  const PLOT = slot >= 80 ? 270 : (compact ? 230 : 250), TOP = 30, BOTTOM = 46;
  let x = G.PAD;
  const colsLayout = chart.bars.map((bar, i) => {
    if (startsGroup(bar, chart.bars[i - 1])) x += G.GAP;
    const side = !colors.plain && (bar.segments || []).length > 1 ? sideWidth(bar) : 0;
    const col = {bar, x, cx: x + slot / 2};
    x += slot + side;
    return col;
  });
  const W = x + G.PAD, H = TOP + PLOT + BOTTOM, base = TOP + PLOT;
  const svg = s('svg', {width: W, height: H, viewBox: '0 0 ' + W + ' ' + H, role: 'group', 'aria-label': L(chart.title) || t('tab_budget')});
  if (compact) svg.setAttribute('class', 'sm');
  svg.appendChild(s('line', {class: 'axis', x1: 0, x2: W, y1: base + 0.5, y2: base + 0.5}));

  colsLayout.forEach((col) => {
    const bar = col.bar, g = s('g', {class: 'col'});
    const hgt = bar.value > 0 ? Math.max(2, (bar.value / max) * PLOT) : 0;
    const bx = col.cx - BAR / 2, top = base - hgt;
    const segs = bar.segments || [];
    if (bar.kind === 'actual' && segs.length && !colors.plain) {
      const sum = segs.reduce((a, sg) => a + Math.max(0, sg.value), 0) || 1;
      let y0 = base;
      segs.forEach((sg, i) => {
        const sh = (Math.max(0, sg.value) / sum) * hgt, isTop = i === segs.length - 1;
        // a 2px gap in the surface colour separates the parts; no outline
        const gap = isTop ? 0 : Math.min(2, sh / 2);
        const y = y0 - sh + gap, hh = Math.max(0.5, sh - gap);
        if (isTop) g.appendChild(s('path', {class: 'bar', d: roundedTop(bx, y, BAR, hh, 4), fill: colors.map[partKey(sg.label)]}));
        else g.appendChild(s('rect', {class: 'bar', x: bx, y, width: BAR, height: hh, fill: colors.map[partKey(sg.label)]}));
        y0 -= sh;
      });
      if (segs.length > 1) {
        // the breakdown is listed beside the bar: latest on top, as on the slide
        segs.forEach((sg, i) => {
          const ly = base - 8 - i * 17, lx = col.cx + BAR / 2 + 10;
          g.appendChild(s('rect', {x: lx, y: ly - 9, width: 9, height: 9, rx: 1.5, fill: colors.map[partKey(sg.label)]}));
          g.appendChild(s('text', {class: 'pl', x: lx + 13, y: ly}, partText(sg)));
        });
      }
    } else if (hgt > 0) {
      g.appendChild(s('path', {class: 'bar', d: roundedTop(bx, top, BAR, hgt, 4), fill: bar.kind === 'budget' ? C_BUDGET : C_ACTUAL}));
    }
    g.appendChild(s('text', {class: 'v', x: col.cx, y: top - 8, 'text-anchor': 'middle'}, V(bar)));
    const shown = L(bar.label) || ''; const words = bar.group ? [shown] : shown.split(/\s+/).filter(Boolean).slice(0, 2);
    words.forEach((wd, i) => g.appendChild(s('text', {class: 'xl', x: col.cx, y: base + 17 + i * 15, 'text-anchor': 'middle'}, wd)));
    const hit = s('rect', {class: 'hit', x: col.x, y: 4, width: slot, height: base - 4, tabindex: 0, role: 'img',
      'aria-label': [L(chart.title), L(bar.group), L(bar.label), V(bar)].filter(Boolean).join(' ') + (segs.length ? ' (' + segs.map((sg) => (L(sg.label) + ' ' + PV(sg, bar)).trim()).join(', ') + ')' : '')});
    ['pointerenter', 'pointermove', 'focus'].forEach((evn) => hit.addEventListener(evn, (ev) => showTip(ev, bar, chart.title, colors)));
    ['pointerleave', 'blur'].forEach((evn) => hit.addEventListener(evn, hideTip));
    g.appendChild(hit);
    svg.appendChild(g);
  });
  // one label under each run of bars that share a group
  for (let i = 0; i < colsLayout.length;) {
    const gname = colsLayout[i].bar.group;
    let j = i;
    while (j + 1 < colsLayout.length && colsLayout[j + 1].bar.group === gname) j++;
    if (gname) svg.appendChild(s('text', {class: 'xg', x: (colsLayout[i].cx + colsLayout[j].cx) / 2, y: base + 34, 'text-anchor': 'middle'}, L(gname)));
    i = j + 1;
  }
  const fig = h('figure', 'ff-chart');
  fig.style.width = W + 'px';   // a long (translated) title wraps instead of widening the chart
  fig.appendChild(h('figcaption', null, L(chart.title) || ''));
  fig.appendChild(svg);
  return fig;
}

/* redraw the charts when the space changes (window resize, sidebar, rotation) */
let resizeWatch = null;
function watchWidth(el, fn) {
  if (resizeWatch) { resizeWatch.disconnect(); resizeWatch = null; }
  if (!el || !window.ResizeObserver) return;
  let last = el.clientWidth;
  resizeWatch = new ResizeObserver(() => {
    const w = el.clientWidth;
    if (w && Math.abs(w - last) > 1) { last = w; fn(); }
  });
  resizeWatch.observe(el);
}

function renderBudget(body, doc) {
  const colors = partColors(doc.sections || []);
  const legend = h('div', 'ff-legend top');
  const item = (color, label) => { const sp = h('span'); const i = h('i'); i.style.background = color; sp.appendChild(i); sp.appendChild(document.createTextNode(label)); return sp; };
  legend.appendChild(item(C_BUDGET, t('budget')));
  legend.appendChild(item(C_ACTUAL, t('actual')));
  if (colors.keys.length) {
    const sep = h('span', 'sep'); sep.title = t('parts'); sep.setAttribute('role', 'separator'); sep.setAttribute('aria-label', t('parts'));
    legend.appendChild(sep);
    colors.keys.forEach((k) => legend.appendChild(item(colors.map[k], partName(colors, k))));
  }
  body.appendChild(legend);
  const sections = (doc.sections || []).map((section) => {
    const bars = [];
    section.blocks.forEach((b) => b.charts.forEach((c) => c.bars.forEach((bar) => bars.push(bar))));
    // one value scale for the whole section, as on the slide
    return {section, colors, m: sectionMetrics(section, colors), max: Math.max.apply(null, bars.map((b) => b.value).concat([1])), blockEls: []};
  });
  const grid = h('div', 'ff-sections' + (sections.length === 1 ? ' one' : ''));

  sections.forEach((x) => {
    const section = x.section, colors = x.colors;
    const el = h('section', 'ff-section');
    const header = h('header');
    header.appendChild(h('h3', null, L(section.title)));
    el.appendChild(header);

    const blocks = h('div', 'ff-blocks');
    section.blocks.forEach((block) => {
      const b = h('div', 'ff-block');
      const charts = h('div', 'ff-charts');
      b.appendChild(charts);
      if (block.notes && block.notes.length) {
        const ul = h('ul', 'ff-notes');
        block.notes.forEach((n) => ul.appendChild(h('li', null, L(n))));
        b.appendChild(ul);
      }
      blocks.appendChild(b);
      x.blockEls.push({el: b, chartsEl: charts, block});
    });
    x.blocksEl = blocks;
    el.appendChild(blocks);

    // the same numbers without the picture
    const det = h('details', 'ff-data');
    det.appendChild(h('summary', null, t('data_table')));
    const table = h('table'), thead = h('thead'), hr = h('tr');
    [['th_chart', ''], ['th_item', ''], ['th_value', 'num'], ['th_parts', '']].forEach(([k, c]) => hr.appendChild(h('th', c, t(k))));
    thead.appendChild(hr); table.appendChild(thead);
    const tb = h('tbody');
    section.blocks.forEach((block) => block.charts.forEach((chart) => chart.bars.forEach((bar) => {
      const tr = h('tr');
      tr.appendChild(h('td', null, L(chart.title || section.title)));
      tr.appendChild(h('td', null, [bar.group, bar.label].filter(Boolean).map(L).join(' · ') + (/预算|实际|budget|actual/i.test(bar.label) ? '' : ' (' + kindLabel(bar.kind) + ')')));
      tr.appendChild(h('td', 'num', V(bar)));
      tr.appendChild(h('td', null, (bar.segments || []).map((sg) => (L(sg.label) + ' ' + PV(sg, bar)).trim()).join(' · ')));
      tb.appendChild(tr);
    })));
    table.appendChild(tb); det.appendChild(table);
    el.appendChild(det);
    grid.appendChild(el);
  });
  body.appendChild(grid);

  const clamp = (v) => Math.max(G.MIN_SLOT, Math.min(G.MAX_SLOT, Math.floor(v)));
  const layout = () => {
    hideTip();
    // what a panel adds around its charts: the padding of .ff-blocks and the panel border
    const first = sections[0];
    const cs = getComputedStyle(first.blocksEl);
    const chrome = parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight) + 2;
    const W = grid.clientWidth, colGap = parseFloat(getComputedStyle(grid).columnGap) || 0;
    const allBars = sections.reduce((a, x) => a + x.m.bars, 0) || 1;
    // 1. panels side by side, as on the slide, whenever the bars and their labels still fit
    const beside = (W - colGap * (sections.length - 1) - sections.reduce((a, x) => a + x.m.fixed + chrome, 0)) / allBars;
    const sideBySide = sections.length > 1 && beside >= G.SIDE_BY_SIDE_MIN;
    // 2. otherwise one panel per row. Either way every panel uses the same slot, so bars match.
    const slot = sideBySide ? clamp(beside) : clamp(Math.min.apply(null, sections.map((x) => (W - chrome - x.m.fixed) / Math.max(1, x.m.bars))));
    grid.style.gridTemplateColumns = sideBySide
      ? sections.map((x) => 'minmax(0,' + Math.round(x.m.bars * slot + x.m.fixed + chrome) + 'fr)').join(' ')
      : 'minmax(0,1fr)';
    sections.forEach((x) => {
      const avail = x.blocksEl.clientWidth - (chrome - 2);
      x.blockEls.forEach((b, k) => {
        b.chartsEl.textContent = '';
        b.block.charts.forEach((chart) => b.chartsEl.appendChild(drawChart(chart, x.max, x.colors, slot)));
        const w = x.m.blocks[k].bars * slot + x.m.blocks[k].fixed;
        b.el.style.flexBasis = w + 'px';
        // a lone block with room to spare puts its commentary beside the chart instead of under it
        b.el.classList.toggle('row', x.blockEls.length === 1 && avail - w >= 300);
      });
    });
  };
  layout();
  watchWidth(grid, layout);
}

/* ---------------------------------------------------------------- upload */
function buildUploadDialog() {
  const ov = h('div', 'overlay'); ov.id = 'ffOverlay'; ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-modal', 'true');
  const panel = h('div', 'ov-panel narrow');
  const head = h('div', 'ov-head'); head.appendChild(h('b')).id = 'ffUpTitle';
  const close = h('button'); close.type = 'button'; close.id = 'ffUpClose'; head.appendChild(close);
  panel.appendChild(head);
  const form = h('form', 'form'); form.id = 'ffForm';
  const drop = h('div', 'drop'); drop.id = 'ffDrop';
  const file = h('input'); file.type = 'file'; file.id = 'ffFile'; file.accept = 'image/png,image/jpeg,image/webp,image/gif';
  const dt = h('div', 'drop-txt'); dt.appendChild(h('b')).id = 'ffDropTxt'; dt.appendChild(h('span')).id = 'ffDropTypes';
  const fname = h('div', 'drop-file'); fname.id = 'ffFileName';
  drop.appendChild(file); drop.appendChild(dt); drop.appendChild(fname);
  form.appendChild(drop);
  const grid = h('div', 'grid2');
  const mk = (id, lblId, control) => { const l = h('label'); l.appendChild(h('span')).id = lblId; control.id = id; l.appendChild(control); grid.appendChild(l); return control; };
  const selTab = mk('ffUpTab', 'ffUpTabLbl', h('select'));
  const inYear = mk('ffUpYear', 'ffUpYearLbl', h('input')); inYear.type = 'number'; inYear.min = 2000; inYear.max = 2100; inYear.required = true;
  const selMonth = mk('ffUpMonth', 'ffUpMonthLbl', h('select'));
  form.appendChild(grid);
  form.appendChild(h('p', 'hint')).id = 'ffUpHint';
  const foot = h('div', 'form-foot');
  foot.appendChild(h('span', 'form-msg')).id = 'ffUpMsg';
  const cancel = h('button', 'btn ghost'); cancel.type = 'button'; cancel.id = 'ffUpCancel';
  const submit = h('button', 'btn primary'); submit.type = 'submit'; submit.id = 'ffUpSubmit';
  foot.appendChild(cancel); foot.appendChild(submit);
  form.appendChild(foot);
  panel.appendChild(form); ov.appendChild(panel);
  $('view-factors').appendChild(ov);

  const pick = (f) => {
    state.picked = f || null;
    const old = drop.querySelector('.ff-preview'); if (old) { URL.revokeObjectURL(old.src); old.remove(); }
    fname.textContent = f ? f.name + ' · ' + Math.max(1, Math.round(f.size / 1024)) + ' KB' : '';
    if (f && MIME_EXT[f.type]) { const img = h('img', 'ff-preview'); img.alt = ''; img.src = URL.createObjectURL(f); drop.appendChild(img); }
    setMsg('');
  };
  ov._pick = pick;
  file.addEventListener('change', () => pick(file.files[0]));
  ['dragenter', 'dragover'].forEach((e) => drop.addEventListener(e, (ev) => { ev.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach((e) => drop.addEventListener(e, () => drop.classList.remove('over')));
  document.addEventListener('paste', (ev) => {
    if (!ov.classList.contains('open')) return;
    const f = Array.from((ev.clipboardData && ev.clipboardData.files) || []).find((x) => MIME_EXT[x.type]);
    if (f) { ev.preventDefault(); pick(f); }
  });
  [selTab, inYear, selMonth].forEach((n) => n.addEventListener('change', paintReplaceHint));
  inYear.addEventListener('input', paintReplaceHint);
  close.addEventListener('click', closeUpload);
  cancel.addEventListener('click', closeUpload);
  ov.addEventListener('click', (ev) => { if (ev.target === ov) closeUpload(); });
  document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape' && ov.classList.contains('open')) closeUpload(); });
  form.addEventListener('submit', submitUpload);
}
function paintUploadDialog() {
  if (!$('ffOverlay')) return;
  $('ffUpTitle').textContent = t('up_title');
  $('ffUpClose').textContent = t('close');
  $('ffDropTxt').textContent = t('up_drop');
  $('ffDropTypes').textContent = t('up_types');
  $('ffUpTabLbl').textContent = t('up_tab');
  $('ffUpYearLbl').textContent = t('up_year');
  $('ffUpMonthLbl').textContent = t('up_month');
  $('ffUpCancel').textContent = t('cancel');
  $('ffUpSubmit').textContent = t('up_submit');
  const selTab = $('ffUpTab'), selMonth = $('ffUpMonth');
  const curTab = selTab.value, curMonth = selMonth.value;
  selTab.textContent = ''; selMonth.textContent = '';
  TABS.forEach((tab) => { const o = h('option', null, t('tab_' + tab)); o.value = tab; selTab.appendChild(o); });
  for (let m = 1; m <= 12; m++) { const o = h('option', null, monthName(m)); o.value = String(m); selMonth.appendChild(o); }
  if (curTab) selTab.value = curTab;
  if (curMonth) selMonth.value = curMonth;
  paintReplaceHint();
}
function uploadTarget() {
  const year = Number($('ffUpYear').value), month = Number($('ffUpMonth').value);
  return {tab: $('ffUpTab').value, year, month, ym: year + '-' + String(month).padStart(2, '0')};
}
function paintReplaceHint() {
  const hint = $('ffUpHint'); if (!hint) return;
  const tg = uploadTarget();
  const exists = months(tg.tab).includes(tg.ym);
  hint.textContent = t('up_hint') + (exists ? ' ' : '');
  if (exists) hint.appendChild(h('b', 'ff-replace', t('up_replace')));
}
function setMsg(text, cls) { const m = $('ffUpMsg'); m.className = 'form-msg' + (cls ? ' ' + cls : ''); m.textContent = text || ''; }
function openUpload() {
  const now = new Date();
  $('ffUpTab').value = state.tab;
  // default to the month after the newest one shown, or the current month
  const all = months(state.tab), last = all[all.length - 1];
  let y = now.getFullYear(), m = now.getMonth() + 1;
  if (last) { y = Number(last.slice(0, 4)); m = Number(last.slice(5)) + 1; if (m > 12) { m = 1; y += 1; } }
  $('ffUpYear').value = y; $('ffUpMonth').value = String(m);
  $('ffFile').value = ''; $('ffOverlay')._pick(null);
  $('ffUpSubmit').disabled = false;
  paintReplaceHint();
  $('ffOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeUpload() {
  $('ffOverlay').classList.remove('open');
  if (!document.querySelector('.overlay.open')) document.body.style.overflow = '';
}
async function submitUpload(ev) {
  ev.preventDefault();
  const f = state.picked, tg = uploadTarget();
  if (!f) { setMsg(t('up_need_file'), 'err'); return; }
  if (!MIME_EXT[f.type]) { setMsg(t('up_bad_type'), 'err'); return; }
  if (f.size > MAX_BYTES) { setMsg(t('up_too_big'), 'err'); return; }
  if (!(tg.year >= 2000 && tg.year <= 2100)) { setMsg(t('up_year'), 'err'); return; }
  const DL = window.DataLayer, btn = $('ffUpSubmit');
  btn.disabled = true;
  try {
    if (DL && DL.mode === 'static') {
      setMsg(t('up_saving'));
      const bytes = new Uint8Array(await f.arrayBuffer());
      const name = tg.tab + '-' + tg.ym + '.' + MIME_EXT[f.type];
      await DL.commitFile('factors/incoming/' + name, bytes, 'factors: upload ' + name);
      setMsg(t('up_pending'), 'ok');
      toast(t('up_pending'), DL.actionsUrl ? {text: t('view_actions'), href: DL.actionsUrl()} : null);
    } else {
      setMsg(t('up_working'));
      const fd = new FormData();
      fd.append('file', f); fd.append('tab', tg.tab); fd.append('year', String(tg.year)); fd.append('month', String(tg.month));
      const r = await fetch('/api/factors/upload', {method: 'POST', body: fd});
      let data = null; try { data = await r.json(); } catch (e) {}
      if (r.status === 401) { location.href = '/login.html?next=' + encodeURIComponent(location.hash); return; }
      if (!r.ok) throw new Error((data && data.error) || (r.status + ' ' + r.statusText));
      await loadIndex(true);
      closeUpload();
      toast(t('up_done', {tab: t('tab_' + tg.tab), month: monthLabel(tg.ym)}));
      if (location.hash === '#/factors/' + tg.tab + '/' + tg.ym) show(tg.tab, tg.ym); else go(tg.tab, tg.ym);
    }
  } catch (e) {
    setMsg(e.message || String(e), 'err');
  } finally {
    btn.disabled = false;
  }
}

/* ---------------------------------------------------------------- note for a month */
function buildNoteDialog() {
  const ov = h('div', 'overlay'); ov.id = 'ffNoteOverlay'; ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-modal', 'true');
  const panel = h('div', 'ov-panel narrow');
  const head = h('div', 'ov-head'); head.appendChild(h('b')).id = 'ffNoteTitle';
  const close = h('button'); close.type = 'button'; close.id = 'ffNoteClose'; head.appendChild(close);
  panel.appendChild(head);
  const form = h('form', 'form'); form.id = 'ffNoteForm';
  const field = h('label', 'ff-field'); field.appendChild(h('span')).id = 'ffNoteLbl';
  const text = h('textarea'); text.id = 'ffNoteText'; text.rows = 5; text.maxLength = 8000;
  field.appendChild(text); form.appendChild(field);
  form.appendChild(h('p', 'hint')).id = 'ffNoteHint';
  const auto = h('div', 'ff-autonote'); auto.id = 'ffNoteAuto'; auto.hidden = true;
  form.appendChild(auto);
  const copy = h('button', 'btn small ghost'); copy.type = 'button'; copy.id = 'ffNoteCopy'; copy.hidden = true;
  form.appendChild(copy);
  const warn = h('div', 'ff-warnpick'); warn.id = 'ffNoteWarnBox';
  warn.appendChild(h('b')).id = 'ffNoteWarnLbl';
  warn.appendChild(h('p', 'hint')).id = 'ffNoteWarnHint';
  warn.appendChild(h('div')).id = 'ffNoteWarnList';
  form.appendChild(warn);
  const foot = h('div', 'form-foot');
  foot.appendChild(h('span', 'form-msg')).id = 'ffNoteMsg';
  const cancel = h('button', 'btn ghost'); cancel.type = 'button'; cancel.id = 'ffNoteCancel';
  const submit = h('button', 'btn primary'); submit.type = 'submit'; submit.id = 'ffNoteSubmit';
  foot.appendChild(cancel); foot.appendChild(submit);
  form.appendChild(foot);
  panel.appendChild(form); ov.appendChild(panel);
  $('view-factors').appendChild(ov);

  close.addEventListener('click', closeNote);
  cancel.addEventListener('click', closeNote);
  ov.addEventListener('click', (ev) => { if (ev.target === ov) closeNote(); });
  document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape' && ov.classList.contains('open')) closeNote(); });
  form.addEventListener('submit', saveNote);
}
function noteMsg(text, cls) { const m = $('ffNoteMsg'); m.className = 'form-msg' + (cls ? ' ' + cls : ''); m.textContent = text || ''; }
/* explain = opened from the warning box: the warnings on screen start ticked */
function openNote(explain) {
  const doc = state.doc;
  if (!doc) return;
  const tab = state.tab, ym = state.ym;
  $('ffNoteTitle').textContent = t('note_dlg', {tab: t('tab_' + tab), month: monthLabel(ym)});
  $('ffNoteClose').textContent = t('close');
  $('ffNoteLbl').textContent = t('note_label');
  $('ffNoteHint').textContent = t('note_hint');
  $('ffNoteWarnLbl').textContent = t('note_warns');
  $('ffNoteWarnHint').textContent = t('note_tick');
  $('ffNoteCancel').textContent = t('cancel');
  $('ffNoteSubmit').textContent = t('note_save');
  $('ffNoteSubmit').disabled = false;
  $('ffNoteText').value = (doc.notes || []).join('\n');
  noteMsg('');
  const auto = $('ffNoteAuto'); auto.textContent = ''; auto.hidden = !(doc.auto_notes || []).length;
  if (!auto.hidden) {
    auto.appendChild(h('b', null, t('note_auto')));
    doc.auto_notes.forEach((x) => auto.appendChild(h('p', null, LQ(x))));
  }

  const all = doc.warnings || [], hidden = doc.dismissed || [];
  const list = $('ffNoteWarnList'); list.textContent = '';
  $('ffNoteWarnBox').hidden = all.length === 0;
  all.forEach((w) => {
    const row = h('label', 'ff-check');
    const cb = h('input'); cb.type = 'checkbox'; cb.value = w; cb.checked = hidden.includes(w) || !!explain;
    row.appendChild(cb); row.appendChild(h('span', null, LQ(w)));
    list.appendChild(row);
  });

  // the month before often needs the same explanation: offer its note
  const copy = $('ffNoteCopy'); copy.hidden = true; copy.onclick = null;
  const list2 = months(tab), prev = list2[list2.indexOf(ym) - 1];
  if (prev && !(doc.notes || []).length && !(doc.auto_notes || []).length) {
    getJson('data/factors/' + tab + '/' + prev + '.json').then((before) => {
      if (!before || !(before.notes || []).length || state.ym !== ym || state.tab !== tab) return;
      copy.textContent = t('note_copy', {month: monthLabel(prev)});
      copy.onclick = () => { $('ffNoteText').value = before.notes.join('\n'); $('ffNoteText').focus(); };
      copy.hidden = false;
    }).catch(() => {});
  }

  $('ffNoteOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
  setTimeout(() => $('ffNoteText').focus(), 50);
}
function closeNote() {
  $('ffNoteOverlay').classList.remove('open');
  if (!document.querySelector('.overlay.open')) document.body.style.overflow = '';
}
async function saveNote(ev) {
  ev.preventDefault();
  const doc = state.doc, tab = state.tab, ym = state.ym;
  if (!doc) return;
  const notes = $('ffNoteText').value.split(/\n+/).map((x) => x.trim()).filter(Boolean);
  const dismissed = Array.from(document.querySelectorAll('#ffNoteWarnList input:checked')).map((cb) => cb.value);
  if (dismissed.length && !notes.length) { noteMsg(t('note_need_text'), 'err'); return; }
  const DL = window.DataLayer, btn = $('ffNoteSubmit');
  btn.disabled = true; noteMsg(t('note_saving'));
  try {
    let pending = false;
    if (DL && DL.mode === 'static') {
      // on GitHub Pages the month's data file is committed with the note in it
      const next = Object.assign({}, doc, {notes, dismissed});
      const bytes = new TextEncoder().encode(JSON.stringify(next, null, 2) + '\n');
      await DL.commitFile('factors/data/' + tab + '/' + ym + '.json', bytes, 'factors: note for ' + tab + ' ' + ym);
      state.doc = next; pending = true;
    } else {
      const r = await fetch('/api/factors/' + tab + '/' + ym + '/notes', {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({notes, dismissed})});
      let data = null; try { data = await r.json(); } catch (e) {}
      if (r.status === 401) { location.href = '/login.html?next=' + encodeURIComponent(location.hash); return; }
      if (!r.ok) throw new Error((data && data.error) || (r.status + ' ' + r.statusText));
      state.doc = Object.assign({}, doc, {notes: data.notes, dismissed: data.dismissed});
    }
    closeNote();
    if (state.tab === tab && state.ym === ym) renderDoc($('ffBody'), state.doc);
    if (pending) toast(t('note_pending'), DL.actionsUrl ? {text: t('view_actions'), href: DL.actionsUrl()} : null);
    else toast(t('note_saved'));
  } catch (e) {
    noteMsg(e.message || String(e), 'err');
  } finally {
    btn.disabled = false;
  }
}

/* ---------------------------------------------------------------- change a month's date */
function buildMoveDialog() {
  const ov = h('div', 'overlay'); ov.id = 'ffMoveOverlay'; ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-modal', 'true');
  const panel = h('div', 'ov-panel narrow');
  const head = h('div', 'ov-head'); head.appendChild(h('b')).id = 'ffMoveTitle';
  const close = h('button'); close.type = 'button'; close.id = 'ffMoveClose'; head.appendChild(close);
  panel.appendChild(head);
  const form = h('form', 'form'); form.id = 'ffMoveForm';
  form.appendChild(h('p', 'hint')).id = 'ffMoveNow';
  const grid = h('div', 'grid2');
  const ly = h('label'); ly.appendChild(h('span')).id = 'ffMoveYearLbl';
  const year = h('input'); year.type = 'number'; year.id = 'ffMoveYear'; year.min = 2000; year.max = 2100; year.required = true; ly.appendChild(year);
  const lm = h('label'); lm.appendChild(h('span')).id = 'ffMoveMonthLbl';
  const month = h('select'); month.id = 'ffMoveMonth'; lm.appendChild(month);
  grid.appendChild(ly); grid.appendChild(lm);
  form.appendChild(grid);
  const row = h('label', 'ff-check ff-replace-row'); row.id = 'ffMoveReplaceRow'; row.hidden = true;
  const cb = h('input'); cb.type = 'checkbox'; cb.id = 'ffMoveReplace';
  row.appendChild(cb); row.appendChild(h('span')).id = 'ffMoveReplaceLbl';
  form.appendChild(row);
  const foot = h('div', 'form-foot');
  foot.appendChild(h('span', 'form-msg')).id = 'ffMoveMsg';
  const cancel = h('button', 'btn ghost'); cancel.type = 'button'; cancel.id = 'ffMoveCancel';
  const submit = h('button', 'btn primary'); submit.type = 'submit'; submit.id = 'ffMoveSubmit';
  foot.appendChild(cancel); foot.appendChild(submit);
  form.appendChild(foot);
  panel.appendChild(form); ov.appendChild(panel);
  $('view-factors').appendChild(ov);

  [year, month].forEach((n) => { n.addEventListener('change', paintMoveTarget); n.addEventListener('input', paintMoveTarget); });
  close.addEventListener('click', closeMove);
  cancel.addEventListener('click', closeMove);
  ov.addEventListener('click', (ev) => { if (ev.target === ov) closeMove(); });
  document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape' && ov.classList.contains('open')) closeMove(); });
  form.addEventListener('submit', submitMove);
}
function moveMsg(text, cls) { const m = $('ffMoveMsg'); m.className = 'form-msg' + (cls ? ' ' + cls : ''); m.textContent = text || ''; }
function moveTarget() {
  const year = Number($('ffMoveYear').value), month = Number($('ffMoveMonth').value);
  return {year, month, ym: year + '-' + String(month).padStart(2, '0')};
}
/* show the "replace" tick only when the chosen month already holds other data */
function paintMoveTarget() {
  const tg = moveTarget(), row = $('ffMoveReplaceRow');
  const taken = tg.ym !== state.ym && months(state.tab).includes(tg.ym);
  row.hidden = !taken;
  if (taken) $('ffMoveReplaceLbl').textContent = t('move_replace', {month: monthLabel(tg.ym)});
  else $('ffMoveReplace').checked = false;
  moveMsg('');
}
function openMove() {
  if (!state.doc || !state.ym) return;
  $('ffMoveTitle').textContent = t('move_dlg', {tab: t('tab_' + state.tab)});
  $('ffMoveClose').textContent = t('close');
  $('ffMoveNow').textContent = t('move_now', {month: monthLabel(state.ym)});
  $('ffMoveYearLbl').textContent = t('up_year');
  $('ffMoveMonthLbl').textContent = t('up_month');
  $('ffMoveCancel').textContent = t('cancel');
  $('ffMoveSubmit').textContent = t('move_submit');
  $('ffMoveSubmit').disabled = false;
  const sel = $('ffMoveMonth'); sel.textContent = '';
  for (let m = 1; m <= 12; m++) { const o = h('option', null, monthName(m)); o.value = String(m); sel.appendChild(o); }
  $('ffMoveYear').value = state.ym.slice(0, 4);
  sel.value = String(Number(state.ym.slice(5)));
  $('ffMoveReplace').checked = false;
  paintMoveTarget();
  $('ffMoveOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeMove() {
  $('ffMoveOverlay').classList.remove('open');
  if (!document.querySelector('.overlay.open')) document.body.style.overflow = '';
}
async function submitMove(ev) {
  ev.preventDefault();
  const tab = state.tab, from = state.ym, tg = moveTarget();
  if (!(tg.year >= 2000 && tg.year <= 2100)) { moveMsg(t('up_year'), 'err'); return; }
  if (tg.ym === from) { moveMsg(t('move_same'), 'err'); return; }
  const taken = months(tab).includes(tg.ym), replace = $('ffMoveReplace').checked;
  if (taken && !replace) { moveMsg(t('move_need_replace'), 'err'); return; }
  const DL = window.DataLayer, btn = $('ffMoveSubmit');
  btn.disabled = true; moveMsg(t('move_working'));
  try {
    if (DL && DL.mode === 'static') {
      // on GitHub Pages the request is committed and the build workflow applies it
      const request = {to: tg.ym, replace, requested_at: new Date().toISOString()};
      const name = tab + '-' + from + '.move.json';
      await DL.commitFile('factors/incoming/' + name, new TextEncoder().encode(JSON.stringify(request, null, 2) + '\n'), 'factors: change date ' + tab + ' ' + from + ' -> ' + tg.ym);
      closeMove();
      toast(t('move_pending'), DL.actionsUrl ? {text: t('view_actions'), href: DL.actionsUrl()} : null);
    } else {
      const r = await fetch('/api/factors/' + tab + '/' + from + '/move', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({year: tg.year, month: tg.month, replace})});
      let data = null; try { data = await r.json(); } catch (e) {}
      if (r.status === 401) { location.href = '/login.html?next=' + encodeURIComponent(location.hash); return; }
      if (!r.ok) throw new Error((data && data.error) || (r.status + ' ' + r.statusText));
      await loadIndex(true);
      closeMove();
      toast(t('move_done', {month: monthLabel(tg.ym)}));
      go(tab, tg.ym);
    }
  } catch (e) {
    moveMsg(e.message || String(e), 'err');
  } finally {
    btn.disabled = false;
  }
}

/* ---------------------------------------------------------------- panel integration */
function toLang(lang) { return lang === 'cn' || lang === 'zh' ? 'cn' : 'en'; }
window.FundFactors = {
  mount(lang, tab, ym) {
    state.lang = toLang(lang);
    return show(tab || state.tab, ym || null);
  },
  setLanguage(lang) {
    const next = toLang(lang);
    if (next === state.lang) return;
    state.lang = next;
    if (state.built && !$('view-factors').hidden) show(state.tab, state.ym);
  },
};
window.addEventListener('scroll', hideTip, {passive: true});
})();
