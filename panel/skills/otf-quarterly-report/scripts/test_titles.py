import titlecheck as TC

# ── 2026Q2 那一季的真实数据（从 v1 报告的图里读出来）────────────────
FITCH_LEV = [5.89,6.05,6.40,6.64,6.88,6.55,6.26,6.16,6.07,5.79,5.95,5.95,6.00,5.90]
FITCH_COV = [2.55,2.66,2.77,2.51,2.25,1.90,1.72,1.56,1.63,1.70,1.83,1.85,1.86,1.89,2.00]
# 图 17 九年月度→季度序列，末点 2.75（披露 2.8）
NA_AVG = [2.93,2.17,2.15,2.11,1.98,2.44,2.63,2.58,2.77,2.23,2.60,2.30,2.59,3.80,4.47,
          4.18,3.13,2.90,2.42,2.50,2.30,2.10,1.90,1.76,2.08,2.02,2.25,2.06,2.10,2.50,
          2.40,2.48,2.48,2.43,2.60,2.45,2.75]
NA_TAIL = [8.6,8.0,8.5,9.0,10.6]          # 右轴：>8% 非应计的 BDC 占比，末两期 9.0→10.6
PIK_TII = [5.8,5.9,6.1,6.0,6.2,6.2,6.8,6.6,6.6,6.3,6.2,6.0,6.4]
PIK_TAIL= [5.4,7.4,8.2,5.3,7.4,8.4,9.6,9.9,6.3,6.8,6.2,6.5,8.0]
SECTOR_D = {'Healthcare':3.5-1.7, 'Information Technology':2.1-0.7,
            'Materials & Resources':2.5-1.6, 'Business Products & Services (B2B)':1.2-1.1,
            'Consumer Products & Services (B2C)':2.6-2.7,
            'Financial Services':0.5-1.1, 'Energy':0.1-0.9}

CASES = [
  ('固定标题（不该被校验）', 'OTF vs leading BDCs — share price',
   dict(series=[1,2,3])),
  ('图 15 本季', 'Borrower leverage — flat to slightly down',
   dict(series=FITCH_LEV)),
  ('图 16 本季', 'Interest coverage — improved on the quarter, still near lows',
   dict(series=FITCH_COV)),
  ('图 17 本季', 'Non-accruals across BDCs — average at a five-year high',
   dict(series=NA_AVG, full=NA_AVG)),
  ('图 18 本季', 'PIK income across BDCs — 6.4% of investment income, more high-PIK BDCs',
   dict(series=PIK_TII, rhs=PIK_TAIL)),
  ('图 20 本季', 'Non-accruals by sector — Healthcare & IT saw the sharpest rise (Healthcare, Information Technology)',
   dict(series=[1.7,3.5], deltas=SECTOR_D)),
]
for name, title, kw in CASES:
    try:
        print(f'{TC.verify(title, **kw):5} | {name}')
    except ValueError as e:
        print(f'FAIL  | {name}\n       {str(e)}')

print('\n=== 反向：照抄上季标题但数据已经反了 ===')
NEG = [
  ('coverage 其实下滑了却还写 improved',
   'Interest coverage — improved on the quarter, still near lows',
   dict(series=FITCH_COV[:-1] + [1.80])),
  ('已经不是五年新高了却还写 five-year high',
   'Non-accruals across BDCs — average at a five-year high',
   dict(series=NA_AVG + [2.10], full=NA_AVG + [2.10])),
  ('标题写 6.4% 但数据已经是 7.1%',
   'PIK income across BDCs — 6.4% of investment income, more high-PIK BDCs',
   dict(series=PIK_TII + [7.1], rhs=PIK_TAIL + [8.6])),
  ('高 PIK 的 BDC 其实减少了却还写 more',
   'PIK income across BDCs — 6.4% of investment income, more high-PIK BDCs',
   dict(series=PIK_TII, rhs=PIK_TAIL[:-1] + [5.0])),
  ('升幅最大的其实是 Materials 却还点名 Healthcare/IT',
   'Non-accruals by sector — sharpest rise (Healthcare, Information Technology)',
   dict(series=[1,2], deltas={**SECTOR_D, 'Materials & Resources': 9.9})),
  ('杠杆其实大涨却还写 flat to slightly down',
   'Borrower leverage — flat to slightly down',
   dict(series=FITCH_LEV + [6.80])),
]
for name, title, kw in NEG:
    try:
        TC.verify(title, **kw); print(f'漏抓  | {name}')
    except ValueError as e:
        print(f'抓到  | {name}\n       {str(e).splitlines()[-1].strip()}')
