# -*- coding: utf-8 -*-
"""末点体检：每条画出来的序列，末期都必须有值 —— 不许「账本里有、图上不画」。

⛔ Alex 2026-08-25：「图7 你要定死，必须更新到最新，就算没有完整一年的，
   但是 YTD，你就要画出来。」

背景：图 7 的 `26 YTD` 利差 144bps 一直在账本里（ytd.2026_through_March），
却因为「三个月不能跟年均比」没画 —— 而同一张图上 2 个月的 2020、7 个月的 2021、
6 个月的 2022 全都画了（就是为此才有「<9 个月画空心点」的约定）。
对某一期单独发明理由 = 自己藏数据，下季换个人跑会以为源文件没有。

判据：时间轴 exhibit 的每条画出来的序列，最后一期不许是 None。
要留空必须在该 exhibit 上写 `_last_null_reason`，逐条说明是**哪条序列、为什么**，
并且理由必须指向源文件（源图就到那一期 / 源表没有这一列）。
⛔ 「不可比 / 窗口太短 / 不完整」不算理由 —— 那是画法问题（空心点、虚线、标注），
不是不画的理由。脚本会直接顶回来。

用法：python3 pc_lastpoint.py [--strict]
"""
import io, json, re, sys
sys.path.insert(0, '.')
import pcpaths as P
import exhibits

D = json.load(io.open(P.ledger_path(), encoding='utf-8'))
E = D['exhibits']
EX = exhibits.load()

# 会画出来的序列容器
SERIES_HOLDERS = ('lines', 'series', 'stacks', 'median', 'p25', 'p75', 'vals')

# ⚠ 判据必须是「有没有指到源文件」这种**正向语义**，不是「有没有出现某个词」。
#   第一版写的是 BAD_REASON=不可比|太短|… 结果把「⛔ 不是『不可比』不画，是源文件没有这一期」
#   这种正确理由也毙掉了 —— 和 `'ylim' not in ln` 一模一样的错（SKILL 硬要求第七条）。
import os
_QD = P.quarter_dir()
_FILES = set()
for _root, _, _fs in os.walk(_QD):
    for _f in _fs:
        _FILES.add(_f.lower())
        _st = re.sub(r'\.(pdf|xlsx|xls|csv|docx|json)$', '', _f.lower())
        if len(_st) >= 8:
            _FILES.add(_st)
LOCATOR = re.compile(r'\b(slide|sheet|p\.?\d|page\s*\d|表|页|图)\b|"[^"]{6,}"|“[^”]{6,}”')
EMPTY_EXCUSE = re.compile(r'不可比|太短|不完整|not comparable|incomplete|partial (?:year|window)', re.I)


def reason_ok(why):
    low = why.lower()
    names_file = any(f in low for f in _FILES)
    has_loc = bool(LOCATOR.search(why))
    return names_file and has_loc

bad, waived, ok = [], [], 0
for r in list(EX):
    slug, n = r['slug'], r['n']
    ent = E.get(slug) or {}
    if ent.get('axis_kind') == 'category':
        continue                      # 分类轴没有「末期」
    axis = ent.get('periods') or ent.get('labels')
    if not axis:
        continue
    xs = ent.get('x_start')
    reasons = ent.get('_last_null_reason') or {}

    def check(name, arr):
        global ok
        if not isinstance(arr, list) or len(arr) != len(axis):
            return
        if arr[-1] is not None:
            ok += 1
            return
        why = reasons.get(name)
        if not why:
            bad.append((n, slug, name, axis[-1], '末期留空但没写 _last_null_reason'))
        elif reason_ok(why):
            waived.append((n, slug, name, axis[-1], why[:110]))
        elif EMPTY_EXCUSE.search(why):
            bad.append((n, slug, name, axis[-1],
                        '理由只说了「不可比/太短/不完整」，没指到源文件的具体位置 —— '
                        '观测期不足是画法问题（空心点/虚线），不是不画的理由'))
        else:
            bad.append((n, slug, name, axis[-1],
                        '理由没有指到本季文件夹里的具体文件 + slide/表/页 —— '
                        f'必须写清源文件在哪一期就断了：{why[:60]}'))

    for holder in SERIES_HOLDERS:
        v = ent.get(holder)
        if isinstance(v, dict):
            for k, arr in v.items():
                if not str(k).startswith('_'):
                    check(f'{holder}.{k}', arr)
        elif isinstance(v, list):
            check(holder, v)
    rl = ent.get('rhs_line')
    if isinstance(rl, dict):
        check('rhs_line.vals', rl.get('vals'))

print(f'\n=== 末点体检 · {P.rq()} ===')
print(f'  末期有值的序列：{ok} 条')
if waived:
    print(f'  ⚠ 末期留空但写了源文件依据 {len(waived)} 条（每季要重新确认源文件是否已经补上）：')
    for n, s, nm, per, why in waived:
        print(f'      Ex {n} {s} · {nm}（末期 {per}）\n          {why}')
if bad:
    print(f'  ✗ {len(bad)} 条序列末期留空且不该留：')
    for n, s, nm, per, why in bad:
        print(f'      Ex {n} {s} · {nm}（末期 {per}）\n          {why}')
    print('\n  ⛔ 账本里有值就必须画出来。观测期不足就用空心点/虚线 + Note 说明，不是不画。')
else:
    print('  ✓ 没有「账本里有、图上不画」的末点')
print()
sys.exit(1 if (bad and '--strict' in sys.argv) else 0)
