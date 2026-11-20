# -*- coding: utf-8 -*-
"""Ex 30 §6.1 券商观点汇总。每行都锁定：机构 / 报告名 / 日期 / 作者 / 文件名。"""
import json, io, collections

ROWS = [
 dict(house='Morgan Stanley', team='US Credit Strategy, Banks & Asset Managers',
      title='Connecting the Dots Around Private Credit', date='2026-04-02',
      authors='Vishwas Patkar, Vishwanath Tirupattur, Joyce Jiang, Michael Cyprys, Manan Gosalia, Brian Wilczynski',
      file='Connecting the Dots Around Private Credit.pdf', pages=47,
      view='进入以软件为中心的、行业集中型违约周期；回报低于历史、AUM 增长因零售赎回而放缓。'
           '但系统性风险低、银行受影响有限、机构资金需求稳定。',
      stance='谨慎但不看系统性风险'),
 dict(house='Morgan Stanley', team='Global Macro (Sunday Start)',
      title="Private Credit: Pressures Contained, Not Resolved", date='2026-07-12',
      authors='Vishwanath Tirupattur, Vishwas Patkar',
      file='Private Credit Pressures Contained Not Resolved.pdf', pages=9,
      view='4 月那轮噪音（BDC 赎回、公募 BDC 折价、软件 AI 敞口）已缓和但没消失。'
           '维持原判断：信用风险显著但不系统性，年初波动是定价与情绪的重置，不是无序去杠杆的开端。'
           'AI 冲击会继续在软件板块里分化结果。',
      stance='维持原判断，压力未解除'),
 dict(house='Morgan Stanley', team='Research (Private Credit Tracker)',
      title='Private Credit Tracker 1Q26 – Softening Fundamentals', date='2026-06-23',
      authors='Joyce Jiang', file='Private Credit Tracker 1Q26 – Softening Fundamentals.pdf', pages=52,
      view='基本面走软：BDC 平均非应计升至 2.8%（五年最高）、PIK 占投资收益升至 6.4%；'
           '预计整体直贷违约率将升至 8%（与新冠峰值相当），但集中在软件与 AI 相邻板块。',
      stance='基本面转弱',
      note='⚠ 与 Market 目录下的 "MS Private Credit 1Q26 tracker.pdf" 是同一份文件（md5 相同），'
           '§2–§5 的图表数据就来自它。券商观点表里只算一条，不要因为两个目录各有一份就记成两家观点。'),
 dict(house='Morgan Stanley', team='Equity Research (Ares)',
      title='Ares Management Corp: Private Credit Discussion Takeaways', date='2026-04-02',
      authors='Michael Cyprys, Annalei Davis', file='Private Credit Discussion.pdf', pages=10,
      view='与 ARES 管理层交流后，对其穿越周期并捕捉机会的能力信心增强；股价年内跌 35%、'
           '坏消息已较多反映在价格里，对 ARES 转为偏正面（评级仍为 Equal-weight，目标价 $178）。',
      stance='个股偏正面（行业层面中性）'),
 dict(house='Barclays', team='US HG Credit Research',
      title='Business Development Companies: Early Themes and Trends from 2Q Reporting',
      date='2026-08-04', authors='Peter Troisi, Ishika Goyal',
      file='Barclays_US_HG_Research_Business_Development_Companies_Early_Themes_and_Trends_from_2Q_Reporting.pdf',
      pages=12,
      view='已披露 2Q26 的 BDC 显示资产质量以可控速度转弱：非应计会上升但不会实质冲击多数 BDC 的'
           '盈利或流动性。问题集中在后疫情年份 —— Cliffwater 数据显示 2022 年份的 LTM 非应计几乎是'
           '2023 年份的两倍，2022 及更早年份占直贷市场非应计的七成以上，且这类老年份敞口多在公募 BDC。'
           '另外银行与私募信贷的竞争在加剧（2Q26 SLOOS 显示银行放松了部分 C&I 条件），'
           '部分 BDC 开始参与 hyperscaler 融资。',
      stance='转弱但可控'),
 dict(house='UBS', team='Global Credit Strategy',
      title='Public and Private Credit Outlook', date='2026-07-22',
      authors='Matthew Mish, Julien Conzano, Sachin Ganesh, Henry Morrison-Jones, Bhanu Baweja',
      file='ued42349.pdf', pages=33,
      view='美国处在信用周期的更后段，由私募信贷与低评级杠杆融资市场领跌，压力迹象更多；'
           '欧洲整体比美国健康。预测美国利差跑输、杠杆贷款利差最弱：'
           '美国 LL 从当前 480bp 走阔到 3Q26 510bp、4Q26 575bp；美国 HY 267→275→325bp；'
           '美国 IG 75→75→85bp。全球私募信贷违约率美国上行、欧洲下行。',
      stance='看空利差，尤其杠杆贷款',
      note='⚠ 文件名是 ued42349.pdf，看不出是谁的报告 —— 认 PDF 内页标题与作者。'),
 dict(house='Goldman Sachs', team='Credit Strategy Research',
      title='Macro Credit Views: Dispersion, not disruption', date='2026-06-29',
      authors='Amanda Lynam', file='Macro Credit Views_ Dispersion, not disruption.pdf', pages=12,
      view='方向上只是温和走阔，被「按收益率买」的资金托住：养老金与保险至少持有美元公司债存量的四成，'
           '且美元 IG 长端收益率 5.7% 明显高于美国寿险业债券组合平均收益率 4.8%，'
           '配置还有增加空间。所以尽管利差历史分位偏紧、供给压力也大，仍只看温和走阔。',
      stance='分化而非崩塌'),
 dict(house='J.P. Morgan', team='North America Equity Research (Life Insurance)',
      title='J.P. Morgan Life Insurance: Private Credit 1Q26 Snapshot', date='2026-06-26',
      authors='Pablo S. Singzon, Kevin Wijendra', file='JPM_J_P__Morgan_Life_Ins_2026-06-26_5348342.pdf',
      pages=9,
      view='寿险的私募信贷敞口约占投资资产 17%，其中约九成是投资级（整体组合是 95/5），'
           '主要是私募配售这类成熟资产类别，因此整体可接受。但监管数据显示（含 144a）敞口自 2012 年'
           '以来几近翻倍至约 40%，且私募信用评级用得越来越多、透明度下降。'
           '真正需要盯的是资产杠杆更高的年金型寿险公司。',
      stance='可接受，但透明度下降'),
]

D = json.load(io.open('series.json', encoding='utf-8'),
              object_pairs_hook=collections.OrderedDict)
e = D['exhibits']['sent_broker_summary']
e['_shape'] = 'rows_flat'
e['rows'] = [dict(label=f"{r['house']} — {r['title']}", **r) for r in ROWS]
e['as_of'] = '2026Q3'
e['src'] = ('2026Q3/Broker/ 目录下 8 份 PDF，逐份读首页/执行摘要后归纳。'
            '每行都锁死了机构 / 团队 / 报告名 / 发布日 / 作者 / 文件名 / 页数，可逐条回溯：'
            + '；'.join(f"{r['house']}《{r['title'][:34]}》{r['date']}（{r['file']}）" for r in ROWS) + '。'
            '⚠ 目录里 8 份文件只对应 7 条独立观点 —— '
            '"Private Credit Tracker 1Q26 – Softening Fundamentals.pdf" 与 Market 目录下的 '
            '"MS Private Credit 1Q26 tracker.pdf" 是同一份（md5 都是 1b4730b8f1fc7cf1607f5dc73893f6e9），'
            '这里按一条计，别数成两家。'
            '⚠ 文件名不可靠：UBS 那份叫 ued42349.pdf、MS 的两份靠标题才分得清团队 —— 一律认内页标题与作者。'
            '⚠ 取阅记录：MS 的几份页脚写 "Downloaded by steven.xu@junsoncapital.com"，'
            'GS 那份写 "For the exclusive use of XIYANG.ZHAO@JUNSONCAPITAL.COM" —— '
            '都是内部取阅，转发受限，正文引用只写机构与报告名，不要把这些字段贴进报告。'
            '本节是观点归纳，不含任何本报告自行计算的数字；表里出现的数字（如 UBS 的利差预测、'
            'Barclays 引用的 Cliffwater 年份数据）都是原报告的原话。')
e['note'] = ('Note: Summary of sell-side views on private credit published between April and August 2026, '
             'as read from the reports in the quarter\'s broker folder. Each row records the publisher, '
             'report title, date and authors so the view can be traced back. Figures quoted are the '
             'publishers\' own. Sources: Morgan Stanley, Barclays, UBS, Goldman Sachs and J.P. Morgan '
             'research, as listed.')
e['_method'] = '逐份读首页/执行摘要归纳；8 份文件 → 7 条独立观点（1 份重复）'
e['source_line'] = 'Sell-side research, as listed'
json.dump(D, io.open('series.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
n = sum(1 for v in D['exhibits'].values() if v.get('src'))
print(f'Ex 30 写入完成；src 覆盖 {n}/58')
