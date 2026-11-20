#!/usr/bin/env python3
"""扫最终报告 docx 里的每个数字，回 series.json 核 —— 抓图文矛盾。

  python3 crosscheck.py REPORT.docx [--strict]

核心是「近似但不相等」检测：正文写 16.49、账本是 16.48，两处各自看着都自洽，
通读发现不了，但只要值接近却不等，就极可能是抄错或另抽了一遍。
这正是把生图和正文合成一个 skill 要防的那类错。

判定：
  完全命中账本某个值                        → OK
  与某个账本值近似、且主题词与上下文相符      → **可疑矛盾**，报出来
  其余                                     → 账本外的数（新闻数字、目标价、研报口径），列出待人工确认

主题词匹配是关键：不做的话股价 266.91 会撞上 EBITDA 266.0 这种毫无关系的值，
噪音把真问题埋掉。只有当账本那一项的标签词（行标、系列名、图名）与正文该数字周围的词
重合 ≥ MINOVERLAP 个时，才拿来比。只重合一个词（比如仅 ticker）不算。
"""
import json, re, sys, zipfile
from collections import defaultdict

NEAR = 0.5          # 相对差阈值：|a-b| ≤ NEAR% 的绝对值 → 视为近似
MINOVERLAP = 2      # 主题词至少要重合几个才算「同一件事」。1 个太松：
                    #   跌幅表里的股价只靠 ticker 就能撞上 NAV/股，全是噪音
MINLEN = 2          # 只查两位及以上有效数字，避免 1、2、3 这种编号噪音


def docx_text(p):
    with zipfile.ZipFile(p) as z:
        x = z.read('word/document.xml').decode('utf-8')
    x = re.sub(r'</w:p>', '\n', x)
    x = re.sub(r'<[^>]+>', '', x)
    return x


STOP = {'series', 'rows', 'items', 'vals', 'other', 'ylim', 'ytick', 'window',
        'max', 'pct', 'ps', 'and', 'the', 'per', 'memo', 'total', 'chg', 'qoq',
        'fig', 'tbl', 'cq', 'pq', 'avg', 'at', 'of'}


def tokens(*parts):
    """把路径/标签切成可跟正文上下文比对的词。"""
    out = set()
    for p in parts:
        for w in re.split(r'[^0-9A-Za-z\u4e00-\u9fff]+', str(p).lower()):
            if len(w) >= 3 and w not in STOP and not w.isdigit():
                out.add(w)
    return out


def ledger_values(d):
    """账本里所有数值 → [(值, 路径, 词集)]，词集用于跟正文上下文做主题匹配。
    不做主题匹配的话，股价 266.91 会撞上 EBITDA 266.0 这种毫无关系的值。"""
    out = []

    def walk(o, path, labels):
        if isinstance(o, dict):
            lab = labels | ({str(o['label'])} if isinstance(o.get('label'), str) else set())
            if isinstance(o.get('v'), (int, float)):
                out.append((round(float(o['v']), 4), '/'.join(path), tokens(*path, *lab)))
            for k, v in o.items():
                if k in ('src', 'note', '_note', 'footnote', 'label'):
                    continue
                walk(v, path + (str(k),), lab)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, path + (str(i),), labels)
        elif isinstance(o, (int, float)):
            out.append((round(float(o), 4), '/'.join(path), tokens(*path, *labels)))
        elif isinstance(o, str):
            m = re.fullmatch(r'\s*([+-]?\d+(?:\.\d+)?)\s*%?\s*', o)
            if m:
                out.append((round(float(m.group(1)), 4), '/'.join(path), tokens(*path, *labels)))
    walk(d.get('charts', {}), (), set())
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    doc = sys.argv[1]
    LV = ledger_values(json.load(open('series.json', encoding='utf-8')))
    exact = {v for v, _, _ in LV}
    txt = docx_text(doc)

    suspect, outside = [], []
    seen = set()
    for m in re.finditer(r'(?<![\w.])(\d+(?:\.\d+)?)\s*(%|x|bp|pp)?', txt):
        raw, unit = m.group(1), m.group(2) or ''
        if len(raw.replace('.', '')) < MINLEN:
            continue
        v = round(float(raw), 4)
        if 1900 <= v <= 2100 and '.' not in raw:
            continue
        ctx = txt[max(0, m.start() - 90):m.end() + 40].replace('\n', ' ').strip()
        key = (v, unit, ctx[:40])
        if key in seen:
            continue
        seen.add(key)
        if v in exact:
            continue
        ctok = tokens(ctx)
        near = [(k, p) for k, p, tk in LV
                if k and abs(k - v) <= abs(v) * NEAR / 100 and k != v and len(tk & ctok) >= MINOVERLAP]
        if near:
            suspect.append((v, unit, near[:3], ctx))
        else:
            outside.append((v, unit, ctx))

    print(f'账本里 {len(exact)} 个不同数值；正文扫出 {len(seen)} 个数字位置')
    print(f'\n=== 可疑矛盾 {len(suspect)} 处（近似但不相等，重点看这里）===')
    for v, u, near, ctx in suspect[:40]:
        pairs = '，'.join(f'{k}（{p}）' for k, p in near)
        print(f'  正文 {v}{u}　账本最近值 {pairs}')
        print(f'      …{ctx}…')
    print(f'\n=== 账本外的数 {len(outside)} 处（新闻/目标价/研报口径，人工确认）===')
    for v, u, ctx in outside[:25]:
        print(f'  {v}{u}　…{ctx[:90]}…')
    if len(outside) > 25:
        print(f'  …另有 {len(outside)-25} 处')

    # ── 门的漏洞补丁 ────────────────────────────────────────────────
    # approve.py 只校验 PNG 与 series.json 的 sha256。阶段二完全可以在自己的
    # 容器里现抽一批表格数据写进 docx，门看不见 —— 实测发生过：T4/T5/T6 的 34 个数
    # 在签收之后被抽出来直接进正文，账本和清单里都没有，用户无从核对。
    #
    # 判据不能用「账本外的数总量」—— 新闻数字、卖方目标价、研报口径本来就在账本外，
    # 一份完整报告有几百个是正常的。要精准命中：账本外的数里，凡上下文出现
    # 08_tables.md 规定该进账本的那几张表的行标，就是漏出来的表格数据。
    LEDGER_TABLE_CUES = {
        'T4 借款人基本面': ['weighted average revenue', 'weighted avg revenue',
                            'weighted average ebitda', 'weighted avg ebitda',
                            'enterprise value', 'net ltv', 'average position size',
                            'portfolio companies'],
        'T5 融资结构': ['revolving credit facility', 'spv asset facility', 'clo',
                        'total debt', 'unsecured share', 'available liquidity',
                        'committed', 'drawn'],
        'T6 杠杆与资本': ['net leverage', 'target range', 'asset coverage',
                          'debt capacity', 'statutory floor'],
    }
    leaked = []
    for v, u, ctx in outside:
        low = ctx.lower()
        for tname, cues in LEDGER_TABLE_CUES.items():
            if any(c in low for c in cues):
                leaked.append((tname, v, u, ctx))
                break
    if leaked:
        by_t = {}
        for tname, v, u, ctx in leaked:
            by_t.setdefault(tname, []).append(f'{v}{u}')
        print(f'\n⛔ 有 {len(leaked)} 个数在账本外，但按 08_tables.md 本该在账本里：')
        for tname, vals in by_t.items():
            print(f'   {tname}：{len(vals)} 个 —— {", ".join(vals[:10])}'
                  + ('…' if len(vals) > 10 else ''))
        print('   这批数没进账本、没上核对清单、也没经过门。处理顺序：')
        print('     1) 按 08_tables.md 写进 series.json（tbl04/tbl05/tbl06），每行带 src')
        print('     2) 重跑 review_sheet.py，把清单落到 out/')
        print('     3) 交用户核对新增那几行，用户确认后 approve.py --sign（不要自己代签）')
        print('     4) 再跑本脚本，这一节应该清零')
        if '--strict' in sys.argv:
            sys.exit(1)

    if suspect and '--strict' in sys.argv:
        sys.exit(1)


if __name__ == '__main__':
    main()
