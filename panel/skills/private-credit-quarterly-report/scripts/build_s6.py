# -*- coding: utf-8 -*-
"""§9 Competitor 附录与 cohort 图（Ex 53–58）。只读账本。"""
import json, io, sys
sys.path.insert(0, '.')
import matplotlib; matplotlib.use('Agg')
import matplotlib.ticker as mt
import numpy as np
import junson_style as js

# ⛔ 三只自家基金同图出现，颜色必须互不相同 —— 一律走 js.OWN_FUNDS（palette 里有断言）。
#    2026-08-26 换色时踩过：HILITE 换成 C3 之后与 GOLD（也是 C3）撞了，PAG 和 HSBC 同色。
OWN = js.OWN_FUNDS

D = json.load(io.open('series.json', encoding='utf-8'))
E = D['exhibits']
FS = lambda: matplotlib.rcParams['font.size']


def dual_bars(slug, kind, h, y1lab, y2lab, every=2):
    """两个不同量纲的指标：左轴柱、右轴柱，按 vintage 并排。"""
    ent = E[slug]
    ks = list(ent['series'])
    # ⛔ x_start：只裁画的左端，账本里的历史点一个不删（js.xwin 的注释里有原因）
    lb, a, b = js.xwin(ent, ent['labels'],
                       np.array(ent['series'][ks[0]], dtype=float),
                       np.array(ent['series'][ks[1]], dtype=float))
    x = np.arange(len(lb)); wd = 0.38
    fig, ax = js.figure(kind, h=h)
    ax.bar(x - wd / 2, a, width=wd * 0.92, color=js.NAVY, label=ks[0])
    ax.set_ylim(*(ent['ylim'] if ent.get('ylim') else (0, np.nanmax(a) * 1.30)))
    ax.set_ylabel(y1lab); js.finish(ax)
    ax2 = js.twin_right(ax)
    ax2.bar(x + wd / 2, b, width=wd * 0.92, color=js.GOLD, label=ks[1])
    ax2.set_ylim(*(ent['rhs_ylim'] if ent.get('rhs_ylim') else (0, np.nanmax(b) * 1.30)))
    ax2.set_ylabel(y2lab, fontsize=FS())
    ax2.tick_params(labelsize=FS())
    _ix = js.tick_idx(len(lb), every)
    ax.set_xticks([x[i] for i in _ix])
    ax.set_xticklabels([f"’{lb[i][-2:]}" for i in _ix])
    js.assert_last_ticked(ax, _ix[-1] + 1)   # 末期必须在刻度里
    ax.set_xlim(-0.7, len(lb) - 0.3)
    ax2.set_xlim(-0.7, len(lb) - 0.3)
    hs = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
    ls = ax.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
    js.legend_inside(ax, hs, ls, ent=ent, slug=slug, handlelength=1.1,
                     labelspacing=0.2)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def size_and_count(slug, kind, h, ylab, every=2):
    ent = E[slug]
    p, v, _cnt = js.xwin(ent, ent['periods'],
                         np.array(list(ent['stacks'].values())[0], dtype=float) / 1000.0,
                         np.array(ent['rhs_line']['vals'], dtype=float))
    x = np.arange(len(p))
    fig, ax = js.figure(kind, h=h)
    ax.bar(x, v, color=js.NAVY, width=0.7, label='Aggregate fund size (US$bn)')
    _dys6 = None   # 见下：等 ylim 定了再算
    ax.set_ylim(*(ent['ylim'] if ent.get('ylim') else (0, v.max() * 1.28)))
    ax.set_ylabel(ylab); js.finish(ax)
    cnt = _cnt
    ax2 = js.twin_right(ax)
    ax2.plot(x, cnt, color=js.GOLD, lw=1.4, marker='o', ms=js.ms(1.4),
             label=ent['rhs_line']['label'])
    ax2.set_ylim(*(ent['rhs_ylim'] if ent.get('rhs_ylim') else (0, cnt.max() * 1.28)))
    ax2.set_ylabel('Number of funds', fontsize=FS()); ax2.tick_params(labelsize=FS())
    ax2.annotate(f'{cnt.max():.0f}', (x[int(cnt.argmax())], cnt.max()),
                 textcoords='offset points', xytext=(0, 4), ha='center',
                 fontweight='bold', color=js.GOLD, fontsize=FS())
    _ix = js.tick_idx(len(p), every)
    ax.set_xticks([x[i] for i in _ix]); ax.set_xticklabels([p[i] for i in _ix], rotation=0)
    js.assert_last_ticked(ax, _ix[-1] + 1)   # 末期必须在刻度里
    ax.set_xlim(-0.8, len(p) - 0.2); ax2.set_xlim(-0.8, len(p) - 0.2)
    hs = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
    ls = ax.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
    js.legend_inside(ax, hs, ls, ent=ent, slug=slug, handlelength=1.2,
                     labelspacing=0.2)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def median_band(slug, kind, h, ylab, fmt='{:.1f}', every=2, show_n=True):
    ent = E[slug]
    # ⛔ x_start：只裁画的左端，账本里的历史点一个不删（同 dual_bars / size_and_count）。
    #    Alex 2026-08-26：「图 56 57 58 的 x 轴都从 13 年开始画，统一一下」——
    #    三张原来分别从 ’10 / ’10 / ’11 起，裁到 2013 之后横轴完全一致（2013–2025 十三年），
    #    读者能在三张之间对同一个 vintage。这个函数原来根本没接 x_start，写了也不生效。
    lb, med, p25, p75 = js.xwin(
        ent, ent['labels'],
        np.array([np.nan if v is None else v for v in ent['median']], dtype=float),
        np.array([np.nan if v is None else v for v in ent['p25']], dtype=float),
        np.array([np.nan if v is None else v for v in ent['p75']], dtype=float))
    x = np.arange(len(lb))
    fig, ax = js.figure(kind, h=h)
    ax.fill_between(x, p25, p75, color=js.BANDS[0], zorder=0, label='P25–P75')
    ax.plot(x, med, color=js.NAVY, lw=1.5, marker='o', ms=js.ms(1.5), label='Median')
    ax.annotate(fmt.format(med[-1]), (x[-1], med[-1]), textcoords='offset points',
                xytext=(4, 6), ha='left', fontweight='bold', color=js.NAVY,
                fontsize=FS(), annotation_clip=False)
    lo = min(0, np.nanmin(p25))
    ax.set_ylim(*(ent['ylim'] if ent.get('ylim') else (lo, np.nanmax(p75) * 1.12)))
    # ⛔ ytick 原来这个函数根本没接 —— 账本里写了也不生效，刻度是 matplotlib 自己挑的
    #    （E57 账本写着 0.25，纸上恰好也是 0.25，所以一直没被发现）。同 x_start 那个坑。
    if ent.get('ytick'):
        ax.yaxis.set_major_locator(mt.MultipleLocator(ent['ytick']))
    _ix = js.tick_idx(len(lb), every)
    ax.set_xticks([x[i] for i in _ix])
    ax.set_xticklabels([f"’{lb[i][-2:]}" for i in _ix])
    js.assert_last_ticked(ax, _ix[-1] + 1)   # 末期必须在刻度里
    ax.set_xlim(-0.5, len(lb) - 0.5 + len(lb) * 0.07)
    ax.set_ylabel(ylab); js.finish(ax)
    # ⛔ 横轴标题整行不画。两步走到这儿的：
    #    8-25 Alex：「其他图里如果出现一样的情况，也是要删去，不要（n=xxx）」—— 去掉了
    #        "Vintage  (n = funds:  ’19 12  ’22 25 …)" 里的 n= 部分，留下 "Vintage"；
    #    8-26 Alex：「图56 57 58 的下面都有写了个 vintage n=xxxxx，这一行都删掉，不允许出现」
    #        —— 整行去掉。刻度本来就是年份、题注里也写着 by vintage，这行是冗余；
    #        同事那三张也没有横轴标题。
    #    样本数仍在账本 `n` 字段里，要引用就写在正文/Note 里，**不许回到图上**。
    #    `show_n` 这个参数从此无效，留着只为不改调用签名。
    _ = show_n
    # 自家基金叠点 —— 基线题注 "with Junson funds" 说的就是这些标记，第一版漏了
    ov = ent.get('overlay') or []
    # 这两个都是 own_fund（Junson 自己的基金）—— HILITE 红只给自家基金
    MK = {'PAG BRS III': ('D', OWN[0]), 'HSBC RCF': ('^', OWN[1]),
          'Guggenheim PDF IV': ('s', OWN[2])}
    y0, y1 = ax.get_ylim()
    span = y1 - y0

    # ── 叠点标签排布（2026-08-25 重写）─────────────────────────────────────────
    # 旧写法是「同一 vintage 的第一个点标下方、第二个标上方」，只看顺序不看图上有什么，
    # 实测踩了两次：
    #   Ex 56 ’23 的 PAG 14.7% 标在下方 → 正好落在中位数折线（≈10.6）上，数字被线穿过；
    #   Ex 58 ’24 的 Guggenheim 1.20x 与 HSBC 1.21x y 只差 0.01 → 两个标记完全叠住。
    # 现在的规则，三条，按顺序判：
    #   1) 同 vintage 上 y 差 < 轴高 10% 的算「挤在一起」，标记左右错开，标签同侧上下摞；
    #   2) 标签放在**远离中位数线**的那一侧 —— 点在线上方就标上方，在下方就标下方；
    #   3) 那一侧放不下（会出轴）就翻到另一侧。
    NEAR = 0.10          # 同 vintage「挤在一起」的阈值（占轴高）
    PAD  = 0.055         # 一行标签大约占的轴高，用来判会不会出界
    STEP = 11            # 同侧摞第二行的额外偏移（pt）

    pts = []
    for o in ov:
        try:
            i0 = lb.index(str(o['vintage']))
        except ValueError:
            continue
        v = o['value']
        pts.append({'o': o, 'i0': i0, 'v': v, 'off': v > y1,
                    'yy': min(v, y1 - span * 0.035)})

    # 1) 分组：同 vintage 且 y 挨得近
    groups = []
    for p in pts:
        for g in groups:
            if g[0]['i0'] == p['i0'] and abs(g[0]['yy'] - p['yy']) < span * NEAR:
                g.append(p); break
        else:
            groups.append([p])

    for g in groups:
        mref = med[g[0]['i0']] if not np.isnan(med[g[0]['i0']]) else None
        # 2) 远离中位数线的那侧；没有中位数就默认上方
        gy = sum(p['yy'] for p in g) / len(g)
        up = True if mref is None else (gy >= mref)
        # 3) 整摞放不下就翻面
        need = span * PAD * len(g)
        if up and gy + need > y1:
            up = False
        if (not up) and gy - need < y0:
            up = True
        # 离中位数线近的先排，越往外越远，这样最内侧那行离线最远的空隙最大
        g.sort(key=lambda p: abs(p['yy'] - (mref if mref is not None else gy)))
        for k, p in enumerate(g):
            p['up'] = up
            p['dy'] = (9 + STEP * k) if up else -(11 + STEP * k)
            # 标记左右错开（只在挤在一起时才动，单点保持在刻度正上）
            p['xi'] = p['i0'] if len(g) == 1 else p['i0'] + 0.17 * (k - (len(g) - 1) / 2)

    # ── 先画标记，记下它们的 bbox，标签要避开 ────────────────────────────
    inv = ax.transData.inverted()

    def _box(art):
        bb = art.get_window_extent(fig.canvas.get_renderer())
        (bx0, by0), (bx1, by1) = inv.transform(((bb.x0, bb.y0), (bb.x1, bb.y1)))
        return (min(bx0, bx1), min(by0, by1), max(bx0, bx1), max(by0, by1))

    def _hit(b, placed):
        return any(not (b[2] < q[0] or b[0] > q[2] or b[3] < q[1] or b[1] > q[3])
                   for q in placed)

    _mk_half_x = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.022
    _mk_half_y = span * 0.030
    occupied = []
    for p in pts:
        o = p['o']
        mk, col = MK.get(o['name'], ('o', js.OWN_FUND_FALLBACK))  # 兜底也不许撞三色
        # ⛔ 名字标在点旁边（Alex 2026-08-26），所以**不再给图例条目** ——
        #    同一个名字和数值在一张图上出现两遍是噪音。图例只留 P25–P75 与 Median。
        ax.scatter([p['xi']], [p['yy']], marker=mk, s=52, color=col,
                   edgecolor='white', linewidth=0.7, zorder=5)
        p['col'] = col
        occupied.append((p['xi'] - _mk_half_x, p['yy'] - _mk_half_y,
                         p['xi'] + _mk_half_x, p['yy'] + _mk_half_y))
    fig.canvas.draw()

    # ── 标签择位：首选原规则算出来的方向，撞了就换候选位 ──────────────────
    # ⛔ 标签带上名字之后横向长了三四倍，光靠「远离中位数线」不够 ——
    #    Ex 58 实测：Guggenheim 的标签正好压在 PAG 的菱形上。所以逐个候选位实测 bbox。
    _ax0, _ax1 = ax.get_xlim()
    for p in sorted(pts, key=lambda q: -q['yy']):
        o = p['o']
        _f = (p['xi'] - _ax0) / (_ax1 - _ax0)
        _ha0 = 'right' if _f > 0.62 else ('left' if _f < 0.38 else 'center')
        _dy0 = abs(p['dy']) if p['up'] else -abs(p['dy'])
        # 候选：先试首选方向的三种对齐，再翻到另一侧，最后加大纵向偏移
        _cands = []
        for _dy in (_dy0, -_dy0, _dy0 * 1.9, -_dy0 * 1.9):
            for _ha in (_ha0, 'center', 'left', 'right'):
                _dx = {'right': -5, 'left': 5, 'center': 0}[_ha]
                if (_ha, _dy) not in [(c[2], c[1]) for c in _cands]:
                    _cands.append((_dx, _dy, _ha))
        _txt = f"{o['name']}{'†' if o.get('dagger') else ''} " \
               f"{fmt.format(p['v'])}{'*' if p['off'] else ''}"
        _placed = None
        for _dx, _dy, _ha in _cands:
            a = ax.annotate(_txt, (p['xi'], p['yy']), textcoords='offset points',
                            xytext=(_dx, _dy), ha=_ha,
                            va=('bottom' if _dy > 0 else 'top'),
                            fontweight='bold', color=p['col'], fontsize=FS() * 0.82,
                            annotation_clip=False,
                            # 82% 白底：标签横穿中位数线 / P25–P75 带是躲不掉的
                            # （Ex 57 实测被线划掉一道），底色把线断开，和
                            # legend_inside / flip_if_overflow 同一处理。
                            bbox=dict(boxstyle='square,pad=0.14', facecolor='white',
                                      alpha=0.82, edgecolor='none'))
            fig.canvas.draw()
            b = _box(a)
            _inside = (b[0] >= min(_ax0, _ax1) - 1e-9 and b[2] <= max(_ax0, _ax1) + 1e-9
                       and b[1] >= y0 and b[3] <= y1)
            if _inside and not _hit(b, occupied):
                occupied.append(b); _placed = a; break
            a.remove()
        if _placed is None:      # 所有候选都撞 —— 退回首选位，至少别丢标签
            _dx, _dy, _ha = _cands[0]
            a = ax.annotate(_txt, (p['xi'], p['yy']), textcoords='offset points',
                            xytext=(_dx, _dy), ha=_ha,
                            va=('bottom' if _dy > 0 else 'top'),
                            fontweight='bold', color=p['col'], fontsize=FS() * 0.82,
                            annotation_clip=False,
                            bbox=dict(boxstyle='square,pad=0.14', facecolor='white',
                                      alpha=0.82, edgecolor='none'))
            fig.canvas.draw()
            occupied.append(_box(a))
            print(f'    ⚠ {slug}: {o["name"]} 的标签所有候选位都撞了，用了首选位 —— 去看一眼')
    # 图例走 legend_inside：位置优先读账本冻结的 legend_loc，没冻结就实测最空的一角并打印
    # 建议。半透明白底顺手治了 Ex 57 的老毛病 —— 中位数线从 ’11 起就在 95% 上下，
    # 原来 upper left 的无框图例正好被这条线横穿，"Guggenheim PDF IV†" 那行读不出来。
    js.legend_inside(ax, ent=ent, slug=slug, fontsize=FS() * 0.85,
                     labelspacing=0.2, borderpad=0.25)
    js.save(fig, f'charts/{slug}.png', kind=kind)


def bubbles(slug, kind, h, xlab, ylab, topn=None):
    ent = E[slug]; pts = ent['points']
    if topn:
        pts = pts[:topn]
    fig, ax = js.figure(kind, h=h)
    xs = np.array([p['avg_quartile'] for p in pts], dtype=float)
    ys = np.array([p['median_irr'] for p in pts], dtype=float)
    ss = np.array([p['n_ranked'] for p in pts], dtype=float)
    ax.scatter(xs, ys, s=ss * 9, color=js.NAVY, alpha=0.72, edgecolor='white', lw=0.6)
    _ovx = [o['avg_quartile'] for o in (ent.get('overlay') or [])]
    _xr = min([xs.min()] + _ovx)
    ax.set_xlim(xs.max() + 0.28, _xr - 0.22)               # x 反向：1 = 最好，放右边
    ax.set_ylim(*(ent['ylim'] if ent.get('ylim') else (min(0, ys.min() - 1), ys.max() * 1.16)))
    ax.set_xlabel(xlab); ax.set_ylabel(ylab); js.finish(ax)
    ax.text(0.015, 0.955, 'Bubble size = number of PitchBook-ranked funds',
            transform=ax.transAxes, fontsize=FS() * 0.88, color=js.GRAY, va='top')
    # 只标账本里指定的那几家 —— 29 家全标会糊成一片。
    # 同一坐标上可能落着两家（例：Carlyle 与 Blue Torch 都是 1.75 / 14.30），
    # 必须合并成一个标注，否则文字完全重合（guards 会直接抛错）。
    def short(m):
        for a, b in ((' Asset Management', ' AM'), (' Investment Partners', ''),
                     (' Capital Management', ''), (' Capital Advisors', ''),
                     (' Direct Lending', ' DL'), (' Partners', ''), (' Group', ''), ('The Carlyle', 'Carlyle')):
            m = m.replace(a, b)
        return m

    tags = set(ent.get('label_managers') or [])
    groups = {}
    for p_, xx, yy in zip(pts, xs, ys):
        if p_['manager'] not in tags:
            continue
        groups.setdefault((round(xx, 2), round(yy, 2)), []).append(short(p_['manager']))

    # 29 家全标必然压叠。做法照基线：先试点周围 8 个方位、两档距离；
    # 都放不下的拉到右侧成一列，用细引线连回气泡（基线就是这么排的）。
    fig.canvas.draw()
    inv = ax.transData.inverted()

    def box_of(txt_art):
        bb = txt_art.get_window_extent(fig.canvas.get_renderer())
        (x0, y0), (x1, y1) = inv.transform(((bb.x0, bb.y0), (bb.x1, bb.y1)))
        return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

    def hits(b, placed_boxes):
        for q in placed_boxes:
            if not (b[2] < q[0] or b[0] > q[2] or b[3] < q[1] or b[1] > q[3]):
                return True
        return False

    CANDS = [(0, 11), (0, -13), (9, 4), (-9, 4), (9, -8), (-9, -8),
             (0, 20), (0, -22), (16, 10), (-16, 10)]
    boxes, leftovers = [], []
    items = sorted(groups.items(), key=lambda kv: (-kv[0][1], kv[0][0]))
    for (xx, yy), names in items:
        lbl = ' / '.join(names)
        done = False
        for dx, dy in CANDS:
            a = ax.annotate(lbl, (xx, yy), textcoords='offset points', xytext=(dx, dy),
                            ha='center' if dx == 0 else ('left' if dx > 0 else 'right'),
                            va='bottom' if dy > 0 else 'top',
                            fontsize=FS() * 0.80, color=js.NAVY, annotation_clip=False)
            fig.canvas.draw()
            b = box_of(a)
            if not hits(b, boxes):
                boxes.append(b); done = True; break
            a.remove()
        if not done:
            leftovers.append((xx, yy, lbl))
    # 放不下的拉到左侧（高四分位那侧，气泡稀疏）成一列，用细引线连回去；
    # 列里的每个标签也要参与碰撞检测，否则会压到别的标签上
    if leftovers:
        xlo, xhi = ax.get_xlim()          # 注意 x 轴反向：xlo 是 4.x，xhi 是 1.x
        ylo, yhi = ax.get_ylim()
        colx = xlo + (xhi - xlo) * 0.012
        span = yhi - ylo
        leftovers.sort(key=lambda t: -t[1])
        slots = [yhi - span * 0.05 - i * span * 0.055 for i in range(40)]
        used = set()
        for xx, yy, lbl in leftovers:
            for si, ty in enumerate(slots):
                if si in used:
                    continue
                a = ax.annotate(lbl, xy=(xx, yy), xytext=(colx, ty), ha='left',
                                va='center', fontsize=FS() * 0.80, color=js.NAVY,
                                annotation_clip=False,
                                arrowprops=dict(arrowstyle='-', color=js.GRID, lw=0.6,
                                                shrinkA=1, shrinkB=3))
                fig.canvas.draw()
                b = box_of(a)
                if not hits(b, boxes):
                    boxes.append(b); used.add(si); break
                a.remove()
    # 自家基金叠点（口径见账本 overlay_note：按 cohort 分位反推的等效四分位）
    # own_fund 专用配色：HILITE 红只给自家基金
    MK = {'PAG BRS III': ('D', OWN[0]), 'HSBC RCF': ('^', OWN[1])}
    ylo, yhi = ax.get_ylim()
    for o in (ent.get('overlay') or []):
        mk, col = MK.get(o['name'], ('o', js.OWN_FUND_FALLBACK))  # 兜底也不许撞三色
        off = o['median_irr'] > yhi
        yy = min(o['median_irr'], yhi - (yhi - ylo) * 0.045)
        ax.scatter([o['avg_quartile']], [yy], marker=mk, s=64, color=col,
                   edgecolor='white', linewidth=0.8, zorder=6)
        ax.annotate(f"{o['name']} {o['median_irr']:.1f}%" + ('*' if off else ''),
                    (o['avg_quartile'], yy), textcoords='offset points',
                    xytext=(-6, -13), ha='right', fontweight='bold', color=col,
                    fontsize=FS() * 0.85, annotation_clip=False)
    # 气泡大小图例：基线有，第一版漏了
    for i, nn in enumerate(ent.get('size_legend') or []):
        ax.scatter([], [], s=nn * 9, color=js.NAVY, alpha=0.72, edgecolor='white',
                   lw=0.6, label=f'{nn} funds')
    if ent.get('size_legend'):
        ax.legend(loc='upper left', bbox_to_anchor=(0.0, 0.90), frameon=False,
                  labelspacing=1.0, handletextpad=1.2, borderpad=0.1,
                  fontsize=FS() * 0.85, scatterpoints=1)
    js.save(fig, f'charts/{slug}.png', kind=kind)


dual_bars('ca_cohort_iqr', 'solo', 2.9, 'Net IRR IQR (pp)', 'TVPI IQR (x)', every=1)
size_and_count('ca_apx_universe', 'solo', 2.9, 'Aggregate fund size (US$bn)', every=1)
# ⛔ 三张统一：x_start=2013（账本里冻结）+ 同一个 every —— 横轴刻度年份三张一模一样，
#    才谈得上「统一」。13 个点、every=2 → ’13 ’15 ’17 ’19 ’21 ’23 ’25。
median_band('ca_apx_irr_by_vintage', 'pair', 3.0, 'Net IRR (%)', '{:.1f}%', every=2)
median_band('ca_apx_tvpi_by_vintage', 'pair', 3.0, 'TVPI (x)', '{:.2f}x', every=2)
median_band('ca_apx_called_by_vintage', 'solo', 2.9, 'Called down (%)', '{:.0f}%', every=2)
bubbles('ca_apx_mgr_consistency', 'solo', 3.2,
        'Average PitchBook fund quartile (1 = top)', 'Median net IRR (%)')
print('\n§9 六张出完')
