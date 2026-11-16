/* Macro / Market — a view of the AID Research Panel (#/macro/<topic>/<YYYY-MM>).
   Two fixed topics (tags): the weekly updates and the market's rate expectations (市场加息预期); each
   has one brief per month: a title and the slides of a deck, in upload order. Each slide was read by
   Claude (macro/scripts/extract_macro.py) into blocks: charts (line, vertical bars, horizontal
   bars with parts), tables with coloured cells, bullet lists, call-outs, text and footnotes; this
   file draws them. The data comes from data/macro/<YYYY-MM>.json. Uploading several screenshots
   at once:
     local server   POST /api/macro/upload, read at once (one Claude call per slide)
     GitHub Pages   the images are committed to macro/incoming/ and the build workflow reads them
   Exposes window.MacroMarket = { mount(lang, month), setLanguage(lang) }; lang is "en" | "cn".
   Every label that comes from the data is inserted with textContent. */
(function () {
'use strict';

const SVG_NS = 'http://www.w3.org/2000/svg';
const SERIES_COLORS = ['#1d4e89', '#9a9a9a', '#2a78d6', '#c58b1a', '#5b9a6b', '#8a5bb0'];
const C_PART = '#1d4e89', C_REST = '#bdbdbd';
const MIME_EXT = {'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp', 'image/gif': 'gif'};
const MAX_BYTES = 5 * 1024 * 1024;

const STR = {
  en: {
    year: 'Year', month: 'Month', upload: 'Upload slides', empty_title: 'No brief yet',
    empty_text: 'Upload the screenshots of a deck: Claude reads each slide into charts and tables, in order.',
    load_error: 'The brief could not be loaded', slide: 'Slide {n}', warn_title: 'Check against the slides',
    extracted: 'Read from the uploaded slides on {date}', by_model: 'by {model}', manual: 'transcribed by hand',
    source: 'View slide image', en_make: 'Create English labels', en_working: 'Creating the English labels…', en_done: 'English labels created',
    up_title: 'Upload slides', up_brief: 'Brief title (optional)', up_brief_ph: 'Defaults to the first slide title',
    up_drop: 'Drop the slide screenshots here or click to choose', up_types: 'PNG, JPEG or WebP · several at once · read in the order listed',
    up_order: 'Slides in reading order', up_hint: 'A month that already has a brief is replaced by the new upload.',
    up_replace: 'This month already has a brief: uploading replaces it.', up_need_file: 'Drop at least one slide image',
    up_bad_type: 'Only PNG, JPEG, WebP or GIF images', up_too_big: 'An image is larger than 5 MB', up_year: 'Year must be between 2000 and 2100',
    up_working: 'Reading {n} slide(s) with Claude… about a minute per slide', up_saving: 'Saving the images to GitHub…',
    up_pending: 'Saved to GitHub. The site reads the slides and rebuilds in a few minutes; refresh after that.', view_actions: 'View build progress',
    up_done: '{n} slides read for {month}', cancel: 'Cancel', submit: 'Read the slides', close: 'Close ✕', remove: 'Remove', up: 'Up', down: 'Down',
    // the weekly updates: a document per date, not slides
    date: 'Date', upload_file: 'Upload file', empty_file_title: 'No weekly update yet',
    empty_file_text: 'Upload the weekly update as a Word or PDF file: it is read into text, tables and figures.',
    file_title: 'Upload the weekly update', file_drop: 'Drop the file here or click to choose', file_types: '.docx or .pdf · one file · a date that already has one is replaced',
    file_date: 'Date of the update', file_need: 'Choose a .docx or .pdf file', file_bad: 'Only .docx or .pdf files', file_too_big: 'The file is larger than 40 MB',
    file_working: 'Reading the file…', file_done: 'Weekly update saved for {date}', file_replace: 'This date already has an update: uploading replaces it.',
    file_hint: 'One update per date; the file is kept with the entry.', open: 'Open', tables: 'tables', figures: 'figures',
    week: 'Week', week_n: 'Week {n}', all: 'All', no_match: 'No update in that week',
  },
  cn: {
    year: '年份', month: '月份', upload: '上传幻灯片', empty_title: '暂无简报',
    empty_text: '上传一组幻灯片截图：Claude 按顺序把每一页读成图表和表格。',
    load_error: '无法加载简报', slide: '第 {n} 页', warn_title: '请对照原图核对',
    extracted: '{date} 从上传的幻灯片读取', by_model: '由 {model}', manual: '人工录入',
    source: '查看原图', en_make: '生成英文标签', en_working: '正在生成英文标签…', en_done: '英文标签已生成',
    up_title: '上传幻灯片', up_brief: '简报标题（可选）', up_brief_ph: '默认使用第一页标题',
    up_drop: '拖入幻灯片截图或点击选择', up_types: 'PNG、JPEG 或 WebP · 可多张 · 按列表顺序读取',
    up_order: '阅读顺序', up_hint: '该月已有简报时，新上传会替换它。',
    up_replace: '该月已有简报：上传将替换它。', up_need_file: '至少拖入一张幻灯片图片',
    up_bad_type: '只支持 PNG、JPEG、WebP 或 GIF 图片', up_too_big: '有图片超过 5 MB', up_year: '年份须在 2000 到 2100 之间',
    up_working: '正在用 Claude 读取 {n} 页… 每页约一分钟', up_saving: '正在保存图片到 GitHub…',
    up_pending: '已保存到 GitHub。网站将在几分钟内读取幻灯片并重新构建，之后请刷新。', view_actions: '查看构建进度',
    up_done: '{month} 已读取 {n} 页', cancel: '取消', submit: '读取幻灯片', close: '关闭 ✕', remove: '移除', up: '上移', down: '下移',
    date: '日期', upload_file: '上传文件', empty_file_title: '暂无每周更新',
    empty_file_text: '上传每周更新的 Word 或 PDF 文件：系统将其读取为正文、表格和图表。',
    file_title: '上传每周更新', file_drop: '拖入文件或点击选择', file_types: '.docx 或 .pdf · 单个文件 · 同一日期已有更新时会被替换',
    file_date: '更新日期', file_need: '请选择 .docx 或 .pdf 文件', file_bad: '只支持 .docx 或 .pdf 文件', file_too_big: '文件超过 40 MB',
    file_working: '正在读取文件…', file_done: '{date} 的每周更新已保存', file_replace: '该日期已有更新：上传将替换它。',
    file_hint: '每个日期一份更新；文件与条目一起保存。', open: '打开', tables: '张表', figures: '张图',
    week: '周', week_n: '第 {n} 周', all: '全部', no_match: '该周没有更新',
  },
};

/* the two fixed topics (tags) of the view, in display order; each has its own months under
   data/macro/<topic>/ and its own upload */
const TOPICS = [
  {id: 'weekly', en: 'Weekly Updates', cn: '每周更新', kind: 'file'},  // a document per date
  {id: 'rates', en: 'Rate Hike Expectations', cn: '市场加息预期', kind: 'slides'},  // a deck per month
];
const DEFAULT_TOPIC = 'rates';
const FILE_EXT = {'.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.pdf': 'application/pdf'};
const WEEKLY_SECTOR = 'macro_weekly';  // the panel sector that holds the weekly updates
const MAX_FILE_BYTES = 40 * 1024 * 1024;
function topicById(id) { return TOPICS.find((x) => x.id === id) || null; }
function fileTopic() { const tp = topicById(state.topic); return !!(tp && tp.kind === 'file'); }
function keyLabel(key) { return /^\d{4}-\d{2}-\d{2}$/.test(key || '') ? dateLabel(key) : monthLabel(key); }
function dateLabel(d) { const [y, m, dd] = d.split('-').map(Number); return new Date(y, m - 1, dd).toLocaleDateString(locale(), {year: 'numeric', month: 'long', day: 'numeric'}); }
function topicLabel(tp) { const x = typeof tp === 'string' ? topicById(tp) : tp; return x ? (state.lang === 'cn' ? x.cn : x.en) : ''; }

const state = {lang: 'en', topic: DEFAULT_TOPIC, ym: null, index: null, indexTopic: null, doc: null, built: false, seq: 0, files: [], weeklyFile: null,
               yearFilter: '', monthFilter: '', weekFilter: ''};  // the weekly list's filters
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
function monthLabel(ym) { const [y, m] = ym.split('-').map(Number); return new Date(y, m - 1, 1).toLocaleDateString(locale(), {year: 'numeric', month: 'long'}); }
function monthName(m) { return new Date(2000, m - 1, 1).toLocaleDateString(locale(), {month: 'long'}); }
function toast(msg, link) {
  const n = $('toast'); if (!n) return;
  n.textContent = msg;
  if (link) { const a = h('a', null, ' ' + link.text); a.href = link.href; a.target = '_blank'; a.rel = 'noopener'; a.style.color = '#9FC4F0'; n.appendChild(a); }
  n.classList.add('show'); clearTimeout(n._tm); n._tm = setTimeout(() => n.classList.remove('show'), link ? 9000 : 2600);
}
/* English version: the brief carries "en": {original: English}; shown when the interface is English */
const CJK = /[㐀-䶿一-鿿]/;
function english() { return state.lang === 'en' ? ((state.doc && state.doc.en) || {}) : null; }
function L(text) { const en = english(); return (en && text && en[text]) || text; }
function lacksEnglish(doc) {
  if (!doc) return false;
  const en = doc.en || {};
  let missing = false;
  const look = (x) => { if (typeof x === 'string' && CJK.test(x) && !en[x]) missing = true; };
  look(doc.title);
  (doc.pages || []).forEach((p) => {
    look(p.title); look(p.subtitle);
    (p.blocks || []).forEach((b) => {
      look(b.title); look(b.text);
      (b.items || []).forEach(look); (b.notes || []).forEach(look); (b.categories || []).forEach(look); (b.columns || []).forEach(look);
      (b.series || []).forEach((sr) => look(sr.name));
      (b.bars || []).forEach((bar) => { look(bar.group); look(bar.label); look(bar.text); (bar.parts || []).forEach((pt) => look(pt.name)); });
      (b.rows || []).forEach((row) => row.forEach((c) => look(c.text)));
    });
  });
  return missing;
}
async function makeEnglish() {
  const ym = state.ym;
  toast(t('en_working'));
  try {
    const r = await fetch('/api/macro/' + state.topic + '/' + ym + '/translate', {method: 'POST'});
    let data = null; try { data = await r.json(); } catch (e) {}
    if (r.status === 401) { location.href = '/login.html?next=' + encodeURIComponent(location.hash); return; }
    if (!r.ok) throw new Error((data && data.error) || (r.status + ' ' + r.statusText));
    toast(t('en_done'));
    if (state.ym === ym) show(state.topic, ym);
  } catch (e) { toast(e.message || String(e)); }
}

/* ---------------------------------------------------------------- data */
async function getJson(path) {
  const r = await fetch(path, {cache: 'no-cache'});
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(r.status + ' ' + path);
  return r.json();
}
async function loadIndex(force) {
  if (state.index && state.indexTopic === state.topic && !force) return state.index;
  if (fileTopic()) {
    // the weekly updates are reports of the panel (sector "macro_weekly", one per date), shown
    // by the report reader; the list here comes from the panel's data layer
    const data = await window.DataLayer.load();
    const reps = (data.reports || []).filter((r) => r.sector === WEEKLY_SECTOR && r.date);
    reps.sort((a, b) => (b.date + (b.uploaded_at || '')).localeCompare(a.date + (a.uploaded_at || '')));
    state.weekly = reps;
    state.index = reps.map((r) => r.date);
  } else {
    const idx = await getJson('data/macro/' + state.topic + '/index.json');
    state.index = (idx && idx.months) || [];
  }
  state.indexTopic = state.topic;
  return state.index;
}
function weeklyByDate(date) { return (state.weekly || []).find((r) => r.date === date) || null; }
function months() { return (state.index || []).slice().sort(); }
function go(ym, topic) { location.hash = '#/macro/' + (topic || state.topic) + (ym ? '/' + ym : ''); }

/* ---------------------------------------------------------------- shell */
function build() {
  if (state.built) return;
  const card = $('macroCard');
  card.textContent = '';
  // the topic tags: fixed, one click switches the view to that topic's months
  const tags = h('nav', 'sub-tabs mk-tags'); tags.id = 'mkTags'; tags.setAttribute('aria-label', 'topics');
  TOPICS.forEach((tp) => {
    const b = h('button'); b.type = 'button'; b.dataset.topic = tp.id;
    b.addEventListener('click', () => { if (state.topic !== tp.id) go(null, tp.id); });
    tags.appendChild(b);
  });
  card.appendChild(tags);
  const bar = h('div', 'mk-bar');
  const left = h('div', 'mk-bar-title'); left.id = 'mkBarTitle';
  bar.appendChild(left);
  const ctl = h('div', 'mk-controls');
  const ly = h('label'); ly.appendChild(h('span')).id = 'mkYearLbl'; const ys = h('select'); ys.id = 'mkYear'; ly.appendChild(ys);
  const lm = h('label'); lm.appendChild(h('span')).id = 'mkMonthLbl'; const ms = h('select'); ms.id = 'mkMonth'; lm.appendChild(ms);
  const lw = h('label'); lw.id = 'mkWeekRow'; lw.appendChild(h('span')).id = 'mkWeekLbl'; const ws = h('select'); ws.id = 'mkWeek'; lw.appendChild(ws);
  const up = h('button', 'btn primary small'); up.type = 'button'; up.id = 'mkUpload';
  ctl.appendChild(ly); ctl.appendChild(lm); ctl.appendChild(lw); ctl.appendChild(up);
  ws.addEventListener('change', () => { state.weekFilter = ws.value; renderWeeklyList($('mkBody')); });
  bar.appendChild(ctl);
  card.appendChild(bar);
  const body = h('div', 'mk-body'); body.id = 'mkBody';
  card.appendChild(body);
  ys.addEventListener('change', () => {
    if (fileTopic()) { state.yearFilter = ys.value; state.monthFilter = ''; state.weekFilter = ''; paintShell(); renderWeeklyList($('mkBody')); return; }
    const inYear = months().filter((m) => m.startsWith(ys.value + '-')); go(inYear[inYear.length - 1] || null);
  });
  ms.addEventListener('change', () => {
    if (fileTopic()) { state.monthFilter = ms.value; state.weekFilter = ''; paintShell(); renderWeeklyList($('mkBody')); return; }
    go(ms.value);
  });
  up.addEventListener('click', () => openUpload());
  buildUploadDialog();
  state.built = true;
}
function paintShell() {
  Array.from($('mkTags').children).forEach((b) => { b.textContent = topicLabel(b.dataset.topic); b.className = b.dataset.topic === state.topic ? 'on' : ''; });
  $('mkYearLbl').textContent = t('year');
  $('mkMonthLbl').textContent = t('month');
  $('mkWeekLbl').textContent = t('week');
  $('mkWeekRow').hidden = !fileTopic();
  $('mkUpload').textContent = '⬆ ' + (fileTopic() ? t('upload_file') : t('upload'));
  const all = months();
  const years = Array.from(new Set(all.map((m) => m.slice(0, 4)))).sort().reverse();
  const ys = $('mkYear'), ms = $('mkMonth'), ws = $('mkWeek');
  ys.textContent = ''; ms.textContent = ''; ws.textContent = '';
  years.forEach((y) => { const o = h('option', null, y); o.value = y; ys.appendChild(o); });
  if (fileTopic()) {
    // the weekly updates: year, then month and week of the month to narrow the list ("All" keeps it whole)
    if (!years.includes(state.yearFilter)) state.yearFilter = years[0] || '';
    ys.value = state.yearFilter;
    const inYear = all.filter((d) => d.startsWith(state.yearFilter + '-'));
    const monthsIn = Array.from(new Set(inYear.map((d) => d.slice(0, 7)))).sort().reverse();
    const oAll = h('option', null, t('all')); oAll.value = ''; ms.appendChild(oAll);
    monthsIn.forEach((m) => { const o = h('option', null, monthName(Number(m.slice(5, 7)))); o.value = m; ms.appendChild(o); });
    if (!monthsIn.includes(state.monthFilter)) state.monthFilter = '';
    ms.value = state.monthFilter;
    const wAll = h('option', null, t('all')); wAll.value = ''; ws.appendChild(wAll);
    if (state.monthFilter) {
      const weeks = Array.from(new Set(inYear.filter((d) => d.startsWith(state.monthFilter)).map(weekOfMonth))).sort((a, b) => b - a);
      weeks.forEach((w) => { const o = h('option', null, t('week_n', {n: w})); o.value = String(w); ws.appendChild(o); });
      if (!weeks.map(String).includes(state.weekFilter)) state.weekFilter = '';
    } else state.weekFilter = '';
    ws.value = state.weekFilter;
    ys.disabled = years.length === 0; ms.disabled = inYear.length === 0; ws.disabled = !state.monthFilter;
    paintUploadDialog();
    return;
  }
  const year = state.ym ? state.ym.slice(0, 4) : years[0];
  if (year) ys.value = year;
  all.filter((m) => m.startsWith(year + '-')).forEach((m) => { const o = h('option', null, monthName(Number(m.slice(5)))); o.value = m; ms.appendChild(o); });
  if (state.ym) ms.value = state.ym;
  ys.disabled = years.length === 0; ms.disabled = all.length === 0;
  paintUploadDialog();
}

/* ---------------------------------------------------------------- render */
async function show(topic, ym) {
  const seq = ++state.seq;
  build();
  // an address from before the topics (#/macro/2026-10) means the rates topic
  if (topic && /^\d{4}-\d{2}$/.test(topic)) { ym = topic; topic = DEFAULT_TOPIC; }
  state.topic = topicById(topic) ? topic : DEFAULT_TOPIC;
  const body = $('mkBody');
  body.classList.add('is-loading');
  try { await loadIndex(false); } catch (e) { state.index = []; state.indexTopic = state.topic; }
  if (seq !== state.seq) return;
  const all = months();
  if (fileTopic()) {
    // the weekly updates: a list of the dated reports, each opening in the report reader
    state.ym = all[all.length - 1] || null;
    const want = '#/macro/' + state.topic;
    if (location.hash !== want && location.hash.indexOf('#/macro') === 0) history.replaceState(null, '', want);
    paintShell();
    state.doc = null; $('mkBarTitle').textContent = '';
    body.classList.remove('is-loading');
    if (!state.ym) { renderEmpty(body); return; }
    // like a sector of the research panel: the tag opens the latest update in the reader at once
    // (its month / week pickers move between the updates); the list stays for an empty topic only
    const latest = state.weekly[0];
    if (latest) { location.replace('#/r/' + latest.id); return; }
    renderWeeklyList(body);
    return;
  }
  state.ym = all.includes(ym) ? ym : (all[all.length - 1] || null);
  const want = '#/macro/' + state.topic + (state.ym ? '/' + state.ym : '');
  if (location.hash !== want && location.hash.indexOf('#/macro') === 0) history.replaceState(null, '', want);
  paintShell();
  if (!state.ym) { state.doc = null; $('mkBarTitle').textContent = ''; body.classList.remove('is-loading'); renderEmpty(body); return; }
  let doc = null, err = null;
  try { doc = await getJson('data/macro/' + state.topic + '/' + state.ym + '.json'); } catch (e) { err = e; }
  if (seq !== state.seq) return;
  body.classList.remove('is-loading');
  state.doc = doc;
  if (!doc) { renderEmpty(body, err ? (t('load_error') + ': ' + err.message) : t('load_error')); return; }
  renderDoc(body, doc);
}
/* the weekly updates, latest first; each row opens the report reader (contents on the left, the
   index of tables and figures on the right) */
function weekOfMonth(date) { return Math.ceil(Number(date.slice(8, 10)) / 7); }  // days 1-7 are week 1
function renderWeeklyList(body) {
  body.textContent = '';
  const list = h('div', 'mk-weekly');
  const shown = (state.weekly || []).filter((r) => (!state.yearFilter || r.date.startsWith(state.yearFilter + '-'))
    && (!state.monthFilter || r.date.startsWith(state.monthFilter)) && (!state.weekFilter || String(weekOfMonth(r.date)) === state.weekFilter));
  if (!shown.length) { body.appendChild(h('div', 'mk-empty', t('no_match'))); return; }
  shown.forEach((r) => {
    const row = h('a', 'mk-week'); row.href = '#/r/' + r.id;
    row.appendChild(h('span', 'mk-week-date', dateLabel(r.date)));
    const main = h('span', 'mk-week-main');
    main.appendChild(h('b', null, r.title || r.source_name || r.date));
    const bits = [];
    if (r.stats && r.stats.tables) bits.push(r.stats.tables + ' ' + t('tables'));
    if (r.stats && r.stats.images) bits.push(r.stats.images + ' ' + t('figures'));
    if (r.source_name) bits.push(r.source_name);
    main.appendChild(h('span', 'mk-week-sub', bits.join(' · ')));
    row.appendChild(main);
    row.appendChild(h('span', 'mk-week-open', t('open') + ' ›'));
    list.appendChild(row);
  });
  body.appendChild(list);
}
function renderEmpty(body, message) {
  body.textContent = '';
  const box = h('div', 'mk-empty');
  box.appendChild(h('b', null, message || t(fileTopic() ? 'empty_file_title' : 'empty_title')));
  if (!message) box.appendChild(document.createTextNode(t(fileTopic() ? 'empty_file_text' : 'empty_text')));
  box.appendChild(document.createElement('br'));
  const b = h('button', 'btn primary', '⬆ ' + (fileTopic() ? t('upload_file') : t('upload'))); b.type = 'button';
  b.addEventListener('click', () => openUpload());
  box.appendChild(b);
  body.appendChild(box);
}
function renderDoc(body, doc) {
  body.textContent = '';
  $('mkBarTitle').textContent = L(doc.title) || '';
  const head = h('div', 'mk-head');
  head.appendChild(h('h2', null, L(doc.title) || monthLabel(state.ym)));
  head.appendChild(h('span', 'mk-period', monthLabel(state.ym)));
  body.appendChild(head);
  if ((doc.warnings || []).length) {
    const w = h('div', 'mk-warn');
    w.appendChild(h('b', null, t('warn_title')));
    const ul = h('ul'); doc.warnings.forEach((x) => ul.appendChild(h('li', null, x)));
    w.appendChild(ul); body.appendChild(w);
  }
  // the slide index: one link per slide, like a deck's contents
  if ((doc.pages || []).length > 1) {
    const nav = h('nav', 'mk-toc');
    doc.pages.forEach((p) => {
      const a = h('a', null, (p.n) + '. ' + (L(p.title) || t('slide', {n: p.n})));
      a.href = '#mk-slide-' + p.n;
      a.addEventListener('click', (ev) => { ev.preventDefault(); const n = $('mk-slide-' + p.n); if (n) n.scrollIntoView({block: 'start', behavior: 'smooth'}); });
      nav.appendChild(a);
    });
    body.appendChild(nav);
  }
  (doc.pages || []).forEach((p) => body.appendChild(renderPage(p)));
  const meta = h('div', 'mk-meta');
  let when = doc.extracted_at || '';
  try { when = new Date(doc.extracted_at).toLocaleDateString(locale(), {year: 'numeric', month: 'short', day: 'numeric'}); } catch (e) {}
  const model = doc.model === 'manual transcription' ? t('manual') : t('by_model', {model: doc.model || ''});
  meta.appendChild(h('span', null, t('extracted', {date: when}) + ' · ' + model));
  if (state.lang === 'en' && lacksEnglish(doc) && !(window.DataLayer && window.DataLayer.mode === 'static')) {
    const enLink = h('a', null, t('en_make')); enLink.href = '#'; enLink.setAttribute('role', 'button');
    enLink.addEventListener('click', (ev) => { ev.preventDefault(); makeEnglish(); });
    meta.appendChild(enLink);
  }
  body.appendChild(meta);
}
function renderPage(p) {
  const sec = h('section', 'mk-slide'); sec.id = 'mk-slide-' + p.n;
  const head = h('header');
  head.appendChild(h('span', 'mk-no', String(p.n)));
  head.appendChild(h('h3', null, L(p.title) || t('slide', {n: p.n})));
  if (p.source_image) {
    const a = h('a', 'mk-src', t('source')); a.target = '_blank'; a.rel = 'noopener';
    a.href = 'data/macro/' + state.topic + '/' + state.ym + '/' + encodeURIComponent(p.source_image);
    a.addEventListener('click', (ev) => {
      if (!window.AIDLightbox || ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.button !== 0) return;
      ev.preventDefault(); window.AIDLightbox.open(a.href, (L(p.title) || '') + ' · ' + monthLabel(state.ym));
    });
    head.appendChild(a);
  }
  sec.appendChild(head);
  if (p.subtitle) sec.appendChild(h('p', 'mk-sub', L(p.subtitle)));
  const grid = h('div', 'mk-blocks');
  (p.blocks || []).forEach((b) => { const el = renderBlock(b); if (el) grid.appendChild(el); });
  sec.appendChild(grid);
  return sec;
}
function renderBlock(b) {
  if (b.type === 'chart') return b.kind === 'hbar' ? renderHBars(b) : renderXYChart(b);
  if (b.type === 'table') return renderTable(b);
  if (b.type === 'bullets') {
    const box = h('div', 'mk-block mk-bullets');
    if (b.title) box.appendChild(h('h4', null, L(b.title)));
    const ul = h('ul'); b.items.forEach((x) => ul.appendChild(h('li', null, L(x)))); box.appendChild(ul);
    return box;
  }
  if (b.type === 'callout') { const box = h('div', 'mk-block mk-callout wide'); if (b.title) box.appendChild(h('h4', null, L(b.title))); box.appendChild(h('p', null, L(b.text))); return box; }
  if (b.type === 'text') { const box = h('div', 'mk-block mk-text wide'); if (b.title) box.appendChild(h('h4', null, L(b.title))); box.appendChild(h('p', null, L(b.text))); return box; }
  if (b.type === 'footnotes') { const box = h('div', 'mk-block mk-foot wide'); b.items.forEach((x) => box.appendChild(h('p', null, L(x)))); return box; }
  return null;
}
function blockHead(box, b) {
  if (b.title) { const hd = h('div', 'mk-bhead'); hd.appendChild(h('h4', null, L(b.title))); box.appendChild(hd); }
}
function notes(box, list) {
  if (!(list || []).length) return;
  const n = h('div', 'mk-notes'); list.forEach((x) => n.appendChild(h('span', null, L(x)))); box.appendChild(n);
}

/* ---------------------------------------------------------------- charts */
function fmtTick(v, unit) {
  const digits = Math.abs(v) >= 100 ? 0 : (Math.abs(v) >= 10 ? 1 : 2);
  return v.toLocaleString('en-US', {maximumFractionDigits: digits}) + (unit === '%' ? '%' : '');
}
/* line or vertical bars over categories, drawn as a responsive SVG */
function renderXYChart(b) {
  const box = h('div', 'mk-block mk-chart');
  blockHead(box, b);
  const cats = b.categories || [], series = b.series || [];
  const vals = [];
  series.forEach((sr) => sr.points.forEach((pt) => { if (pt.value !== null && pt.value !== undefined) vals.push(pt.value); }));
  if (!vals.length) return box;
  const W = 640, H = 320, PL = 56, PR = series.length > 1 && b.kind === 'line' ? 84 : 24, PT = 26, PB = 42;
  let lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
  if (b.kind === 'bar') lo = Math.min(0, lo);
  const span = (hi - lo) || Math.abs(hi) || 1;
  lo -= span * (b.kind === 'bar' && lo === 0 ? 0 : 0.18); hi += span * 0.18;
  const step = niceStep((hi - lo) / 4);
  lo = Math.floor(lo / step) * step; hi = Math.ceil(hi / step) * step;
  const sx = (i) => PL + (cats.length === 1 ? (W - PL - PR) / 2 : (W - PL - PR) * i / (cats.length - 1));
  const sy = (v) => PT + (H - PT - PB) * (1 - (v - lo) / (hi - lo));
  const svg = s('svg', {viewBox: '0 0 ' + W + ' ' + H, class: 'mk-svg', role: 'img'});
  for (let v = lo; v <= hi + 1e-9; v += step) {
    svg.appendChild(s('line', {x1: PL, x2: W - PR, y1: sy(v), y2: sy(v), class: 'grid'}));
    svg.appendChild(s('text', {x: PL - 8, y: sy(v) + 4, 'text-anchor': 'end', class: 'tick'}, fmtTick(v, b.unit)));
  }
  if (b.kind === 'bar') {
    const slot = (W - PL - PR) / Math.max(1, cats.length), bw = Math.min(46, slot * 0.7 / Math.max(1, series.length));
    series.forEach((sr, si) => sr.points.forEach((pt, i) => {
      if (pt.value === null || pt.value === undefined) return;
      const x = PL + slot * i + slot / 2 - (series.length * bw) / 2 + si * bw;
      const y0 = sy(Math.max(0, lo)), y1 = sy(pt.value);
      svg.appendChild(s('rect', {x, y: Math.min(y0, y1), width: bw - 3, height: Math.max(1, Math.abs(y0 - y1)), fill: SERIES_COLORS[si % SERIES_COLORS.length], rx: 2}));
      svg.appendChild(s('text', {x: x + (bw - 3) / 2, y: Math.min(y0, y1) - 6, 'text-anchor': 'middle', class: 'val', fill: SERIES_COLORS[si % SERIES_COLORS.length]}, pt.text));
    }));
    cats.forEach((c, i) => svg.appendChild(s('text', {x: PL + slot * i + slot / 2, y: H - PB + 20, 'text-anchor': 'middle', class: 'cat'}, L(c))));
  } else {
    cats.forEach((c, i) => svg.appendChild(s('text', {x: sx(i), y: H - PB + 20, 'text-anchor': i === 0 ? 'start' : (i === cats.length - 1 ? 'end' : 'middle'), class: 'cat'}, L(c))));
    series.forEach((sr, si) => {
      const color = SERIES_COLORS[si % SERIES_COLORS.length], pts = [];
      sr.points.forEach((pt, i) => { if (pt.value !== null && pt.value !== undefined) pts.push([sx(i), sy(pt.value), pt, i]); });
      svg.appendChild(s('polyline', {points: pts.map((q) => q[0] + ',' + q[1]).join(' '), fill: 'none', stroke: color, 'stroke-width': si === 0 ? 3 : 2.2, 'stroke-linejoin': 'round'}));
      pts.forEach((q, k) => {
        svg.appendChild(s('circle', {cx: q[0], cy: q[1], r: 4.2, fill: color}));
        // the first series keeps its labels above the line, the others below, so they do not
        // collide; the first and last points' labels sit beside the point, clear of the axes
        const above = si === 0, first = k === 0 && pts.length > 1, last = k === pts.length - 1 && pts.length > 1;
        const anchor = first || last ? 'start' : 'middle', x = first || last ? q[0] + 9 : q[0];
        svg.appendChild(s('text', {x, y: above ? q[1] - 11 : q[1] + 20, 'text-anchor': anchor, class: 'val', fill: color, 'font-weight': si === 0 ? 700 : 500}, q[2].text + (last && series.length > 1 ? '  ' + L(sr.name) : '')));
      });
    });
  }
  box.appendChild(svg);
  if (series.length > 1) {
    const lg = h('div', 'mk-legend');
    series.forEach((sr, si) => { const sp = h('span'); const i = h('i'); i.style.background = SERIES_COLORS[si % SERIES_COLORS.length]; sp.appendChild(i); sp.appendChild(document.createTextNode(L(sr.name))); lg.appendChild(sp); });
    box.appendChild(lg);
  }
  notes(box, b.notes);
  return box;
}
function niceStep(raw) {
  const p = Math.pow(10, Math.floor(Math.log10(raw || 1)));
  const n = raw / p;
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * p;
}
/* horizontal bars, with optional group headings and a coloured part of each bar */
function renderHBars(b) {
  const box = h('div', 'mk-block mk-chart mk-hbars wide');
  blockHead(box, b);
  const bars = b.bars || [];
  const max = Math.max.apply(null, bars.map((x) => Math.abs(x.value)).concat([1]));
  const list = h('div', 'mk-hlist');
  let group = null;
  bars.forEach((bar) => {
    if (bar.group && bar.group !== group) { group = bar.group; list.appendChild(h('div', 'mk-hgroup', L(group))); }
    const row = h('div', 'mk-hrow');
    row.appendChild(h('span', 'mk-hlabel', L(bar.label)));
    const track = h('div', 'mk-htrack');
    const fill = h('div', 'mk-hfill'); fill.style.width = (100 * Math.abs(bar.value) / max) + '%';
    const part = (bar.parts || []).find((pt) => pt.share !== null && pt.share !== undefined);
    if (part) {
      const seg = h('span', 'mk-hpart'); seg.style.width = (100 * part.share) + '%'; seg.style.background = C_PART; seg.title = L(part.name) + (part.text ? ' ' + part.text : '');
      fill.appendChild(seg); fill.style.background = C_REST;
    } else fill.style.background = C_PART;
    track.appendChild(fill);
    track.appendChild(h('span', 'mk-hval', L(bar.text) || String(bar.value)));
    row.appendChild(track);
    list.appendChild(row);
  });
  box.appendChild(list);
  if ((b.notes || []).length) {
    const lg = h('div', 'mk-legend');
    b.notes.forEach((x, i) => { const sp = h('span'); const dot = h('i'); dot.style.background = i === 0 ? C_PART : C_REST; sp.appendChild(dot); sp.appendChild(document.createTextNode(L(x))); lg.appendChild(sp); });
    box.appendChild(lg);
  }
  return box;
}
function renderTable(b) {
  const box = h('div', 'mk-block mk-tablewrap wide');
  blockHead(box, b);
  const tb = h('table', 'mk-table');
  if ((b.columns || []).some((c) => c)) {
    const thead = h('thead'), tr = h('tr');
    b.columns.forEach((c) => tr.appendChild(h('th', null, L(c))));
    thead.appendChild(tr); tb.appendChild(thead);
  }
  const tbody = h('tbody');
  (b.rows || []).forEach((row) => {
    const tr = h('tr');
    row.forEach((c, i) => { const td = h(i === 0 ? 'th' : 'td', 'tone-' + (c.tone || 'none'), L(c.text)); if (i === 0) td.scope = 'row'; tr.appendChild(td); });
    tbody.appendChild(tr);
  });
  tb.appendChild(tbody);
  const wrap = h('div', 'mk-scroll'); wrap.appendChild(tb); box.appendChild(wrap);
  notes(box, b.notes);
  return box;
}

/* ---------------------------------------------------------------- upload dialog */
function buildUploadDialog() {
  const ov = h('div', 'overlay'); ov.id = 'mkOverlay'; ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-modal', 'true');
  const panel = h('div', 'ov-panel narrow');
  const head = h('div', 'ov-head'); head.appendChild(h('b')).id = 'mkUpTitle';
  const close = h('button'); close.type = 'button'; close.id = 'mkUpClose'; head.appendChild(close);
  panel.appendChild(head);
  const form = h('form', 'form'); form.id = 'mkForm';
  const drop = h('div', 'drop'); drop.id = 'mkDrop';
  const file = h('input'); file.type = 'file'; file.id = 'mkFile'; file.multiple = true; file.accept = 'image/png,image/jpeg,image/webp,image/gif';
  const dt = h('div', 'drop-txt'); dt.appendChild(h('b')).id = 'mkDropTxt'; dt.appendChild(h('span')).id = 'mkDropTypes';
  drop.appendChild(file); drop.appendChild(dt);
  form.appendChild(drop);
  const listLbl = h('span', 'lbl'); listLbl.id = 'mkOrderLbl'; form.appendChild(listLbl);
  const list = h('div', 'file-list mk-files'); list.id = 'mkFiles'; list.hidden = true; form.appendChild(list);
  const grid = h('div', 'grid2');
  const mk = (id, lblId, control, span) => { const l = h('label', span ? 'span2' : null); l.appendChild(h('span')).id = lblId; control.id = id; l.appendChild(control); grid.appendChild(l); return control; };
  const inTitle = mk('mkUpBrief', 'mkUpBriefLbl', h('input'), true); inTitle.type = 'text';
  const inYear = mk('mkUpYear', 'mkUpYearLbl', h('input')); inYear.type = 'number'; inYear.min = 2000; inYear.max = 2100; inYear.required = true;
  const selMonth = mk('mkUpMonth', 'mkUpMonthLbl', h('select'));
  form.appendChild(grid);
  form.appendChild(h('p', 'hint')).id = 'mkUpHint';
  const foot = h('div', 'form-foot');
  foot.appendChild(h('span', 'form-msg')).id = 'mkUpMsg';
  const cancel = h('button', 'btn ghost'); cancel.type = 'button'; cancel.id = 'mkUpCancel';
  const submit = h('button', 'btn primary'); submit.type = 'submit'; submit.id = 'mkUpSubmit';
  foot.appendChild(cancel); foot.appendChild(submit);
  form.appendChild(foot);
  panel.appendChild(form); ov.appendChild(panel);
  $('view-macro').appendChild(ov);

  file.addEventListener('change', () => { addFiles(file.files); file.value = ''; });
  ['dragenter', 'dragover'].forEach((e) => drop.addEventListener(e, (ev) => { ev.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach((e) => drop.addEventListener(e, () => drop.classList.remove('over')));
  drop.addEventListener('drop', (ev) => { ev.preventDefault(); addFiles(ev.dataTransfer.files); });
  document.addEventListener('paste', (ev) => {
    if (!ov.classList.contains('open')) return;
    const fs = Array.from((ev.clipboardData && ev.clipboardData.files) || []).filter((x) => MIME_EXT[x.type]);
    if (fs.length) { ev.preventDefault(); addFiles(fs); }
  });
  [inYear, selMonth].forEach((n) => n.addEventListener('change', paintReplaceHint));
  inYear.addEventListener('input', paintReplaceHint);
  close.addEventListener('click', closeUpload);
  cancel.addEventListener('click', closeUpload);
  ov.addEventListener('click', (ev) => { if (ev.target === ov) closeUpload(); });
  document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape' && ov.classList.contains('open')) closeUpload(); });
  form.addEventListener('submit', submitUpload);
}
/* the slides picked so far, in reading order; the list can be reordered and trimmed */
function addFiles(list) {
  Array.from(list || []).forEach((f) => { if (!state.files.some((x) => x.name === f.name && x.size === f.size)) state.files.push(f); });
  renderFiles();
}
function renderFiles() {
  const box = $('mkFiles'); box.textContent = '';
  box.hidden = !state.files.length; $('mkOrderLbl').hidden = !state.files.length;
  state.files.forEach((f, i) => {
    const row = h('label');
    row.appendChild(h('span', 'mk-fno', String(i + 1)));
    row.appendChild(h('span', 'mk-fname', f.name));
    row.appendChild(h('span', 'sz', Math.max(1, Math.round(f.size / 1024)) + ' KB'));
    const mkBtn = (txt, title, fn, disabled) => { const b = h('button', 'rm', txt); b.type = 'button'; b.title = title; b.disabled = !!disabled; b.addEventListener('click', fn); row.appendChild(b); };
    mkBtn('▲', t('up'), () => { state.files.splice(i - 1, 0, state.files.splice(i, 1)[0]); renderFiles(); }, i === 0);
    mkBtn('▼', t('down'), () => { state.files.splice(i + 1, 0, state.files.splice(i, 1)[0]); renderFiles(); }, i === state.files.length - 1);
    mkBtn('✕', t('remove'), () => { state.files.splice(i, 1); renderFiles(); });
    box.appendChild(row);
  });
}
function paintUploadDialog() {
  if (!$('mkOverlay')) return;
  $('mkUpTitle').textContent = t('up_title'); $('mkUpClose').textContent = t('close');
  $('mkDropTxt').textContent = t('up_drop'); $('mkDropTypes').textContent = t('up_types');
  $('mkOrderLbl').textContent = t('up_order');
  $('mkUpBriefLbl').textContent = t('up_brief'); $('mkUpBrief').placeholder = t('up_brief_ph');
  $('mkUpYearLbl').textContent = t('year'); $('mkUpMonthLbl').textContent = t('month');
  $('mkUpCancel').textContent = t('cancel'); $('mkUpSubmit').textContent = t('submit');
  const selMonth = $('mkUpMonth'), cur = selMonth.value;
  selMonth.textContent = '';
  for (let m = 1; m <= 12; m++) { const o = h('option', null, monthName(m)); o.value = String(m); selMonth.appendChild(o); }
  if (cur) selMonth.value = cur;
  renderFiles(); paintReplaceHint();
}
function uploadTarget() {
  const year = Number($('mkUpYear').value), month = Number($('mkUpMonth').value);
  return {year, month, ym: year + '-' + String(month).padStart(2, '0')};
}
function paintReplaceHint() {
  const hint = $('mkUpHint'); if (!hint) return;
  const exists = months().includes(uploadTarget().ym);
  hint.textContent = exists ? t('up_replace') : t('up_hint');
}
function setMsg(text, cls) { const m = $('mkUpMsg'); m.className = 'form-msg' + (cls ? ' ' + cls : ''); m.textContent = text || ''; }
function openUpload() {
  if (fileTopic()) { openFileUpload(); return; }
  const now = new Date();
  $('mkUpYear').value = now.getFullYear(); $('mkUpMonth').value = String(now.getMonth() + 1);
  $('mkUpBrief').value = ''; state.files = []; renderFiles(); setMsg('');
  $('mkUpSubmit').disabled = false;
  paintReplaceHint();
  $('mkOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeUpload() {
  $('mkOverlay').classList.remove('open');
  if (!document.querySelector('.overlay.open')) document.body.style.overflow = '';
}
async function submitUpload(ev) {
  ev.preventDefault();
  const files = state.files, tg = uploadTarget(), title = $('mkUpBrief').value.trim();
  if (!files.length) { setMsg(t('up_need_file'), 'err'); return; }
  if (files.some((f) => !MIME_EXT[f.type])) { setMsg(t('up_bad_type'), 'err'); return; }
  if (files.some((f) => f.size > MAX_BYTES)) { setMsg(t('up_too_big'), 'err'); return; }
  if (!(tg.year >= 2000 && tg.year <= 2100)) { setMsg(t('up_year'), 'err'); return; }
  const DL = window.DataLayer, btn = $('mkUpSubmit');
  btn.disabled = true;
  try {
    if (DL && DL.mode === 'static') {
      setMsg(t('up_saving'));
      for (let i = 0; i < files.length; i++) {
        const name = state.topic + '-' + tg.ym + '-' + String(i + 1).padStart(2, '0') + '.' + MIME_EXT[files[i].type];
        await DL.commitFile('macro/incoming/' + name, new Uint8Array(await files[i].arrayBuffer()), 'macro: upload ' + name);
      }
      await DL.commitFile('macro/incoming/' + state.topic + '-' + tg.ym + '.meta.json', new TextEncoder().encode(JSON.stringify({title}, null, 2) + '\n'), 'macro: upload ' + state.topic + ' ' + tg.ym);
      setMsg(t('up_pending'), 'ok');
      toast(t('up_pending'), DL.actionsUrl ? {text: t('view_actions'), href: DL.actionsUrl()} : null);
    } else {
      setMsg(t('up_working', {n: files.length}));
      const fd = new FormData();
      files.forEach((f) => fd.append('files', f, f.name));
      fd.append('year', String(tg.year)); fd.append('month', String(tg.month)); fd.append('title', title); fd.append('topic', state.topic);
      const r = await fetch('/api/macro/upload', {method: 'POST', body: fd});
      let data = null; try { data = await r.json(); } catch (e) {}
      if (r.status === 401) { location.href = '/login.html?next=' + encodeURIComponent(location.hash); return; }
      if (!r.ok) throw new Error((data && data.error) || (r.status + ' ' + r.statusText));
      await loadIndex(true);
      closeUpload();
      toast(t('up_done', {n: data.pages, month: monthLabel(tg.ym)}));
      if (location.hash === '#/macro/' + state.topic + '/' + tg.ym) show(state.topic, tg.ym); else go(tg.ym);
    }
  } catch (e) { setMsg(e.message || String(e), 'err'); }
  finally { btn.disabled = false; }
}

/* ---------------------------------------------------------------- the weekly update: one file per date */
function buildFileDialog() {
  const ov = h('div', 'overlay'); ov.id = 'mkFileOverlay'; ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-modal', 'true');
  const panel = h('div', 'ov-panel narrow');
  const head = h('div', 'ov-head'); head.appendChild(h('b')).id = 'mkFileTitle';
  const close = h('button'); close.type = 'button'; close.id = 'mkFileClose'; head.appendChild(close);
  panel.appendChild(head);
  const form = h('form', 'form'); form.id = 'mkFileForm';
  const drop = h('div', 'drop'); drop.id = 'mkFileDrop';
  const file = h('input'); file.type = 'file'; file.id = 'mkFileInput'; file.accept = '.docx,.pdf';
  const dt = h('div', 'drop-txt'); dt.appendChild(h('b')).id = 'mkFileDropTxt'; dt.appendChild(h('span')).id = 'mkFileTypes';
  drop.appendChild(file); drop.appendChild(dt);
  form.appendChild(drop);
  const chosen = h('div', 'file-list mk-files'); chosen.id = 'mkFileChosen'; chosen.hidden = true; form.appendChild(chosen);
  const grid = h('div', 'grid2');
  const mk = (id, lblId, control, span) => { const l = h('label', span ? 'span2' : null); l.appendChild(h('span')).id = lblId; control.id = id; l.appendChild(control); grid.appendChild(l); return control; };
  const inTitle = mk('mkFileBrief', 'mkFileBriefLbl', h('input'), true); inTitle.type = 'text';
  const inDate = mk('mkFileDate', 'mkFileDateLbl', h('input'), true); inDate.type = 'date'; inDate.required = true;
  form.appendChild(grid);
  form.appendChild(h('p', 'hint')).id = 'mkFileHint';
  const foot = h('div', 'form-foot');
  foot.appendChild(h('span', 'form-msg')).id = 'mkFileMsg';
  const cancel = h('button', 'btn ghost'); cancel.type = 'button'; cancel.id = 'mkFileCancel';
  const submit = h('button', 'btn primary'); submit.type = 'submit'; submit.id = 'mkFileSubmit';
  foot.appendChild(cancel); foot.appendChild(submit);
  form.appendChild(foot);
  panel.appendChild(form); ov.appendChild(panel);
  $('view-macro').appendChild(ov);
  file.addEventListener('change', () => { state.weeklyFile = file.files[0] || null; paintFileDialog(); });
  ['dragenter', 'dragover'].forEach((e) => drop.addEventListener(e, (ev) => { ev.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach((e) => drop.addEventListener(e, () => drop.classList.remove('over')));
  drop.addEventListener('drop', (ev) => { ev.preventDefault(); state.weeklyFile = (ev.dataTransfer.files && ev.dataTransfer.files[0]) || null; paintFileDialog(); });
  inDate.addEventListener('change', paintFileDialog);
  cancel.addEventListener('click', closeFileUpload); close.addEventListener('click', closeFileUpload);
  ov.addEventListener('click', (ev) => { if (ev.target === ov) closeFileUpload(); });
  form.addEventListener('submit', submitFileUpload);
}
function paintFileDialog() {
  if (!$('mkFileOverlay')) return;
  $('mkFileTitle').textContent = t('file_title'); $('mkFileClose').textContent = t('close');
  $('mkFileDropTxt').textContent = t('file_drop'); $('mkFileTypes').textContent = t('file_types');
  $('mkFileBriefLbl').textContent = t('up_brief'); $('mkFileBrief').placeholder = t('up_brief_ph');
  $('mkFileDateLbl').textContent = t('file_date');
  $('mkFileCancel').textContent = t('cancel'); $('mkFileSubmit').textContent = t('upload_file');
  const box = $('mkFileChosen'); box.textContent = '';
  const f = state.weeklyFile;
  box.hidden = !f;
  if (f) { const row = h('label'); row.appendChild(h('span', 'mk-fname', f.name)); row.appendChild(h('span', 'sz', Math.max(1, Math.round(f.size / 1024)) + ' KB')); box.appendChild(row); }
  const date = $('mkFileDate').value;
  $('mkFileHint').textContent = date && months().includes(date) ? t('file_replace') : t('file_hint');
}
function openFileUpload() {
  if (!$('mkFileOverlay')) buildFileDialog();
  const now = new Date();
  $('mkFileDate').value = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0') + '-' + String(now.getDate()).padStart(2, '0');
  $('mkFileBrief').value = ''; state.weeklyFile = null;
  const m = $('mkFileMsg'); m.className = 'form-msg'; m.textContent = '';
  $('mkFileSubmit').disabled = false;
  paintFileDialog();
  $('mkFileOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeFileUpload() {
  $('mkFileOverlay').classList.remove('open');
  if (!document.querySelector('.overlay.open')) document.body.style.overflow = '';
}
async function submitFileUpload(ev) {
  ev.preventDefault();
  const f = state.weeklyFile, date = $('mkFileDate').value, title = $('mkFileBrief').value.trim();
  const msg = (text, cls) => { const m = $('mkFileMsg'); m.className = 'form-msg' + (cls ? ' ' + cls : ''); m.textContent = text || ''; };
  if (!f) { msg(t('file_need'), 'err'); return; }
  const ext = '.' + (f.name.split('.').pop() || '').toLowerCase();
  if (!FILE_EXT[ext]) { msg(t('file_bad'), 'err'); return; }
  if (f.size > MAX_FILE_BYTES) { msg(t('file_too_big'), 'err'); return; }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) { msg(t('file_date'), 'err'); return; }
  const DL = window.DataLayer, btn = $('mkFileSubmit');
  btn.disabled = true;
  try {
    // the file becomes a report of the panel (sector "macro_weekly", dated), read with the
    // panel's parser; the static site commits it to panel/incoming and the build reads it
    msg(t(DL && DL.mode === 'static' ? 'up_saving' : 'file_working'));
    const [y, m] = date.split('-').map(Number);
    const res = await DL.upload({sector: WEEKLY_SECTOR, year: y, quarter: Math.floor((m - 1) / 3) + 1, nature: 'full', language: '', title, keywords: '', section: '', date}, f);
    if (res && res.pending) {
      msg(t('up_pending'), 'ok');
      toast(t('up_pending'), DL.actionsUrl ? {text: t('view_actions'), href: DL.actionsUrl()} : null);
      return;
    }
    await loadIndex(true);
    closeFileUpload();
    toast(t('file_done', {date: dateLabel(date)}));
    if (res && res.id) location.hash = '#/r/' + res.id; else show('weekly', null);
  } catch (e) {
    if (e && e.needLogin) { location.href = '/login.html?next=' + encodeURIComponent(location.hash); return; }
    msg(e.message || String(e), 'err');
  }
  finally { btn.disabled = false; }
}

/* ---------------------------------------------------------------- panel integration */
function toLang(lang) { return lang === 'cn' || lang === 'zh' ? 'cn' : 'en'; }
window.MacroMarket = {
  // the tab itself (#/macro, no topic) opens the default topic, so that the topic tags are always
  // reachable from a weekly update's reader page
  mount(lang, topic, ym) { state.lang = toLang(lang); return show(topic || DEFAULT_TOPIC, ym); },
  setLanguage(lang) {
    const next = toLang(lang);
    if (next === state.lang) return;
    state.lang = next;
    if (state.built && !$('view-macro').hidden) show(state.topic, state.ym);
  },
};
})();
