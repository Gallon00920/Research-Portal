"""Junson Capital house chart style for the Private Credit Quarterly.

Usage:
    import junson_style as js
    js.apply()                       # set global rcParams
    fig, ax = js.figure('half')      # 'half' (side-by-side) or 'full' width
    ax.bar(x, y, color=js.NAVY)
    js.finish(ax)                    # spines/grid cleanup
    js.label_bars(ax, x, y)          # bold navy value labels
    fig.savefig(path, **js.SAVE_KW)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- palette：与 OTF 季报统一（用户 2026-08-21 指定）----------------------
# 原 PC 色板（#1F2A44 / #7A9BB8 / #2FA6A0 / #2E7D4F）已作废，换成 OTF 那一套色号。
# 角色映射：OTF 里 #A93226 是「唯一的红，只给标的本身」；PC 没有单一标的，
# 这个位置给 **Junson 自己的三只基金**（竞品图里的高亮），其余序列一律不许用红色系。
# 配色全部从 palette.py 取 —— 那里不 import 任何第三方库，
# 出稿脚本和校验脚本也共用它，避免各写一份常量后悄悄漂开。
from palette import (NAVY, BLUE, LIGHTBL, GREYBL, GOLD, SLATE, ROSE, LIGHTGY,
                     MAROON, RHS, HILITE, PIE_OTHER, GRAY, BODY, GRID, AXIS, BANDS, DOCX)
# 旧名兼容 —— 一律指回 palette 的位次，别在这里写十六进制。
# ⛔ 2026-08-25 踩过：这里原来又写了一遍 `BANDS = [...]` 覆盖 import 进来的值，
#    于是 palette 换了色、评级带图还是旧色，而且没人看得出来。
#    规矩：junson_style 只做「取名」和「排版」，色值只有 palette.py 一处真值。
STEEL, TEAL, MIDBLUE, GREEN = BLUE, LIGHTBL, RHS, GOLD
from palette import SERIES, SERIES_EXT, series_ext
# 自家三只基金的标记色（同图同时出现，palette 里断言过互不相同）
from palette import OWN_FUNDS, OWN_FUND_FALLBACK

# ── 版面锁：画布宽 = Word 插入宽（1:1）────────────────────────────────
# 2026Q3 成稿实测：并排图插 3.35 in，画布 4.4–5.3 in（缩到 63–76%）；
# 单图插 6.5–6.9 in，画布 8.3–8.7 in（缩到 75–79%）。图内 7pt 因此只显示 5.0–5.8pt。
# 而且有两张单图插到 6.90 in，超出正文可用宽 6.74 in，溢出页面。
# 现在锁 1:1：图内写多少 pt，纸上就是多少 pt，不用再算比例。
DPI = 200
CANVAS = {
    "pair": 3.35,      # 并排（一组两张 3.35 + 0.04 gap = 6.74，与正文同宽）
    "solo": 6.74,      # 单图 —— 就是正文可用宽，不许再大
    "tall": 5.30,      # 窄高单图（Alex 2026-08-24 为 Ex 9 定：长度缩短、高度拉高），Word 侧居中插入
}
CANVAS_TOL = 0.02
SAVE_KW = dict(dpi=DPI, facecolor="white")   # 不用 bbox_inches='tight'，它会裁掉白边破坏 1:1

# 图内字号：1:1 之后这就是纸上实际字号。正文 7.5pt，所以图内取 6–7.5pt。
# PC 的图**不放标题也不放脚注** —— 题注和 Note/Source 都在 Word 侧，图内只有数据。
FS = {
    "pair": dict(axis=6.5, tick=6.0, label=6.0, legend=6.0),
    "solo": dict(axis=7.5, tick=7.0, label=7.0, legend=7.0),
    "tall": dict(axis=7.5, tick=7.0, label=7.0, legend=7.0),
}

# 兼容旧调用：以前的 'half'/'full'/'square' 映射到新的两档，但会打印一次提醒
_LEGACY = {"half": "pair", "full": "solo", "square": "solo"}
_warned = set()


def _kind(k):
    if k in CANVAS:
        return k
    if k in _LEGACY:
        nk = _LEGACY[k]
        if k not in _warned:
            _warned.add(k)
            print(f"[junson_style] '{k}' 是旧名，已映射到 '{nk}'（画布 {CANVAS[nk]} in，1:1）")
        return nk
    raise ValueError(f"未知画布类型 {k!r}，只能是 {list(CANVAS)}")


SIZES = {k: (v, None) for k, v in CANVAS.items()}   # 高度由调用方给


def apply(kind="pair"):
    f = FS[_kind(kind)]
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "font.size": f["tick"],
        "axes.edgecolor": AXIS,
        "axes.labelcolor": BODY,
        "xtick.color": BODY,
        "ytick.color": BODY,
        "xtick.labelsize": f["tick"],
        "ytick.labelsize": f["tick"],
        "axes.labelsize": f["axis"],
        "legend.frameon": False,
        "legend.fontsize": f["legend"],
        "axes.grid": False,
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Calibri", "Arial"],
    })


def figure(kind="pair", h=None, **kw):
    """建图的唯一入口。宽度不给选 —— 并排 3.35 in、单图 6.74 in，1:1。

        fig, ax = js.figure('pair', h=2.4)
        fig, ax = js.figure('solo', h=3.2)
    """
    k = _kind(kind)
    apply(k)
    w = CANVAS[k]
    if h is None:
        h = {"pair": 2.4, "solo": 3.2, "tall": 4.2}[k]
    fig, ax = plt.subplots(figsize=(w, h), **kw)
    fig.patch.set_facecolor("white")
    fig._js_kind = k
    return fig, ax


def save(fig, path, kind=None, skip_check=False):
    """落盘 + 两道硬检查：画布宽必须等于插入宽；图内文字不许压叠。

    不许用 skip_check=True 绕过 —— 出图后还要自己逐张看一遍。
    """
    k = _kind(kind or getattr(fig, "_js_kind", "pair"))
    want = CANVAS[k]
    w_in = fig.get_size_inches()[0]
    if abs(w_in - want) > CANVAS_TOL:
        raise SystemExit(
            f"[版面] {path}: figsize[0]={w_in:.2f} in，{k} 必须是 {want} in。\n"
            f"  画布宽 = Word 插入宽（1:1），图内写多少 pt 纸上就是多少 pt。\n"
            f"  按现在这个宽度，插到 {want} in 之后图内 {FS[k]['tick']} pt 的字只剩 "
            f"{FS[k]['tick'] * want / w_in:.1f} pt。\n"
            f"  用 js.figure('{k}', h=...) 建图，不要自己写 plt.subplots(figsize=(...))。")
    if not skip_check:
        try:
            import guards
            guards.check(fig)
        except ImportError:
            print("[junson_style] 没找到 guards.py —— 压叠/水平标签/描点检查被跳过了，请补上")
    fig.tight_layout()
    _do_fit_right(fig)          # 出图脚本调过 js.fit_right() 的，在这里真正执行
    _warn_right_overflow(fig, path)
    fig.savefig(path, **SAVE_KW)
    plt.close(fig)
    try:
        from PIL import Image
        got = Image.open(path).width / DPI
        if abs(got - want) > 0.03:
            raise SystemExit(f"[版面] {path}: 落盘宽 {got:.2f} in ≠ {want} in，1:1 被破坏")
    except ImportError:
        pass
    print(f"[written] {path}  {want} in @ {DPI} dpi ({k})")


MARKER_RATIO = 2.0


def ms(lw):
    """描点直径 = 线宽 × 2（与 OTF 统一）。guards.assert_marker_size() 会硬查。"""
    return lw * MARKER_RATIO


def finish(ax, ygrid=True, pct_y=False):
    """House cleanup: kill top/right spines, y-grid only, grid behind data."""
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if ygrid:
        ax.yaxis.grid(True, color=GRID, linewidth=1.0)
        ax.set_axisbelow(True)
    if pct_y:
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1))


def label_bars(ax, xs, tops, fmt="{:,.0f}", dy_frac=0.015, color=NAVY, fontsize=None):
    """Bold navy value labels above bar tops (pass stacked totals for stacks)."""
    fontsize = fontsize or plt.rcParams["font.size"]
    ymax = max(tops) if len(tops) else 1
    for x, t in zip(xs, tops):
        ax.text(x, t + ymax * dy_frac, fmt.format(t),
                ha="center", va="bottom", fontweight="bold",
                color=color, fontsize=fontsize)


def endpoint_label(ax, x, y, text, color=GREEN, dx=0.2, fontsize=None):
    """Bold label at a line's endpoint (e.g. latest value callout)."""
    ax.annotate(text, (x, y), xytext=(x + dx, y), fontweight="bold",
                color=color, fontsize=fontsize or plt.rcParams["font.size"], va="center")


def tick_idx(n, step):
    """时间序列的横轴刻度下标 —— **末期一定上刻度**。

    ⛔ 这是写死的（Alex 2026-08-24）。抽稀标签时如果最后一期没被选中，
    图上读起来就像数据停在更早的一期 —— 2026Q3 踩过：图 5 数据到 May-26，
    标签隔 11 个月一个，最后一个落在 Aug-25，看图的人以为只更新到去年。

    做法：按 step 均匀取，然后强制把末期加进来；如果末期离前一个刻度太近
    （< step 的一半）就把那个前刻度顶掉，避免两个标签压在一起。
    """
    if n <= 0:
        return []
    step = max(1, int(step))
    idx = list(range(0, n, step))
    last = n - 1
    if idx and idx[-1] != last:
        if last - idx[-1] < max(2, step // 2):
            idx[-1] = last
        else:
            idx.append(last)
    return idx


def assert_last_ticked(ax, n):
    """确认末期真的上了刻度。⛔ 不通过就抛错 —— 别让「看起来停在去年」再发生一次。"""
    if n <= 1:
        return
    ticks = [t for t in ax.get_xticks()]
    if not ticks or max(ticks) < n - 1 - 1e-6:
        raise ValueError(
            f'横轴末期没上刻度：共 {n} 期，最大刻度落在下标 {max(ticks) if ticks else None}，'
            f'应当是 {n-1}。图上会读成数据停在更早的一期。'
            f'\n  改法：用 js.tick_idx(len(periods), step) 生成刻度下标。')


def twin_right(ax):
    """Right-hand axis styled like the house look."""
    ax2 = ax.twinx()
    for s in ("top",):
        ax2.spines[s].set_visible(False)
    return ax2


def rating_band_chart(items, bands=None, kind="pair", h=2.6):
    """Positioning graphics like Exhibits 22/24: horizontal shaded rating bands
    (low->high risk top to bottom) with navy diamond markers.

    items: list of (label, band_index 0..3, x_position 0..1), e.g.
           [("HY 3.6x", 1, 0.25), ("Syndicated Loans 4.0x", 2, 0.45), ...]
    bands: list of band names top->bottom, default AAA-BBB/BB1-BB3/B1-B3/CCC.
    """
    bands = bands or ["AAA - BBB", "BB1-BB3", "B1-B3", "CCC"]
    heights = [1.0] * len(bands)
    fig, ax = figure(kind, h=h)
    y = 0
    centers = []
    for i, (name, h) in enumerate(zip(bands[::-1], heights[::-1])):
        ax.axhspan(y, y + h, color=BANDS[::-1][i % len(BANDS)])
        centers.append(y + h / 2)
        ax.text(0.03, y + h - 0.25, name, fontsize=plt.rcParams["font.size"], color=BODY)
        y += h
    centers = centers[::-1]
    for label, band_i, xpos in items:
        yy = centers[band_i] + (0.18 if band_i else 0)
        ax.scatter([xpos], [yy], marker="D", s=140, color=NAVY, zorder=5)
        ax.text(xpos + 0.03, yy, label, fontsize=plt.rcParams["font.size"], color=NAVY, va="center")
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, y)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.annotate("", xy=(-0.02, 0), xytext=(-0.02, y),
                arrowprops=dict(arrowstyle="<->", color=NAVY))
    ax.text(-0.06, y, "Low", fontsize=plt.rcParams["font.size"], color=BODY, ha="right", va="top")
    ax.text(-0.06, 0, "High", fontsize=plt.rcParams["font.size"], color=BODY, ha="right", va="bottom")
    return fig, ax

# ──────────────────────────────────────────────────────────────────────────
# x_start —— 只裁「画」的左端，不动账本
#
# ⛔ Alex 2026-08-25：「图53需要从19年开始画，图54需要从13年开始画就行。」
#
# 铁律一说历史点只追加不重算，所以**不许把早年的数从账本里删掉**。
# 要少画几年，就在该 exhibit 上写 `x_start`，出图时按它切；账本仍保留全量，
# 下季重算/回看/审计都还在。
#
# `x_start` 是**固定起点，不是滚动窗口** —— 每季只在右端加一期，左端不动。
# 想改成滚动窗口，用 `window_max`（见 SKILL「滚动窗口」一节），两者不要同时给。
# ──────────────────────────────────────────────────────────────────────────
def xstart_idx(ent, axis):
    """返回该 exhibit 应从 axis 的第几个元素开始画。没写 x_start 就返回 0。"""
    xs = ent.get('x_start')
    if xs in (None, ''):
        return 0
    want = str(xs)
    ax = [str(a) for a in axis]
    if want in ax:
        return ax.index(want)
    raise SystemExit(f'✗ x_start={want!r} 不在横轴里。横轴现有：{ax}\n'
                     f'  x_start 必须**精确等于**横轴上的某个标签 —— 写错了就会静默少画/多画一年。')


def xwin(ent, axis, *arrays):
    """一次切轴与若干条数据。用法：
        lb, a, b = js.xwin(ent, ent['labels'], a, b)
    """
    i = xstart_idx(ent, axis)
    if i == 0:
        return (list(axis),) + tuple(arrays)
    return (list(axis)[i:],) + tuple(
        (a[i:] if a is not None else None) for a in arrays)

def place_bar_labels(ax, xs, tops, texts, ax2=None, rhs_vals=None,
                     color=None, fontsize=None, pad_pt=1.5):
    """画柱值标签，并**按实测 bbox** 避开右轴那条线。

    ⛔ 2026-08-25 的教训：先用「两个轴的归一化高度差 < 阈值」估过一版，
       结果 2017/2023 两根柱被判成撞了、标签移进柱内，而线其实在柱顶**下方** ——
       移进去正好撞上。几何靠估是估不准的（字号、offset、轴高都在里面）。
       改成：先按默认位置画，量出标签的真实像素框，再把线在该 x 处的像素 y 算出来，
       真的落在框里才翻到柱内；柱内也撞就横向让开半格。
    """
    fig = ax.figure
    fig.canvas.draw()                      # 有 renderer 才能量 bbox
    ren = fig.canvas.get_renderer()
    color = color or NAVY
    fontsize = fontsize or plt.rcParams['font.size']
    line_y_px = {}
    if ax2 is not None and rhs_vals is not None:
        for i, rv in enumerate(rhs_vals):
            if rv is None or rv != rv:
                continue
            line_y_px[i] = ax2.transData.transform((0, float(rv)))[1]

    out = []
    for i, (xx, tv, tx) in enumerate(zip(xs, tops, texts)):
        for attempt in ('above', 'inside', 'shift'):
            dy = 3 if attempt == 'above' else -3
            va = 'bottom' if attempt == 'above' else 'top'
            dx = 0 if attempt != 'shift' else 9
            col = color if attempt == 'above' else 'white'
            an = ax.annotate(tx, (xx, tv), textcoords='offset points',
                             xytext=(dx, dy), ha='center', va=va, zorder=6,
                             fontweight='bold', color=col, fontsize=fontsize)
            if i not in line_y_px:
                out.append(an); break
            bb = an.get_window_extent(renderer=ren)
            ly = line_y_px[i]
            if not (bb.y0 - pad_pt <= ly <= bb.y1 + pad_pt):
                out.append(an); break
            an.remove()
        else:
            out.append(ax.annotate(tx, (xx, tv), textcoords='offset points',
                                   xytext=(9, -3), ha='center', va='top', zorder=6,
                                   fontweight='bold', color='white', fontsize=fontsize))
    return out

# ──────────────────────────────────────────────────────────────────────────
# 图例放图内
#
# ⛔⛔ Alex 2026-08-25：「Exhibit 23 中的图注要放在图里，而不是图的下面，不止 E23，
#     这个也要写在阶段一生图的底层。」
#
# 为什么放图内：图例放图下会把 Word 侧的题注—图—Note 三段压得更挤，而且并排图
# （3.35 in）下方本来就要留 Note 的位置。图例进图内之后图能长回来。
#
# 怎么选位：先看账本 `legend_loc`（冻结值）；没有就**实测四角的数据密度**挑最空的一角，
# 并打印一行建议值 —— 看过之后把它写进账本冻结。
# ⛔ 不许每季自动重选：自动选会让同一张图的图例跨季跳位置，读者会以为图变了。
# ──────────────────────────────────────────────────────────────────────────
_CORNERS = {
    'upper left':  (0.00, 0.55, 0.46, 1.00),
    'upper right': (0.54, 0.55, 1.00, 1.00),
    'lower left':  (0.00, 0.00, 0.46, 0.45),
    'lower right': (0.54, 0.00, 1.00, 0.45),
}


def _corner_ink(ax, box):
    """某一角里有多少「数据墨」—— 用渲染后的像素数，不靠猜。"""
    import numpy as _np
    fig = ax.figure
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    buf = _np.frombuffer(fig.canvas.buffer_rgba(), dtype=_np.uint8).reshape(h, w, 4)[:, :, :3]
    bb = ax.get_window_extent()
    x0 = int(bb.x0 + box[0] * bb.width);  x1 = int(bb.x0 + box[2] * bb.width)
    y0 = int(h - (bb.y0 + box[3] * bb.height)); y1 = int(h - (bb.y0 + box[1] * bb.height))
    reg = buf[max(0, y0):max(1, y1), max(0, x0):max(1, x1)]
    if reg.size == 0:
        return 10 ** 9
    # 非白、且不是网格线的浅灰 —— 就算数据墨
    dark = (reg.max(2) < 235)
    return int(dark.sum())


def legend_inside(ax, handles=None, labels=None, ent=None, ncol=1, slug='', **kw):
    """把图例放进图内。位置优先取账本 `legend_loc`，否则实测四角挑最空的并打印建议。"""
    loc = (ent or {}).get('legend_loc')
    if not loc:
        ink = {k: _corner_ink(ax, b) for k, b in _CORNERS.items()}
        loc = min(ink, key=ink.get)
        print(f"    ⚠ {slug or ax.get_ylabel() or '?'}: legend_loc 未冻结，实测最空的一角是 "
              f"'{loc}'（各角墨量 {ink}）—— 看过之后写进账本冻结")
    # `boxed=True`：实心白底 + 细黑框。给「图例色块可能被误读成数据点」的图用 ——
    # ⛔ Alex 2026-08-25：「可以用个细的黑色矩形框线把图标框起来，就不会读错了。」
    # 起因：Ex 51/52 的图例放图内右下时，三个色块正好落在 2027Q1–Q2 的横轴位置上，
    # 被读成「2027 年有数据」（Alex 2026-08-24 就这么读的）。框起来之后它读作图例，
    # 不再读作散点 —— 所以那两张不再需要「图例放图外」的例外。
    boxed = bool((ent or {}).get('legend_boxed'))
    o = dict(loc=loc, frameon=True,
             framealpha=1.0 if boxed else 0.82,
             edgecolor='black' if boxed else 'none',
             handlelength=1.2, labelspacing=0.22, borderpad=0.35 if boxed else 0.25,
             ncol=ncol, fontsize=plt.rcParams['font.size'])
    o.update(kw)
    # ⛔ 图例要挂在**最上面那层轴**上：twin_right 建出来的 ax2 是后画的一层，
    #    挂在 ax 上的图例会被 ax2 的折线盖住（zorder 管不了跨 Axes 的绘制顺序）——
    #    2026-08-25 实测 mkt_dl_origination 的 "Refi"、mkt_inst_aum_decomp 的
    #    "Dry powder as % of NAV (rs)" 都被右轴折线划了一道。
    own, pos = ax, ax.get_position().bounds
    for a in ax.figure.axes:
        if a is not ax and a.get_position().bounds == pos:
            own = a
    if handles is None and own is not ax:
        handles, labels = [], []
        for a in ax.figure.axes:
            if a.get_position().bounds == pos:
                hh, ll = a.get_legend_handles_labels()
                handles += hh; labels += ll
    lg = (own.legend(handles, labels, **o) if handles is not None else own.legend(**o))
    fr = lg.get_frame()
    fr.set_facecolor('white')
    if boxed:
        fr.set_linewidth(0.6)
    lg.set_zorder(9)
    return lg


# ── 右侧越界：检测 + 修 ──────────────────────────────────────────────────────
# 起因（2026-08-25）：Ex 26 右轴末点标 "10.7" 顶在右边框上，"7" 被边框和右轴刻度 "12"
# 切开。原来靠 `xlim=(..., len(p)-0.4+len(p)*0.07)` 这种经验余量给末点标签留位置 ——
# 余量按周期数算，标签宽度按字数算，两者没关系，周期一多就不够。
#
# ⚠ 判据分两种，混起来就全是假警报（第一版就是，14 张里 11 张是好图）：
#   · **有右轴**（twin_right）：坐标区右边框外面就是右轴的刻度和刻度标签，末点标签越过
#     右边框就一定压在它们身上 —— 右边框就是硬边界。
#   · **没有右轴**：右边框外面是空白页边，末点标签本来就该写在那儿（endpoint_label、
#     `annotation_clip=False` 都是为这个），只有越出**画布**才是真被切掉。
def _right_bound(fig, ax):
    """这张图右侧的硬边界（display 像素）。有右轴 = 坐标区右边框；没有 = 画布右边。"""
    r = fig.canvas.get_renderer()
    has_twin = any(a is not ax and abs(a.get_window_extent(r).x1
                                       - ax.get_window_extent(r).x1) < 2.0
                   and a.yaxis.get_ticks_position() in ('right', 'default')
                   and len(a.get_yticklabels()) and a.get_yaxis().get_visible()
                   for a in fig.axes)
    if has_twin:
        return ax.get_window_extent(r).x1, 'right axis'
    return fig.get_window_extent().x1, 'canvas'


def _text_overflow_px(fig):
    """量出图内文字越过右侧硬边界最多多少像素。返回 (px, 文字, 边界种类)。"""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    prim = [a for a in fig.axes if a.get_yaxis().get_ticks_position() != 'right']
    ax0 = prim[0] if prim else fig.axes[0]
    bound, what = _right_bound(fig, ax0)
    worst, who = 0.0, None
    for ax in fig.axes:
        for t in list(ax.texts):
            if not t.get_visible() or not (t.get_text() or '').strip():
                continue
            try:
                bb = t.get_window_extent(r)
            except Exception:
                continue
            if bb.x1 - bound > worst:
                worst, who = bb.x1 - bound, t.get_text()
    return worst, who, what


def _warn_right_overflow(fig, path, tol_px=1.0):
    over, who, what = _text_overflow_px(fig)
    if over > tol_px:
        print(f"    ⚠ {path}: 图内文字 {who!r} 越过{what} {over:.0f}px —— "
              f"在 js.save() 之前调 js.fit_right(ax, ax2) 补余量")


def flip_if_overflow(ann, ax_primary, dx=None, last_seg=None):
    """末值标签压到右边界外就镜像到点的左侧，返回是否翻了。

    ⛔ 先翻标签，再考虑推轴 —— 推轴会在末柱和右轴之间留一大片空白
    （2026-08-26 实测 mkt_dl_origination：为了 '80%' 把 x 上限 64.90 → 72.36，
    凭空多出约十个柱宽）。量的是真实渲染 bbox，不是拍余量；翻完仍越界交给 fit_right 兜底。

    `last_seg` = 末段的方向（末值 − 前一个值）。翻到左边之后要**躲开折线**：
    末段在涨，线占的是左下方 → 标签放左**上**；末段在跌 → 标签放左**下**。
    给不出方向就沿用原来的上下位置。另外一律加 82% 白底 —— 左边是数据区，
    没有底色的话文字会被折线或柱子划掉一道。
    """
    fig = ann.figure or ax_primary.figure
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bound, _ = _right_bound(fig, ax_primary)
    try:
        bb = ann.get_window_extent(r)
    except Exception:
        return False
    if bb.x1 - bound <= 0.5:
        return False
    ox, oy = ann.xyann
    ndx = -(abs(ox) if dx is None else abs(dx))
    ndy = oy
    if last_seg is not None:
        ndy = abs(oy) if last_seg >= 0 else -abs(oy)
    ann.set_position((ndx, ndy))
    ann.set_ha('right')
    ann.set_va('bottom' if ndy > 0 else 'top')
    # ⛔ 翻到左边就压在折线上了（右边是图外，左边是数据区）—— 给 82% 白底把线断开，
    #    和 legend_inside 一样的处理。不给底色的话 '80%' 被折线划掉一道（2026-08-26 实测）。
    ann.set_bbox(dict(boxstyle='square,pad=0.12', facecolor='white',
                      alpha=0.82, edgecolor='none'))
    fig.canvas.draw()
    return True


def fit_right(ax, *twins):
    """登记「这张图右侧要按实测补余量」。真正的推轴在 js.save() 里做。

    ⚠ 必须放在 tight_layout 之后 —— tight_layout 会重排坐标区，在它之前量出来的
    越界像素数到落盘时已经不对了（2026-08-25 实测 mkt_dl_origination 差 2px 就是这样）。
    所以这里只登记，save() 里 tight_layout 完再迭代。
    """
    x0, x1 = ax.get_xlim()
    axes = [ax] + [t for t in twins if t is not None]
    if not twins:
        # 不传 twin 就自己找：同一张图上 x 范围一致的轴（twin_right 建出来的都算）
        axes = [a for a in ax.figure.axes if a.get_xlim() == (x0, x1)]
    ax.figure._js_fit_right = axes


def _do_fit_right(fig, pad_pt=2.0, rounds=5):
    """实测越界多少就把 x 上限往右推多少，迭代到不越界。

    只动 xlim（连 twin 一起动），不动数据、不动字号、不动画布宽 —— 1:1 锁不受影响。
    推完 xlim 刻度标签会重排、坐标区宽度会变，所以要迭代。
    """
    axes = getattr(fig, '_js_fit_right', None)
    if not axes:
        return
    for _ in range(rounds):
        over, who, _w = _text_overflow_px(fig)
        if over <= 0.5:
            return
        r = fig.canvas.get_renderer()
        x0, x1 = axes[0].get_xlim()
        px_per_unit = axes[0].get_window_extent(r).width / (x1 - x0)
        add = (over + pad_pt * fig.dpi / 72.0) / px_per_unit
        for a in axes:
            a.set_xlim(x0, x1 + add)
        print(f"    · fit_right: {who!r} 越界 {over:.0f}px，x 上限 {x1:.2f} → {x1 + add:.2f}")
