# -*- coding: utf-8 -*-
"""§6.2 Related news 长度体检 + 券商观点表的排除/方向性主张体检。

⛔ Alex 2026-08-25：
  ① 「6.2 Related news 的新闻长度，最长不允许超过 100 个单词，不含末尾新闻链接。」
  ② 「ARES 这种肯定不能出现的，一定要把 specific 的公司排除！」
  ③ QoQ Chg 里的方向性主张（tone improved / unchanged / upgraded）必须有账本里的
     上季立场做依据 —— 没有就不许写方向（我给 GS 写反过一次）。

用法：python3 pc_newscheck.py <成稿>.docx [--strict]
      不给 docx 就只跑账本侧的 ②③。
"""
import io, json, re, sys, zipfile, html
sys.path.insert(0, '.')
import pcpaths as P

MAXW = 100
D = json.load(io.open(P.ledger_path(), encoding='utf-8'))
E = D['exhibits']
bad = []

# ── ① Related news 每条 ≤100 词（不含末尾链接）──────────────────────
doc = next((a for a in sys.argv[1:] if a.endswith('.docx')), None)
if doc:
    x = re.sub(r'</w:p>', '\n', zipfile.ZipFile(doc).read('word/document.xml').decode('utf8'))
    lines = html.unescape(re.sub(r'<[^>]+>', '', x)).split('\n')
    i0 = next((i for i, l in enumerate(lines) if 'Related news' in l), None)
    if i0 is None:
        bad.append('成稿里找不到 §6.2 Related news')
    else:
        n_items = 0
        for l in lines[i0 + 1:]:
            s = ' '.join(l.split())
            if not s:
                continue
            if not s.startswith('·'):
                break                      # 下一节开始了
            n_items += 1
            body = re.sub(r'https?://\S+', '', s)          # 去掉末尾链接
            body = re.sub(r'\s*\([^)]*\d{4}[^)]*\)\s*$', '', body)   # 去掉尾部「(出版方, 日期)」
            w = len(body.split())
            if w > MAXW:
                bad.append(f'§6.2 第 {n_items} 条 {w} 词（上限 {MAXW}）：{body[:70]}…')
        print(f'  §6.2 Related news：{n_items} 条，'
              f'{sum(1 for b in bad if "§6.2" in b)} 条超 {MAXW} 词')
else:
    print(f'  §6.2 未查（没给成稿 docx）')

# ── ② 券商观点表不许出现个股研报 ─────────────────────────────────
bs = E.get('sent_broker_summary') or {}
ISSUER = re.compile(r'\bARES\b|Ares Management|\bOTF\b|\bBXSL\b|\bORCC\b|Corp\b|Inc\b'
                    r'|target price|Equal-?weight|Overweight|Underweight', re.I)
for c in bs.get('columns_en', []):
    if ISSUER.search(c.get('reports', '')):
        bad.append(f'券商观点表 {c["house"]} 的 reports 串里有个股研报：{c["reports"]}')
excl = [r['label'] for r in bs.get('rows', []) if r.get('_excluded_from_table')]
print(f'  券商观点表：{len(bs.get("columns_en", []))} 家；'
      f'主动排除并留痕的个股研报 {len(excl)} 份 {excl if excl else ""}')

# ── ③ QoQ 里的方向性主张必须有上季立场做依据 ───────────────────────
DIRECT = re.compile(r'\b(improved|deteriorat\w+|unchanged|upgraded|downgraded|better than|'
                    r'worse than)\b|vs\s*[1-4]Q', re.I)
hist = bs.get('stance_history') or {}
qs = sorted(k for k in hist if re.fullmatch(r'\d{4}Q[1-4]', k))
prev = qs[-2] if len(qs) >= 2 else None
MONTHS = ('January|February|March|April|May|June|July|August|September|October|'
          'November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec')
CROSSQ = re.compile(r'vs\s*[1-4]Q|vs\s*(last|prior|previous)\s*quarter|'
                    r'(?<!\w)(improved|deteriorated|unchanged|upgraded|downgraded)(?!\w)', re.I)
for c in bs.get('columns_en', []):
    q = c.get('qoq', '')
    m = DIRECT.search(q)
    if not m:
        continue
    # 同季内比较（例：「July tone better than April」）—— 两个端点都在本季文件夹里，
    # 由 reports 串的日期证明，不需要 stance_history。
    months = set(re.findall(MONTHS, q, re.I))
    rep_months = len(re.findall(r'\b\d{1,2}/\d{1,2}\b', c.get('reports', '')))
    if len(months) >= 2 and rep_months >= 2 and not CROSSQ.search(q):
        continue
    if not prev or c['house'] not in (hist.get(prev) or {}):
        bad.append(f'券商观点表 {c["house"]} 的 QoQ 写了跨季方向性主张「{m.group(0)}」，'
                   f'但账本 stance_history 里没有上季（{prev or "无"}）这家的立场 —— '
                   f'⛔ 无据的方向不许写。同季内比较（两份都在本季文件夹）要把两个端点'
                   f'都写出来（例：July tone better than April）才算有据。')
print(f'  QoQ 方向性主张：上季基准 {prev or "无（本季是第一季，任何方向都写不了）"}')

if bad:
    print(f'\n  ✗ {len(bad)} 处不合规：')
    for b in bad:
        print('      ' + b)
else:
    print('\n  ✓ 三项都合规')
print()
sys.exit(1 if (bad and '--strict' in sys.argv) else 0)
