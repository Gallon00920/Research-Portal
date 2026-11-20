# -*- coding: utf-8 -*-
"""图内一致性体检：一张图的散文里出现的数，必须在**这张图自己的数据字段**里找得到。

⛔ 2026Q3 踩过（Alex 2026-08-25 抓出来）：图 31 的图下 Note 写「195 → 209」，
   同一张图的侧栏 bullet 却写「194 → 207」—— 一张图里两套数，差 2bn，活到了 v4。
   `pc_crosscheck` 抓不到，因为它是拿全本账本当值池、逐个数比对；
   194/207 在账本里（就写在那条 bullet 自己的 text 里），所以「命中账本」。

   本脚本换一个角度：**范围收到单张图内**。
   题注 / Note / 侧栏 / bullet 里的每个数，只允许来自这张图的数据字段
   （series/lines/stacks/vals/rows/points/median/p25/p75/aux/ytd/scale/n_* …）。
   找不到 → 报出来。这样「同一事实两个版本」必然有一个落在图外，一定被抓到。

用法：python3 pc_factcheck.py [--strict]
"""
import io, json, re, sys
sys.path.insert(0, '.')
import pcpaths as P
import exhibits

D = json.load(io.open(P.ledger_path(), encoding='utf-8'))
E = D['exhibits']
EX = exhibits.load()

PROSE_KEYS = {'note', 'caption_rendered', 'text', 'title', 'label',
              'groups_note', 'gap_label'}
# 这些键里的数字是「说明/病历/口径」，不是对读者的数值主张 —— 不查
SKIP_PROSE = re.compile(r'^_|^src$')

NUM = re.compile(r'(?<![\w.,%-])(\d[\d,]*(?:\.\d+)?)')


def _prose(ent):
    """收集这张图所有会印到纸上的散文（含侧栏 bullet），带字段路径。"""
    out = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if SKIP_PROSE.match(str(k)):
                    continue
                if k in PROSE_KEYS and isinstance(v, str):
                    out.append(('/'.join(path + (str(k),)), v))
                else:
                    walk(v, path + (str(k),))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, path + (str(i),))
    walk(ent, ())
    return out


def _data_numbers(ent):
    """这张图的数据字段里所有数值（含各种精度的四舍五入形态）。"""
    vals = set()

    def walk(o, key=''):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in PROSE_KEYS or k == 'src' or str(k).startswith('_'):
                    continue
                walk(v, str(k))
        elif isinstance(o, list):
            for v in o:
                walk(v, key)
        elif isinstance(o, bool):
            return
        elif isinstance(o, (int, float)):
            vals.add(float(o))
        elif isinstance(o, str) and len(o) <= 40:
            for m in NUM.finditer(o):
                try:
                    vals.add(float(m.group(1).replace(',', '')))
                except ValueError:
                    pass
    walk(ent)
    # 派生形态：四舍五入到 0/1/2 位、÷1000（$m→$bn）、×100 / ÷100（比例↔百分数）
    grown = set()
    for v in vals:
        for w in (v, v / 1000.0, v * 1000.0, v * 100.0, v / 100.0):
            for dp in (0, 1, 2, 3):
                grown.add(round(w, dp))
    return grown


# meta 里的全局口径数（筛选样本数、导出日、期名）任何一张图都可以引用 —— 并进每张图的池子
_META_POOL = _data_numbers({k: v for k, v in (D.get('meta') or {}).items()
                            if k in ('screen', 'as_of', 'periods', 'comparator_set')})

bad, checked = [], 0
for r in list(EX):
    slug, n = r['slug'], r['n']
    ent = E.get(slug)
    if not ent:
        continue
    pool = _data_numbers(ent) | _META_POOL
    # 显式豁免：口径定义里的门槛值（"BDCs with total assets above $50m"、"rolling 90-day"）
    # 不是对读者的数值主张,不必有数据字段。⛔ 必须逐条写理由 —— 空着或只写数字不算豁免,
    # 目的是让豁免看得见,而不是让检查安静下来。
    _ex = ent.get('_prose_exempt') or {}
    if _ex and not all(isinstance(v, str) and len(v) >= 6 for v in _ex.values()):
        bad.append((n, slug, '_prose_exempt', 0.0,
                    '豁免必须逐条写理由（≥6 字），不许留空'))
    exempt = set()
    for k in _ex:
        try:
            exempt.add(float(str(k)))
        except ValueError:
            pass
    # 期名、年份、编号不算数值主张
    for path, txt in _prose(ent):
        for m in NUM.finditer(txt):
            raw = m.group(1).replace(',', '')
            try:
                v = float(raw)
            except ValueError:
                continue
            if len(raw.replace('.', '')) < 2:
                continue
            if 1900 <= v <= 2100 and '.' not in raw:
                continue          # 年份
            after = txt[m.end():m.end() + 14]
            before = txt[max(0, m.start() - 26):m.start()]
            # 日期：「31 March 2026」「1 April」
            if re.match(r'\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', after):
                continue
            # sheet / 文件名 / 引号里的编号：「sheet "07 BDC Maturity Wall"」
            if re.search(r'(sheet|slide|table|figure|exhibit|p\.|page)\s*[“"\u2018\']?$',
                         before, re.I):
                continue
            # 区间的后半截：「5–7yr」「2021–22」「US$230–250bn」
            if re.search(r'[\d](\s*[–—-]\s*)$', before):
                continue
            checked += 1
            if any(round(v, dp) in pool for dp in (0, 1, 2, 3)):
                continue
            if v in exempt:
                continue
            ctx = ' '.join(txt[max(0, m.start() - 55):m.end() + 30].split())
            bad.append((n, slug, path, v, ctx))

print(f'\n=== 图内一致性 · {P.rq()} ===')
print(f'  查了 {checked} 个「散文里的数值主张」，覆盖 {len(list(EX))} 张图\n')
if bad:
    print(f'  ✗ {len(bad)} 个数在本图散文里出现，但本图数据字段里没有：')
    for n, slug, path, v, ctx in bad[:30]:
        print(f'      Ex {n} {slug} · {path}\n          {v} —— …{ctx}…')
    print('\n  处理顺序：')
    print('    1) 先判断是「散文抄错」还是「数据字段缺这个数」')
    print('    2) 抄错 → 改散文，并**全图搜一遍这个事实**（题注/Note/侧栏/正文/跨节引用一起改）')
    print('    3) 数据缺 → 按 report-spec 写进对应字段并带 src，再重跑 pc_review_sheet')
else:
    print('  ✓ 每张图的散文数值都能在本图数据字段里找到')
print()
sys.exit(1 if (bad and '--strict' in sys.argv) else 0)
