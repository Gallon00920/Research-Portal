# 阶段二：正文逐节行文契约（prose-spec）

**这份文件管「怎么写」；`report-spec.md` 管「写什么」；`exhibit_contracts.md` 管图表。**
写每一节之前先读本文件对应小节；写完对照「禁止项」自查一遍。

行文标杆 = 上一版成稿 `assets/baseline-2026Q3-EN.docx`（**2026Q3 定稿，本项目自己出的**）。
`assets/colleague-template-2026Q3-EN.docx` 是同事最初那份模板，只在**版式**拿不准时回看。
本文件里的英文摘录取自这两份，**只学句式、论证顺序和信息密度 —— 摘录里的每一个数字都是
上季的，一律作废，必须换成本季账本值。**（铁律四：上一版只能对答案和抄样式，不能当数据源。）

## 段长基准（2026Q3 定稿实测，Alex 已认可这个篇幅）

Alex 2026-08-25 明确「不用压」：58 张图配同事那份 3,577 词等于一半的图在正文没有落脚点，
所以基准取 **2026Q3 定稿的 7,192 词**。下面每小节的「段/词」就是这一版的实测值，
下季对照它 ±40% 自查；同事那份的更短数字放在括号里，作为「最低信息量」的地板参考。

| 小节 | 段 | 词 | （同事版） |
|---|---|---|---|
| 2.1 Private credit market size | 2 | 222 | (94) |
| 2.2 Supply side | 1 | 112 | (92) |
| 2.3 Demand side | 3 | 293 | (80) |
| 2.4 Fund flow — MM CLOs | 3 | 199 | (88) |
| 3.1 DL returns vs public credit | 3 | 381 | (124) |
| 3.2 Spread premium over BSL | 4 | 273 | (99) |
| 4.1 Spread | 1 | 106 | (140 含 4.2) |
| 4.2 Covenant & PIK | 3 | 241 | — |
| 5.1 Default rate | 5 | 565 | (143) |
| 5.2 Recovery rate | 2 | 191 | (68) |
| 5.3 Leverage | 2 | 138 | (59) |
| 5.4 Interest coverage | 2 | 141 | (51) |
| 5.5 BDC non-accruals | 2 | 201 | (66) |
| 5.6 PIK income | 2 | 132 | (64) |
| 6.1 Broker summary | 1 | 120 | (12) |
| 6.2 Related news | 5 条 | 623 | (377) |
| Things We Should Know | 引言 + 5 条 | 778 | (470) |
| 8 Fund Update 引言 | 1 | 100 | — |
| 8.1 PAG | 4 | 304 | (745 三只合计) |
| 8.2 Guggenheim | 4 | 377 | — |
| 8.3 HSBC RCF | 6 | 506 | — |
| 9.1 Positioning scorecard | 2 | 231 | (783 全节合计) |
| 9.2 Named comparators | 1 | 142 | — |
| 9.3 Momentum & trajectory | 1 | 81 | — |
| 9.4 Cohort health | 1 | 133 | — |
| 9.5 Appendix + Methodology | 2 | 475 | — |
| Disclaimer | 1 | 125 | — |
| **合计** | | **7,192** | (3,577) |

⚠ 下面各小节里写的「≈xx 词」是同事那份的地板值，**按上表的定稿值写**，
地板值只用来判断「是不是漏讲了」。

---

## 一、来源代号（照 OTF 的约定，逐段生效）

| 代号 | 含义 |
|---|---|
| **L** | 已在 `series.json` —— **从这儿读，禁止为写正文再抽一遍源文件** |
| **N** | 当季 filings / 研报新抽（只限图表上没出现过的数；抽完也要落账本） |
| **W** | 联网（记出版方 + 日期 + 完整 URL） |
| **H** | 人写 / 问用户（如 Guggenheim 内部计算数 —— 见 `series_bank.gug_internal_returns.fill_checklist`） |

## 二、全篇硬规矩（每一节都适用）

1. **全篇英文。** 引账本字段时只许用英文字段（如 `meta.screen.criteria_en`）；
   中文字段是账本内部注记，进正文即错。`pc_docxcheck.py` 有 CJK 硬检查，出现即不通过。
2. **加粗：每段至多一个头条数字。** 基线实测 0.78 处/段（含标题行）—— 每节一个水平值
   （`US$2,557bn` / `508bp` / `4.37%` / `2.8%` 这类）+ bullet 的引导短语。
   ⛔ 不是「关键数字都加粗」：2026Q3 第一版 6 处/段，读起来满屏黑点、反而没重点。
   机制上由 `build_doc.py::_bold_policy()` 兜底（每段只留第一处），
   `pc_docxcheck` 查密度。引用 exhibit 一律 `{{ex:slug}}`，绝不手写编号。
3. **数字和形容词必须同向。** 数据换方向，文字跟着换 —— 不许把上季的形容词留在本季的数上。
4. **凡表格/图上已完整展示的内容，正文不逐行复述** —— 只点「变动最大的 1–2 项 + 含义」。
5. 每段的写法：**先水平、再变动、后归因/含义**（level → change → why/so-what）。
   标杆全篇都是这个节奏，反例是「罗列式」：把五个数并排念一遍就结束。
6. 禁止占位：`[To be written]`／`待补`／空小节。写不出就删掉那一节。
7. 段长基准（词数）来自标杆实测，写完可粗查：偏离 ±40% 就该检查是不是写水了或写漏了。

---

## 三、逐节契约

### 标题块（H）
三行：`JUNSON Capital Research` / `Private Credit Quarterly Report (<RQ>)` /
`Coverage: private credit / direct lending / BDC / MM CLO` + 出稿日。不写别的。

### §2 Market Size

**2.1 Private credit market size — 2 段，合计 ≈95 词（L）**
- 段1：全球私债 AUM 总量 → 三渠道拆分（各 $ 和 %）→ 机构渠道自 2015 年的增长归因
  （dry powder + NAV 各多少）。
- 段2：美国杠杆信贷总盘子 → 三市场拆分（$ 和 %）→ 私募信贷这一叠谁在持有（BDC/DL 基金/
  PC CLO/养老/保险）。
- 标杆句式（数字作废）：
  > "Global private debt AUM has reached approximately **US$2,557bn**, of which the
  > institutional channel accounts for **77.1%** (~US$1,971bn), retail 15.5% (~US$396bn)
  > and the insurance estimate 7.4% (~US$189bn)…"
- 禁止：把 Ex 1 的逐年柱值念出来。

**2.2 Supply side — 1 段 ≈92 词（L）**
- 顺序：dry powder 峰值与最新（写清是哪年峰值）→ 「新增 dry powder / NAV」比值的趋势
  及其含义（募资驱动 vs 投放驱动）→ 募资额与基金数 vs 2021/22 峰值。
- 标杆句式：
  > "Dry powder peaked in 2024 at **US$634.8bn** and edged down to US$618.2bn… the ratio
  > has declined steadily from 66.9% in 2015 to 45.7% in…"

**2.3 Demand side — 1 段 ≈80 词（L + LCD wrap 季度精确值只喂正文）**
- 顺序：PC 在 LBO 融资的份额（LTM 笔数口径）vs 峰值 → 发起量 YTD 与 y/y（KBRA）→
  refi 占比 → **本季 vs 上季的季度量与笔数（LCD wrap，精确值）**。
- ⛔ spec §2.3 写死：wrap 的 `01 DL Volume`/`03 LBO Volume` 只进正文，不上图 5/6。

**2.4 Fund flow — 1 段 ≈88 词（L）**
- 顺序：MM CLO 发行 YTD（写清 through 几月）与 y/y → 全年背景 → MM 占总 CLO 发行比 →
  AAA 利差走向及与 BSL CLO 的基差。
- ⚠ YTD 口径句要与 Ex 7 的 Note 一致（"2026 YTD through March" 是 S&P 自己的口径）。

### §3 Returns & Relative Value

**3.1 — 2 段，合计 ≈130 词（L）**
- 段1（对着 Ex 8 表）：自 2015 年化回报/波动/Sharpe，PD vs HY、BSL、S&P500 →
  **必须挂平滑警告**（fair-value 计价、与 BSL 的相关性）→ T12M 回报及同比。
- 段2（对着 Ex 9 图，**2026Q3 起 Ex 9 = 回报两条 + HY YTW，起点 2015/12 写死**）：
  先引收益率水平（`aux.yield_context`，as-labelled：Lincoln x.x%、比 single-B 高 x.xpp）→
  一句点明「下图是回报不是收益率」→ 两条序列的年均/波动/负回报季数 → 末期差 vs 十年均差 →
  HY YTW 水平 → 收尾再挂一次 fair-value 平滑警告。
- ⛔ 回报和收益率两个口径不许混说；9.7/8.4 是收益率、8.7/4.8 是回报，各说各的。

**3.2 — 2 段 ≈100 词（L）**
- 段1：unitranche rolling-90d 利差最新值 vs 本季低点 → single-B BSL 水平 → 溢价 bp 及方向。
- 段2：分 EBITDA 档的收敛/发散 → 用 LCD 问卷/观察数据佐证一句。

### §4 Pricing & Term

**4.1 Spread — 1 段 ≈70 词（L）**：把 §3.2 的两个利差数**综合复用**（不重抽），
加 LCD 问卷给的典型定价 colour（$50m EBITDA 非周期行业的报价区间）。
**4.2 Covenant & PIK — 1 段 ≈70 词（L）**：cov-lite 分层（上中市场 vs 下中市场各自的
covenant 保有率及 vintage 对比）→ PIK toggle 份额一句。
- 标杆句式："Terms show the same stratification: cov-lite keeps rising in the upper middle
  market, where only **~37%** of 2024-vintage deals carry at least one financial covenant
  (vs ~54% in 2021)…"

### §5 Credit Fundamentals

**5.1 Default rate — 3 段 + 1 句表引言 ≈145 词（L）**
- 段1：S&P credit-estimate 口径 TTM（含 SD 与不含 SD 两条的方向差）。
- 表引言 1 句：「五家数据商在定义/样本/权重上差异巨大，本季方向都不一致（谁升谁降）」→ Ex 16 表。
- 段2（Ex 19 后）：**软件单独一句行情** —— 软件 TTM 违约 vs 资产类整体 + MS 预期。
**5.2 Recovery — 1 段 ≈68 词（L）**：违约前 12 个月的 mark 路径（提前定价）→ 各组落点。
**5.3 Leverage — 1 段 ≈59 词（L）**：先评级带定位（HY/BSL/DL 各多少倍、落哪个带）→
  再时序（Fitch vs Lincoln 方向）。
**5.4 ICR — 1 段 ≈51 词（L）**：定位（DL 只有 x.x 倍，是高杠杆的镜像）→ 边际改善一句。
**5.5 Nonaccrual — 1 段 ≈66 词（L）**：均值到几年高位 → 8%+ 尾部占比 → 公募/私募劈叉及原因。
**5.6 PIK — 1 段 ≈64 词（L）**：均值与 12% 阈值以上占比 → 公募 vs 私募 → 与 5.5 同款
  vintage 解释一句。

### §6 Sentiment

**6.1 Broker summary（N）**：表（每份实际收到的 broker 报告一列 + QoQ change 行）+
一行 Source。正文不写段落。
**6.2 Related news — 5 条 LIST，每条 ≈75 词（W + N）**
- 每条 = **粗体导语短句**（事件本质）→ 事实与数字 → 一句对私募信贷/组合的含义。
- 按重要性排序不按时间。区分事件 vs 观点；单一来源标注。
- ⛔ **每条来源必须是 Word 超链接且指向那一篇的完整 URL**（`docx_helpers.hyperlink()` 会拦
  裸域名）。拿不到准确网址就删掉这一条 —— 缺料不臆造。
- 标杆句式（数字作废）：
  > "**Redemption wave intensified in 2Q26**: BCRED requests rose from 7% in Q1 to 10% in
  > Q2; Apollo Debt Solutions from 11% to 17%; … after HLEND first enforced its 5% cap,
  > the market fell in line."

### §7 Things We Should Know — 引言 1 句 + **恰好 5 条** LIST，每条 ≈78 词（N/W/H）
- 准入：框架各节**没覆盖**的原创观察；每条以「对 Junson 组合的含义」收尾。
- 每条 = **粗体判断句**开头（不是名词短语，是有立场的完整判断）→ 证据 2–3 句 → 含义 1 句。
- 其中一条可挂本节的机动 exhibit（2026Q3 是 Ex 31 BDC maturity wall）。
- **最后写**（全篇写完才知道什么没被覆盖）。
- 标杆判断句（学句式）："Software repricing has moved from beta to alpha." /
  "The 2028 refinancing wall did not shrink — it is being pushed out." /
  "Vintage is now the most important stratification variable."
- 禁止：与前文重复同一论点换个说法；写成新闻复述（那是 6.2 的事）。

### §8 Fund Update

**开头 1 段（L）**：⛔ spec 硬性要求 —— 显式声明基金层基准日滞后：
> "…based on each manager's Q1 2026 investor report. All valuations are as of 31 March
> 2026 and therefore predate the 2Q public-market repricing discussed above."

**每只基金三小节，结构写死：**
- *Fund snapshot* —— 2 条 LIST：`Quarter activity:`（本季动作 + 关键数）、
  `Manager commentary:`（管理人观点浓缩成 1–2 句，带市场背景）。
- *Portfolio composition* —— 1 段 ≈60 词：加权特征（利差/杠杆/LTV/EBITDA/sponsored 比）→
  行业/类型集中度 → QoQ 说清（有口径切换必须点明，如 %NAV → %par 记 `_basis_change`）。
- *Fund level performance detail* —— 1 段 ≈60 词：IRR/MOIC/DPI 水平 + QoQ 方向 + 归因一句
  + 与预期回报带的相对位置。
  - PAG 标杆："Current net IRR of **14.7%** (gross 20.8%) with net MOIC of 1.11x and DPI
    of 0.30x; IRR/MOIC edged down q/q on the exit mix… while DPI rose sharply on the
    quarter's distributions."
  - **Guggenheim 特例（H）**：季报无回报指标 → 本段改写组合层（40 笔全 Performing、
    监控名单点名）+ 一句「§9 的回报数为 Junson 内部计算（见 fill_checklist，问用户）」。
    ⛔ 不许写 "left blank rather than estimated" 之类与 §9 实际填数矛盾的句子 ——
    §8.2 和 §9 的表述必须对齐同一个处理方式。
  - HSBC 必须带 ramp-up 限定："the IRR is elevated by early OID-driven realisations
    during ramp-up and the manager expects it to normalise…"（OID 那半句 2026Q3 核不到
    源就不写，换成 small-denominator 表述）。

### §9 Competitor Analysis

**开头 1 段 ≈45 词（L）**：一句话交代 screen（331 只北美直贷、导出日）+ 本季是否基线季
（基线季 QoQ 全为 n/a 且说明原因）。
**9.1 记分卡 — 表 + 表后分析段 ≈90 词（L）**
- 表后段落固定开头句式："Two readings deserve comment." → 挑**两个**最反直觉的读数拆解
  （profile artefact / 样本噪音 / 口径差），每个 2–3 句。
- ⛔ 不逐行念表。† / * 的含义在 Note 里，正文只在需要时引用。
**9.2 Named comparators — 表引言 1 段 ≈50 词（L）**：对标集怎么选的一句 + 数据滞后提醒一句。
**9.3/9.4 Momentum & trajectory — 各 1 段 ≈45 词（L）**：基线季写「这个模块从下季开始
成为头条图，本季记水平/首点」的前瞻段；从 2026Q4 起改写实际 QoQ 与轨迹解读。
**9.5 Cohort health — 1 段 ≈50 词（L）**：为什么盯 IQR 宽度（分散度走阔 = 行业压力先兆），
本季最宽的 cohort 点名。
**9.6 Appendix — 引言 1 句 + Methodology 段（L）**
- ⛔ **Methodology 段照 `build_doc.py` 里现行版本的骨架写，那是 2026Q3 定稿的标准**：
  样本（写清 333 行 vs 331 只基金）→ vintage 约定（带**有出处的**首投月份；核不到月份就
  只写年份）→ 百分位定义 + 分母随披露覆盖变化 → **三只自家基金不在池内**（外部基准披露，
  Alex 2026-08-21 指定必写）→ 季度流程（重导出、原始列重算、与归档基线 diff）→
  口径标注（† 为什么偏保守的因果链、* 为什么失真）→ 年度刷新句收尾。
- 每一句都要「给数 + 给因果」；写完对照同事版自检：他有的信息维度一个不能少。

### §10 Disclaimer（H，固定文本）
用 `build_doc.py` 现行版本；提及 ICE 数据 internal-use-only 的限制随 Ex 9 存在而保留。

---

## 四、Note（图下脚注）的写法

> ⛔⛔ **Alex 2026-08-25 定死：Note 默认只写 `Source:` 一行。**
> 原话：「所有图片下面的 Note 一般只要写 source 就行，除非出现需要额外说明的
> 比如一些特有的词汇。」

**默认形态就是一行：**

```
Source: <出版方全名>.
```

⛔ 不要把口径、方法、末期理由、数据质量分级这些**默认**写进 Note —— 它们的家在账本
（`_method` / `_caveat` / `_anchors` / `source_latest_period`），读者要的是出处。
2026Q3 那一版 Note 平均 60+ 词、最长 90 词，把图下挤成一段小论文，这是过度。

**只有下面这几种情况才允许在 `Source:` 前面加一句**，而且**一句为限、越短越好**：

| 允许加 | 例子 | 为什么必须说 |
|---|---|---|
| **特有词汇/自定义指标**读者会看不懂 | `26 YTD` 是源表自己的口径（through March）；`UOP`；`P25–P75`；`†` `*` 标记的含义 | 图上出现了一个不解释就读不懂的词 |
| 数不是从源文件直接读的 | `Values are read from the source chart.` | 关系到能不能引用到小数位 |
| 同一张图里混了两个基准日/两个口径 | 机构口径 6/30、零售与保险 12/31 | 不说就会被当成同一天 |
| 图上有断口 / 空心点 / 不报的格子 | `2Q20–3Q20 cut off in source.` | 图上看得见异常，必须给一句解释 |
| 数字是 Junson 自己算的 | `Junson calculations.` | 责任归属 |

**判据**：这一句如果删掉，读者会**读错图**吗？会 → 留；只是「知道更多」→ 删，去账本里写。

`pc_notecheck.py` 会盯着：只有 `Source:` 一行的直接通过；多出来的句子必须能对上上面
那张表里的某一类，并且该 exhibit 上要有 `_note_extra_reason` 说明是哪一类。

**Source 行本身的要求不变**：出版方全名；ICE 序列带 FRED 代号；经券商转手的二手数据
按源图 Source 行原样写（例：`Source: KBRA, Morgan Stanley Research.`）。

## 五、本季踩过、写正文时必须避开的坑（2026Q3 实录）

| 坑 | 规矩 |
|---|---|
| 中文字段注入英文正文（Methodology 段） | 只用 `*_en` 字段；`pc_docxcheck` CJK 检查兜底 |
| "previous quarter's snapshot" 写错事实 | 对账对象是什么就写什么；基线季没有"上季" |
| §8.2 与 §9 对 Guggenheim 的表述矛盾 | 同一处理方式全篇一个口径 |
| 图上数与正文数两处各自抽取 | 正文一律从账本读（L），`pc_crosscheck` 全文扫 |
| 动态题注印出 `{cq}` 花括号 | 题注一律取 `caption_rendered`；两道检查兜底 |
| 上季形容词配本季数字 | 写完每段回读：方向词与数一致 |
