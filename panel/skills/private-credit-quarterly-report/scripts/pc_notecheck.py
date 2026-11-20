# -*- coding: utf-8 -*-
"""Note 体检：图下脚注默认只写 `Source:` 一行。

⛔⛔ Alex 2026-08-25：「所有图片下面的 Note 一般只要写 source 就行，
   除非出现需要额外说明的 比如一些特有的词汇。」

判据：
  只有 Source 一行                        → ✓
  Source 前面还有句子                     → 必须在该 exhibit 上写 `_note_extra_reason`，
                                            值是下面 ALLOWED 里的某个类别（可多选，逗号分隔）
                                            + 一句为什么。类别对不上或没写 → ✗
类别（见 references/prose-spec.md 第四节）：
  term       图上有不解释就读不懂的自定义词/标记（26 YTD、UOP、P25–P75、† *）
  digitised  值是从源图上量的，不是源文件直接读的
  twobasis   同一张图混了两个基准日或两个口径
  gap        图上有断口 / 空心点 / 不报的格子
  junson     数字是 Junson 自己算的

用法：python3 pc_notecheck.py [--strict]
"""
import io, json, re, sys
sys.path.insert(0, '.')
import pcpaths as P
import exhibits

ALLOWED = {'term', 'digitised', 'twobasis', 'gap', 'junson'}
MAX_EXTRA_SENT = 2          # Source 之外最多两句；超过就是又写成小论文了

D = json.load(io.open(P.ledger_path(), encoding='utf-8'))
E = D['exhibits']
EX = exhibits.load()


def split_note(note):
    """返回 (Source 之前的正文, Source 行)。"""
    m = re.search(r'\bSources?\s*:', note)
    if not m:
        return note.strip(), ''
    body = note[:m.start()]
    body = re.sub(r'^\s*Note\s*:\s*', '', body).strip()
    return body, note[m.start():].strip()


clean, flagged, bad = [], [], []
for r in list(EX):
    slug, n = r['slug'], r['n']
    note = (E.get(slug) or {}).get('note') or ''
    if not note.strip():
        bad.append((n, slug, 0, 'Note 是空的 —— 至少要有 Source 行'))
        continue
    body, src = split_note(note)
    if not src:
        bad.append((n, slug, 0, '没有 Source 行'))
        continue
    if not body:
        clean.append((n, slug))
        continue
    sents = [x for x in re.split(r'(?<=[.。])\s+', body) if x.strip()]
    reason = (E[slug].get('_note_extra_reason') or '').strip()
    cats = {c.strip() for c in re.split(r'[,，/]', reason.split('—')[0]) if c.strip()}
    words = len(body.split())
    if not reason:
        bad.append((n, slug, words,
                    f'Source 之外还有 {len(sents)} 句（{words} 词）但没写 _note_extra_reason'))
    elif not cats & ALLOWED:
        bad.append((n, slug, words,
                    f'_note_extra_reason 的类别对不上 {sorted(ALLOWED)}：{reason[:60]}'))
    elif len(sents) > MAX_EXTRA_SENT:
        bad.append((n, slug, words,
                    f'Source 之外 {len(sents)} 句（上限 {MAX_EXTRA_SENT}）—— 其余搬去账本 '
                    f'_method / _caveat / _anchors'))
    else:
        flagged.append((n, slug, words, sorted(cats & ALLOWED), sents[0][:70]))

print(f'\n=== Note 体检 · {P.rq()} ===')
print(f'  只有 Source 一行：{len(clean)} 张')
if flagged:
    print(f'  ⚠ 带额外说明且理由成立：{len(flagged)} 张')
    for n, s, w, c, first in flagged:
        print(f'      Ex {n} {s}（{w} 词，{"+".join(c)}）\n          {first}…')
# ── Note / 题注里不许提「样本数印在图上」，也不许出现 n=数字 ────────────────
# ⛔ Alex 2026-08-26：「图 56 57 58 的下面都有写了个 vintage n=xxxxx，这一行都删掉，
#    **不允许出现**」。图上由 guards.assert_no_sample_counts() 硬拦；这里管纸面文字：
#    Note 里既不许自己写 n=26，也不许再说「样本数印在轴下方」（那东西已经不存在了，
#    留着就是指着一个不存在的东西让读者去找）。
_NEQ = re.compile(r'(?<![A-Za-z])n\s*=')
_ghost = []
for _slug, _e in E.items():
    for _k in ('note', 'caption'):
        _v = _e.get(_k)
        if not isinstance(_v, str):
            continue
        if _NEQ.search(_v):
            _ghost.append(f'{_slug}.{_k}: 出现 n=数字 —— 样本数只存在账本 `n` 字段里')
        if 'below the axis' in _v or 'printed below' in _v:
            _ghost.append(f'{_slug}.{_k}: 还在说样本数印在轴下方 —— 图上已经没有这行了')
if _ghost:
    print(f'  ✗ 样本数残留 {len(_ghost)} 处：')
    for _g in _ghost:
        print('      ' + _g)
    bad.append((0, '<样本数残留>', 0, '；'.join(_ghost[:3])))
else:
    print('  ✓ Note/题注里没有样本数残留（图上由 guards 硬拦）')

if bad:
    print(f'  ✗ {len(bad)} 张不合规：')
    for n, s, w, why in bad:
        print(f'      Ex {n} {s} —— {why}')
    print('\n  ⛔ 默认形态就是一行 `Source: …`。要多写，先问自己：这句删掉读者会不会**读错图**？')
    print('     会 → 留一句，并在该 exhibit 写 _note_extra_reason="<类别> — <一句理由>"')
    print('     只是知道更多 → 删掉，搬去账本 _method / _caveat / _anchors')
print()
sys.exit(1 if (bad and '--strict' in sys.argv) else 0)
