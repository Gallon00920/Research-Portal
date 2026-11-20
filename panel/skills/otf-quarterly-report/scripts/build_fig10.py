import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import chartlib as C

PERIODS = ["1Q25","2Q25","3Q25","4Q25","1Q26","2Q26"]
DATA = {   # 取自 2026Q2 版报告图 12 的读值
 'BXSL':[27.40,27.35,27.18,26.94,26.27,25.53],
 'ARCC':[19.82,19.89,20.03,19.95,19.60,19.35],
 'OTF' :[17.11,17.20,17.29,17.34,16.53,16.48],
 'TSLX':[17.09,17.18,17.22,17.00,16.24,16.24],
 'OBDC':[15.13,15.05,15.00,14.90,14.42,14.26],
 'GBDC':[15.05,15.04,15.00,14.89,14.42,14.25],
}
YLIM, YTICK = (14, 28), 2

C.use_style()
fig, ax = plt.subplots(figsize=(17.6, 10.3))
C.frame(ax); ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_color('#DCE0E5')
xs = list(range(len(PERIODS)))

for tk, ys in DATA.items():
    c = C.TICKER_COLORS[tk]
    sub = (tk == 'OTF')
    ax.plot(xs, ys, color=c, lw=(4 if sub else 2.2), marker='o',
            ms=(8 if sub else 6), zorder=(6 if sub else 3))

ax.set_ylim(*YLIM); ax.yaxis.set_major_locator(MultipleLocator(YTICK))
ax.set_xticks(xs); ax.set_xticklabels(PERIODS, fontsize=21, color='#6B7684')
ax.tick_params(axis='y', labelsize=19, colors='#6B7684', length=0)
ax.set_xlim(-0.12, len(PERIODS) - 0.88)

ax.set_title('BDC NAV per Share  |  1Q25 – 2Q26', fontsize=30,
             fontweight='bold', color=C.TITLE, loc='left', pad=44)
ax.text(0, 1.015, 'Net asset value (NAV) per share, USD at quarter end   ·   '
        'Source: company 10-Q filings and quarterly earnings releases',
        transform=ax.transAxes, ha='left', va='bottom', fontsize=17, color=C.NOTE)

# ---- 右侧三段式：末点 → 同色虚线 → ticker 粗体 → 数值列 ----
# 最小间距按像素算，不按 y 跨度百分比 —— y 跨度大的图按百分比会不够
LBL = 22
fig.canvas.draw()
px_per_unit = ax.get_window_extent().height / (YLIM[1] - YLIM[0])
gap = max((YLIM[1] - YLIM[0]) * 0.032, LBL * 1.25 * fig.dpi / 72 / px_per_unit)
ends = sorted(((ys[-1], tk) for tk, ys in DATA.items()), key=lambda p: p[0])
placed = []
for y, tk in ends:
    yy = y if not placed else max(y, placed[-1][0] + gap)
    placed.append((yy, y, tk))
xe = xs[-1]
for yy, y, tk in placed:
    c = C.TICKER_COLORS[tk]
    ax.plot([xe, xe + 0.62], [y, yy], ls='--', lw=1.2, color=c,
            clip_on=False, zorder=4)
    ax.text(xe + 0.68, yy, tk, color=c, fontsize=22, fontweight='bold',
            va='center', ha='left', clip_on=False)
    ax.text(xe + 1.32, yy, f'{y:.2f}', color=C.TEXT, fontsize=22,
            va='center', ha='left', clip_on=False)

C.footnote(fig,
    "NAV per share = total net assets divided by common shares outstanding at quarter end; each point is the reported NAV per share, not adjusted NAV per share. "
    "GBDC's fiscal year ends 9/30 and is shown here on a calendar-quarter basis. 2Q26 is the latest reported quarter, as of 6/30/2026.",
    size=17, width=138)

fig.subplots_adjust(left=0.05, right=0.855, top=0.86, bottom=0.20)
C.save(fig, 'demo_fig10_newpalette.png')
