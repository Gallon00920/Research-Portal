# -*- coding: utf-8 -*-
"""表头体检：§8 那几张表的列名写死，逐张核对字面量。

⛔ Alex 2026-08-25：「Exhibit 36 和 37 和 38 的表格的左侧和顶部的表头也必须是一样的
   （跟同事的报告）」「E41 和 E42 也是要跟同事的报告里的表格的表头一样」
   以及 Fund snapshot 两张表的行/列固定。

季度标签用 <pq> / <cq> 占位，从各 exhibit 自己的 periods 读；其余一个字都不许变。
用法：python3 pc_hdrcheck.py [--strict]
"""
import io, json, sys
sys.path.insert(0, '.')
import pcpaths as P

D = json.load(io.open(P.ledger_path(), encoding='utf-8'))
E = D['exhibits']

# slug -> 表头模板（<pq>/<cq> 会用该 exhibit 的 periods 替换）
HDR = {
 # E16：七列固定，只有倒数二/三列是季度（Alex 2026-08-25）
 'cf_provider_compare_table': ['Provider', 'Sample / scope', 'Definition / methodology',
                               '<pq>', '<cq>', 'Trend', 'Cohort'],
 'fund_pag_comp_qoq':   ['By portfolio type', '<pq>', '<cq>', 'QoQ Δ',
                         'By currency', '<pq>', '<cq>', 'QoQ Δ'],
 'fund_pag_kpi_qoq':    ['Metric', '<cq>', '<pq>'],
 'fund_pag_top10':      ['Investment', 'Date', 'Portfolio type', 'CCY', 'Spread',
                         'Amount ($m)', 'Total value ($m)', 'UW IRR', 'Expected IRR'],
 'fund_gug_comp_qoq':   ['GICS sub-industry (top)', '<pq>*', '<cq>', 'QoQ Δ*',
                         'Sponsored (% of NAV)', '<pq>', '<cq>', 'QoQ Δ'],
 'fund_gug_closed_deals': ['Deal', 'Structure', 'Pricing', 'Net leverage', 'LTV',
                           'Differentiator'],
 'fund_hsbc_comp_qoq':  ['Sector', '<pq>', '<cq>', 'QoQ Δ',
                         'Sector', '<pq>', '<cq>', 'QoQ Δ'],
 'fund_hsbc_portfolio': ['Project', 'Sector', 'Country', 'Margin', 'Committed (€m)',
                         'Drawn (€m)', 'Maturity', 'Est. ROIC', 'Watchlist'],
 # E47：第三列是基准季标签，跟着 meta.rq 走 —— 用 <rq> 占位
 'ca_scorecard':        ['Fund / basis', 'Metric', '<rq>', 'QoQ Δ', 'Cohort median',
                         'Cohort Δ', 'Percentile', 'Pct Δ', 'Read'],
 'ca_named_comparators': ['Fund', 'Vintage', 'Size ($m)', 'Net IRR', 'TVPI', 'DPI',
                          'Called %', 'Dry powder %', 'PB quartile'],
}
# ⛔ Fund snapshot 表 A 的行名**三只基金各一套**（Alex 2026-08-26 纠正过：
#    「Guggenheim … 的 Fund snapshot 的左边的表格的最左侧一列还是不对，你对照一下同事的，
#     然后固定。以及 HSBC RCF … 也是」）。原来这里写死了一套六行给三只共用，所以
#    GUG（五行）和 HSBC（六行但内容不同）纸上印的是 PAG 那套 —— 全绿而全错。
#    现在一律读各自的 row_labels_fixed.expected；缺这个字段直接 ✗。
SNAP_B_HDR = ['Metric', '<pq>', '<cq>', 'QoQ Δ']
FUNDS = ['fund_pag', 'fund_gug', 'fund_hsbc']

bad, ok = [], 0


def resolve(tpl, ent):
    per = ent.get('periods') or []
    # 有的表存了三期（例 E37 的 3Q25/4Q25/1Q26）—— 一律取**最后两期**当上季/本季
    pq = per[-2] if len(per) >= 2 else '<pq?>'
    cq = per[-1] if len(per) >= 1 else '<cq?>'
    return [c.replace('<pq>', str(pq)).replace('<cq>', str(cq)).replace('<rq>', P.rq())
            for c in tpl]


print(f'\n=== 表头体检 · {P.rq()} ===')
for slug, tpl in HDR.items():
    ent = E.get(slug)
    if not ent:
        bad.append(f'{slug}: 账本里没有这个 exhibit'); continue
    # 有 header_template 的（例 E47 的 <rq>）以模板为真值，header 只是本季快照
    if ent.get('header_template'):
        tpl = ent['header_template']
    want = resolve(tpl, ent)
    got = ent.get('header')
    if got is None:
        bad.append(f'{slug}: 账本里没有 `header` 字段 —— 表头必须落在账本上，'
                   f'不许只写在 build_doc 的调用里。应为：{want}')
    elif list(got) != want:
        bad.append(f'{slug}: 表头对不上\n          账本 {list(got)}\n          应为 {want}')
    else:
        ok += 1

# Fund snapshot 两张表
for f in FUNDS:
    a, b = E.get(f + '_snapshot'), E.get(f + '_snapshot_qoq')
    if not a or not b:
        bad.append(f'{f}: 缺 Fund snapshot 的两张表（{f}_snapshot / {f}_snapshot_qoq）—— '
                   f'三只基金结构必须一致（report-spec §8）')
        continue
    # ⛔ 表 A **不许有表头行** —— 同事那版就是纯 label|value（Alex 2026-08-26 纠正过：
    #    「是两个分开的的横向排放的表，表头和最左侧边的栏必须一样」）。
    if a.get('header'):
        bad.append(f'{f}_snapshot 不该有 header —— Fund snapshot 左表没有表头行，'
                   f'现在写着 {a["header"]}；表头只有右表（表B）有')
    if not a.get('_no_header'):
        bad.append(f'{f}_snapshot 缺 `_no_header: true` —— 用来标明这张表不画表头行')
    for _t, _e in (('A', a), ('B', b)):
        _cw = _e.get('col_widths_cm') or {}
        if not _cw.get('widths') or not _cw.get('fixed'):
            bad.append(f'{f}_snapshot 表{_t} 缺冻结列宽（col_widths_cm.widths + fixed=true）'
                       f'—— 两张表要并排且同宽，宽度不能交给 autofit')
    _awant = ((a.get('row_labels_fixed') or {}).get('expected')) or []
    if not _awant:
        bad.append(f'{f}_snapshot 缺 row_labels_fixed.expected —— 表A 的行名必须逐字冻结在'
                   f'账本里，⛔ 三只基金各一套，不许共用')
    elif [r.get('label') for r in a.get('rows', [])] != _awant:
        bad.append(f'{f}_snapshot: 表A 行标对不上冻结清单，应为 {_awant}，'
                   f'实为 {[r.get("label") for r in a.get("rows", [])]}')
    elif list(b.get('header') or []) != resolve(SNAP_B_HDR, b):
        bad.append(f'{f}_snapshot_qoq: 表头应为 {resolve(SNAP_B_HDR, b)}')
    else:
        ok += 2
    # ⛔ 表B 的最左列（KPI 行名与行数）逐字锁成同事那版，各基金各一套 ——
    #    Alex 2026-08-26：「snapshot 的右边的 metrics 为什么 PAG BRS Fund III 的少了 NAV？
    #    这也能错吗？HSBC RCF Partnership Fund 的 metrics 少了 Credit facility outstanding」
    _bl = ((b.get('row_labels_fixed') or {}).get('expected')) or []
    if not _bl:
        bad.append(f'{f}_snapshot_qoq 缺 row_labels_fixed.expected —— '
                   f'表B 的 KPI 行名必须逐字冻结在账本里')
    else:
        _got = [r.get('label') for r in (b.get('rows') or [])]
        if _got != _bl:
            _lack = [x for x in _bl if x not in _got]
            _extra = [x for x in _got if x not in _bl]
            bad.append(f'{f}_snapshot_qoq 表B 行对不上冻结清单（结构性：KPI 名是固定词汇表）'
                       + (f'；少了 {_lack}' if _lack else '')
                       + (f'；多了 {_extra}' if _extra else '')
                       + ('；顺序不对' if not _lack and not _extra else ''))
        else:
            ok += 1
        # ⛔ 三格都要有内容，但允许是 n/d / n/a —— 源报告本季少披露一个指标是常态
        #    （Alex 2026-08-26：「某个数下个季度没提供…QoQ Chg 那就是 n/a」）。
        #    真正不许的是「空着」和「n/d 却还算出了一个 Δ」。
        for r in (b.get('rows') or []):
            for _k2 in ('pq', 'cq', 'delta'):
                if not str(r.get(_k2) or '').strip():
                    bad.append(f'{f}_snapshot_qoq 的 {r.get("label")!r} 缺 {_k2} —— '
                               f'没披露就写 n/d，别留空')
            _cq, _pq, _dl = (str(r.get('cq')).strip(), str(r.get('pq')).strip(),
                             str(r.get('delta')).strip())
            if 'n/d' in (_cq, _pq) and _dl not in ('n/a', 'new'):
                bad.append(f'{f}_snapshot_qoq 的 {r.get("label")!r}：有一头是 n/d，'
                           f'Δ 却是 {_dl!r} —— ⛔ 缺一头做不出差，应为 n/a'
                           f'（上季缺、本季有则写 new）')
            if _cq == 'n/d' and _pq not in ('', 'n/d') and _cq == _pq:
                bad.append(f'{f}_snapshot_qoq 的 {r.get("label")!r}：本季看着是沿用了上季值')
    for k in ('quarter_activity', 'manager_commentary'):
        if not (a.get(k) or b.get(k)):
            bad.append(f'{f}: 缺固定 bullet `{k}:` —— 没内容也要写 none this quarter')

# E45 的 QoQ：本季有净增/净减就必须带项目名（Alex 2026-08-25）
_hq = E.get('fund_hsbc_comp_qoq') or {}
import re as _re
for r in _hq.get('rows', []):
    dl = str(r.get('delta', ''))
    if dl in ('–', '—', '-', ''):
        continue
    if not _re.search(r'\(', dl):
        bad.append(f"fund_hsbc_comp_qoq 行「{r.get('label')}」的 QoQ 是 {dl!r}，"
                   f"但没写是哪个项目 —— ⛔ 有净增/净减就要写成 `+1 (项目名)`")
    else:
        ok += 1

# E47：history 里有上季记录，三个 Δ 列就不许还是 n/a
_sc = E.get('ca_scorecard') or {}
_h = _sc.get('history') or {}
_qs = sorted(q for q in _h if len(q) == 6 and q[:4].isdigit())
if len(_qs) >= 2:
    _prev = _qs[-2]
    for r in _sc.get('rows', []):
        if str(r.get('qoq', '')).startswith('baseline') or r.get('qoq') == 'n/a':
            if f"{r['fund']} — {r['metric']}" in (_h.get(_prev) or {}):
                bad.append(f"ca_scorecard 行「{r['fund']} — {r['metric']}」的 QoQ 还是 "
                           f"{r.get('qoq')!r}，但 history[{_prev}] 里有这一条 —— "
                           f"⛔ 有上季记录就必须做差，不许留 n/a")
    ok += 1
else:
    print(f'  E47 history：只有 {_qs} —— 首季，三个 Δ 列写 n/a 是对的；'
          f'本季 {len(_h.get(_qs[-1], {})) if _qs else 0} 行已入账本，下季可做差')

# E48：两行灰底分组标题必须在，名字固定
_ncmp = E.get('ca_named_comparators') or {}
_tl = _ncmp.get('tier_labels') or {}
_want_tiers = ['Core-to-upper MM', 'Low-to-core MM']
_have = [v for v in _tl.values() if v]
if _have != _want_tiers:
    bad.append(f'ca_named_comparators.tier_labels 的分组标题应为 {_want_tiers}，现在是 {_have}')
else:
    ok += 1
for _t in _tl:
    if not any(r.get('tier') == _t for r in _ncmp.get('rows', [])):
        bad.append(f'ca_named_comparators: tier_labels 里有 {_t!r} 但 rows 里没有这一组的基金')
# E48 最左列**整列**逐格核（Alex 2026-08-25:「最左侧那一列的所有东西都要一样」）
_lf = _ncmp.get('row_labels_fixed') or {}
_want_left = _lf.get('expected') or []
if not _want_left:
    bad.append('ca_named_comparators: 缺 row_labels_fixed.expected —— 最左列的字面量必须落账本')
else:
    _got_left = []
    for _t, _lab in _tl.items():
        _mem = [r for r in _ncmp.get('rows', []) if r.get('tier') == _t]
        if not _mem:
            continue
        if _lab:
            _got_left.append(_lab)
        for r in _mem:
            _got_left.append(r.get('row_label') or f'<缺 row_label: {r.get("label")}>')
    if _got_left != _want_left:
        for a, b in zip(_got_left + [''] * 9, _want_left + [''] * 9):
            if a != b:
                bad.append(f'ca_named_comparators 最左列对不上：账本 {a!r} ≠ 应为 {b!r}')
    else:
        ok += 1
    if any('House' in str(r.get('row_label')) or ' — ' in str(r.get('row_label', ''))[:40]
           and not str(r.get('row_label', '')).startswith('Junson')
           for r in _ncmp.get('rows', [])):
        bad.append('ca_named_comparators: 竞品行的 row_label 带了「House — 」前缀 —— '
                   '⛔ 同事那版不带，只有自家三只用 "Junson — " 开头')

# ── 冻结行名分两类：结构性硬冻，数据性只做同季一致性 ────────────────────
# ⛔ 2026-08-26 的教训：E38/E41/E42/E46/E48 的行名是**本季数据**（持仓、行业、成交），
#    当永久契约冻死等于保证下季硬失败。Alex 要的是列序与写法固定，不是行名永远不变。
for _slug in sorted(k for k, v in E.items() if (v or {}).get('row_labels_fixed')):
    _rlf = E[_slug]['row_labels_fixed']
    if 'structural' not in _rlf:
        bad.append(f'{_slug}.row_labels_fixed 缺 `structural` —— 必须说清这组行名是'
                   f'**固定词汇表**(true，硬冻) 还是**本季数据**(false，带 _rq 戳)')
        continue
    if _rlf['structural']:
        if not _rlf.get('_structural_why'):
            bad.append(f'{_slug}: structural=true 但没写 _structural_why')
        else:
            ok += 1
        continue
    _miss = [f for f in ('_rq', '_varies_why', '_frozen_part') if not _rlf.get(f)]
    if _miss:
        bad.append(f'{_slug}: structural=false 但缺 {_miss} —— 数据性行名必须写清'
                   f'「快照属于哪一季」「为什么会变」「真正不许变的是哪些写法」')
    elif _rlf['_rq'] != P.rq():
        print(f'  · {_slug}: 行名快照是 {_rlf["_rq"]} 的，本季 {P.rq()} —— '
              f'取数阶段确认过行集变动后要把 expected 与 _rq 更新到本季')
        ok += 1
    else:
        ok += 1

# 图形形态
FORM = {'fund_pag_comp_type': 'pie', 'fund_pag_comp_geo': 'pie',
        'fund_pag_comp_bank': 'vbars', 'fund_hsbc_sector': 'pie',
        'fund_hsbc_margin': 'vbars'}          # E44 也必须竖着（Alex 2026-08-25）
for slug, form in FORM.items():
    got = (E.get(slug) or {}).get('chart_form')
    if got != form:
        bad.append(f'{slug}: chart_form 应为 {form!r}，现在是 {got!r}')
    else:
        ok += 1

# ── 冻结了列宽的表：重算复核，短一格就报错 ─────────────────────────────
# ⛔ Alex 2026-08-26：E48「第一列的列宽拉长到能让第一列里的每一行都只用一行显示，也不要太长，
#    然后固定这个宽度」；E47「也设置一下 让第一列每一行的字就只占一行，跟 E48 要求一样」。
#    固定值在各 exhibit 的 col_widths_cm.widths。这里按同样的量法重算 —— 下季基金集合变了、
#    出现更长的名字或简称，必须在这儿炸出来，不许到纸上才发现折了行。
_TEXT_CM = 17.12          # 正文可用宽
_WFONT = None
try:                       # 有 fontTools + Carlito 就现场重量
    from fontTools.ttLib import TTFont as _TTF
    _FM = {}
    for _k, _pth in (('r', '/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf'),
                     ('b', '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf')):
        _f = _TTF(_pth)
        _FM[_k] = (_f['head'].unitsPerEm, _f['hmtx'].metrics, _f.getBestCmap())

    def _wcm(_s, _bold, _size=7.5):
        _upm, _hm, _cm = _FM['b' if _bold else 'r']
        return sum(_hm[_cm.get(ord(c)) or _cm.get(ord('?'))][0]
                   for c in str(_s)) / _upm * _size / 72 * 2.54
    _WFONT = _wcm
except Exception as _e:
    print(f'  · 列宽现场重量跳过（{type(_e).__name__}）—— 改用账本存的 _required_cm')

for _slug in sorted(k for k, v in E.items() if (v or {}).get('col_widths_cm')):
    _x = E[_slug]; _cw = _x['col_widths_cm']; _wid = _cw.get('widths') or []
    _hd = _x.get('header') or []
    _rws = _x.get('rows') or []
    # 无表头的小表（§8 Fund snapshot 左表）按**行宽**算列数
    _ncol = len(_hd) if _hd else (max((len(r) if isinstance(r, list) else 2)
                                      for r in _rws) if _rws else 0)
    if not _wid:
        bad.append(f'{_slug}: col_widths_cm 里没有 widths'); continue
    if not _cw.get('fixed'):
        bad.append(f'{_slug}.col_widths_cm.fixed 必须为 true —— python-docx 默认 autofit，'
                   f'只声明列宽 Word 会自己重算并抢走第一列的宽度')
        continue
    if len(_wid) != _ncol:
        bad.append(f'{_slug}: 列宽 {len(_wid)} 个 ≠ {_ncol} 列'); continue
    if sum(_wid) > _TEXT_CM + 1e-6:
        bad.append(f'{_slug}: 列宽合计 {sum(_wid):.2f}cm > 正文可用 {_TEXT_CM}cm')
    else:
        ok += 1
    _live = None
    if _WFONT:
        # 现场量得到的：表头（全列，粗体）+ 第一列的 row_label / 分组标题（粗体）
        _live = ([_WFONT(h, True) for h in _hd] if _hd
                 else [0.0] * _ncol)
        if not _hd:      # 无表头表：第一列量固定行名，其余列不量（值是长文本，允许换行）
            for _r in _rws:
                _lb = _r.get('label') if isinstance(_r, dict) else (_r[0] if _r else '')
                if _lb:
                    _live[0] = max(_live[0], _WFONT(_lb, True))
        _first = [(_x.get('tier_labels') or {}).get(k) for k in (_x.get('tier_labels') or {})]
        _first += [r.get('row_label') for r in (_x.get('rows') or [])]
        for _sv in _first:
            if _sv:
                _live[0] = max(_live[0], _WFONT(_sv, True))
        _live = [round(v + 0.38, 3) for v in _live]
    _stored = _cw.get('_required_cm') or []
    if _live and _stored and len(_live) == len(_stored):
        _need = [max(a, b) for a, b in zip(_live, _stored)]
    else:
        _need = _live or _stored or []
    if not _need:
        bad.append(f'{_slug}: 既量不到也没有 _required_cm，列宽无法复核'); continue
    _short = [f'第 {j+1} 列 ({_hd[j]!r}) 冻结 {w}cm < 需要 {n}cm（应 ≥ {n+0.10:.2f}）'
              for j, (w, n) in enumerate(zip(_wid, _need)) if w < n + 0.01]
    if _short:
        bad.append(f'{_slug} 列宽不够，纸上会折行：' + '；'.join(_short))
    else:
        ok += 1
    if _live and _stored and any(a > b + 0.02 for a, b in zip(_live, _stored)):
        print(f'  · {_slug}: 现场重量比账本 _required_cm 更宽（现场 {_live}）—— '
              f'内容变长了，把 _required_cm 和 widths 一起重算')

print(f'  对上的：{ok} 项')
if bad:
    print(f'  ✗ {len(bad)} 项不合规：')
    for b in bad:
        print('      ' + b)
    print('\n  ⛔ 表头是框架定死的（report-spec §8），不是每季自己想的。'
          '\n     季度标签从该 exhibit 的 periods 读；其余一个字都不许变。')
else:
    print('  ✓ §8 的结构与表头全部对上')
print()
sys.exit(1 if (bad and '--strict' in sys.argv) else 0)
