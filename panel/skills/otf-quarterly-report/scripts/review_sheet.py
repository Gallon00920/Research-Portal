#!/usr/bin/env python3
"""门 1/2 的核对清单 + 算术恒等式自查。

  python3 review_sheet.py            → out/REVIEW_<CQ>.md
  python3 review_sheet.py --strict   → 恒等式不过就 exit 1

清单一行一个本季新增的数：指标 / 上季 / 本季 / QoQ / 出处。用户逐行校对。
恒等式是不占用户时间的那部分自查：加总关系、口径关系、单调关系。
"""
import json, sys, os, re

SER = 'series.json'
D = json.load(open(SER, encoding='utf-8'))
CQ, PQ = D['meta']['cq'], D['meta']['pq']
CH = D['charts']
TOL = 0.15          # 占比类加总容差（四舍五入累积）


def series_of(k):
    c = CH.get(k, {})
    return c.get('series', {}), c


def val(k, s, p):
    ser, _ = series_of(k)
    n = ser.get(s, {}).get(p)
    if isinstance(n, dict):
        return n.get('v')
    return n


def fmt(x):
    return '—' if x is None else (f'{x:g}' if isinstance(x, (int, float)) else str(x))


# ── 恒等式 ────────────────────────────────────────────────────────
checks = []


def eq(name, got, want, tol=TOL):
    ok = got is not None and want is not None and abs(got - want) <= tol
    checks.append((ok, name, f'{fmt(got)} vs {fmt(want)}'))
    return ok


def ge(name, a, b):
    ok = a is not None and b is not None and a >= b - 1e-9
    checks.append((ok, name, f'{fmt(a)} ≥ {fmt(b)}'))
    return ok


def approx_sum(name, parts, want, tol=TOL):
    if any(p is None for p in parts):
        checks.append((False, name, '有分项缺失'))
        return False
    return eq(name, round(sum(parts), 4), want, tol)


# T1 资产类别八档 / memo 关系
tb = CH.get('tbl01_capital_structure')
if tb:
    def r(lbl, col):
        for row in tb['rows']:
            if row['label'] == lbl:
                return float(str(row[col]).rstrip('%'))
        return None
    for col, per in (('pq', PQ), ('cq', CQ)):
        d = r('Memo: total debt investments', col)
        e = r('Memo: total equity & joint ventures', col)
        approx_sum(f'T1 {per} debt + equity = 100%', [d, e], 100.0)
        s = r('Memo: senior secured debt', col)
        approx_sum(f'T1 {per} senior secured = 一留 + 二留',
                   [r('First-lien senior secured debt', col),
                    r('Second-lien senior secured debt', col)], s)

# 图 1 行业占比加总（前 10 + Other）
# 只认已知结构，认不出就明确跳过 —— 绝不把 dict 里所有数字盲加，
# 那会把 n_industries 这类计数当占比加进去，得出一个看着很像的错数。
_p1 = CH.get('fig01_industry_pie', {})
for _key, _per in (('pq', PQ), ('cq', CQ)):
    _d = _p1.get(_key)
    _parts = None
    if isinstance(_d, dict) and isinstance(_d.get('vals'), list):
        _parts = [x for x in _d['vals'] if isinstance(x, (int, float))]
        if isinstance(_d.get('other'), (int, float)):
            _parts = _parts + [_d['other']]
        else:
            _parts = None
    elif _p1.get('series'):
        _parts = [val('fig01_industry_pie', s, _per) for s in _p1['series']]
        if any(not isinstance(x, (int, float)) for x in _parts):
            _parts = None
    if _parts:
        approx_sum(f'图 1 {_per} 行业占比加总（前 10 + Other）= 100%', _parts, 100.0, 0.6)
    else:
        checks.append((None, f'图 1 {_per} 行业占比加总', '结构不认识，跳过 —— 请人工核'))

# 图 7 评级四档加总
rt, _ = series_of('fig07_risk_rating')
if rt:
    for per in list(next(iter(rt.values())).keys()):
        parts = [val('fig07_risk_rating', s, per) for s in rt]
        if all(p is not None for p in parts):
            approx_sum(f'图 7 {per} 评级加总 = 100%', parts, 100.0, 0.35)

# 图 6 非应计：成本口径 ≥ 公允值口径
for per in (PQ, CQ):
    a = val('fig06_nonaccrual', 'OTF_COST', per)
    b = val('fig06_nonaccrual', 'OTF_FV', per)
    if a is not None and b is not None:
        ge(f'图 6 {per} 非应计 成本 ≥ 公允值', a, b)

# 图 4 覆盖率 = NII ÷ 总分红
n4, _ = series_of('fig04_nii_coverage')
if n4:
    for per in (PQ, CQ):
        nii = val('fig04_nii_coverage', 'GAAP_NII_PS', per)
        base = val('fig04_nii_coverage', 'BASE_DIV_PS', per)
        spec = val('fig04_nii_coverage', 'SPECIAL_DIV_PS', per) or 0
        cov = val('fig04_nii_coverage', 'COVERAGE_PCT', per)
        if None not in (nii, base, cov) and (base + spec):
            eq(f'图 4 {per} 覆盖率 = NII ÷ 总分红', cov, round(nii / (base + spec) * 100, 1), 1.0)

# ── 核对清单 ──────────────────────────────────────────────────────
lines = [f'# 核对清单 · {CQ}', '',
         f'上季 = {PQ}　本季 = {CQ}　股价截止 = {D["meta"].get("as_of","—")}', '',
         '逐行核对本季那一列。出处一栏能指到文件就够，页码是回执不是路标。', '']

# ── prices.csv 基准日完整性 ────────────────────────────────────────
# 归一化基准日缺任何一个 ticker 的收盘价，图 8/9 的基点和 T8 的跌幅就全错。
# 实测踩过：OTF 缺 2025-06-12，跌幅算成 −28.4% 而真值是 −30.8%，差 2.4pp。
_BASE = '2025-06-12'
try:
    import csv as _csv
    with open('prices.csv', encoding='utf-8') as _f:
        _rows = list(_csv.DictReader(_f))
    _tk = [c for c in (_rows[0].keys() if _rows else []) if c.endswith('_close_usd')]
    _base_row = next((r for r in _rows if r.get('date') == _BASE), None)
    if _base_row is None:
        checks.append((False, f'prices.csv 基准日 {_BASE}', '这一行根本不存在'))
    else:
        _miss = [c.replace('_close_usd', '') for c in _tk
                 if not str(_base_row.get(c, '')).strip()]
        checks.append((not _miss, f'prices.csv 基准日 {_BASE} 各 ticker 收盘价齐备',
                       '齐备' if not _miss else f'缺 {", ".join(_miss)} —— 图 8/9 基点与 T8 跌幅会错'))
    _gaps = {c.replace('_close_usd', ''): sum(1 for r in _rows if not str(r.get(c, '')).strip())
             for c in _tk}
    _bad_gaps = {k2: v for k2, v in _gaps.items() if v > 5}
    if _bad_gaps:
        checks.append((False, 'prices.csv 空值过多',
                       '; '.join(f'{k2} 缺 {v} 天' for k2, v in _bad_gaps.items())))
except FileNotFoundError:
    checks.append((None, 'prices.csv', '文件不存在，跳过 —— 图 8/9 与 T8 无法出'))

# ── T3 软件分层：占比加总 + 混合 AI 敞口 ──────────────────────────
_t3 = CH.get('tbl03_software_layer')
if isinstance(_t3, dict) and isinstance(_t3.get('layers'), list):
    _ls = [l for l in _t3['layers'] if isinstance(l, dict) and l.get('pct') is not None]
    if _t3.get('_VOID'):
        checks.append((False, 'T3 软件分层占比作废，尚未重算',
                       str(_t3['_VOID'])[:110]))
    elif not _ls:
        checks.append((False, 'T3 软件分层占比全空',
                       'layers 里没有一个 pct —— 必须按本季 10-Q Schedule of Investments '
                       '逐家公允值自算，不许留空也不许取草稿 xlsx'))
    if _ls and not _t3.get('_VOID'):
        eq('T3 各层敞口占比加总 = 100%', sum(l['pct'] for l in _ls), 100.0, tol=0.15)
        if _t3.get('portfolio_fv_total') and all(l.get('fv') is not None for l in _ls):
            eq('T3 各层公允值合计 = 组合公允值（漏判公司会露出来）',
               sum(l['fv'] for l in _ls), _t3['portfolio_fv_total'],
               tol=max(1.0, _t3['portfolio_fv_total'] * 0.005))
        else:
            checks.append((None, 'T3 各层公允值合计',
                           '缺 fv / portfolio_fv_total，跳过 —— 占比改成自算后要逐层记公允值'))
        if _t3.get('n_companies') and all(l.get('n') is not None for l in _ls):
            eq('T3 参与计算的公司数 = 10-Q 披露的组合公司数',
               sum(l['n'] for l in _ls), _t3['n_companies'], tol=0)
        else:
            checks.append((None, 'T3 公司数', '缺 n / n_companies，跳过 —— 无法确认没漏公司'))
        _bl = sum(l['pct'] * l.get('impact_weight', 0) for l in _ls) / 100 * 100
        if _t3.get('blended_ai_impact') is not None:
            eq('T3 混合 AI 敞口 = Σ 占比 × 权重',
               _t3['blended_ai_impact'], _bl, tol=0.06)
else:
    checks.append((None, 'T3 软件分层', '结构不认识或缺失，跳过 —— 请人工核'))

lines += ['## 算术恒等式自查', '']
bad = [c for c in checks if c[0] is False]
skip = [c for c in checks if c[0] is None]
_m = {True: '✓', False: '✗', None: '?'}
lines += [f'{_m[ok]} {nm} —— {det}' for ok, nm, det in checks] or ['（无可用恒等式）']
lines += ['', f'**通过 {len(checks)-len(bad)-len(skip)}　不通过 {len(bad)}　跳过 {len(skip)}**'
          + ('' if not bad else '　**有不通过项，先修数再交付**')
          + ('' if not skip else '　**跳过项必须人工核**'), '']

# 本季新增点的期标签：主体各图用 Q<n>'<yy>，BDC 竞品图用 <n>Q<yy>（§2.2 两套写法），
# 行业图跟源研报的最新期（比 OTF filings 晚一季）。逐图取「序列最后一期」才不会漏。
def _cq_alt(cq):
    import re as _r
    m = _r.match(r"Q(\d)'(\d\d)$", cq)
    return f'{m.group(1)}Q{m.group(2)}' if m else None

lines += ['## 本季新增的数', '', '| 图/表 | 系列 | 期 | 上季 | 本季 | QoQ | 出处 |',
          '|---|---|---|---|---|---|---|']
# 覆盖检查：记录每个条目出了几行。一行没出 = 结构不认识或本季没抽数，
# 必须点名 —— 静默跳过正是让 30 行竞品数从没被人看过的那个 bug。
_n0, _rows_by_key = len(lines), {}
for k, c in CH.items():
    if not isinstance(c, dict):
        continue
    _mark = len(lines)
    # 任何 tbl* 条目只要有 rows 就上清单 —— 不能只认 T1，
    # 否则 T4/T5/T6 这类新加的表会静默缺席，用户签收时根本没见过。
    # T3 是快照表（没有 pq/cq 两列），单独出行 —— 否则会被记成"意外空缺"
    if k == 'tbl03_software_layer' and isinstance(c.get('layers'), list):
        for l in c['layers']:
            if not isinstance(l, dict):
                continue
            _reps = ', '.join(l.get('reps', []) or [])
            _fv = l.get('fv'); _n = l.get('n')
            _det = f'权重 {l.get("impact_weight","—")}'
            if _fv is not None: _det += f'　公允值 ${_fv:,.1f}mm'
            if _n is not None:  _det += f'　{_n} 家'
            if _reps: _det += f'　代表持仓 {_reps}'
            lines.append(f'| {k} | {l.get("layer","?")} | {CQ} | — | '
                         f'**{l.get("pct","—")}%** | {_det} | '
                         f'{(l.get("src") or c.get("src",""))[:60]} |')
        if c.get('blended_ai_impact') is not None:
            lines.append(f'| {k} | Blended AI-impact score | {CQ} | — | '
                         f'**{c["blended_ai_impact"]}%** | Σ 占比 × 权重 | '
                         f'{c.get("src","")[:60]} |')
        _rows_by_key[k] = len(lines) - _mark
        continue

    if k.startswith('tbl') and isinstance(c.get('rows'), list):
        for row in c['rows']:
            if not isinstance(row, dict):
                continue
            lbl = row.get('label') or row.get('name') or row.get('metric') or '?'
            pq_v = row.get('pq', row.get('prev', '—'))
            cq_v = row.get('cq', row.get('cur', '—'))
            qoq_v = row.get('qoq', row.get('chg', '—'))
            src_v = row.get('src') or c.get('src', '')
            lines.append(f'| {k} | {lbl} | {CQ} | {pq_v} | **{cq_v}** | {qoq_v} | {src_v[:60]} |')
        _rows_by_key[k] = len(lines) - _mark
        continue

    # 无时间序列结构的图也要逐个数上清单，否则用户签收时根本没见过它们
    if k == 'fig03_nav_bridge':
        for it in c.get('items', []):
            lines.append(f'| {k} | {it["label"]} | {CQ} | — | **{it["v"]}** | — | '
                         f'{(it.get("src") or c.get("src",""))[:60]} |')
        if c.get('omitted'):
            lines.append(f'| {k} | omitted item | {CQ} | — | **0.00** | — | {c["omitted"][:60]} |')
        _rows_by_key[k] = len(lines) - _mark
        continue
    if k == 'fig20_nonaccrual_sector':
        per = c.get('sector_period', '')
        for s in c.get('sectors', []):
            d3, cv = s.get('avg3y'), s.get('cq')
            dlt = f'{cv - d3:+.2f}' if isinstance(cv, (int, float)) and isinstance(d3, (int, float)) else '—'
            lines.append(f'| {k} | {s["name"]} | {per} | {d3} (3Y avg) | **{cv}** | {dlt} | '
                         f'{c.get("src","")[:60]} |')
        lines.append(f'| {k} | sharpest-rise claim | {per} | — | '
                     f'**{", ".join(c.get("sharpest_rise", []))}** | — | 标题判断句，按升幅排序 |')
        _rows_by_key[k] = len(lines) - _mark
        continue
    if k == 'fig01_industry_pie':
        names = c.get('labels_short') or c.get('labels_full') or []
        pq_d, cq_d = c.get('pq', {}), c.get('cq', {})
        for i, v in enumerate(cq_d.get('vals', [])):
            nm = names[i] if i < len(names) else f'#{i+1}'
            pv = pq_d.get('vals', [None] * 99)[i]
            dlt = f'{v - pv:+.2f}' if isinstance(pv, (int, float)) else '—'
            lines.append(f'| {k} | {nm} | {CQ} | {pv} | **{v}** | {dlt} | {cq_d.get("src","")[:60]} |')
        lines.append(f'| {k} | Other | {CQ} | {pq_d.get("other")} | **{cq_d.get("other")}** | '
                     f'— | {cq_d.get("n_other")} of {cq_d.get("n_industries")} industries |')
        _rows_by_key[k] = len(lines) - _mark
        continue

    ser = c.get('series', {})
    for s, pts in ser.items():
        keys = list(pts.keys())
        if not keys:
            continue
        # CQ 的两种写法都认；都没有就退回该序列自己的最后一期（行业图比 filings 晚一季）
        alt = _cq_alt(CQ)
        cur_key = CQ if CQ in pts else (alt if alt and alt in pts else keys[-1])
        cur = pts[cur_key]
        cv = cur.get('v') if isinstance(cur, dict) else cur
        i = keys.index(cur_key)
        prev = keys[i - 1] if i > 0 else None
        pv = (pts[prev].get('v') if isinstance(pts[prev], dict) else pts[prev]) if prev else None
        qoq = f'{cv - pv:+.2f}' if isinstance(cv, (int, float)) and isinstance(pv, (int, float)) else '—'
        src = (cur.get('src') if isinstance(cur, dict) else '') or c.get('src', '')
        lines.append(f'| {k} | {s} | {cur_key} | {fmt(pv)} | **{fmt(cv)}** | {qoq} | {src[:60]} |')
    _rows_by_key[k] = len(lines) - _mark

# ── 覆盖检查 ──────────────────────────────────────────────────────
_empty = [k for k, n in _rows_by_key.items() if n == 0]
_NOT_ROWWISE = {'fig08_price_software', 'fig09_price_bdc', 'fig21_software_stack'}
_unexpected = [k for k in _empty if k not in _NOT_ROWWISE]
_ndata = sum(_rows_by_key.values())
lines += ['', '## 覆盖检查', '',
          f'账本 {len(_rows_by_key)} 个条目，出了 {len(_rows_by_key)-len(_empty)} 个，'
          f'共 {_ndata} 行数据。']
lines += ['', '图 8 / 图 9 的数在 `prices.csv`，看走势图与 T8 跌幅表；图 21 是分层文字，看图与 4.3 正文。'
          '这三张不进逐行清单。']
if _unexpected:
    lines += ['', '**⛔ 以下条目一行都没出现在清单上 —— 要么结构不认识，要么本季没抽数，'
              '签收前必须查清：**', ''] + [f'- `{k}`' for k in _unexpected]
lines += ['']

os.makedirs('out', exist_ok=True)
p = f'out/REVIEW_{CQ.replace(chr(39),"")}.md'
open(p, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print(f'[coverage] {len(_rows_by_key)-len(_empty)}/{len(_rows_by_key)} 个条目出了行，共 {_ndata} 行数据'
      + (f'　!! 意外空缺：{", ".join(_unexpected)}' if _unexpected else ''))
print(f'[written] {p}　恒等式 {len(checks)-len(bad)}/{len(checks)} 通过，新增数 '
      f'{sum(1 for l in lines if l.startswith("| ") and "**" in l)} 行')
for _, nm, det in skip:
    print('  ? 跳过（需人工核）：', nm, '——', det)
if bad:
    print('恒等式不通过：')
    for _, nm, det in bad:
        print('  ✗', nm, '——', det)
    if '--strict' in sys.argv:
        sys.exit(1)
