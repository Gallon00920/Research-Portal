# -*- coding: utf-8 -*-
"""末期证据表：图画到哪一期 / 该口径的源文件最多能给到哪一期 / 文件夹里同主题最新的料到哪一期。

Alex 2026-08-24：「你自己看看其他的有没有更新的到最新的数据」——不靠嘴说，逐张摆证据。
Alex 2026-08-25：⛔ 不许写死本季的期名清单 —— 下季全变。

所以这个脚本**不带任何期名表**：三条时间线全部从账本的
`source_latest_period`（含 `folder_freshest`）读；「今天」取系统日期。
下季只要账本更新了，这张表自动跟着变。
"""
import io, json, re, sys, datetime
sys.path.insert(0, '.')
import pcpaths as P
import exhibits

D = json.load(io.open(P.ledger_path(), encoding='utf-8'))
E, M = D['exhibits'], D['meta']
EX = exhibits.load()
TODAY = datetime.date.today().strftime('%Y-%m')

AXIS_FIELDS = ('periods', 'labels', 'vintages', 'groups')


def last_of(e):
    """账本里横轴末期。四种字段形状按顺序试 —— 不是每张图都用 periods。"""
    for f in AXIS_FIELDS:
        v = e.get(f)
        if isinstance(v, list) and v:
            return str(v[-1]), f
    return None, None


rows, stale, nodecl = [], [], []
for r in list(EX):
    slug, n = r['slug'], r['n']
    e = E.get(slug) or {}
    d = e.get('source_latest_period')
    if not d:
        continue                                    # 非时间轴或未声明,pc_period_check 会点名
    got, fld = last_of(e)
    cap = str(d.get('this_quarter'))
    ff = d.get('folder_freshest') or {}
    is_cat = e.get('axis_kind') == 'category'
    same = bool(ff.get('same_measure'))
    verdict = ('分类轴，末期看 as_of' if is_cat
               else '源上限' if str(ff.get('period')) == cap
               else f'源上限；文件夹里 {ff.get("period")} 更新但'
                    + ('**同口径 —— 应该用上**' if same else '口径不同'))
    okk = is_cat or (got is not None and (got == cap or cap in got or got in cap))
    if not okk:
        stale.append((n, slug, got, cap))
    rows.append((n, slug, fld or '?', got, cap, str(ff.get('period') or '—'), same, verdict))

print(f'\n=== 末期证据表 · {M.get("rq")}（今天 {TODAY}）===\n')
print('%-4s %-27s %-8s %-11s %-11s %-9s %s' %
      ('Ex', 'slug', '轴字段', '图到', '该口径源上限', '文件夹最新', '结论'))
print('-' * 126)
for n, slug, fld, got, cap, ffp, same, verdict in rows:
    print('%-4s %-27s %-8s %-11s %-11s %-9s %s' %
          (n, slug, fld, str(got), cap, ffp, verdict))
print()
print(f'  共 {len(rows)} 张声明了末期的图')
print('  图末期 ≠ 该口径源上限的：', stale if stale else '无 —— 每一张都取到了源文件的极限')
_cat = {r['slug'] for r in list(EX) if (E.get(r['slug']) or {}).get('axis_kind') == 'category'}
diff = [(n, slug, ffp) for n, slug, _, _, cap, ffp, same, _ in rows
        if ffp not in ('—', cap) and not same]
if diff:
    print(f'\n  ⓘ 文件夹里有更新的料、但口径不同（各自在账本里写了理由）：{len(diff)} 张')
    for n, slug, ffp in diff:
        why = (E[slug]['source_latest_period']['folder_freshest'].get('why_not_used') or '')[:70]
        print(f'     Ex {n} {slug} → 文件夹最新 {ffp}：{why}…')
hard = [(n, slug, ffp) for n, slug, _, _, cap, ffp, same, _ in rows
        if same and ffp not in ('—', cap) and slug not in _cat]
if hard:
    print(f'\n  ✗ 文件夹里有**同口径**更新的料却没用上：{hard}')
print()
sys.exit(1 if (stale or hard) else 0)
