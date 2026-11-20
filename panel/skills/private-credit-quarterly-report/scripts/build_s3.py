# -*- coding: utf-8 -*-
"""Ex 7 / Ex 14 —— S&P Direct Lending deck 这批。只读账本。"""
import json, io, sys
sys.path.insert(0, '.')
import matplotlib; matplotlib.use('Agg')
import matplotlib.ticker as mt
import numpy as np
import junson_style as js

D = json.load(io.open('series.json', encoding='utf-8'))
E = D['exhibits']


def bars_with_rhs_gappy(slug, kind, h, ylabel, rhs_label_fmt='{:.0f}'):
    """柱 + 右轴折线，折线允许 None 断档（Ex 7：2012–2019 无利差数据）。"""
    ent = E[slug]; p = ent['periods']
    x = np.arange(len(p))
    fig, ax = js.figure(kind, h=h)
    k = list(ent['stacks'])[0]
    v = np.array(ent['stacks'][k], dtype=float)
    ax.bar(x, v, color=js.NAVY, width=0.7, label=k)
    ax.set_ylim(*ent['ylim'])
    # 柱值标签默认放柱顶上方；但右轴那条线可能正好压在这个高度（2026Q3：2021 的 22.5
    # 被 156bps 的折线划过）。判据用**两个轴各自的归一化高度**，不写死索引 —— 下季数据
    # 一变，谁碰谁也会变。碰上就把标签改成放柱内、白字。
    _r = ent['rhs_line']
    _rv = [None if q is None else float(q) for q in _r['vals']]
    _rlo, _rhi = ent.get('rhs_ylim') or (0, max(q for q in _rv if q is not None) * 1.45)
    _ylo, _yhi = ent['ylim']
    for xx, vv, rr in zip(x, v, _rv):
        _bh = (vv - _ylo) / (_yhi - _ylo)
        _lh = None if rr is None else (rr - _rlo) / (_rhi - _rlo)
        _clash = _lh is not None and abs(_lh - _bh) < 0.085
        ax.annotate(f'{vv:,.1f}', (xx, vv), textcoords='offset points',
                    xytext=(0, -9 if _clash else 2), ha='center',
                    va='top' if _clash else 'baseline', fontweight='bold',
                    color='white' if _clash else js.NAVY,
                    fontsize=matplotlib.rcParams['font.size'] * 0.9)
    ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    ax.set_xticks(x); ax.set_xticklabels(p)
    ax.set_ylabel(ylabel); js.finish(ax)

    r = ent['rhs_line']
    vals = np.array([np.nan if q is None else float(q) for q in r['vals']])
    ax2 = js.twin_right(ax)
    ax2.plot(x, vals, color=js.GOLD, lw=1.4, marker='', label=r['label'])
    # 观测月份数：>=9 个月画实心点，<9 个月画空心点 —— 让「这年数据很稀」一眼看得见
    nobs = ent.get('aux', {}).get('spread_months_observed') or [12] * len(x)
    for i, (vv, nn) in enumerate(zip(vals, nobs)):
        if np.isnan(vv):
            continue
        full = nn >= 9
        ax2.plot([x[i]], [vv], marker='o', ms=js.ms(1.4), lw=1.4,
                 color=js.GOLD, mfc=js.GOLD if full else 'white',
                 mew=1.0, mec=js.GOLD)
    # ⛔ 右轴一律先看账本 rhs_ylim（跨季可比）；只有账本没给才退回 autoscale
    if ent.get('rhs_ylim'):
        ax2.set_ylim(*ent['rhs_ylim'])
    else:
        ax2.set_ylim(0, np.nanmax(vals) * 1.45)
    ax2.yaxis.set_major_locator(mt.MultipleLocator(ent.get('rhs_ytick') or 50))
    ax2.tick_params(labelsize=matplotlib.rcParams['font.size'])
    ax2.set_ylabel("'AAA' spread over SOFR (bps)",
                   fontsize=matplotlib.rcParams['font.size'])
    good = np.nonzero(~np.isnan(vals))[0]
    for i in (good[0], good[-1]):
        ax2.annotate(rhs_label_fmt.format(vals[i]), (x[i], vals[i]),
                     textcoords='offset points', xytext=(0, 7), ha='center',
                     fontweight='bold', color=js.GOLD,
                     fontsize=matplotlib.rcParams['font.size'],
                     annotation_clip=False)
    ax.set_xlim(-0.7, len(p) - 0.3)
    ax2.set_xlim(-0.7, len(p) - 0.3)
    hs = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
    ls = ax.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
    js.legend_inside(ax, hs, ls, ent=ent, slug=slug, handlelength=1.2,
                     labelspacing=0.25)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def long_lines(slug, kind, h, ylabel, dy=None, tick_every=None, fmt='{:.1f}'):
    """长月度序列：不画描点（太密），末值标签手工错开。"""
    ent = E[slug]; p = ent['periods']; x = np.arange(len(p))
    fig, ax = js.figure(kind, h=h)
    cols = [js.NAVY, js.BLUE, js.GOLD, js.GREYBL]
    styles = ['--', '-', '-']
    dy = dy or [8] * 4
    for i, (kk, vv) in enumerate(ent['lines'].items()):
        vals = [np.nan if q is None else float(q) for q in vv]
        ax.plot(x, vals, color=cols[i], lw=1.1, ls=styles[i % len(styles)],
                marker='', label=kk)
        j = max(n for n in range(len(vals)) if not np.isnan(vals[n]))
        ax.annotate(fmt.format(vals[j]), (x[j], vals[j]),
                    textcoords='offset points', xytext=(3, dy[i]), ha='left',
                    fontweight='bold', color=cols[i],
                    fontsize=matplotlib.rcParams['font.size'],
                    annotation_clip=False)
    ax.set_ylim(*ent['ylim'])
    ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    st = tick_every or max(1, -(-len(p) // 6))
    idx = list(range(0, len(p), st))
    if len(p) - 1 - idx[-1] >= max(2, st // 2):
        idx.append(len(p) - 1)
    else:
        idx[-1] = len(p) - 1
    ax.set_xticks([x[i] for i in idx])
    ax.set_xticklabels([p[i].replace(' 20', " '") for i in idx])
    ax.set_xlim(-1, len(p) + len(p) * 0.06)
    ax.set_ylabel(ylabel); js.finish(ax)
    js.legend_inside(ax, ent=ent, ncol=1, slug=slug)
    js.save(fig, f'charts/{slug}.png', kind=kind)


bars_with_rhs_gappy('mkt_mmclo_issuance_spread', 'solo', 2.9, 'New issuance (US$bn)')
long_lines('cf_sp_default_vs_specgrade', 'pair', 2.9, 'TTM default rate (%)',
           dy=[9, -13, -13], tick_every=18, fmt='{:.2f}')   # 4.37% 是披露明值，保两位
print('\nEx 7 / Ex 14 出完')
