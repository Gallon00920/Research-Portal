# -*- coding: utf-8 -*-
"""末期核对：图画到哪一期 vs 源文件更新到哪一期。

Alex 2026-08-24：「以后不管每次更新都是要去文件路径下面的文件夹看最新的报告资料/excel
更新到哪一期，或者给的 pitchbook 的资料画到那一期来决定的。」

这个脚本查五件事：
  ① 账本里声明的源末期 == 图的末期
  ② 时间序列图有没有漏声明 source_latest_period（漏了就是下季会画成旧数据的位置）
  ③ 末期看起来像不像过期的（跟本季 rq 差太远就点名，让人去核）
  ④ 有没有声明 folder_freshest —— 本季文件夹里**同主题**最新的料走到哪一期
  ⑤ folder_freshest 比图末期新时：same_measure=True 就是**硬错**（文件夹里有同口径的
     新数没用上）；same_measure=False 必须写 why_not_used，写了才放行

④⑤ 是 Alex 2026-08-24 那句「你自己看看其他的有没有更新的到最新的数据？为什么 skill
连这个最简单的一点都没规定」的答案：光对「源文件走到哪」不够，还要对「文件夹里最新的料
走到哪」，两者不等时必须书面说清为什么。
"""
import io, json, re, sys
sys.path.insert(0, '.')
import exhibits

D = json.load(io.open('series.json', encoding='utf-8'))
E = D['exhibits']
RQ = D['meta'].get('rq') or D['meta'].get('cq')
RQY = int('20' + RQ[2:4]) if re.match(r'\d{4}Q\d', RQ) is None else int(RQ[:4])
EX = exhibits.load()

TIME = re.compile(r'^(\d[QH]\d\d|\d{4}|[A-Z][a-z]{2}[- ]\d{2,4}|\d{2} YTD|\d{4}-\d{4}|\d{4}[-–]\d{4})$')

fails, warns, oks, nodecl, noff = [], [], [], [], []
n_time = 0
for r in EX:
    slug, n = r['slug'], r['n']
    e = E.get(slug) or {}
    p = e.get('periods')
    if not p or not isinstance(p, list):
        continue
    if e.get('axis_kind') == 'category':
        continue                       # 账本明确标了分类轴（如到期年份分档）
    is_time = sum(bool(TIME.match(str(q))) for q in p) >= max(2, len(p) // 2)
    if not is_time:
        continue                       # 分类轴（行业、基金名…）不适用
    n_time += 1
    decl = e.get('source_latest_period')
    if not decl:
        nodecl.append((n, slug, p[-1]))
        continue
    ff = decl.get('folder_freshest')
    if not ff:
        noff.append((n, slug, p[-1]))
    else:
        same = bool(ff.get('same_measure'))
        newer = str(ff.get('period')) != str(p[-1])
        if newer and same:
            fails.append((n, slug, p[-1], ff.get('period'),
                          f'文件夹里有**同口径**更新的料（{ff.get("file")}）却没用上'))
        elif newer and not same and not (ff.get('why_not_used') or '').strip():
            fails.append((n, slug, p[-1], ff.get('period'),
                          'folder_freshest 比图末期新且口径不同，但没写 why_not_used'))
    if str(decl['chart_ends']) != str(p[-1]):
        fails.append((n, slug, p[-1], decl['chart_ends'], '声明的 chart_ends 与账本实际末期不符'))
    elif str(decl['this_quarter']) != str(p[-1]):
        fails.append((n, slug, p[-1], decl['this_quarter'], '图末期 ≠ 源末期'))
    else:
        # 末期年份离本季太远 -> 提醒人工核
        m = re.search(r'(20\d\d|\b\d\d\b)$', str(p[-1]))
        yy = None
        if m:
            g = m.group(1)
            yy = int(g) if len(g) == 4 else 2000 + int(g)
        if yy and RQY - yy >= 2:
            warns.append((n, slug, p[-1], f'末期比本季({RQY})早 {RQY-yy} 年 —— 源文件真的只到这里？'))
        else:
            oks.append((n, slug, p[-1]))

print(f'\n=== 末期核对 · {RQ} ===\n')
print(f'  时间轴图 {n_time} 张')
for n, s, a, b, why in fails:
    print(f'  ✗ Ex {n} {s}: 图到 {a}，{why}（声明 {b}）')
for n, s, a, w in warns:
    print(f'  ? Ex {n} {s}: 末期 {a} —— {w}')
for n, s, a in noff:
    print(f'  ✗ Ex {n} {s}: 末期 {a}，但 source_latest_period 里没有 folder_freshest —— '
          f'必须写清本季文件夹里同主题最新的料到哪一期，否则看不出是「源头到这儿」还是「取旧了」')
for n, s, a in nodecl:
    print(f'  ✗ Ex {n} {s}: 末期 {a}，但没声明 source_latest_period —— 必须补，'
          f'否则下季不知道该去哪儿核「源文件更新到哪一期」')
if not fails and not nodecl and not noff:
    print(f'  ✓ {len(oks)} 张图末期与声明的源末期一致；{len(warns)} 张待人工确认')
    nf = [(r['n'], r['slug'], (E[r['slug']]['source_latest_period']['folder_freshest']))
          for r in EX
          if (E.get(r['slug']) or {}).get('source_latest_period', {}).get('folder_freshest')
          and not E[r['slug']]['source_latest_period']['folder_freshest'].get('same_measure')]
    if nf:
        print()
        print(f'  ⓘ 文件夹里有更新的料、但口径不同（各自都写了理由）：{len(nf)} 张')
        for n, s2, ff in nf:
            print(f'     Ex {n} {s2}: 图到 {E[s2]["periods"][-1]}，文件夹最新 {ff["period"]}'
                  f' —— {ff["why_not_used"][:60]}…')
print()
sys.exit(1 if (fails or nodecl or noff) else 0)
