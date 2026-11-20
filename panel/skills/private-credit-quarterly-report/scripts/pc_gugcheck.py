# -*- coding: utf-8 -*-
"""古根海姆手动输入体检 —— 跑在**取数阶段开头**，把该问用户的槽逐个列出来。

⛔ Alex 2026-08-24：AID Portfolio Tracking Master 那份 excel 不进季度文件夹，
   skill **不许**从它取数、它里面的数**不能存进账本**。
⛔ Alex 2026-08-25 再次强调：「E49 和 E50 的图里的古根海姆的数据也是到时候 skill 运行的时候
   需要手动输入的。」

所以这几张图的 Guggenheim 格子每季都是空的，必须**主动发对话框问用户**。
本脚本做三件事：
  ① 把 series_bank.gug_internal_returns.fill_checklist 逐项打出来（每季档 + 年度档分开）
  ② 检查每个 slug 在账本里 Guggenheim 那一行/那个点**现在是空还是有值**
  ③ 检查有值的那些，src 是否带「用户提供」或授权例外标记 —— 防止悄悄从别处取

用法：python3 pc_gugcheck.py [--strict]
     --strict：只要还有该问没问（空槽且没标 gap）就 exit 1
"""
import io, json, re, sys
sys.path.insert(0, '.')
import pcpaths as P
import exhibits

D = json.load(io.open(P.ledger_path(), encoding='utf-8'))
E = D['exhibits']
BANK = (D.get('series_bank') or {}).get('gug_internal_returns') or {}
FC = BANK.get('fill_checklist') or []
try:
    EX = exhibits.load()
    NUM = {r['slug']: r['n'] for r in list(EX)}
except Exception:
    NUM = {}

GUG = re.compile(r'gugg', re.I)
OKSRC = re.compile(r'用户|授权例外|user[- ]provided|manual', re.I)


def gug_cells(slug):
    """返回 [(位置描述, 值, src)] —— 这张图里 Guggenheim 的格子。"""
    ent = E.get(slug) or {}
    out = []
    for key in ('rows', 'rows_dpi', 'overlay', 'points', 'own_funds'):
        v = ent.get(key)
        if isinstance(v, list):
            for i, r in enumerate(v):
                if isinstance(r, dict) and GUG.search(json.dumps(r, ensure_ascii=False)):
                    val = r.get('cq', r.get('value', r.get('v')))
                    out.append((f'{key}[{i}]', val, r.get('src') or ''))
    h = ent.get('history')
    if isinstance(h, dict):
        for k, pts in h.items():
            if GUG.search(str(k)) and isinstance(pts, list):
                last = pts[-1] if pts else None
                # ⚠ src 要从这个点自己身上读 —— 第一版写死成 ''，于是标了授权例外的点
                #    也被报成「src 没标」（2026-08-25 自己踩的）
                out.append((f'history[{k}]',
                            (last.get('percentile') if isinstance(last, dict) else last),
                            (last.get('src') if isinstance(last, dict) else '') or ''))
    return out


print(f'\n=== 古根海姆手动输入体检 · {P.rq()} ===')
if not FC:
    print('  ✗ series_bank.gug_internal_returns.fill_checklist 是空的 —— '
          '这份清单就是「哪几张图有 Guggenheim 的坑」的唯一真值，丢了就会漏填')
    sys.exit(1)

todo, filled, bad, deferred = [], [], [], []
for item in FC:
    slug = item['slug']
    cad = item.get('节奏', '')
    n = NUM.get(slug, '?')
    # ── 本季故意不填的槽（`_deferred_in` 列了哪几季）─────────────────────
    # ⛔ 只在列到的那一季算「故意」；过了就是硬失败 —— Alex 2026-08-26:
    #    「下季度…是一定要入点的，如果用户漏输入了，那你要提醒用户。」
    _dfr = [str(x) for x in (item.get('_deferred_in') or [])]
    cells = gug_cells(slug)
    if _dfr and P.rq() in _dfr and not cells:
        deferred.append((n, slug, item.get('_deferred_2026Q3') or item.get('_why') or '',
                         item.get('_next_quarter_must', '')))
        continue
    if not cells:
        if _dfr:
            bad.append(f'E{n} {slug}: 上一季（{"/".join(_dfr)}）是**故意**先不填的，'
                       f'本季 {P.rq()} 已经过了那一季 —— ⛔ 必须入点：'
                       f'{item.get("_next_quarter_must", "问用户拿到数就补上")}\n'
                       f'          → 现在就去问用户「{item.get("要问用户的", "")}」；'
                       f'用户漏输入要**主动提醒**，不许静默跳过，也不许沿用上季的「先不入」')
        else:
            bad.append(f'E{n} {slug}: 清单说这里有 Guggenheim 的坑，但账本里找不到对应的格子 '
                       f'—— 图的结构变了？清单要跟着改')
        continue
    for loc, val, src in cells:
        empty = val is None or val == '' or (isinstance(val, dict) and not val)
        if empty:
            todo.append((n, slug, loc, cad, item.get('要问用户的', '')))
        else:
            filled.append((n, slug, loc, val, src, cad))

print(f'  清单 {len(FC)} 项；每季档 {sum(1 for i in FC if i.get("节奏") == "每季")} 项、'
      f'年度档 {sum(1 for i in FC if "年度" in str(i.get("节奏")))} 项\n')
if deferred:
    print(f'  ⚠ 本季**故意**不填 {len(deferred)} 处（用户当季拍板，下季自动转成必填）：')
    for n, slug, why, nxt in deferred:
        print(f'      E{n} {slug}　{why}')
        if nxt:
            print(f'          ⛔ 下季：{nxt}')
if todo:
    print(f'  ⚠ 还空着、需要**发对话框问用户** {len(todo)} 处：')
    for n, slug, loc, cad, ask in todo:
        print(f'      E{n} {slug} · {loc}　[{cad}]　问：{ask}')
if filled:
    print(f'\n  已填 {len(filled)} 处 —— 逐个核 src 是否标了「用户提供 / 授权例外」：')
    for n, slug, loc, val, src, cad in filled:
        flag = '✓' if OKSRC.search(src) else '✗ src 没标来源是用户手输'
        print(f'      E{n} {slug} · {loc} = {val}　{flag}')
        if not OKSRC.search(src):
            bad.append(f'E{n} {slug} · {loc} 有值但 src 没标「用户提供」或「授权例外」—— '
                       f'⛔ 这个数只能来自用户手输，不许从 AID master excel 或别处取')
print()
print('  ⛔ 铁律提醒：')
print('     · AID Portfolio Tracking Master 那份 excel **不进季度文件夹**，'
      'skill 不许读它、它的数不许进账本')
print('     · 问用户时必须一并确认三件事：①截至哪一期 ②IRR 口径（YTD 年化 vs 成立以来 ITD）'
      '③标注 † computed internally by Junson')
print('     · 用户不给就**留空 + 写 gap 说明**，绝不拿上季的值顶上')
if bad:
    print(f'\n  ✗ {len(bad)} 处不合规：')
    for b in bad:
        print('      ' + b)
print()
sys.exit(1 if (bad or (todo and '--strict' in sys.argv)) else 0)
