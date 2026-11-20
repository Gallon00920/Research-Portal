#!/usr/bin/env python3
"""并排列出上季与本季结论快照的差异 —— 直接喂给各处 QoQ Chg 格子。

  python3 conclusions_diff.py _state/conclusions_<PQ>.json _state/conclusions_<CQ>.json

输出四块：
  1) 券商逐家：rating / 目标价 / 立场标签 的变化，以及 key_points 的进出
  2) 公司逐家：view 标签与关键指标的变化
  3) theses：核心判断、共识、分歧、分层排序的变化
  4) open_items 闭环：上季提的议题这季有没有收口 —— 最容易漏的一块
"""
import json, sys


def load(p):
    return json.load(open(p, encoding='utf-8'))


def chg(a, b):
    a, b = (a or '—'), (b or '—')
    return f'{a} → {b}' if str(a) != str(b) else f'{a}（未变）'


def setdiff(a, b):
    a, b = set(a or []), set(b or [])
    return sorted(b - a), sorted(a - b)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    P, C = load(sys.argv[1]), load(sys.argv[2])
    print(f'# 结论环比　{P.get("cq","?")} → {C.get("cq","?")}\n')

    pb = {b['name']: b for b in P.get('brokers', [])}
    cb = {b['name']: b for b in C.get('brokers', [])}
    print('## 1. 券商')
    for n in sorted(set(pb) | set(cb)):
        p, c = pb.get(n), cb.get(n)
        if not p:
            print(f'\n**{n}**　【本季新增覆盖】　{c.get("view_label","")}')
            print(f'  rating {c.get("rating","—")}　目标价 {c.get("target_price","—")}')
            print(f'  驱动：{c.get("stance_driver","—")}')
            continue
        if not c:
            print(f'\n**{n}**　【本季无新报告】　上季立场：{p.get("view_label","")}')
            print('  → T7/T10 的 QoQ Chg 写「本季无更新，沿用上季」，不要凭空延续观点')
            continue
        print(f'\n**{n}**')
        for f, lab in (('rating', 'rating'), ('target_price', '目标价'),
                       ('valuation_basis', '估值基准'), ('view_label', '立场标签')):
            if str(p.get(f, '')) != str(c.get(f, '')):
                print(f'  {lab}：{chg(p.get(f), c.get(f))}　←── 变了')
            else:
                print(f'  {lab}：{c.get(f) or "—"}（未变）')
        print(f'  本季驱动：{c.get("stance_driver","—")}')
        added, gone = setdiff(p.get('key_points'), c.get('key_points'))
        for x in added:
            print(f'  ＋ 新增判断：{x}')
        for x in gone:
            print(f'  － 上季有本季未再提：{x}')

    pc = {x['ticker']: x for x in P.get('companies', [])}
    cc = {x['ticker']: x for x in C.get('companies', [])}
    if pc or cc:
        print('\n## 2. 软件公司')
        for t in sorted(set(pc) | set(cc)):
            p, c = pc.get(t, {}), cc.get(t, {})
            print(f'\n**{t}**　view：{chg(p.get("view_label"), c.get("view_label"))}')
            print(f'  关键指标：{chg(p.get("key_metric"), c.get("key_metric"))}')
            added, gone = setdiff(p.get('key_points'), c.get('key_points'))
            for x in added:
                print(f'  ＋ {x}')
            for x in gone:
                print(f'  － {x}')

    pt, ct = P.get('theses', {}), C.get('theses', {})
    print('\n## 3. Thesis / 共识 / 分歧 / 分层排序')
    print(f'\n2.6.1 核心判断：\n  上季：{pt.get("peer_thesis","—")}\n  本季：{ct.get("peer_thesis","—")}')
    added, gone = setdiff(pt.get('consensus'), ct.get('consensus'))
    print('\n3.2 市场共识：')
    for x in added:
        print(f'  ＋ 本季新增：{x}')
    for x in gone:
        print(f'  － 上季有本季不再列：{x}')
    if not added and not gone:
        print('  （共识条目与上季一致）')
    print('\n3.2 分歧：')
    pd = {d.get('topic'): d for d in pt.get('debates', []) if isinstance(d, dict)}
    cd = {d.get('topic'): d for d in ct.get('debates', []) if isinstance(d, dict)}
    for k in sorted(set(pd) | set(cd)):
        if k not in pd:
            print(f'  ＋ 本季新分歧「{k}」：{cd[k].get("core","")}')
        elif k not in cd:
            print(f'  － 上季分歧「{k}」本季已不列 —— 是收敛了还是被更大的分歧顶掉了？正文要交代')
        else:
            for f in ('side_a', 'side_b', 'core'):
                if pd[k].get(f) != cd[k].get(f):
                    print(f'  ~ 「{k}」的 {f}：{chg(pd[k].get(f), cd[k].get(f))}')
    pl, cl = pt.get('layer_ranking', []), ct.get('layer_ranking', [])
    print(f'\n4.3 分层排序：{"未变" if pl == cl else "变了"}')
    if pl != cl:
        print(f'  上季：{" > ".join(pl)}\n  本季：{" > ".join(cl)}')

    print('\n## 4. open_items 闭环（最容易漏）')
    po = P.get('open_items', [])
    co_topics = {o.get('topic') for o in C.get('open_items', [])}
    if not po:
        print('  上季没有留 open_items，无需收口')
    for o in po:
        state = '本季仍在列' if o.get('topic') in co_topics else '本季未再列'
        print(f'\n  【{o.get("section","?")}】{o.get("topic","?")}　—— {state}')
        print(f'    上季要盯的：{o.get("watch_next","—")}')
        print(f'    → 本季正文必须回答这一句，答完再决定是收口还是继续留在 open_items')
    for o in C.get('open_items', []):
        if o.get('topic') not in {x.get('topic') for x in po}:
            print(f'\n  【{o.get("section","?")}】{o.get("topic","?")}　—— 本季新开')


if __name__ == '__main__':
    main()
