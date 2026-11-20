# -*- coding: utf-8 -*-
"""从 series.json 导出 sources_ledger_<quarter>.md —— 一行一个数,每行带出处。

规则:
  · 遍历 exhibit_manifest.json 定义的顺序,编号与成稿一致
  · 每个数值一行:Exhibit 号 / 字段路径 / 期或标签 / 数值 / 出处
  · 出处优先取点级 src,没有就落到图级 src
  · meta.screen / meta.cohorts / meta.comparator_set / meta.web_research 单独成节
  · 缺口(_gap_note / history_gaps / gap)照抄进去 —— 缺口也是要交付的信息
"""
import io, json, sys, re, datetime
import exhibits

LEDGER = 'series.json'
SKIP = {'_shape', '_section', '_layout', '_as_of_block', '_method', '_note',
        'src', 'note', 'source_line', 'caption_rendered', 'as_of',
        'ylim', 'yticks', 'window_max', 'colors', 'color', 'style',
        'digitised', 'anchors', 'residual_max',
        'periods', 'labels'}          # 坐标轴标签,由 Period 列承载,不单独成行
NUM = (int, float)


def fmt(v):
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        s = f'{v:,.4f}'.rstrip('0').rstrip('.')
        return s if s else '0'
    if isinstance(v, int):
        return f'{v:,}'
    return str(v)


def clean(s):
    s = re.sub(r'\s+', ' ', str(s)).strip()
    return s.replace('|', '\\|')


def walk(node, path, labels, src, out):
    """把嵌套结构摊平成 (字段路径, 期/标签, 值, 出处) 四元组。"""
    if isinstance(node, dict):
        # 点级 src 覆盖图级
        my = node.get('src') or node.get('_src') or src
        per = node.get('periods') or node.get('labels') or labels
        for k, v in node.items():
            if k in SKIP or k.startswith('_') and k != '_src':
                continue
            if k == '_src':
                continue
            walk(v, path + [str(k)], per, my, out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            if isinstance(v, (dict, list)):
                lab = None
                if isinstance(v, dict):
                    lab = v.get('label') or v.get('name') or v.get('quarter') or v.get('fund')
                walk(v, path + ([str(lab)] if lab else [f'[{i}]']), labels, src, out)
            elif isinstance(v, NUM):
                lab = labels[i] if (labels and i < len(labels)) else f'[{i}]'
                out.append(('/'.join(path), str(lab), v, src))
            elif isinstance(v, str) and re.search(r'\d', v):
                lab = labels[i] if (labels and i < len(labels)) else f'[{i}]'
                out.append(('/'.join(path), str(lab), v, src))
    elif isinstance(node, NUM):
        out.append(('/'.join(path[:-1]) or path[0], path[-1], node, src))
    elif isinstance(node, str) and re.search(r'\d', node) and len(node) < 60:
        out.append(('/'.join(path[:-1]) or path[0], path[-1], node, src))


def main():
    d = json.load(io.open(LEDGER, encoding='utf-8'))
    rq = d['meta'].get('rq') or d['meta'].get('cq')
    EX = exhibits.load()
    E = d['exhibits']
    L = []
    w = L.append

    w(f'# Junson Private Credit Quarterly Report {rq} — Sources Ledger')
    w('')
    w(f'Exported from `series.json` on {datetime.date.today().isoformat()}. '
      'One row per figure that appears in the report. Every row carries the source '
      'it was read from; where a figure is a Junson calculation the row says so and '
      'names the inputs.')
    w('')
    w('**Data-quality vocabulary** — *exact / as-labelled / as-disclosed* = taken '
      'straight from a source table or printed label; *digitised* = measured off a '
      'source chart with anchor validation (trend only); *Junson calculation* = '
      'derived here from ledger inputs; *web research* = external publication, '
      'publisher and date given.')
    w('')

    # ── as-of 三层 ──
    w('## As-of dates')
    w('')
    w('| Layer | As of | Note |')
    w('|---|---|---|')
    for k, v in d['meta']['as_of'].items():
        a = v.get('quarter') or v.get('export_date')
        w(f"| {k} | {a} | {clean(v.get('note',''))} |")
    w('')

    # ── exhibit 逐张 ──
    w('## Exhibits')
    w('')
    total = 0
    missing_src = []
    for rec in EX:
        slug = rec['slug']
        e = E.get(slug)
        n = rec['n']
        cap = (e or {}).get('caption_rendered') or rec['caption']
        cap = re.sub(r'\{[^}]*\}', '…', cap).strip().rstrip(',').strip()
        w(f"### Exhibit {n} — {cap}  `{slug}`")
        w('')
        if not e:
            w('_不在账本里 —— 本季无数据。_')
            w('')
            continue
        w(f"**Exhibit source.** {clean(e.get('src','—'))}")
        w('')
        if e.get('note'):
            w(f"**Printed note.** {clean(e['note'])}")
            w('')
        for gk in ('_gap_note', 'history_gaps', 'gap'):
            if e.get(gk):
                w(f"**Gap ({gk}).** {clean(json.dumps(e[gk], ensure_ascii=False))}")
                w('')
        rows = []
        walk({k: v for k, v in e.items() if k not in SKIP},
             [], e.get('periods') or e.get('labels'), e.get('src'), rows)
        if not rows:
            w('_本 exhibit 在账本里没有数值字段。_')
            w('')
            continue
        w('| Field | Period / label | Value | Source |')
        w('|---|---|---|---|')
        exsrc = clean(e.get('src') or '')
        for path, lab, val, src in rows:
            if not src:
                missing_src.append(f'Ex {n} {slug} {path}')
            s = clean(src or '')
            if not s:
                s = '⚠ 无出处'
            elif s == exsrc:
                s = '↑ exhibit source'          # 不重复刷同一段,读起来才能用
            elif len(s) > 300:
                s = s[:297] + '…'
            w(f'| `{path}` | {clean(lab)} | {fmt(val)} | {s} |')
            total += 1
        w('')

    # ── meta 各块 ──
    w('## Competitor screen')
    w('')
    for k, v in d['meta']['screen'].items():
        w(f'- **{k}** — {clean(v)}')
    w('')

    w('## Vintage cohort statistics (Junson calculation from the PitchBook export)')
    w('')
    w('| Vintage | n funds | Metric | n | Median | P25 | P75 | IQR | Min | Max |')
    w('|---|---|---|---|---|---|---|---|---|---|')
    ncoh = 0
    for vint, c in sorted(d['meta']['cohorts'].items()):
        for met in ('irr', 'tvpi', 'dpi', 'called_pct', 'dry_powder_pct'):
            m = c.get(met) or {}
            if not m.get('n'):
                continue
            w(f"| {vint} | {c.get('n_funds','')} | {met} | {m.get('n')} | "
              f"{fmt(m.get('median','')) if m.get('median') is not None else ''} | "
              f"{fmt(m.get('p25','')) if m.get('p25') is not None else ''} | "
              f"{fmt(m.get('p75','')) if m.get('p75') is not None else ''} | "
              f"{fmt(m.get('iqr','')) if m.get('iqr') is not None else ''} | "
              f"{fmt(m.get('min','')) if m.get('min') is not None else ''} | "
              f"{fmt(m.get('max','')) if m.get('max') is not None else ''} |")
            ncoh += 6
    w('')
    w(f"_Source: {clean(d['meta']['screen']['source'])}. Percentiles are the "
      "strictly-below share within the vintage-matched cohort; all cohort statistics "
      "are recomputed from the raw export each quarter, never carried forward._")
    w('')

    w('## Comparator set')
    w('')
    w(f"**Selection rule.** {clean(d['meta']['comparator_set']['rule'])}")
    w('')
    cs = d['meta']['comparator_set']['funds']
    cols = ['tier', 'house', 'fund', 'vintage', 'size_usdm', 'net_irr', 'tvpi',
            'dpi', 'called_pct', 'dry_powder_pct', 'pb_quartile', 'n_in_series']
    w('| ' + ' | '.join(cols) + ' |')
    w('|' + '---|' * len(cols))
    for f in cs:
        w('| ' + ' | '.join(
            (fmt(f.get(c)) if isinstance(f.get(c), NUM) else clean(f.get(c) or '')) for c in cols) + ' |')
    w('')
    ncomp = len(cs) * len([c for c in cols if c not in ('tier', 'house', 'fund', 'pb_quartile')])

    wr = d['meta'].get('web_research') or {}
    if wr:
        w('## Web research')
        w('')
        w('| Item | Value | Publisher / date | URL |')
        w('|---|---|---|---|')
        nweb = 0
        for k, v in wr.items():
            if not isinstance(v, dict):
                w(f'| {clean(k)} | {clean(v)} |  |  |')
                continue
            w(f"| {clean(k)} | {clean(v.get('value', v.get('val','')))} | "
              f"{clean(v.get('publisher',''))} {clean(v.get('date',''))} | "
              f"{clean(v.get('url',''))} |")
            nweb += 1
        w('')

    w('## Row count')
    w('')
    w(f'- Exhibit-level figures: **{total}**')
    w(f'- Cohort statistics: **{ncoh}**')
    w(f'- Comparator-set figures: **{ncomp}**')
    w(f'- Exhibits covered: **{len(EX)}**')
    w('')
    if missing_src:
        w('### ⚠ Rows without a source')
        w('')
        for m in missing_src:
            w(f'- {m}')
        w('')

    out = f'out/sources_ledger_{rq}.md'
    io.open(out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print(f'[written] {out}')
    print(f'  exhibit 层数值 {total} 个；cohort {ncoh}；对标组 {ncomp}')
    if missing_src:
        print(f'  ⚠ {len(missing_src)} 行没有出处：')
        for m in missing_src[:15]:
            print('   ', m)
        sys.exit(1)
    print('  ✓ 每一行都有出处')


main()
