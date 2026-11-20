# -*- coding: utf-8 -*-
"""从 manifest 生成 series.json 骨架。数据点留空，第一次运行时填。"""
import json, io

man = json.load(io.open('exhibit_manifest.json', encoding='utf-8'))

SHAPES = {  # slug -> 数据形状（决定 review_sheet 怎么查恒等式）
 'series_stacked':  ['mkt_aum_by_channel','mkt_inst_aum_decomp','mkt_fundraising',
                     'mkt_dl_origination','mkt_mmclo_issuance_spread','cf_bdc_nonaccrual_avg',
                     'cf_bdc_pik_avg'],
 'series_lines':    ['ret_yield_vs_singleb','ret_dl_spread_vs_bsl','ret_dl_spread_by_ebitda',
                     'cf_sp_default_vs_specgrade','cf_sp_dl_vs_bsl_default','cf_fitch_ttm_default',
                     'cf_kbra_dld_default','cf_leverage_timeseries','cf_ebitda_coverage_ts',
                     'cf_bdc_nonaccrual_pubpriv','cf_bdc_pik_pubpriv','mkt_lbo_bsl_vs_private'],
 'shares':          ['mkt_us_levcredit_split','fund_pag_comp_type','fund_pag_comp_geo',
                     'fund_pag_comp_ccy','fund_pag_comp_bank','fund_gug_gics_mix',
                     'fund_gug_sponsored','fund_hsbc_sector'],
 'bars_categorical':['cf_fitch_default_by_sector','cf_recovery_by_sector','cf_recovery_path',
                     'prc_covenants_by_vintage','prc_pik_toggle_share','fund_hsbc_margin',
                     'ca_cohort_iqr','ca_apx_universe','ca_apx_irr_by_vintage',
                     'ca_apx_tvpi_by_vintage','ca_apx_called_by_vintage'],
 'band_positioning':['cf_leverage_band','cf_icr_band'],
 'scatter_bubble':  ['ca_apx_mgr_consistency'],
 'pct_history':     ['ca_momentum_irr','ca_momentum_tvpi','ca_traj_irr_pct','ca_traj_tvpi_pct'],
 'rows_qoq':        ['cf_provider_compare_table','fund_pag_comp_qoq','fund_pag_kpi_qoq',
                     'fund_gug_comp_qoq','fund_hsbc_comp_qoq','ca_scorecard'],
 'rows_flat':       ['ret_risk_return_table','fund_pag_top10','fund_gug_closed_deals',
                     'fund_hsbc_portfolio','ca_named_comparators','sent_broker_summary'],
 'freeform':        ['tws_extra_exhibit'],
}
shape_of = {s: k for k, v in SHAPES.items() for s in v}
try:                                       # 有现成账本就以它为准
    LIVE = json.load(io.open('series.json', encoding='utf-8'))['exhibits']
except Exception:
    LIVE = {}

# 各段落的数据基准归属（三个基准日并存 —— 必须显式）
BLOCK = {'2':'market','3':'market','4':'market','5':'market','6':'market','7':'market',
         '8':'fund','9':'competitor'}

SKEL = {
 'series_stacked':  {'periods': [], 'stacks': {}, 'rhs_line': None, 'ylim': None, 'ytick': None},
 'series_lines':    {'periods': [], 'lines': {}, 'ylim': None, 'ytick': None},
 'shares':          {'labels': [], 'vals': [], 'panels': None},
 'bars_categorical':{'labels': [], 'vals': [], 'highlight': None},
 'band_positioning':{'bands': [], 'items': []},
 'scatter_bubble':  {'points': [], 'highlight': []},
 'pct_history':     {'history': {}},
 'rows_qoq':        {'rows': []},
 'rows_flat':       {'cols': [], 'rows': []},
 # 后来补的形状 —— ledger.md 的形状表里都有，这里也必须有骨架，
 # 不然 gen 一遇到就 KeyError（曾经被 pc_audit G 组抓到过）
 'series_grouped':          {'periods': [], 'stacks': {}, 'rhs_line': None, 'ylim': None, 'ytick': None},
 'groups_stacked':          {'groups': [], 'stacks': {}},
 'groups_bars':             {'groups': [], 'bars': {}},
 'bars_grouped_categorical':{'labels': [], 'groups': {}, 'highlight': None},
 'bars_categorical_dual':   {'labels': [], 'left': [], 'right': [], 'left_label': None, 'right_label': None},
 'median_iqr_by_vintage':   {'vintages': [], 'median': [], 'p25': [], 'p75': [], 'n': [], 'own_funds': []},
 'freeform':        {},
}

out = {
 'meta': {
   '_note': ('PC 季报数据账本。历史点只追加不重算。key 是 exhibit_manifest.json 里的稳定 slug，'
             '不是 exhibit 编号 —— 编号每季会变，slug 不会。'),
   'rq': None,
   'as_of': {
     'market':     {'quarter': None, 'note': '市场层：MS Tracker / S&P / PitchBook·LCD / KBRA / Fitch'},
     'fund':       {'quarter': None, 'note': '基金层：三份投资人报告，通常滞后市场层 1–2 季'},
     'competitor': {'export_date': None, 'note': 'PitchBook 导出日，就是竞品层的基准日'},
   },
   'screen': {'universe_fund_count': None, 'definition': 'North America direct lending drawdown funds'},
   'comparator_set': {'upper_mm': [], 'core_mm': [], '_note': '人工选定，改了必须在正文声明'},
   'vintage_convention': {'PAG_BRS_III': None, 'Guggenheim_PDF_IV': None, 'HSBC_RCF': None},
 },
 'exhibits': {}
}

for e in man['exhibits']:
    sl = e['slug']
    # 账本里已经在用的形状是真值 —— 这里的 SHAPES 只是首次建账时的默认值。
    # 否则改了一张图的画法之后，模板与账本就会长期不一致（pc_audit G 组会一直红）。
    sh = (LIVE.get(sl) or {}).get('_shape') or shape_of.get(sl, 'freeform')
    sec_top = e['section'].split('.')[0]
    ent = {
      '_shape': sh,
      '_section': e['section'],
      '_layout': e['layout'],
      '_as_of_block': BLOCK.get(sec_top, 'market'),
      'src': '',            # 图级来源：哪一期出自哪份文件的哪个位置（按标题定位，不写死页码/slide 号）
      'window_max': None,   # null = 不裁；数字 = 最多保留几期（年度序列一律 null）
      'note': '',           # 图下 Note: ... 的内容
      'source_line': e['source'],
    }
    ent.update(json.loads(json.dumps(SKEL[sh])))
    out['exhibits'][sl] = ent

io.open('series_template.json','w',encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
from collections import Counter
print('series_template.json 生成完毕')
print('形状分布:', dict(Counter(v['_shape'] for v in out['exhibits'].values())))
print('基准归属:', dict(Counter(v['_as_of_block'] for v in out['exhibits'].values())))
miss=[e['slug'] for e in man['exhibits'] if e['slug'] not in shape_of]
print('没分配形状的:', miss if miss else '无（tws_extra_exhibit 走 freeform）')
