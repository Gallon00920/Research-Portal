# 图 1–9 · OTF 自身（§2.1 / §2.2 / §2.3 / §2.5）



### § 2.1 Portfolio composition


---

#### 图 1 · Portfolio by industry — top 10 + other, {PQ} vs {CQ}

- **位置**：`2.1 Portfolio composition → Industry`，图在上、表在下（表最后一列 `QoQ Chg`）。
- **图型**：**双饼并排**，左 `{PQ}`、右 `{CQ}`，各带子标题（bold、`#16283F`）。
- **画布**：`figsize=(18, 8.1)`，纯白底。
- **数据源**：`OTF\` 当季 10-Q 的行业分布表（`Investments by industry` / schedule of investments 汇总）取 CQ；**上季数取上季那份 10-Q**（不要用当季 10-Q 的对比列）。
- **构成**：按 **CQ 占比降序**取前 10 个 GICS sub-industry，余下全部并成 `Other`；**两期用同一套排序和同一套配色**，扇区顺序从 12 点起顺时针。
- **配色**（固定映射到排位，不映射到行业名）：

  | 排位 | 色号 |
  |---|---|
  | 1 | `#16283F` |
  | 2 | `#2E6DA4` |
  | 3 | `#A93226` |
  | 4 | `#8C97A5` |
  | 5 | `#C9A227` |
  | 6 | `#9DB8D2` |
  | 7 | `#4B5B6E` |
  | 8 | `#C08578` |
  | 9 | `#AEB4BC` |
  | 10 | `#6E1F18` |
  | Other | `#D5DAE0` |

- **标注**：扇区外引线标签，格式 `<行业简称> <占比 1 位小数>%`。行业名用简称保持一行：`Health Care Tech`、`Div. Financial Services`、`Div. Consumer Services`、`HC Providers & Services`、`Aerospace & Defense`。扇区间 `wedgeprops={'edgecolor':'white','linewidth':2}`。
- **脚注**：`* % of portfolio fair value; top-10 industries ranked by {CQ}, same order both periods; "Other" = remaining <n> of <N> industries at {CQ} (<n'> of <N'> at {PQ}). Source: OTF {CQ} and {PQ} 10-Q industry composition`
- **配套文字点评**要引用 `<YYYYMM>OTF 草稿*.xlsx` 的 `OTF` sheet：High / Mid 分级各自合计占比及其环比（High = Application Software、Systems Software、Internet & Direct Marketing Retail、IT Services、Professional Services；Mid = 两个 healthcare、三个 diversified services、Life Sciences Tools），以及「按 30% 违约假设的四个行业合计」。**分级表每季按 xlsx 最新版重读，不要背。**

---


### § 2.2 Financial & debt


---

#### 图 2 · Portfolio yields vs funding cost & SOFR

- **位置**：`2.2 → Cash yield trend`
- **图型**：**分组柱状图 3 系列 + 虚线折线 1 系列**（SOFR）。
- **画布**：`figsize=(6.05, 3.5)`（宽度由 `chartlib.figure()` 锁死），纯白底。
- **期数**：5 期（§2.3），x 轴 `Q<n>'<yy>`，Q4 那期标 `Q4'<yy>`。
- ⛔ **柱子上的数值必须水平放置（`rotation=0`），不许竖排。** 这是写死的。
  柱子窄放不下就把 y 轴上限抬高、或缩短数字（`13.1%` 不写 `13.10%`）、或把数值标到柱子外侧上方，
  **不要转 90°**。`guards.assert_flat_labels()` 会拦。
- **系列与配色**：

  | 系列 | 色 | 类型 |
  |---|---|---|
  | Wtd avg total yield of portfolio | `#16283F` | 柱 |
  | Wtd avg yield of debt & income-producing sec. | `#2E6DA4` | 柱 |
  | Avg stated interest rate on debt outstanding | `#A93226` | 柱 |
  | 3M SOFR (reference) | `#8C97A5` | 折线 `ls='--'`, `lw=2.5`, `marker='o'`, `ms=chartlib.ms(2.5)` = 5.0 |

- **图例**：图外顶部，**2 行 × 2 列**，`frameon=False`；SOFR 排第一位（左上）。
- **y 轴**：`%`，从 0 起，上限留到 12。
- **标注**：每根柱顶标 1 位小数（不带 `%`），bold、同系列色；SOFR 只在**最后一期**标值，标在点右侧、色 `#8C97A5`。
- **数据源**：`OTF\` 当季 10-Q（portfolio yield 披露）+ 当季 deck；SOFR 用 deck 的对照页或 10-Q 里的 base rate 披露。历史 4 期从 `历史报告\` 对应 filing 取。
- **脚注模板**：
  ```
  * Navy: weighted-avg total yield of the whole portfolio at fair value, incl. non-accruals and OID accretion. Blue: same yield on accruing debt & income-producing securities only.
  Red: avg stated interest rate on OTF's own outstanding borrowings, i.e. its funding cost. Gray dashed: 3-month SOFR, the floating base rate driving both asset coupons and
  funding cost. Source: OTF {CQ} 10-Q; {CQ} Earnings Presentation slides <n> & <m>
  ```

---

#### 图 3 · NAV per share bridge — {PQ} → {CQ}

- **位置**：`2.2 → NAV bridge`
- **图型**：**瀑布图**。首尾为落地柱（`#16283F`，从 y 轴下界起），中间为悬空增量柱；相邻柱之间用**灰色虚线连接**（`ls='--'`, `lw=1`, 灰）。
- **画布**：`figsize=(16.2, 8.2)`，纯白底。
- **拆项**：**照抄当季 deck 的 "Net Asset Value Per Share Bridge" 页的拆项，不要自己合并或新增**。2026Q2 那季为：`{PQ} NAV` → `Adjusted NII` → `Base dividend` → `Special dividend` → `Repurchase accretion` → `Realized & unrealized gain & other` → `{CQ} NAV`。
- **配色**：正增量 `#2E6DA4`，负增量 `#A93226`，首尾 `#16283F`。
- **标注**：增量柱标 `+0.30` / `−0.35`（2 位小数，带符号，U+2212），色随柱；首尾柱标绝对值（`16.49` / `16.48`），色 `#16283F`，均 bold、置于柱外。
- **x 轴标签**：长项分两行（`Realized &` / `unrealized` / `gain & other`）。
- **y 轴**：`NAV per share ($)`，范围收窄到能看清 0.01 级变化（如 15.4–17.0），不要从 0 起。
- **脚注模板**：
  ```
  * Bridge items per {CQ} Earnings Presentation p.<n>; <口径说明，如 GAAP NII/sh equalled adjusted NII/sh at $X this quarter; change in accrued capital-gains incentive fee was $0.00 and is
  omitted>; items rounded, sum may differ from ending NAV due to rounding
  ```
- **注意**：deck 里若某拆项当季为 0，**在脚注写明已省略**，不要画一根零高度柱。

---

#### 图 4 · NII vs dividend & coverage

- **位置**：`2.2 → NII & dividend coverage`
- **图型**：**分组柱（NII 单柱 + 分红堆叠柱）+ 右轴折线（覆盖率）**。
- **画布**：`figsize=(17, 9)`，纯白底，双轴。
- **期数**：5 期，x 轴 `Q<n>'<yy>`。
- **系列与配色**：

  | 系列 | 色 | 类型 | 轴 |
  |---|---|---|---|
  | GAAP NII / sh | `#16283F` | 柱 | 左 |
  | Base dividend / sh | `#2E6DA4` | 堆叠柱下段 | 左 |
  | Special dividend / sh | `#8C97A5` | 堆叠柱上段 | 左 |
  | Coverage (rhs) | `#A93226` | 折线 `lw=2.5`, `marker='o'` | 右 |

- **图例**：图外顶部单行 4 项，`frameon=False`。
- **左轴** `$ per share`；**右轴** `Coverage (GAAP NII ÷ total dividend, %)`，轴脊、刻度、轴标题全部 `#A93226`。
- **标注**：NII 柱顶标 2 位小数 bold（`#16283F`）；分红堆叠柱顶标合计（`0.40`），色 `#8C97A5`；覆盖率折线每点标整数百分比（`75%`），色 `#A93226`，放在点下方偏右避让柱子。
- **覆盖率定义**：`GAAP NII ÷ 当季宣派总分红（base + special）`。同时在正文写出「仅对 base 的覆盖率」，但**不入图**。
- **数据源**：`OTF\` 当季 10-Q financial highlights / income statement + 历史 filings；分红宣派金额从 deck / 10-Q 附注取。
- **脚注模板**：
  ```
  * Navy: GAAP net investment income per share each quarter (adjusted NII was $X in {PQ} and $Y in {CQ}). Blue + gray: dividends declared for the quarter — fixed $Z
  base after the Jun-2025 listing; the $0.05 specials are a finite five-tranche series tied to the listing that ends with the <quarter> payment on <date>. Red line: coverage = GAAP NII ÷
  total declared dividend. Source: OTF 10-Q financial highlights & income statements; {CQ} Earnings Presentation p.<n>
  ```

---


### § 2.3 Default concern —— 违约代理三图（全篇证据链核心）


三张图共用同一套骨架：**OTF 自身序列（navy，粗）+ BDC 行业均值参照（`#8C97A5`，细）+ 本季点红色高亮**；6 期，Q4 标 `FY<yy>`。行业均值取自 MS Private Credit Tracker，**比 OTF 少一期**，所以灰线到 `Q1'26` 就停，脚注写 `no {CQ} sector print yet`。

> ### ⛔ 本节硬规则：图 5 / 图 6 的图面不出现来源，也不出现括号
>
> - **不写 `Source:`、不写 `per Morgan Stanley Private Credit Tracker`、不写 `Re-plotted from …`** —— 无论在脚注还是在图上的灰色说明行。
> - **括号连同括号里的内容一律删掉** —— `(2.8% at 1Q26 as disclosed, a five-year high; earlier quarters digitised from the source chart)` 这种整段删除，不要改写成不带括号的版本。
> - 出处不是不要，而是**只写进 `series.json` 的 `src` 字段**（§3.3）—— 自己心里有数、随时可复核，但图上不露。
> - 图 7 同属本节，**脚注同样不写来源**；但图 7 括号里是 10-Q 的评级释义（`1 = performing above expectations`…），属于口径定义不是出处，**保留**。
> - 这条只管 §2.3。其余各图（§2.2、§2.5、§3.3 等）照旧在脚注写具体来源到页码。

---

#### 图 5 · PIK income as % of total investment income

- **位置**：`2.3 → PIK`
- **图型**：双折线（上 navy = OTF，下灰 = 行业均值），**上下分离、不共享标注区**。
- **画布**：`figsize=(13.7, 5.5)`，纯白底（扁）。
- **系列**：OTF `#16283F`，`lw=3`，`marker='o'` `ms=10`；BDC sector average `#8C97A5`，`lw=2`，`marker='s'` `ms=8`。
- **标注**：OTF 每点上方标 1 位小数百分比 bold；**最后一期点 `#A93226`、`ms=16`、标签同色**。灰线每点下方标值（`#8C97A5`，非 bold）。
- **灰线不用图例**，改在灰线上方直接写一行 bold 说明：`BDC sector average — quarterly through {行业最新期}`，色 `#8C97A5`。
  > **§2.3 三张图不写来源、不用括号**（见本节开头的红框规则）：说明行里**不许**出现 `MS Private Credit Tracker` 之类的出处，也**不许**带括号。出处只写进 `series.json` 的 `src` 字段，图上不露。
- **y 轴** `%`，范围留到能同时容纳两条线且中间有空白（如 4–17）。
- **数据源**：OTF 各期 filing 的 PIK interest + PIK dividend ÷ total investment income；**单季口径**，年末点用「全年 − 前九个月」。行业均值取 MS Tracker 的 `%PIK Income over Total Investment Income`。
- **脚注模板**（**无来源、无括号**）：
  ```
  * PIK interest + PIK dividends ÷ total investment income, single-quarter basis; year-end point = full year − nine months; each point from that period's filing.
  {CQ} = \$A ÷ \$B = C%. Gray series: BDC sector average PIK share of total investment income — quarterly through {行业最新期}; no {CQ} sector print yet.
  ```

---

#### 图 6 · Non-accruals — at amortized cost vs at fair value

- **位置**：`2.3 → Non-accrual`
- **图型**：双折线（OTF 成本口径 + OTF 公允值口径）+ 灰色行业均值线。
- **画布**：`figsize=(13.9, 5.7)`，纯白底。
- **系列**：`At amortized cost` `#16283F` `lw=3` `marker='o'`；`At fair value` `#2E6DA4` `lw=3` `marker='s'`；行业均值 `#8C97A5` `lw=2` `marker='s'`。
- **关键**：公允值口径**只从有披露的那一期开始**（2026Q2 那季是 FY25 起），**之前留空，不连线、不插值**。
- **图例**：图内左中部，只放 OTF 两条线，`frameon=False`；行业均值同图 5 用图上一行 bold 文字说明，文案 `BDC sector average at cost — quarterly through {行业最新期}`，**无来源、无括号**。
- **标注**：成本线值标在点上方（`#16283F`，bold）；公允值线值标在点下方（`#2E6DA4`，bold）；灰线值标在点上方（`#8C97A5`）。
- **脚注模板**（**无来源、无括号**）：
  ```
  * Non-accrual investments as % of the total portfolio; fair-value basis disclosed from {首个披露期} onward — earlier gaps left blank, not interpolated; each point from that
  period's filing. {CQ}: <n> issuers on non-accrual, <m> added in the quarter. Gray series: BDC sector average non-accrual rate at cost — quarterly through {行业最新期};
  no {CQ} sector print yet.
  ```

---

#### 图 7 · Internal risk ratings distribution

- **位置**：`2.3 → Internal risk rating`
- **图型**：**100% 堆叠柱**，6 期。
- **画布**：`figsize=(16.2, 9.2)`，纯白底。
- **分段与配色**（自下而上）：`Rating 1` `#16283F` → `Rating 2` `#2E6DA4` → `Rating 3` `#8C97A5` → `Rating 4+5` `#A93226`。
- **图例**：图外顶部单行 4 项，`frameon=False`。
- **标注**：Rating 1/2/3 的值标在**段内居中、白字 bold**（1 位小数，不带 `%`）；`Rating 4+5` 段太薄，标在**柱顶外侧**，写成 `4+5: 0.5`，色 `#A93226`，bold。
- **y 轴** `% of portfolio fair value`，0–100（上方留出 4+5 标签空间）。
- **数据源**：当季 deck 的 Investment Rating 页；历史 5 期从 `历史报告\` 对应 filing 的 Investment Rating 表取。若 rating 5 四舍五入为 0.0% 则与 4 合并，并在脚注写明。
- **脚注模板**：
  ```
  * Per 10-Q definitions: 1 = performing above expectations (lowest risk); 2 = performing as expected (all new investments start at 2); 3 = performing below expectations, risk
  increased; 4/5 = performing materially/substantially below expectations, principal at risk (5 highest). {CQ} rating-4 is X% and rating-5 rounds to 0.0% — shown combined.
  Each point from that period's filing.
  ```

---


### § 2.5 Price comparison


---

#### 图 8 · OTF vs leading software companies — share price
#### 图 9 · OTF vs leading BDCs — share price

两张图同一套规格，只换 peer set。

- **位置**：`2.5 Price comparison`，两图上下排列，下面接 since-listing 跌幅表（Word 表格）。
- **图型**：归一化日线走势图，**起点 2025-06-12（OTF NYSE 上市日）归一至 100**。
- **画布**：`figsize=(16.2, 9.4)`，纯白底。
- **peer set 与配色**：

  | 图 8（软件） | 色 | | 图 9（BDC） | 色 |
  |---|---|---|---|---|
  | MSFT | `#4B5B6E` | | ARCC | `#4B5B6E` |
  | ORCL | `#C9A227` | | BXSL | `#C9A227` |
  | CRM | `#9DB8D2` | | OBDC | `#9DB8D2` |
  | NOW | `#AEB4BC` | | TSLX | `#AEB4BC` |
  | **OTF** | `#A93226` | | GBDC | `#2E6DA4` |
  | | | | **OTF** | `#A93226` |

  OTF：`lw=3.5`，`zorder` 最高，带轻微阴影（`SimpleLineShadow(offset=(1.6,-1.6), alpha=0.3)`）；peer `lw=1.6`。

- **数据**：`Report\` 里**没有价格文件** → 联网取各 ticker 日收盘（stockanalysis.com 等），`2025-06-12` 至 `AS_OF`；**未经股息调整**。落盘成 CSV 缓存（列名 `date, <TICKER>_close_usd`），下次增量 append、按 `date` 去重。抓不到就用上次缓存并在脚注写明截止日。
- **必备元素**：
  - `axhline(100)`：灰、`ls='--'`、`lw=1`、`alpha=0.5`；
  - **右上角** `As of {AS_OF}`，色 `#5A6B7B`；
  - **右侧末点标签**：`<TICKER> <归一化值取整>`，同系列色，OTF bold；标签按末值排序后**上下错开**（最小间距 = y 跨度 3.2%），被顶开的标签补一根细引线；
  - **图例**：图内左下角单行，`frameon=False`；
  - y 轴 `Indexed price (start = 100)`；x 轴按月主刻度、格式 `YYYY-MM`。
- **脚注模板**：
  ```
  * Indexed to 100 at OTF's NYSE listing date 2025-06-12, daily closes. MSFT Microsoft; ORCL Oracle; CRM Salesforce; NOW ServiceNow. Source: exchange closing prices
  via stockanalysis.com, through {AS_OF}
  ```
- **配套跌幅表（Word 表格，不是图）**：列 = `Ticker` / `Listing-day close 6/12/25` / `Close {AS_OF}` / `Since listing`；OTF 排第一行，其余**按跌幅从大到小**；`Since listing` 用 1 位小数带符号。

---
