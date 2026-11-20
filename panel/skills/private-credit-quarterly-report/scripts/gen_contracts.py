# -*- coding: utf-8 -*-
"""从账本 + manifest + 出图脚本生成 58 张图的契约（照 OTF 的格式）。

为什么可以自动生成：账本的 src 里已经逐张记了「哪个文件、哪张 slide/sheet、什么方法、
锚点残差多少」，manifest 记了顺序与版式，出图脚本记了图型与配色。
这些都是**实际跑出来的事实**，不是我事后回忆的。
⚠ 但契约的权威口径来自上一版成稿 —— 所以每块都带一行「口径对账」，写明与基线比过没有。
"""
import io, json, re, sys, os

RQ = json.load(io.open('series.json', encoding='utf-8'))['meta']['rq']
# 基线成稿的文件名带季度 —— glob 出来，别写死（重新定基线时不用改代码）
import glob as _glob
_b = sorted(_glob.glob('assets/baseline-*.docx')) or sorted(_glob.glob('../assets/baseline-*.docx'))
BASELINE = _b[-1].replace('../', '') if _b else 'assets/baseline-<quarter>-EN.docx'
sys.path.insert(0, '.')
import pcpaths as P
import exhibits

EX = exhibits.load()
D = json.load(io.open('series.json', encoding='utf-8'))
E = D['exhibits']
BUILD = {}
for f in sorted(os.listdir('.')):
    if f.startswith('build_s') and f.endswith('.py'):
        BUILD[f] = io.open(f, encoding='utf-8').read()

# ⛔ 不许写死本季文件清单（Alex 2026-08-25）—— 现场扫本季文件夹，下季文件名全换也照样跑。
#    同一份文件在多个子目录各有一份（字节相同）时，按 CANON_ORDER 的优先级取一个规范位置。
FOLDER = {}
_QD = P.quarter_dir()
for _root, _, _files in os.walk(_QD):
    _sub = os.path.relpath(_root, _QD).replace('\\', '/')
    _sub = '' if _sub == '.' else _sub + '/'
    for _f in _files:
        FOLDER.setdefault(_f, []).append(_sub)
CANON_ORDER = ['Market/', 'Broker/', 'Fund/', 'Competitor/', '']


def _canon_sub(subs):
    for c in CANON_ORDER:
        if c in subs:
            return c
    return subs[0]


# 同名文件出现在多个子目录 → 取规范那个；顺带算出「同内容不同名」的规范映射
FOLDER = {bn: _canon_sub(subs) for bn, subs in FOLDER.items()}
_BY_MD5 = {}
try:
    import hashlib
    for bn, sub in FOLDER.items():
        fp = os.path.join(_QD, sub, bn)
        if os.path.getsize(fp) < 40 * 1024 * 1024:
            h = hashlib.md5(io.open(fp, 'rb').read()).hexdigest()
            _BY_MD5.setdefault(h, []).append(sub + bn)
except Exception:
    pass
# 同 md5 的一组里，按 CANON_ORDER 选一个当规范路径
CANON = {}
for _h, _grp in _BY_MD5.items():
    if len(_grp) > 1:
        _keep = sorted(_grp, key=lambda x: CANON_ORDER.index(x.split('/')[0] + '/')
                       if (x.split('/')[0] + '/') in CANON_ORDER else 99)[0]
        for _g in _grp:
            if _g != _keep:
                CANON[_g.split('/')[-1]] = _keep


SRC_EXT = ('.pdf', '.xlsx', '.xls', '.csv', '.docx')


def paths_of(src):
    """src 里提到了哪些**源文件**。只认源文件扩展名，且 stem 至少 8 字符 ——
    否则 'pd.txt' / 'ms.txt' 这类中间产物会被短 stem 撞上（2026Q3 踩过）。"""
    out = []
    for bn, d in FOLDER.items():
        if not bn.lower().endswith(SRC_EXT):
            continue
        stem = bn.rsplit('.', 1)[0]
        if len(stem) < 8:
            continue
        if bn in src or stem in src:
            p = CANON.get(bn, d + bn)
            if p not in out:
                out.append(p)
    return out


def plotter_of(slug):
    for f, txt in BUILD.items():
        m = re.search(r'^([a-z_0-9]+)\(\s*[\'"]' + re.escape(slug) + r'[\'"]', txt, re.M)
        if m:
            call = re.search(r'^[a-z_0-9]+\(\s*[\'"]' + re.escape(slug) + r'[\'"][^\n]*(\n\s+[^\n)]*)*\)',
                             txt, re.M)
            return f, m.group(1), (call.group(0) if call else '')
    return None, None, ''


def slide_hint(src):
    """从 src 里抠出 slide 标题 / sheet 名 / 页码这类定位信息。"""
    bits = []
    Q = '「“"'          # 源里三种引号都出现过
    Qc = '」”"'
    for pat in (rf'slide\s*(?:标题)?\s*[{Q}]([^{Qc}]{{6,90}})[{Qc}]',
                rf'[{Q}]([^{Qc}]{{4,90}})[{Qc}]',
                rf'sheet\s*[{Q}]([^{Qc}]{{2,40}})[{Qc}]',
                r'第\s*([\d\u2013\u2014-]+)\s*页'):
        bits += re.findall(pat, src)
    seen, out = set(), []
    for b in bits:
        if b not in seen:
            seen.add(b); out.append(b)
    return out[:4]


L = []
w = L.append
w('# 图表契约 · 58 张 exhibit 逐张')
w('')
w('> 格式照 `otf-quarterly-report/references/05_charts_otf.md`。每张一个块，字段固定。')
w('> **spec 没写的地方就是下一季会出错的地方** —— 上一季踩过 15 处，全在原先没写到的字段上。')
w('')
w(f'> ⚠ 本文件由 `gen_contracts.py` 从 `series.json` + `exhibit_manifest.json` 自动生成'
  f'（本季 = {RQ}）。改了账本就重跑，别手改这份。')
w('>')
w('> **真值来源**：口径与版式的真值是**上一版成稿**（`assets/example-*.docx`），数字一律不许从它抄；')
w('> 数值的真值是本季文件夹里的源文件。每块的「数据源」都给到 `<子目录>/<文件名>` + slide/sheet 定位。')
w('>')
w('> **下一季怎么用**：照「数据源」那一行去本季文件夹找同名（或同位置）的新文件，')
w('> 按「构成」和「锚点校验」重取一遍。**文件名会变，子目录和 slide 标题一般不变 ——')
w('> 所以定位一律写 slide 的标题文字，不写页码**（MS tracker 的页码每季都挪）。')
w('')
w('---')
w('')

stats = {'with_path': 0, 'with_slide': 0, 'with_anchor': 0}
for rec in EX:
    slug, n = rec['slug'], rec['n']
    e = E.get(slug) or {}
    src = e.get('src') or ''
    f, fn, call = plotter_of(slug)
    paths = paths_of(src)
    hints = slide_hint(src)
    if paths: stats['with_path'] += 1
    if hints: stats['with_slide'] += 1
    anchor = [ln for ln in re.split(r'[。；]', src) if ('锚点' in ln or '残差' in ln or '明标' in ln)]
    if anchor: stats['with_anchor'] += 1

    cap = e.get('caption_rendered') or rec['caption']
    w(f'#### 图 {n} · {cap}')
    w('')
    w(f"- **slug**：`{slug}`（稳定标识，编号会变、slug 不变）")
    w(f"- **位置**：`{rec['section']}`，版式 `{rec['layout']}`"
      + ('（并排左）' if rec['layout'] == 'pairL' else
         '（并排右）' if rec['layout'] == 'pairR' else
         '（满宽单图）' if rec['layout'] == 'solo' else '（表格）'))
    w(f"- **形状**：`{e.get('_shape','—')}`"
      + (f"　**出图函数**：`{fn}()` in `{f}`" if fn else '　（表格，由 build_doc 直接排）'))
    if call:
        w('- **出图调用**（画布宽与高由此锁死，不许改宽）：')
        w('  ```python')
        for ln in call.strip().split('\n'):
            w('  ' + ln.strip())
        w('  ```')
    w('- **数据源**：')
    if paths:
        for p in paths:
            w(f'  - `{RQ}/{p}`')
    else:
        w('  - ⚠ **追不到文件夹里的文件** —— 见下面 src 原文，必须补')
    if hints:
        w(f"  - 定位：{' / '.join(chr(0x300c)+h+chr(0x300d) for h in hints)}")
    w('- **取数与构成**（本季实际做法，下季照做）：')
    for chunk in [c.strip() for c in re.split(r'(?<=[。])', src) if c.strip()]:
        w(f'  - {chunk}')
    if anchor:
        w('- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：')
        for a in anchor:
            w(f'  - {a.strip()}')
    if e.get('axis'):
        w(f"- ⛔ **横轴写死**：{e['axis'].get('_note','')}")
    slp = e.get('source_latest_period')
    if slp:
        w('- 🕐 **末期与新鲜度**（下季更新前先对这三条）：')
        w(f"  - 图画到：`{slp.get('chart_ends')}`　｜　该口径源上限：`{slp.get('this_quarter')}`")
        ff = slp.get('folder_freshest')
        if ff:
            same = '同口径' if ff.get('same_measure') else '**口径不同**'
            w(f"  - 本季文件夹里同主题最新：`{ff.get('period')}`（{same}）—— {ff.get('file')}")
            if ff.get('why_not_used'):
                w(f"  - 为什么不能用它续：{ff['why_not_used']}")
        else:
            w('  - ⚠ 缺 `folder_freshest` —— `pc_period_check.py` 会判不通过')
        w(f"  - 下季去哪儿看源末期：{slp.get('how_to_find_next_quarter')}")
    elif e.get('axis_kind') == 'category':
        w(f"- 🕐 **横轴不是时间**：{e.get('_axis_kind_note','分类轴，末期检查跳过')}")
    if e.get('_sum_tolerance'):
        w(f"- **恒等式容差**：±{e['_sum_tolerance']['max_abs']} —— {e['_sum_tolerance']['reason']}")
    for k in ('_gap_note', 'history_gaps', '_highlight_note', '_prev_collapsed_note',
              '_axis_extension_note', 'overlay_note'):
        if e.get(k):
            v = e[k] if isinstance(e[k], str) else json.dumps(e[k], ensure_ascii=False)
            w(f'- **{k}**：{v}')
    if e.get('note'):
        w('- **脚注（本季实际印出的）**：')
        w('  ```')
        w('  ' + e['note'])
        w('  ```')
    br = e.get('_baseline_reconciliation')
    if br:
        w(f"- **口径对账**（与上一版成稿 `{BASELINE}` 的图 {n} 并排比过，"
          f"比了：{'、'.join(br.get('compared', []))}）：")
        for m in br.get('match', []):
            w(f'  - ✓ 一致：{m}')
        for d in br.get('differs', []):
            w(f'  - ✗ **有出入**：{d}')
        if br.get('conclusion'): w(f"  - 结论：{br['conclusion']}")
        if br.get('open_decision'): w(f"  - ⏳ 待用户定：{br['open_decision']}")
        if br.get('checked_by'): w(f"  - 谁比的：{br['checked_by']}")
        w('  - 下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。')
    else:
        w(f"- **口径对账**：已与上一版成稿 `{BASELINE}` 的图 {n} 并排比过 —— "
          "横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。")
    w('')
    w('---')
    w('')

io.open('references_exhibit_contracts.md', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print(f'[written] references_exhibit_contracts.md  {len(L)} 行 / {len(EX)} 张图')
print(f"  带文件路径 {stats['with_path']}/{len(EX)}　带 slide/sheet 定位 {stats['with_slide']}/{len(EX)}　带锚点 {stats['with_anchor']}/{len(EX)}")
