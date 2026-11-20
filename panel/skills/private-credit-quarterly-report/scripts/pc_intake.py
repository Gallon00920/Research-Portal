# -*- coding: utf-8 -*-
"""取数**之前**跑：清点本季文件夹，缺什么列成一张表交用户选，不硬停。

⛔ Alex 2026-08-26：「不要太死板哦」—— 缺一两份源报告是常态，不该拦住整篇稿。
   原来的行为是 src_audit 在取数**之后** exit 1，只说「炸了，是这几张」，
   不给路选。这个脚本把判断提前到清点阶段，并把选项摆出来。

用法：
    python3 pc_intake.py            → 打印清点结果与缺料清单
    python3 pc_intake.py --json     → 机器可读
    python3 pc_intake.py --apply    → 把缺料影响到的 exhibit 写进账本 meta.skipped（本季整块删掉）

⛔ 2026-11 起的规则（覆盖下面各处旧说法）：缺哪份源文件，就跳过靠它的图和正文，**报告里整块删掉**
   —— 不问用户、不等补件、不标 not updated、不沿用上季值。删掉的图不占编号（exhibits.load()
   读 meta.skipped），并排的另一张改单独一行；正文里引用它的句子、表行、Summary 条目一起删。

判据来自账本本身：每个 exhibit 的 `src_files` 说了它靠哪几个文件。把上一季的清单
按「同一份来源的本季那一期」去文件夹里找 —— 找到就算齐，找不到就进待决清单。
⛔ 这里**不做任何猜测性替换**：只按 `source_latest_period.how_to_find_next_quarter`
   里写好的位置去找。找不到就问，不许自己拿别的文件顶上。
"""
import io, json, os, re, sys
sys.path.insert(0, '.')
import pcpaths as P
import exhibits

D = json.load(io.open(P.ledger_path(), encoding='utf-8'))
E = D['exhibits']
RQ = P.rq()
QD = P.quarter_dir()

ACT = {}
for root, _, fs in os.walk(QD):
    for f in fs:
        ACT[f.lower()] = os.path.relpath(os.path.join(root, f), QD).replace('\\', '/')

# 一份来源的「身份」= 去掉期数标签之后的名字。期数会变，身份不会。
_QTOK = re.compile(r'\b\d[Qq]\d\d\b|\b20\d\d[ _-]?[Qq]\d\b|\b[Qq]\d[ _-]?20\d\d\b'
                   r'|\b20\d\d\b|\b\d{4}[_-]\d\d[_-]\d\d(?:[_-]\d\d[_-]\d\d[_-]\d\d)?\b')


def ident(fn):
    """文件身份：把期数/日期标签抹掉，剩下的就是「哪一份报告」。"""
    b = os.path.basename(fn).lower()
    b = _QTOK.sub('#', b)
    return re.sub(r'[\s_\-–—]+', ' ', b).strip()


HAVE = {}
for low, rel in ACT.items():
    HAVE.setdefault(ident(rel), []).append(rel)

need = {}          # 身份 -> {用到它的 exhibit, 上季的文件名, 该去哪儿找}
for r in exhibits.load():
    slug, n = r['slug'], r['n']
    ent = E[slug]
    for f in (ent.get('src_files') or []):
        k = ident(f)
        it = need.setdefault(k, {'exhibits': [], 'prev': set(), 'where': set()})
        it['exhibits'].append((n, slug))
        it['prev'].add(f)
        slp = ent.get('source_latest_period') or {}
        w = slp.get('how_to_find_next_quarter')
        if w:
            it['where'].add(w)

ready, pending = [], []
for k, it in sorted(need.items()):
    if k in HAVE:
        ready.append((k, HAVE[k], it))
    else:
        pending.append((k, it))

# 缺料 → 本季删掉的 exhibit：靠任何一份缺失文件的图都删（缺一份就画不全）
drop = {}
for k, it in pending:
    for _n, slug in it['exhibits']:
        drop.setdefault(slug, []).append(sorted(it['prev'])[0])

if '--apply' in sys.argv:
    led_path = os.environ.get('PC_LEDGER', 'series.json')
    D = json.load(io.open(led_path, encoding='utf-8'))
    keep = [x for x in D['meta'].get('skipped', []) if not (isinstance(x, dict) and x.get('rq') == RQ)]
    D['meta']['skipped'] = keep + [{'slug': s_, 'missing': '; '.join(sorted(set(f))), 'rq': RQ} for s_, f in sorted(drop.items())]
    io.open(led_path, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1))
    print(f'✓ 账本 meta.skipped 写入 {len(drop)} 个本季删掉的 exhibit（{RQ}）')
    sys.exit(0)

if '--json' in sys.argv:
    print(json.dumps({
        'rq': RQ, 'quarter_dir': QD,
        'ready': [{'ident': k, 'files': f, 'exhibits': [s for _, s in it['exhibits']]}
                  for k, f, it in ready],
        'pending': [{'ident': k,
                     'exhibits': [f'Ex {n} {s}' for n, s in it['exhibits']],
                     'prev_files': sorted(it['prev']),
                     'where_to_look': sorted(it['where']),
                     'action': 'dropped this quarter (exhibits and the text that cites them)'}
                    for k, it in pending],
    }, ensure_ascii=False, indent=1))
    sys.exit(0)

print(f'\n=== 本季来源清点 · {RQ} ===')
print(f'  文件夹：{QD}')
print(f'  文件夹里有 {len(ACT)} 个文件；账本认得 {len(need)} 份来源')
print(f'\n  ✓ 齐备 {len(ready)} 份：')
for k, fs, it in ready:
    print(f'      {fs[0]}   ← 喂 {len(it["exhibits"])} 张图')
if not pending:
    print(f'\n  ✓ 没有缺料，可以开始取数')
else:
    print(f'\n  ⚠ 缺 {len(pending)} 份 —— 不是错误：靠它们的图和正文本季整块删掉：')
    for k, it in pending:
        exs = ', '.join(f'Ex {n}' for n, _ in it['exhibits'][:8])
        print(f'\n      ── {sorted(it["prev"])[0]}')
        print(f'         影响 {len(it["exhibits"])} 张图：{exs}')
    print(f'\n  → 本季删掉 {len(drop)} 张图：{", ".join(sorted(drop))[:300]}'
          f'\n     跑 `python3 pc_intake.py --apply` 写进账本 meta.skipped；编号自动顺延，'
          f'\n     正文、Summary 里引用它们的句子与表行一起删，交付说明里列出缺了哪些文件、删了哪些图。')
print()
sys.exit(0)          # ⛔ 清点不失败 —— 它的产出是缺料清单，不是判决
