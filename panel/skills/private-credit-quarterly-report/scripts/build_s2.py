# -*- coding: utf-8 -*-
"""§2 Market Size 出图 —— 只读账本，样式全走 junson_style。"""
import json, io, sys
sys.path.insert(0, '.')
import matplotlib; matplotlib.use('Agg')
import numpy as np
import junson_style as js
import exhibits

D = json.load(io.open('series.json', encoding='utf-8'))
E = D['exhibits']
EX = exhibits.load()


def stacked_with_rhs(slug, kind, h, ylabel, stack_keys, rhs=True, fmt='{:,.0f}',
                     label_last_only=True, rhs_fmt='{:.0f}%', label_total=True,
                     dollar_y=False, legend_loc='upper left', legend_ncol=1):
    ent = E[slug]
    p = ent['periods']
    fig, ax = js.figure(kind, h=h)
    x = np.arange(len(p))
    bottom = np.zeros(len(p))
    # ⛔ 堆叠分项按位次取色，但**位 2 是留给右轴那条线的**（GOLD = SERIES[1]）——
    #    有右轴线就跳过位 2，没有就按 1-2-3-4 顺着来。
    #    2026-08-26 换位后必须这样写：原来写死 [NAVY, BLUE, LIGHTBL, GREYBL]，
    #    换位之后那四个名字指到位 1/3/5/4，E1（没有右轴线）的第二段就轮不到刚提上来的青绿。
    _has_rhs = bool(rhs and ent.get('rhs_line'))
    colors = ([js.SERIES[0]] + js.SERIES[2:5]) if _has_rhs else js.SERIES[:4]
    for i, k in enumerate(stack_keys):
        v = np.array(ent['stacks'][k], dtype=float)
        ax.bar(x, v, bottom=bottom, color=colors[i], label=k, width=0.72)
        bottom += v
    if ent.get('ylim'):
        ax.set_ylim(*ent['ylim'])
    if ent.get('ytick'):
        ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(ent['ytick']))
    if dollar_y:
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda v, _: f'${v:,.0f}'))
    # 年度序列（标签是 4 位年份）一律每个都标，照基线；
    # 月度/季度序列才抽稀，否则 43 个月标签必压叠
    _annual = all(isinstance(v, str) and len(v) == 4 and v.isdigit() for v in p)
    if _annual or len(p) <= 16:
        step = 1
        _rot = 90 if (_annual and len(p) > 8 and kind == 'pair') else 0
    else:
        tgt = 6 if kind == 'pair' else 12
        step = max(1, -(-len(p) // tgt)); _rot = 0
    _ix = js.tick_idx(len(p), step)          # 末期一定上刻度
    ax.set_xticks([x[i] for i in _ix])
    ax.set_xticklabels([p[i] for i in _ix], rotation=_rot, ha='center')
    js.assert_last_ticked(ax, _ix[-1] + 1)   # 末期必须在刻度里
    ax.set_ylabel(ylabel)
    js.finish(ax)
    # 末柱总计标签（水平）
    idx = ([len(p) - 1] if label_last_only else range(len(p))) if label_total else []
    # ⛔ 柱值标签**延后到右轴画完之后**再画 —— 要判断「右轴那条线是否压在柱顶标签上」，
    #    必须先有 ax2 真实的 ylim（rhs_ylim 可能来自账本、可能是 0–100、也可能是 max*1.45，
    #    在这里猜会猜错：2026-08-25 就是猜成 0–100、实际是 0–800，判定全失效）。
    ax2 = None
    if rhs and ent.get('rhs_line'):
        r = ent['rhs_line']
        ax2 = js.twin_right(ax)
        vals = [v for v in r['vals']]
        import numpy as _np
        ax2.plot(x, [_np.nan if v is None else v for v in vals], color=js.GOLD,
                 lw=1.4, marker='o', ms=js.ms(1.4), label=r['label'])
        _ispct = '%' in rhs_fmt
        ax2.set_ylim(*(ent['rhs_ylim'] if ent.get('rhs_ylim') else
                (0, 100) if _ispct else
                (0, max(v for v in vals if v is not None) * 1.45)))
        if _ispct:
            ax2.yaxis.set_major_formatter(
                matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
        ax2.tick_params(labelsize=matplotlib.rcParams['font.size'])
        # 末值标签放到点的右下方外侧 —— 放在线上会被线和 marker 压住
        _li = [i for i, v in enumerate(vals) if v is not None][-1]
        _ann = ax2.annotate(rhs_fmt.format(vals[_li]), (x[_li], vals[_li]),
                            textcoords='offset points', xytext=(6, -11), ha='left',
                            fontweight='bold', color=js.GOLD,
                            fontsize=matplotlib.rcParams['font.size'],
                            annotation_clip=False)
        # ⛔ 左右留白对称：首柱左边缘在 -0.36（柱宽 0.72），所以右边界取 len-1+0.7。
        #    原来写 len(p)-0.1，右边比左边宽 0.2 个单位。
        ax2.set_xlim(-0.7, len(p) - 1 + 0.7)
        # ⛔ 末值标签越界先翻到点左边，别让 fit_right 去推轴 —— Alex 2026-08-26:
        #    「E5 …最后一根柱子到右侧 y 轴的距离太宽了」，就是推轴推出来的。
        _seg = (None if _li == 0 or vals[_li - 1] is None
                else vals[_li] - vals[_li - 1])
        js.flip_if_overflow(_ann, ax, last_seg=_seg)
        hs = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
        ls = ax.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
        if legend_loc == 'below':
            js.legend_inside(ax, hs, ls, ent=ent, ncol=legend_ncol or 1, slug=slug,
                             columnspacing=1.0)
        else:
            # ⛔ 不许 frameon=False：这几张图的右轴折线从图例文字后面穿过去，
            #    没有底色的话 "Dry powder as % of NAV (rs)"、"Refi" 都被线划掉一道
            #    （2026-08-25 实测 mkt_inst_aum_decomp / mkt_dl_origination）。
            #    legend_inside 给 82% 白底，位置仍然用这里指定的 legend_loc。
            # ⛔ 图例必须挂在 **ax2** 上：twin 轴是后画的一层，右轴那条折线
            #    永远盖在 ax 的图例上面（zorder 管不了跨 Axes 的绘制顺序）。
            #    挂 ax 的那一版，"Dry powder as % of NAV (rs)" 和 "Refi" 都被折线划了
            #    一道（2026-08-25 实测）。挂 ax2 之后 82% 白底才真的挡住线。
            js.legend_inside(ax, hs, ls, ent=ent, ncol=legend_ncol or 1, slug=slug,
                             loc=legend_loc, labelspacing=0.25)
    else:
        js.legend_inside(ax, ent=ent, ncol=legend_ncol or 1, slug=slug,
                         loc=legend_loc, labelspacing=0.25, columnspacing=1.1)
    # ── 柱值标签（此时 ax2 的 ylim 已定）───────────────────────────
    _idx = list(idx)
    if _idx:
        _rv = ent['rhs_line']['vals'] if ax2 is not None else None
        # ⛔ Alex 2026-08-26：「每一个数 如果是估算的那就在数的前面加个 ~，严谨一点。」
        #    哪些期是估算的由**账本** estimated_periods 说了算，脚本只读不判 ——
        #    换季某一年拿到明值就从名单里删掉那一年，不用改这里。
        _est = set(ent.get('estimated_periods') or [])
        _lab = [('~' if p[i] in _est else '') + fmt.format(bottom[i]) for i in _idx]
        js.place_bar_labels(ax, [x[i] for i in _idx], [bottom[i] for i in _idx], _lab,
                            ax2=ax2,
                            rhs_vals=[(_rv[i] if _rv else None) for i in _idx])
    # 末点标签顶到右轴刻度上就把 x 上限往右推（实测，不是拍余量）——
    # Ex 26 的 "10.7" 被右边框和右轴刻度 "12" 切开就是这么来的
    js.fit_right(ax)
    js.save(fig, f'charts/{slug}.png', kind=kind)


# Exhibit 1 —— 单图满宽
stacked_with_rhs('mkt_aum_by_channel', 'solo', 3.1, '',
                 ['Institutional', 'Retail', 'Insurance estimate'], rhs=False,
                 label_last_only=False, dollar_y=True,
                 legend_loc='upper left', legend_ncol=3)

# Exhibit 3 / 4 —— 并排
stacked_with_rhs('mkt_inst_aum_decomp', 'pair', 2.5, '',
                 ['Dry powder', 'NAV'], rhs=True, label_total=False, dollar_y=True)
stacked_with_rhs('mkt_fundraising', 'pair', 2.5, '',
                 ['Capital raised'], rhs=True, rhs_fmt='{:.0f}',
                 label_last_only=False)
print('\n§2.1–2.2 三张图出完')


# ══════════════ 追加：Ex 2 / 5 / 6 / 10 / 12 / 31 ══════════════
import matplotlib.ticker as mt


def two_panel_pie(slug, h=2.9):
    ent = E[slug]
    fig, axes = matplotlib.pyplot.subplots(1, 2, figsize=(js.CANVAS['solo'], h))
    fig.patch.set_facecolor('white')
    js.apply('solo')
    cols = [js.NAVY, js.BLUE, js.LIGHTBL, js.GREYBL, js.SLATE]
    # 左盘的标签带美元金额（基线是 "$1.5tn, 35%"，第一版只剩百分比）
    for ax, (labels, vals, title, vlab) in zip(axes, [
            (ent['labels'], ent['vals'], 'By market', ent.get('val_labels')),
            (ent['panels']['right']['labels'], ent['panels']['right']['vals'],
             ent['panels']['right']['title'], None)]):
        w, _ = ax.pie(vals, colors=cols[:len(vals)], startangle=90,
                      counterclock=False, wedgeprops=dict(width=0.42, edgecolor='white'))
        ax.set_title(title, fontsize=js.FS['solo']['axis'], color=js.NAVY, pad=4)
        # 标签放环外 + 引线 —— 放环内会被楔形边缘裁掉
        for k_, (wg, lb, v) in enumerate(zip(w, labels, vals)):
            ang = np.deg2rad((wg.theta1 + wg.theta2) / 2)
            x0, y0 = 0.98 * np.cos(ang), 0.98 * np.sin(ang)
            x1, y1 = 1.16 * np.cos(ang), 1.16 * np.sin(ang)
            ha = 'left' if x1 >= 0 else 'right'
            ax.plot([x0, x1], [y0, y1], color=js.GREYBL, lw=0.6)
            # 带金额的标签换成两行 —— 一行会顶出画布（基线也是两行）
            _t = (lb + '\n' + vlab[k_]) if (vlab and k_ < len(vlab)) else f'{lb}  {v}%'
            ax.annotate(_t, (x1, y1),
                        xytext=(3 if x1 >= 0 else -3, 0), textcoords='offset points',
                        ha=ha, va='center', fontsize=js.FS['solo']['label'],
                        color=js.NAVY, fontweight='bold', annotation_clip=False)
        ax.set_xlim(-2.15, 2.15); ax.set_ylim(-1.5, 1.5)
    js.save(fig, f'charts/{slug}.png', kind='solo')


def lines(slug, kind, h, ylabel, rhs_key=None, fmt='{:,.0f}', step=None):
    ent = E[slug]
    p = ent['periods']; x = np.arange(len(p))
    fig, ax = js.figure(kind, h=h)
    cols = [js.NAVY, js.BLUE, js.GOLD, js.GREYBL]
    keys = [k for k in ent['lines'] if k != rhs_key]
    for i, k in enumerate(keys):
        v = ent['lines'][k]
        ax.plot(x, v, color=cols[i], lw=1.4, marker='o', ms=js.ms(1.4), label=k)
        ax.annotate(fmt.format(v[-1]), (x[-1], v[-1]), textcoords='offset points',
                    xytext=(4, 7), ha='left', fontweight='bold', color=cols[i],
                    fontsize=matplotlib.rcParams['font.size'], annotation_clip=False)
    if ent.get('ylim'): ax.set_ylim(*ent['ylim'])
    if ent.get('ytick'): ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    st = step or (max(1, len(p)//6) if kind == 'pair' else max(1, len(p)//10))
    _ix = js.tick_idx(len(p), st)
    ax.set_xticks([x[i] for i in _ix]); ax.set_xticklabels([p[i] for i in _ix])
    js.assert_last_ticked(ax, _ix[-1] + 1)   # 末期必须在刻度里
    ax.set_xlim(-0.5, len(p) - 0.5 + len(p)*0.10)
    ax.set_ylabel(ylabel); js.finish(ax)
    hs, ls = ax.get_legend_handles_labels()
    if ent.get('rhs_line'):
        r = ent['rhs_line']; ax2 = js.twin_right(ax)
        ax2.plot(x, r['vals'], color=js.GOLD, lw=1.2, marker='o', ms=js.ms(1.2),
                 label=r['label'])
        ax2.set_ylim(*(ent['rhs_ylim'] if ent.get('rhs_ylim') else (0, max(r['vals']) * 1.35)))
        ax2.tick_params(labelsize=matplotlib.rcParams['font.size'])
        ax2.annotate(f"{r['vals'][-1]:,.0f}", (x[-1], r['vals'][-1]),
                     textcoords='offset points', xytext=(4, -12), ha='left',
                     fontweight='bold', color=js.GOLD,
                     fontsize=matplotlib.rcParams['font.size'], annotation_clip=False)
        h2, l2 = ax2.get_legend_handles_labels(); hs += h2; ls += l2
    # 图例放下方图外，避免压住折线
    js.legend_inside(ax, hs, ls, ent=ent, ncol=1, slug=slug)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def hbars(slug, kind, h, xlabel, fmt='{:.0f}%'):
    ent = E[slug]
    lb = ent['labels']; v = ent['vals']
    fig, ax = js.figure(kind, h=h)
    y = np.arange(len(lb))[::-1]
    # HILITE 那个红只留给 Junson 自己的基金（OTF 规矩，见 style-guide）。
    # 这里高亮的是行业/均值行之类，用金色。
    hl = js.OWN_FUNDS[0] if ent.get('highlight_is_own_fund') else js.GOLD
    cols = [hl if l == ent.get('highlight') else js.NAVY for l in lb]
    ax.barh(y, v, color=cols, height=0.62)
    for yy, vv in zip(y, v):
        ax.annotate(fmt.format(vv), (vv, yy), textcoords='offset points',
                    xytext=(3, 0), va='center', ha='left', fontweight='bold',
                    color=js.NAVY, fontsize=matplotlib.rcParams['font.size'])
    ax.set_yticks(y); ax.set_yticklabels(lb)
    ax.set_xlim(0, max(v) * 1.22); ax.set_xlabel(xlabel)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    ax.xaxis.grid(True, color=js.GRID, lw=0.8); ax.set_axisbelow(True)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def grouped_bars(slug, kind, h, ylabel, fmt='{:,.0f}', label_all=False, label_last=False):
    ent = E[slug]
    p = ent['periods']; ks = list(ent['stacks'])
    x = np.arange(len(p)); wd = 0.8 / len(ks)
    fig, ax = js.figure(kind, h=h)
    cols = [js.GREYBL, js.NAVY, js.BLUE]
    for i, k in enumerate(ks):
        xs = x + i*wd - 0.4 + wd/2
        vs = ent['stacks'][k]
        ax.bar(xs, vs, width=wd*0.92, color=cols[i], label=k)
        if label_all:
            for xx, vv in zip(xs, vs):
                ax.annotate(fmt.format(vv), (xx, vv), textcoords='offset points',
                            xytext=(0, 2), ha='center', fontweight='bold',
                            color=js.NAVY, fontsize=matplotlib.rcParams['font.size']*0.92)
        elif label_last and i == len(ks) - 1:
            ax.annotate(fmt.format(vs[-1]), (xs[-1], vs[-1]), textcoords='offset points',
                        xytext=(0, 3), ha='center', fontweight='bold', color=js.NAVY,
                        fontsize=matplotlib.rcParams['font.size'])
    if ent.get('ylim'): ax.set_ylim(*ent['ylim'])
    if ent.get('ytick'): ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    ax.set_xticks(x); ax.set_xticklabels(p)
    ax.set_ylabel(ylabel); js.finish(ax)
    ax.legend(loc='upper left', frameon=False, handlelength=1.2, labelspacing=0.25,
              borderpad=0.1)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def grouped_with_rhs(slug, kind, h, ylabel, rhs_fmt='{:.0f}%', tgt=None):
    """分组柱 + 右轴折线。x 轴标签按画布宽度抽稀 —— 29 个季度全标必压叠。"""
    ent = E[slug]
    p = ent['periods']; ks = list(ent['stacks'])
    x = np.arange(len(p)); wd = 0.8 / len(ks)
    fig, ax = js.figure(kind, h=h)
    cols = [js.BLUE, js.GOLD, js.LIGHTBL]
    for i, k in enumerate(ks):
        ax.bar(x + i*wd - 0.4 + wd/2, ent['stacks'][k], width=wd*0.92,
               color=cols[i], label=k)
    # ⛔ y 轴冻结:账本给了 ylim 就用它,不许 autoscale 覆盖(早前这里先设后覆盖,等于没冻)
    if ent.get('ylim'):
        ax.set_ylim(*ent['ylim'])
    else:
        ax.set_ylim(0, max(max(v) for v in ent['stacks'].values()) * 1.28)   # 给图例留头
    n = tgt or (6 if kind == 'pair' else 12)
    step = max(1, -(-len(p) // n))
    _ix = js.tick_idx(len(p), step)
    ax.set_xticks([x[i] for i in _ix]); ax.set_xticklabels([p[i] for i in _ix])
    js.assert_last_ticked(ax, _ix[-1] + 1)   # 末期必须在刻度里
    ax.set_ylabel(ylabel)
    js.finish(ax)
    h1, l1 = ax.get_legend_handles_labels()
    if ent.get('rhs_line'):
        r = ent['rhs_line']
        ax2 = js.twin_right(ax)
        vs = r['vals']
        ax2.plot(x, [np.nan if v is None else v for v in vs], color=js.SLATE,
                 lw=1.4, marker='^', ms=js.ms(1.4), label=r['label'])
        ax2.set_ylim(0, 105)
        ax2.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: rhs_fmt.format(v)))
        ax2.tick_params(labelsize=matplotlib.rcParams['font.size'])
        ax2.set_xlim(-0.7, len(p) - 0.3)
        last = [i for i, v in enumerate(vs) if v is not None][-1]
        ax2.annotate(rhs_fmt.format(vs[last]), (x[last], vs[last]),
                     textcoords='offset points', xytext=(-4, 5), ha='right',
                     fontweight='bold', color=js.SLATE,
                     fontsize=matplotlib.rcParams['font.size'])
        h2, l2 = ax2.get_legend_handles_labels()
        h1 += h2; l1 += l2
    js.legend_inside(ax, h1, l1, ent=ent, slug=slug, handlelength=1.1,
                     labelspacing=0.2, fontsize=matplotlib.rcParams['font.size'] * 0.95)
    js.save(fig, f'charts/{slug}.png', kind=kind)


import matplotlib.pyplot
two_panel_pie('mkt_us_levcredit_split', h=2.9)
# Ex 5：框架口径 —— 月度 refi / non-refi 堆叠 + % non-refi 三月均线（右轴）
stacked_with_rhs('mkt_dl_origination', 'pair', 2.5, 'US$bn',
                 ['Refi', 'Non-refi'], rhs=True, rhs_fmt='{:.0f}%',
                 label_total=False, dollar_y=True,
                 legend_loc='below', legend_ncol=3)
# Ex 6：框架口径 —— BSL vs 私募的 LBO 笔数分组柱 + % 私募 LTM 折线（右轴）
grouped_with_rhs('mkt_lbo_bsl_vs_private', 'pair', 2.5, 'LBO count')
# Ex 10：框架口径 —— 月度 rolling-90d，43 个月，标签每 6 个月一个（照源图）
lines('ret_dl_spread_vs_bsl', 'pair', 2.5, 'bps', fmt='{:,.0f}', step=6)
# Ex 12 改为 groups_stacked（见文件末尾）—— 这里原先误画的是 LCD 问卷
# Ex 31 与侧栏并排（无框 1×2），所以画布必须是 pair 宽 —— 1:1 锁会拦 solo 缩插
grouped_bars('tws_extra_exhibit', 'pair', 2.5, 'US$bn', label_all=False, label_last=True)
print('\n追加六张出完')


# ══════════ 评级带定位图（Ex 22 / 24）══════════
def band_chart(slug, kind='pair', h=2.9):
    """评级带定位图 —— 纵向是**连续刻度**（杠杆/覆盖倍数），菱形按数值定位。

    2026-08-24 复核源图（tracker p22）后改的：源图纵向是数值刻度，带子只是底色；
    第一版把菱形按「第几条带」放，丢了「高度 = 倍数」。scale 的标定见账本 scale._src。
    """
    ent = E[slug]
    sc = ent['scale']
    vmax = sc['vmax']; edges = sc['band_edges']       # 从图顶那条带的结束值起，共 3 条界
    low_top = sc['direction'] == 'low_top'
    fig, ax = js.figure(kind, h=h)
    fs = matplotlib.rcParams['font.size']
    # 带区间（数值域，图顶带在前）
    cuts = [0] + list(edges) + [vmax] if low_top else [vmax] + list(edges) + [0]
    for i, name in enumerate(ent['bands']):
        a, b = cuts[i], cuts[i + 1]
        ax.axhspan(min(a, b), max(a, b), color=js.BANDS[i], zorder=0)
        # 带名放各自带的靠上位置
        ytxt = (min(a, b) + 0.18 * abs(b - a)) if not low_top else (min(a, b) + 0.82 * abs(b - a))
        ax.text(0.02, ytxt, name, fontsize=fs, color=js.NAVY, va='center', zorder=3)
    for it in ent['items']:
        y = it['y']
        ax.scatter([it['x']], [y], marker='D', s=26, color=js.NAVY, zorder=5)
        ha = it.get('ha')
        if ha:
            dx = 7 if ha == 'left' else -7
            ax.annotate(it['label'], (it['x'], y), textcoords='offset points',
                        xytext=(dx, 0), ha=ha, va='center', fontweight='bold',
                        color=js.NAVY, fontsize=fs, zorder=5, annotation_clip=False)
        else:
            up = it.get('dy', -1) > 0
            ax.annotate(it['label'], (it['x'], y), textcoords='offset points',
                        xytext=(0, 8 if up else -8), ha='center',
                        va='bottom' if up else 'top', fontweight='bold',
                        color=js.NAVY, fontsize=fs, zorder=5)
    ax.set_xlim(0, 1.0)
    ax.set_ylim((vmax, 0) if low_top else (0, vmax))   # low_top：数值 0 在图顶
    ax.set_xticks([]); ax.set_yticks([])
    for s_ in ax.spines.values():
        s_.set_visible(False)
    ytop, ybot = (0, vmax) if low_top else (vmax, 0)
    ax.annotate('', xy=(-0.03, ytop), xytext=(-0.03, ybot),
                arrowprops=dict(arrowstyle='<->', color=js.GREYBL, lw=0.8),
                annotation_clip=False)
    ax.text(-0.05, ytop, ent.get('axis_top', 'Low'), fontsize=fs,
            color=js.GRAY, ha='right', va='top')
    ax.text(-0.05, ybot, ent.get('axis_bottom', 'High'), fontsize=fs,
            color=js.GRAY, ha='right', va='bottom')
    js.save(fig, f'charts/{slug}.png', kind=kind)


band_chart('cf_leverage_band')
band_chart('cf_icr_band')
def vbars_hl(slug, kind, h, ylabel, fmt='{:.1f}'):
    """竖版分类柱 + 单根高亮。

    ⛔ Alex 2026-08-25：「Exhibit 21 的图要竖着，像同事报告里的 E21 一样。」
    版式照同事那版（8 个行业在横轴、标签两行折断并旋转、柱值标在柱顶上方、纵轴 0–80/10）；
    配色走我们自己的六色：其余 C1、高亮 C3。标签折行文本从账本 `label_wrap` 读，
    不在脚本里写死行业名 —— 下季行业集合会变。
    """
    ent = E[slug]
    # ⛔ 形状由账本定死，出图函数反过来校验 —— 原来「竖着」只体现在这里调了 vbars_hl，
    #    账本上没有痕迹，改一行调用就悄悄横过去了，而且没有任何检查会发现。
    if ent.get('chart_form') != 'vbars':
        raise SystemExit(f"✗ {slug}: 账本 chart_form={ent.get('chart_form')!r}，"
                         f"但这里走的是竖版 vbars_hl()。形状是记住的版式，"
                         f"要改先改账本（Alex 2026-08-25：「E21 的图要竖着」）。")
    lb = ent['labels']; v = np.array(ent['vals'], dtype=float)
    wrap = ent.get('label_wrap') or {}
    fig, ax = js.figure(kind, h=h)
    x = np.arange(len(lb))
    hi = ent.get('highlight')
    cols = [(js.BLUE if l == hi else js.NAVY) for l in lb]      # BLUE = C3 #2EA69F
    ax.bar(x, v, color=cols, width=0.62)
    ax.set_ylim(*(ent['ylim'] if ent.get('ylim') else (0, v.max() * 1.18)))
    if ent.get('ytick'):
        ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(ent['ytick']))
    for xx, vv in zip(x, v):
        ax.annotate(fmt.format(vv), (xx, vv), textcoords='offset points',
                    xytext=(0, 3), ha='center', va='bottom', fontweight='bold',
                    color=js.NAVY, fontsize=matplotlib.rcParams['font.size'] * 0.9)
    ax.set_xticks(x)
    _rot = ent.get('label_rotation', 45)
    ax.set_xticklabels([wrap.get(l, l) for l in lb], rotation=_rot,
                       ha='center' if _rot == 90 else 'right')
    ax.set_ylabel(ylabel)
    ax.set_xlim(-0.7, len(lb) - 0.3)
    js.finish(ax)
    js.save(fig, f'charts/{slug}.png', kind=kind)


vbars_hl('cf_recovery_by_sector', 'pair', 3.0, 'Implied recovery (pt)', fmt='{:.1f}')
print('\n评级带两张 + 回收率分行业出完')


# ══════════ slide 33：契约结构 + PIK toggle（分组图）══════════
def groups_stacked(slug, kind='pair', h=2.9, pct=True):
    """分组 100% 堆叠：groups × periods 展平成一排柱子，段名放轴下。"""
    ent = E[slug]
    gs, ps = ent['groups'], ent['periods']
    ng, np_ = len(gs), len(ps)
    ks = list(ent['stacks'])
    fig, ax = js.figure(kind, h=h)
    # 组间留一格空隙
    xs = np.concatenate([np.arange(np_) + g * (np_ + 0.9) for g in range(ng)])
    bottom = np.zeros(len(xs))
    cols = [js.NAVY, js.BANDS[1]]
    for i, k in enumerate(ks):
        v = np.array(ent['stacks'][k], dtype=float)
        ax.bar(xs, v, bottom=bottom, color=cols[i % len(cols)], label=k, width=0.66)
        bottom += v
    ax.set_ylim(*ent.get('ylim', [0, 100]))
    ax.yaxis.set_major_locator(mt.MultipleLocator(ent.get('ytick', 20)))
    if pct:
        ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    ax.set_xticks(xs)
    ax.set_xticklabels([f"’{p[-2:]}" for p in ps] * ng)
    ax.set_xlim(xs[0] - 0.75, xs[-1] + 0.75)
    js.finish(ax)
    # 段名：放在年份刻度下面一行
    fs = matplotlib.rcParams['font.size']
    for g, name in enumerate(gs):
        cx = xs[g * np_ : (g + 1) * np_].mean()
        ax.annotate(name.replace(' Middle Market', ' MM'), (cx, 0),
                    xytext=(0, -18), textcoords='offset points', ha='center',
                    va='top', fontsize=fs, color=js.NAVY, fontweight='bold',
                    annotation_clip=False)
    js.legend_inside(ax, ent=ent, ncol=1, slug=slug)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def groups_bars(slug, kind='pair', h=2.9, fmt='{:.0f}%', pct=True):
    """分组柱：x = groups，组内一根柱对应一个 series（年份）。None = 未披露，不画柱。"""
    ent = E[slug]
    gs = ent['groups']; ser = ent['series']; ks = list(ser)
    x = np.arange(len(gs)); wd = 0.82 / len(ks)
    fig, ax = js.figure(kind, h=h)
    cols = [js.NAVY, js.GOLD, js.SLATE, js.BLUE]
    fs = matplotlib.rcParams['font.size']
    for i, k in enumerate(ks):
        xs = x + i * wd - 0.41 + wd / 2
        vs = [np.nan if v is None else float(v) for v in ser[k]]
        ax.bar(xs, vs, width=wd * 0.9, color=cols[i % len(cols)], label=k)
        for xx, vv in zip(xs, vs):
            if np.isnan(vv):
                continue
            ax.annotate(fmt.format(vv), (xx, vv), textcoords='offset points',
                        xytext=(0, 2), ha='center', fontweight='bold',
                        color=js.NAVY, fontsize=fs * 0.92)
    ax.set_ylim(*ent.get('ylim', [0, 45]))
    ax.yaxis.set_major_locator(mt.MultipleLocator(ent.get('ytick', 5)))
    if pct:
        ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    ax.set_xticks(x)
    ax.set_xticklabels([g.replace(' Middle Market', '\nMM') for g in gs])
    js.finish(ax)
    ax.legend(loc='upper left', frameon=False, handlelength=1.1, ncol=2,
              labelspacing=0.2, columnspacing=1.0, borderpad=0.1)
    js.save(fig, f'charts/{slug}.png', kind=kind)


groups_stacked('prc_covenants_by_vintage', 'pair', 2.9)
groups_bars('prc_pik_toggle_share', 'pair', 2.9)
print('\nslide 33 两张出完')
