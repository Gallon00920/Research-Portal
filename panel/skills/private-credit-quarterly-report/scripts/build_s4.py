# -*- coding: utf-8 -*-
"""§5.5 / §5.6 四张 BDC 图（Ex 26–29）。只读账本。"""
import json, io, sys
sys.path.insert(0, '.')
import matplotlib; matplotlib.use('Agg')
import matplotlib.ticker as mt
import numpy as np
import junson_style as js

D = json.load(io.open('series.json', encoding='utf-8'))
E = D['exhibits']
FS = lambda: matplotlib.rcParams['font.size']


def _xticks(ax, p, x, kind, every=None):
    st = every or max(1, -(-len(p) // (6 if kind == 'pair' else 12)))
    idx = list(range(0, len(p), st))
    if len(p) - 1 - idx[-1] >= max(2, st // 2):
        idx.append(len(p) - 1)
    else:
        idx[-1] = len(p) - 1
    ax.set_xticks([x[i] for i in idx])
    ax.set_xticklabels([p[i] for i in idx])


def _rhs(ax, ent, x, color=None, marker=False, lw=1.2, dy=-12):
    r = ent.get('rhs_line')
    if not r:
        return [], []
    vals = np.array([np.nan if q is None else float(q) for q in r['vals']])
    ax2 = js.twin_right(ax)
    color = color or js.GOLD
    ax2.plot(x, vals, color=color, lw=lw, marker='o' if marker else '',
             ms=js.ms(lw), label=r['label'])
    lo, hi = ent.get('rhs_ylim', [0, np.nanmax(vals) * 1.35])
    ax2.set_ylim(lo, hi)
    if ent.get('rhs_ytick'):
        ax2.yaxis.set_major_locator(mt.MultipleLocator(ent['rhs_ytick']))
    ax2.tick_params(labelsize=FS())
    # 冲出右轴上限被源图裁掉的段：照源图画「穿顶而出 / 穿顶而入」的两段短线（位置是量的）
    off = r.get('offscale')
    if off:
        # ⛔ Alex 2026-08-25：「你为什么不把纵坐标轴拉长一点？」
        # 原来这里照源图画「穿顶而出、再穿顶而入」两段短线 —— 那是**复刻源图的裁切瑕疵**，
        # 在我们自己重画的图上读起来像渲染 bug。改法：轴留足余量（账本 rhs_ylim 抬高），
        # 缺口不再用穿顶短线表示，而是画成**显式的断口**：两端各一个空心端点 + 缺口上方
        # 一条贴着轴顶的虚线横档 + 一行小字说明「源图在此裁切，未披露」。
        # 数值仍然是 None —— 抬轴不会把源图裁掉的数变出来，只是让缺口读作缺口。
        hi_ = ent.get('rhs_ylim', [0, 15])[1]
        ex, re_ = off['exit'], off['reenter']
        gap0, gap1 = ex['from_idx'], re_['to_idx']
        ytop = off.get('gap_band_val', hi_ * 0.965)
        ax2.plot([gap0, gap1], [ytop, ytop], color=color, lw=lw * 0.8,
                 ls=(0, (2.2, 2.2)), clip_on=True, zorder=2)
        ax2.plot([gap0, gap0], [ex['from_val'], ytop], color=color, lw=lw * 0.8,
                 ls=(0, (2.2, 2.2)), clip_on=True, zorder=2)
        ax2.plot([gap1, gap1], [re_['to_val'], ytop], color=color, lw=lw * 0.8,
                 ls=(0, (2.2, 2.2)), clip_on=True, zorder=2)
        ax2.plot([gap0, gap1], [ex['from_val'], re_['to_val']], marker='o', ls='none',
                 mfc='white', mec=color, mew=1.1, ms=js.ms(lw) * 1.15, clip_on=True, zorder=3)
        lbl = off.get('gap_label')
        if lbl:
            ax2.annotate(lbl, ((gap0 + gap1) / 2, ytop), textcoords='offset points',
                         xytext=(0, 4), ha='center', va='bottom', color=color,
                         fontsize=FS() - 0.5, annotation_clip=False, zorder=4)
    j = max(i for i in range(len(vals)) if not np.isnan(vals[i]))
    ax2.annotate(f'{vals[j]:.1f}', (x[j], vals[j]), textcoords='offset points',
                 xytext=(3, dy), ha='left', fontweight='bold', color=color,
                 fontsize=FS(), annotation_clip=False)
    ax2.set_xlim(-0.6, len(x) - 0.4 + len(x) * 0.07)
    return ax2.get_legend_handles_labels()


def lines_rhs(slug, kind, h, ylabel, dy=8, rdy=-12, every=None, fmt='{:.1f}'):
    ent = E[slug]; p = ent['periods']; x = np.arange(len(p))
    fig, ax = js.figure(kind, h=h)
    cols = [js.NAVY, js.GREYBL, js.BLUE]
    for i, (k, v) in enumerate(ent['lines'].items()):
        vv = [np.nan if q is None else float(q) for q in v]
        ax.plot(x, vv, color=cols[i], lw=1.2, marker='', label=k)
        j = max(n for n in range(len(vv)) if not np.isnan(vv[n]))
        ax.annotate(fmt.format(vv[j]), (x[j], vv[j]), textcoords='offset points',
                    xytext=(3, dy if i == 0 else -11), ha='left', fontweight='bold',
                    color=cols[i], fontsize=FS(), annotation_clip=False)
    ax.set_ylim(*ent['ylim'])
    ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    _xticks(ax, p, x, kind, every)
    ax.set_xlim(-0.6, len(p) - 0.4 + len(p) * 0.07)
    ax.set_ylabel(ylabel); js.finish(ax)
    h2, l2 = _rhs(ax, ent, x, dy=rdy)
    hs, ls = ax.get_legend_handles_labels()
    js.legend_inside(ax, hs + h2, ls + l2, ent=ent, ncol=1, slug=slug, handlelength=1.5)
    # 末点标签顶到右轴刻度上就把 x 上限往右推（实测，不是拍余量）——
    # Ex 26 的 "10.7" 被右边框和右轴刻度 "12" 切开就是这么来的
    js.fit_right(ax)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def bars_rhs(slug, kind, h, ylabel, every=None, fmt='{:.1f}', rdy=-12):
    ent = E[slug]; p = ent['periods']; x = np.arange(len(p))
    fig, ax = js.figure(kind, h=h)
    k = list(ent['stacks'])[0]
    v = np.array(ent['stacks'][k], dtype=float)
    ax.bar(x, v, color=js.NAVY, width=0.66, label=k)
    ax.annotate(fmt.format(v[-1]), (x[-1], v[-1]), textcoords='offset points',
                xytext=(0, 3), ha='center', fontweight='bold', color=js.NAVY,
                fontsize=FS())
    ax.set_ylim(*ent['ylim'])
    ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    _xticks(ax, p, x, kind, every)
    ax.set_xlim(-0.7, len(p) - 0.3 + len(p) * 0.07)
    ax.set_ylabel(ylabel); js.finish(ax)
    h2, l2 = _rhs(ax, ent, x, dy=rdy)
    hs, ls = ax.get_legend_handles_labels()
    js.legend_inside(ax, hs + h2, ls + l2, ent=ent, ncol=1, slug=slug, handlelength=1.5)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def grouped_ts(slug, kind, h, ylabel, every=None, fmt='{:.1f}', label_last=True):
    ent = E[slug]; p = ent['periods']; ks = list(ent['stacks'])
    x = np.arange(len(p)); wd = 0.8 / len(ks)
    fig, ax = js.figure(kind, h=h)
    cols = [js.NAVY, js.GOLD, js.BLUE]
    for i, k in enumerate(ks):
        xs = x + i * wd - 0.4 + wd / 2
        vs = np.array(ent['stacks'][k], dtype=float)
        ax.bar(xs, vs, width=wd * 0.9, color=cols[i], label=k)
        if label_last:
            ax.annotate(fmt.format(vs[-1]), (xs[-1], vs[-1]),
                        textcoords='offset points', xytext=(0, 3), ha='center',
                        fontweight='bold', color=cols[i], fontsize=FS() * 0.92)
    ax.set_ylim(*ent['ylim'])
    ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    _xticks(ax, p, x, kind, every)
    ax.set_ylabel(ylabel); js.finish(ax)
    ax.legend(loc='upper left', frameon=False, handlelength=1.1, ncol=2,
              labelspacing=0.2, columnspacing=1.0, borderpad=0.1)
    js.save(fig, f'charts/{slug}.png', kind=kind)


lines_rhs('cf_bdc_nonaccrual_avg', 'pair', 2.9, 'Avg nonaccrual at cost (%)', every=8,
          dy=-11, rdy=8)   # 左右两轴的末值标签会撞：navy 压下去、gold 顶上去
lines_rhs('cf_bdc_nonaccrual_pubpriv', 'pair', 2.9, 'Nonaccruals at cost (%)', every=6)
bars_rhs('cf_bdc_pik_avg', 'pair', 2.9, 'PIK / total inv. income (%)', every=3)
grouped_ts('cf_bdc_pik_pubpriv', 'pair', 2.9, 'PIK / total inv. income (%)', every=3)
print('\nEx 26–29 出完')


# ══════════ Ex 17 / Ex 18 —— 评级机构违约口径（tracker p28）══════════
def bars_simple(slug, kind, h, ylabel, every=None, fmt='{:.1f}', label_all=False):
    ent = E[slug]; p = ent['periods']; x = np.arange(len(p))
    fig, ax = js.figure(kind, h=h)
    k = list(ent['stacks'])[0]
    v = np.array(ent['stacks'][k], dtype=float)
    ax.bar(x, v, color=js.NAVY, width=0.66)
    idx = range(len(p)) if label_all else [int(np.argmax(v)), len(p) - 1]
    for i in sorted(set(idx)):
        ax.annotate(fmt.format(v[i]), (x[i], v[i]), textcoords='offset points',
                    xytext=(0, 3), ha='center', fontweight='bold', color=js.NAVY,
                    fontsize=FS() * 0.92)
    ax.set_ylim(*ent['ylim'])                       # 从 0 起 —— guards 会查
    ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    _xticks(ax, p, x, kind, every)
    ax.set_ylabel(ylabel); js.finish(ax)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def grouped_cat(slug, kind, h, ylabel, fmt='{:.1f}', wrap=None):
    """类别型分组柱（Ex 18：五个类别 × 两个时点）。"""
    ent = E[slug]
    lb = ent['labels']; ser = ent['series']; ks = list(ser)
    x = np.arange(len(lb)); wd = 0.78 / len(ks)
    fig, ax = js.figure(kind, h=h)
    cols = [js.GOLD, js.NAVY, js.BLUE]
    for i, k in enumerate(ks):
        xs = x + i * wd - 0.39 + wd / 2
        vs = np.array(ser[k], dtype=float)
        ax.bar(xs, vs, width=wd * 0.9, color=cols[i], label=k)
        for xx, vv in zip(xs, vs):
            ax.annotate(fmt.format(vv), (xx, vv), textcoords='offset points',
                        xytext=(0, 2), ha='center', fontweight='bold',
                        color=cols[i], fontsize=FS() * 0.88)
    ax.set_ylim(*ent['ylim'])
    ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    ax.set_xticks(x)
    ax.set_xticklabels([(wrap(l) if wrap else l) for l in lb])
    ax.set_ylabel(ylabel); js.finish(ax)
    ax.legend(loc='upper left', frameon=False, handlelength=1.1, ncol=2,
              labelspacing=0.2, columnspacing=1.0, borderpad=0.1)
    js.save(fig, f'charts/{slug}.png', kind=kind)


bars_simple('cf_fitch_ttm_default', 'pair', 2.9, 'TTM default rate (%)',
            every=4, label_all=False)
grouped_cat('cf_kbra_dld_default', 'pair', 2.9, 'Issuer TTM default rate (%)',
            wrap=lambda s: s.replace('Direct Lending ', 'DL\n').replace(' Loans', '\nLoans')
                            .replace(' Bonds', '\nBonds').replace('DL\nAll', 'DL\nAll'))
print('\nEx 17 / Ex 18 出完')
