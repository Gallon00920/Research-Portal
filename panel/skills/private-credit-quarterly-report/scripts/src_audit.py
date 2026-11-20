# -*- coding: utf-8 -*-
"""来源可追性体检：每张 exhibit 的 src 里提到的文件，本季文件夹里是否真的存在。

Alex 2026-08-24：每张图必须能追到具体文件路径，下季照路径取数。
Alex 2026-08-25：⛔ 不许写死本季文件名 —— 下季文件全换。

所以这个脚本**不带任何文件清单**：现场扫本季文件夹，再把账本里 src 提到的文件名
拿去比对。文件名下季变了也照样能用。
"""
import io, json, os, re, sys, glob
sys.path.insert(0, '.')
import pcpaths as P
import exhibits

D = json.load(io.open(P.ledger_path(), encoding='utf-8'))
E = D['exhibits']
EX = exhibits.load()
QD = P.quarter_dir()

# 现场扫本季文件夹：{小写文件名: 相对路径}
ACTUAL = {}
for root, _, files in os.walk(QD):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), QD).replace('\\', '/')
        ACTUAL[f.lower()] = rel

# ⚠ 别用正则从 src 里"抠文件名"——真实文件名带空格（"MS Private Credit 1Q26 tracker.pdf"），
#   正则会截成 "tracker.pdf"。反过来做:拿**文件夹里真实存在的文件名**去 src 里找子串。
BANNED = re.compile(r'_v\d|Junson_Private_Credit_Report|example-\d{4}|baseline-\d{4}|colleague-template')
HASEXT = re.compile(r'\.(pdf|xlsx|xls|csv|png|docx|json)\b', re.I)

ok, miss, nofile, banned, partial, noman = [], [], [], [], [], []
for r in list(EX):
    slug, n = r['slug'], r['n']
    src = (E.get(slug) or {}).get('src') or ''
    if not src.strip():
        nofile.append((n, slug, '（src 为空）'))
        continue
    if BANNED.search(src):
        banned.append((n, slug, BANNED.search(src).group(0)))
    low = src.lower()
    hit = [ACTUAL[fn] for fn in ACTUAL if fn in low]
    # ⛔ 逐文件核，不是任意命中即过 —— src 点名几份就得几份都在。
    #    2026-08-26 实测：券商表 src 点 9 份，少 1 份靠「任意命中」照样判过，
    #    结果表上照印那一家而它的报告本季不在文件夹里。
    _named = list((E.get(slug) or {}).get('src_files') or [])
    _absent = [f for f in _named if os.path.basename(f).lower() not in ACTUAL]
    if _absent:
        partial.append((n, slug, _absent, len(_named),
                        (E.get(slug) or {}).get('_src_files_rq')))
    elif not _named:
        noman.append((n, slug))
    if hit:
        ok.append((n, slug, sorted(hit, key=len)[-1]))
    elif HASEXT.search(src):
        # src 里写了文件名，但文件夹里没有这个文件 —— 真错
        miss.append((n, slug, HASEXT.split(src)[0][-48:] + HASEXT.search(src).group(0)))
    else:
        nofile.append((n, slug, src[:60]))

print(f'\n=== 来源可追性 · {P.rq()} ===')
print(f'  本季文件夹：{QD}（扫到 {len(ACTUAL)} 个文件）\n')
print(f'  能追到文件夹里真实文件的：{len(ok)} / {len(list(EX))}')
if nofile:
    print(f'  ? src 里没写文件名的 {len(nofile)} 张（可能是纯联网/纯自算，人工确认）：')
    for n, s, why in nofile[:10]:
        print(f'      Ex {n} {s} —— {why}')
if miss:
    print(f'  ✗ src 提到的文件在本季文件夹里找不到 {len(miss)} 张：')
    for n, s, nm in miss:
        print(f'      Ex {n} {s} —— {nm}')
if banned:
    print(f'  ✗ src 指向上一版报告（铁律四禁止）{len(banned)} 张：')
    for n, s, w in banned:
        print(f'      Ex {n} {s} —— 命中 "{w}"')

# ══════════════════════════════════════════════════════════════════════════
# 第零条的机械检查：**嵌套 src** —— 侧栏 bullet、点级 src、side_panel._src 等
# ⛔ Alex 2026-08-25：图 31 侧栏 bullet 的数是从同事报告搬的，而它的 src 写成
#    「取自本季文件夹」，图级 src 检查完全看不到 —— 因为那条 src 不在图级。
#    所以这里把账本里**每一个** src / _src 字段都走一遍，不管埋多深。
# ══════════════════════════════════════════════════════════════════════════
WEB_OK = re.compile(r'https?://|web research|联网|用户\s*20\d\d|用户提供|用户\s*<|Junson 流程约定'
                    r'|行业惯例|自算|Junson calculations|账本 stacks|本 exhibit', re.I)
# 全称词：写了「全部/逐条/都是」就必须逐条核过 —— 2026Q3 就是靠一句「全部取自本季文件夹」
# 把一条抄来的 bullet 盖过去的
TOTALISER = re.compile(r'全部|逐条|每一条|都是取自|均取自|all (?:three|of the)')

nested_ok, nested_bad, nested_web, nested_total, nested_soft, nested_waiver = [], [], [], [], [], []

# 真实文件名的「可辨识词干」：src 里常按短名写（"tracker p7"、"S&P Direct Lending deck"），
# 不必逼着每处都写全名 —— 但必须能落到文件夹里某个真实文件上。
_STEMS = {}
for _f, _rel in ACTUAL.items():
    _st = re.sub(r'\.(pdf|xlsx|xls|csv|png|docx|json)$', '', _f)
    for _tok in re.split(r'[_\-\s]+', _st):
        if len(_tok) >= 8:
            _STEMS.setdefault(_tok, _rel)
    if len(_st) >= 8:
        _STEMS.setdefault(_st, _rel)

def _names_real_file(v):
    low = v.lower()
    if any(f in low for f in ACTUAL):
        return True
    return any(t in low for t in _STEMS)

def _walk_src(o, path):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ('src', '_src') and isinstance(v, str) and v.strip():
                loc = '/'.join(path + (k,))
                # 授权例外：用户明确点头允许用季度文件夹之外的东西（例：Guggenheim 的
                # 内部计算数走同事的 CA_snapshot）。必须写成 '⚠授权例外(<谁><日期>): …'，
                # 才算通过 —— 而且永远单独列出来，不许静默混进 ✓ 里。
                if v.lstrip().startswith('⚠授权例外'):
                    nested_waiver.append((loc, v[:100]))
                    continue
                # 订正记录里会**提到**上一版报告（「这句原来是从 X 搬的，错了」）——
                # 那是病历，不是来源声明。只查 ⛔ 标记之前的部分。
                claim = re.split(r'⛔', v)[0]
                if BANNED.search(claim):
                    nested_bad.append((loc, '命中上一版报告：' + BANNED.search(claim).group(0)))
                elif _names_real_file(v):
                    nested_ok.append(loc)
                    if TOTALISER.search(v):
                        nested_total.append((loc, TOTALISER.search(v).group(0)))
                elif HASEXT.search(v):
                    # 写了扩展名却匹配不上真实文件 —— 多半是把文件名写成了缩略式
                    # （"q2-2026-…-quarterly-wrap.xlsx" 带省略号）。这是真错：下季照它取不到数。
                    nested_bad.append((loc, '写了文件名但对不上文件夹里任何一个（缩略/省略号也算错，'
                                       '下季照它取不到数）：' + HASEXT.split(v)[0][-40:]
                                       + HASEXT.search(v).group(0)))
                elif WEB_OK.search(v):
                    nested_web.append(loc)
                else:
                    nested_soft.append((loc, v[:70]))
            else:
                _walk_src(v, path + (str(k),))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            _walk_src(v, path + (str(i),))

for slug, ent in E.items():
    # 图级 src 上面已经查过，这里只查嵌套的
    _walk_src({k: v for k, v in ent.items() if k not in ('src',)}, ('exhibits', slug))
_walk_src(D.get('series_bank', {}), ('series_bank',))
_walk_src((D.get('meta') or {}), ('meta',))

if noman:
    print(f'\n  ? {len(noman)} 张没有 src_files 清单（取数阶段应当维护它）：'
          f'{[f"Ex {n} {sl}" for n, sl in noman][:8]}')
if partial:
    _same, _cross = [], []
    for it in partial:
        (_same if it[4] == P.rq() else _cross).append(it)
    if _same:
        print(f'\n  ✗ src_files 里的文件在本季文件夹里找不到 {len(_same)} 张'
              f'（清单是本季的 —— 真错）：')
        for n, slug, absent, tot, _q in _same:
            print(f'      Ex {n} {slug} —— 引用 {tot} 个，缺 {len(absent)}：{absent}')
        print('      ⛔ 原来的判据是「任意命中即过」，多源 exhibit 少一个源会被静默放过')
        print('         （2026-08-26 实测：券商表引用 9 份，抽掉 1 份照样判过，表照印那一家）。')
    if _cross:
        print(f'\n  ⚠ 另有 {len(_cross)} 张的 src_files 是上一季的清单，本季文件夹里没有那些文件'
              f' —— 这是「本季没更新这张图」，走缺料对话框决定怎么办，不算错：')
        for n, slug, absent, tot, _q in _cross[:8]:
            print(f'      Ex {n} {slug}（清单属 {_q}）缺 {absent}')

print(f'  嵌套 src（侧栏/点级/bank）：追到本季文件 {len(nested_ok)}　'
      f'标了联网/用户/自算 {len(nested_web)}　? 只写了来源没写文件 {len(nested_soft)}　'
      f'✗ 对不上文件 {len(nested_bad)}')
if nested_soft:
    print('  ? 这些 src 说了来源但没落到具体文件（人工确认，下季照它取数可能找不到位置）：')
    for loc, v in nested_soft[:12]:
        print(f'      {loc} —— {v}')
if nested_bad:
    print('  ✗ 下面这些 src 不合第零条：')
    for loc, why in nested_bad[:20]:
        print(f'      {loc}\n          {why}')
if nested_waiver:
    print(f'  ⚠ 授权例外 {len(nested_waiver)} 处（用户点头才允许，每季运行时必须重新确认）：')
    for loc, v in nested_waiver:
        print(f'      {loc}\n          {v}')
if nested_total:
    print(f'  ⚠ 用了全称词（「全部/逐条」）的 src {len(nested_total)} 处 —— '
          f'必须逐条核过才能这么写，写不出就把范围缩小：')
    for loc, w in nested_total[:10]:
        print(f'      {loc} —— "{w}"')
print()
_partial_same = [it for it in partial if it[4] == P.rq()]
sys.exit(1 if (miss or banned or _partial_same or nested_bad) else 0)
