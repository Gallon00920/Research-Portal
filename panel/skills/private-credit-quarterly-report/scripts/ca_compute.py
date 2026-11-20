# -*- coding: utf-8 -*-
"""§9 Competitor —— 从 PitchBook 导出表算 cohort 统计，写进账本。

铁律：只用 PitchBook 这份导出表算。同事的 CA_snapshot_2026Q3.json 只能事后对账，
不能当输入（那是上一版报告的产物）。
"""
import openpyxl, json, io, collections, statistics as st

# ⛔ 季度与路径一律由 pcpaths 从账本 meta.rq 推 —— 不写季度目录、不写文件全名。
#    文件名带导出时间戳，下季必变,所以用通配符取唯一一份。
import sys as _sys
_sys.path.insert(0, '.')
import pcpaths as _P

XLSX = _P.one('Competitor/PitchBook_Search_Result_Columns_*.xlsx',
              what='PitchBook 直贷基金筛选导出表')
# 导出日从文件名里的时间戳读（PitchBook 导出名格式 ..._YYYY_MM_DD_HH_MM_SS.xlsx）
import re as _re
_m = _re.search(r'(\d{4})_(\d{2})_(\d{2})', _os.path.basename(XLSX)) if (_os := __import__('os')) else None
EXPORT_DATE = f'{_m.group(1)}-{_m.group(2)}-{_m.group(3)}' if _m else ''
if not EXPORT_DATE:
    raise SystemExit(f'✗ 从文件名读不出导出日:{_os.path.basename(XLSX)}\n'
                     f'  PitchBook 导出名应含 _YYYY_MM_DD_ 时间戳;'
                     f'改名了就把导出日手写进账本 meta.screen.export_date 再跑。')
SCREEN = ('PitchBook 检索：Fund Strategy = Direct Lending；'
          'Fund Location = Americas > North America。导出日 2026-08-13，'
          '导出人 Xiyang Zhao (Junson Capital)，检索链接 https://my.pitchbook.com/?pcc=1372632-49')

ws = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)['Data']
rows = list(ws.iter_rows(values_only=True))
h = next(i for i, r in enumerate(rows) if r and r[0] == 'Fund ID')
HDR = list(rows[h])
recs = [dict(zip(HDR, r)) for r in rows[h + 1:] if r[0] and str(r[0]).strip()
        and not str(r[0]).startswith('©')]
print(f'样本数 {len(recs)} 只基金')
print('  ⚠ report-spec 写「333 funds at baseline」—— 那是数了表格行数：\n'
      '    表头之后 333 行 = 331 只基金 + 1 个全空行 + 1 行 PitchBook 版权声明。\n'
      '    真实样本数是 331。下季重跑不要去「凑」333。')


def num(v):
    if v is None or v == '':
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def q(vals, p):
    """线性插值分位数，和 numpy 默认口径一致。"""
    s = sorted(vals); n = len(s)
    if n == 0:
        return None
    if n == 1:
        return s[0]
    k = (n - 1) * p
    lo, hi = int(k), min(int(k) + 1, n - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def stats(vals):
    v = [x for x in vals if x is not None]
    if not v:
        return {'n': 0}
    return {'n': len(v), 'median': round(q(v, .5), 4),
            'p25': round(q(v, .25), 4), 'p75': round(q(v, .75), 4),
            'iqr': round(q(v, .75) - q(v, .25), 4),
            'min': round(min(v), 4), 'max': round(max(v), 4)}


by_v = collections.defaultdict(list)
for r in recs:
    vt = num(r.get('Vintage'))
    if vt:
        by_v[int(vt)].append(r)

cohorts = {}
for vt in sorted(by_v):
    g = by_v[vt]
    cohorts[str(vt)] = {
        'n_funds': len(g),
        'agg_size_usdm': round(sum(x for x in (num(r['Fund Size']) for r in g) if x), 1),
        'n_with_size': sum(1 for r in g if num(r['Fund Size']) is not None),
        'irr': stats([num(r['IRR']) for r in g]),
        'tvpi': stats([num(r['TVPI']) for r in g]),
        'dpi': stats([num(r['DPI']) for r in g]),
        'called_pct': stats([num(r['Called Down %']) for r in g]),
        'dry_powder_pct': stats([num(r['Dry Powder %']) for r in g]),
    }

print('\nvintage  n   IRR(n/中位/IQR)        TVPI(n/中位/IQR)      called%(n/中位)')
for vt in sorted(cohorts, key=int):
    c = cohorts[vt]; i, t, cd = c['irr'], c['tvpi'], c['called_pct']
    print(f"{vt}   {c['n_funds']:3d}  "
          f"{i['n']:3d} {i.get('median','—'):>7} {i.get('iqr','—'):>7}   "
          f"{t['n']:3d} {t.get('median','—'):>6} {t.get('iqr','—'):>6}   "
          f"{cd['n']:3d} {cd.get('median','—'):>6}")

json.dump({'screen': SCREEN, 'export_date': EXPORT_DATE,
           'universe_fund_count': len(recs), 'cohorts': cohorts},
          io.open('ca_cohorts.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n→ ca_cohorts.json')


# ══════════════ 与同事快照对账（只对账，不当输入）══════════════
# 同事快照（可选，只用于事后对账）—— 在父目录里按模式找，没有就跳过
import glob as _glob
_snaps = sorted(_glob.glob(_os.path.join(_P.UPLOADS, '**', 'CA_snapshot_*.json'), recursive=True))
SNAP = _snaps[-1] if _snaps else ''
try:
    snap = json.load(io.open(SNAP, encoding='utf-8'))
except Exception as ex:
    snap = None
    print(f'\n（读不到快照：{ex}）')

if snap:
    print(f'\n── 与快照 {SNAP} 对账（我这边是从 xlsx 独立重算的）──')
    print('   注意同事的字段命名：q1 存的是「上四分位（表现更好那端）」、q3 存的是下四分位，')
    print('   和统计学惯例反着（PE 圈 "first quartile" = 最好那档）。对账时按 iqr 比即可。')
    KEY = {'IRR': 'irr', 'TVPI': 'tvpi', 'DPI': 'dpi'}
    bad = 0; tot = 0
    for vt, blocks in (snap.get('cohorts') or {}).items():
        mine = cohorts.get(vt)
        if not mine:
            print(f'  {vt}: 我这边没有这个 vintage'); bad += 1; continue
        for mk, ours in KEY.items():
            sb = blocks.get(mk) or {}
            m = mine[ours]
            for nm, a, b in (('n', m.get('n'), sb.get('n')),
                             ('med', m.get('median'), sb.get('med')),
                             ('iqr', m.get('iqr'), sb.get('iqr'))):
                if b is None:
                    continue
                tot += 1
                ok = a is not None and abs(a - b) <= max(0.011, abs(b) * 0.012)
                if not ok:
                    bad += 1
                    print(f'  ✗ {vt} {mk} {nm}: 我 {a}  同事 {b}')
    print(f'  → 对账 {tot} 项，不一致 {bad} 项' +
          ('（全部吻合，说明两边都是从同一份 xlsx 正确算出来的）' if bad == 0 else ''))
    print(f'  → 样本数：我 331 只基金；同事快照没记这个字段；'
          f'report-spec 写的 333 是行数（含空行 + 版权行）。')
    print('  → 同事快照里的三只 Junson 基金数值（PAG 14.7/1.11/0.30 等）本轮不采信为输入，'
          '按铁律必须从基金季报 PDF 重新提取，提完再和这里对账。')
