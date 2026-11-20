# 14 张表：样式与规格

## T1 出成 PNG，其余 13 张是 Word 原生表格

`tablelib.py` + `build_tbl01.py` 出 T1 的 PNG。**用 Chromium 截图不用 matplotlib** —— 表格框线和文字对齐的度量控制不住。

## 表格真实样式（从 v1 报告的 `word/document.xml` 读出来的；字号已按最新要求改为 8pt）

> **所有 14 张表统一 Arial 8 号**，表头、数据、行标、Total 行、表下小注一律 8pt（`w:sz="16"`）。
> 只有字号变，框线色、底色、加粗、边距、列宽全部不动。
> **T1 是 PNG**，所以它的 8pt 要在渲染时就是 8pt —— 画布宽 7.11 in、1:1，HTML 里直接写 `font-size:8pt`。

> ⛔ 「无边框、无底纹」是错的。**有框线、有底色。**

| 元素 | 规格 |
|---|---|
| 全部框线（含内框线）| `#C9D2DC`，`sz=4`（0.5pt），single |
| 表头行 | 底色 `#1F3B5B`，白字 `#FFFFFF`，**加粗**；首列左对齐，数值列居中 |
| 数据行 | **只有首列**有底色 `#EEF2F6`，数值列留白 |
| 正文 | 色 **`#000000`（纯黑）**，**8pt（`sz=16`）**，字体 **Arial**（容器里用 Liberation Sans 替代，度量兼容）|
| Total 行 | 加粗；`QoQ Chg` 列的 `—` 不加粗 |
| 单元格边距 | 上下 90 dxa、左右 120 dxa，垂直居中 |
| 列宽 | 数值型四列表 = 40% / 18% / 18% / 24%，表宽 7.12 in 满宽（A4 竖版正文满宽；T9 在横版节按 **10.54 in**） |
| 表下小注 | 灰色斜体 `#5A6B7B`，**Arial 8pt**，写口径 + 来源 |

数值列一律「上季 / 本季 / QoQ Chg」三列，`QoQ Chg` 用 `↑ +0.1pp` / `↓ −0.2pp` / `flat` / `—`，负号用 `−`（U+2212）。

## 哪几张的数进账本

| 表 | 进账本？ | 理由 |
|---|---|---|
| **T1** Capital structure | ✅ 已在 `tbl01_capital_structure` | 有上季列 |
| **T4** Borrower fundamentals | ✅ 要进 `tbl04_borrower_fundamentals` | 有上季列，冻结才能免掉下季回翻上季 filing |
| **T5** Financing profile | ✅ 要进 `tbl05_financing_profile` | 同上 |
| **T6** Leverage & capital | ✅ 要进 `tbl06_leverage_capital` | 同上 |
| T2 Industry | 已在 `fig01_industry_pie` | 跟图 1 同一份数据 |
| T3 Software layer exposure | ✅ 要进 `tbl03_software_layer` | 占比是**本季自算**的，公司→分层映射必须冻结，否则每季重判 205 家 |
| T8 Since-listing 跌幅表 | ❌ | 由 `prices.csv` 直接算，确定性计算无分歧空间 |
| T9 六家竞品 | ❌ 但**数值必须从账本读** | 五个指标 = 图 10–14 的数据，重抽就是自找矛盾 |
| T7、T10–T14 | ❌ | 内容是判断不是数值。里面出现的数字要过 `crosscheck.py` |

## 逐张规格

| # | 章节 | 表 | 列 | 行 / 要点 |
|---|---|---|---|---|
| **T1** | 2.1 Capital structure | 资产类型占比（**PNG**）| 资产类型 ｜ PQ ｜ CQ ｜ QoQ Chg | 一留 / 二留 / 无担保及专业金融债 / 优先股 / 普通股及 JV / Total + 四个 memo 行。**senior secured = 一留 + 二留**，10-Q 把 specialty finance debt 与两档并列，不计入 |
| T2 | 2.1 Industry | 行业占比（配图 1）| 行业 ｜ PQ ｜ CQ ｜ QoQ Chg | 按 CQ 降序前 10 + Other + Total；memo：系统+应用软件合计、前十合计、持有行业数 |
| T3 | 2.1 Software layer | 软件分层敞口 | 层 ｜ 占组合公允值 % ｜ 代表持仓 | Application / Platform / Infrastructure / 非软件；代表持仓每层 ≤3 家。**占比必须从本季 10-Q 的 Schedule of Investments 自算，见下方专节** |
| T4 | 2.1 Borrower fundamentals | 借款人基本面 | 指标 ｜ PQ ｜ CQ ｜ QoQ Chg | 加权平均收入 / EBITDA / 企业价值 / Net LTV / 平均持仓规模 / 组合公司数。**Net LTV 的估值方式必须写在小注里**；未披露写「本份文件未披露」，不硬凑 |
| T5 | 2.2 Financing profile | 融资结构 | 工具 ｜ 承诺额 ｜ PQ 已提取 ｜ CQ 已提取 ｜ QoQ Chg | 循环额度 / 各 SPV / CLO / 各期票据（标票息与到期）+ Total debt + 无担保占比 + 可用流动性。新增与到期在名称里标 `— new, <月>-<yy>` / `— matured` |
| T6 | 2.2 Leverage ratio | 杠杆与资本 | 指标 ｜ PQ ｜ CQ ｜ QoQ Chg | 净杠杆 / 管理层目标区间 / 资产覆盖率（标 150% 法定下限）/ 到目标上限的加杠杆空间 / 触发下限前可吸收的组合跌幅。**放在 Leverage ratio 那段文字之后** |
| T7 | 2.4 Sell-side view & TP | 卖方目标价汇总 | 券商为列（文件夹内 + 联网找到的**最近一季**覆盖）| 行 = Rating ｜ Target price ｜ QoQ Chg ｜ Valuation（无则 NA）｜ Key points。**不写研究员姓名**。联网找到的必须在小注里写来源并附链接；只有文件夹内一家也要做成表 |
| T8 | 2.5 Price comparison | 上市以来跌幅 | Ticker ｜ 上市日收盘 ｜ `AS_OF` 收盘 ｜ Since listing | OTF 第一行，同业按跌幅降序；`Since listing` 1 位小数带符号。**永远按上市日算全程**，不受股价图窗口影响 |
| T9 | 2.6.1 | 六家竞品对比（横排 landscape）| OTF ｜ ARCC ｜ BXSL ｜ OBDC ｜ TSLX ｜ GBDC（代号 + 全名）| 行 = 底层资产 / Key factors / 流动性压力 / P/NAV 与股息率；每格 ≤4 条、每条 ≤2 行。**Thesis 粗体判断句放表前，全段不用括号**。五个指标的数值从账本读，独有特征从五家当季 filings 抽 |
| T10 | 3.1 Broker view summary | 私募信贷/BDC 券商观点 | 券商为列，**列由当季实际研报决定、不写死**；同一家不同团队观点背离才拆两列 | 行 = 覆盖范围 / View / Key Points / QoQ Chg。每列带覆盖标签（Private Credit / BDC / 两者）；Key Points 3–4 条必带具体数据，点名 BDC ≤3 家。**不写研究员姓名** |
| T11 | 4.1 Broker view | AI×软件券商观点 | 券商为列（当季实际研报决定）| 行 = Key Points（3–4 条）/ QoQ 观点变化。**表内不出现个股 ticker**（个股归 Company 表）。每条 = 一个可证伪判断：机制 + 点名层级/定价模式 + 精准 hedge，不写「报告认为」 |
| T12 | 4.1 Company view（上）| 软件公司观点 | MSFT ｜ ORCL（2 列，适配竖排）| 行 = View（英文标签）/ Key Points；每家带一个关键指标 |
| T13 | 4.1 Company view（下）| 软件公司观点 | CRM ｜ NOW（2 列）| 同 T12 |
| T14 | 4.1 Market consensus & key debate | 共识与分歧 | Debate ｜ Broker stance ｜ Software-company stance ｜ Core of the disagreement | 只由 T11–T13 综合，不引入新料、不重复同一数字 |


---

## ⛔ T3 Software layer exposure：占比必须自算，禁止取内部 xlsx

**`202607OTF 草稿 - 副本.xlsx` 的 `Crosscheck` sheet 是去年的数据，不许再当占比来源。**
那份 workbook 的分层占比（Application 49.5% / Platform 11.4% / Infrastructure 12.4% / 非软件 26.8%）
是旧口径旧持仓，组合每季都在变（本季 205 家 vs 上季 203 家，公允值 $14.7bn vs $14.1bn），
照抄就是把一年前的结构冒充本季结构。

### 每季怎么算

1. **读本季 10-Q 的 Schedule of Investments**，逐个 portfolio company 取
   **公允值（Fair Value）**与业务描述。这是唯一的占比数据源。
2. **给每家公司判一个层**：`Application` / `Platform` / `Infrastructure` / `Non-software`。
   按**借款人主业**判，不按 GICS 行业码。同一家公司的多笔债权（1L / 2L / revolver / equity）
   合并成一家的公允值。
3. **占比 = 该层公允值合计 ÷ 组合公允值合计**，保留一位小数。
4. **混合 AI 敞口 = Σ(该层占比 × 该层 impact_weight)**，权重仍是 30% / 20% / 5% / 0%。
5. **代表持仓**每层挑 ≤3 家，从该层公允值最大的几家里取，不要写小仓位。

### 公司→分层映射必须冻结（不然每季重判两百多家）

映射存 `_state/layer_map.json`，结构：

```json
{
  "Anaplan":        {"layer": "Application",   "since": "Q2'26", "basis": "planning SaaS, 10-Q business description"},
  "Arctic Wolf":    {"layer": "Infrastructure","since": "Q2'26", "basis": "managed security operations"},
  "SpaceX":         {"layer": "Non-software",  "since": "Q2'26", "basis": "aerospace, not software"}
}
```

**冻结规则与 `series.json` 同级：已判定的公司不重判**，除非该公司主业发生实质变化（并在 `basis` 里写清）。
每季只需要处理**名单差异**：

| 情形 | 做法 |
|---|---|
| 本季新增的公司 | 判层、写进 `layer_map.json`、`since` 记本季 |
| 本季退出的公司 | 保留在 map 里（下季可能回来），但不进本季占比计算 |
| 已有公司 | 直接沿用 map 里的层，**只更新公允值** |

第一次跑要判 200 多家，之后每季通常只有 5–15 家新名字。

### `src` 怎么写

```
"src": "本季 10-Q Schedule of Investments 逐家公允值汇总；公司→分层取 _state/layer_map.json（本季新增 N 家已判层）；混合敞口 = Σ 占比×权重"
```

**`src` 里出现 `.xlsx` / `草稿` / `Crosscheck` 一律 fail** —— `selfcheck.py` 有针对 `tbl03` 的专项检查。
（注意：其他表的 xlsx 来源仍然合法，这条禁令**只针对 tbl03 的占比**。）

### 自查

- 四层公允值合计 == 组合公允值合计（10-Q 披露的 total fair value），差额 > 0.5% 就是有公司漏判
- 四层占比合计 == 100%（±0.15pp 容差，四舍五入所致）
- 混合 AI 敞口 == Σ 占比×权重（±0.06pp）
- 参与计算的公司数 == 10-Q 披露的 portfolio company 数（本季 205）
