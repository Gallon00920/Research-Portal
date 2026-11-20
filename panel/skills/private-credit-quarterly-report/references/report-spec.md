# Report specification — section-by-section contract

This is the fixed analytical framework of the Junson Private Credit Quarterly.

> ⚠ **下文的 Exhibit 编号是 2026Q3 基线的编号，仅供阅读定位。**
> **实际编号由 `scripts/exhibit_manifest.json` + `scripts/exhibits.py` 生成，不在这里维护。**
> 正文引用 exhibit 一律写 `{{ex:slug}}` 占位符，最后一步统一替换成 `Exhibit N`。
> slug 见 manifest；增删一张图只改 manifest，编号自动重排。
>
> ⚠ **每张 exhibit 的数据来自 `series.json`（账本），不是每季重抽。**
> 账本结构与纪律见 `references/ledger.md`。凡 exhibit 上出现过的数，正文一律从账本读。 Where a paragraph is described, update its
numbers and direction each quarter but keep its analytical question fixed.

Every exhibit ends with a small gray note line combining `Note: ...` (data quality,
basis, caveats) and `Source: ...` (providers). Body paragraphs bold their headline
numbers.

## Table of contents

1. Title block
2. Market Size
3. Returns & Relative Value
4. Pricing & Term
5. Credit Fundamentals
6. Sentiment
7. Things We Should Know
8. Fund Update (PAG / Guggenheim / HSBC)
9. Competitor Analysis (+ snapshot JSON schema)
10. Closing disclaimer

---

## 1. Title block

```
JUNSON Capital Research          <- "JUNSON Capital " navy bold 26pt + "Research" blue 26pt
Private Credit Quarterly Report  (2026Q3)   <- navy 20pt + quarter gray 13pt
Coverage: private credit / direct lending / BDC / MM CLO    <right-tab>  13 Aug, 2026
```
Date = report production date. Header on every page:
`JUNSON Capital｜ Private Credit Quarterly<TAB><quarter>`; footer:
`Fundamental Analysis Report — For internal research use only`.

## 2. Market Size

### 2.1 Private credit market size
- Para: global private debt AUM level and channel split — institutional / retail /
  insurance, with $ and % for each; institutional growth since 2015 decomposed into dry
  powder + NAV. Source: PitchBook annual global private debt report (+ xlsx summary).
- **Exhibit 1** — stacked bar: Private debt AUM (US$bn) by channel, 2015–latest.
  Institutional bars = exact PitchBook values (dry powder + NAV); retail/insurance split
  approximated from source chart for earlier years, latest year exact.
- Para: US leveraged credit market size and split (leveraged loans / HY / private
  credit, $ and %), then holders of the private credit stack (BDCs, DL funds, PC CLOs,
  pensions, insurers). Source: PitchBook|LCD via MS tracker.
- **Exhibit 2** — two-panel donut/pie: left by market, right holders of the PC stack.

### 2.2 Supply side
- Para: dry powder level and trajectory; newly added dry powder as % of NAV trend
  (fundraising-driven growth vs deployment); global fundraising $ and fund count vs the
  2021/2022 peaks. Source: PitchBook.
- **Exhibits 3 & 4** (side-by-side) — institutional fund AUM decomposition (NAV + dry
  powder stacked, with dry-powder-as-%-NAV line) | fundraising activity (capital raised
  bars + fund count line).

### 2.3 Demand side
- Para: PC share of LBO financing (LTM count basis) vs peak; direct lending origination
  volumes YTD and y/y (KBRA); refi share; latest quarter volume vs prior quarter (LCD
  deal count and $). Sources: MS tracker/KBRA; LCD wrap.
- **Exhibits 5 & 6** (side-by-side) — DL origination monthly (refi vs non-refi stacked,
  % non-refi line) | LBOs financed BSL vs private markets (count share).
  > ⛔ 这两张的口径不许换。源图在 MS tracker 的 "Deal Activity | Refinancing and New Money…"
  > 那一页:右上 "Direct Lending Origination ($B)"（Refi/Nonrefi 月度堆叠,来源 KBRA）,
  > 右下 "LBOs Financed in BSL vs Private Markets (By Count)"（含 % Private Credit in LTM 线）。
  > 两张都要从图上测,`digitising.md` 的锚点校验照做:
  > Ex 5 用同页披露的 "~$87bn (-24% y/y)" 对总量与同比;
  > Ex 6 用自己测出的笔数反算 LTM 占比,与测出的绿线逐点比(2026Q3 全程差 ≤1.1pp)。
  > ⚠ Ex 5 扫描时必须避开图例色块(2026Q3 版位于 y 500–545),否则图例会被并进相邻柱,
  > 出现一根满格假柱。
  > LCD wrap 的 `01 DL Volume` / `03 LBO Volume` 是季度精确值,**只喂正文**
  > （spec 本节正文要「latest quarter volume vs prior quarter」）,不上这两张图。

### 2.4 Fund flow
- Para: MM CLO new issuance YTD and y/y, full-year context, MM share of total CLO
  issuance; MM CLO AAA spread trend and any basis move vs BSL CLOs. Source: S&P Global
  Ratings / LevFin Insights (via S&P Direct Lending deck).
- **Exhibit 7** — bars annual MM CLO issuance + AAA spread line (rhs), spread annual
  averages approximated from source chart.
  > ⛔ 柱子的最后一根是**本年 YTD**（2026Q3 版是 `26 YTD` = 9.54,至 3 月）。
  > 折线不延到 YTD 那一列 —— 三个月的均值与全年均值不可比。
  > 2026Q3 踩过:YTD 的数在账本 `ytd` 里、正文也引了,但柱子停在 2025,少了一根。

## 3. Returns & Relative Value

### 3.1 Direct lending quarterly return vs. HY
- Para: since-2015 annualised return / vol / Sharpe for PD vs HY, BSL, S&P 500; note the
  smoothing caveat (fair-value based, correlation with BSL); DL T12M return and change
  y/y. Source: Lincoln VOG / PitchBook|LCD / Bloomberg via MS tracker.
- **Exhibit 8** — data table (rows: annualised return, vol, Sharpe, correlation w/BSL,
  T12M return; cols: PD (All), Lower MM, Upper MM, HY, All BSL, Single B BSL, S&P 500).
- Para: stock-basis yields quoted from source text (Lincoln 9.7% / single-B 8.4%, 1.3pp premium,
  as-labelled in tracker p41 left chart; full yield series retired to `series_bank.ms_p41L_yields`),
  then realised T12M returns: mean / stdev / negative-quarter counts for both series, latest gap
  vs ten-year average, HY YTW level, and the fair-value smoothing caveat.
- **Exhibit 9** — line chart quarterly, 4Q15–latest: Lincoln Senior Debt Index and Morningstar
  LSTA US single-B loans **trailing-12-month total returns** (from tracker p41 RIGHT chart
  "Annual Total Returns"), plus **ICE BofA US HY yield-to-worst** (FRED, exact quarter-end
  values, frozen in the ledger) as a dashed overlay. Zero baseline drawn.
  > ⛔ **一张图两个口径，三处都要写清。** 两条贷款线是 T12M **回报**，HY 线是 **YTW 收益率**。
  > Alex 2026-08-24：「yield 跟 annual total return 可以画在一起，但不是说这两个是一个意思」。
  > 题注、图例、Note 都必须分别标注口径；端点 8.7 / 4.8 是回报，7.4 是收益率。
  > ⛔ 横轴全数字 YYYY/MM，**起点 2015/12，写死**（Alex 2026-08-24 最终版：「把14年的数据取消，
  > 从2015年12月开始画。现在写死这个」）。逐年 12 月一个刻度。源图从 4Q14 起，那 4 期不画，
  > 但全量 46 期冻结在 series_bank（回报 + ICE 各一条）—— 不许删、不许重取。
  > 历史沿革：上一版把这张图标成 "yields" 且 2014–15 段画错了（Alex 确认同事本意就是画
  > MS 的回报图）。收益率口径的序列（p41 左图，4Q17 起）已退到 `series_bank.ms_p41L_yields`，
  > 正文只引用其 1Q26 水平；⛔ 回报和收益率两条序列永远不许互填。

### 3.2 Private credit spread premium over BSL
- Para: unitranche new-origination spreads (rolling 90d) latest print vs trough; Single
  B BSL level; the premium in bp and its direction.
- **Exhibits 10 & 11** (side-by-side) — DL new-origination spreads vs Single B BSL
  (bps, monthly lines) | DL new-origination spread by EBITDA cohort (<$25m, $25–50m,
  $50–100m, $100m+).
- Para: cohort convergence/divergence; corroborating LCD survey/observed data.

## 4. Pricing & Term

### 4.1 Spread
- Para: synthesis of §3.2 plus the LCD lender survey (pricing for a reference $50m-EBITDA
  40% LTV unitranche; 6-month-forward expectations).

### 4.2 Covenant structure & PIK %
- Para: cov-lite share by vintage in upper MM vs lower MM; share of new deals with PIK
  toggle by segment. Source: LCD/MS.
- **Exhibits 12 & 13** (side-by-side) — % of deals with ≥1 financial covenant across
  vintages by segment | % with PIK toggle across vintages by segment.

## 5. Credit Fundamentals

### 5.1 Default rate
- Para: S&P credit-estimate TTM default rate incl. selective defaults (level, direction);
  conventional ex-SD trend.
- **Exhibits 14 & 15** (side-by-side) — S&P credit-estimate default rates vs US
  spec-grade | S&P T12M DL vs BSL default rate comparison.
- Para: the five-provider disagreement (direction by provider this quarter).
- **Exhibit 16** — provider comparison table: Fitch / S&P / KBRA DLD / Lincoln /
  Proskauer; columns: sample/scope, definition/methodology, prior Q, current Q, trend
  arrow, cohort. Update the two quarter columns and arrows each quarter.
- **Exhibits 17 & 18** (side-by-side) — Fitch TTM PC default rate time series | KBRA DLD
  issuer TTM default rate DL vs BSL.
- Para + **Exhibit 19** — sector split (Fitch LTM default rate by sector bar chart);
  software vs asset-class total callout; MS's forward default-mix view.

### 5.2 Recovery rate
- Para: BDC-mark implied recoveries — pre-default marks vs at-default (DL vs syndicated;
  PIK vs non-PIK); sector averages (first-lien sample), software vs best sector.
- **Exhibits 20 & 21** (side-by-side) — implied recovery path (1yr/6m/3m pre-default →
  at default) | implied recovery by sector bars.

### 5.3 Leverage ratio (debt/EBITDA)
- Para: cross-market gross leverage (HY vs BSL vs DL with rating-band framing); time
  series direction (Fitch private MM, Lincoln, public Single B).
- **Exhibits 22 & 23** (side-by-side) — Exhibit 22 is the rating-band positioning
  graphic (band chart: AAA-BBB / BB / B / CCC with diamond markers for HY, Syndicated,
  DL); Exhibit 23 total leverage time series.

### 5.4 Interest coverage ratio
- Para: cross-market ICR positioning (mirror image of leverage); q/q direction and driver
  (base rates).
- **Exhibits 24 & 25** (side-by-side) — ICR positioning band chart | EBITDA coverage
  quarterly series.

### 5.5 BDC non-accrual rate
- Para: average BDC nonaccruals at cost (level, is it a high?); share of BDCs >8%;
  public vs private split and the vintage caveat.
- **Exhibits 26 & 27** (side-by-side) — average nonaccruals + share >8% | public vs
  private BDC nonaccruals.

### 5.6 PIK income % of total income
- Para: average BDC PIK % of investment income; share above 12% threshold; public vs
  private trend; sub-90 PIK sector concentration (leading indicator of "bad PIK").
- **Exhibits 28 & 29** (side-by-side) — average PIK % + >12% share | public vs private
  average PIK.

Primary source for §5.5–5.6 and much of §5: the MS Private Credit Tracker; S&P Direct
Lending deck for S&P measures; Fitch/KBRA numbers usually via the tracker or web.

## 6. Sentiment

### 6.1 Broker summary
- **Exhibit 30** — table, one column per broker report received this quarter (e.g. MS,
  JPM, GS, Barclays, UBS). Rows: **View** (one-line stance, e.g. "Cautious-to-neutral:
  pressures contained, not resolved"), **Key points** (3–6 bullet lines with the
  report's key numbers), **QoQ change** (how the house's view moved vs last quarter —
  new coverage, tone shift, forecast changes). Column headers include report short-name
  and date. Source line lists all brokers + "Junson AID summary".

### 6.2 Related news
- 4–6 bullet paragraphs, each: **bold lead-in phrase** + colon + dense factual summary
  with numbers, ending with why it matters. Drawn from folder reports AND web research.
  Recurring themes to check every quarter: non-traded BDC/interval-fund redemptions and
  gates; the quarter's marquee default/restructuring; landmark financings that expand
  the asset class; secondaries volume and valuation transparency; volume/sector rotation.

## 7. Things We Should Know

Intro line ("Five observations we consider important after reading all of this
quarter's uploaded materials — points not covered by the framework sections above and
directly relevant to the Junson portfolio:") then exactly **five** bold-led bullets.
Each: a thesis sentence in bold-ish lead, evidence with numbers, and an explicit
implication/action for Junson (evaluate holdings at name level, request vintage splits,
cross-check marks vs secondary prints, etc.). One bullet may carry its own exhibit
(2026Q3 used Exhibit 31, BDC maturity wall QoQ with a side-comment panel as a 1×2
table). These must be fresh insights each quarter, not restatements of §2–6.

## 8. Fund Update

Intro para: which reports (each manager's latest investor report), valuation as-of date,
and the marks-lag caveat.

For **each** of the three holdings — PAG BRS Fund III (SRT strategy), Guggenheim
Private Debt Fund IV (US direct lending), HSBC RCF Partnership Fund (RCF strategy) —
four fixed blocks:

1. **Fund snapshot** —— ⛔ 必须**印出这个段名**（三级小标题，`H.minorheading`，10pt 深藏蓝）。
   ⛔ **两张表横向并排**，外层是无框线 1 行 2 列的排版表（`H.table_pair`）：

   | | 左格 表 A | 右格 表 B |
   |---|---|---|
   | 表头行 | **没有**（纯 label \| value） | `Metric \| <pq> \| <cq> \| QoQ Δ`，深蓝底 |
   | 最左列 | 六行固定（见下），三只基金逐字相同 | KPI 行名，各基金按自己披露的口径 |
   | 列宽 | `[3.4, 4.9]` 冻结 | `[3.5, 1.6, 1.6, 1.6]` 冻结 |
   | 合计 | 8.3cm | 8.3cm（两张同宽，并排占满正文 17.12cm） |

   两张表都**不进 exhibit 编号**（不在 `exhibit_manifest.json` 里）。
   由 `build_doc.fund_snapshot(fkey)` 一个函数出，三只基金共用 —— 结构不可能只对一只。

   > ⛔ 2026-08-26 踩过两次：第一次整段没渲染；第二次渲染了但**两张表上下摞着放**、
   > 还给左表加了个 `Metric | Value` 的深蓝表头。Alex 两次都一眼看出来
   > （「是两个分开的的横向排放的表，表头和最左侧边的栏必须一样。除了季度。我跟你说过啊」）。
   > 现在 `pc_docxcheck` 有一条**查纸面结构**：Fund snapshot 段后紧跟的表必须是外层 1×2、
   > 左右格各嵌一张表，三只都对上才放行；`pc_hdrcheck` 查左表不许有 `header`、
   > 两张表都必须有冻结列宽。
2. 紧接在 Fund snapshot 段内的两条 bullet：**Quarter activity**（本季成交/退出/签署，
   带金额与定价）与 **Manager commentary**（管理人市场观点压到 2–3 行）。
   两条都从账本的 `quarter_activity` / `manager_commentary` 读，缺了直接抛错。
3. **Portfolio composition** —— ⛔ 同样必须印出段名。para with the book's aggregate stats, then side-by-side
   composition charts (PAG: portfolio type / geography / currency / bank counterparty,
   Exhibits 32–35; Guggenheim: GICS sub-industry mix / sponsored split, Exhibits 39–40;
   HSBC: sector mix / margin by project, Exhibits 43–44), then a **composition QoQ
   table** (Exhibits 36 / 41 / 45): current Q vs prior Q shares with QoQ Δ column —
   this requires holding both quarters' reports or last quarter's table.
4. **Fund level performance detail** —— ⛔ 同样必须印出段名。para (IRR/MOIC/TVPI/DPI vs prior quarter and vs
   expectations; realised deals; watchlist/non-accruals), then:
   - PAG: **Exhibit 37** KPI table Q vs prior Q (gross/net IRR, gross/net MOIC,
     contributions, distributions, DPI, NAV, etc.); **Exhibit 38** top-10 positions
     table (investment, date, type, ccy, spread, amount, total value, UW IRR, expected
     IRR) condensed from the full schedule with totals in the note.
   - Guggenheim: **Exhibit 42** quarter's closed transactions table (deal, structure,
     pricing, net leverage, LTV, differentiator). Note: fund does not disclose
     fund-level IRR/NAV — say so; use asset-level performance status (x of y
     Performing, monitor list names).
   - HSBC: **Exhibit 46** current portfolio table (project, sector, country, margin,
     committed, drawn, maturity, est. ROIC, watchlist RAG).

## 9. Competitor Analysis

Quarterly peer tracker vs vintage-matched cohorts from the PitchBook screen
(`Competitor/PitchBook_Search_Result_Columns_*.xlsx`, North America direct lending
drawdown funds；2026Q3 导出为 **331 只基金** —— report-spec 早前写的 333 是数表格行数（表头后 333 行 = 331 只基金 + 1 空行 + 1 行 PitchBook 版权声明），下季不要去凑 333). Intro para states cohort basis and points to the
Appendix for conventions.

### 9.1 Positioning scorecard — **Exhibit 47**
Table: per fund (PAG 2023v fund-level; Guggenheim 2024v † investor-level; HSBC 2024v *
ramp-up distorted) × metric (Net IRR, TVPI, DPI): current value, QoQ Δ, cohort median,
cohort Δ, percentile, percentile Δ, and a one-word "Read" (Top quartile / Below median
/ 2nd quartile...). Percentile = share of cohort funds strictly below the fund's value.
Note gives cohort sizes per metric. Follow with an interpretation para for any
odd-looking readings (profile artefacts, basis differences).

### 9.2 Named comparator table — **Exhibit 48**
Junson's three funds + named flagship funds (upper MM: KKR / Ares / Apollo;
core MM: TPG Twin Brook / Golub / HarbourVest / Oaktree) from the same screen:
vintage, size, net IRR, TVPI, DPI, called %, dry powder %, PB quartile.

> **选取规则（Alex 2026-08-21 定，覆盖原来的「latest」）：取该管理人旗舰 direct lending
> 系列的最新一只**，不是单纯 vintage 最新。单纯按 vintage 取会拿到 side-car 和小体量专户：
> Ares 会取到 Emerald（2023、$370m、IRR 27.3%）而不是旗舰 Senior Direct Lending Fund II
> （2021、$8.0bn、IRR 13%）。系列用**基金名**正则锁定，不要用 Investor 字段 ——
> PitchBook 的 Investor 写法每季会变（Twin Brook 有时写成 "TPG Angelo Gordon"）。
> 当季用的正则存在 `series.json` 的 `meta.comparator_set.series_patterns`，每季核一遍。
> 取到的基金若 called% < 25%，打 `*` 标记（还在建仓，IRR/TVPI 没意义）——
> 2026Q3 的 Twin Brook Fund VI 就是这种情况（called 5%、IRR −4.4%）。

> ⚠⚠ **口径披露（必写）：我们自己的三只基金不在这个筛选池里。** 筛选限定
> Fund Location = Americas › North America；PAG BRS III（香港）、HSBC RCF（卢森堡 RAIF）、
> Guggenheim PDF IV 在 2026Q3 那份 331 只的导出表里**命中数 0/0/0**。
> 所以 §9 的分位数是「相对一个外部北美基准的位置」，不是「同组内排名」，
> 且 PAG 主亚洲、HSBC 主欧洲，存在地域错配。§9 开头段与附录方法论段都要显式写出来。
> Ex 55（管理人一致性气泡图）因此**无法叠加 Junson 自己的基金**，图注要说明原因，
> 不许留白让人以为漏画了。
> （备选方案是把筛选扩成全球，Alex 2026-08-21 选择不改口径、只做披露 ——
> 理由是保住与上一版报告的可比性。若日后改口径，全部分位与轨迹都要重建。）

### 9.3 Relative momentum — **Exhibits 49 & 50** (side-by-side)
From the second tracked quarter on: each fund's QoQ ΔIRR/ΔTVPI vs its cohort median's
QoQ change (beat/lag scatter or paired bars). Baseline quarter: record levels instead.

### 9.4 Percentile trajectory — **Exhibits 51 & 52** (side-by-side)
IRR percentile and TVPI percentile per fund, one point added per quarter; flag any fund
drifting down through P75/P50.

### 9.5 Cohort health monitor — **Exhibit 53**
IQR width by vintage (IRR in pp, TVPI in x); commentary on dispersion as the early
signal of industry stress reaching fund marks.

### 9.6 Appendix (annual refresh) — **Exhibits 54–58**
Peer universe by vintage (agg size + count); manager consistency bubble chart (avg PB
quartile vs median net IRR, ≥4 ranked funds, Junson funds highlighted); net IRR /
TVPI / called-% by vintage with median + IQR bands and Junson funds overlaid; then the
**Methodology** paragraph: screen definition and export date, Junson vintage convention
(year of first investment: PAG=2023, Guggenheim=2024, HSBC=2024), percentile
definition, quarterly re-export + diff process, metric-basis markers († investor-level,
* ramp-up distorted). Refresh this appendix annually or on material change only.

### Competitor 的快照已并入总账本

> ⚠ **早前独立的 `CA_snapshot_<quarter>.json` 已并入 `series.json`。**
> `meta.cohorts` 存 cohort 统计；`meta.screen` 存筛选口径与样本数；
> `meta.comparator_set` 存点名对标组；`exhibits.ca_traj_*.history` 存分位轨迹（只追加）。
> 这样全部 58 个 exhibit 共用一本账，不用维护两套。schema 见 `references/ledger.md`。
>
> 下面这份旧 schema 保留作对照 —— 字段名与含义未变，只是搬进了 `series.json`:

```json
{
  "quarter": "2026Q3",
  "screen_export_date": "2026-08-13",
  "universe_fund_count": 331,          // 2026Q3 实际筛出的基金数。早前这里写 333 是把表格行数当了基金数（表头后 333 行 = 331 只 + 1 空行 + 1 行版权声明）——每季都要从原始导出重数，不要沿用
  "funds": {
    "PAG_BRS_III":  {"vintage": 2023, "basis": "fund-level",
                      "net_irr": 0.147, "tvpi": 1.11, "dpi": 0.30,
                      "pct_irr": 92, "pct_tvpi": 28, "pct_dpi": 72},
    "Guggenheim_PDF_IV": {"vintage": 2024, "basis": "investor-level",
                      "net_irr": 0.093, "tvpi": 1.20, "dpi": 0.18,
                      "pct_irr": 18, "pct_tvpi": null, "pct_dpi": null},
    "HSBC_RCF":     {"vintage": 2024, "basis": "fund-level-rampup",
                      "net_irr": 0.345, "tvpi": 1.21, "dpi": 0.14,
                      "pct_irr": null, "pct_tvpi": null, "pct_dpi": null}
  },
  "cohorts": {
    "2023": {"n_irr": 26, "n_tvpi": 25, "n_dpi": 25,
              "median_irr": 0.107, "median_tvpi": 1.15, "median_dpi": 0.15,
              "iqr_irr_pp": 4.6, "iqr_tvpi": 0.13},
    "2024": {"n_irr": 11, "n_tvpi": 8, "n_dpi": 8,
              "median_irr": null, "median_tvpi": null, "median_dpi": null,
              "iqr_irr_pp": null, "iqr_tvpi": 0.04}
  },
  "percentile_history": {
    "PAG_BRS_III": [{"quarter": "2026Q3", "pct_irr": 92, "pct_tvpi": 28}]
  }
}
```

(Values above are the 2026Q3 baseline where known; carry `percentile_history` forward by
appending, so trajectory charts can be rebuilt from the latest snapshot alone. Fill
nulls as they become computed.)

## 10. Closing disclaimer

Final gray small-print paragraph: internal use only; digitised-approximation caveat
("Except where marked as exact / as-labelled / as-disclosed values, intermediate points
of time series in redrawn charts are digitised approximations from the source charts,
shown for trend only; please refer to the original reports when citing."); name the
archived snapshot file for next quarter's delta computation.

---

## §8 Fund Update —— 结构与表头写死（Alex 2026-08-25）

> 原话:「Fund Update 其中有三个 fund,每个 fund 下面的结构都要是一样的,要包含
> Fund snapshot、Portfolio composition、Fund level performance detail。」

### 小节标题带策略标签

同事那版每只基金的小节标题是 `<Fund name> (<strategy>)`,我们保留自己的 8.x 编号再接上标签:

| 我们印的 |
|---|
| `8.1  PAG BRS Fund III (SRT strategy)` |
| `8.2  Guggenheim Private Debt Fund IV (US direct lending)` |
| `8.3  HSBC RCF Partnership Fund (RCF strategy)` |

三个段名是 10pt 加粗深藏蓝（`H.minorheading`）,与 12.5pt 的小节标题、9.5pt 的正文分三档。

> ⛔ 2026-08-26 踩过:账本里三只基金的 snapshot 数据齐全、`pc_hdrcheck` 也全过,
> **但 build_doc 从来没渲染过这一段**,三个段名一个都没印在纸上,Alex 一眼看出来
> （「Portfolio composition 也没了,Fund level performance detail 也没有」）。
> 账本级检查看不到纸面 —— 所以 `pc_docxcheck` 现在有一条**逐只基金查这三个段名与段序**,
> 缺一个就不许交稿。

### 8.x 每只基金一律三段,顺序不变

```
8.x  <Fund name>
     Fund snapshot                       ← 两张表 + 两条 bullet
       表 A：静态事实（六行，见下）
       表 B：Metric | <pq> | <cq> | QoQ Δ
       · Quarter activity:  …
       · Manager commentary: …
     Portfolio composition               ← 组合构成的图 + 一张 QoQ 表
     Fund level performance detail       ← 业绩/持仓明细表
```

⛔ 三只基金（PAG BRS III / Guggenheim PDF IV / HSBC RCF）**段名、段序、表结构完全一致**,
不许因为某只基金披露得少就少一段;缺料就在该段写 not disclosed,段不许省。

### Fund snapshot 表 A —— **三只基金各一套行名**

> ⛔ Alex 2026-08-26:「Guggenheim Private Debt Fund IV (US direct lending) 的 Fund snapshot
> 的左边的表格的最左侧一列还是不对,你对照一下同事的,然后固定。以及 HSBC RCF Partnership
> Fund (RCF strategy) 的的 Fund snapshot 的左边的表格的最左侧一列还是不对,你对照一下同事的,
> 然后固定。」
>
> ⚠ **这条推翻了 2026-08-25 的「三只统一成 PAG 那六行」**。当时统一成一套,结果 GUG / HSBC
> 纸上印的是 PAG 的行名 —— 而 `pc_hdrcheck` 里 `SNAP_ROWS` 也写死成同一套,所以全绿而全错。
> 现在改成各读自己的 `row_labels_fixed.expected`,三套如下:

| PAG BRS III (6) | Guggenheim PDF IV (5) | HSBC RCF (6) |
|---|---|---|
| `Strategy` | `Strategy` | `Strategy` |
| `Total commitments` | `Inception` | `Initial close` |
| `Final close` | `Final close` | `Final close` |
| `Investment period ends` | `Initial target` | `Term` |
| `Initial term ends` | `Performance basis` | `Base currency` |
| `Status` | — | `Watchlist` |

行名只能改账本,不许改代码里的字面量。某一行的**值**拿不到就写 `not disclosed`,⛔ 行不许删,
也不许拿同事那版的数顶上（铁律四）。换行名的时候旧行的值不许丢 —— 存进
`_rows_off_table` 并在 `_rows_off_table_why` 里逐行写清它去哪了。

**三道检查**（表A 没有深蓝表头行,所以按表头配对的那条检查看不到它,必须单独查）:

| 查什么 | 谁查 |
|---|---|
| 账本的行名与冻结清单 | `pc_hdrcheck.py`（各基金各一套） |
| `build_doc` 拼出来的行序 | `build_doc.fund_snapshot()` 里的 `_fixcol()` |
| 纸上左表的第一列 | `pc_docxcheck.py`（按 Fund snapshot 段序取外层 1×2 的左格） |

### Fund snapshot 表 B —— 表头固定,只有季度跟着走

```
Metric | <periods[0]> | <periods[1]> | QoQ Δ
```

⛔ 除了两个季度标签,其余列名一个字都不许变。季度从该 exhibit 自己的 `periods` 读。

### 表 B 下面固定两条 bullet

```
· Quarter activity:  <本季发生了什么 —— 交易、退出、募资、facility 变动>
· Manager commentary: <管理人自己的话 —— 市场环境、策略调整>
```

⛔ 两条都要有,顺序不变。没内容就写 none this quarter,不许省掉 bullet。

### 图形形态固定（不由数据启发式决定）

| Exhibit | 形态 | 账本字段 |
|---|---|---|
| E32 `fund_pag_comp_type` | **饼图** | `chart_form: pie` |
| E33 `fund_pag_comp_geo` | **饼图** | `chart_form: pie` |
| E35 `fund_pag_comp_bank` | **竖版柱** | `chart_form: vbars` |
| E43 `fund_hsbc_sector` | **饼图** | `chart_form: pie` |
| E44 `fund_hsbc_margin` | **竖版柱**（参考线改水平虚线） | `chart_form: vbars` |

⛔ `shares()` 原来按 `DONUT_MAX=5` / `DONUT_MIN_SLICE=8` 自动决定饼图还是横柱,
切片一多一小就悄悄退化成横柱。现在 **`chart_form` 优先**,框架说饼图就是饼图。

饼图版式:图例靠左、饼靠右（半径 0.72、圆心右移）。**切片颜色一律 `js.series_ext(n)`** ——
前 6 个是 Alex 那六色原色,第 7–12 个是同一批色**混白 52%**,第 13–18 个混白 76%
（Alex 2026-08-25 批准「用六色的淡化版」）。⛔ 只许沿这六色向白混,不许引入新色相;
混合比例写死,同一个位次跨季永远同色。⛔ 也不许 `SERIES[i % 6]` 循环（第 7 片会与第 1 片同色,
实测撞过）;超过 18 片 `series_ext()` 直接报错 —— 那种切片数本来就不该用饼图。

### 表头逐张写死（跟同事的报告一致）

季度标签用 `<pq>` / `<cq>` 占位,其余**一个字都不许变**。

| Exhibit | 表头（第一行） |
|---|---|
| E36 `fund_pag_comp_qoq` | `By portfolio type \| <pq> \| <cq> \| QoQ Δ \| By currency \| <pq> \| <cq> \| QoQ Δ` |
| E37 `fund_pag_kpi_qoq` | `Metric \| <cq> \| <pq>`　⚠ 本季在前、上季在后（同事那版就是 Q1 2026 \| Q4 2025） |
| E38 `fund_pag_top10` | `Investment \| Date \| Portfolio type \| CCY \| Spread \| Amount ($m) \| Total value ($m) \| UW IRR \| Expected IRR` |
| E41 `fund_gug_comp_qoq` | `GICS sub-industry (top) \| <pq>* \| <cq> \| QoQ Δ* \| Sponsored (% of NAV) \| <pq> \| <cq> \| QoQ Δ` |
| E42 `fund_gug_closed_deals` | `Deal \| Structure \| Pricing \| Net leverage \| LTV \| Differentiator` |
| E45 `fund_hsbc_comp_qoq` | `Sector \| <pq> \| <cq> \| QoQ Δ \| Sector \| <pq> \| <cq> \| QoQ Δ` |
| E46 `fund_hsbc_portfolio` | `Project \| Sector \| Country \| Margin \| Committed (€m) \| Drawn (€m) \| Maturity \| Est. ROIC \| Watchlist` |
| E47 `ca_scorecard` | `Fund / basis \| Metric \| <rq> \| QoQ Δ \| Cohort median \| Cohort Δ \| Percentile \| Pct Δ \| Read`　⚠ 第三列是**基准季标签**，跟 `meta.rq` 走；三个 Δ 列在基线季全是 n/a |
| E48 `ca_named_comparators` | `Fund \| Vintage \| Size ($m) \| Net IRR \| TVPI \| DPI \| Called % \| Dry powder % \| PB quartile`　＋两行灰底分组标题，见下 |

**左侧首列（行标）也固定**:E36 首列是组合类型名、E37 是指标名、E38 是项目名、
E41 是 GICS 子行业名、E45 是行业名、E46 是项目名 —— 行的**集合**每季会变（新增/退出),
但**列名与列序不许变**。

> ⛔ Alex 2026-08-26:「E46 还没改？同事的 E46 里有 base 这一列？**表头顺序都给我定死,
> 以及最左边的这一列**」「Exhibit 38 还不改」「Exhibit 41 也是」

行标落在各 exhibit 的 `row_labels_fixed`:
`expected` = 纸上最左那一列逐格的字面量;双栏表另有 `left` / `right` 行规格与 `right_col`。
本季冻结了最左列的九张表:E36 E38 E41 E42 E46 E48 + 三只基金的 snapshot 表 B。

**E41 是八列双栏,不是四列摘要。** 左栏 GICS 子行业(含 `Software (Sys + App)` 合并行
+ 两条缩进分项 `– Systems Software` / `– Application Software`),右栏 sponsored 拆分。
两栏的值都从饼图条目(`src_left` / `src_right` 指的 slug)的 `vals` / `vals_pq` 现算,
⛔ 不许在 `build_doc` 里写字面量。上季没有这一片(本季新增的子行业)那一格印 `—`,
QoQ 印 `new` —— ⛔ **不许当 0% 去做差**;先确认源图会不会印 0% 的切片,会印才能这么判。
E41 的 account overview 那组数(投资笔数/投放额/杠杆/LTV)仍在账本 `rows` 里,
**只喂 §8.2 正文**,两套数据都留着,谁也不许删。

四道检查各查一段,缺一段就会出现「账本绿、纸上错」:

| 查什么 | 谁查 |
|---|---|
| 账本里的表头字面量 + 冻结列宽够不够宽 | `pc_hdrcheck.py` |
| `build_doc` 自己拼出来的行序 | `build_doc._fixcol()`,对不上直接终止出稿 |
| 纸上的表头 | `pc_docxcheck.py`(冻结表头逐字出现) |
| 纸上的最左列 | `pc_docxcheck.py`(逐格对 `row_labels_fixed`) |

### E45 的 QoQ 必须写出是哪个项目

> ⛔ Alex 2026-08-25:「Exhibit 45 的 QoQ 必须包含投了哪个项目,如果投了的话。」

本季净增/净减的那一格写成 **`+1 (项目名)`** / **`-1 (项目名)`**;一格多笔就并列 `+2 (A, B)`;
没有变动写 `–`。⛔ **不许编项目名** —— 名字要能在 `fund_hsbc_portfolio` 的 rows 里找到。

判定新增的做法:本季持仓表 vs 上季投资人报告正文列的持仓名单,取差集。
2026Q3 实例:Healthcare→Tooth、Life sciences→Oliver、Logistics→Box
(1Q26 共 11 笔 vs 4Q25 正文列的 8 笔 —— Emerald、Connect、Media、Alpha、Pique、Ink、Service、Freeze)。

`pc_hdrcheck.py` 会查:`delta` 不是 `–` 的行,括号里必须有项目名。

### Fund snapshot 表 A —— 本季实际取到什么（各基金各一套行名）

| PAG BRS III | 值 |
|---|---|
| Strategy | SRT，senior secured |
| Total commitments | US$952m |
| Final close | 28 Jan 2025 |
| Investment period ends | 28 Dec 2026 |
| Initial term ends | 28 Dec 2029 (+1+1) |
| Status | Investing，2026 年底前投满 |

| Guggenheim PDF IV | 值 |
|---|---|
| Strategy | US MM direct lending，1L / unitranche ⚠归纳 |
| Inception | 30 May 2024（p5 "Inception Date 5.30.2024"） |
| Final close | 31 Mar 2026（p1 "held its final close on March 31, 2026"） |
| Initial target | US$3.0bn（closed on US$4.5bn — hard cap）⚠ 两个数都印，免得丢了原来 Total commitments 那行 |
| Performance basis | Aggregate of three vehicles (Guardian (U), IV-A, IV-B); no fund-level return metrics disclosed |

| HSBC RCF | 值 |
|---|---|
| Strategy | RCF，sponsor-backed LBO，EBITDA>US$20m |
| Initial close | Q4 2023（p4 "Fund Key Data"） |
| Final close | **not disclosed** —— p4 反而写着季后又签 EUR 100m，募集仍在进行 |
| Term | 9 + 1 + 1 years from initial close（p4 明标 "9 +1 +1 years"） |
| Base currency | EUR (reporting currency) ⚠ 源文件**没有** "base currency" 这一项；p4 每个基金层数字都是 EUR 计价，故格里写明是 reporting currency，不冒充明标项 |
| Watchlist | None — no assets on the watchlist（p4 "There are no assets on the Watchlist."）⛔ 源文件不给 RAG 颜色，不许写 Green |

⛔ `not disclosed` 的四格是**报告里真的没有**，逐格在 `_src` 里写了检索结论（例：Guggenheim 两份
报告全文检索 "investment period" 无命中）。**不许推算、不许拿同事那版顶上** —— 两处踩过：
同事写 HSBC final close = 30 Jun 2026（本季文件夹追不到出处，不采用）、
写 HSBC fund term = 8 years（本季报告明标是 **9** +1+1，不采用他的 8）。

### E47 `ca_scorecard` —— 换季两个必做动作

**1. 表头第三列跟着 `meta.rq` 变。**
账本里存的是 `header_template = ['Fund / basis','Metric','<rq>','QoQ Δ','Cohort median',
'Cohort Δ','Percentile','Pct Δ','Read']`;`header` 只是本季解析后的快照。
`build_doc` 必须 `[c.replace('<rq>', RQ) for c in header_template]` 现算。
⛔ 读快照 = 下季印出旧季度。`pc_hdrcheck` 把两者对比当哨兵。

**2. 三个 Δ 列下季必须填上。**
本季（首季）全 n/a 是因为没有上季。`history[<季>]` 已存九行:

```
history["2026Q3"]["PAG BRS Fund III — Net IRR"] = {
    value: "14.7%", value_num: 14.7,
    cohort_median: 10.745, cohort_n: 26, percentile: 92.0,
    basis: "fund-level", marker: null }
```

下季做差（三列各有自己的分母）:

| 列 | 算法 |
|---|---|
| `QoQ Δ` | 本季 `value_num` − `history[上季][key].value_num` |
| `Cohort Δ` | 本季 `cohort_median` − `history[上季][key].cohort_median` |
| `Pct Δ` | 本季 `percentile` − `history[上季][key].percentile`（写成 `+6pp` / `-3pp`） |

`key = "<fund> — <metric>"`（em dash）。⛔ 上季值只能从 `history` 取,不许翻上一季成稿。
⛔ 下季不许再是 n/a;只有 `history` 查不到上季那一条才允许，并注明原因。
⚠ `cohort_median` / `percentile` 每季用**当季 PitchBook 导出重算**（池子会变），
`history` 只用来做差 —— 不许拿旧值当本季值。

### E48 `ca_named_comparators` —— 左侧结构与灰底分组行

> ⛔ Alex 2026-08-25:「表的左侧的表头必须也是一样，要加上 Core-to-upper MM 和
> Low-to-core MM，背景是灰色的。」

```
Fund | Vintage | Size ($m) | Net IRR | TVPI | DPI | Called % | Dry powder % | PB quartile   ← 深蓝表头
Junson — PAG BRS Fund III            …                                    ┐
Junson — Guggenheim PDF IV           …                                    │ 自家三只，无分组标题
Junson — HSBC RCF Partnership Fund * …                                    ┘
Core-to-upper MM                                          ← 灰底 E8E8E8，首格加粗横跨整行
KKR / Ares / Apollo                  …
Low-to-core MM                                            ← 灰底 E8E8E8
TPG Twin Brook / Golub / HarbourVest / Oaktree             …
```

- 分组行底色 `E8E8E8`，首格加粗并 `merge` 横跨整行，其余格留空
- 数据行隔行浅底 `F2F5F9`
- 机制:`docx_helpers.data_table(group_rows=[...], zebra='F2F5F9')`
- ⛔ 分组名从账本 `tier_labels`（`{tier: 标题}`，`None` = 不画标题）读，
  **不在 `build_doc` 里写死** —— 下季基金集合会变，tier 名不会
- ⛔ 原来只有八列（缺 `Dry powder %`）且没有分组行，已补齐


## E55 `ca_apx_mgr_consistency` —— 古根海姆下季**必须**入点

> ⛔ Alex 2026-08-26:「E55 古根海姆先不入点,但下季度生成新报告的时候 你问了用户
> 古根海姆的数据之后,是一定要入点的,如果用户漏输入了,那你要提醒用户。」

- **2026Q3**:不入点（当季拍板,已执行）。清单槽上写 `_deferred_in: ["2026Q3"]`。
- **2026Q4 起**:问到 IRR 之后**一定要入点**;用户漏输入要**主动提醒**,
  ⛔ 不许因为「上季没入」就继续不入。`pc_gugcheck` 一过那一季就把这个槽从
  「故意不填」翻成**硬失败**,并把要问用户的话打出来。
- x 轴的等效四分位跟 PAG / HSBC 同一算法:由该基金 IRR 在当季 cohort 里的分位反推
  （PAG 分位 92、HSBC 100 都落第一四分位,故 x=1.0）。这是 Junson calculation,
  不是 PitchBook 给的四分位 —— 三只都一样,`overlay_note` 里写明。
- 拿不到 IRR:留空 + 在 `overlay_missing` 写 gap 说明,⛔ 绝不拿上季的值顶上。

⚠ 顺带纠正:`overlay_missing` 原来写的理由是「Guggenheim 不在 PitchBook 排名样本里,
内部计算给不出平均四分位」—— 那条**不自洽**,PAG 和 HSBC 也都不在那 331 只池子里。
缺席的真实原因只有一个:Alex 本季决定先不入。旧文本留在 `_overlay_missing_prev_20260826`。

## 正文交叉引用写节名,不写节号

> ⛔ Alex 2026-08-26:「那你就改成写节名」

标题的「几点几」去掉之后,正文再写 `Section 5.1` 读者在纸上找不到。所以 24 处交叉引用
一律改成写标题原文（读者能直接 Ctrl-F）。节名的唯一真值是 `build_doc` 里的 `SEC` 字典,
正文用 `xr('5.1')` 取;`sec()` / `sub()` 反过来核对 —— 改了标题忘了改 `SEC`,
出稿直接终止。`pc_docxcheck` 另有一条查纸面:正文出现 `Section <数字>` 就 ✗。
§8 三只基金那三个小节名走账本的 `fund_name`,不进 `SEC`。

## 记住的同事版式（运行时不许打开同事那份 docx）

⛔ Alex 2026-08-26：「我所有说按同事的报告格式的，都是要你**记住格式**，而不是每次运行的
时候去看同事的报告。」理由很实在 —— 后续季度 `assets/colleague-template-*.docx` 可能根本
不在手边。所以下面每一条都已经抄成**字面量**落在账本里，运行时只读账本。

机器可读的同一份清单在账本顶层 `_frozen_colleague_formats.items`；`pc_hdrcheck` 会逐条查
承载字段是否还在（空了就 fail 并打印 Alex 的原话），表头另外逐字比对模板。
**要改先改账本，不许改代码里的字面量。**

| # | slug | 承载字段 | Alex 的原话 |
|---|---|---|---|
| Ex 16 | `cf_provider_compare_table` | `header_template` / `header` | E16 这个表:每一个列名都是固定的,除了倒数第二和倒数第三列的季度,要根据报告来 |
| Ex 19 | `cf_fitch_default_by_sector` | `emphasis` | E19 的图也需要改,Total 是深蓝色,software 是亮蓝色,其他是比深蓝色稍浅的色 |
| Ex 21 | `cf_recovery_by_sector` | `chart_form` | Exhibit 21 的图要竖着,像同事报告里的 E21 一样 |
| Ex 32 | `fund_pag_comp_type` | `chart_form` | E32 和 E33 都必须是饼图 |
| Ex 33 | `fund_pag_comp_geo` | `chart_form` | E32 和 E33 都必须是饼图 |
| Ex 35 | `fund_pag_comp_bank` | `chart_form` | E35 的柱状图必须竖着 |
| Ex 36 | `fund_pag_comp_qoq` | `header` | Exhibit 36 和 37 和 38 的表格的左侧和顶部的表头也必须是一样的(跟同事的报告) |
| Ex 37 | `fund_pag_kpi_qoq` | `header` | 同上 —— ⚠ E37 是本季在前、上季在后(Metric | <cq> | <pq>),同事那版就是这样 |
| Ex 38 | `fund_pag_top10` | `header` `row_labels_fixed` `col_widths_cm` | Exhibit 38 还不改 —— 九列(末两列 UW IRR / Expected IRR)+ 最左那十个项目名,都写死 |
| Ex 41 | `fund_gug_comp_qoq` | `header` `row_labels_fixed` `col_widths_cm` | Exhibit 41 也是 表格的表头和最左侧一列 要跟同事的一模一样,直接写死 —— 八列双栏 |
| Ex 42 | `fund_gug_closed_deals` | `header` | 同上(E42) |
| Ex 43 | `fund_hsbc_sector` | `chart_form` | E43 必须是饼图 |
| Ex 44 | `fund_hsbc_margin` | `chart_form` | E44 的条形图必须竖着 |
| Ex 45 | `fund_hsbc_comp_qoq` | `header` | E46 和 E47 的表头也必须跟同事 report 的格式一样;另 E45 的 QoQ 必须包含投了哪个项目 |
| Ex 46 | `fund_hsbc_portfolio` | `header` `row_labels_fixed` `col_widths_cm` | E46 还没改？同事的 E46 里有 base 这一列？表头顺序都给我定死,以及最左边的这一列 —— ⛔ 没有 Base 列,base rate 并进 Margin 一格 |
| Ex 47 | `ca_scorecard` | `header_template` | E47 这个 2026Q3 表头你下一季度应该要修改 —— 是变动的 |
| Ex 48 | `ca_named_comparators` | `header` / `row_labels_fixed` / `tier_labels` / `col_widths_cm` | E48 这个表头也是固定的,表的左侧的表头必须也是一样,要加上 Core-to-upper MM 和 Low-to-core MM,背景是灰色的;最左侧那一 |
| Ex 57 | `ca_apx_tvpi_by_vintage` | `ylim` / `ytick` | 图 57 的 y 轴也按同事报告来,必须一样,你改成那个数,然后把数写死 |
| §8 | `fund_pag_snapshot` | `row_labels_fixed` / `header` | Fund Update 其中有三个 fund,每个 fund 下面的结构都要是一样的 |
| §8 | `fund_gug_snapshot` | `row_labels_fixed` / `header` | 同上 |
| §8 | `fund_hsbc_snapshot` | `row_labels_fixed` / `header` | 同上 |
| §8 | `fund_pag_snapshot_qoq` | `header` / `periods` | 同上 |
| §8 | `fund_gug_snapshot_qoq` | `header` / `periods` | 同上 |
| §8 | `fund_hsbc_snapshot_qoq` | `header` / `periods` | 同上 |

几条容易踩的：

- **E37** 是**本季在前、上季在后**（`Metric | <cq> | <pq>`）—— 跟其他 QoQ 表相反，同事那版就是这样。
- **E47** 的第三列是基准季标签，跟着 `meta.rq` 走（账本里用 `<rq>` 占位），每季都变。
- **E48** 最左列是**整列**逐格字面量（含 `†` / `*`），不是只有两行分组标题；列宽也是冻结的。
- **E57** 纵轴 1.0–1.8、每 0.1 一格，是从同事图上抄的印刷刻度，**不许按本季数据重算**。
- **E19** 的三档配色（Total 深藏蓝 / Software 亮蓝 / 其余更浅）走账本 `emphasis`。
