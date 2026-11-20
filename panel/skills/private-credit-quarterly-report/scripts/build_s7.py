# -*- coding: utf-8 -*-
"""Ex 15 / 20 + §8 基金侧图。只读账本。

`shares` 的画法规则：切片 ≤5 用圆环（和研报原图一致、也读得清）；
>5 改成横条并按占比降序 —— 3.35in 画布上放 9–13 个圆环标签必然重叠，
guards 会直接抛错，不如一开始就换成横条。
"""
import json, io, sys
sys.path.insert(0, '.')
import matplotlib; matplotlib.use('Agg')
import matplotlib.ticker as mt
import numpy as np
import junson_style as js

# ⛔ 三只自家基金同图出现，颜色必须互不相同 —— 一律走 js.OWN_FUNDS（palette 里有断言）。
OWN = js.OWN_FUNDS

D = json.load(io.open('series.json', encoding='utf-8'))
E = D['exhibits']
FS = lambda: matplotlib.rcParams['font.size']
DONUT_MAX = 5
DONUT_MIN_SLICE = 8.0   # 有小于这个占比的切片就别画圆环 —— 相邻小扇形的引线标签会撞


def pie_chart(slug, kind, h, unit='%'):
    """强制饼图 —— ⛔ Alex 2026-08-25：「E32 和 E33 都必须是饼图」「E43 必须是饼图」。

    形态由账本 `chart_form` 定死，不由数据启发式（DONUT_MAX / DONUT_MIN_SLICE）决定：
    框架说是饼图就是饼图，切片再小也是饼图（铁律五：口径由框架定死）。
    小切片不在扇形里写字（写不下、会互相压），一律进图例：图例项写 `标签 62%`。
    """
    ent = E[slug]
    lb = list(ent['labels']); v = np.array(ent['vals'], dtype=float)
    fig, ax = js.figure(kind, h=h)
    # 切片超过 6 个：Alex 2026-08-25 允许「用六色的淡化版」——
    # js.series_ext() 沿这六色向白混（52% / 76% 两档），⛔ 不引入新色相、不循环。
    # 之前用 PIE_OTHER 中性灰兜底，9 个切片时最后三块全一样，看不出区别（实测）。
    cols = js.series_ext(len(lb))
    # 饼靠右、图例靠左，两边都不挤 —— 饼半径给到 0.72，圆心右移
    w, _ = ax.pie(v, colors=cols, startangle=90, counterclock=False,
                  radius=0.72, center=(0.42, 0.0),
                  wedgeprops=dict(edgecolor='white', linewidth=0.8))
    ax.set_aspect('equal')
    ax.set_xlim(-1.15, 1.18); ax.set_ylim(-0.80, 0.80)
    fmt = '{:.0f}' if float(np.max(v)) >= 10 and all(float(x) == int(x) for x in v) else '{:.1f}'
    labs = [f'{l}  {fmt.format(x)}{unit}' for l, x in zip(lb, v)]
    ax.legend(w, labs, loc='center left', bbox_to_anchor=(-0.02, 0.5),
              frameon=False, handlelength=1.0, labelspacing=0.30, borderpad=0.0,
              fontsize=matplotlib.rcParams['font.size'] * 0.92)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def vbars_share(slug, kind, h, ylabel=None, unit='%'):
    """强制竖版柱 —— ⛔ Alex 2026-08-25：「E35 的柱状图必须竖着」。"""
    ent = E[slug]
    lb = list(ent['labels']); v = np.array(ent['vals'], dtype=float)
    wrap = ent.get('label_wrap') or {}
    fig, ax = js.figure(kind, h=h)
    x = np.arange(len(lb))
    ax.bar(x, v, color=js.NAVY, width=0.66)
    ax.set_ylim(*(ent['ylim'] if ent.get('ylim') else (0, v.max() * 1.20)))
    if ent.get('ytick'):
        ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    for xx, vv in zip(x, v):
        ax.annotate(f'{vv:.0f}{unit}' if vv == int(vv) else f'{vv:.1f}{unit}',
                    (xx, vv), textcoords='offset points', xytext=(0, 2), ha='center',
                    va='bottom', fontweight='bold', color=js.NAVY,
                    fontsize=matplotlib.rcParams['font.size'] * 0.88)
    ax.set_xticks(x)
    ax.set_xticklabels([wrap.get(l, l) for l in lb],
                       rotation=ent.get('label_rotation', 90),
                       ha='center' if ent.get('label_rotation', 90) == 90 else 'right')
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.set_xlim(-0.7, len(lb) - 0.3)
    js.finish(ax)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def shares(slug, kind, h, unit='%'):
    # ⛔ 形态优先看账本 chart_form（框架定死的那几张），再退回数据启发式
    _f = E[slug].get('chart_form')
    if _f == 'pie':
        return pie_chart(slug, kind, h, unit=unit)
    if _f == 'vbars':
        return vbars_share(slug, kind, h, unit=unit)
    ent = E[slug]
    def _resid(l):
        return l.lower().startswith(('other', 'others'))
    pairs = sorted(zip(ent['labels'], ent['vals']),
                   key=lambda kv: (_resid(kv[0]), -kv[1]))
    lb = [k for k, _ in pairs]; vs = [v for _, v in pairs]
    fig, ax = js.figure(kind, h=h)
    cols = [js.NAVY, js.BLUE, js.LIGHTBL, js.GREYBL, js.SLATE, js.GOLD,
            js.ROSE, js.LIGHTGY, js.RHS, js.BANDS[1], js.BANDS[2], js.MAROON, js.GRAY]
    if len(vs) <= DONUT_MAX and min(vs) >= DONUT_MIN_SLICE:
        w, _ = ax.pie(vs, colors=cols[:len(vs)], startangle=90, counterclock=False,
                      wedgeprops=dict(width=0.44, edgecolor='white'))
        for wg, l, v in zip(w, lb, vs):
            ang = np.deg2rad((wg.theta1 + wg.theta2) / 2)
            x0, y0 = 0.99 * np.cos(ang), 0.99 * np.sin(ang)
            x1, y1 = 1.26 * np.cos(ang), 1.26 * np.sin(ang)
            ha = 'left' if x1 >= 0 else 'right'
            ax.plot([x0, x1], [y0, y1], color=js.GREYBL, lw=0.6)
            _vl = (ent.get('val_labels') or {})
            _txt = (_vl[ent['labels'].index(l)] if isinstance(_vl, list) and l in ent['labels']
                    else f'{v:g}{unit}')
            ax.annotate(f'{l}  {_txt}', (x1, y1),
                        xytext=(3 if x1 >= 0 else -3, 0), textcoords='offset points',
                        ha=ha, va='center', fontsize=FS(), color=js.NAVY,
                        fontweight='bold', annotation_clip=False)
        ax.set_xlim(-2.0, 2.0); ax.set_ylim(-1.35, 1.35)
    else:
        y = np.arange(len(lb))[::-1]
        # highlight：账本点名的类别用金色（基线在 Ex 39 高亮两条 software）
        hl = set(ent.get('highlight') or [])
        bcols = [js.GOLD if l in hl else js.NAVY for l in lb]
        ax.barh(y, vs, color=bcols, height=0.66)
        for yy, vv, ll in zip(y, vs, lb):
            ax.annotate(f'{vv:g}{unit}', (vv, yy), textcoords='offset points',
                        xytext=(3, 0), va='center', ha='left', fontweight='bold',
                        color=js.GOLD if ll in hl else js.NAVY, fontsize=FS() * 0.95)
        ax.set_yticks(y); ax.set_yticklabels(lb)
        ax.set_xlim(0, max(vs) * 1.20)
        for s_ in ('top', 'right'):
            ax.spines[s_].set_visible(False)
        ax.xaxis.grid(True, color=js.GRID, lw=0.8); ax.set_axisbelow(True)
        ax.set_xlabel(f'Share of total ({unit})')
    js.save(fig, f'charts/{slug}.png', kind=kind)


def cat_vbars(slug, kind, h, ylabel, fmt='{:.0f}', hline=None, hlabel=None):
    """分类竖柱（带可选水平参考线）—— ⛔ Alex 2026-08-25：「E44 的条形图必须竖着」。

    形态由账本 `chart_form: vbars` 定死。参考线从横线改成水平线（原来是竖版图里的 vline）。
    标签折行/旋转从账本 `label_wrap` / `label_rotation` 读，不在脚本里写死项目名。
    """
    ent = E[slug]
    lb = list(ent['labels']); v = np.array(ent['vals'], dtype=float)
    wrap = ent.get('label_wrap') or {}
    fig, ax = js.figure(kind, h=h)
    x = np.arange(len(lb))
    ax.bar(x, v, color=js.NAVY, width=0.64)
    ax.set_ylim(*(ent['ylim'] if ent.get('ylim') else (0, v.max() * 1.22)))
    if ent.get('ytick'):
        ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    for xx, vv in zip(x, v):
        ax.annotate(fmt.format(vv), (xx, vv), textcoords='offset points', xytext=(0, 2),
                    ha='center', va='bottom', fontweight='bold', color=js.NAVY,
                    fontsize=matplotlib.rcParams['font.size'] * 0.85)
    if hline is not None:
        ax.axhline(hline, color=js.BLUE, lw=1.1, ls='--', zorder=3)
        ax.annotate(hlabel or f'{hline:.1f}', (len(lb) - 0.5, hline),
                    textcoords='offset points', xytext=(-2, 3), ha='right', va='bottom',
                    color=js.BLUE, fontsize=matplotlib.rcParams['font.size'] * 0.85)
    ax.set_xticks(x)
    ax.set_xticklabels([wrap.get(l, l) for l in lb],
                       rotation=ent.get('label_rotation', 90),
                       ha='center' if ent.get('label_rotation', 90) == 90 else 'right')
    ax.set_ylabel(ylabel)
    ax.set_xlim(-0.7, len(lb) - 0.3)
    js.finish(ax)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def cat_hbars(slug, kind, h, xlabel, fmt='{:.0f}', vline=None, vlabel=None):
    # ⛔ 形态优先看账本 chart_form
    if E[slug].get('chart_form') == 'vbars':
        return cat_vbars(slug, kind, h, xlabel, fmt=fmt, hline=vline, hlabel=vlabel)
    """类别多（11 个项目）时用横条：竖条的 45° 斜标签在 3.35in 上会互相压
    （guards 抓到过 Media×Emerald、Ink×Service、Freeze×Connect 三处）。"""
    ent = E[slug]
    lb, vs = ent['labels'], ent['vals']
    y = np.arange(len(lb))[::-1]
    fig, ax = js.figure(kind, h=h)
    ax.barh(y, vs, color=js.NAVY, height=0.66)
    for yy, vv in zip(y, vs):
        ax.annotate(fmt.format(vv), (vv, yy), textcoords='offset points',
                    xytext=(3, 0), va='center', ha='left', fontweight='bold',
                    color=js.NAVY, fontsize=FS() * 0.92)
    if vline is not None:
        ax.axvline(vline, color=js.GOLD, lw=1.1, ls='--', zorder=3)
        # 标注放到画框外的上方 —— 放框内会压柱子的数值标签，放框下会被 x 轴线切掉
        ax.annotate(vlabel or f'{vline:g}', (vline, 1.0),
                    xycoords=('data', 'axes fraction'),
                    textcoords='offset points', xytext=(0, 3), ha='center', va='bottom',
                    color=js.GOLD, fontweight='bold', fontsize=FS() * 0.9,
                    annotation_clip=False)
    ax.set_yticks(y); ax.set_yticklabels(lb)
    ax.set_xlim(0, max(vs) * 1.22)
    ax.xaxis.set_major_locator(mt.MultipleLocator(100))
    ax.set_xlabel(xlabel)
    for s_ in ('top', 'right'):
        ax.spines[s_].set_visible(False)
    ax.xaxis.grid(True, color=js.GRID, lw=0.8); ax.set_axisbelow(True)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def cat_bars(slug, kind, h, ylabel, fmt='{:.0f}', hline=None, hlabel=None):
    ent = E[slug]
    lb, vs = ent['labels'], ent['vals']
    x = np.arange(len(lb))
    fig, ax = js.figure(kind, h=h)
    ax.bar(x, vs, color=js.NAVY, width=0.66)
    for xx, vv in zip(x, vs):
        ax.annotate(fmt.format(vv), (xx, vv), textcoords='offset points',
                    xytext=(0, 3), ha='center', fontweight='bold', color=js.NAVY,
                    fontsize=FS() * 0.88)
    if hline is not None:
        ax.axhline(hline, color=js.GOLD, lw=1.1, ls='--', zorder=3)
        ax.annotate(hlabel or f'{hline:g}', (len(lb) - 0.5, hline),
                    textcoords='offset points', xytext=(-2, 4), ha='right',
                    color=js.GOLD, fontweight='bold', fontsize=FS() * 0.9)
    ax.set_ylim(*ent['ylim'])
    ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    ax.set_xticks(x); ax.set_xticklabels(lb, rotation=45, ha='right')
    ax.set_ylabel(ylabel); js.finish(ax)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def grouped_cat3(slug, kind, h, ylabel, fmt='{:.1f}', wrap=None, ncol=2):
    ent = E[slug]
    lb, ser = ent['labels'], ent['series']
    ks = list(ser); x = np.arange(len(lb)); wd = 0.80 / len(ks)
    fig, ax = js.figure(kind, h=h)
    cols = [js.NAVY, js.BANDS[1], js.SLATE, js.BLUE]
    for i, k in enumerate(ks):
        xs = x + i * wd - 0.40 + wd / 2
        vs = np.array(ser[k], dtype=float)
        ax.bar(xs, vs, width=wd * 0.9, color=cols[i], label=k)
        for xx, vv in zip(xs, vs):
            ax.annotate(fmt.format(vv), (xx, vv), textcoords='offset points',
                        xytext=(0, 2), ha='center', color=js.NAVY,
                        fontweight='bold', fontsize=FS() * 0.72)
    ax.set_ylim(*ent['ylim'])
    ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    ax.set_xticks(x)
    ax.set_xticklabels([(wrap(l) if wrap else l) for l in lb])
    ax.set_ylabel(ylabel); js.finish(ax)
    js.legend_inside(ax, ent=ent, ncol=ent.get('legend_ncol', 1), slug=slug)
    js.save(fig, f'charts/{slug}.png', kind=kind)


# ── §5 补两张 ──
sys.path.insert(0, '.')
from build_s5 import qlines            # 复用长序列折线
qlines('cf_sp_dl_vs_bsl_default', 'pair', 2.9, 'T12M default rate (%)', every=24,
       fmt='{:.1f}%', dys=[9, -12], styles=('-', '-'), lws=(1.2, 1.2))
grouped_cat3('cf_recovery_path', 'pair', 3.0, 'Implied recovery (pt)', fmt='{:.1f}',
             wrap=lambda s: s.replace('Direct lending — ', 'DL\n').replace('Syndicated loans', 'Syndicated\nloans'),
             ncol=2)

# ── §8 基金侧 ──
for slug, h in (('fund_pag_comp_type', 2.9), ('fund_pag_comp_geo', 2.9),
                ('fund_pag_comp_ccy', 2.9), ('fund_pag_comp_bank', 2.9),
                ('fund_gug_gics_mix', 3.2), ('fund_gug_sponsored', 2.9),
                ('fund_hsbc_sector', 2.9)):
    shares(slug, 'pair', h)
cat_hbars('fund_hsbc_margin', 'pair', 3.2, 'Margin over base rate (bp)',
          vline=319.6, vlabel='wtd avg 319.6bp')
print('\nEx 15 / 20 + §8 基金侧七张出完')


# ══════════ Ex 49–52：基线季的画法 ══════════
# report-spec §9.3 写「Baseline quarter: record levels instead」——
# 本季账本只有一个季度点，画不出 QoQ 动量，也画不出轨迹线。
# 所以：49/50 画「本基金 vs cohort 中位」的水平对比；51/52 画分位点位 + P25/P50/P75 参考线。
# 两者都在图内标明「baseline」，不许留白让人以为漏画。
def _pair_value_labels(ax, xf, fv, xc, cm, f_, fs, span):
    """Fund / cohort-median 一对柱的数值标签。

    ⛔ 两个都写在各自柱顶上方，只有**两根柱高度差得够多**才行 —— 柱心相距 0.36 个轴单位，
    在 pair 画布上只有 ~9pt，而 "1.11" 这种四字标签宽 ~14pt，横向必然重叠，靠的是纵向
    错开。2026-08-25 实测 Ex 50 的 TVPI 那三对（1.11/1.15、1.20/1.10、1.21/1.10）
    高度差太小，六个标签全粘成 "1.111.15"、"1.201.10"。
    缩字号解决不了（差的是宽度不是高度），转角度违反「图内数值标签一律水平」。

    所以按柱高差分三种：
      1) 差得够多（≥ span*5.5%，约一行字高）—— 各写各自柱顶上方，天然错开；
      2) 差得不够，但浅色柱够高塞得进一行字 —— cohort 的写**进浅色柱里**
         （#D7DEE6 底 + 深藏蓝字，对比度够），一上一下，谁属于哪根柱不用猜；
      3) 差得不够且浅色柱太矮 —— cohort 的照常写柱顶上方，把 **Fund 那个抬高一行**让开。
    """
    NEAR, INSIDE = span * 0.055, span * 0.13
    up_f, up_c, inside = 2, 2, False
    if abs(fv - cm) < NEAR:
        if cm >= INSIDE:
            inside = True
        else:
            up_f = 13
    ax.annotate(f_.format(fv), (xf, fv), textcoords='offset points', xytext=(0, up_f),
                ha='center', va='bottom', fontweight='bold', color=js.NAVY, fontsize=fs)
    ax.annotate(f_.format(cm), (xc, cm), textcoords='offset points',
                xytext=(0, -2 if inside else up_c), ha='center',
                va='top' if inside else 'bottom',
                fontweight='bold', color=js.NAVY, fontsize=fs)


def level_vs_median(slug, kind, h, ylabel, fmt='{:.2f}', second='rows_dpi',
                    second_label='DPI', second_fmt='{:.2f}'):
    ent = E[slug]
    if ent.get(second):
        return _two_metric_panels(slug, kind, h, ylabel, fmt, second, second_label, second_fmt)
    rows = [r for r in ent['rows'] if isinstance(r.get('cq'), (int, float))]
    skipped = [r['label'] for r in ent['rows'] if not isinstance(r.get('cq'), (int, float))]
    lb = [r['label'] for r in rows]
    fv = [float(r['cq']) for r in rows]
    cm = [float(r['cohort_median']) for r in rows]
    x = np.arange(len(lb)); wd = 0.36
    fig, ax = js.figure(kind, h=h)
    ax.bar(x - wd / 2, fv, width=wd * 0.92, color=js.NAVY, label='Fund')
    ax.bar(x + wd / 2, cm, width=wd * 0.92, color=js.BANDS[1], label='Vintage cohort median')
    _ylim = ent['ylim'] if ent.get('ylim') else (0, max(fv + cm) * 1.30)
    ax.set_ylim(*_ylim)
    _span = _ylim[1] - _ylim[0]
    for xx, a_, b_ in zip(x, fv, cm):
        _pair_value_labels(ax, xx - wd / 2, a_, xx + wd / 2, b_, fmt,
                           FS() * 0.85, _span)
    ax.set_xticks(x)
    ax.set_xticklabels([l.replace(' Fund III', ' III').replace(' Partnership Fund', '')
                         .replace('Guggenheim PDF IV', 'Guggenheim\nPDF IV')
                         .replace('PAG BRS III', 'PAG\nBRS III')
                         .replace('HSBC RCF', 'HSBC\nRCF') for l in lb])
    ax.set_ylabel(ylabel); js.finish(ax)
    txt = 'Baseline quarter — momentum starts next quarter'
    if skipped:
        txt += f'\n{", ".join(skipped)}: no disclosed metric this quarter'
    # 说明文字放图外下方，图例放图内左上 —— 两个都塞在上方会撞（guards 抓到过）
    ax.text(0.0, -0.30, txt, transform=ax.transAxes, fontsize=FS() * 0.82,
            color=js.GRAY, va='top', ha='left')
    ax.legend(loc='upper left', frameon=False, handlelength=1.1, labelspacing=0.2,
              borderpad=0.1)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def _two_metric_panels(slug, kind, h, ylabel, fmt, second, second_label, second_fmt):
    """两个指标并排（基线 Ex 50 就是 TVPI | DPI 两组）。基金柱 + cohort 中位柱。"""
    ent = E[slug]
    blocks = [('TVPI', ent['rows'], fmt), (second_label, ent[second], second_fmt)]
    fig, ax = js.figure(kind, h=h)
    wd, gap = 0.36, 0.9
    xt, xl, allv, pos = [], [], [], 0.0
    pairs = []          # 数值标签等 ylim 定下来再画 —— 要按轴高判柱子塞不塞得进字
    skipped = set()
    for bi, (bname, rows_, f_) in enumerate(blocks):
        rr = [r for r in rows_ if isinstance(r.get('cq'), (int, float))]
        skipped |= {r['label'] for r in rows_ if not isinstance(r.get('cq'), (int, float))}
        for r in rr:
            fv, cm = float(r['cq']), float(r['cohort_median'])
            ax.bar(pos - wd / 2, fv, width=wd * 0.92, color=js.NAVY,
                   label='Fund' if (bi == 0 and not xt) else None)
            ax.bar(pos + wd / 2, cm, width=wd * 0.92, color=js.BANDS[1],
                   label='Vintage cohort median' if (bi == 0 and not xt) else None)
            pairs.append((pos - wd / 2, fv, pos + wd / 2, cm, f_))
            allv += [fv, cm]
            xt.append(pos)
            xl.append(r['label'].replace(' Fund III', '\nIII')
                      .replace(' Partnership Fund', '').replace('PAG BRS', 'PAG\nBRS')
                      .replace('HSBC RCF', 'HSBC\nRCF')
                      .replace('Guggenheim PDF IV', 'Gugg.\nPDF IV'))
            pos += 1.0
        # 组标题
        ax.annotate(bname, ((xt[-1] + xt[-len(rr)]) / 2, max(allv) * 1.16),
                    ha='center', fontweight='bold', color=js.NAVY, fontsize=FS())
        pos += gap
    _ylim = ent['ylim'] if ent.get('ylim') else (0, max(allv) * 1.34)
    ax.set_ylim(*_ylim)
    _span = _ylim[1] - _ylim[0]
    for xf_, fv_, xc_, cm_, f_ in pairs:
        _pair_value_labels(ax, xf_, fv_, xc_, cm_, f_, FS() * 0.8, _span)
    ax.set_xticks(xt); ax.set_xticklabels(xl)
    ax.set_ylabel(ylabel); js.finish(ax)
    txt = 'Baseline quarter — momentum starts next quarter'
    if skipped:
        txt += f'\n{", ".join(sorted(skipped))}: no disclosed metric this quarter'
    ax.text(0.0, -0.50, txt, transform=ax.transAxes, fontsize=FS() * 0.82,
            color=js.GRAY, va='top', ha='left')
    js.legend_inside(ax, ent=ent, ncol=1, slug=slug, columnspacing=1.2,
                     fontsize=FS() * 0.85)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def _fwd_quarters(start, n):
    y, q = int(start[:4]), int(start[-1])
    out = []
    for _ in range(n):
        out.append(f'{y}Q{q}'); q += 1
        if q > 4:
            q = 1; y += 1
    return out


def pct_points(slug, kind, h, ylabel, nq=5):
    """分位轨迹：横轴是时间，本季是第一个点，后面留空等下季 append。

    第一版把横轴做成了基金名，时间维度整个没了 —— 可这张图名字就叫 trajectory，
    基线的横轴是 2026Q3→2027Q3。已改回。
    """
    ent = E[slug]
    hist = ent['history']
    names = list(hist)
    qs = _fwd_quarters(ent['as_of'], nq)
    qi = {q: i for i, q in enumerate(qs)}
    fig, ax = js.figure(kind, h=h)
    for lvl, lab in ((75, 'Q1 threshold (P75)'), (50, 'Median (P50)'), (25, 'P25')):
        ax.axhline(lvl, color=js.GRID, lw=1.0, zorder=0,
                   linestyle='--' if lvl != 50 else '-')
        ax.annotate(lab, (nq - 0.55, lvl), textcoords='offset points', xytext=(0, 4),
                    ha='right', va='bottom', fontsize=FS() * 0.85, color=js.GRAY)
    # own_fund 专用配色：三只都是自家基金，HILITE 红给第一只
    MK = {0: ('D', OWN[0]), 1: ('s', OWN[2]), 2: ('^', OWN[1])}
    miss = []
    # 先把每只基金的末点算出来，看有没有落在同一处 ——
    # 2026Q3 实测 Ex 52：Guggenheim 与 HSBC 的 TVPI 都是 P100，两个标记完全重合，
    # 后画的把先画的盖住，两个不同色的 "P100" 也叠成一个，读者只看得见一只基金。
    # 分位数相同是真实情况，不许改数；能改的是画法 —— 标记左右错开、标签上下错开，
    # 让「两只基金都在 P100」看得出来。
    last = {}
    for i, nm in enumerate(names):
        if hist[nm]:
            pp = hist[nm][-1]
            if pp['quarter'] in qi:
                last[i] = (qi[pp['quarter']], pp['percentile'])
    used = []
    for i in last:
        xa, ya = last[i]
        for g in used:
            xb, yb = last[g[0]]
            if xa == xb and abs(ya - yb) < 3.0:      # 3 个分位点以内算重合
                g.append(i); break
        else:
            used.append([i])
    grp = {i: (k, len(g)) for g in used for k, i in enumerate(g)}
    DX, DY = 0.11, 16            # 标记横向错开（轴单位）／标签纵向错开（pt）

    for i, nm in enumerate(names):
        pts = hist[nm]
        mk, col = MK.get(i, ('o', js.NAVY))           # own_fund 序列
        if not pts:
            miss.append(nm)
            ax.scatter([], [], marker=mk, s=46, color=col, label=nm + '†')
            continue
        k, n = grp.get(i, (0, 1))
        off = (k - (n - 1) / 2) if n > 1 else 0.0
        dx, dy = DX * off, DY * off
        xsq = [qi[p['quarter']] + dx for p in pts if p['quarter'] in qi]
        ysq = [p['percentile'] for p in pts if p['quarter'] in qi]
        if len(xsq) > 1:
            ax.plot(xsq, ysq, color=col, lw=1.4, zorder=4)
        ax.scatter(xsq, ysq, marker=mk, s=52, color=col, edgecolor='white',
                   linewidth=0.7, zorder=5, label=nm)
        p = pts[-1]
        # ⛔ Alex 2026-08-25：「E51 和 E52 的 n=几全都删去 包括括号」—— 只留 P92 这种
        ax.annotate(f"P{p['percentile']:.0f}", (xsq[-1], ysq[-1]),
                    textcoords='offset points', xytext=(9, dy), ha='left', va='center',
                    fontweight='bold', color=col, fontsize=FS() * 0.88,
                    annotation_clip=False)
    ax.set_ylim(0, 112); ax.yaxis.set_major_locator(mt.MultipleLocator(25))
    ax.set_xlim(-0.5, nq - 0.5)
    ax.set_xticks(np.arange(nq)); ax.set_xticklabels(qs)
    ax.set_ylabel(ylabel); js.finish(ax, ygrid=False)
    # ⛔ 图例必须放坐标区外。这是散点轨迹图 —— 图例色块画在图内会被读成数据点：
    #    上一版把图例放在图内右下，三个色块正好压在 2027Q1–Q2 的横轴位置上，
    #    被读成「2027 年有数据」（Alex 2026-08-24 就这么读的）。
    # ⛔ Alex 2026-08-25：这两张也放图内 —— 用细黑框把图例框起来就不会被读成数据点。
    #    （8-24 那次误读是因为图例色块无框、落在 2027Q1–Q2 的横轴位置上。）
    #    账本 legend_boxed=true 打开实心白底 + 0.6pt 黑框。
    js.legend_inside(ax, ent=ent, ncol=1, slug=slug,
                     fontsize=FS() * 0.85, scatterpoints=1)
    txt = f"Baseline quarter ({ent['as_of']}) — one point per fund; trajectory builds each quarter"
    if miss:
        txt += f"\n{', '.join(miss)}: no disclosed metric, no point plotted"
    ax.text(0.0, -0.30, txt, transform=ax.transAxes, fontsize=FS() * 0.82,
            color=js.GRAY, va='top', ha='left')
    js.save(fig, f'charts/{slug}.png', kind=kind)


level_vs_median('ca_momentum_irr', 'pair', 3.0, 'Net IRR (%)', fmt='{:.1f}')
level_vs_median('ca_momentum_tvpi', 'pair', 3.0, 'TVPI (x)', fmt='{:.2f}')
pct_points('ca_traj_irr_pct', 'pair', 3.0, 'Net IRR percentile')
pct_points('ca_traj_tvpi_pct', 'pair', 3.0, 'TVPI percentile')
print('\nEx 49–52（基线季画法）出完')
