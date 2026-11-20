"""出图前的四道硬检查 —— 由 chartlib.save() 自动调用，不许绕过。

1) assert_no_cjk       图内一律英文。Lato 没有中文字形，中文会静默渲染成豆腐块 □□。
2) assert_no_overlap   任何两段文字互相压叠、或开了 clip 的 ax.text 被坐标区裁掉。
3) assert_flat_labels  图内数值标签一律水平（rotation=0）。竖排的数字读起来要歪头。
4) assert_marker_size  折线的描点直径 = 线宽的 2 倍。点太大会盖住线和相邻的点。

压叠检查用 display bbox 两两求交；会先滤掉 locator 生成的越界刻度对象
（ylim 从 0 起时 locator 仍会造出 -0.5 这种，实际不画，但 bbox 存在）。
"""
import re
import matplotlib
import matplotlib.text

CJK = re.compile(r'[　-〿㐀-䶿一-鿿＀-￯]')


def _offview(t, ticklim):
    """locator 造出的越界刻度：不画，但有 bbox，必须滤掉。"""
    lim = ticklim.get(id(t))
    if lim is None:
        return False
    s = t.get_text().strip()
    if not re.fullmatch(r'−?-?\d+(?:\.\d+)?', s):
        return False
    v = float(s.replace('−', '-'))
    return not (min(lim) - 1e-9 <= v <= max(lim) + 1e-9)


def visible_texts(fig):
    fig.canvas.draw()
    ticklim = {}
    for ax in fig.axes:
        for t in ax.get_xticklabels():
            ticklim[id(t)] = ax.get_xlim()
        for t in ax.get_yticklabels():
            ticklim[id(t)] = ax.get_ylim()
    out = []
    for t in fig.findobj(matplotlib.text.Text):
        if not (t.get_text().strip() and t.get_visible()):
            continue
        if _offview(t, ticklim):
            continue
        out.append(t)
    return out


def assert_no_cjk(fig):
    bad = [t.get_text() for t in visible_texts(fig) if CJK.search(t.get_text())]
    if bad:
        raise ValueError('图内出现中文/全角字符，必须全英文：'
                         + ' | '.join(dict.fromkeys(bad))[:300])


def assert_no_overlap(fig, allow=(), tol=None):
    """allow 里的文字串跳过。tol 参数保留只为向后兼容，实际不用。
    只查压叠，不查"是否跑到坐标区外" —— 饼图引线标签、右侧 ticker/数值列
    都是故意画在坐标区外的，bbox_inches='tight' 会把画布扩出去容纳它们。"""
    rend = fig.canvas.get_renderer()
    items, seen = [], set()
    for t in visible_texts(fig):
        s = t.get_text()
        if s in allow:
            continue
        try:
            bb = t.get_window_extent(renderer=rend)
        except Exception:
            continue
        if bb.width <= 0 or bb.height <= 0:
            continue
        # twinx 会让同一组 x 刻度标签被两个 axes 各画一份，位置完全重合。
        # 那是同一段文字画了两次，不是压叠 —— 按 (文字, 位置) 去重。
        key = (s, round(bb.x0, 1), round(bb.y0, 1))
        if key in seen:
            continue
        seen.add(key)
        items.append((s, bb, t))

    bad = []
    for i in range(len(items)):
        si, bi, _ = items[i]
        for j in range(i + 1, len(items)):
            sj, bj, _ = items[j]
            ox = min(bi.x1, bj.x1) - max(bi.x0, bj.x0)
            oy = min(bi.y1, bj.y1) - max(bi.y0, bj.y0)
            if ox <= 0 or oy <= 0:
                continue
            # 文字 bbox 自带上下留白，相邻两行会有零星纵向交叠 —— 那不算压叠。
            # 判成压叠要求：纵向交叠 > 较矮那个的 45%，且横向交叠 > 较窄那个的 25%
            mh = min(bi.height, bj.height)
            mw = min(bi.width, bj.width)
            if mh <= 0 or mw <= 0:
                continue
            fy, fx = oy / mh, ox / mw
            # 同一段文字被画了两次且几乎完全重合（twinx 的共享 x 刻度就是这样）——
            # 那不是压叠，读者看到的是同一个字。
            if si == sj and fy > 0.9:
                continue
            if fy > 0.45 and fx > 0.25:
                bad.append(f'文字压叠（纵 {fy:.0%} 横 {fx:.0%}）: '
                           f'"{si[:26]}" x "{sj[:26]}"')
    if bad:
        raise ValueError('压叠检查未通过：\n  - ' + '\n  - '.join(bad[:10]))


MARKER_RATIO = 2.0      # 描点直径 ÷ 线宽
MARKER_TOL = 0.35       # 允许的偏差（pt）


def assert_flat_labels(fig, allow_rot=()):
    """图内数值标签必须水平。

    只查 ax.texts（annotate / text / bar_label 产生的），不查刻度标签 ——
    长的 x 轴刻度该转就转。要例外就把那段文字传进 allow_rot。
    """
    bad = []
    for ax in fig.axes:
        for t in ax.texts:
            s_ = t.get_text().strip()
            if not s_ or s_ in allow_rot:
                continue
            r = float(t.get_rotation()) % 360
            if not (r < 1e-6 or abs(r - 360) < 1e-6):
                bad.append(f'"{s_[:24]}" rotation={r:g}°')
    if bad:
        raise ValueError(
            '数值标签必须水平（rotation=0），下面这些是斜的或竖的：\n  - '
            + '\n  - '.join(bad[:10])
            + '\n  条形图上的数值尤其不许竖排 —— 竖着的数字读起来要歪头。'
              '位置不够就把 y 轴上限抬高，或者标到条形外侧，不要转 90°。')


def assert_marker_size(fig, ratio=MARKER_RATIO, tol=MARKER_TOL):
    """折线的描点直径 = 线宽 × 2。

    matplotlib 里 markersize 就是直径（pt），linewidth 也是 pt，所以直接比。
    没有 marker 的线（marker='' / None）跳过。
    """
    bad = []
    for ax in fig.axes:
        for ln in ax.get_lines():
            mk = ln.get_marker()
            if mk in (None, 'None', 'none', '', ' '):
                continue
            lw = float(ln.get_linewidth())
            ms = float(ln.get_markersize())
            if lw <= 0:
                continue
            want = lw * ratio
            if abs(ms - want) > tol:
                lbl = ln.get_label()
                lbl = '' if str(lbl).startswith('_') else f'（{lbl}）'
                bad.append(f'lw={lw:g} → markersize 应为 {want:g}，实际 {ms:g}{lbl}')
    if bad:
        raise ValueError(
            f'描点直径必须是线宽的 {ratio:g} 倍：\n  - ' + '\n  - '.join(bad[:10])
            + f'\n  改法：markersize=linewidth*{ratio:g}，或者用 chartlib.ms(lw)。')


def check(fig, allow=(), allow_rot=()):
    assert_no_cjk(fig)
    assert_no_overlap(fig, allow=allow)
    assert_flat_labels(fig, allow_rot=allow_rot)
    assert_marker_size(fig)
