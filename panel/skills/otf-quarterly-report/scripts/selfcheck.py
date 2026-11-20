#!/usr/bin/env python3
"""§8 出图后自检。每季出图后跑一次，FAIL 就不许交付。"""
import json, os, re, glob, sys, collections
import matplotlib; matplotlib.use('Agg')
import matplotlib.text
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import chartlib as C, build_charts as B

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, 'series.json'))); M = S['meta']; CH = S['charts']
CQ, PQ, TRK, AS_OF = M['cq'], M['pq'], M['tracker'], M['as_of']
fail, warn = [], []

# 抓每张图实际画上去的文字
TX = {}
_orig = C.save
def cap(fig, path, kind='A'):
    fig.canvas.draw()
    fb = fig.bbox
    # 各轴的实际显示区间：locator 会生成越界刻度对象（如 ylim 0 起却造出 -0.5），
    # 它们不会画出来，得先滤掉，否则会被误判成"用 hyphen 当负号"
    # locator 会生成越界刻度对象（如 ylim 从 0 起却造出 -0.5），它们不会画出来，
    # 得按各自所属的那根轴的显示区间逐个滤掉，否则会被误判成"用 hyphen 当负号"
    ticklab = {}
    for ax in fig.axes:
        for t in ax.get_xticklabels():
            ticklab[id(t)] = ax.get_xlim()
        for t in ax.get_yticklabels():
            ticklab[id(t)] = ax.get_ylim()
    def offview(t):
        lim = ticklab.get(id(t))
        if lim is None:
            return False
        m = re.fullmatch(r'\u2212?-?\d+(?:\.\d+)?', t.get_text().strip())
        if not m:
            return False
        v = float(t.get_text().replace('\u2212', '-'))
        return not (min(lim) - 1e-9 <= v <= max(lim) + 1e-9)
    keep = []
    for t in fig.findobj(matplotlib.text.Text):
        if not (t.get_text().strip() and t.get_visible()):
            continue
        if offview(t):
            continue
        try:                      # 只留真正落在画布里的文字（滤掉 locator 生成的越界刻度）
            bb = t.get_window_extent()
            if bb.x1 < fb.x0 - 2 or bb.x0 > fb.x1 + 2 or bb.y1 < fb.y0 - 2 or bb.y0 > fb.y1 + 2:
                continue
        except Exception:
            pass
        keep.append(t.get_text())
    TX[os.path.basename(path)[:5]] = keep
    return _orig(fig, path, kind)
C.save = cap; B.C.save = cap
for k in sorted(B.FIGS):
    B.FIGS[k]()
C.save = _orig; B.C.save = _orig

# 1 清单
pngs = {os.path.basename(f)[:5] for f in glob.glob(os.path.join(HERE, 'out', '*.png'))}
for n in range(0, 22):
    if f'fig{n:02d}' not in pngs:
        fail.append(f'fig{n:02d} missing (§7.1 / §7.3)')

# 2 纯白底（fig00 装饰条例外；tbl01 是裁到边框的表格截图，改判主色）
for f in sorted(glob.glob(os.path.join(HERE, 'out', '*.png'))):
    _b = os.path.basename(f)
    if _b.startswith('fig00'):
        continue
    im = Image.open(f).convert('RGB')
    if _b.startswith('tbl'):
        # 表格截图四角可能正好落在 #C9D2DC 边框线上，取样角点会误报。
        # 表格的底仍必须是纯白：要求出现最多的颜色就是 (255,255,255)。
        from collections import Counter as _C
        if _C(im.getdata()).most_common(1)[0][0] != (255, 255, 255):
            fail.append(f'{_b}: background not pure white (§4.1)')
        continue
    if any(im.getpixel(p) != (255, 255, 255) for p in
           [(0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)]):
        fail.append(f'{_b}: background not pure white (§4.1)')

# 3 图内全英文；负号不用 hyphen
for fn, ts in TX.items():
    blob = ' | '.join(ts)
    if any('一' <= c <= '鿿' for c in blob):
        fail.append(f'{fn}: CJK on chart (§4.1)')
    for t in ts:
        if re.search(r'(?<![A-Za-z0-9])-\d', t) and 'non-' not in t.lower():
            fail.append(f'{fn}: hyphen as minus -> {t[:50]}')

# 4 §2.3 图 5/6 无来源无括号；图 7 无来源但留评级释义
for fn in ('fig05', 'fig06'):
    blob = ' | '.join(TX[fn])
    for bad in ('Source', 'Morgan Stanley', 'Re-plotted', 'Tracker', 'J.P. Morgan', 'PitchBook'):
        if bad in blob:
            fail.append(f'{fn}: source reference on chart "{bad}" (§2.3)')
    par = [t for t in TX[fn] if '(' in t or ')' in t]
    if par:
        fail.append(f'{fn}: parenthesis on chart -> {par}')
blob7 = ' | '.join(TX['fig07'])
for bad in ('Source', 'Earnings Presentation', 'Morgan Stanley'):
    if bad in blob7:
        fail.append(f'fig07: footnote must not cite a source ("{bad}")')
if '1 = performing above expectations' not in blob7:
    fail.append('fig07: 10-Q rating definitions must be kept')

# 5 其余各图脚注必须有来源
for fn, ts in TX.items():
    if fn in ('fig00', 'fig05', 'fig06', 'fig07', 'fig21'):
        continue
    if not re.search(r'source:|re-plotted', ' | '.join(ts), re.I):
        fail.append(f'{fn}: footnote has no source (§4.4)')

# 6 季度标签两套写法不许混用；行业图不许外推到 CQ
for fn, ts in TX.items():
    if fn == 'fig00':
        continue
    n = int(fn[3:5]); blob = ' | '.join(ts)
    a = set(re.findall(r"Q[1-4]'\d\d", blob)); b = set(re.findall(r"\b[1-4]Q\d\d\b", blob))
    if n in (1, 2, 3, 4, 5, 6, 7) and (b - {TRK}):
        fail.append(f"{fn}: should use Q<n>'<yy>, found {sorted(b)} (§2.2)")
    if 10 <= n <= 14 and a:
        fail.append(f"{fn}: should use <n>Q<yy>, found {sorted(a)} (§2.2)")
    if 15 <= n <= 20 and CQ in blob:
        fail.append(f'{fn}: industry chart must stay on {TRK}, not {CQ} (§2.4)')

# 7 期数 / 窗口 / 冻结轴
for k in ('fig15_borrower_leverage', 'fig16_interest_coverage', 'fig17_bdc_nonaccrual_avg',
          'fig18_pik_over_tii', 'fig19_pik_over_nii'):
    if CH[k]['window_max'] is not None:
        fail.append(f'{k}: window_max must be null (§3.5)')
def periods(k):
    c = CH[k]
    return c['periods'] if 'periods' in c else list(next(iter(c['series'].values())).keys())
for k, n in (('fig02_cash_yield', 5), ('fig04_nii_coverage', 5)):
    if len(periods(k)) != n:
        fail.append(f'{k}: expected {n} periods (§2.3)')
for k in ('fig05_pik_share', 'fig06_nonaccrual', 'fig07_risk_rating'):
    ps = periods(k)
    if len(ps) != 6 or not any(p.startswith('FY') for p in ps):
        fail.append(f"{k}: need 6 periods with Q4 labelled FY<yy> (§2.3)")
for k, c in CH.items():
    if c.get('window_max') == 8 and len(periods(k)) > 8:
        fail.append(f'{k}: more than 8 periods on a two-year-capped chart (§3.5)')
    if 'ylim' in c and 'ytick' not in c:
        fail.append(f'{k}: ylim frozen but ytick missing (§3.5.1)')

# 8 每点都有 src；研报读点标 est
pts = nosrc = est = 0
def walk(d, p):
    global pts, nosrc, est
    if isinstance(d, dict):
        if 'v' in d and not isinstance(d['v'], (dict, list)):
            pts += 1
            if not d.get('src'): nosrc += 1; fail.append(f'{p}: point without src (§3.3)')
            if d.get('est'): est += 1
            return
        for k, v in d.items(): walk(v, f'{p}.{k}')
    elif isinstance(d, list):
        for i, v in enumerate(d): walk(v, f'{p}[{i}]')
walk(CH, 'charts')

# 9 股价缓存
import csv
rows = list(csv.DictReader(open(os.path.join(HERE, 'prices.csv'))))
ds = [r['date'] for r in rows]
if len(ds) != len(set(ds)) or ds != sorted(ds):
    fail.append('prices.csv must be deduped by date and ascending (§3.6)')
if ds[-1] != AS_OF:
    fail.append(f'prices.csv ends {ds[-1]}, AS_OF is {AS_OF} (§2.1)')
for fn in ('fig08', 'fig09'):
    if not any(t.startswith('As of') for t in TX[fn]):
        fail.append(f'{fn}: missing "As of <date>" (§2.5)')

# 10 标题定性词按本季重判
na = [v['v'] for v in CH['fig17_bdc_nonaccrual_avg']['series']['AVG_AT_COST'].values()]
if 'five-year high' in ' '.join(TX['fig17']) and na[-1] != max(na[-20:]):
    fail.append('fig17: title claims a five-year high, data disagrees (§4.4)')
sec = CH['fig20_nonaccrual_sector']
rises = sorted(((d['cq'] - d['avg3y'], d['name']) for d in sec['sectors']), reverse=True)
if [n for _, n in rises[:2]] != sec['sharpest_rise']:
    fail.append('fig20: sharpest_rise stale, recompute (§4.4)')
if max(v for v, _ in rises) < 1.0 and sec.get('triggered'):
    fail.append('fig20: trigger condition not met this quarter (§6 fig20)')

# 11 §7.4 四项不许生成
for f in glob.glob(os.path.join(HERE, 'out', '*.png')):
    if re.search(r'implied_tp|position_monitor|gs_software_exposure|leverage_scale', f):
        fail.append(f'§7.4 item generated: {f}')

print(f'figures rendered : {len(TX)}')
print(f'data points      : {pts}  (all with src: {nosrc == 0}; digitised/est: {est})')
print(f'prices.csv       : {len(rows)} rows, {ds[0]} .. {ds[-1]}')
print(f'CQ / PQ / AS_OF  : {CQ} / {PQ} / {AS_OF}   industry period: {TRK}')
print('=' * 50)

# ── 来源可追溯性 ────────────────────────────────────────────────
# 两层约定：图级 src 兜底（哪一期出自哪份文件），点级 src 只补差异（算式、口径例外）。
# 所以点级写 "same" 是合法的 —— 只要它所在的那张图有可解析的图级 src。
import re as _re2

_BANNED = _re2.compile(r'_v1\b|update_v1|Fundamental_Analysis|\.docx|报告表|报告里|'
                       r'上一版报告|report table|v1 报告', _re2.I)

# 可解析的来源特征：本地 PDF、SEC accession、券商研报、竞品线上 filings/材料
_RESOLVABLE = _re2.compile(
    r'\.pdf|\.xlsx|\.xlsm|\.csv|\.docx'      # 本地文件。xlsx 是内部模型（T3 的官方来源，
                                              # 见 08_tables.md）；csv 是价格缓存
    r'|000174\d{4}-\d\d-\d{6}'              # SEC accession
    r'|10-[QK]|8-K'                            # filing 类型
    r'|Tracker|Figure\s*\d|slide\s*\d|p\.\s*\d|pp?\.\s*\d'
    r'|earnings (?:release|presentation)|investor presentation|press release'
    r'|financial highlights|MD&A|Note\s*\d'
    r'|\b(ARCC|BXSL|OBDC|TSLX|GBDC|OTF|MSFT|ORCL|CRM|NOW)\b'
    r'|stockanalysis|exchange closing', _re2.I)

_bad_banned, _bad_unresolved = [], []
for _ck, _cv in S['charts'].items():
    _chart_src = _cv.get('src', '') if isinstance(_cv, dict) else ''
    _chart_ok = bool(_RESOLVABLE.search(_chart_src))
    _pts = []
    def _collect(o):
        if isinstance(o, dict):
            if isinstance(o.get('src'), str):
                _pts.append(o['src'])
            for _v in o.values(): _collect(_v)
        elif isinstance(o, list):
            for _v in o: _collect(_v)
    _collect(_cv)
    for _s in [_chart_src] + _pts:
        if _s and _BANNED.search(_s):
            _bad_banned.append(f'{_ck}: {_s[:80]}')
    # 点级解析不了时，靠图级兜底
    for _s in _pts:
        if not _RESOLVABLE.search(_s) and not _chart_ok:
            _bad_unresolved.append(f'{_ck}: "{_s[:60]}" 且该图无可解析的图级 src')

if _bad_banned:
    fail.append(f'{len(_bad_banned)} 个 src 指向上一版报告（二手数据，禁用）：'
                + ' / '.join(dict.fromkeys(_bad_banned))[:200])
if _bad_unresolved:
    fail.append(f'{len(_bad_unresolved)} 个 src 既指不到具体来源、所在图也没有图级 src：'
                + ' / '.join(dict.fromkeys(_bad_unresolved))[:200])
print(f'[src] 禁用来源 {len(_bad_banned)}，无法追溯 {len(_bad_unresolved)}')

print('PASS — all §8 checks clear' if not fail else f'FAIL — {len(fail)} issue(s)')
for x in fail: print('  x', x)
for x in warn: print('  ! ', x)
sys.exit(1 if fail else 0)

# ── tbl03 专项：软件分层占比禁止取内部 xlsx（那是去年数据）─────────────
# 其他表的 xlsx 来源仍然合法，这条只针对 tbl03。
_T3_BANNED = _re2.compile(r'\.xlsx|\.xlsm|草稿|Crosscheck|crosscheck', _re2.I)


def check_tbl03_source(charts):
    """tbl03_software_layer 的 src 里出现 xlsx / 草稿 / Crosscheck 一律 fail。"""
    t3 = charts.get('tbl03_software_layer')
    if not isinstance(t3, dict):
        return []
    bad = []
    srcs = [('chart', t3.get('src', ''))]
    for i, l in enumerate(t3.get('layers') or []):
        if isinstance(l, dict) and l.get('src'):
            srcs.append((f'layers/{i}', l['src']))
    for where, src in srcs:
        if src and _T3_BANNED.search(src):
            bad.append(
                f'tbl03_software_layer/{where}: src 指向内部 xlsx —— '
                f'「{src[:70]}」。分层占比必须从本季 10-Q 的 Schedule of Investments '
                f'逐家公允值自算，草稿 workbook 是去年的数据。见 08_tables.md 的 T3 专节')
    if not _re2.search(r'Schedule of Investments|schedule of investments|10-Q',
                       t3.get('src', '')):
        bad.append(
            'tbl03_software_layer/chart: src 里没提 10-Q Schedule of Investments —— '
            '占比的唯一合法来源是本季 10-Q 的投资明细表')
    return bad
