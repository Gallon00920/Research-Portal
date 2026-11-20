#!/usr/bin/env python3
"""图片版 T1 · 2.1 Portfolio composition → Capital structure

数据全部读 series.json 的 tbl01_capital_structure，每行带 src（文件 + 页码）。
样式取自 v1 报告 document.xml 的真实表格：深蓝表头白字、#C9D2DC 全框线、
首列 #EEF2F6、Arial、Total 行加粗、表下灰色斜体小注。

跑法：python3 build_tbl01.py     输出 out/tbl01_capital_structure_<CQ>.png
Word 插入宽度 10.65 in
"""
import json, os, sys
import tablelib as T

D  = json.load(open('series.json', encoding='utf-8'))
CQ, PQ = D['meta']['cq'], D['meta']['pq']
KEY = 'tbl01_capital_structure'

spec_src = D['charts'].get(KEY)
if not spec_src:
    sys.exit(f'series.json 里没有 {KEY}。先从当季与上季 10-Q 抽资产类别占比，'
             f'每行连 src（文件 + 页码）一起写进 series.json，再跑本脚本。'
             f'不许拿上一版报告的表格数字当占位。')

tot = spec_src.get('total_row', 'Total')
spec = {
  'cols': ['Asset class', PQ, CQ, 'QoQ Chg'],
  'colw': [320, 144, 144, 192],                 # 40 / 18 / 18 / 24 %，合计 800
  'rows': [{'cells': [r['label'], r['pq'], r['cq'], r['qoq']],
            'total': (r['label'] == tot)} for r in spec_src['rows']],
  'note': spec_src['note'].format(cq=CQ, pq=PQ),
}
os.makedirs('out', exist_ok=True)
out = f"out/tbl01_capital_structure_{CQ.replace(chr(39),'')}.png"
T.render(spec, out)
