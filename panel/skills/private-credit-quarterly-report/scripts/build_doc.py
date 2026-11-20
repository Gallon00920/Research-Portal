# -*- coding: utf-8 -*-
"""阶段二：按 report-spec 组装 Junson Private Credit Quarterly Report（英文全篇）。

铁律：正文里凡 exhibit 上出现过的数，一律从 series.json 读 —— 不在这里手打。
      引用 exhibit 一律写 {{ex:slug}}，最后由 exhibits.resolve() 换成 Exhibit N。
"""
import json, io, sys, os
import re as _re_mod
sys.path.insert(0, '.')
import pcpaths as P
import exhibits
import docx_helpers as H

D = json.load(io.open('series.json', encoding='utf-8'))
E = D['exhibits']
META = D['meta']

# ⛔ 季度、出稿日、各层期标签一律从账本读,**不许在这里写字面量**。
#    2026Q3 踩过:RQ 和三张表的表头写死成 '2026Q3' / '1Q26' / '4Q25',
#    下季换文件夹跑出来会是「新数据 + 旧期名」—— 版面检查还会通过(文件名与页眉一起错)。
RQ = META['rq']
# ⛔ Alex 2026-08-26：「报告大标题的时间 为什么还是8月24日，你这个不能写死啊
#    必须是skill运行的当日的时间。」—— 标题块第三行的日期一律取**运行当日**，
#    不许从账本读、不许写字面量。账本里只留一条 `_last_built` 做记录（不参与印刷）。
from datetime import date as _date
DATE = _date.today().strftime('%-d %b, %Y')
PER = META['periods']                       # market_cq/pq、fund_cq/pq/ppq
OUT = P.report_name()          # 文件名里的季度来自账本，不许手打
EX = exhibits.load()


# ───────────────────────── 从账本取值的小工具 ─────────────────────────
class Miss(Exception):
    pass


def g(slug, *path, default=Miss):
    """按路径从账本取值。取不到就抛错 —— 宁可出稿失败，也不许静默写个错数。"""
    cur = E[slug]
    for k in path:
        try:
            cur = cur[k] if not isinstance(k, int) else cur[k]
        except (KeyError, IndexError, TypeError):
            if default is Miss:
                raise Miss(f'账本里取不到 {slug} → {"/".join(map(str, path))}')
            return default
    return cur


def last(slug, *path):
    v = g(slug, *path)
    return [x for x in v if x is not None][-1]


def num(x, dp=1, pct=False, unit=''):
    if x is None:
        return '—'
    s = f'{x:,.{dp}f}'
    if dp == 0:
        s = f'{x:,.0f}'
    return s + ('%' if pct else '') + unit


def _num(x):
    # 从 '14.7%' / '1.11x' 里取数 —— E47 的 delta 列要做差
    import re as _re
    m = _re.match(r'^-?[\d.]+', str(x).replace('%', '').replace('x', ''))
    return float(m.group()) if m else None


def note_of(slug):
    # Note 里也可以引用别的 exhibit —— 一律走 {{ex:slug}}，不许写死 "Exhibit 17"。
    # 编号每季会变，写死的编号下季就指错图（铁律二）。
    return exhibits.resolve(E[slug]['note'])


def cap(slug, **kw):
    """题注 = 编号（exhibits.py 是唯一来源）+ 文本。

    动态题注的文本一律取账本的 caption_rendered —— 那是按本季数据重写过、
    并且被 pc_review_sheet 逐个数检查过的版本。manifest 里的模板只作兜底。
    两边都有就核一遍：不一致直接报错，不许悄悄挑一个印上去。
    """
    cr = (E.get(slug) or {}).get('caption_rendered')
    if not cr:
        return EX.caption(slug, **kw)
    if kw:
        want = EX.rec(slug)['caption'].format(**kw)
        if want.strip() != cr.strip():
            raise SystemExit(
                f'✗ {slug} 的题注两处不一致：\n'
                f'  账本 caption_rendered ：{cr}\n'
                f'  manifest 模板填出来的：{want}\n'
                '  账本那份是本季重写、且过了核对清单的 —— 先定哪个对，再把另一处改齐。')
    return f'Exhibit {EX.n(slug)}: {cr}'


# 正文段落用 [(文字, 是否加粗), ...] 表达。
#
# ⛔ 加粗的规矩（Alex 2026-08-25 纠正，判据取自上一版成稿实测）：
#    基线成稿全篇正文只加粗 ~16 处 —— **每节最多一个「头条数字」**（US$2,557bn / 508bp /
#    4.37% / 5.7x / 2.8% / 14.7% 这类），外加 bullet 的引导短语（`Quarter activity:`、
#    新闻条的导语、TWSK 的判断句）。不是「关键数字都加粗」。
#    我第一版把几乎每个数都加粗了（正文 369 处，约每段 6 处，是基线的 12 倍），
#    读起来满屏黑点、反而没有重点 —— 这条规矩本来是我自己从基线误推出来的，现在收紧。
#
#    b()  = 标记「这是本段值得强调的数」；_bold_policy 只让**每段第一个**真正加粗，
#           其余自动降级为普通文字 —— 我的段落是「先水平、再变动、后归因」，
#           第一个 b() 就是该段的水平值，正好是头条数字。
#    hl() = 显式头条（与 b() 同效，语义更清楚，用在想强调「就是这个」的地方）
def b(x):
    return (str(x), True)


def hl(x):
    """本段/本节的头条数字 —— 真加粗。每段至多一个。"""
    return (str(x), True)


def lead(x):
    """bullet 的引导短语（`Quarter activity:` / 新闻导语 / TWSK 判断句）—— 真加粗。"""
    return (str(x), True)


def t(x):
    return (str(x), False)


def _bold_policy(parts, kind):
    """加粗策略的唯一出口：正文段最多留 1 处加粗（取第一处），bullet 的引导短语豁免。"""
    seen = 0
    out = []
    for i, (x, bo) in enumerate(parts):
        if bo:
            first_run = (i == 0)                 # 段首 = 引导短语，豁免
            if first_run and kind == 'bullet':
                out.append((x, True)); continue
            if seen == 0:
                out.append((x, True)); seen = 1; continue
            out.append((x, False)); continue
        out.append((x, bo))
    return out


PARTS = []          # (kind, payload) 的线性列表，最后统一渲染


# ── 章节号 → 印在纸上的标题 ────────────────────────────────────────────
# ⛔ Alex 2026-08-26 把标题里的「几点几」全去掉了，所以正文的交叉引用一律**写节名**，
#    不写节号（写了读者在纸上找不到）。节名只有这一处真值：`xr()` 从这里取，
#    `sec()` / `sub()` 反过来核对自己收到的标题在不在这里 —— 两边不许各写一份。
SEC = {
    '2':   'Market Size',
    '2.1': 'Private credit market size',
    '2.2': 'Supply side',
    '2.3': 'Demand side',
    '2.4': 'Fund flow — middle-market CLOs',
    '3':   'Returns & Relative Value',
    '3.1': 'Direct lending returns versus public credit',
    '3.2': 'Private credit spread premium over syndicated loans',
    '4':   'Pricing & Term',
    '4.1': 'Spread',
    '4.2': 'Covenant structure and PIK',
    '5':   'Credit Fundamentals',
    '5.1': 'Default rate',
    '5.2': 'Recovery rate',
    '5.3': 'Leverage',
    '5.4': 'Interest coverage',
    '5.5': 'BDC non-accruals',
    '5.6': 'PIK income as a share of investment income',
    '6':   'Sentiment',
    '6.1': 'Broker summary',
    '6.2': 'Related news',
    '7':   'Things We Should Know',
    '8':   'Fund Update',
    '9':   'Competitor Analysis',
    '9.1': 'Positioning scorecard',
    '9.2': 'Relative momentum and percentile trajectory',
    '9.3': 'Cohort health monitor',
    '9.4': 'Appendix — peer universe and methodology',
    '10':  'Disclaimer',
}
_SEEN_HEADINGS = set()


def xr(no):
    """正文交叉引用：写节名，⛔ 不许写节号。"""
    if no not in SEC:
        raise SystemExit(f'✗ 正文引用了不存在的节号 {no!r} —— SEC 里没有这一节')
    return SEC[no]


def sec(title):
    _SEEN_HEADINGS.add(title)
    PARTS.append(('sec', title))


_SECNO = _re_mod.compile(r'^\d+(?:\.\d+)*[.、]?\s+')


def sub(title):
    """小节标题。⛔ Alex 2026-08-26：「把每个标题前面的几点几都去掉 …
    只要去掉数字和小数点，标题部分其他不变。」

    调用点仍写 '9.1  Positioning scorecard' —— 节号是 report-spec 的节序契约，
    删了就没法核对顺序；这里只在**印之前**剥掉前缀，标题其余部分一个字不动。"""
    _t = _SECNO.sub('', title)
    _SEEN_HEADINGS.add(_t)
    PARTS.append(('sub', _t))


def minor(title):
    PARTS.append(('minor', title))


def tblp(label, header, rows, widths=None, bold_first=True, note=None, fixed_cols=False):
    """无编号小表（§8 Fund snapshot 两张表）。"""
    PARTS.append(('tblp', (label, header, rows, widths, bold_first, note, fixed_cols)))


def para(parts):
    PARTS.append(('body', parts if isinstance(parts, list) else [t(parts)]))


def blt(parts):
    PARTS.append(('bullet', parts if isinstance(parts, list) else [t(parts)]))


def bltlink(parts, url, link_text):
    """带来源超链接的 bullet —— Related news 每条必须能点开那一篇。"""
    PARTS.append(('bulletlink', (parts, url, link_text)))


def _dropped(slug):
    """本季缺源文件、已从报告删掉的图（账本 meta.skipped）—— 不插、不占号。"""
    return slug in EX.skipped


def ex1(slug, **kw):
    if _dropped(slug):
        return
    PARTS.append(('ex', (slug, kw)))


def expair(l, r):
    # 并排的两张删了一张：剩下那张单独一行；两张都删了就什么都不插
    l = None if (l is None or _dropped(l)) else l
    r = None if (r is None or _dropped(r)) else r
    if l and r:
        PARTS.append(('expair', (l, r)))
    elif l or r:
        PARTS.append(('ex', (l or r, {})))


def tbl(slug, header, rows, widths=None, bold_first=True, group_rows=None, zebra=None,
        fixed_cols=False):
    if _dropped(slug):
        return
    PARTS.append(('tbl', (slug, header, rows, widths, bold_first, group_rows, zebra,
                          fixed_cols)))


ND = 'n/d'          # not disclosed —— 源报告本季没给这个数
NA = 'n/a'          # 做不出差（缺一头）
NEWV = 'new'        # 上季没有、本季新增


def qoq_cells(pq, cq, fmt=lambda v: f'{v:g}', unit='pp'):
    """一格三值 → (上季, 本季, QoQ Δ)。缺一头就降级，⛔ 绝不拿另一头顶上。

    ⛔ Alex 2026-08-26：「某个数可能下个季度没提供，如果要有 QoQ Chg 的话那就是 n/a」。
      · 本季缺 → 本季印 n/d，Δ 印 n/a（⛔ 不许沿用上季值当本季值）
      · 上季缺 → 上季印 n/d，Δ 印 new
      · 两头都缺 → 三格全 n/d / n/a，该 exhibit 要写 gap 说明
    """
    if cq is None and pq is None:
        return (ND, ND, NA)
    if cq is None:
        return (fmt(pq), ND, NA)
    if pq is None:
        return (ND, fmt(cq), NEWV)
    _d = cq - pq
    return (fmt(pq), fmt(cq),
            f'0.0{unit}' if _d == 0 else f'{_d:+.0f}{unit}')


def _dirword(delta, tmpl):
    """把账本的 '+1pp' / '-3pp' / '0.0pp' 翻成 rose 1pp / fell 3pp / was unchanged at。"""
    d = str(delta).strip()
    v = d.lstrip('+-')
    if d.startswith('-'):
        return tmpl.format('fell', v)
    if d.startswith('+'):
        return tmpl.format('rose', v)
    return tmpl.format('was unchanged', 'at').replace(' at at ', ' at ')


def _ppmove(slug, i):
    """从饼图条目的 vals / vals_pq 现算「up 3pp」这种说法 —— ⛔ 不许写死。"""
    c, q = g(slug, 'vals')[i], g(slug, 'vals_pq')[i]
    d = c - q
    return 'unchanged' if d == 0 else f'{"up" if d > 0 else "down"} {abs(d):.0f}pp'

def _fixcol(slug, rows, key='expected'):
    """冻结了最左列的表：印之前逐格核一遍。

    Alex 2026-08-26：「表头顺序都给我定死，以及最左边的这一列」。
    pc_hdrcheck 查账本、pc_docxcheck 查纸面，这一条查**中间那一步** ——
    build_doc 自己拼出来的行序，免得再出一次「账本绿、纸上错」。

    ⛔ 分两类（`row_labels_fixed.structural`），因为「冻结」对两类表意思不同：
      structural=True  —— 行名是固定词汇表（KPI 名、snapshot 条目名）。对不上直接炸。
      structural=False —— 行名是**本季数据**（持仓名、行业名、本季成交）。
          同季对不上 = 出稿代码拼错了，炸；
          跨季对不上 = 数据本来就该变（新投/退出/重排），**打印差异让人确认，不炸**。
          2026-08-26 的教训：把 E38/E41/E42/E46/E48 的行名当永久契约冻死，
          下季一定硬失败 —— Alex 要的是列序和写法固定，不是这十一个项目名永远不变。"""
    rlf = g(slug, 'row_labels_fixed')
    want = list(rlf[key])
    got = [r[0] for r in rows]
    if got == want:
        return rows
    if rlf.get('structural', True):
        raise SystemExit(f'✗ {slug} 最左列对不上冻结清单（结构性，行名是固定词汇表）\n'
                         f'    应为 {want}\n    实为 {got}\n'
                         f'    {rlf.get("_structural_why", "")}')
    if rlf.get('_rq') == RQ:
        raise SystemExit(f'✗ {slug} 最左列对不上本季快照（_rq={RQ} 就是本季）——\n'
                         f'    同季对不上只可能是出稿代码拼错了，不是数据变了\n'
                         f'    应为 {want}\n    实为 {got}')
    # 跨季：行集变了是正常的，打印差异，把快照更新的责任交回取数阶段
    _out = [x for x in want if x not in got]
    _in = [x for x in got if x not in want]
    ROWDIFF.append((slug, rlf.get('_rq'), _out, _in))
    return rows


ROWDIFF = []      # 数据性行名跨季变动，收尾统一打印
GAPS = []         # 本季缺披露的格子，收尾统一打印并要求写 gap 说明


def _panel_qoq(slug, side, src_slug):
    """§8 双栏表的一栏：按账本的行规格从饼图条目合成「上季 / 本季 / QoQ Δ」。

    行规格 `from` 用 || 分隔要合并的切片名，`agg='sum'` 表示相加。
    上季缺这一片（本季新增）就印 — / new —— ⛔ 不许当 0% 去做差。"""
    ent = E[src_slug]
    labs, cq, pq = ent['labels'], ent['vals'], ent['vals_pq']
    out = []
    for sp in g(slug, 'row_labels_fixed', side):
        ks = [x.strip() for x in sp['from'].split('||')]
        miss = [k for k in ks if k not in labs]
        if miss:
            raise SystemExit(f'✗ {slug} 的行「{sp["label"]}」在 {src_slug} 里找不到切片 {miss}')
        ix = [labs.index(k) for k in ks]
        _c = [cq[i] for i in ix]
        _p = [pq[i] for i in ix]
        C = None if any(v is None for v in _c) else sum(_c)
        P = None if any(v is None for v in _p) else sum(_p)
        # ⛔ 缺一头就降级，不再硬失败 —— 源报告少披露一片是常态（Alex 2026-08-26）。
        #    上季缺 → new；本季缺 → n/d + n/a，⛔ 绝不拿上季值当本季值。
        _pq, _cq, _dl = qoq_cells(P, C, fmt=lambda v: f'{v:.0f}%')
        if P is None and C is not None:
            _dl = g(slug, '_delta_marker_new')        # 账本里写的就是 'new'
        out.append([sp['label'], _pq, _cq, _dl])
        if C is None:
            GAPS.append((slug, sp['label'], '本季源报告没披露这一片'))
    return out


def _twopanel(slug):
    """左栏 + 右栏并成八列；行数不齐的用空格补满。"""
    L = _panel_qoq(slug, 'left', g(slug, 'row_labels_fixed', 'src_left'))
    R = _panel_qoq(slug, 'right', g(slug, 'row_labels_fixed', 'src_right'))
    _fixcol(slug, L)
    _fixcol(slug, R, 'right_col')
    n = max(len(L), len(R))
    return [(L[i] if i < len(L) else ['', '', '', ''])
            + (R[i] if i < len(R) else ['', '', '', '']) for i in range(n)]

def pagebreak():
    PARTS.append(('pb', None))


# ═════════════════════════════ 2. Market Size ═════════════════════════════
sec('Market Size')

_p = g('mkt_aum_by_channel', 'periods')
_inst = g('mkt_aum_by_channel', 'stacks', 'Institutional')
_ret = g('mkt_aum_by_channel', 'stacks', 'Retail')
_ins = g('mkt_aum_by_channel', 'stacks', 'Insurance estimate')
_tot = _inst[-1] + _ret[-1] + _ins[-1]
sub('2.1  Private credit market size')
para([
    t('Global private debt assets under management reached '),
    b(f'US${_tot/1000:.2f}tn'), t(f' at the end of {_p[-1]}, split between '),
    b(f'US${_inst[-1]:,.0f}bn'), t(f' ({_inst[-1]/_tot*100:.0f}%) of institutional capital, '),
    b(f'US${_ret[-1]:,.0f}bn'), t(f' ({_ret[-1]/_tot*100:.0f}%) raised through retail vehicles and an estimated '),
    b(f'US${_ins[-1]:,.0f}bn'), t(f' ({_ins[-1]/_tot*100:.0f}%) held on insurance balance sheets. '),
    t('The shape of that growth matters more than the level. Institutional AUM has risen '),
    b(f'{_inst[-1]/_inst[0]:.1f}x'), t(f' since {_p[0]}, but the composition has shifted decisively from '
      'commitments waiting to be deployed towards capital already at work: dry powder grew '),
    b(f'{g("mkt_inst_aum_decomp","stacks","Dry powder")[-1]/g("mkt_inst_aum_decomp","stacks","Dry powder")[0]:.1f}x'),
    t(' over the same period while NAV grew '),
    b(f'{g("mkt_inst_aum_decomp","stacks","NAV")[-1]/g("mkt_inst_aum_decomp","stacks","NAV")[0]:.1f}x'),
    t('. Retail is the fastest-growing channel from a small base, and the insurance estimate only '
      'appears from 2023 in the source data — the earlier years are not zero exposure but '
      'unmeasured exposure.'),
])
ex1('mkt_aum_by_channel', y0=_p[0], y1=_p[-1])

_lv = g('mkt_us_levcredit_split', 'labels'), g('mkt_us_levcredit_split', 'vals')
_hold = g('mkt_us_levcredit_split', 'panels', 'right')
para([
    t('Within the US, private credit is now a co-equal third of the leveraged credit market: '),
    b(f'{_lv[1][2]:.0f}%'), t(' against '), b(f'{_lv[1][0]:.0f}%'),
    t(' for leveraged loans and '), b(f'{_lv[1][1]:.0f}%'), t(' for high yield. '),
    t('Ownership of that stack is more concentrated than the headline suggests. '),
    b(f'{_hold["vals"][0]:.0f}%'), t(f' sits with {_hold["labels"][0]} and '),
    b(f'{_hold["vals"][1]:.0f}%'), t(f' with {_hold["labels"][1]} — so roughly '),
    b(f'{_hold["vals"][0]+_hold["vals"][1]:.0f}%'),
    t(' of the asset class is held in vehicles that mark to model rather than to market. '
      'PC CLOs add another '), b(f'{_hold["vals"][2]:.0f}%'),
    t(f', with pensions and insurers holding the remaining {_hold["vals"][3]+_hold["vals"][4]:.0f}%. '
      'That structure is why BDC disclosure is the most useful public window into private credit '
      'credit quality, and why this report leans on it heavily in ' + xr('5') + '.'),
])
ex1('mkt_us_levcredit_split')

sub('2.2  Supply side')
_dp = g('mkt_inst_aum_decomp', 'stacks', 'Dry powder')
_nav = g('mkt_inst_aum_decomp', 'stacks', 'NAV')
_dpr = g('mkt_inst_aum_decomp', 'rhs_line', 'vals')
_cr = g('mkt_fundraising', 'stacks', 'Capital raised')
_fc = g('mkt_fundraising', 'rhs_line', 'vals')
_afs = g('mkt_fundraising', 'aux', 'avg_fund_size_usdm')
para([
    t('Dry powder stood at '), b(f'US${_dp[-1]:,.0f}bn'), t(f' at end-{_p[-1]}, down from '),
    b(f'US${_dp[-2]:,.0f}bn'), t(' a year earlier and the first annual decline in the series. '
      'Measured against the NAV it has to be deployed into, the overhang is now '),
    b(f'{_dpr[-1]:.1f}%'), t(' — the lowest reading since 2015 and well below the '),
    b(f'{max(_dpr):.1f}%'), t(f' peak in {_p[_dpr.index(max(_dpr))]}. '
      'Read alongside fundraising, this is a market that is digesting rather than accumulating: '
      'capital raised fell to '), b(f'US${_cr[-1]:,.0f}bn'), t(' from '),
    b(f'US${_cr[-2]:,.0f}bn'), t(f' and a {max(_cr):,.0f}bn peak in {_p[_cr.index(max(_cr))]}, '
      'while the number of funds closing collapsed to '), b(f'{_fc[-1]:,.0f}'),
    t(f' from {max(_fc):,.0f} in {_p[_fc.index(max(_fc))]}. '
      'Fewer, larger funds is the clearest structural signal in this section: the average fund '
      'closing in '), b(f'{_p[-1]}'), t(' raised '),
    b(f'US${_afs["last_period"]:,.1f}m'), t(f' against US${_afs["first_period"]:,.1f}m in {_p[0]}.'),
])
expair('mkt_inst_aum_decomp', 'mkt_fundraising')


sub('2.3  Demand side')
_o5 = g('mkt_dl_origination', 'aux', 'ytd_2026')
_om = g('mkt_dl_origination', 'periods')
_orf = g('mkt_dl_origination', 'stacks', 'Refi')
_onr = g('mkt_dl_origination', 'stacks', 'Non-refi')
_osh = g('mkt_dl_origination', 'rhs_line', 'vals')
_opk = g('mkt_dl_origination', 'aux', 'peak_month')
_lq = g('mkt_dl_origination', 'aux', 'lcd_quarterly')
_l6b = g('mkt_lbo_bsl_vs_private', 'stacks', 'Syndicated loans')
_l6p = g('mkt_lbo_bsl_vs_private', 'stacks', 'Private credit')
_l6q = g('mkt_lbo_bsl_vs_private', 'periods')
_l6l = g('mkt_lbo_bsl_vs_private', 'rhs_line', 'vals')
_l6e = g('mkt_lbo_bsl_vs_private', 'aux', 'ltm_endpoint_pct')
_l6pk = g('mkt_lbo_bsl_vs_private', 'aux', 'peak_ltm_pct')
_lmax = max(x for x in _l6l if x is not None)
para([
    t('Private credit now finances the large majority of sponsor buyouts. On a last-twelve-months '
      'count basis the private markets funded '), b(f'{_l6e["measured_from_line"]:.0f}%'),
    t(f' of LBOs as at {_l6q[-1]}, against '), b(f'{_l6pk:.0f}%'),
    t(f' at the {_l6q[_l6l.index(_lmax)]} peak and around '),
    b(f'{[x for x in _l6l if x is not None][0]:.0f}%'), t(' when the series starts. '
      'The quarter itself split '), b(f'{_l6p[-1]:,.0f}'), t(' private deals against '),
    b(f'{_l6b[-1]:,.0f}'), t(' syndicated ones. The share has been flat in the low 80s for eight '
      'quarters now — the land grab is finished, and from here private credit grows with sponsor '
      'activity rather than by taking share. Our own independent check reproduces the source’s '
      'LTM line to within 1.1pp at every point '),
    t('(see the note to '), t('{{ex:mkt_lbo_bsl_vs_private}}'), t(').'),
])
para([
    t('Origination volume, though, is down. KBRA tracked '),
    b(f'~US${_o5["kbra_disclosed_usdbn"]:,.0f}bn'),
    t(' of direct lending originations in the first five months of 2026, '),
    b(f'{_o5["kbra_disclosed_yoy_pct"]:+.0f}%'), t(' year on year, and the decline is almost '
      'entirely refinancing: refi accounted for just '),
    b(f'{_o5["refi_share_ytd_pct"]:.0f}%'), t(f' of year-to-date volume, so the non-refi share has '
      f'climbed back to '), b(f'{_osh[-1]:.0f}%'), t(f' on a three-month average from a low of '),
    b(f'{min(x for x in _osh if x is not None):.0f}%'),
    t(f' in {_om[_osh.index(min(x for x in _osh if x is not None))]}. '
      'New money has held up better than the headline: '),
    b(f'~US${_o5["lbo_financing_ytd_usdbn"]:,.0f}bn'),
    t(f' of LBO financing ({_o5["lbo_financing_yoy_pct"]:+.0f}% y/y) and '),
    b(f'US${_o5["addon_ma_ytd_usdbn"]:,.0f}bn'),
    t(f' of add-on M&A ({_o5["addon_ma_yoy_pct"]:+.0f}%). '
      f'The monthly series peaked at '), b(f'US${_opk["total_usdbn"]:.0f}bn'),
    t(f' in {_opk["label"]} and May 2026 was the weakest month for new money in three years.'),
])
para([
    t('On LCD’s quarterly measure the latest full quarter was still the strongest of the series: '),
    b(f'US${_lq["estimated_volume_usdbn"][-2]:,.1f}bn'), t(' across '),
    b(f'{_lq["deal_count"][-2]:,.0f}'), t(f' deals in {_lq["periods"][-2]}, against '),
    b(f'US${_lq["estimated_volume_usdbn"][-3]:,.1f}bn'), t(' across '),
    b(f'{_lq["deal_count"][-3]:,.0f}'), t(f' in {_lq["periods"][-3]}. '
      f'The two sources disagree in direction because they measure different things — KBRA counts '
      f'calendar months to May and LCD counts completed quarters to March — and the '
      f'{_lq["periods"][-1]} LCD figure is a partial print. '
      'The read-through for our holdings is that origination capacity is not the constraint this '
      'cycle: pricing and structure are, which is where ' + xr('3') + ' and ' + xr('4')
      + ' go next.'),
])
expair('mkt_dl_origination', 'mkt_lbo_bsl_vs_private')

sub('2.4  Fund flow — middle-market CLOs')
_cy = g('mkt_mmclo_issuance_spread', 'periods')
_ci = g('mkt_mmclo_issuance_spread', 'stacks', 'MM CLO new issuance')
_cs = g('mkt_mmclo_issuance_spread', 'rhs_line', 'vals')
_yt = g('mkt_mmclo_issuance_spread', 'ytd')
_sh = g('mkt_mmclo_issuance_spread', 'aux', 'mm_share_of_total_clo_issuance_pct')
_nobs = g('mkt_mmclo_issuance_spread', 'aux', 'spread_months_observed')
# 末列是 26 YTD（不完整年度）；讲全年一律用倒数第二列
_FY = -2
_ytdbar = g('mkt_mmclo_issuance_spread', 'aux', 'ytd_bar')
para([
    t('Middle-market CLO issuance reached '), b(f'US${_ci[_FY]:,.2f}bn'), t(f' in {_cy[_FY]}, essentially '
      'matching the '), b(f'US${max(_ci):,.2f}bn'), t(f' record set in {_cy[_ci.index(max(_ci))]} and '),
    b(f'{_ci[_FY]/_ci[0]:.0f}x'), t(f' the {_cy[0]} level. MM CLOs now take '),
    b(f'{_sh[-1]:.1f}%'), t(' of all US CLO issuance. Year to date the picture is softer — the final '
      'column on the chart is 2026 through March: '),
    b(f'US${_yt["2026_through_March"]["mm_new_issue"]:,.2f}bn'),
    t(' through March against '), b(f'US${_yt["2025_through_March"]["mm_new_issue"]:,.2f}bn'),
    t(f' a year earlier ({_yt["pct_change_yoy"]["mm_new_issue"]:+.1f}%), and the reset/refi market '
      'has all but shut — '), b(f'US${_yt["resets_refis"]["2026_through_March"]["mm"]:,.2f}bn'),
    t(f' against US${_yt["resets_refis"]["2025_through_March"]["mm"]:,.2f}bn, '),
    b(f'{_yt["resets_refis"]["pct_change_yoy"]["mm"]:+.1f}%'), t('.'),
])
para([
    t('On pricing, the average MM CLO ‘AAA’ spread narrowed to '),
    b(f'{_cs[_FY]:,.0f}bp'), t(f' in {_cy[_FY]} from a '), b(f'{max(x for x in _cs if x):,.0f}bp'),
    t(f' peak in {_cy[_cs.index(max(x for x in _cs if x))]}, and averaged '),
    b(f'{_ytdbar["mm_aaa_spread_avg_bps"]:,.0f}bp'), t(' over the first three months of 2026. '
      'Two caveats travel with that line. '
      'First, the source chart only starts in January 2020, and the early annual averages rest on '
      'very few monthly prints — '), b(f'{_nobs[8]} months in {_cy[8]}'), t(' and '),
    b(f'{_nobs[9]} in {_cy[9]}'), t(' — which is why those markers are drawn hollow. '
      'Second, the basis to BSL CLOs depends entirely on the window: on a first-quarter average it '
      'narrowed slightly year on year, but within 2026 it widened from '),
    b('17.8bp in January'), t(' to '), b('33.0bp in March'),
    t('. The March widening is the fresher signal and is consistent with the public-loan selloff '
      'discussed in ' + xr('4') + '.'),
])
ex1('mkt_mmclo_issuance_spread')


# ═══════════════════ 3. Returns & Relative Value ═══════════════════
sec('Returns & Relative Value')

sub('3.1  Direct lending returns versus public credit')
_rr = {r[0]: r[1:] for r in g('ret_risk_return_table', 'rows')}
_rc = g('ret_risk_return_table', 'cols')[1:]
_i = {c: k for k, c in enumerate(_rc)}
para([
    t('Since 2015 private debt has returned '), b(_rr['Annualised return'][_i['Private debt (All)']]),
    t(' a year with '), b(_rr['Annualised return volatility'][_i['Private debt (All)']]),
    t(' of volatility, for a Sharpe ratio of '), b(_rr['Sharpe ratio'][_i['Private debt (All)']]),
    t(' against '), b(_rr['Sharpe ratio'][_i['HY']]), t(' for high yield and '),
    b(_rr['Sharpe ratio'][_i['All BSLs']]), t(' for broadly syndicated loans. '
      'Taken at face value that is an implausibly good risk-adjusted record, and the reason is '
      'in the denominator rather than the numerator: the private debt series is built from '
      'Lincoln International’s discounted-cash-flow fair values, not observed prices, so quarterly '
      'volatility of '), b(_rr['Annualised return volatility'][_i['Private debt (All)']]),
    t(' reflects a valuation process as much as it reflects credit risk. '
      'The correlation row is the tell — private debt correlates '),
    b(_rr['Correlation with private debt'][_i['All BSLs']]),
    t(' with syndicated loans, so the underlying exposure is far closer to public leveraged credit '
      'than the volatility gap implies. We read the Sharpe ratios as a smoothing artefact and '
      'anchor on yield instead.'),
])
para([
    t('On yield the ranking is cleaner and holds up. Private debt has yielded '),
    b(_rr['Yield (2017–now)'][_i['Private debt (All)']]), t(' since 2017 against '),
    b(_rr['Yield (2017–now)'][_i['Single B BSLs']]), t(' for single-B syndicated loans and '),
    b(_rr['Yield (2017–now)'][_i['HY']]), t(' for high yield. Within private debt the lower middle '
      'market pays the most — '), b(_rr['Yield (2017–now)'][_i['Lower MM']]),
    t(' against '), b(_rr['Yield (2017–now)'][_i['Upper MM']]),
    t(' in the upper middle market — while carrying the lowest reported volatility, which is again '
      'a marking artefact rather than evidence that smaller borrowers are safer.'),
])
tbl('ret_risk_return_table', g('ret_risk_return_table', 'cols'),
    g('ret_risk_return_table', 'rows'), widths=[4.6] + [1.56] * 8)

# ── Ex 9（Alex 2026-08-24 定稿）：回报两条（p41 右图）+ HY YTW 一条，画在一张图。
#    正文先引收益率水平（aux.yield_context，as-labelled），再讲回报 —— 两个口径分开说。
_ra = g('ret_dl_vs_bsl_total_return', 'aux')
_rq = g('ret_dl_vs_bsl_total_return', 'periods')
_rl, _rg = _ra['lincoln'], _ra['morningstar']
_yc = _ra['yield_context']
_rhy = g('ret_dl_vs_bsl_total_return', 'lines', 'ICE BofA US High Yield (YTW, %)')
para([
    t('On a stock basis Lincoln’s senior debt portfolio is priced to yield '),
    b(f'{_yc["lincoln_yield_1q26"]:.1f}%'), t(f' as of {_rq[-1]}, '),
    b(f'{_yc["premium_pp"]:.1f}pp'), t(' above single-B loans at '),
    b(f'{_yc["lsta_singleb_yield_1q26"]:.1f}%'),
    t(' — the illiquidity and credit-risk premium. What the exhibit below shows is the other '
      'side of the same comparison: not what the books are priced to earn, but what they '
      'actually delivered, as trailing-twelve-month total returns, with the US high-yield '
      'yield-to-worst overlaid for context — two different measures deliberately on one chart. '
      f'Since {_ra["_stat_window"].split("–")[0]} Lincoln’s index returned '),
    b(f'{_rl["mean"]:.1f}%'), t(' a year on average with a standard deviation of '),
    b(f'{_rl["stdev_pp"]:.2f}pp'), t(' and '), b(f'{_rl["n_negative_quarters"]}'),
    t(' negative quarters; single-B loans averaged '), b(f'{_rg["mean"]:.1f}%'),
    t(' with a standard deviation of '), b(f'{_rg["stdev_pp"]:.2f}pp'), t(' and '),
    b(f'{_rg["n_negative_quarters"]}'), t(' negative quarters, ranging from '),
    b(f'{_rg["min"]:.1f}%'), t(f' ({_rg["min_period"]}) to '), b(f'{_rg["max"]:.1f}%'),
    t(f' ({_rg["max_period"]}). In {_rq[-1]} the two returns stand at '),
    b(f'{_rl["last"]:.1f}%'), t(' and '), b(f'{_rg["last"]:.1f}%'), t(' — a gap of '),
    b(f'{_ra["gap_pp"]["last"]:.1f}pp'), t(' against a '),
    b(f'{_ra["gap_pp"]["mean_last_40q"]:.2f}pp'),
    t(' average over the past ten years — while high yield offers '), b(f'{_rhy[-1]:.1f}%'),
    t(' to worst. Read the smoothness of the Lincoln line with the marking caveat firmly '
      'attached: the index is built from quarterly fair-value estimates on illiquid loans, not '
      'traded prices, so part of that stability is the measurement method rather than the '
      'credit.'),
])
ex1('ret_dl_vs_bsl_total_return', _width_cm=H.TALL_CM)   # tall 画布 5.30in，居中

sub('3.2  Private credit spread premium over syndicated loans')
_sq = g('ret_dl_spread_vs_bsl', 'periods')
_sdl = g('ret_dl_spread_vs_bsl', 'lines', 'Unitranche deals (rolling 90d)')
_sbsl = g('ret_dl_spread_vs_bsl', 'lines', 'Single B BSL')
_saux = g('ret_dl_spread_vs_bsl', 'aux')
_slq = _saux['lcd_quarterly']
_sq_q = _slq['periods']
_sdl_q = _slq['lines']['Direct lending spread (bps)']
_sbsl_q = _slq['lines']['Single B BSL spread (bps)']
_sprem_q = _slq['lines']['Premium (bps)']
para([
    t('On new originations the unitranche spread was '), b(f'{_sdl[-1]:,.0f}bp'),
    t(f' in {_sq[-1]} on a rolling 90-day basis, against '), b(f'{_sbsl[-1]:,.0f}bp'),
    t(' for single-B syndicated loans — a premium of '),
    b(f'{_saux["premium_bps_latest"]:,.0f}bp'), t('. Direct lending pricing has been remarkably '
      'stable through the public-loan selloff: the series troughed at '),
    b(f'{_saux["trough_feb26_bps"]:,.0f}bp'), t(' in February and has widened back since, while '
      'the syndicated comparator swung far harder — from '),
    b(f'{max(x for x in _sbsl if x):,.0f}bp'), t(f' at the start of the series to a low of '),
    b(f'{min(x for x in _sbsl if x):,.0f}bp'), t(' and back. That asymmetry is the whole case for '
      'the illiquidity premium: private pricing is negotiated, public pricing is marked.'),
])
para([
    t('On LCD’s quarterly measure the same picture reads a little differently, and the difference '
      'is worth naming. There the direct lending spread was '), b(f'{_sdl_q[-1]:,.0f}bp'),
    t(f' in {_sq_q[-1]} against '), b(f'{_sbsl_q[-1]:,.0f}bp'),
    t(' for single-B loans, a premium of '), b(f'{_sprem_q[-1]:,.0f}bp'),
    t(f' — up from {_sprem_q[-2]:,.0f}bp in {_sq_q[-2]} and the widest of the eight quarters that '
      'series covers. The two sources differ on the syndicated leg because they measure different '
      'loan populations, so the premium level is not comparable between them; the direction — '
      'wider — is the same in both.'),
])
_cq = g('ret_dl_spread_by_ebitda', 'labels')
# 键名带月份 —— 取最后一个键，别写字面量（下季源图换月份不用改代码）
_ebk = list(g('ret_dl_spread_by_ebitda', 'series'))[-1]
_c26 = g('ret_dl_spread_by_ebitda', 'series', _ebk)
_c25 = g('ret_dl_spread_by_ebitda', 'series', 'YE25')
_ytd = [a - bb for a, bb in zip(_c26, _c25)]
para([
    t('The cohort detail matters more than the average. Year to date the upper middle market has '
      'repriced hardest — the '), b(_cq[3]), t(' cohort widened '), b(f'{_ytd[3]:+,.0f}bp'),
    t(f' to {_c26[3]:,.0f}bp — while the two sub-US$50m cohorts barely moved ('),
    b(f'{_ytd[0]:+,.0f}bp'), t(' and '), b(f'{_ytd[1]:+,.0f}bp'), t('). '
      'That is the signature of a public-market shock transmitting into the part of private credit '
      'that competes most directly with syndicated loans, and it is corroborated by the single-B '
      'syndicated comparator widening '), b(f'{_ytd[4]:+,.0f}bp'), t(' over the same period — the '
      'largest move of any cohort on the chart. Smaller borrowers, which have no syndicated '
      'alternative, saw no such repricing.'),
])
expair('ret_dl_spread_vs_bsl', 'ret_dl_spread_by_ebitda')


# ═════════════════════════ 4. Pricing & Term ═════════════════════════
sec('Pricing & Term')

sub('4.1  Spread')
para([
    t('Pulling ' + xr('3.2') + ' together with the lender survey: new-origination spreads '
      'have widened '
      'at the large end and held flat at the small end, and lenders themselves expect terms to get '
      'tighter rather than looser from here. In the LCD survey for the quarter '),
    b('61%'), t(' of respondents expected loan covenants to tighten slightly and '),
    b('2%'), t(' considerably, against '), b('9%'), t(' expecting any loosening at all and '),
    b('28%'), t(' expecting no change — a net tightening bias of roughly '),
    b('54 points'), t('. That is a lender base that has already repriced risk in its own '
      'expectations, which is consistent with the upper-middle-market spread widening and with the '
      'covenant and PIK data below.'),
])

sub('4.2  Covenant structure and PIK')
_cg = g('prc_covenants_by_vintage', 'groups')
_cp = g('prc_covenants_by_vintage', 'periods')
_cl = g('prc_covenants_by_vintage', 'stacks', 'Cov-lite')
_n = len(_cp)
_upper = _cl[2 * _n:3 * _n]
_core = _cl[1 * _n:2 * _n]
_lower = _cl[0:_n]
para([
    t('Documentation quality is the sharpest dividing line in private credit today, and it splits '
      'by borrower size rather than by vintage. Every lower-middle-market deal in the '),
    b(f'{_cp[0]}–{_cp[-1]}'), t(' vintages retained at least one maintenance covenant — '),
    b('0% cov-lite'), t(' in all four years. In the upper middle market the cov-lite share reached '),
    b(f'{_upper[-1]}%'), t(f' in the {_cp[-1]} vintage against a {min(_upper[:-1])}–{max(_upper[:-1])}% '
      'range for the three prior vintages. The core middle market sits between the two at '),
    b(f'{_core[-1]}%'), t(f' for {_cp[-1]}. '
      'So the 2024 vintage is where documentation protection thinned out, and it thinned out only '
      'for the largest borrowers — precisely the cohort that also repriced hardest this year.'),
])
_pg = g('prc_pik_toggle_share', 'groups')
_ps = g('prc_pik_toggle_share', 'series')
para([
    t('PIK toggles tell the same story. In the '), b(f'{_cp[-1]}'), t(' vintage '),
    b(f'{_ps[_cp[-1]][2]}%'), t(f' of {_pg[2].lower()} deals were originated with a PIK feature '
      'against '), b(f'{_ps[_cp[-1]][1]}%'), t(f' in the {_pg[1].lower()} and '),
    b(f'{_ps[_cp[-1]][0]}%'), t(f' in the {_pg[0].lower()}. For the upper middle market that is a '
      'jump from '), b(f'{_ps[_cp[-2]][2]}%'), t(f' in {_cp[-2]}. '
      'Two of the twelve cells on the chart are blank in the source — the '),
    b(f'{_cp[0]} {_pg[1].lower()}'), t(' and '), b(f'{_cp[1]} {_pg[2].lower()}'),
    t(' vintages — and the source does not say whether that means zero or not disclosed, so we show '
      'them as not reported rather than as zero. Taken with the covenant data, the 2024 '
      'upper-middle-market vintage carries both the thinnest documentation and the most '
      'payment flexibility, which is the combination that shows up later as PIK-driven '
      'non-accruals rather than as clean defaults.'),
])
expair('prc_covenants_by_vintage', 'prc_pik_toggle_share')


# ═══════════════════════ 5. Credit Fundamentals ═══════════════════════
sec('Credit Fundamentals')

sub('5.1  Default rate')
_dq = g('cf_sp_default_vs_specgrade', 'periods')
_inc = g('cf_sp_default_vs_specgrade', 'lines', 'CE default rate (incl. selective defaults)')
_exc = g('cf_sp_default_vs_specgrade', 'lines', 'CE default rate (excl. selective defaults)')
_sg = g('cf_sp_default_vs_specgrade', 'lines', 'U.S. speculative-grade default rate')
para([
    t('S&P’s credit-estimate default rate including selective defaults was '),
    b(f'{_inc[-1]:.2f}%'), t(f' on a trailing twelve-month basis at {_dq[-1]}, down from '),
    b(f'{_inc[-4]:.2f}%'), t(f' at end-{_dq[-4].split()[1]}. That decline is entirely a '
      'selective-default story: strip selective defaults out and the rate is '),
    b(f'{_exc[-1]:.2f}%'), t(f', versus {_exc[-13]:.2f}% a year earlier — conventional defaults have '
      'been drifting up while distressed exchanges have been rolling off the twelve-month window. '
      'The gap between the two lines, '), b(f'{_inc[-1]-_exc[-1]:.1f}pp'), t(', is the amount of '
      'stress being resolved through amendment rather than through default, and it is the single '
      'most important number in this section. For reference the US speculative-grade rate stands at '),
    b(f'{_sg[-1]:.1f}%'), t(f', so credit-estimated private borrowers are defaulting {_inc[-1]-_sg[-1]:.1f}pp '
      'faster than public high yield on the same definition.'),
])
_ddl = g('cf_sp_dl_vs_bsl_default', 'lines', 'Direct lending defaults')
_dbsl = g('cf_sp_dl_vs_bsl_default', 'lines', 'BSL defaults')
para([
    t('Against syndicated loans the same measure shows direct lending at '), b(f'{_ddl[-1]:.1f}%'),
    t(' versus '), b(f'{_dbsl[-1]:.1f}%'), t(f' — a {_ddl[-1]-_dbsl[-1]:.1f}pp penalty for the private '
      'market. Both peaked far higher in 2020 ('), b(f'{max(_ddl):.1f}%'), t(' and '),
    b(f'{max(_dbsl):.1f}%'), t(' respectively) and the current levels are roughly half those highs. '
      'Morgan Stanley’s forward view is that direct lending defaults reach '), b('8%'),
    t(', similar to the COVID peak, but concentrated in software and AI-adjacent sectors rather than '
      'broad-based as in 2020 — a mix shift, not a repeat.'),
])
expair('cf_sp_default_vs_specgrade', 'cf_sp_dl_vs_bsl_default')

_pv = g('cf_provider_compare_table', 'rows')
_up = [r for r in _pv if '↑' in r['trend']]
_dn = [r for r in _pv if '↓' in r['trend']]
para([
    t('Any single default number in private credit is a methodology choice, so it is worth putting '
      'the five providers side by side. This quarter they disagree on direction as well as level: '),
    b(f'{len(_dn)}'), t(' reported lower defaults quarter on quarter ('),
    t(', '.join(f'{r["label"]} {r["pq"]}→{r["cq"]}' for r in _dn)), t(') while '),
    b(f'{len(_up)}'), t(' reported higher ('),
    t(', '.join(f'{r["label"]} {r["pq"]}→{r["cq"]}' for r in _up)), t('). '
      'The spread across providers is '),
    b(f'{min(float(r["cq"].rstrip("%")) for r in _pv):.1f}%–{max(float(r["cq"].rstrip("%")) for r in _pv):.1f}%'),
    t(' for what is nominally the same asset class. The levels are not comparable — Fitch annualises '
      'while S&P uses a trailing twelve months, KBRA covers only senior secured non-syndicated term '
      'loans, and Proskauer counts loans rather than issuers — so only the direction within each row '
      'carries information. Read that way, the honest summary is that defaults are flat to slightly '
      'lower on most definitions and the dispersion tells you how much of the answer depends on who '
      'is counting.'),
])
# ⛔ Alex 2026-08-25：列名全部固定，只有倒数第二/第三列的季度跟着报告走 ——
#    那两个期名从**本图自己的 periods** 读（源表 p27 的列头），不许借 meta.periods
#    的任何一层（market 是 1Q26/2Q26，fund 这季刚好等于 4Q25/1Q26，是巧合）。
_pp = g('cf_provider_compare_table', 'periods')
# ⛔ 七个列名从账本的 header_template 读，不许在这里写死 —— 记住的格式一律落账本
#    （Alex 2026-08-26：「都是要你记住格式，而不是每次运行的时候去看同事的报告」）。
_phdr = [c.replace('<pq>', str(_pp[0])).replace('<cq>', str(_pp[1]))
         for c in g('cf_provider_compare_table', 'header_template')]
tbl('cf_provider_compare_table',
    _phdr,
    [[r['label'], r['sample_scope'], r['definition_method'], r['pq'], r['cq'],
      r['trend'], r['cohort']] for r in _pv],
    widths=[1.9, 4.6, 4.6, 1.15, 1.15, 1.0, 1.75], bold_first=True)

_fq = g('cf_fitch_ttm_default', 'periods')
_fv = g('cf_fitch_ttm_default', 'stacks', 'Fitch TTM private credit default rate (%)')
_kc = g('cf_kbra_dld_default', 'labels')
_ka = g('cf_kbra_dld_default', 'series', "Apr '26")
_kd = g('cf_kbra_dld_default', 'series', "Dec '25")
para([
    t('Fitch’s series, which is the highest of the five, reached '), b(f'{_fv[-1]:.1f}%'),
    t(f' in {_fq[-1]} from {_fv[-2]:.1f}% the month before — so on Fitch’s definition the trend '
      'turned back up after the first quarter. KBRA’s issuer measure moved the other way across all '
      'three private-market cohorts: direct lending overall fell to '), b(f'{_ka[0]:.1f}%'),
    t(f' from {_kd[0]:.1f}%, sponsored to {_ka[1]:.1f}% from {_kd[1]:.1f}% and lower middle market to '
      f'{_ka[2]:.1f}% from {_kd[2]:.1f}%, while high-yield bonds rose to '), b(f'{_ka[4]:.1f}%'),
    t(f' from {_kd[4]:.1f}%. On KBRA’s numbers the private market improved while the public market '
      'deteriorated — the opposite of the S&P comparison above, and a good illustration of why we '
      'show the provider table rather than picking a house number.'),
])
expair('cf_fitch_ttm_default', 'cf_kbra_dld_default')

_sl = g('cf_fitch_default_by_sector', 'labels')
_sv = g('cf_fitch_default_by_sector', 'vals')
_tot_i = _sl.index('Total')
_sw = _sl.index('Technology Software')
para([
    t('By sector Fitch puts the overall direct lending default rate at '), b(f'{_sv[_tot_i]:.1f}%'),
    t(', with '), b(f'{_sl[0]} at {_sv[0]:.1f}%'), t(' at the top and '),
    b(f'{_sl[-2]} at {_sv[-2]:.1f}%'), t(' near the bottom. The finding that matters for this '
      'portfolio is that '), b(f'technology software sits at {_sv[_sw]:.1f}%'), t(', among the '
      'lowest of the twenty-one sectors and '),
    b(f'{_sv[_tot_i]-_sv[_sw]:.1f}pp'), t(' below the asset-class average. '
      'Software is where the market expects the next default wave and where it has not yet arrived. '
      'That gap between expectation and realisation is the crux of this quarter: the AI-disruption '
      'thesis is a forward view about a sector that is currently one of the better-performing ones, '
      'so it will be visible in marks and PIK behaviour long before it is visible in default counts.'),
])
ex1('cf_fitch_default_by_sector')


sub('5.2  Recovery rate')
_rg = g('cf_recovery_path', 'labels')
_r1 = g('cf_recovery_path', 'series', '1 year pre-default')
_rd = g('cf_recovery_path', 'series', 'Default date')
_sl2 = g('cf_recovery_by_sector', 'labels')
_sv2 = g('cf_recovery_by_sector', 'vals')
_swi = _sl2.index('Software')
para([
    t('BDC marks imply that recovery expectations erode steadily rather than collapsing at the '
      'moment of default. Across all direct lending the implied recovery falls from '),
    b(f'{_r1[0]:.1f} points'), t(' a year before default to '), b(f'{_rd[0]:.1f} points'),
    t(f' at the default date — a {_r1[0]-_rd[0]:.1f}-point slide over four quarters. '
      'Syndicated loans recover '), b(f'{_rd[3]:.1f} points'),
    t(f', so direct lending gives up {_rd[3]-_rd[0]:.1f} points relative to the public market. '
      'The PIK split is the more actionable cut: non-PIK loans recover '),
    b(f'{_rd[2]:.1f} points'), t(' against '), b(f'{_rd[1]:.1f} points'), t(' for PIK loans, a gap of '),
    b(f'{_rd[2]-_rd[1]:.1f} points'), t('. PIK is therefore not merely a timing accommodation — it '
      'is associated with materially worse outcomes when the loan does break, which is why '
      + xr('5.6') + ' tracks PIK share as a leading indicator rather than as a yield '
      'enhancement.'),
])
para([
    t('By sector the first-lien 2023–2026 average ranges from '), b(f'{_sv2[0]:.1f} points'),
    t(f' in {_sl2[0].lower()} down to '), b(f'{_sv2[-1]:.1f} points'), t(f' in {_sl2[-1].lower()}. '
      'Software sits mid-table at '), b(f'{_sv2[_swi]:.1f} points'), t(f', {_sv2[0]-_sv2[_swi]:.1f} '
      'points below the best sector. Combined with the default data above, software currently '
      'screens as average on recovery and better than average on default frequency — the risk in '
      'the sector is prospective, not realised.'),
])
expair('cf_recovery_path', 'cf_recovery_by_sector')

sub('5.3  Leverage')
_lb = g('cf_leverage_band', 'items')
_lq = g('cf_leverage_timeseries', 'periods')
_lf = g('cf_leverage_timeseries', 'lines', 'Fitch – private MM portfolio')
_ll = g('cf_leverage_timeseries', 'lines', 'Lincoln International')
_lp = [x for x in g('cf_leverage_timeseries', 'lines', 'Public loan borrowers (single B)') if x is not None]
_lbs = g('cf_leverage_band', 'scale')
_lbn = g('cf_leverage_band', 'bands')
def _band_of(v, edges=_lbs['band_edges'], names=_lbn):
    """连续刻度上的取值落在哪条评级带（低倍数在上）。"""
    for i, e in enumerate(edges):
        if v < e:
            return names[i]
    return names[-1]
para([
    t('On gross leverage the three markets line up in the order you would expect: '),
    t(', '.join(i['label'] for i in _lb)),
    t(f' — high yield sits in the {_band_of(_lb[0]["y"])} band on the agencies’ mapping while '
      f'direct lending maps to {_band_of(_lb[2]["y"])}. Direct lending carries '),
    b(f'{_lb[2]["y"] - _lb[0]["y"]:.1f}x'),
    t(' more leverage than high yield, which is the single clearest statement of what the '
      'illiquidity premium is compensating for.'),
])
para([
    t('The time series is more reassuring than the level. Fitch’s monitored private middle-market '
      'portfolio fell to '), b(f'{_lf[-1]:.1f}x'), t(f' in {_lq[-1]} from {_lf[-2]:.1f}x, and Lincoln’s '
      'median was flat at '), b(f'{_ll[-1]:.1f}x'), t(f'. Both are well below the {max(_lf):.1f}x peak '
      f'Fitch recorded in {_lq[_lf.index(max(_lf))]}. Public single-B borrowers sit at '),
    b(f'{_lp[-1]:.1f}x'), t(', so the private-public leverage gap has narrowed to roughly '),
    b(f'{_lf[-1]-_lp[-1]:.1f}x'), t(' on Fitch’s measure — from over 1.5x in 2022. '
      'Leverage is not where the deterioration is showing up this cycle.'),
])
expair('cf_leverage_band', 'cf_leverage_timeseries')

sub('5.4  Interest coverage')
_ib = g('cf_icr_band', 'items')
_ibs = g('cf_icr_band', 'scale')
_ibn = g('cf_icr_band', 'bands')
def _icr_band_of(v, edges=_ibs['band_edges'], names=_ibn):
    """覆盖倍数的评级带（高倍数在上，所以从上往下比大小反过来）。"""
    for i, e in enumerate(edges):
        if v > e:
            return names[i]
    return names[-1]
_cq2 = g('cf_ebitda_coverage_ts', 'periods')
_cf = g('cf_ebitda_coverage_ts', 'lines', 'Fitch – private MM portfolio')
_cl2 = [x for x in g('cf_ebitda_coverage_ts', 'lines', 'Lincoln International') if x is not None]
para([
    t('Coverage is the mirror image and the less comfortable one. Direct lending screens at '),
    b(_ib[2]['label'].split()[-1]), t(' of EBITDA-to-cash-interest against '),
    b(_ib[0]['label'].split()[-1]), t(' for high yield and '), b(_ib[1]['label'].split()[-1]),
    t(' for syndicated loans, which puts it a full rating band lower — in the '),
    b(_icr_band_of(_ib[2]['y'])), t(' band while high yield sits in '),
    b(_icr_band_of(_ib[0]['y'])), t('. Higher leverage at a floating rate is a '
      'coverage problem before it is a leverage problem.'),
])
para([
    t('The direction, though, has turned. Coverage improved again in '), b(f'{_cq2[-1]}'),
    t(', with Fitch’s portfolio at '), b(f'{_cf[-1]:.2f}x'), t(' and Lincoln at '),
    b(f'{_cl2[-1]:.2f}x'), t(f' — both back around 2.0x from troughs of {min(_cf):.2f}x and '
      f'{min(_cl2):.2f}x in 2023. The driver is the base rate rather than EBITDA: cash interest '
      'falls mechanically as SOFR comes down, so this improvement would reverse if rates stopped '
      'falling. We would treat the recovery from the 2023 trough as rate relief, not as operating '
      'repair, until EBITDA growth confirms it.'),
])
expair('cf_icr_band', 'cf_ebitda_coverage_ts')


sub('5.5  BDC non-accruals')
_nq = g('cf_bdc_nonaccrual_avg', 'periods')
_na = g('cf_bdc_nonaccrual_avg', 'lines', 'Avg nonaccrual at cost (%)')
_n8 = [x for x in g('cf_bdc_nonaccrual_avg', 'rhs_line', 'vals') if x is not None]
_npb = g('cf_bdc_nonaccrual_pubpriv', 'lines', 'Public BDCs')
_npv = g('cf_bdc_nonaccrual_pubpriv', 'lines', 'Private BDCs')
para([
    t('The average non-accrual rate at cost across BDCs rose to '), b(f'{_na[-1]:.1f}%'),
    t(f' in {_nq[-1]}, the highest reading in five years, and the share of BDCs reporting '
      'non-accruals above 8% rose to '), b(f'{_n8[-1]:.1f}%'), t('. Both series are still far below '
      'their 2020 peaks ('), b(f'{max(_na):.2f}%'), t(' and above 15% respectively — the share line '
      'exceeds the chart’s axis cap in mid-2020, so we show it as broken rather than guess a value). '
      'The direction is what counts: this is the fourth consecutive quarter of increase.'),
])
para([
    t('Splitting public from private is where the number becomes useful. Public BDCs reached '),
    b(f'{_npb[-1]:.2f}%'), t(' — a post-COVID high — while private vehicles sit at '),
    b(f'{_npv[-1]:.2f}%'), t(f', a gap of {_npb[-1]-_npv[-1]:.1f}pp. The tempting read is that '
      'private managers underwrite better. The likelier explanation is vintage: most non-traded BDCs '
      'were formed after 2022 and carry little exposure to the 2020–21 vintages where the losses sit, '
      'so a cleaner book is being compared with an older one. Morgan Stanley’s own vintage-controlled '
      'cut reverses the conclusion — among vehicles created before 2021, private BDC non-accruals '
      'have risen faster than public. For our purposes that means a private vehicle’s headline '
      'non-accrual rate is not evidence of quality unless it is adjusted for when the book was built.'),
])
expair('cf_bdc_nonaccrual_avg', 'cf_bdc_nonaccrual_pubpriv')

sub('5.6  PIK income as a share of investment income')
_pq2 = g('cf_bdc_pik_avg', 'periods')
_pa = g('cf_bdc_pik_avg', 'stacks', 'Avg PIK income / total investment income (%)')
_p12 = g('cf_bdc_pik_avg', 'rhs_line', 'vals')
_ppb = g('cf_bdc_pik_pubpriv', 'stacks', 'Public BDCs')
_ppv = g('cf_bdc_pik_pubpriv', 'stacks', 'Private BDCs')
para([
    t('PIK income ticked up to '), b(f'{_pa[-1]:.1f}%'), t(f' of total investment income in {_pq2[-1]}, '
      'and close to '), b(f'{_p12[-1]:.0f}%'), t(f' of BDCs reported PIK above 12% against '
      f'{_p12[-2]:.0f}% the prior quarter. The level looks modest; the composition does not. '
      'Public BDCs have gone from '), b(f'{_ppb[0]:.1f}%'), t(f' in {_pq2[0]} to '),
    b(f'{_ppb[-1]:.1f}%'), t(f' — {_ppb[-1]-_ppb[0]:+.1f}pp in thirteen quarters — while private '
      'vehicles have stayed inside a '), b(f'{min(_ppv):.1f}–{max(_ppv):.1f}%'), t(' range. '
      'Given the recovery evidence in ' + xr('5.2') + ', where PIK loans recover '),
    b(f'{_rd[2]-_rd[1]:.1f} points'), t(' less than non-PIK, a rising PIK share at the public '
      'vehicles is the clearest early-warning series in this report. Morgan Stanley adds that around '
      '20% of PIK loans are now marked below 90 points, at or above post-COVID highs — so the market '
      'is already discriminating between good and bad PIK even where the income statement is not.'),
])
expair('cf_bdc_pik_avg', 'cf_bdc_pik_pubpriv')


# ═══════════════════════════ 6. Sentiment ═══════════════════════════
sec('Sentiment')

sub('6.1  Broker summary')
# ⛔ 券商表按**本季文件夹里实际有的研报**出列（Alex 2026-08-26）——
#    照账本印会印出「报告本季不在文件夹里」的那一家。判据用 rows[*].file：
#    某一家名下一份研报都没有，这一列就不出，并进 DROPPED_HOUSES 供交付说明列出。
_QF = set()
for _r_, _d_, _fs_ in __import__('os').walk(P.quarter_dir()):
    _QF |= {f.lower() for f in _fs_}
_house_files = {}
for _r in g('sent_broker_summary', 'rows'):
    _house_files.setdefault(_r['house'], []).append(_r.get('file') or '')
_bc_all = g('sent_broker_summary', 'columns_en')
_bc, DROPPED_HOUSES = [], []
for _c in _bc_all:
    _fl = _house_files.get(_c['house'], [])
    _present = [f for f in _fl if f.lower() in _QF]
    if _present or not _fl:
        _bc.append(_c)
    else:
        DROPPED_HOUSES.append((_c['house'], _fl))
if not _bc:
    raise SystemExit('✗ 本季文件夹里一份券商研报都没有 —— §6.1 整节无从写起，'
                     '先走 pc_intake.py 的待决清单')
_nrep = sum(1 for _r in g('sent_broker_summary', 'rows')
            if (_r.get('file') or '').lower() in _QF)
_NUMW = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six', 7: 'Seven',
         8: 'Eight', 9: 'Nine', 10: 'Ten'}
para([
    t(f'{_NUMW.get(_nrep, _nrep)} sell-side reports reached us this quarter across '
      f'{_NUMW.get(len(_bc), len(_bc)).lower()} houses, published between '
      'April and August. The spread of views is narrow on diagnosis and wide on prescription: '
      'everyone agrees fundamentals are softening and dispersion is rising, but they disagree on '
      'whether spreads compensate for it. '),
    b('Barclays'), t(' and '), b('Morgan Stanley'), t(' describe deterioration that is contained; '),
    b('UBS'), t(' is the only house putting forward numbers on spread widening and the most bearish; '),
    b('Goldman Sachs'), t(' argues the yield-based bid caps any widening; and '),
    b('J.P. Morgan'), t(' looks at the channel nobody else covers — insurance balance sheets. '
      'Where they converge is on software and on vintage: the 2020–22 cohorts are the problem, and '
      'the software exposure inside them is the part still to play out.'),
])
# ⛔ 上面那段正文点名了几家券商。某一家本季没提供研报、列已经不出，
#    正文里那句还留着就是在讲一个纸上不存在的东西 —— 炸掉，让写正文的人改那句。
_named_houses = {h for h in {c['house'] for c in _bc_all}
                 if any(h in x for x, _bo in PARTS[-1][1])}
_ghost = sorted(_named_houses - {c['house'] for c in _bc})
if _ghost:
    raise SystemExit(f'✗ §6.1 正文点名了 {_ghost}，但这几家本季没提供研报、表上已经没有这一列'
                     f'\n   ⛔ 把那句话改掉再出稿 —— 不许留着讲一个纸上不存在的券商')

tbl('sent_broker_summary',
    ['', *[f'{c["house"]}\n({c["reports"]})' for c in _bc]],
    [['View'] + [c['view'] for c in _bc],
     ['Key points'] + ['\n'.join('· ' + p for p in c['points']) for c in _bc],
     ['QoQ change'] + [c['qoq'] for c in _bc]],
    widths=[1.9] + [round((17.1 - 1.9) / len(_bc), 2)] * len(_bc),
    bold_first=True)

sub('6.2  Related news')
_W = {w['id']: w for w in META['web_research']['items']}
_bd = _W['bdc_redemptions']['figures']
# 键名带季度 —— 从 meta.periods 拼，别写字面量（下季会 KeyError，正好当哨兵）
_bd_act = _bd[f'{PER["market_pq"]}_actual_pct_of_shares']
_bd_fc = _bd[f'{PER["market_cq"]}_bofa_forecast_pct']
_fs = _W['fsb_vulnerabilities']['figures']
bltlink([b('Redemption requests were expected to peak this quarter. '),
         t('BofA analysis via PitchBook put first-quarter requests at '),
         b(f'{_bd_act["Blackstone BCRED"]}%'),
         t(' of shares outstanding at Blackstone’s BCRED, '),
         b(f'{_bd_act["Apollo Debt Solutions"]}%'),
         t(' at Apollo Debt Solutions and '),
         b(f'{_bd_act["Blue Owl OTIC"]}%'),
         t(' at Blue Owl’s OTIC, with second-quarter peaks forecast at '),
         b(f'{_bd_fc["Blackstone BCRED"]}%'), t(', '),
         b(f'{_bd_fc["Apollo Debt Solutions"]}%'), t(' and '),
         b(f'{_bd_fc["Blue Owl OTIC"]}%'),
         t(' respectively — against typical caps of '),
         b(f'{_bd["typical_quarterly_redemption_cap_pct"]}%'),
         t('. Why it matters: at several times the cap the gate holds but the queue rolls forward, '
           'so pressure is deferred, not resolved — and it lands on the non-traded vehicles '
           + xr('5.5') + ' shows with the cleanest non-accruals. Second-quarter figures '
           'are forecasts. '),
         t('Source: ')],
        _W['bdc_redemptions']['url'],
        f'PitchBook (LCD), {_W["bdc_redemptions"]["date"]}')
bltlink([b('The FSB put an official number on the leverage gap — and it matches ours. '),
         t('The FSB’s May report sizes private credit at '),
         b(f'US${_fs["market_size_usd_tn"].split()[0]}tn'),
         t(' (US about US$1tn) and borrower leverage of '),
         b(f'{_fs["borrower_leverage_x"].split()[0]}x debt/EBITDA'),
         t(' against roughly 4x for leveraged loans. It separates outright defaults of '),
         b(f'{_fs["outright_default_pct"]}%'), t(' from a measure including restructurings of '),
         b(f'{_fs["incl_selective_default_pct"]}%'), t('. Bank lines to these funds total '),
         b(f'US${_fs["bank_lines_to_pc_funds_usd_bn"]}bn'), t('; roughly '),
         b(f'{_fs["life_insurer_pc_share_pct"]}%'),
         t(' of life insurer portfolios may be private credit. '
           'Why it matters: an independent official source lands on our own exhibits — its leverage '
           'range brackets our 5.7x direct lending against 4.0x syndicated. '),
         t('Source: ')],
        _W['fsb_vulnerabilities']['url'],
        f'Financial Stability Board, {_W["fsb_vulnerabilities"]["date"]}')
blt([b('Banks are competing for the same borrowers again. '),
     t('Barclays reports private credit lenders seeing more competition from banks, corroborated '
       'by bank management commentary and by the SLOOS showing banks eased some C&I terms. '
       'Why it matters: it compresses spreads where private credit’s premium is thinnest (the upper '
       'middle market), and arrives alongside the cov-lite and PIK loosening in '
       + xr('4.2') + '. '),
     t('Source: Barclays, ‘Business Development Companies: Early Themes and Trends from 2Q '
       'Reporting’ (this quarter’s Broker folder); Federal Reserve Senior Loan Officer Opinion '
       f'Survey, {PER["market_cq"]}.')])
blt([b('BDCs started financing hyperscalers. '),
     t('Barclays notes some BDCs are now investing in hyperscaler financings — a new asset type for '
       'vehicles built around sponsor-backed middle-market loans. Why it matters: it expands the '
       'asset class but also imports a different risk profile (concentration, long build cycles, '
       'single-counterparty exposure) into portfolios that investors underwrote as diversified '
       'middle-market credit. Worth asking our managers directly whether they are participating. '),
     t('Source: Barclays, ‘Business Development Companies: Early Themes and Trends from 2Q '
       'Reporting’ (this quarter’s Broker folder).')])
blt([b('The default measurement problem got worse, not better. '),
     t('Five providers now publish private credit default rates and this quarter they ranged from '),
     b('1.6% to 5.7%'),
     t(' for nominally the same asset class, two up and three down. Fitch turned back up in April. '
       'Why it matters: with no agreed denominator any single default statistic can support either '
       'narrative — so this report shows the provider table, not a house number, and weights '
       'BDC-level disclosure above headline default rates. '),
     t('Source: {{ex:cf_provider_compare_table}} of this report, which compiles the five providers’ '
       'own published definitions and rates; Fitch monthly private-credit default update.')])


# ═══════════════════════════ 8. Fund Update ═══════════════════════════
sec('Fund Update')
_af = META['as_of']['fund']['quarter']
_am = META['as_of']['market']['quarter']
para([
    t('This section is based on each manager’s latest investor report: PAG BRS Fund III and '
      'Guggenheim Private Debt Fund IV for '), b(_af), t(', and HSBC RCF Partnership Fund for '),
    b(_af), t(' (reported under the name RCF Capital Solutions Fund). '),
    b('All valuations are as of 31 March 2026 and therefore predate the '), b(_am),
    b(' market data discussed above'), t(' — the spread widening in ' + xr('3.2') + ', the '
      'April–August broker commentary in ' + xr('6') + ' and the BDC redemption figures in '
      + xr('6.2') + ' are all '
      'subsequent to these marks. Where this section reports a fund-level return, read it as a '
      'first-quarter valuation, not as a current one.'),
])

# ═════════ §8 每只基金的 Fund snapshot（三段结构的第一段）═════════
# ⛔ Alex 2026-08-25：「Fund Update 其中有三个 fund，每个 fund 下面的结构都要是一样的，
#    要包含 Fund snapshot、Portfolio composition、Fund level performance detail」
# ⛔ Alex 2026-08-26：「Portfolio composition 也没了，Fund level performance detail 也没有，
#    你这一部分看一下同事的结构」—— 同事那版三只基金各是
#      <Fund name> (<strategy>)           12.5pt
#        Fund snapshot                    10.5pt  ← 静态事实表
#        Portfolio composition            10.5pt  ← 并排组合图 + QoQ 表
#        Fund level performance detail    10.5pt  ← KPI 表 + 明细表
#    段名、段序三只完全一致，缺料写 not disclosed，段不许省。
#    我们这版在 Fund snapshot 里多一张 `Metric | <pq> | <cq> | QoQ Δ` 表 +
#    两条固定 bullet —— 那是 Alex 8-25 明确要求的（「两张表 + 两条 bullet」）。
def fund_snapshot(fkey):
    """fkey: 'pag' / 'gug' / 'hsbc'。两张表从账本读，一个字都不在这里写死。"""
    _a = E[f'fund_{fkey}_snapshot']
    _b = E[f'fund_{fkey}_snapshot_qoq']
    minor('Fund snapshot')
    # ⛔ 两张表**横向并排**（外层无框线 1×2），左表**没有表头行** —— 同事那版就是这个格式，
    #    Alex 2026-08-26 点名纠正过一次（「是两个分开的的横向排放的表」）。
    #    左表六行行名固定、右表表头固定，只有两个季度标签跟着 periods 变。
    # ⛔ Alex 2026-08-26：「Guggenheim / HSBC 的 Fund snapshot 的左边的表格的最左侧一列
    #    还是不对，你对照一下同事的，然后固定。」表A 的行名**三只基金各一套** ——
    #    原来共用 PAG 那六行，所以 GUG / HSBC 纸上全错而所有检查都绿。
    _arow = _fixcol(f'fund_{fkey}_snapshot',
                    [[r['label'], r['value']] for r in _a['rows']])
    _brow = _fixcol(f'fund_{fkey}_snapshot_qoq',
                    [[r['label'], r['pq'], r['cq'], r['delta']] for r in _b['rows']])
    PARTS.append(('tblpair', (
        (None, _arow, _a['col_widths_cm']['widths']),
        (_b['header'], _brow, _b['col_widths_cm']['widths']))))
    for _k, _lb in (('quarter_activity', 'Quarter activity. '),
                    ('manager_commentary', 'Manager commentary. ')):
        _v = _a.get(_k) or _b.get(_k)
        if not _v:
            raise SystemExit(f'✗ fund_{fkey}_snapshot 缺固定 bullet `{_k}` —— '
                             f'没内容也要写 none this quarter（report-spec §8）')
        _txt = str(_v).strip()
        blt([b(_lb), t(_txt[0].upper() + _txt[1:] + ('' if _txt.endswith('.') else '.'))])

sub('8.1  ' + g('fund_pag_snapshot', 'fund_name'))
_pk = {r['label']: r for r in g('fund_pag_kpi_qoq', 'rows')}
_pt = g('fund_pag_top10', 'rows')
para([
    t('PAG BRS Fund III is a specialty risk-transfer strategy with '),
    b('US$' + _pk['Capital commitments (US$m)']['cq'] + 'm'), t(' of commitments, of which '),
    b(_pk['Capital contributions (US$m / %)']['cq'].split(' / ')[1]), t(' has been contributed. '
      'Net IRR eased to '), b(_pk['Net IRR']['cq']), t(' from '), b(_pk['Net IRR']['pq']),
    t(' while net MOIC rose to '), b(_pk['Net MOIC (TVPI)']['cq']), t(' from '),
    b(_pk['Net MOIC (TVPI)']['pq']), t(' and DPI advanced to '), b(_pk['DPI']['cq']),
    t(' from '), b(_pk['DPI']['pq']), t('. The IRR decline alongside a rising multiple is the '
      'signature of a fund lengthening its holding period rather than losing money: distributions '
      'grew to '), b('US$' + _pk['Distributions (US$m)']['cq'] + 'm'), t(' from '),
    b('US$' + _pk['Distributions (US$m)']['pq'] + 'm'), t(', of which '),
    b('US$' + _pk['  of which recallable (US$m)']['cq'] + 'm'), t(' is recallable — so a majority of '
      'the DPI improvement can be called back and is not permanent return of capital. '
      'NAV fell to '), b('US$' + _pk['NAV (US$m)']['cq'] + 'm'), t(' from '),
    b('US$' + _pk['NAV (US$m)']['pq'] + 'm'), t(' as one further investment exited (three of twenty '
      'now realised).'),
])
fund_snapshot('pag')
minor('Portfolio composition')
para([
    t('Composition is unchanged from the prior quarter in all four cuts — a direct consequence of '
      'making no new investments. Subscription line finance is '),
    b(f'{g("fund_pag_comp_type","vals")[0]}%'), t(' of invested amount, large-corporate revolvers '
      'and term loans '), b(f'{g("fund_pag_comp_type","vals")[1]}%'), t(' and secured SME '),
    b(f'{g("fund_pag_comp_type","vals")[2]}%'), t('. Geographically '),
    b(f'{g("fund_pag_comp_geo","vals")[0]}%'), t(' sits in fund domiciles and '),
    b(f'{g("fund_pag_comp_geo","vals")[1]}%'), t(' in Western Europe, with only '),
    b(f'{g("fund_pag_comp_geo","vals")[2]}%'), t(' in North America — so this holding is '
      'structurally uncorrelated with the US middle-market stress that dominates '
      + xr('3') + ' through ' + xr('5') + '. '
      'Currency is '), b(f'{g("fund_pag_comp_ccy","vals")[0]}% USD'), t(', '),
    b(f'{g("fund_pag_comp_ccy","vals")[1]}% EUR'), t(' and '),
    b(f'{g("fund_pag_comp_ccy","vals")[2]}% GBP'), t('. Counterparty concentration is the exposure '
      'worth monitoring: the largest bank counterparty is '),
    b(f'{g("fund_pag_comp_bank","vals")[0]}%'), t(' of invested amount, the top three '),
    b(f'{sum(g("fund_pag_comp_bank","vals")[:3])}%'), t(' and the top five '),
    b(f'{sum(g("fund_pag_comp_bank","vals")[:5])}%'), t('. The fund does not disclose which banks '
      'these are, so we cannot assess correlation between them.'),
])
expair('fund_pag_comp_type', 'fund_pag_comp_geo')
expair('fund_pag_comp_ccy', 'fund_pag_comp_bank')
# ⛔ E36 是**八列双栏**（同事那版如此）：左栏 By portfolio type 逐档、右栏 By currency 逐档，
#    各带上季/本季/QoQ Δ。表头与两栏行名一律从账本读，⛔ 不许在这里写字面量 ——
#    上一版这里写的是四列摘要，跟账本冻结的八列表头完全不是一回事（Alex 2026-08-26 点名）。
def _panel_rows(slug_l, slug_r):
    _L, _R = E[slug_l], E[slug_r]

    def _cells(ent, i):
        if i >= len(ent['labels']):
            return ['', '', '', '']
        _c, _p = ent['vals'][i], ent['vals_pq'][i]
        _d = _c - _p
        return [ent['labels'][i], f'{_p:.0f}%', f'{_c:.0f}%',
                ('0.0pp' if _d == 0 else f'{_d:+.0f}pp')]
    _n = max(len(_L['labels']), len(_R['labels']))
    return [_cells(_L, i) + _cells(_R, i) for i in range(_n)]


tbl('fund_pag_comp_qoq', g('fund_pag_comp_qoq', 'header'),
    _panel_rows('fund_pag_comp_type', 'fund_pag_comp_ccy'),
    widths=[3.4, 1.15, 1.15, 1.25, 2.5, 1.15, 1.15, 1.25])
minor('Fund level performance detail')
# ⛔ E37 三列（`Metric | <cq> | <pq>`，本季在前 —— 同事那版就是这个顺序），
#    最左列九行照同事那版（gross/net 合成一行）。行名与合成规则落在账本
#    row_labels_fixed，⛔ 不许在这里写字面量。上一版多印了一个季度列、行名也是自己拆的。
_pkr = {r['label']: r for r in g('fund_pag_kpi_qoq', 'rows')}


def _kpi(spec, q):
    # spec['from'] 用 '||' 分隔要合成的账本行名，合出来用 ' / ' 连接
    _ks = [x.strip() for x in spec['from'].split('||')]
    _vs = [(_pkr[k][q] if k in _pkr else '—') for k in _ks]
    return ' / '.join(_vs) if len(_vs) > 1 else _vs[0]


tbl('fund_pag_kpi_qoq', g('fund_pag_kpi_qoq', 'header'),
    [[sp['label'], _kpi(sp, 'cq'), _kpi(sp, 'pq')]
     for sp in g('fund_pag_kpi_qoq', 'row_labels_fixed')['rows']],
    widths=[8.6, 4.2, 4.2])
# ⛔ E38 九列，表头与最左那十个项目名都从账本读（Alex 2026-08-26:「Exhibit 38 还不改」）。
#    末两列 UW IRR / Expected IRR 是本季从 PAG 1Q26 第 9 页 Current Investments 表抽的明值。
tbl('fund_pag_top10', g('fund_pag_top10', 'header'),
    _fixcol('fund_pag_top10',
            [[r['label'], r['invest_date'], r['portfolio_type'], r['currency'], r['spread'],
              f'{r["amount_usdm"]:,.1f}', f'{r["total_value_usdm"]:,.1f}',
              r['uw_irr'], r['expected_irr']] for r in _pt]),
    widths=g('fund_pag_top10', 'col_widths_cm', 'widths'), fixed_cols=True)


sub('8.2  ' + g('fund_gug_snapshot', 'fund_name'))
_gk = {r['label']: r for r in g('fund_gug_comp_qoq', 'rows')}
_gd = g('fund_gug_closed_deals', 'rows')
_gg = g('fund_gug_gics_mix', 'all_slices')
para([
    t('Guggenheim PDF IV is a US direct lending strategy reported on an aggregate basis across '
      'three vehicles. The book grew to '), b(_gk['Total investments (no.)']['cq']),
    t(' investments and '), b('US$' + _gk['Invested capital (US$m)']['cq'] + 'm'),
    t(' of invested capital from '), b(_gk['Total investments (no.)']['pq']), t(' and '),
    b('US$' + _gk['Invested capital (US$m)']['pq'] + 'm'), t('. Leverage was unchanged at '),
    b(_gk['Leverage (x)']['cq']),
    t(_dirword(_gk['LTV (%)']['delta'], ' and LTV {} {} to ')), b(_gk['LTV (%)']['cq']), t('. '),
    b('The fund does not disclose fund-level IRR, TVPI, DPI or NAV in its quarterly report'),
    t(' — we searched both this quarter’s and last quarter’s reports and there are no return '
      'metrics of any kind. We therefore assess this holding here on asset-level status and '
      'portfolio construction; the return figures shown for Guggenheim in '
      + xr('9') + ' (marked †) '
      'are Junson’s internal calculations from the manager’s internal investor reporting.'),
])
fund_snapshot('gug')
minor('Portfolio composition')
para([
    t('The portfolio is diversified across '), b(f'{len(_gg)}'), t(' GICS sub-industries, with '),
    b(f'{_gg[0][0]} at {_gg[0][1]}%'), t(', '), b(f'{_gg[1][0]} at {_gg[1][1]}%'), t(' and '),
    b(f'{_gg[2][0]} at {_gg[2][1]}%'), t(' the largest. Combining the two software lines gives '),
    b(f'{_gg[0][1] + [v for k, v in _gg if k == "Application Software"][0]}%'),
    t(' of par in software — the highest single-sector concentration in the book and the exposure '
      'most directly in the path of the AI-disruption thesis in ' + xr('5.1') + '. '),
    b(f'{g("fund_gug_sponsored","vals")[0]}%'),
    t(' of NAV is sponsor-backed, ' + _ppmove('fund_gug_sponsored', 0) + ' on the quarter. '),
    b('One basis caveat: '), t('the GICS mix is reported as a share of par this quarter but as a '
      'share of NAV last quarter, so the two are not directly comparable and we do not show a '
      'quarter-on-quarter delta for the sector lines.'),
])
expair('fund_gug_gics_mix', 'fund_gug_sponsored')
# ⛔ E41 是**八列双栏**（同事那版如此）：左栏 GICS 子行业（Software 合并行 + 两条缩进分项）、
#    右栏 sponsored 拆分，各带上季 / 本季 / QoQ Δ。表头、两栏行名、列宽一律从账本读 ——
#    上一版这里印的是四列的 account overview 摘要，跟账本冻结的八列表头完全不是一回事
#    （Alex 2026-08-26 点名:「Exhibit 41 也是 …… 表格的表头和最左侧一列 要跟同事的一模一样」）。
#    account overview 那组数没删，仍在账本 rows 里喂上面那段正文（见 _rows_role）。
tbl('fund_gug_comp_qoq', g('fund_gug_comp_qoq', 'header'),
    _twopanel('fund_gug_comp_qoq'),
    widths=g('fund_gug_comp_qoq', 'col_widths_cm', 'widths'), fixed_cols=True)
minor('Fund level performance detail')
# ⛔ E42 六列，表头从账本读（同事那版：Deal | Structure | Pricing | Net leverage | LTV |
#    Differentiator）。上一版自己加了一列 Business、还把 Pricing 和 Leverage 调了序 ——
#    Alex 2026-08-25 就说过 E42 表头要跟同事一样。业务描述并进 Deal 一格（换行），不丢内容。
tbl('fund_gug_closed_deals', g('fund_gug_closed_deals', 'header'),
    [[d['row_label'], d['structure'], d['pricing'],
      d['net_leverage'], d['ltv'], d['differentiator']] for d in _gd],
    widths=[4.3, 3.4, 2.6, 1.9, 1.1, 3.8])


sub('8.3  ' + g('fund_hsbc_snapshot', 'fund_name'))
_hk = {r['label']: r for r in g('fund_hsbc_comp_qoq', 'aux', 'fund_kpi_qoq', 'rows')}
_hp = g('fund_hsbc_portfolio', 'rows')
_hs = g('fund_hsbc_sector', 'labels'), g('fund_hsbc_sector', 'vals')
para([
    t('The HSBC RCF fund invests in revolving credit facilities to sponsor-backed European '
      'borrowers. Fund size grew to '), b('EUR ' + _hk['Fund size (EURm)']['cq'] + 'm'),
    t(' on '), b('EUR 66m'), t(' of new commitments and holdings rose to '),
    b(_hk['Number of investments held']['cq']), t(' from '),
    b(_hk['Number of investments held']['pq']), t('. Reported IRR rose to '),
    b(_hk['IRR (post fee, pre carry)']['cq']), t(' from '),
    b(_hk['IRR (post fee, pre carry)']['pq']), t(', TVPI eased to '), b(_hk['TVPI']['cq']),
    t(' from '), b(_hk['TVPI']['pq']), t(' and DPI fell to '), b(_hk['DPI']['cq']), t(' from '),
    b(_hk['DPI']['pq']), t('. '),
    b('None of these ratios should be read as performance yet. '),
    t('Capital called is '), b('EUR ' + _hk['Capital called (EURm)']['cq'] + 'm'),
    t(' against a '), b('EUR ' + _hk['Fund size (EURm)']['cq'] + 'm'), t(' fund, and average '
      'utilisation across settled RCF commitments is '),
    b(_hk['Average utilisation of RCF commitments']['cq']), t(' — this is a fund in ramp-up. '
      'The DPI decline in particular is arithmetic, not deterioration: cumulative income '
      'distributions were unchanged at '),
    b('EUR ' + _hk['Total income distributions (EURm)']['cq'] + 'm'), t(' while paid-in capital rose '
      'from EUR ' + _hk['Capital called (EURm)']['pq'] + 'm to EUR ' +
      _hk['Capital called (EURm)']['cq'] + 'm, so the same numerator over a larger denominator gives '
      'a smaller ratio.'),
])
fund_snapshot('hsbc')
minor('Portfolio composition')
para([
    t('By RCF commitment the book is spread across '), b(f'{len(_hs[0])}'), t(' sectors, with '),
    b(f'{_hs[0][0]} and {_hs[0][1]}'), t(' the largest at '), b(f'{_hs[1][0]}%'),
    t(' each, followed by '), b(f'{_hs[0][2]} at {_hs[1][2]}%'), t('. '
      'Pricing is tight relative to direct lending: the commitment-weighted average margin across '
      'the nine settled investments is '),
    b(f'{g("fund_hsbc_margin","weighted_avg_bps"):.1f}bp'), t(' over the base rate, ranging from '),
    b(f'{min(g("fund_hsbc_margin","vals")):.0f}bp'), t(' to '),
    b(f'{max(g("fund_hsbc_margin","vals")):.0f}bp'), t('. That is roughly '),
    b(f'{g("fund_hsbc_margin","aux","inside_dl_spread_bps","value"):.0f}bp'),
    t(' inside the direct lending new-origination spread from ' + xr('3.2')
      + ' — appropriate for '
      'undrawn revolvers to sponsor-backed borrowers, but it means the return depends on '
      'commitment fees and utilisation rather than on drawn margin. Base rates differ by deal '
      '(SOFR, SONIA and EURIBOR all appear), so margins are comparable across the book but all-in '
      'yields are not.'),
])
expair('fund_hsbc_sector', 'fund_hsbc_margin')
_h45 = g('fund_hsbc_comp_qoq', 'rows')
_h45t = g('fund_hsbc_comp_qoq', 'total')
_hrow = []                                   # 基线那种两组并排的紧凑排法
_half = -(-len(_h45) // 2)
for _i in range(_half):
    _a = _h45[_i]
    _bb = _h45[_i + _half] if _i + _half < len(_h45) else None
    _hrow.append([_a['label'], str(_a['pq']), str(_a['cq']), _a['delta']] +
                 ([_bb['label'], str(_bb['pq']), str(_bb['cq']), _bb['delta']] if _bb else ['', '', '', '']))
_hrow.append([_h45t['label'], str(_h45t['pq']), str(_h45t['cq']), _h45t['delta'], '', '', '', ''])
tbl('fund_hsbc_comp_qoq',
    (['Sector', PER['fund_pq'], PER['fund_cq'], 'QoQ Δ'] * 2),
    _hrow, widths=[2.9, 1.1, 1.1, 1.1, 2.9, 1.1, 1.1, 1.1])
minor('Fund level performance detail')
# ⛔ E46 九列，同事那版的列序（Alex 2026-08-26:「同事的 E46 里有 base 这一列？表头顺序都给我
#    定死，以及最左边的这一列」）—— **没有 Base 列**，base rate 并进 Margin 一格（SOF+350）；
#    Status 换成 Drawn (€m) / Est. ROIC / Watchlist 三列（RCF Q1 2026 第 10 页明值）。
tbl('fund_hsbc_portfolio', g('fund_hsbc_portfolio', 'header'),
    _fixcol('fund_hsbc_portfolio',
            [[r['label'], r['sector'], r['country'], r['margin'],
              f'{r["commitment_eurm"]:.2f}', f'{r["drawn_eurm"]:.2f}',
              r['maturity'], r['est_roic'], r['watchlist']] for r in _hp]),
    widths=g('fund_hsbc_portfolio', 'col_widths_cm', 'widths'), fixed_cols=True)


# ══════════════════════ 9. Competitor Analysis ══════════════════════
sec('Competitor Analysis')
_scr = META['screen']
_coh = META['cohorts']
para([
    t('This section benchmarks the three holdings against vintage-matched cohorts drawn from a '
      'PitchBook screen of North American direct lending drawdown funds, exported '),
    b(_scr['export_date']), t(' and covering '), b(f'{_scr["universe_fund_count"]} funds'), t('. '
      'Percentile is defined as the share of cohort funds strictly below the fund’s value; cohort '
      'sizes differ by metric and are stated in each exhibit. '),
    b('One methodological point has to be made plainly: none of the three holdings is a constituent '
      'of this screen. '),
    t('PAG is Hong Kong based, HSBC RCF is a Luxembourg RAIF and Guggenheim PDF IV does not appear '
      'in the export — all three return zero matches. The percentiles therefore measure position '
      'against an external North American benchmark, not rank within a peer group the funds belong '
      'to, and PAG (Asia-focused) and HSBC (Europe-focused) carry a genuine geographic mismatch '
      'against it. We keep the screen unchanged for comparability with prior quarters and disclose '
      'the mismatch rather than widening the universe. Conventions are set out in the appendix.'),
])

sub('9.1  Positioning scorecard')
_sc = g('ca_scorecard', 'rows')
_pag = {r['metric']: r for r in _sc if r['fund'].startswith('PAG')}
_hsb = {r['metric']: r for r in _sc if r['fund'].startswith('HSBC')}
para([
    t('PAG screens strongly on IRR and weakly on multiple against its 2023 cohort: net IRR of '),
    b(_pag['Net IRR']['cq']), t(' puts it at the '), b(f'{_pag["Net IRR"]["percentile"]:.0f}th percentile'),
    t(f' of {_pag["Net IRR"]["cohort_n"]} funds (cohort median '),
    b(f'{_pag["Net IRR"]["cohort_median"]:.2f}%'), t('), while TVPI of '), b(_pag['TVPI']['cq']),
    t(' sits at only the '), b(f'{_pag["TVPI"]["percentile"]:.0f}th'), t(' against a median of '),
    b(f'{_pag["TVPI"]["cohort_median"]:.2f}x'), t('. That combination is a profile artefact rather '
      'than a contradiction: a specialty risk-transfer book with short-dated, self-liquidating '
      'exposures generates a high annualised return without ever accumulating a large multiple. '
      'DPI at '), b(_pag['DPI']['cq']), t(' ranks '), b(f'{_pag["DPI"]["percentile"]:.0f}th'),
    t(', consistent with that reading — though as noted under '
      + g('fund_pag_snapshot', 'fund_name') + ' the majority of those '
      'distributions are recallable.'),
])
para([
    t('HSBC screens at the top of its 2024 cohort on every metric — '),
    b(f'{_hsb["Net IRR"]["percentile"]:.0f}th percentile on IRR'), t(' and '),
    b(f'{_hsb["TVPI"]["percentile"]:.0f}th on TVPI'), t(' — and that is precisely why the reading '
      'should be discarded. With '), b('2.5% of the fund called'), t(' and average RCF utilisation of '),
    b('11.7%'), t(', an IRR of '), b(_hsb['Net IRR']['cq']), t(' is a ramp-up artefact computed on a '
      'very small denominator. The cohort itself is thin: '),
    b(f'{_hsb["TVPI"]["cohort_n"]} funds'), t(' for TVPI against '),
    b(f'{_pag["TVPI"]["cohort_n"]}'), t(' for the 2023 vintage. Guggenheim’s figures throughout '
      'this section (marked †) are Junson’s internal calculations from the manager’s internal '
      'investor reporting — its quarterly report discloses no return metrics — and its percentiles '
      'are recomputed by us from the PitchBook export: '), b('9.3%'), t(' net IRR sits at the '),
    b('18th percentile'), t(' of the 2024 cohort, while '), b('1.20x'), t(' TVPI screens top of a '
      'thin, young cohort where distributions barely differ.'),
])
# 表头九列，第三列是基准季标签 —— 从 header_template + meta.rq 现算，
# 不许读账本里 header 那份本季快照（下季 rq 变了、快照没变就会印出旧季度）。
_sch = [c.replace('<rq>', RQ) for c in g('ca_scorecard', 'header_template')]
_shist = g('ca_scorecard', 'history')
_sqs = sorted(q for q in _shist if len(str(q)) == 6 and str(q)[:4].isdigit())
_sprev = _sqs[-2] if len(_sqs) >= 2 else None


def _sdelta(r, field, unit='', dp=2):
    # 三个 delta 列：本季减 history 里上季那一条。没有上季记录才写 n/a。
    if not _sprev:
        return 'n/a'
    prev = (_shist.get(_sprev) or {}).get(f"{r['fund']} - {r['metric']}") \
        or (_shist.get(_sprev) or {}).get(f"{r['fund']} \u2014 {r['metric']}")
    if not prev or prev.get(field) is None:
        return 'n/a'
    cur = (r['cohort_median'] if field == 'cohort_median'
           else r['percentile'] if field == 'percentile' else _num(r['cq']))
    if cur is None:
        return 'n/a'
    return f'{cur - prev[field]:+.{dp}f}{unit}'


# ⛔ 最左格印账本的 row_label，不许在这里现拼 —— 与 E48 同一套做法
#    （Alex 2026-08-26:「E47 第一列也设置一下 让第一列每一行的字就只占一行，跟 E48 要求一样」）。
#    列宽同样从账本读并走 fixed 布局，否则 autofit 会把第一列的宽度分给别人。
_scw = g('ca_scorecard', 'col_widths_cm')
tbl('ca_scorecard', _sch,
    [[r['row_label'],
      r['metric'], r['cq'],
      _sdelta(r, 'value'),
      ('\u2014' if r['cohort_median'] is None else f'{r["cohort_median"]:.2f}'),
      _sdelta(r, 'cohort_median'),
      ('\u2014' if r['percentile'] is None else f'P{r["percentile"]:.0f}'),
      _sdelta(r, 'percentile', unit='pp', dp=0),
      r['read']] for r in _sc],
    widths=_scw['widths'], fixed_cols=bool(_scw.get('fixed')))

# ⛔ Alex 2026-08-26：「同事的报告里原来没有 .2 Named comparators 这一节，那你就别加上。
#    这一行删掉。」—— 同事那版 §9 只有 Positioning scorecard / Relative momentum /
#    Percentile trajectory / Cohort health monitor / Appendix 五节，E48 那张表是放在
#    Positioning scorecard 里的，没有单独的小标题。这里只删标题行，表和正文原位保留。
_nc = g('ca_named_comparators', 'rows')
_flag = [r for r in _nc if r.get('tier') != 'own fund']
para([
    t('The named comparators are the latest fund in each house’s flagship direct lending series, '
      'taken from the same screen. Across the seven, net IRR ranges from '),
    b(f'{min(r["net_irr"] for r in _flag if r["net_irr"] is not None):.1f}%'), t(' to '),
    b(f'{max(r["net_irr"] for r in _flag if r["net_irr"] is not None):.1f}%'),
    t(' — a 30-point spread that is mostly explained by vintage and deployment stage rather than '
      'by manager skill. The lowest reading, '),
    b('TPG Twin Brook Direct Lending Fund VI at −4.4%'), t(', is a 2025 vintage only 5% called and '
      'is marked with an asterisk for that reason; the highest, '),
    b('Ares Emerald at 27.3%'), t(', is a US$370m 2023-vintage vehicle rather than the '
      'US$8bn flagship, which is why we select on flagship series rather than on latest vintage. '
      'Junson’s own rows sit above the comparators and use different bases — size on commitments '
      'for PAG, in euro for HSBC, and called-percentage computed differently for each — so the '
      'columns are not strictly like-for-like across the panel.'),
])
# ⛔ E48 九列 + 两行灰底分组标题（Alex 2026-08-25）。表头与 tier 分组名都从账本读，
#    ⛔ 不许在这里写死 —— 下季基金集合会变，tier 名不会。
_nhdr = g('ca_named_comparators', 'header')
_ntiers = g('ca_named_comparators', 'tier_labels')
_EM = '\u2014'


def _q1(v):
    return _EM if v is None else str(v)[0] and ('Q' + str(v)[0] if str(v)[0].isdigit() else _EM)


_nrows, _ngrp = [], []
for _tier, _lab in _ntiers.items():
    _mem = [r for r in _nc if r.get('tier') == _tier]
    if not _mem:
        continue
    if _lab:                              # None = 不画分组标题（自家基金那组）
        _ngrp.append(len(_nrows))
        _nrows.append([_lab] + [''] * (len(_nhdr) - 1))
    for r in _mem:
        _nrows.append([
            # ⛔ 最左列印 `row_label` —— 逐格照同事那版的字面量（含 † / * 标记），
            #    不加 House 前缀、不用内部 `label`（Alex 2026-08-25:「最左侧那一列的所有东西都要一样」）
            r['row_label'],
            str(r['vintage']),
            _EM if r.get('size_usdm') is None else f'{r["size_usdm"]:,.0f}',
            _EM if r.get('net_irr') is None else f'{r["net_irr"]:.1f}%',
            _EM if r.get('tvpi') is None else f'{r["tvpi"]:.2f}x',
            _EM if r.get('dpi') is None else f'{r["dpi"]:.2f}x',
            _EM if r.get('called_pct') is None else f'{r["called_pct"]:.0f}%',
            _EM if r.get('dry_powder_pct') is None else f'{r["dry_powder_pct"]:.0f}%',
            _q1(r.get('pb_quartile')),
        ])
# ⛔ 列宽从账本读并走 fixed 布局 —— 第一列 4.4cm 是按最长 row_label 量出来的，
#    autofit 会把它抢走（详见账本 col_widths_cm._why）。不许在这里写死。
_ncw = g('ca_named_comparators', 'col_widths_cm')
tbl('ca_named_comparators', _nhdr, _nrows,
    widths=_ncw['widths'], fixed_cols=bool(_ncw.get('fixed')),
    group_rows=_ngrp, zebra='F2F5F9')


sub('9.2  Relative momentum and percentile trajectory')
para([
    t('This is the first quarter recorded in the ledger, so there is no prior percentile to compare '
      'against and no momentum to report. Exhibits for relative momentum therefore show levels '
      'against the cohort median rather than quarter-on-quarter change, and the trajectory charts '
      'carry a single point each. From next quarter both become genuine time series, built by '
      'appending to the ledger rather than recomputing — which is the point of holding the '
      'percentile history in '), b('series.json'), t(' rather than in the document.'),
])
expair('ca_momentum_irr', 'ca_momentum_tvpi')
expair('ca_traj_irr_pct', 'ca_traj_tvpi_pct')

sub('9.3  Cohort health monitor')
_ci = g('ca_cohort_iqr', 'labels')
_cirr = g('ca_cohort_iqr', 'series', 'IRR IQR (pp)')
_ctv = g('ca_cohort_iqr', 'series', 'TVPI IQR (x)')
_nb = g('ca_cohort_iqr', 'n_by_vintage')
para([
    t('Dispersion within a vintage is the earliest place industry stress shows up in fund marks, '
      'because managers revalue at different speeds. The IRR interquartile range across the '),
    b(f'{_ci[0]}–{_ci[-1]}'), t(' vintages runs from '), b(f'{min(_cirr):.2f}pp'), t(' to '),
    b(f'{max(_cirr):.2f}pp'), t(f', widest in {_ci[_cirr.index(max(_cirr))]}. For the two vintages '
      'that matter most to this portfolio, dispersion is '),
    b(f'{_cirr[_ci.index("2023")]:.2f}pp'), t(' for 2023 ('),
    b(f'n={_nb["2023"]["irr"]}'), t(') and '), b(f'{_cirr[_ci.index("2024")]:.2f}pp'),
    t(' for 2024 ('), b(f'n={_nb["2024"]["irr"]}'), t('). On TVPI the 2024 cohort is the tightest in '
      'the series at '), b(f'{_ctv[_ci.index("2024")]:.2f}x'), t(' — but that is a young-vintage '
      'effect, not stability: funds three quarters into deployment have not yet had time to diverge. '
      'The reading to watch is whether 2023 and 2024 dispersion widens over the next two quarters '
      'while the medians hold, which would indicate that some managers are marking the software and '
      'PIK exposure discussed in ' + xr('5') + ' and others are not.'),
])
ex1('ca_cohort_iqr')

sub('9.4  Appendix — peer universe and methodology')
_uv = g('ca_apx_universe', 'periods')
_un = g('ca_apx_universe', 'rhs_line', 'vals')
_us = g('ca_apx_universe', 'stacks', 'Aggregate fund size (US$m)')
_mg = g('ca_apx_mgr_consistency', 'points')
para([
    t('The screen’s vintage profile shows the asset class’s growth and its recent stall: fund '
      'formation peaked at '), b(f'{max(_un)} funds'), t(f' in {_uv[_un.index(max(_un))]} and has '
      'fallen to '), b(f'{_un[-2]}'), t(f' in {_uv[-2]}, while aggregate size peaked at '),
    b(f'US${max(_us)/1000:,.1f}bn'), t(f' in {_uv[_us.index(max(_us))]}. Note the two series do not '
      'share a denominator — size only aggregates funds that disclose it — so the ratio should not '
      'be read as average fund size. On manager consistency, '), b(f'{len(_mg)} managers'),
    t(' have at least four PitchBook-ranked funds; average quartile ranges from '),
    b(f'{min(m["avg_quartile"] for m in _mg):.2f}'), t(' to '),
    b(f'{max(m["avg_quartile"] for m in _mg):.2f}'), t(' and median net IRR from '),
    b(f'{min(m["median_irr"] for m in _mg):.1f}%'), t(' to '),
    b(f'{max(m["median_irr"] for m in _mg):.1f}%'), t('. The upward slope of that chart is '
      'definitional — PitchBook assigns quartiles on performance — so what it actually shows is the '
      'spread of median IRR within each quartile band and how many funds each record rests on. '
      'None of the three holdings appears, for the reason given at the top of this section.'),
])
ex1('ca_apx_universe')
ex1('ca_apx_mgr_consistency')
expair('ca_apx_irr_by_vintage', 'ca_apx_tvpi_by_vintage')
ex1('ca_apx_called_by_vintage')
_VE = {'PAG': META['vintage_convention_evidence']['PAG_BRS_III'].split('——')[0].replace('首笔投资','').strip(),
       'GUG': META['vintage_convention_evidence']['Guggenheim_PDF_IV'].split('——')[0].replace('首笔投资','').strip()}
para([
    b('Methodology. '), t('Peer universe: '), t(_scr['criteria_en']), t(' — the export lists 333 '
      'rows, of which 331 are funds. Vintage convention (Junson): holdings are assigned the year '
      f'of their first investment — PAG BRS III = 2023 (first investments {_VE["PAG"]}), Guggenheim '
      f'PDF IV = 2024 (first investments {_VE["GUG"]}), HSBC RCF = 2024 — consistent with PitchBook’s '
      'first-investment convention for the peer universe, so fund and cohort vintages are '
      'like-for-like. Percentile = share of cohort funds with the metric strictly below the '
      'fund’s value; cohort denominators vary by metric with disclosure coverage (2024 vintage: '
      'IRR n=11, TVPI and DPI n=8). None of the three holdings is itself a constituent of the '
      'screen — PAG invests primarily in Asia and HSBC RCF is a Luxembourg RAIF — so percentiles '
      'measure position against an external North American benchmark, not rank within the funds’ '
      'own pool. Quarterly process: the same screen is re-exported each quarter, cohort statistics '
      'are recomputed from the raw PitchBook columns on fresh marks — never carried forward — and '
      'every metric is diffed against the archived baseline; this quarter’s baseline was '
      'reconciled against an independently prepared snapshot across 36 cohort statistics with no '
      'discrepancies, and is archived in the data ledger (series.json) together with the '
      'percentile histories for next quarter’s delta. Metric basis: PAG and HSBC figures are '
      'fund-level as reported; Guggenheim PDF IV does not disclose fund-level performance, so we '
      f'use Junson-calculated, investor-level figures as of {PER["market_cq"]} (net IRR 9.3%, TVPI 1.20x, DPI '
      '0.18x), marked † — investor-level metrics reflect our subscription timing, fee drag and '
      'the J-curve of our own capital calls and therefore typically sit below fund-level '
      'equivalents, so †-marked readings are conservative. HSBC RCF’s IRR is marked * as ramp-up '
      'distorted: with only 2.5% of commitments called, a very small denominator inflates early '
      'IRR. This appendix is refreshed annually or on material change.'),
])

# ══════════════════════ 10. Closing disclaimer ══════════════════════
sec('Disclaimer')
PARTS.append(('disclaimer',
  'For internal research use only. Not investment advice and not for distribution outside Junson '
  'Capital. Except where marked as exact, as-labelled or as-disclosed values, intermediate points '
  'of time series in redrawn charts are digitised approximations read from the source charts and '
  'are shown for trend only; please refer to the original reports when citing. Fund-level figures '
  'are as reported by each manager and are valued as of 31 March 2026, which predates the market '
  'data in ' + xr('2') + ' through ' + xr('6') + '. Competitor percentiles measure position '
  'against an external North '
  'American benchmark of which none of the three holdings is a constituent. The full data ledger, '
  f'including a source reference for every figure in this report, is archived as '
  f'series.json alongside sources_ledger_{RQ}.md for next quarter’s delta computation.'))


# ═══════════════ 7. Things We Should Know（最后写，插到 §8 之前）═══════════════
_S7 = []
_save = PARTS
PARTS = _S7
sec('Things We Should Know')
para([
    t('Five observations we consider important after reading all of this quarter’s uploaded '
      'materials — points not covered by the framework sections above and directly relevant to the '
      'Junson portfolio:'),
])

_mw = g('tws_extra_exhibit', 'periods')
# 两个快照日的键名带月份 —— 取前后两个键，别写字面量
_mwk = list(g('tws_extra_exhibit', 'stacks'))
_d25 = g('tws_extra_exhibit', 'stacks', _mwk[0])
_m26 = g('tws_extra_exhibit', 'stacks', _mwk[-1])
blt([b('BDCs quietly termed out their own liabilities in a single quarter, and nobody is reporting it. '),
     t('Between December and March the 2026 maturity bucket in the BDC debt stack fell from '),
     b(f'US${_d25[0]:,.1f}bn'), t(' to '), b(f'US${_m26[0]:,.1f}bn'), t(f' ({_m26[0]/_d25[0]-1:+.0%}) '
       'and the 2027 bucket from '), b(f'US${_d25[1]:,.1f}bn'), t(' to '), b(f'US${_m26[1]:,.1f}bn'),
     t(', while the 2031–2033 bucket grew from '), b(f'US${_d25[5]:,.1f}bn'), t(' to '),
     b(f'US${_m26[5]:,.1f}bn'), t('. Every section above looks at the asset side of BDC balance '
       'sheets; this is the liability side, and it says two things at once — the refinancing window '
       'was open, and managers judged it worth using rather than waiting. '),
     b('Implication for Junson: '), t('the vehicles holding the credit we are indirectly exposed to '
       'have just bought themselves three to seven years of funding runway. That reduces the risk of '
       'a forced-seller dynamic transmitting from BDC liabilities into private credit marks, which '
       'is the channel we would otherwise worry about most given the redemption data in '
       + xr('6.2') + '. '
       'It is a genuine positive and it is not in any broker report we received.')])
PARTS.append(('expanel', ('tws_extra_exhibit',)))

_gg_soft = g('fund_gug_gics_mix', 'all_slices')
_soft_tot = sum(v for k, v in _gg_soft if 'Software' in k)
blt([b('The US software stress that dominates this report touches only one of our three holdings — '
       'and that one is concentrated in it. '),
     t('PAG has '), b(f'{g("fund_pag_comp_geo","vals")[2]}%'), t(' of invested amount in North '
       'America and HSBC is entirely European; both are bank-facing revolver and risk-transfer '
       'strategies with no software exposure to speak of. Guggenheim, by contrast, carries '),
     b(f'{_soft_tot}% of par in software'), t(' across systems and application software — its '
       'largest single-sector position. So the AI-disruption thesis in ' + xr('5.1')
       + ', the 2024 upper-middle-market cov-lite and PIK loosening in ' + xr('4.2')
       + ', and the software recovery data in ' + xr('5.2') + ' all converge on one holding '
       'rather than being spread across the book. '),
     b('Implication for Junson: '), t('the portfolio is more concentrated in this risk than a '
       'three-fund count suggests, and it is the fund that discloses no return metrics. We should '
       'request name-level detail on the software positions and their marks, since we cannot infer '
       'anything from a fund-level number that does not exist.')])

_pkr = {r['label']: r for r in g('fund_pag_kpi_qoq', 'rows')}
_rec = float(_pkr['  of which recallable (US$m)']['cq'])
_dist = float(_pkr['Distributions (US$m)']['cq'])
blt([b('DPI is overstating permanent capital return, and the disclosure to fix it already exists. '),
     t('PAG’s DPI improved from '), b(_pkr['DPI']['pq']), t(' to '), b(_pkr['DPI']['cq']),
     t(' on distributions of '), b(f'US${_dist:,.0f}m'), t(' — but '), b(f'US${_rec:,.0f}m'),
     t(f' of that, {_rec/_dist:.0%}, is recallable, and unpaid commitments rose accordingly. '
       'On a non-recallable basis the distribution was '),
     b(f'US${_dist-_rec:,.0f}m'), t('. The headline DPI is not wrong, but it measures cash that has '
       'left the fund rather than capital we have permanently got back, and the gap this quarter is '
       'more than two thirds. '),
     b('Implication for Junson: '), t('ask all three managers to split distributions into recallable '
       'and non-recallable in their standard reporting, and use the non-recallable series when '
       'comparing DPI across funds or against the cohort medians in ' + xr('9')
       + '. PAG discloses the '
       'split already; the other two do not.')])

_hkr = {r['label']: r for r in g('fund_hsbc_comp_qoq', 'aux', 'fund_kpi_qoq', 'rows')}
blt([b('Ratios computed on a barely-called fund are noise, and we are currently reporting them as '
       'signal. '),
     t('HSBC’s reported IRR of '), b(_hkr['IRR (post fee, pre carry)']['cq']), t(' sits on '),
     b('EUR ' + _hkr['Capital called (EURm)']['cq'] + 'm'), t(' of called capital against a '),
     b('EUR ' + _hkr['Fund size (EURm)']['cq'] + 'm'), t(' fund — '),
     b(f'{float(_hkr["Capital called (EURm)"]["cq"])/float(_hkr["Fund size (EURm)"]["cq"]):.1%}'),
     t(' called — and its DPI fell from '), b(_hkr['DPI']['pq']), t(' to '), b(_hkr['DPI']['cq']),
     t(' for no reason other than the denominator growing while distributions stayed flat at '),
     b('EUR ' + _hkr['Total income distributions (EURm)']['cq'] + 'm'),
     t('. ' + xr('9') + ' dutifully places it in the top percentile of its cohort on every '
       'metric, which '
       'is arithmetically correct and analytically meaningless. '),
     b('Implication for Junson: '), t('adopt a minimum-called threshold — 25% is the convention we '
       'would suggest — below which we record the metrics but do not rank them or act on them. '
       'Applied this quarter that suppresses HSBC’s percentiles and one of the seven named '
       'comparators (Twin Brook Fund VI, 5% called, −4.4% IRR).')])

blt([b('Most of what looks like manager skill in this quarter’s data is vintage or denominator, and '
       'one of our managers changed a denominator without saying so. '),
     t('Three examples from this report. Public BDC non-accruals run '),
     b(f'{_npb[-1]-_npv[-1]:.1f}pp'), t(' above private, which reads as better private underwriting '
       'until Morgan Stanley’s vintage-controlled cut reverses the ranking. The seven named '
       'comparators span '),
     b(f'{min(r["net_irr"] for r in _flag if r["net_irr"] is not None):.1f}% to '
       f'{max(r["net_irr"] for r in _flag if r["net_irr"] is not None):.1f}%'),
     t(' on net IRR, driven mostly by vintage and deployment stage. And Guggenheim reported its '
       'sector mix as a share of par this quarter having used a share of NAV last quarter — had we '
       'computed a quarter-on-quarter sector delta without checking, we would have reported '
       'portfolio shifts that did not happen. '),
     b('Implication for Junson: '), t('require vintage splits with every manager report, and verify '
       'the denominator of every disclosed percentage before computing any change over time. We have '
       'added a basis-change field to the data ledger so that a switch like Guggenheim’s is recorded '
       'the quarter it happens rather than discovered a year later.')])

PARTS = _save
_i8 = next(i for i, (k, v) in enumerate(PARTS) if k == 'sec' and v == 'Fund Update')
PARTS[_i8:_i8] = _S7


# ── 本季没提供研报的券商：表上已经不出这一列，交付说明要写 ──────────────
if DROPPED_HOUSES:
    print(f'\n  ⚠ §6.1 券商表少了 {len(DROPPED_HOUSES)} 家（本季文件夹里没有它们的研报）：')
    for _h, _fl in DROPPED_HOUSES:
        print(f'      {_h} —— 上季用的是 {_fl}')
    print('      → 表上这几列已经不出。交付说明里必须写「X 家本季未提供」，'
          '⛔ 不许静默少一列。')

# ── 本季没披露的格子：统一报告，并检查有没有写 gap 说明 ────────────────
if GAPS:
    print(f'\n  ⚠ 本季有 {len(GAPS)} 格源报告没披露（已印 n/d，QoQ Δ 印 n/a）：')
    _nogap = []
    for _sl, _lb, _why in GAPS:
        print(f'      {_sl} · {_lb} —— {_why}')
        if not (E[_sl].get('_gap_note') or E[_sl].get('history_gaps')):
            _nogap.append(_sl)
    if _nogap:
        raise SystemExit(f'✗ 这些 exhibit 有 n/d 的格子但账本里没写 gap 说明：'
                         f'{sorted(set(_nogap))}\n'
                         f'   ⛔ 缺数可以，静默不行 —— 在账本写 _gap_note 说清'
                         f'「哪个数、源报告哪一页没给、下季去哪儿看」')

# ── 数据性行名跨季变动：统一报告，不当错误 ─────────────────────────────
if ROWDIFF:
    print('\n  ⚠ 这些表的行集跟上季不同（数据性行名，正常）—— 逐张确认过再交稿：')
    for _sl, _oq, _out, _in in ROWDIFF:
        print(f'      {_sl}（快照是 {_oq} 的）')
        if _out:
            print(f'        退出/不再出现：{_out}')
        if _in:
            print(f'        本季新增：{_in}')
    print('      → 确认无误后把 row_labels_fixed.expected 与 _rq 更新到本季，'
          '否则下季还会再报一遍')


# ── SEC 与实际印出来的标题必须一一对上 ────────────────────────────────
# ⛔ 正文的交叉引用（xr()）写的是节名。如果哪天改了标题却忘了改 SEC，
#    正文就会引用一个纸上不存在的名字 —— 读者 Ctrl-F 找不到，而且没人会发现。
#    所以在渲染之前对一遍：SEC 里的每个名字都必须真的被 sec()/sub() 印出去过。
_sec_miss = sorted(v for v in SEC.values() if v not in _SEEN_HEADINGS)
if _sec_miss:
    raise SystemExit(f'✗ SEC 里这些节名纸上没有对应标题：{_sec_miss}\n'
                     f'   正文用 xr() 引用它们就会指向一个不存在的名字。'
                     f'   改了标题就要同步改 SEC（那是唯一真值）。')
_sub_extra = sorted(h for h in _SEEN_HEADINGS
                    if h not in set(SEC.values())
                    and h not in ('Fund snapshot', 'Portfolio composition',
                                  'Fund level performance detail')
                    # §8 三只基金的小节名从账本 fund_name 读，正文也直接引账本，
                    # 不走 SEC —— 不算「引用不到」
                    and h not in {g(f'fund_{k}_snapshot', 'fund_name')
                                  for k in ('pag', 'gug', 'hsbc')})
if _sub_extra:
    print(f'  · 有标题不在 SEC 里（正文引用不到它们）：{_sub_extra}')


# ═════════════════════════ 渲染成 docx ═════════════════════════
def render():
    doc = H.new_report_doc(RQ, DATE)
    used = []
    for kind, payload in PARTS:
        if kind == 'sec':
            H.section_heading(doc, payload)
        elif kind == 'minor':
            H.minorheading(doc, payload)
        elif kind == 'tblpair':
            H.table_pair(doc, payload[0], payload[1])
        elif kind == 'tblp':
            _lb, _hd, _rw, _wd, _bf, _nt, _fx = payload
            H.plain_table(doc, _lb, _hd, _rw, note=_nt, col_widths_cm=_wd,
                          bold_first_col=_bf, fixed_cols=_fx)
        elif kind == 'sub':
            H.subheading(doc, payload)
        elif kind == 'body':
            H.body(doc, [(exhibits.resolve(x), bo)
                         for x, bo in _bold_policy(payload, 'body')])
        elif kind == 'bullet':
            H.bullet(doc, [(exhibits.resolve(x), bo)
                           for x, bo in _bold_policy(payload, 'bullet')])
        elif kind == 'bulletlink':
            parts, url, ltext = payload
            p = H.bullet(doc, [(exhibits.resolve(x), bo)
                               for x, bo in _bold_policy(parts, 'bullet')])
            H.hyperlink(p, url, ltext, size=9.5)
        elif kind == 'expanel':
            slug, = payload
            sp = E[slug]['side_panel']
            H.exhibit_with_panel(doc, cap(slug), f'charts/{slug}.png',
                                 sp['title'],
                                 [exhibits.resolve(b['text']) for b in sp['bullets']],
                                 note=note_of(slug))
            used.append(slug)
        elif kind == 'ex':
            slug, kw = payload
            kw = dict(kw)
            _wcm = kw.pop('_width_cm', None)
            H.exhibit(doc, cap(slug, **kw), f'charts/{slug}.png',
                      note=note_of(slug),
                      **({'width_cm': _wcm} if _wcm else {}))
            used.append(slug)
        elif kind == 'expair':
            l, r = payload
            L = (cap(l), f'charts/{l}.png', note_of(l))
            R = (cap(r), f'charts/{r}.png', note_of(r)) if r else ('', None, '')
            H.exhibit_pair(doc, L, R)
            used.append(l)
            if r:
                used.append(r)
        elif kind == 'tbl':
            slug, header, rows, widths, boldfirst, grp, zeb, fixw = payload
            H._caption(doc, cap(slug))
            H.data_table(doc, header, rows, col_widths_cm=widths, bold_first_col=boldfirst,
                         group_rows=grp, zebra=zeb, fixed_cols=fixw)
            H._note(doc, note_of(slug))
            used.append(slug)
        elif kind == 'disclaimer':
            H.disclaimer(doc, payload)
        elif kind == 'pb':
            doc.add_page_break()
    os.makedirs('out', exist_ok=True)
    doc.save(OUT)
    return used


if __name__ == '__main__':
    used = render()
    all_slugs = [r['slug'] for r in EX]
    missing = [s for s in all_slugs if s not in used]
    dup = [s for s in set(used) if used.count(s) > 1]
    print(f'[written] {OUT}')
    print(f'  放进文档的 exhibit：{len(used)} / {len(all_slugs)}')
    if missing:
        print(f'  ⚠ 漏了 {len(missing)} 个：{missing}')
    if dup:
        print(f'  ⚠ 重复放了：{dup}')
