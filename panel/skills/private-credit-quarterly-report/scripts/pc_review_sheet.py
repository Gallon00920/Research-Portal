#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""门 1/2 · 核对清单 + 算术恒等式（Private Credit 季报版）

    python3 pc_review_sheet.py            → 写 out/REVIEW_<RQ>.md
    python3 pc_review_sheet.py --strict   → 恒等式不过就 exit 1

恒等式是不占用户时间的那部分自查：加总关系、口径关系、样本数、分位数域。
用户要逐行看的是「本季新增的数」那张清单。
"""
import io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SER = os.path.join(HERE, 'series.json')
MAN = os.path.join(HERE, 'exhibit_manifest.json')
OUT = os.path.join(HERE, 'out')

D = json.load(io.open(SER, encoding='utf-8'))
M = json.load(io.open(MAN, encoding='utf-8'))
EX = D['exhibits']
META = D['meta']
RQ = META.get('rq') or 'UNKNOWN'

checks = []          # (ok:True/False/None, 名称, 明细)
TOL = 0.15


def fmt(x):
    return f'{x:,.4g}' if isinstance(x, (int, float)) else str(x)


def eq(name, got, want, tol=TOL):
    if got is None or want is None:
        checks.append((None, name, '缺值，跳过')); return
    checks.append((abs(got - want) <= tol, name, f'{fmt(got)} vs {fmt(want)}'))


def need(name, cond, detail):
    checks.append((bool(cond), name, detail))


# ══════════ A0 · 印在 Note 上的公式必须真的成立 ══════════
# ⛔ Alex 2026-08-26 要求把 E5 的 non-refi 算法写进 Note。公式一上纸，
#    读者按柱子加总就该算得出那条线 —— 这条恒等式就是替读者先算一遍。
_dl = (EX.get('mkt_dl_origination') or {})
_st, _rl = _dl.get('stacks') or {}, _dl.get('rhs_line') or {}
if _st.get('Refi') and _st.get('Non-refi') and _rl.get('vals'):
    _R, _N, _V = _st['Refi'], _st['Non-refi'], _rl['vals']
    _worst, _at = 0.0, None
    for _i in range(len(_R)):
        _lo = max(0, _i - 2)
        _r, _n = sum(_R[_lo:_i + 1]), sum(_N[_lo:_i + 1])
        if not (_r + _n) or _V[_i] is None:
            continue
        _d = abs(100.0 * _n / (_r + _n) - _V[_i])
        if _d > _worst:
            _worst, _at = _d, (_dl.get('periods') or [])[_i] if _dl.get('periods') else _i
    need('E5 右轴 = 三月合计之比（Note 上印的公式）',
         _worst <= 0.06,
         f'最大偏差 {_worst:.2f}pp（{_at}）—— ⛔ 公式印在 Note 上了，'
         f'读者按柱子加总要能算出这条线；对不上就是两者之一错了')

# ══════════ A · 三个基准日必须都填，且 fund 不得晚于 market ══════════
ao = META.get('as_of', {})
mk, fd, cp = ao.get('market', {}), ao.get('fund', {}), ao.get('competitor', {})
need('基准日 · 市场层已声明', mk.get('quarter'), str(mk.get('quarter')))
need('基准日 · 基金层已声明', fd.get('quarter'), str(fd.get('quarter')))
need('基准日 · 竞品层导出日已声明', cp.get('export_date'), str(cp.get('export_date')))


def qkey(q):
    m = re.match(r'(\d)Q(\d\d)', str(q) or '') or re.match(r'(?:20)?(\d\d)Q(\d)', str(q) or '')
    if not m:
        return None
    a, b = m.groups()
    return (int(b), int(a)) if len(a) == 1 else (int(a), int(b))


if mk.get('quarter') and fd.get('quarter'):
    a, b = qkey(mk['quarter']), qkey(fd['quarter'])
    if a and b:
        need('基准日 · 基金层不晚于市场层（基金报告本来就滞后）', b <= a,
             f"市场 {mk['quarter']} / 基金 {fd['quarter']}"
             + ('' if b <= a else ' —— 基金比市场还新，八成填错了'))
    if a and b and b < a:
        checks.append((None, '基准日错位提醒',
                       f"市场 {mk['quarter']} vs 基金 {fd['quarter']} —— "
                       f'第 8 节开头必须显式声明这个滞后，否则读者会误读'))

# ══════════ B · 占比类必须加总到 100% ══════════
for sl, e in EX.items():
    if e.get('_shape') != 'shares':
        continue
    vals = e.get('vals') or []
    if not vals:
        checks.append((None, f'{sl} 占比加总', '无数据，跳过')); continue
    if isinstance(vals[0], (list, tuple)):          # 多面板
        for i, panel in enumerate(vals):
            eq(f'{sl} 面板{i+1} 占比加总 = 100%', sum(panel), 100.0)
    else:
        tol = e.get('_sum_tolerance')
        if tol:
            ok = abs(sum(vals) - 100.0) <= tol['max_abs']
            checks.append((ok, f'{sl} 占比加总 = 100%（容差 ±{tol["max_abs"]}）',
                           f'{sum(vals):g} vs 100 —— {tol["reason"]}'))
        else:
            eq(f'{sl} 占比加总 = 100%', sum(vals), 100.0)

# ══════════ C · 堆叠图：分项之和 = 总计（若给了总计） ══════════
for sl, e in EX.items():
    if e.get('_shape') != 'series_stacked':
        continue
    st = e.get('stacks') or {}
    tot = st.get('total') or st.get('Total')
    if not st or not tot:
        continue
    parts = [v for k, v in st.items() if k.lower() != 'total']
    if not parts or not all(len(p) == len(tot) for p in parts):
        checks.append((None, f'{sl} 堆叠分项 = 总计', '长度不齐，跳过')); continue
    bad = [i for i in range(len(tot))
           if abs(sum(p[i] for p in parts) - tot[i]) > max(0.5, abs(tot[i]) * 0.005)]
    need(f'{sl} 每期分项之和 = 总计', not bad,
         '全部吻合' if not bad else f'第 {bad} 期对不上')

# ══════════ C2 · 分组 100% 堆叠：每根柱子加总 = 100 ══════════
for sl, e in EX.items():
    if e.get('_shape') != 'groups_stacked':
        continue
    st = e.get('stacks') or {}
    ng = len(e.get('groups') or []) * len(e.get('periods') or [])
    parts = list(st.values())
    if not parts or not ng or any(len(p) != ng for p in parts):
        checks.append((None, f'{sl} 分组堆叠长度', f'分项长度与 groups×periods={ng} 不齐，跳过')); continue
    bad = [i for i in range(ng) if abs(sum(p[i] for p in parts) - 100) > 0.5]
    need(f'{sl} 每根柱子加总 = 100%', not bad,
         f'{ng} 根柱子全部吻合' if not bad else f'第 {bad} 根对不上')

# ══════════ D · Competitor：分位数域、cohort 样本数、IQR ══════════
sc = EX.get('ca_scorecard', {})
rows = sc.get('rows') or []
pcts = [r.get('percentile') for r in rows if isinstance(r, dict) and r.get('percentile') is not None]
if pcts:
    def num(p):
        m = re.search(r'\d+', str(p)); return int(m.group()) if m else None
    vv = [num(p) for p in pcts]
    need('分位数都落在 0–100', all(v is not None and 0 <= v <= 100 for v in vv),
         f'{len(vv)} 个：{vv[:8]}')
else:
    checks.append((None, '分位数域', 'ca_scorecard 无 rows，跳过'))

coh = META.get('cohorts') or EX.get('ca_scorecard', {}).get('cohorts') or {}
if coh:
    for v, c in coh.items():
        ns = [c.get(k) for k in ('n_irr', 'n_tvpi', 'n_dpi') if c.get(k) is not None]
        if ns:
            need(f'cohort {v} 样本数 ≥ 5（否则分位数没意义）', min(ns) >= 5,
                 f'n = {ns}' + ('' if min(ns) >= 5 else ' —— 样本太小，必须在 Note 里写明'))
        if c.get('iqr_irr_pp') is not None:
            need(f'cohort {v} IQR 非负', c['iqr_irr_pp'] >= 0, f"{c['iqr_irr_pp']}pp")
else:
    checks.append((None, 'cohort 统计', '账本里没有 cohorts，跳过'))

uc = META.get('screen', {}).get('universe_fund_count')
need('PitchBook 筛选样本数已记录', uc, f'{uc} 只' if uc else '缺 —— 分位数无法复核')

cs = META.get('comparator_set') or {}
need('点名对标组已记录（改了必须在正文声明）',
     cs.get('upper_mm') or cs.get('core_mm'),
     f"upper {len(cs.get('upper_mm') or [])} 家 / core {len(cs.get('core_mm') or [])} 家")

# ══════════ E · percentile_history 只追加，不许改历史 ══════════
for sl in ('ca_traj_irr_pct', 'ca_traj_tvpi_pct'):
    h = (EX.get(sl) or {}).get('history') or {}
    if not h:
        checks.append((None, f'{sl} 轨迹历史', '空，基线季正常')); continue
    gaps = (EX.get(sl) or {}).get('history_gaps') or {}
    for fund, pts in h.items():
        qs = [p.get('quarter') for p in pts]
        if not qs:
            # 空历史有两种：真的漏了，或者这只基金本季确实没有可核来源。
            # 后者必须在 history_gaps 里写明原因，才不算失败。
            why = gaps.get(fund)
            checks.append((None if why else False, f'{sl}/{fund} 轨迹历史为空',
                           f'已声明缺口：{why}' if why
                           else '空且未声明原因 —— 要么补数，要么在 history_gaps 里写清为什么没有'))
            continue
        need(f'{sl}/{fund} 期次不重复且含本季', len(qs) == len(set(qs)) and RQ in qs,
             f'{len(qs)} 期：{qs[-3:]}')

# ══════════ F · 来源可追溯：src 必须有文件名，且不许写死 slide 号 ══════════
_noslide = re.compile(r'\bslide\s*\d+', re.I)
_hasfile = re.compile(r'\.(pdf|xlsx|xlsm|csv|docx)\b', re.I)
bad_src, slide_src, empty_src = [], [], []
for sl, e in EX.items():
    src = (e.get('src') or '').strip()
    if not src:
        empty_src.append(sl); continue
    if not _hasfile.search(src):
        bad_src.append(sl)
    if _noslide.search(src) and 'title' not in src.lower() and '标题' not in src:
        slide_src.append(sl)
need('每个 exhibit 的 src 都非空', not empty_src,
     '齐备' if not empty_src else f'{len(empty_src)} 个空：{empty_src[:6]}')
need('src 都含文件名（可复核）', not bad_src,
     '齐备' if not bad_src else f'{len(bad_src)} 个没有文件名：{bad_src[:6]}')
need('src 没有只靠 slide 号定位的（下季一定挪）', not slide_src,
     '齐备' if not slide_src else f'{len(slide_src)} 个写死了 slide 号：{slide_src[:6]}'
     ' —— 要改成按 slide 标题定位，页码只做辅助')

# ══════════ G · 上一版报告绝不能当数据源 ══════════
_BANNED = re.compile(r'_v\d|Junson_Private_Credit_Report|上一版报告|上季报告|previous issue', re.I)
leak = []
for sl, e in EX.items():
    for fld in ('src', 'note', 'source_line'):
        m = _BANNED.search(e.get(fld) or '')
        if m:
            leak.append(f'{sl}.{fld}（命中 "{m.group()}"）')
need('没有拿上一版报告当数据源', not leak,
     '干净' if not leak else f'{leak} —— 上一版只能对答案，不能当来源。'
     '若只是想说明「本季没用它」，把这段话搬到 _gap_note / _method 之类的字段，别放在 src/note 里')

# ══════════ 渲染 ══════════
os.makedirs(OUT, exist_ok=True)
bad = [c for c in checks if c[0] is False]
skip = [c for c in checks if c[0] is None]
mk_ = {True: '✓', False: '✗', None: '?'}

lines = [f'# 核对清单 · {RQ}', '',
         f"数据基准：市场 **{mk.get('quarter')}** ｜ 基金 **{fd.get('quarter')}** ｜ "
         f"竞品导出日 **{cp.get('export_date')}**", '',
         '## 算术恒等式自查', '']
lines += [f'{mk_[ok]} {nm} —— {det}' for ok, nm, det in checks] or ['（无可用恒等式）']
lines += ['', f'**通过 {len(checks)-len(bad)-len(skip)}　不通过 {len(bad)}　跳过 {len(skip)}**', '']

# 动态题注：单独列出来让人确认
dyn = [e for e in M['exhibits'] if e.get('caption_dynamic')]
lines += ['## 带数据主张的题注（这些每季必须按新数据重写，逐条确认）', '',
          '| # | slug | 题注里的主张 | 本季题注 |', '|---|---|---|---|']
import importlib.util as _il
_sp = _il.spec_from_file_location('exh', os.path.join(HERE, 'exhibits.py'))
_ex = _il.module_from_spec(_sp); _sp.loader.exec_module(_ex)
_E = _ex.load()
for e in dyn:
    n = _E.n(e['slug'])
    cur = (EX.get(e['slug']) or {}).get('caption_rendered') or '（未填）'
    lines.append(f"| {n} | `{e['slug']}` | {e['caption_claim']} | {cur} |")
lines += ['']

# 本季新增的数
lines += ['## 本季新增的数（逐行核）', '',
          '| # | exhibit | 项 | 期 | 值 | 出处 |', '|---|---|---|---|---|---|']
nrow = 0
covered = []
for e in M['exhibits']:
    sl = e['slug']; ent = EX.get(sl)
    if not ent:
        continue
    src = (ent.get('src') or '')[:70]
    n = _E.n(sl)
    before = nrow
    sh = ent.get('_shape')
    if sh in ('rows_qoq', 'rows_flat'):
        for r in ent.get('rows') or []:
            if isinstance(r, (list, tuple)):
                # 矩阵型表格（第一格是行名，后面是各列的值），例如 Ex 8 风险收益表
                if not r:
                    continue
                lines.append(f'| {n} | {sl} | {r[0]} | {RQ} | '
                             f'**{" / ".join(str(x) for x in r[1:])}** | {src} |'); nrow += 1
                continue
            if not isinstance(r, dict):
                continue
            lbl = r.get('label') or r.get('metric') or r.get('name') or '?'
            cur = r.get('cq', r.get('cur', r.get('value', '—')))
            pq_ = r.get('pq', r.get('prev', '—'))
            lines.append(f'| {n} | {sl} | {lbl} | {RQ} | {pq_} → **{cur}** | {src} |'); nrow += 1
    elif sh == 'shares':
        for lb, v in zip(ent.get('labels') or [], ent.get('vals') or []):
            lines.append(f'| {n} | {sl} | {lb} | {RQ} | **{v}%** | {src} |'); nrow += 1
    elif sh in ('series_stacked', 'series_lines'):
        ps = ent.get('periods') or []
        gs = ent.get('stacks') or ent.get('lines') or {}
        for k, v in gs.items():
            if isinstance(v, list) and ps and len(v) == len(ps):
                lines.append(f'| {n} | {sl} | {k} | {ps[-1]} | **{v[-1]}** | {src} |'); nrow += 1
    elif sh == 'groups_stacked':
        gs = ent.get('groups') or []; ps = ent.get('periods') or []
        for k, v in (ent.get('stacks') or {}).items():
            for gi, g in enumerate(gs):
                for pi, pp in enumerate(ps):
                    j = gi * len(ps) + pi
                    if j < len(v):
                        lines.append(f'| {n} | {sl} | {g} · {k} | {pp} | **{v[j]}** | {src} |'); nrow += 1
    elif sh == 'groups_bars':
        for k, v in (ent.get('series') or {}).items():
            for g, vv in zip(ent.get('groups') or [], v):
                lines.append(f'| {n} | {sl} | {g} | {k} | '
                             f'**{"未披露" if vv is None else vv}** | {src} |'); nrow += 1
    elif sh == 'series_grouped':
        ps = ent.get('periods') or []
        for k, v in (ent.get('stacks') or {}).items():
            if ps and len(v) == len(ps):
                lines.append(f'| {n} | {sl} | {k} | {ps[-1]} | **{v[-1]}** | {src} |'); nrow += 1
    elif sh == 'bars_grouped_categorical':
        for k, v in (ent.get('series') or {}).items():
            for lb, vv in zip(ent.get('labels') or [], v):
                lines.append(f'| {n} | {sl} | {lb} | {k} | **{vv}** | {src} |'); nrow += 1
    elif sh == 'bars_categorical':
        for lb, v in zip(ent.get('labels') or [], ent.get('vals') or []):
            lines.append(f'| {n} | {sl} | {lb} | {RQ} | **{v}** | {src} |'); nrow += 1
    elif sh == 'pct_history':
        gaps = ent.get('history_gaps') or {}
        for fund, pts in (ent.get('history') or {}).items():
            if not pts:
                lines.append(f'| {n} | {sl} | {fund} | {RQ} | **无点** | '
                             f'{(gaps.get(fund) or "未声明原因")[:60]} |'); nrow += 1
                continue
            for pt in pts:
                lines.append(f"| {n} | {sl} | {fund} · 分位 | {pt.get('quarter')} | "
                             f"**{pt.get('percentile')}**（n={pt.get('n')}） | {src} |"); nrow += 1
    elif sh == 'bars_categorical_dual':
        for k, v in (ent.get('series') or {}).items():
            for lb, vv in zip(ent.get('labels') or [], v):
                lines.append(f'| {n} | {sl} | {k} | {lb} | **{vv}** | {src} |'); nrow += 1
    elif sh == 'median_iqr_by_vintage':
        for lb, med, p25, p75, nn in zip(ent.get('labels') or [], ent.get('median') or [],
                                         ent.get('p25') or [], ent.get('p75') or [],
                                         ent.get('n') or []):
            lines.append(f'| {n} | {sl} | {ent.get("metric_label", "")} | {lb} | '
                         f'中位 **{med}**（P25 {p25} / P75 {p75}, n={nn}） | {src} |'); nrow += 1
    elif sh == 'scatter_bubble':
        for pt in (ent.get('points') or []):
            lines.append(f"| {n} | {sl} | {pt.get('manager')} | {RQ} | "
                         f"均四分位 **{pt.get('avg_quartile')}** / 中位 IRR "
                         f"**{pt.get('median_irr')}**（n={pt.get('n_ranked')}） | {src} |"); nrow += 1
    elif sh == 'band_positioning':
        for it in ent.get('items') or []:
            lines.append(f'| {n} | {sl} | {it} | {RQ} | — | {src} |'); nrow += 1
    if nrow == before:
        covered.append(sl)

lines += ['', '## 覆盖检查', '',
          f'**{len(M["exhibits"])-len(covered)}/{len(M["exhibits"])} 个 exhibit 出了行，共 {nrow} 行数据**']
if covered:
    lines += ['', '**⛔ 以下 exhibit 一行都没出现在清单上 —— 要么本季没抽数，要么结构不认识，'
              '两种都必须在签收前解决：**', ''] + [f'- `{s}`' for s in covered]
lines += ['']

p = os.path.join(OUT, f'REVIEW_{RQ}.md')
io.open(p, 'w', encoding='utf-8').write('\n'.join(lines))
print(f'[written] {p}　恒等式 {len(checks)-len(bad)}/{len(checks)} 通过，'
      f'新增数 {nrow} 行，覆盖 {len(M["exhibits"])-len(covered)}/{len(M["exhibits"])}')
if bad:
    print('\n恒等式不通过：')
    for _, nm, det in bad:
        print(f'  ✗ {nm} —— {det}')
if '--strict' in sys.argv and bad:
    sys.exit(1)
