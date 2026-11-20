# -*- coding: utf-8 -*-
"""Ex 9 / 23 / 25 —— 多条季度折线。只读账本。"""
import json, io, sys
sys.path.insert(0, '.')
import matplotlib; matplotlib.use('Agg')
import matplotlib.ticker as mt
import numpy as np
import junson_style as js

D = json.load(io.open('series.json', encoding='utf-8'))
E = D['exhibits']
FS = lambda: matplotlib.rcParams['font.size']


def qlines(slug, kind, h, ylabel, every=4, fmt='{:.1f}', dys=None,
           styles=('-', '-', ':'), lws=(1.3, 1.3, 1.1), ncol=1, legy=-0.50):
    ent = E[slug]; p = ent['periods']; x = np.arange(len(p))
    fig, ax = js.figure(kind, h=h)
    cols = [js.NAVY, js.GOLD, js.SLATE]
    dys = dys or [8, -12, 8]
    # 有负值的序列要画 0 基准线（回报图）—— 不画的话读者分不出正负区
    if ent.get('zero_line'):
        ax.axhline(0, color=js.LIGHTGY, lw=1.0, zorder=1)
    # 前两条线之间填浅色带 —— 基线成稿用它表示私募相对公募的溢价
    if ent.get('band_between') and len(ent['lines']) >= 2:
        _ks = list(ent['lines'])[:2]
        _a = np.array([np.nan if q is None else float(q) for q in ent['lines'][_ks[0]]])
        _b = np.array([np.nan if q is None else float(q) for q in ent['lines'][_ks[1]]])
        ax.fill_between(x, _a, _b, where=~(np.isnan(_a) | np.isnan(_b)),
                        color=js.BANDS[0], zorder=0)
    for i, (k, v) in enumerate(ent['lines'].items()):
        vv = np.array([np.nan if q is None else float(q) for q in v])
        ax.plot(x, vv, color=cols[i], lw=lws[i], ls=styles[i], marker='', label=k)
        j = max(n for n in range(len(vv)) if not np.isnan(vv[n]))
        ax.annotate(fmt.format(vv[j]), (x[j], vv[j]), textcoords='offset points',
                    xytext=(3, dys[i]), ha='left', fontweight='bold', color=cols[i],
                    fontsize=FS(), annotation_clip=False)
    ax.set_ylim(*ent['ylim'])
    ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    axc = ent.get('axis') or {}
    if axc.get('x_format') == 'YYYY/MM':
        # ⛔ 契约写死：横轴全数字 YYYY/MM，逐年 12 月一个刻度（Alex 2026-08-24）
        want = set(axc.get('x_tick_quarters') or [])
        idx = [i for i, q in enumerate(p) if q in want]
        Q2M = {'1Q': '03', '2Q': '06', '3Q': '09', '4Q': '12'}
        labs = [f'20{p[i][2:]}/{Q2M[p[i][:2]]}' for i in idx]
        ax.set_xticks([x[i] for i in idx])
        ax.set_xticklabels(labs, rotation=axc.get('rotation', 45), ha='right')
    else:
        idx = list(range(0, len(p), every))
        # 末期单独加一个刻度，但离前一个太近会压字（guards 会抓），所以留半格间距
        if len(p) - 1 - idx[-1] >= max(2, every // 2):
            idx.append(len(p) - 1)
        else:
            idx[-1] = len(p) - 1
        ax.set_xticks([x[i] for i in idx]); ax.set_xticklabels([p[i] for i in idx])
    ax.set_xlim(-0.6, len(p) - 0.4 + len(p) * 0.09)
    ax.set_ylabel(ylabel); js.finish(ax)
    js.legend_inside(ax, ent=ent, ncol=1, slug=slug)
    js.save(fig, f'charts/{slug}.png', kind=kind)


# Ex 9（Alex 2026-08-24 定稿）：MS p41 右图的两条 T12M 回报线 + ICE HY YTW 收益率线。
# 两个口径画在一张图（Alex：可以画在一起，但不是一个意思）——图例和 Note 各自写明口径。
# 前两期回报 = 0 是源图画的 0，必须画出来。末点 8.73 / 7.44 / 4.83，标签错开。
qlines('ret_dl_vs_bsl_total_return', 'tall', 4.2, 'Percent', every=4, fmt='{:.1f}%',
       dys=[9, -14, -14], styles=('-', '-', '--'), lws=(1.4, 1.4, 1.2), ncol=1, legy=-0.32)
qlines('cf_leverage_timeseries', 'pair', 2.9, 'Total leverage (x)', every=4,
       fmt='{:.1f}x', dys=[9, -12, 7])
qlines('cf_ebitda_coverage_ts', 'pair', 2.9, 'EBITDA coverage (x)', every=4,
       fmt='{:.1f}x', dys=[9, -12, 7])
print('\nEx 9 / 10 / 23 / 25 出完')


# ══════════ Ex 11 / Ex 19 ══════════
def grouped_cat2(slug, kind, h, ylabel, fmt='{:.0f}', wrap=None, ncol=3):
    ent = E[slug]
    lb = ent['labels']; ser = ent['series']; ks = list(ser)
    x = np.arange(len(lb)); wd = 0.78 / len(ks)
    fig, ax = js.figure(kind, h=h)
    cols = [js.GREYBL, js.GOLD, js.NAVY]
    for i, k in enumerate(ks):
        xs = x + i * wd - 0.39 + wd / 2
        vs = np.array(ser[k], dtype=float)
        ax.bar(xs, vs, width=wd * 0.9, color=cols[i], label=k)
        if i == len(ks) - 1:                       # 只标最新那一组，避免挤成一片
            for xx, vv in zip(xs, vs):
                ax.annotate(fmt.format(vv), (xx, vv), textcoords='offset points',
                            xytext=(0, 2), ha='center', fontweight='bold',
                            color=js.NAVY, fontsize=FS() * 0.9)
    ax.set_ylim(*ent['ylim'])
    ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    ax.set_xticks(x); ax.set_xticklabels([(wrap(l) if wrap else l) for l in lb])
    ax.set_ylabel(ylabel); js.finish(ax)
    ax.legend(loc='upper right', frameon=False, handlelength=1.1, ncol=ncol,
              labelspacing=0.2, columnspacing=1.0, borderpad=0.1)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def hbars_hl(slug, kind, h, xlabel, fmt='{:.1f}%'):
    ent = E[slug]
    lb = ent['labels']; v = ent['vals']
    fig, ax = js.figure(kind, h=h)
    y = np.arange(len(lb))[::-1]
    # ⛔ Alex 2026-08-25：三档配色，由账本字段驱动，不写死索引 ——
    #    emphasis（Total）→ C1 深藏蓝；highlight（Software）→ C3 六色里最亮的那个；
    #    其余 → C2，比 C1 浅一档。自家基金另说（HILITE）。
    # ⛔ 三档一律按**位次**取色，不写角色名 —— Alex 2026-08-25 冻结的是「Total 深蓝 /
    #    software 亮蓝 / 其余比深蓝稍浅」这个**视觉**要求。2026-08-26 换位之后角色名
    #    BLUE 已经指到蓝灰了，再用它 software 就从青绿变成蓝灰，冻结的版式就破了。
    #    写成位次：位 1 深藏蓝 / 位 2 最亮的那个 / 位 3 比位 1 浅一档 —— 换位前后同色。
    _hl = js.OWN_FUNDS[0] if ent.get('highlight_is_own_fund') else js.SERIES[1]
    _em, _hi = ent.get('emphasis'), ent.get('highlight')
    def _c(l):
        if l == _hi:
            return _hl
        if l == _em:
            return js.SERIES[0]     # 位 1 深藏蓝
        return js.SERIES[2]         # 位 3 —— 比位 1 浅一档
    cols = [_c(l) for l in lb]
    ax.barh(y, v, color=cols, height=0.68)
    for yy, vv in zip(y, v):
        ax.annotate(fmt.format(vv), (vv, yy), textcoords='offset points',
                    xytext=(3, 0), va='center', ha='left', fontweight='bold',
                    color=js.NAVY, fontsize=FS() * 0.9)
    ax.set_yticks(y); ax.set_yticklabels(lb)
    ax.set_xlim(0, max(v) * 1.16)                  # 横柱：x 从 0 起
    ax.xaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    ax.set_xlabel(xlabel)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.xaxis.grid(True, color=js.GRID, lw=0.8); ax.set_axisbelow(True)
    js.save(fig, f'charts/{slug}.png', kind=kind)


_W11 = {'EBITDA < $20m': '<$20m', 'EBITDA $20m–<$50m': '$20–50m',
        'EBITDA $50m–<$100m': '$50–100m', 'EBITDA $100m+': '$100m+',
        'Single B syndicated loans': 'Single B\nBSL'}
grouped_cat2('ret_dl_spread_by_ebitda', 'pair', 2.9, 'Spread (bp)',
             wrap=lambda s: _W11.get(s, s), ncol=3)
hbars_hl('cf_fitch_default_by_sector', 'solo', 4.4, 'LTM default rate (%)')
print('\nEx 11 / Ex 19 出完')
