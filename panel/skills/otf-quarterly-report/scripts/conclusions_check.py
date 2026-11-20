#!/usr/bin/env python3
"""结论快照的颗粒度检查 —— 防止记成「立场转向 stabilization」这种没法做环比的空话。

  python3 conclusions_check.py _state/conclusions_<CQ>.json [--strict]

快照存在的唯一目的是给下一季的 QoQ Chg 供料。所以判定标准不是「写了没有」，
而是「下一季拿它能不能写出带驱动的环比」。据此每类记录都有必填字段和实质性门槛：
带数字、够长、不许占位词。检查不过就是记粗了，回去补。
"""
import json, re, sys

PLACEHOLDER = re.compile(
    r'^(tbd|na|n/?a|—|-+|同上|略|无|无变化|不变|待补|待定|见上|as above|no change)\s*$', re.I)
VAGUE = re.compile(r'(等等|之类|若干|一些|部分指标|多项|整体向好|整体承压|有所改善|有所恶化)')
MINLEN = 12          # 一条 key point 至少这么多字符，否则等于没说
MINPOINTS = 3        # 每家券商至少几条 key point（V4：3–4 条）
MINCONSENSUS = 4     # 3.2 市场共识至少几条（V4：4–5 条）


def has_num(s):
    return bool(re.search(r'\d', s))


def bad_text(s, need_num=False, minlen=MINLEN):
    if not isinstance(s, str) or not s.strip():
        return '空'
    t = s.strip()
    if PLACEHOLDER.match(t):
        return f'占位词「{t}」'
    if len(t) < minlen:
        return f'太短（{len(t)} 字符 < {minlen}）'
    if VAGUE.search(t):
        return f'含模糊表述「{VAGUE.search(t).group(0)}」'
    if need_num and not has_num(t):
        return '不带任何具体数字'
    return None


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    S = json.load(open(sys.argv[1], encoding='utf-8'))
    fail, warn = [], []

    def req(obj, field, where, need_num=False, minlen=MINLEN):
        v = obj.get(field)
        why = bad_text(v if isinstance(v, str) else '', need_num, minlen)
        if why:
            fail.append(f'{where} 的 {field}：{why}')

    # ── brokers ───────────────────────────────────────────────
    bs = S.get('brokers') or []
    if len(bs) < 2:
        fail.append(f'brokers 只有 {len(bs)} 家 —— 至少要覆盖当季实际收到的全部券商')
    for b in bs:
        w = f'broker「{b.get("name","?")}」'
        req(b, 'name', w, minlen=2)
        req(b, 'coverage', w, minlen=3)
        req(b, 'view_label', w, minlen=4)
        req(b, 'stance_driver', w, need_num=True, minlen=15)
        kp = b.get('key_points') or []
        if len(kp) < MINPOINTS:
            fail.append(f'{w} 的 key_points 只有 {len(kp)} 条 —— 至少 {MINPOINTS} 条，'
                        f'否则下季说不出是哪条判断动了')
        for i, p in enumerate(kp):
            why = bad_text(p, need_num=True, minlen=15)
            if why:
                fail.append(f'{w} key_points[{i}]：{why}（每条必须带具体数据）')
        if b.get('covers_otf'):
            for f in ('rating', 'target_price', 'action_date'):
                if not str(b.get(f, '')).strip():
                    fail.append(f'{w} 覆盖 OTF，缺 {f} —— T7 的 QoQ Chg 要拿它比')
            if not str(b.get('valuation_basis', '')).strip():
                warn.append(f'{w} 没写 valuation_basis（如 ~0.7x NAV）')

    # ── companies ─────────────────────────────────────────────
    cs = S.get('companies') or []
    for c in cs:
        w = f'company「{c.get("ticker","?")}」'
        req(c, 'view_label', w, minlen=4)
        req(c, 'key_metric', w, need_num=True, minlen=6)
        kp = c.get('key_points') or []
        if len(kp) < 2:
            fail.append(f'{w} 的 key_points 只有 {len(kp)} 条 —— 至少 2 条')
        for i, p in enumerate(kp):
            why = bad_text(p, need_num=False, minlen=15)
            if why:
                fail.append(f'{w} key_points[{i}]：{why}')

    # ── theses ────────────────────────────────────────────────
    th = S.get('theses') or {}
    req(th, 'peer_thesis', 'theses（2.6.1 核心判断）', minlen=30)
    cons = th.get('consensus') or []
    if len(cons) < MINCONSENSUS:
        fail.append(f'theses.consensus 只有 {len(cons)} 条 —— 至少 {MINCONSENSUS} 条（V4：4–5 条）')
    for i, p in enumerate(cons):
        why = bad_text(p, minlen=15)
        if why:
            fail.append(f'theses.consensus[{i}]：{why}')
    deb = th.get('debates') or []
    if not 1 <= len(deb) <= 2:
        fail.append(f'theses.debates 有 {len(deb)} 个 —— V4 规定至多 2 个、至少 1 个')
    for i, d in enumerate(deb):
        for f in ('topic', 'side_a', 'side_b', 'core'):
            why = bad_text(d.get(f, '') if isinstance(d, dict) else '', minlen=8)
            if why:
                fail.append(f'theses.debates[{i}].{f}：{why}（要点明谁 vs 谁、争什么）')
    lay = th.get('layer_ranking') or []
    if len(lay) < 3:
        fail.append(f'theses.layer_ranking 只有 {len(lay)} 层 —— 要存当季完整排序（最脆弱→最防御）')

    # ── open_items：上季给下季的作业，必须能闭环 ─────────────────
    oi = S.get('open_items') or []
    if not oi:
        warn.append('open_items 为空 —— 若本季 Things we should know 确实没有议题才允许')
    for i, o in enumerate(oi):
        w = f'open_items[{i}]'
        req(o, 'topic', w, minlen=6)
        req(o, 'transmission', w, minlen=20)
        req(o, 'watch_next', w, minlen=15)
        if not str(o.get('section', '')).strip():
            fail.append(f'{w} 没写 section —— 下季要回到同一小节收口')

    # ── section_notes ─────────────────────────────────────────
    sn = S.get('section_notes') or {}
    if len(sn) < 8:
        warn.append(f'section_notes 只有 {len(sn)} 节 —— 各小节的定性结论都该留一句')
    for k, v in sn.items():
        why = bad_text(v, minlen=15)
        if why:
            fail.append(f'section_notes[{k}]：{why}')

    print(f'结论快照检查：{len(fail)} 项不合格，{len(warn)} 项提醒')
    for f in fail:
        print('  ✗', f)
    for w in warn:
        print('  !', w)
    if not fail:
        print('  ✓ 颗粒度达标 —— 下一季拿它能写出带驱动的环比')
    if fail and '--strict' in sys.argv:
        sys.exit(1)


if __name__ == '__main__':
    main()
