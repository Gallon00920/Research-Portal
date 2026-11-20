import json, sys, math
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt
import chartlib as C

CQ  = sys.argv[1] if len(sys.argv) > 1 else None
OUT = sys.argv[2] if len(sys.argv) > 2 else 'fig05.png'
SECTOR_THRU = sys.argv[3] if len(sys.argv) > 3 else '1Q26'

d = json.load(open('series.json'))
cq = CQ or d['meta']['cq']
spec = d['charts']['fig05_pik_share']
otf, sec = spec['series']['OTF'], spec['series']['BDC_SECTOR_AVG']

# 滚动窗口：只取最后 window 期（按 series.json 里的插入顺序 = 时间顺序）
periods = C.roll(list(otf.keys()), cq, spec.get('window_max', 8))
xs   = range(len(periods))
yotf = [otf[p]['v'] for p in periods]
ysec = [sec[p]['v'] if p in sec else None for p in periods]

C.use_style('A')
fig, ax = plt.subplots(figsize=(13.7, 5.5))
C.frame(ax)

ax.plot(xs, yotf, color=C.PALETTE_A[0], lw=3, marker='o', ms=10, zorder=5)
xs_s = [x for x, y in zip(xs, ysec) if y is not None]
ys_s = [y for y in ysec if y is not None]
ax.plot(xs_s, ys_s, color=C.PALETTE_A[3], lw=2, marker='s', ms=8, zorder=4)

C.line_labels(ax, list(xs), yotf, C.PALETTE_A[0], skip_last=True)
C.highlight_last(ax, list(xs)[-1], yotf[-1])
C.line_labels(ax, xs_s, ys_s, C.PALETTE_A[3], size=17, dy=-30, bold=False)

lo, hi = min(ys_s) - 2.4, max(yotf) + 1.8
ax.set_ylim(math.floor(lo / 2) * 2, math.ceil(hi / 2) * 2)
ax.yaxis.set_major_locator(MultipleLocator(2))   # 步长写死，别让 autoscale 抖
ax.set_xticks(list(xs)); ax.set_xticklabels(periods, fontsize=19, color=C.TEXT_A)
ax.tick_params(axis='y', labelsize=15, colors=C.TEXT_A)
ax.set_ylabel('%', fontsize=15, color=C.TEXT_A)
ax.set_xlim(-0.35, len(periods) - 0.65)

C.title(ax, 'PIK income as % of total investment income', size=23)
ax.text(0.02, 0.34, f'BDC sector average — quarterly through {SECTOR_THRU}',
        transform=ax.transAxes, fontsize=18, fontweight='bold', color=C.PALETTE_A[3])

C.footnote(fig,
    f"* PIK interest + PIK dividends ÷ total investment income, single-quarter basis; year-end point = full year − nine months; each point from that period's filing. "
    f"{cq} = \\${'42.3'}mm ÷ \\${'338.0'}mm = {yotf[-1]}%. Gray series: BDC sector average PIK share of total investment income — "
    f"quarterly through {SECTOR_THRU}; no {cq} sector print yet.",
    width=150)

fig.subplots_adjust(left=0.075, right=0.66, top=0.86, bottom=0.30)
C.save(fig, OUT)
