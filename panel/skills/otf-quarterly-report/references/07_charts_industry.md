> ⭐ **3.3 的六张图在阶段二是两两并排的**：图 15 ‖ 16、图 17 ‖ 18、图 19 ‖ 20，
> 每组两张各插 **3.50 in**，中间 0.11 in，**每组下面一段合并分析**（一段话讲两张图）。
> 阶段一出图不受影响 —— 画布仍是 6.05 in，**不为并排重出**。版式细节见 `00_layout.md` 的「并排」一节。
> 图 21 不参与并排，单图 6.05 in。

# 图 15–21 · 行业与软件分层（§3.3 / §4.3）

### § 3.3 Fundamentals —— 行业图（图 15–20，全部重画不截屏）


---

#### 图 15 · Borrower leverage — {当季判断，如 flat to slightly down}

- **位置**：`3.3 → Leverage & EBITDA coverage multiple`（第一张）
- **图型**：三折线。
- **画布**：`figsize=(16.2, 8.7)`，纯白底。
- **窗口**：`window_max = null` —— **不套两年上限**，跨度跟 MS Tracker 源图（约 21 期 / 5 年），左端永不裁。
- **系列**：`Fitch — private MM portfolio` `#16283F` `lw=2.5` `marker='D'`；`Lincoln International` `#2E6DA4` `lw=2.5` `marker='s'`；`Public loan borrowers (single B)` `#8C97A5` `ls='--'` `lw=2`（**无 marker**）。
- **图例**：图内**右上角**，`frameon=False`。
- **末点标注**：三条线各在末点右侧标 `X.Xx`，bold，同系列色（灰线也标）。
- **y 轴** `Total leverage (x)`，范围如 4.0–7.5；x 轴按年主刻度（`2021 … 2026`）。
- **数据源**：MS Private Credit Tracker 的 `Total Leverage (x)` 图（2026Q2 那季在 p.24），**读点重画**。
- **脚注模板**：
  ```
  * Median total leverage (total debt ÷ EBITDA) of private middle-market borrowers, {首期}–{末期}. Navy: Fitch's monitored private MM portfolio, annual through 2024 then quarterly; blue: Lincoln
  International valuation database, quarterly; gray dashed: single-B public broadly-syndicated loan borrowers, as public-market benchmark. Re-plotted from "Total Leverage (x)", Morgan Stanley
  Research, Private Credit Tracker {Q}, p.<n>; underlying data: Fitch, Bloomberg, FactSet, Lincoln International VOG
  ```

---

#### 图 16 · Interest coverage — {当季判断，如 improved on the quarter, still near lows}

- **位置**：同 3.3（第二张）
- 规格与图 15 **完全一致**（同系列、同色、同图例位置、同末点标注、同 `window_max = null`），只换指标：y 轴 `EBITDA coverage (x)`，范围如 1.0–4.0。
- **Lincoln 序列起点晚于 Fitch**（1Q22 起）→ 之前留空不连。
- **脚注**同图 15 模板，标题串改 `"EBITDA Coverage (x)"`，并写明 `Lincoln International valuation database, available from 1Q22`。

---

#### 图 17 · Non-accruals across BDCs — {当季判断，如 average at a five-year high}

- **位置**：`3.3 → Non-accruals & PIK level`（第一张）
- **图型**：**双轴双折线**（长月度序列，约 Mar-17 起）。
- **画布**：`figsize=(16.2, 8.2)`，纯白底，双轴。
- **窗口**：`window_max = null` —— **不套两年上限**。这张图的九年跨度就是它的论点（要能看到 COVID 的 ~4.5% 峰值和 2017–18 的 2.0–2.9% 常态区间），砍短正文那段判断就没了。
- **系列**：左轴 `Average non-accruals at cost (lhs)` `#16283F` `lw=2.2`（无 marker）；右轴 `% of BDCs with 8%+ non-accruals (rhs)` `#437BAD` `lw=1.8`（无 marker）。
- **右轴**轴脊/刻度/轴标题全部 `#437BAD`。
- **图例**：图内左上角，`frameon=False`。
- **末点高亮**：左轴序列末点画 `#A93226` 大圆点（`ms=14`），旁边标 `<值>% — 5-yr high`（当季重判这个定性），色 `#A93226`，bold；右轴序列末点标 `<值>%`，色 `#437BAD`，bold。
- **x 轴**：`Mmm-<yy>`，按年主刻度。
- **数据源**：MS Tracker 的 `Nonaccruals Across BDCs`。
- **脚注模板**：
  ```
  * BDCs with total assets over $50m, {首期} to {末期}. Data re-plotted from "Nonaccruals Across BDCs" in Morgan Stanley Research, Private Credit Tracker {Q}; underlying source: BDC Collateral
  ```

---

#### 图 18 · PIK income across BDCs — {值}% of investment income, more high-PIK BDCs

- **位置**：同 3.3（第二张）
- **图型**：**柱 + 右轴折线**，13 期季度（`Q1'23` 起）。
- **画布**：`figsize=(16.2, 8.0)`，纯白底，双轴。
- **窗口**：`window_max = null` —— **不套两年上限**，跟 MS Tracker 源图的 13 期。
- **系列**：左轴 `Avg PIK income / total investment income (lhs)` 柱 `#16283F`；右轴 `% of BDCs with 12%+ PIK (rhs)` 折线 `#A93226` `lw=2.5` `marker='o'`。
- **右轴**轴脊/刻度/轴标题 `#A93226`。
- **图例**：图内左上角，`frameon=False`。
- **标注**：每根柱顶标 1 位小数（`#16283F`，bold）；折线**只标最后一期**（`8%`，`#A93226`，bold）。
- **y 轴**：左 `Avg PIK / total investment income (%)` 0 起；右 `% of BDCs with 12%+ PIK (rhs)`。
- **数据源**：MS Tracker 的 `%PIK Income over Total Investment Income`。
- **脚注模板**：
  ```
  * BDCs with total assets over $50m. Data re-plotted from "%PIK Income over Total Investment Income" in Morgan Stanley Research, Private Credit Tracker {Q}; underlying source: BDC Collateral
  ```

---

#### 图 19 · PIK as % of net investment income — BDC industry

- **位置**：同 3.3（第三张）
- **图型**：单折线，13 期季度（`Q1'23` 起）。
- **画布**：`figsize=(16.2, 8.0)`，纯白底。
- **窗口**：`window_max = null` —— **不套两年上限**，跟 JPM Figure 2 的 13 期。
- **系列**：`#16283F`，`lw=2.5`，`marker='o'` `ms=8`。
- **标注**：每点标 1 位小数百分比 bold（`#16283F`）；**末点换 `#A93226` 大圆点（`ms=16`）+ 同色标签**。
- **y 轴** `PIK % of net investment income`，范围如 10–18（不从 0 起）。
- **无图例**（单系列）。
- **数据源**：JPM `BDCs: PIKing into PIK` 的 **Figure 2 "PIK % of Net Investment Income"**。
- **脚注模板**：
  ```
  * BDC industry aggregate, {首期}–{末期}. Data re-plotted from Figure 2 "PIK % of Net Investment Income" in J.P. Morgan, BDCs: PIKing into PIK ({报告日期}); underlying sources: J.P.
  Morgan, company reports, BDC Collateral
  ```
- **要点**：这张图必须和图 18 放在一起，正文点评的落点是「gross 口径平、net 口径升 → 分红质量被侵蚀」。

---

#### 图 20 · Non-accruals by sector — {当季判断，如 Healthcare & IT saw the sharpest rise}

- **位置**：同 3.3（第四张）
- **触发条件**：本季行业非应计**明显上升**才放。判断口径：行业均值创多年新高，或任一行业当季 vs 三年均值上升 ≥1pp。触发就必须放（2026Q2 那季已触发）。
- **图型**：**分组柱状图**，每个行业两根柱（三年均值 vs 当季），行业按当季值降序或按源图顺序排列。
- **画布**：`figsize=(12.6, 6.8)`，纯白底。
- **配色**（三系列图例）：

  | 图例项 | 色 |
  |---|---|
  | `Last 3Y average` | `#8C97A5` |
  | `<YYYY> Q<n>` | `#16283F` |
  | `<YYYY> Q<n> — sharpest rise (<行业A>, <行业B>)` | `#A93226` |

  升幅最大的两个行业的**当季柱**改用 `#A93226`，其余当季柱用 `#16283F`。**每季重算是哪两个行业**。

- **图例**：图内右上角三行，`frameon=False`。
- **标注**：每根柱顶标 1 位小数，bold，同柱色。
- **x 轴**：行业名，长名分两行（`Consumer Products` / `& Services (B2C)`）。
- **y 轴** `% of non-accrual loans by cost`，0 起。
- **数据源**：MS Tracker 的 `% of Non-Accrual Loans by Cost (Last 3Y Avg vs <当季>)`。
- **脚注模板**：
  ```
  * % of non-accrual loans by cost, last-3-year average vs {行业最新期}. Data re-plotted from "% of Non-Accrual Loans by Cost" in Morgan Stanley Research, Private Credit Tracker {Q}; underlying
  source: PitchBook | LCD. Note: data as of {行业最新期}
  ```

---


### § 4.3 AI impact on software layers


---

#### 图 21 · The software stack under AI —— **每季重画，层数与层名都不写死**

> ### ⛔ 这张图不做季度复用
>
> 每季拿到的 AI×软件研报**不是同一批券商**，而且**每家的分层方式不一样**。下一季可能是 JPM 和 Barclays 出报告、可能把软件总体分成三层、也可能冒出新的层（比如把 agent 层拆成 orchestration 与 evaluation/observability 两层）。GS 只要改了某一层的定义，这张图就得跟着改。
>
> **上一季那张四层图只是样式参考** —— 参考的是色块高度、字号、四段文字怎么排。**内容一律重读当季研报现画，层数由研报决定，不是 4。**
>
> 严禁做的事：把上一季的 `Application / Orchestration & Intelligence / Data & Platform / Infrastructure` 四层直接抄过来，只换几个代表公司。

- **位置**：`4.3 AI impact on software layers`，图下接 `**Exhibit <n>**` 一行斜体图注 + 各层定义的斜体段落（**段落数 = 当季层数**）。
- **图型**：横向色块示意图（不是数据图），自上而下按「离终端业务最近 → 最底层供给」排：application/record 在最上，infrastructure 在最下。
- **画布**：`figsize=(8.1, 1.6 × 层数)`，`facecolor='white'`；Word 插入宽度 **6.00 in**。

**每季必做的三步：**

1. **先做分层映射表**（内部工作稿，不入报告）。把 `行业\1 - Broker Software+AI\` 下**当季全部**研报读一遍，逐家记：这家分几层、每层叫什么、对每层的判断（受压 / 价值累积 / 受益 / 中性）、点了哪些代表公司。券商名单每季不同，**不要预设是 GS / UBS / BofA**。
2. **合并成当季的 N 层**。N 由映射表决定。合并原则：多家指同一件事的层合并、层名取最通用的说法、只有一家提出的新层若该家论证充分也要单列并在图注写明「仅 <券商> 提出」。
3. **画图 + 在正文写清与上季的差异**：层数变了没有、哪一层被拆或被合、哪一层的判断翻转了、是谁改的定义。

**配色按「判断」映射，不按层名映射** —— 这样层数变了配色逻辑不用改：

| 当季对该层的判断 | 色块 |
|---|---|
| 受压、价值被抽走 | `#D98C8C` |
| 价值正在累积 | `#8FCB9B` |
| 受益 | `#9CC3E4` |
| 受益且最具防御性 | `#5B84A8` |
| 中性 / 券商之间分歧未收敛 | `#AEB4BC` |

同一个判断类别当季出现两层时，同色相加深或减淡一档区分，不换色相。

**每个色块内四段文字**：

1. 左上：层名，bold，大字号，色 `#1A1A1A`；
2. 同行右端（右对齐）：判断标签，bold、小字号、色 `#1F3864`。标签文案按当季判断写，**不要照抄上季**，例：`PRESSURED — value being extracted` / `VALUE ACCRUING` / `BENEFICIARY` / `BENEFICIARY — MOST DEFENSIVE` / `CONTESTED — brokers split`；
3. 层名下方：**当季各家券商对该层的叫法**，逐行 `<券商>: …`，多家叫法一致可合并成 `<A> / <B>: …`，色 `#222222`；
4. 色块底部：`Representatives: <代表公司，逗号分隔>`，**斜体**、灰色。

- **标题**：`The software stack under AI — <N> layers`，`<N>` 是当季层数（三层就写 `three layers`），居中、bold、色 `#1F3864`。
- **`series.json` 存法**：`fig21_software_stack` 下存 `layers` 数组（层名、判断、各家叫法、代表公司、出自哪份研报）+ `brokers` 当季券商名单。**这一项每季覆盖写入**，但把上一季的整份挪到 `prev` 保留，供正文写「vs 上季分层变化」。这是唯一允许覆盖而不是追加的条目，因为它不是时间序列。
- **合并不了怎么办**：若当季研报之间分层冲突大到无法归并（比如两家的层边界完全交叉），改画「按券商分列」的对照图，或退化成一张表，并在正文写明分歧点。**不要强行捏成一套自己的分层。**
- **Word 图注**（斜体，图下方，券商名单按当季实际）：
  ```
  Exhibit <n>  The software stack under AI — layer taxonomy across <当季券商列表> frameworks.
  Source: <当季券商列表> software research frameworks; diagram by Junson AID.
  ```

---
