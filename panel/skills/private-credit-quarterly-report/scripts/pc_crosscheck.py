#!/usr/bin/env python3
"""扫最终报告 docx 里的每个数字，回 series.json 核 —— 抓图文矛盾。（Private Credit 季报版）

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


# ⛔ 账本里的**散文字段**不许进「权威值池」。
# 2026Q3 踩过:Ex 31 侧栏 bullet 的 text 里写着基线那两个错数（194 / 207），
# 而 text 不在 SKIP_KEYS 里、串长又 < 400，于是它自己把自己验证成「命中账本」——
# 图下 Note 写 195→209、同一张图的侧栏写 194→207，检查却报 0 矛盾。
# 散文只能被检查，不能当判据。
SKIP_KEYS = {
    'src', 'note', 'footnote', 'label', 'source_line', 'caption_rendered',
    'text', 'title', 'conclusion', 'differs', 'match', 'compared', 'rule',
    'definition', 'criteria', 'criteria_en', 'row_count_note',
    'own_funds_disclosure', 'basis_marker', 'groups_note',
    'periods', 'labels', 'groups', 'ylim', 'ytick', 'rhs_ylim', 'rhs_ytick',
    'as_of', 'basis_note', 'observation_dates', 'series_patterns', 'metric_label',
    'highlight', 'x_field', 'y_field', 'size_field', 'window_max',
}


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
                # 跳过：来源/注释文字、以及一切不是「数据」的字段。
                # 不跳的话 _section 的 2.1、periods 里的 2015、ylim 的 0/100
                # 都会进比对池，正文里随便一个年份或小节号都能撞上，噪音把真矛盾埋掉。
                if k in SKIP_KEYS or k.startswith('_'):
                    continue
                walk(v, path + (str(k),), lab)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, path + (str(i),), labels)
        elif isinstance(o, (int, float)):
            out.append((round(float(o), 4), '/'.join(path), tokens(*path, *labels)))
        elif isinstance(o, str):
            # 账本里大量数值是带修饰的字符串：'↑ +0.1pp'、'1,258 / 132%'、'0.30x'、'EUR 8.4m'。
            # 原来用 fullmatch 只认「整串就是一个数」，这些一个都抽不到，
            # 于是正文里正确引用它们反而被报成「账本外的数」。改为抽出串里所有数字。
            # 只有「带修饰的短值」才抽:'↑ +0.1pp'、'1,258 / 132%'、'0.30x'、'EUR 8.4m'。
            # 阈值从 400 收到 80:400 会把整段散文当值池（见上面 SKIP_KEYS 的注释）。
            if len(o) > 80:
                return
            for mm in re.finditer(r'[+-]?\d[\d,]*(?:\.\d+)?', o):
                raw = mm.group().replace(',', '')
                try:
                    out.append((round(float(raw), 4), '/'.join(path), tokens(*path, *labels)))
                except ValueError:
                    pass
    # ⚠ 这里原来写的是 d.get('charts') —— 那是 OTF 版账本的键名。
    # Private Credit 的账本用 'exhibits'，所以一直在遍历一个空 dict，
    # ledger_values() 恒返回 0 个值，整个图文矛盾检查形同虚设（2026Q3 收尾时发现）。
    walk(d.get('exhibits', {}), ('exhibits',), set())
    # meta 里这几块的数也会被正文引用：cohort 统计、筛选口径（样本数）、
    # 点名对标组、联网来源的数字。漏掉它们会把正文里正确引用的数报成「账本外」。
    _m = d.get('meta') or {}
    for _k in ('cohorts', 'screen', 'comparator_set', 'web_research', 'as_of'):
        walk(_m.get(_k, {}), (_k,), set())
    if not out:
        raise SystemExit(
            '✗ 账本里没抽到任何数值 —— 几乎一定是键名对不上（应为 exhibits / meta.cohorts）。\n'
            '  这种情况下本脚本会「全部通过」，属于静默失效，必须先修再用，不许当成检查通过。')
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    doc = sys.argv[1]
    _d = json.load(open('series.json', encoding='utf-8'))
    # ⚠ 传整本账本，不是 _d['exhibits'] —— ledger_values 内部会自己走
    #   exhibits 与 meta.cohorts 两处。传子字典会让它什么都抽不到。
    LV = ledger_values(_d)
    exact = {v for v, _, _ in LV}
    txt = docx_text(doc)

    suspect, outside = [], []
    seen = set()
    # 千分位要整体吃掉 —— 原来的正则会把 "1,258" 读成 "258"，
    # 于是账本里明明有 1258，正文里的 US$1,258m 却被报成账本外的数。
    for m in re.finditer(r'(?<![\w.,])(-?\d[\d,]*(?:\.\d+)?)\s*(%|x|bp|pp)?', txt):
        raw, unit = m.group(1).replace(',', ''), m.group(2) or ''
        if len(raw.replace('.', '')) < MINLEN:
            continue
        v = round(float(raw), 4)
        if 1900 <= v <= 2100 and '.' not in raw:
            continue
        # "Exhibit 58" 里的 58 是编号不是数据，跳过（编号由 exhibits.py 单独查连续性）
        if re.search(r'Exhibits?\s*$', txt[max(0, m.start() - 12):m.start()]):
            continue
        ctx = txt[max(0, m.start() - 90):m.end() + 40].replace('\n', ' ').strip()
        key = (v, unit, ctx[:40])
        if key in seen:
            continue
        seen.add(key)
        # 正文按可读性四舍五入（27.29→27.3、370.11→370），也可能带负号。
        # 只要账本里有一个值四舍五入到正文的精度后相等，就算命中。
        def _hit(x):
            if x in exact or -x in exact:
                return True
            for dp in (0, 1, 2):
                if round(x, dp) in {round(e, dp) for e in exact
                                    if abs(e) < abs(x) * 1.02 + 0.01
                                    and abs(e) > abs(x) * 0.98 - 0.01}:
                    return True
            return False
        if _hit(v):
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
        '§5 Credit Fundamentals': [
            'default rate', 'ttm default', 'recovery', 'implied recover',
            'gross leverage', 'total leverage', 'interest coverage', 'ebitda coverage',
            'nonaccrual', 'non-accrual', 'pik income', 'pik rate'],
        '§8 Fund Update': [
            'net irr', 'gross irr', 'moic', 'tvpi', 'dpi', 'called %', 'called-down',
            'unpaid commitment', 'total commitments', 'investment amount',
            'subscription line finance', 'watchlist', 'fund nav', 'nav per'],
        '§9 Competitor Analysis': [
            'percentile', 'cohort median', 'interquartile', 'iqr', 'quartile',
            'vintage', 'dry powder %'],
        '§2 Market Size': [
            'private debt aum', 'institutional aum', 'dry powder', 'fundraising',
            'origination', 'mm clo', 'new issuance'],
    }
    # 用词边界匹配，避免 'nav'/'clo' 这类短词跨节误命中
    import re as _re3
    _CUE_RE = {t: _re3.compile('|'.join(_re3.escape(c) for c in cues), _re3.I)
               for t, cues in LEDGER_TABLE_CUES.items()}
    leaked = []
    for v, u, ctx in outside:
        for tname, rx in _CUE_RE.items():
            if rx.search(ctx):
                leaked.append((tname, v, u, ctx))
                break
    if leaked:
        by_t = {}
        for tname, v, u, ctx in leaked:
            by_t.setdefault(tname, []).append(f'{v}{u}')
        print(f'\n⛔ 有 {len(leaked)} 个数在账本外，但按 report-spec.md 本该在账本里：')
        for tname, vals in by_t.items():
            print(f'   {tname}：{len(vals)} 个 —— {", ".join(vals[:10])}'
                  + ('…' if len(vals) > 10 else ''))
        print('   这批数没进账本、没上核对清单、也没经过门。处理顺序：')
        print('     1) 按 report-spec.md 写进 series.json 对应 slug，每个带 src')
        print('     2) 重跑 pc_review_sheet.py，把清单落到 out/')
        print('     3) 交用户核对新增那几行，用户确认后 approve.py --sign（不要自己代签）')
        print('     4) 再跑本脚本，这一节应该清零')
        if '--strict' in sys.argv:
            sys.exit(1)

    if suspect and '--strict' in sys.argv:
        sys.exit(1)


if __name__ == '__main__':
    main()
