"""标题断言校验 —— 带数据描述的图标题不许跟图上的数据相违背。

背景：股价图那种标题每季固定不变；但「Interest coverage — improved on the
quarter, still near lows」这类标题里有对最新数据的判断，换一季数据一变，
照抄上季标题就会跟图自相矛盾。这个模块把标题里的每个数字和方向词
都拿去跟数据核一遍，对不上就 raise。

用法（在 build_charts.py 里每张带 claim 的图 save 之前调）：

    import titlecheck as TC
    TC.verify(title, series=fitch_vals, full=fitch_all)

claim 只允许用下面枚举里的说法。想表达枚举里没有的判断 → 先在这里加谓词，
不要自由发挥，否则等于没校验。
"""
import re

# ── 方向词 → 谓词。key 是正则，value 是 (说明, 判据函数) ────────────────
def _last(v):  return v[-1]
def _prev(v):  return v[-2] if len(v) > 1 else None


def _near(v, side, frac=0.40):
    lo, hi = min(v), max(v)
    if hi == lo:
        return True
    pos = (_last(v) - lo) / (hi - lo)
    return pos <= frac if side == 'low' else pos >= 1 - frac


DIRECTION = [
    (r'\bimproved\b|\brose\b|\bup\b|\bhigher\b|\brising\b',
     '末值高于上一期', lambda v, **k: _prev(v) is not None and _last(v) > _prev(v)),
    (r'\bdeteriorated\b|\bfell\b|\bdown\b|\blower\b|\bfalling\b|\bdeclin',
     '末值低于上一期', lambda v, **k: _prev(v) is not None and _last(v) < _prev(v)),
    (r'\bflat\b|\bunchanged\b|\bsteady\b|\bstable\b|\brange-bound\b',
     '末值与上一期之差不超过 eps', lambda v, eps=None, **k:
        _prev(v) is not None and abs(_last(v) - _prev(v)) <= (eps if eps is not None
                                                             else 0.02 * max(abs(_last(v)), 1e-9))),
    (r'near (?:the )?lows?|off (?:the )?lows?|still low',
     '末值落在窗口区间下 40%', lambda v, **k: _near(v, 'low')),
    (r'near (?:the )?highs?|still high',
     '末值落在窗口区间上 40%', lambda v, **k: _near(v, 'high')),
]

# 「flat to slightly down」这类复合说法：两个方向词都要成立，
# 但 flat 与 down 天然冲突，所以特判成「小幅下行」
COMPOUND = [
    (r'flat to slightly down',
     '末值不高于上一期，且降幅不超过 eps',
     lambda v, eps=None, **k: _prev(v) is not None and _last(v) <= _prev(v)
        and (_prev(v) - _last(v)) <= (eps if eps is not None else 0.03 * max(abs(_prev(v)), 1e-9))),
    (r'flat to slightly up',
     '末值不低于上一期，且升幅不超过 eps',
     lambda v, eps=None, **k: _prev(v) is not None and _last(v) >= _prev(v)
        and (_last(v) - _prev(v)) <= (eps if eps is not None else 0.03 * max(abs(_prev(v)), 1e-9))),
]

_WORDNUM = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6,
            'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}


def verify(title, series, full=None, rhs=None, deltas=None, eps=None,
           labels=None, periods_per_year=4, tol=0.051):
    """series = 窗口内的主序列（按时间升序）；full = 全序列（算 N 年新高用）；
    rhs = 右轴序列；deltas = {名字: 变化量}（算 sharpest rise 用）。
    labels = 与 full/series 等长的期标签（写 "highest since 4Q21" 这种说法时必须传）。
    tol = 标题里的数字与数据比对时允许的绝对误差（默认 0.051，容得下 1 位小数四舍五入）。"""
    t = title.lower()
    bad = []
    hit_any = False

    # 1) 复合说法优先，命中后把它从文本里去掉，避免被单个方向词重复判
    for pat, desc, pred in COMPOUND:
        if re.search(pat, t):
            hit_any = True
            if not pred(series, eps=eps):
                bad.append(f'"{pat}" 不成立（{desc}）；末两期 = '
                           f'{series[-2] if len(series) > 1 else "NA"} → {series[-1]}')
            t = re.sub(pat, ' ', t)

    # 2) 单个方向词
    for pat, desc, pred in DIRECTION:
        if re.search(pat, t):
            hit_any = True
            if not pred(series, eps=eps):
                bad.append(f'"{re.search(pat, t).group(0)}" 不成立（{desc}）；'
                           f'末两期 = {series[-2] if len(series) > 1 else "NA"} → {series[-1]}，'
                           f'窗口区间 = {min(series)}–{max(series)}')

    # 3) <N>-year high / low
    for m in re.finditer(r'(\d+|' + '|'.join(_WORDNUM) + r')[-\s]year (high|low)', t):
        hit_any = True
        n = int(m.group(1)) if m.group(1).isdigit() else _WORDNUM[m.group(1)]
        side = m.group(2)
        src = full if full else series
        win = src[-(n * periods_per_year):]
        ref = max(win) if side == 'high' else min(win)
        ok = abs(_last(src) - ref) <= tol
        if not ok:
            bad.append(f'"{m.group(0)}" 不成立：近 {n} 年（{len(win)} 期）'
                       f'{"最高" if side == "high" else "最低"}是 {ref}，末值是 {_last(src)}')


    # 3b) highest / lowest since <期标签> —— 卡在 N 年边界上时改用这个说法
    m = re.search(r'(highest|lowest) since ([A-Za-z0-9\'\u2019\-]+)', title, re.I)
    if m:
        hit_any = True
        side, lbl = m.group(1).lower(), m.group(2)
        if not labels:
            bad.append(f'标题写了 "{m.group(0)}"，但没传 labels 进来，无法校验')
        elif lbl not in labels:
            bad.append(f'标题写了 "{m.group(0)}"，但 {lbl} 不在期标签里：{labels[:4]}…')
        else:
            i = labels.index(lbl)
            src = full if full else series
            win = src[i:]                    # 含 lbl 那一期到末期
            ref = max(win) if side == 'highest' else min(win)
            if abs(_last(src) - ref) > tol:
                bad.append(f'"{m.group(0)}" 不成立：{lbl} 以来'
                           f'{"最高" if side == "highest" else "最低"}是 {ref}，末值是 {_last(src)}')

    # 4) sharpest rise (<A>, <B>) —— 括号里点名的必须是变化量最大的那几个
    m = re.search(r'sharpest (?:rise|increase|drop|fall)[^(]*\(([^)]*)\)', title, re.I)
    if m:
        hit_any = True
        if not deltas:
            bad.append('标题点名了 sharpest rise 的对象，但没传 deltas 进来，无法校验')
        else:
            named = [x.strip().lower() for x in m.group(1).split(',') if x.strip()]
            order = sorted(deltas, key=lambda k: deltas[k], reverse='rise' in m.group(0).lower()
                           or 'increase' in m.group(0).lower())
            top = [k.lower() for k in order[:len(named)]]
            if sorted(named) != sorted(top):
                bad.append(f'"sharpest" 点名的是 {named}，但按变化量排序应该是 {top}；'
                           f'deltas = {deltas}')

    # 5) more / fewer <something>  —— 用右轴序列判方向
    m = re.search(r'\b(more|fewer|fewer of|rising number of)\b', t)
    if m and rhs:
        hit_any = True
        want_up = m.group(1) in ('more', 'rising number of')
        ok = (rhs[-1] > rhs[-2]) if want_up else (rhs[-1] < rhs[-2])
        if not ok:
            bad.append(f'"{m.group(1)}" 不成立：右轴末两期 = {rhs[-2]} → {rhs[-1]}')

    # 6) 标题里出现的裸数字，必须能在末值里找到对应
    nums = [float(x) for x in re.findall(r'(?<![\w.])(\d+(?:\.\d+)?)\s*%', title)]
    if nums:
        hit_any = True
        cand = [series[-1]] + ([rhs[-1]] if rhs else []) + ([full[-1]] if full else [])
        for n in nums:
            if not any(abs(n - c) <= tol for c in cand):
                bad.append(f'标题里的 {n}% 跟末值对不上；末值候选 = {cand}')

    if not hit_any:
        return 'FIXED'          # 纯固定标题，无需校验

    if bad:
        raise ValueError(f'标题与数据矛盾 —— "{title}"\n  - ' + '\n  - '.join(bad))
    return 'OK'
