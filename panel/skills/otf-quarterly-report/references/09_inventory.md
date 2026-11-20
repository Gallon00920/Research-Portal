# 全篇图表总清单（21 图 + 14 表 + 1 装饰条）

### 7. 全篇图表总清单（21 图 + 14 表 + 1 装饰条）


这一节是**对照清单**：把「V4 细化行文结构」的附录清单、2026Q2 版完整报告的实际图表、以及本 prompt 的覆盖范围三方对齐。**生成时逐项核对，缺一即回补。**

### 7.1 图（21 张，本 prompt §6 已逐张给规格）

| # | 章节 | 图 | V4 清单 | 完整报告 | 本 prompt |
|---|---|---|---|---|---|
| 1 | 2.1 Industry | 行业双饼 + 表 | ✓ | ✓ | ✓ |
| 2 | 2.2 Cash yield trend | 分组柱 + SOFR 折线 | ✓ | ✓ | ✓ |
| 3 | 2.2 NAV bridge | 瀑布 | ✓ | ✓ | ✓ |
| 4 | 2.2 NII & dividend coverage | 柱 + 覆盖率折线 | ✓ | ✓ | ✓ |
| 5 | 2.3 PIK | 折线 + 行业均值 | ✓ | ✓ | ✓ |
| 6 | 2.3 Non-accrual | 双线 + 行业均值 | ✓ | ✓ | ✓ |
| 7 | 2.3 Internal risk rating | 100% 堆叠柱 | ✓ | ✓ | ✓ |
| 8 | 2.5 Price comparison | OTF vs 四家软件 | ✓ | ✓ | ✓ |
| 9 | 2.5 Price comparison | OTF vs 五家 BDC | ✓ | ✓ | ✓ |
| 10 | 2.6.2 Return comparison | BDC NAV per share | ✓ | ✓ | ✓ |
| 11 | 2.6.2 Return comparison | BDC dividend yield on NAV | ✓ | ✓ | ✓ |
| 12 | 2.6.2 Return comparison | BDC PIK income % | ✓ | ✓ | ✓ |
| 13 | 2.6.3 Asset quality | BDC non-accrual rate | ✓ | ✓ | ✓ |
| 14 | 2.6.3 Asset quality | BDC portfolio co. avg EBITDA | ✓ | ✓ | ✓ |
| 15 | 3.3 Fundamentals | Borrower leverage | ✓ | ✓ | ✓ |
| 16 | 3.3 Fundamentals | Interest coverage | ✓ | ✓ | ✓ |
| 17 | 3.3 Fundamentals | Non-accruals across BDCs | ✓ | ✓ | ✓ |
| 18 | 3.3 Fundamentals | PIK / total investment income | ✓ | ✓ | ✓ |
| 19 | 3.3 Fundamentals | PIK / net investment income | ✓ | ✓ | ✓ |
| 20 | 3.3 Fundamentals | Non-accruals by sector | ✓ 条件触发 | ✓ | ✓ |
| 21 | 4.3 AI impact on software layers | 软件分层示意图（**层数每季按研报重定**）| **✗ V4 写「不配图」** | ✓ | ✓ |

> 图 21 是最终版新增的：V4 里 4.3 明确写「一小节 3–5 条 bullets、**不配图**」，但 2026Q2 版报告放了分层示意图。**以最终版为准，这张图要做**，且每季按当季研报重画（§6 图 21 的红框）。

### 7.2 表（14 张 —— 本 prompt 之前只点了名，现在给规格）

> ### ⛔ 「无边框、无底纹」是错的 —— 按 v1 报告的真实表格样式来
>
> 这套样式是从 v1 报告的 `word/document.xml` 里直接读出来的，**有框线、有底色**：
>
> | 元素 | 规格 |
> |---|---|
> | 全部框线（含内框线） | `#C9D2DC`，`sz=4`（0.5pt），single |
> | 表头行 | 底色 `#1F3B5B`，白字 `#FFFFFF`，**加粗**；首列左对齐，数值列居中 |
> | 数据行 | **只有首列**有底色 `#EEF2F6`，数值列留白 |
> | 正文 | 色 **`#000000`（纯黑）**，**8pt（`sz=16`）**，字体 **Arial**（容器里用 Liberation Sans 替代，度量兼容）|
> | Total 行 | 加粗；`QoQ Chg` 列的 `—` 不加粗 |
> | 单元格边距 | 上下 90 dxa、左右 120 dxa，垂直居中 |
> | 列宽 | 40% / 18% / 18% / 24%，表宽 7.12 in 满宽 |
> | 表下小注 | 灰色斜体 `#5A6B7B`，10pt |
>
> `otf-quarterly-update` skill 里写的「中文正文、等线、无框无色」是给**中文表**的，套到这批英文表上就错了。

**T1 出成 PNG，其余 13 张是 Word 原生表格。** T1 用 `tablelib.py` 渲染：HTML + CSS 写好上面这套样式，再用 Chromium 截图（`device_scale_factor=2`，CSS 表宽 800px → 输出约 1600px）。**不要用 matplotlib 画表** —— 框线和文字对齐的度量控制不住。

每张表下方紧跟一段灰色斜体小注（口径 + 来源），再接正文点评。数值列一律「上季 / 本季 / QoQ Chg」三列，`QoQ Chg` 用 `↑ +0.1pp` / `↓ −0.2pp` / `flat` / `—`，负号用 `−`。

| # | 章节 | 表 | 列 | 行 / 内容要点 |
|---|---|---|---|---|
| **T1（出成 PNG）** | 2.1 Capital structure | 资产类型占比 | 资产类型 ｜ PQ ｜ CQ ｜ QoQ Chg | 一留 / 二留 / 无担保及专业金融债 / 优先股 / 普通股及 JV / Total；再加 memo 行：senior secured、total debt、total equity & JV、unitranche 占一留比 |
| T2 | 2.1 Industry | 行业占比（配图 1） | 行业 ｜ PQ ｜ CQ ｜ QoQ Chg | 按 CQ 降序前 10 + Other + Total；memo 行：系统+应用软件合计、前十合计、持有行业数 |
| T3 | 2.1 Software layer exposure | 软件分层敞口 | 层 ｜ 占组合公允值 % ｜ 代表持仓 | Application / Platform / Infrastructure / 非软件；代表持仓每层 ≤3 家。**占比从本季 10-Q Schedule of Investments 自算，禁止取草稿 xlsx（那是去年数据）** —— 见 `08_tables.md` 专节 |
| T4 | 2.1 Borrower fundamentals | 借款人基本面 | 指标 ｜ PQ ｜ CQ ｜ QoQ Chg | 加权平均收入 / EBITDA / 企业价值 / Net LTV / 平均持仓规模 / 组合公司数。**Net LTV 必须在小注里写出季报的估值方式**（attachment point → last-dollar → enterprise value 的算法）；未披露就写「本份文件未披露」，不硬凑 |
| T5 | 2.2 Financing profile | 融资结构 | 工具 ｜ 承诺额 ｜ PQ 已提取 ｜ CQ 已提取 ｜ QoQ Chg | 循环额度 / 各 SPV / CLO / 各期票据（标票息与到期）+ Total debt + 无担保占比 + 可用流动性。新增与到期的工具要在名称里标 `— new, <月>-<yy>` / `— matured` |
| T6 | 2.2 Leverage ratio | 杠杆与资本 | 指标 ｜ PQ ｜ CQ ｜ QoQ Chg | 净杠杆 / 管理层目标区间 / 资产覆盖率（标注 150% 法定下限）/ 到目标上限的加杠杆空间 / 触发下限前可吸收的组合跌幅。**这张表在 Leverage ratio 那段文字之后** |
| T7 | 2.4 Sell-side view & TP | 卖方目标价汇总 | 券商为列（文件夹内 + 联网找到的**最近一季**覆盖） | 行 = Rating ｜ Target price ｜ QoQ Chg ｜ Valuation（无则 NA）｜ Key points。联网找到的券商必须在小注里写来源并附链接；只有文件夹内一家也要做成表 |
| T8 | 2.5 Price comparison | 上市以来跌幅 | Ticker ｜ 上市日收盘 ｜ `AS_OF` 收盘 ｜ Since listing | OTF 第一行，同业按跌幅降序；`Since listing` 1 位小数带符号 |
| T9 | 2.6.1 BDC competitor analysis | 六家竞品对比（横排 landscape） | OTF ｜ ARCC ｜ BXSL ｜ OBDC ｜ TSLX ｜ GBDC（代号 + 全名） | 行 = 底层资产 / Key factors / 流动性压力 / P/NAV 与股息率；每格 ≤4 条、每条 ≤2 行。**Thesis 粗体判断段放表前**。数据全部来自 `competitor earnings\` 五份当季 filings + OTF 当季 10-Q |
| T10 | 3.1 Broker view summary | 私募信贷/BDC 券商观点 | 券商为列，**列由当季实际研报决定、不写死**；同一家不同团队观点背离才拆两列 | 行 = 覆盖范围 / View / Key Points / QoQ Chg。每列带覆盖标签（Private Credit / BDC / 两者）；Key Points 3–4 条，必带具体数据，点名 BDC ≤3 家 |
| T11 | 4.1 Broker view | AI×软件券商观点 | 券商为列（当季实际研报决定） | 行 = Key Points（3–4 条 bullet）/ QoQ 观点变化。**表内不出现个股 ticker** |
| T12 | 4.1 Company view（上） | 软件公司观点 | MSFT ｜ ORCL（2 列，适配竖排） | 行 = View（英文标签）/ Key Points；每家带一个关键指标 |
| T13 | 4.1 Company view（下） | 软件公司观点 | CRM ｜ NOW（2 列） | 同 T12 |
| T14 | 4.1 Market consensus & key debate | 共识与分歧 | Debate ｜ Broker stance ｜ Software-company stance ｜ Core of the disagreement | 只由 T11–T13 综合，不引入新料、不重复同一数字 |

### 7.3 装饰条（1 张，容易漏）

| # | 位置 | 规格 |
|---|---|---|
| 图 0 | 首页标题行下方 | 横向渐变条，Word 宽 **7.11 in** × 高 **0.23 in**（v3 实测）（原 PNG 1702×56 px 等比缩到 7.12 in；A4 竖版满宽）。左侧到约 62% 处为实色 `#1B355F`，之后线性渐变到右边缘白色 `#FFFFFF`。每季直接复用同一个 PNG，不用重画 |

### 7.4 V4 里有、但最终版**已删 / 未做**的项（**不要生成**）

| V4 清单项 | V4 状态 | 最终版 | 处理 |
|---|---|---|---|
| Implied TP 表（Base/Bear/Bull 三情景 → 隐含目标价） | ~~划线，计划删去~~ | 无 | **不生成**。数据在草稿 xlsx `OTF` sheet 里（Breakeven / Exit year 矩阵），属人写的估值归因，skill 不介入 |
| Position monitoring 表 ×2（持仓快照 + breakeven 矩阵） | ~~划线，计划删去~~ | 无 | **不生成** |
| GS 软件敞口图（3.4.1 Software exposure） | 可选 | 无，3.4.1 只有文字 | **默认不生成**。要做的话按 §4.2 / §4.4 重画，不许截 GS 原图 |
| Leverage ratio 的目标区间刻度图 | 「可选配一条极简水平刻度图」 | 无，只有文字 + T6 | **默认不生成**。要做的话：单行水平刻度，`0.90–1.25x` 目标区间用 `#9DB8D2` 底色带，当前净杠杆用 `#A93226` 竖线标出并标值，`150%` 法定下限对应位置用灰色虚线 |

> 这四项每季**明确跳过**，不要因为 V4 附录里列着就补出来。若某季确实要加回来，先在正文里给它一个固定栏位，再进这张清单。

### 7.4b V4 里已经作废的指令（照着做就错）

| V4 原话 | 为什么作废 |
|---|---|
| 「行业用中文名（系统软件/应用软件/医疗科技/多元金融服务...）」 | **图内一律英文**（§4.1）。图 1 饼图的行业标签用英文简称：`Systems Software`、`Application Software`、`Health Care Tech`、`Div. Financial Services`、`Div. Consumer Services`、`HC Providers & Services`、`Aerospace & Defense`。最终版就是英文，V4 那句不要照做 |
| 「表格一律无边框、无底纹」 | 见 §7.2 红框。v1 报告的表格有 `#C9D2DC` 框线、`#1F3B5B` 表头、`#EEF2F6` 首列 |
| 「4.3 一小节 3–5 条 bullets、不配图」 | 最终版配了软件分层示意图（图 21）|
| 「从 MS Tracker 抠图（保留 Source 行）」 | **不许截屏**，一律读点重画（§6 图 15–20）；§2.3 两张图连来源都不写（§6 §2.3 红框）|

### 7.5 V4 里的几条全局要求（本 prompt 已吸收，列此备查）

- **图片必须缩放到与正文两端同宽** → `03_style.md` 的插入宽度表（A4 竖版图片插入宽 = **7.11 in**；2.6.1 横版节 10.54 in）。
- **每张图下面都要单独的分析与说明**，尤其 §3.3 的六张图，一图一段，不许合并点评。
- **broker 研报自带的图，凡要放进报告的一律重画** → §6 里 图 15–20 全部标了「读点重画，不许截屏」。
- **股价图必须画到今天的前一个交易日** → §2.1 的 `AS_OF`。
- **图不加「图 N｜」题注，只保留 `*` 小注** → §4.4 的脚注规范。唯一例外是图 21，它在最终版里带 `Exhibit <n>` 图注。
- **提到回购要注明具体哪家公司** → T9 的「流动性压力」行、T1/T6 的小注。

---
