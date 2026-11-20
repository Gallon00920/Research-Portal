"""样式冻结层 —— 定稿后不许改。"""
import os
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PALETTE_A = ['#16283F','#2E6DA4','#A93226','#8C97A5','#9DB8D2',
             '#C9A227','#4B5B6E','#C08578','#AEB4BC','#6E1F18']
PIE_OTHER = '#D5DAE0'
RHS_BLUE  = '#437BAD'
TITLE_A, TEXT_A, NOTE_A, GRID_A = '#16283F', '#000000', '#5A6B7B', '#E3E7EC'
# TEXT_A 已由 #22303C 改为纯黑 #000000（正文与图内文字统一纯黑）
TITLE, TEXT, NOTE, GRID = TITLE_A, TEXT_A, NOTE_A, GRID_A
BG = 'white'
HILITE    = '#A93226'

# ↓ 已作废：图 10–14 改走 TICKER_COLORS + 纯白底，这里只为兼容旧调用保留
PALETTE_B = {'OTF':'#E60012','ARCC':'#2A78D6','BXSL':'#EDA100',
             'OBDC':'#4A3AA7','TSLX':'#1BAF7A','GBDC':'#008300'}
BG_B, GRID_B, TITLE_B, SUB_B, NOTE_B = '#FCFCFB','#E1E0D9','#0B0B0B','#52514E','#898781'


TICKER_COLORS = {
    'OTF' : '#A93226',
    'ARCC': '#4B5B6E', 'BXSL': '#C9A227', 'OBDC': '#9DB8D2',
    'TSLX': '#AEB4BC', 'GBDC': '#2E6DA4',
    'MSFT': '#4B5B6E', 'ORCL': '#C9A227', 'CRM': '#9DB8D2', 'NOW': '#AEB4BC',
}


# ── 版面锁（A4 竖版，画布宽 = Word 插入宽，1:1）────────────────────────
# v3 实测：A4 竖版 11906×16838、左右边距 830/832 = 1.15 in、正文可用宽 7.12 in，
# 图片插入宽 7.11 in —— 结构是对的。但画布还是 12–18 in 的旧画布，
# 所以图内 11.5pt 的脚注在 v3 纸上只有 2.2–7.8pt，并排的图 10/11 只剩 2.2–2.4pt。
# 因此把比值锁成 1:1 —— 图内写多少 pt，纸上就是多少 pt。
CANVAS_W = 6.05          # 常规图：正文宽 7.12 in 的 85%，居中，不顶两端
CANVAS_W_FULL = 7.11     # ⭐ 例外：封面最上面那条长横条（fig00_titlebar）必须与正文两端同宽
FULLWIDTH = ('fig00_titlebar',)
DPI      = 200           # 只管清晰度（1422 px 宽），不影响字多大
CANVAS_TOL = 0.01

# ⚠ 阶段一出图不受阶段二并排影响 —— 21 张一律 6.05 in 画布（= 正文宽度的 85%）。
# 2.6.2 的图 10‖11、2.6.3 的图 13‖14 是**阶段二的排版规则**：
# 插入时缩到 3.50 in 并排（v3 就是这么排的），PNG 本身不重出、不换画布。
# 缩到 3.50 in 之后图内字按 58% 显示（脚注 7.5 → 4.3pt），
# 所以这两组的说明与分析合并成一段放在两图下方，读者读下方那段，不读图内脚注。
# 2.6.2：图 10‖11    2.6.3：图 13‖14
# 3.3  ：图 15‖16、图 17‖18、图 19‖20（六张两两并排，每两张下面一段合并分析）
PAIRED_PLACEMENT = ('fig10_bdc_nav', 'fig11_bdc_div_yield',
                    'fig13_bdc_nonaccrual', 'fig14_bdc_avg_ebitda',
                    'fig15_borrower_leverage', 'fig16_interest_coverage',
                    'fig17_bdc_nonaccrual_avg', 'fig18_pik_over_tii',
                    'fig19_pik_over_nii', 'fig20_nonaccrual_sector')
PAIR_INSERT_W = 3.50     # 阶段二插入宽度，不是画布宽度
N_PAIRED = 10            # 并排的图正好 10 张

# 折线描点：直径 = 线宽 × 2。guards.assert_marker_size() 会硬查，不符合直接报错。
MARKER_RATIO = 2.0


def ms(lw):
    """给定线宽返回该用的 markersize（直径 = 线宽 × 2）。

    matplotlib 里 markersize 就是直径（pt），linewidth 也是 pt，所以直接乘。
    用法：ax.plot(x, y, lw=2.0, marker='o', ms=chartlib.ms(2.0))
    以前是 lw=3 / ms=7，点比线粗一倍多，会盖住线和相邻的点。
    """
    return lw * MARKER_RATIO


# 图内字号（1:1，常规图插入时就是纸上实际字号）
FS_TITLE, FS_SUB, FS_AXIS = 13.0, 9.5, 9.0
FS_TICK, FS_LABEL, FS_LEGEND, FS_NOTE = 8.5, 8.5, 9.0, 7.5


def figure(h, **kw):
    """建图的唯一入口 —— 宽度不给选，永远 CANVAS_W。高度按各图比例给。

    并排的四张（图 10/11/13/14）也走这里：它们的画布同样 6.05 in，
    只在阶段二插入时缩到 3.50 in。"""
    fig, ax = plt.subplots(figsize=(CANVAS_W, h), **kw)
    fig.patch.set_facecolor('white')
    return fig, ax


def use_style(kind='A'):
    matplotlib.rcParams['font.family'] = 'Lato'
    matplotlib.rcParams['axes.unicode_minus'] = False


def roll(periods, cq, window_max=8):
    """窗口切片。window_max=8 → 两年上限（只加不删，满 8 期才裁左端）。
    window_max=None → 不设上限，返回全序列（图 15–19 走这一支，左端永不裁）。"""
    ps = periods[:periods.index(cq) + 1]
    return ps if window_max is None else ps[-window_max:]


def frame(ax, kind='A'):
    ax.grid(True, axis='y', color=(GRID_A if kind == 'A' else GRID_B), lw=0.8)
    ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    if kind == 'B':
        ax.spines['left'].set_visible(False)


def title(ax, text, kind='A', size=22):
    if kind == 'A':
        ax.set_title(text, fontsize=size, fontweight='bold', color=TITLE_A, pad=16)
    else:
        ax.set_title(text, fontsize=size, fontweight='bold', color=TITLE_B,
                     loc='left', pad=26)


def footnote(fig, text, kind='A', size=11.5, width=175):
    """左下脚注：按画布宽度折行，每行顶到右边缘。"""
    lines = textwrap.wrap(text, width=width)
    fig.text(0.008, 0.005, '\n'.join(lines), ha='left', va='bottom',
             fontsize=size, color=(NOTE_A if kind == 'A' else NOTE_B))


def highlight_last(ax, x, y, fmt='{:.1f}%', size=19, dy=10):
    ax.plot([x], [y], 'o', ms=15, color=HILITE, zorder=6)
    ax.annotate(fmt.format(y), (x, y), textcoords='offset points',
                xytext=(0, dy), ha='center', fontsize=size,
                fontweight='bold', color=HILITE)


def line_labels(ax, xs, ys, color, fmt='{:.1f}%', size=19, dy=12,
                bold=True, skip_last=False):
    for i, (x, y) in enumerate(zip(xs, ys)):
        if y is None:
            continue
        if skip_last and i == len(xs) - 1:
            continue
        ax.annotate(fmt.format(y), (x, y), textcoords='offset points',
                    xytext=(0, dy), ha='center', fontsize=size,
                    fontweight=('bold' if bold else 'normal'), color=color)


def save(fig, path, kind='A', allow=(), skip_check=False):
    # 出图前两道硬检查：图内全英文 + 任何文字不许压叠/被裁。
    # 报错就去修布局，不要用 skip_check=True 绕过。
    if not skip_check:
        import guards
        guards.check(fig, allow=allow)
    w_in = fig.get_size_inches()[0]
    base = os.path.basename(path)
    is_full = any(base.startswith(k) for k in FULLWIDTH)
    want = CANVAS_W_FULL if is_full else CANVAS_W
    if abs(w_in - want) > CANVAS_TOL:
        raise SystemExit(
            f'[版面] {base}: figsize[0]={w_in:.2f} in，必须是 {want} in。\n'
            + (f'  封面横条与正文两端同宽（{CANVAS_W_FULL} in），不走 85%。\n' if is_full
               else f'  画布宽 = 插入宽 = 正文宽的 85%（{CANVAS_W} in），1:1，图内写多少 pt 纸上就是多少 pt。\n')
            + f'  按现在这个宽度，插到 {want} in 之后图内 {FS_NOTE} pt 的字只剩 '
            + f'{FS_NOTE * want / w_in:.1f} pt。\n'
            + '  用 chartlib.figure(高度) 建图，不要自己写 plt.subplots(figsize=(...))。')
    if is_full:
        print(f'  └ {base} 是封面横条，与正文两端同宽 {CANVAS_W_FULL} in（不走 85%）')
    if any(base.startswith(k) for k in PAIRED_PLACEMENT):
        print(f'  └ {base} 属并排组，阶段二插入 {PAIR_INSERT_W} in，'
              f'图内 {FS_NOTE} pt 将按 {FS_NOTE * PAIR_INSERT_W / CANVAS_W:.1f} pt 显示 —— '
              f'说明与分析合并放两图下方')
    # 不用 bbox_inches='tight' —— 它会裁掉白边，让落盘 PNG 比 figsize 窄，
    # 插到目标宽度时反而被放大，1:1 就破了。留白靠 fig.tight_layout() 收。
    fig.savefig(path, dpi=DPI, facecolor=('white' if kind == 'A' else BG_B))
    plt.close(fig)
    from PIL import Image as _I
    _w = _I.open(path).width / DPI
    if abs(_w - want) > 0.02:
        raise SystemExit(f'[版面] {base}: 落盘宽 {_w:.2f} in ≠ {want} in，1:1 被破坏')
    print('[written]', path, f'{_w:.2f} in @ {DPI} dpi')


# ── 以下为 §3.7 / §4.3 要求补齐的函数（不改动上方已定稿部分）────────────────
from matplotlib.ticker import MultipleLocator as _ML


def yaxis(ax, ylim, ytick):
    """从 series.json 读死上下界与步长，禁用 autoscale（§3.5.1）。"""
    ax.set_ylim(*ylim)
    ax.yaxis.set_major_locator(_ML(ytick))
    ax.set_autoscaley_on(False)


def subtitle(ax, text, size=17):
    ax.text(0, 1.015, text, transform=ax.transAxes, ha='left', va='bottom',
            fontsize=size, color=NOTE_A)


def right_axis(ax2, color):
    ax2.spines['right'].set_color(color)
    ax2.spines['top'].set_visible(False)
    ax2.tick_params(axis='y', colors=color)
    ax2.yaxis.label.set_color(color)


def bar_labels(ax, xs, ys, color, fmt='{:.1f}', size=15, dy=4, bold=True):
    for x, y in zip(xs, ys):
        if y is None:
            continue
        ax.annotate(fmt.format(y), (x, y), textcoords='offset points',
                    xytext=(0, dy), ha='center', fontsize=size,
                    fontweight=('bold' if bold else 'normal'), color=color)


def stacked_labels(ax, xs, bottoms, heights, color='white', fmt='{:.1f}',
                   size=15, min_h=3.0):
    """堆叠柱段内白字 bold；薄段返回给调用方到柱外另写。"""
    thin = []
    for i, (x, b, h) in enumerate(zip(xs, bottoms, heights)):
        if h is None:
            continue
        if h < min_h:
            thin.append(i)
            continue
        ax.text(x, b + h / 2, fmt.format(h), ha='center', va='center',
                fontsize=size, fontweight='bold', color=color)
    return thin


def right_edge_labels(fig, ax, xe, ends, ylim, colors, fmt='{:.2f}',
                      size=22, dash=0.62, tick_x=0.68, val_x=1.32):
    """图 10–14 的「虚线 → ticker 粗体 → 数值列」三段式。间距按像素算。"""
    fig.canvas.draw()
    px_per_unit = ax.get_window_extent().height / (ylim[1] - ylim[0])
    gap = max((ylim[1] - ylim[0]) * 0.032,
              size * 1.25 * fig.dpi / 72 / px_per_unit)
    placed = []
    for y, tk in sorted(ends, key=lambda p: p[0]):
        yy = y if not placed else max(y, placed[-1][0] + gap)
        placed.append((yy, y, tk))
    for yy, y, tk in placed:
        c = colors[tk]
        ax.plot([xe, xe + dash], [y, yy], ls='--', lw=1.2, color=c,
                clip_on=False, zorder=4)
        ax.text(xe + tick_x, yy, tk, color=c, fontsize=size,
                fontweight='bold', va='center', ha='left', clip_on=False)
        ax.text(xe + val_x, yy, fmt.format(y), color=TEXT_A, fontsize=size,
                va='center', ha='left', clip_on=False)


def pie_labels(ax, wedges, labels, vals, size=15):
    """饼图扇区外引线标签：<行业简称> <占比1位>%"""
    for w, lb, v in zip(wedges, labels, vals):
        ang = (w.theta2 + w.theta1) / 2.0
        import math
        x, y = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        ha = 'left' if x >= 0 else 'right'
        ax.annotate(f'{lb} {v:.1f}%', xy=(x * 0.98, y * 0.98),
                    xytext=(x * 1.22, y * 1.22), ha=ha, va='center',
                    fontsize=size, color=TEXT_A,
                    arrowprops=dict(arrowstyle='-', color='#B9C0C8', lw=0.9,
                                    shrinkA=0, shrinkB=2))
