---
name: private-credit-quarterly-report
description: Generate Junson Capital's quarterly Private Credit research report (docx) from a folder of downloaded source reports. Two-phase pipeline with a hard sign-off gate — phase one extracts every number into the ledger (series.json) and builds all 58 exhibits, then stops for the user to check and sign; only then does phase two write the prose and assemble the document. Use this skill whenever the user provides a folder of private credit / direct lending / BDC research materials (broker reports, fund investor reports, market trackers, PitchBook exports) and asks for the quarterly report, a private credit report, PC report, 私募信贷报告, or asks to "update the report" for a new quarter. Also trigger when the user mentions the Junson Private Credit Quarterly, the 04 Research/Private Credit folder, or asks to regenerate/refresh the report from new quarterly materials.
---

# Junson Private Credit Quarterly Report Generator

Produce the Junson Capital "Private Credit Quarterly Report" as a Word document that
exactly matches the house template — same section framework, same exhibit style, same
formatting — from one quarter's folder of downloaded source reports plus targeted web
research.

`assets/baseline-2026Q3-EN.docx`（**2026Q3 定稿,本项目产出**）是行文与版面构造的参照
—— **它只是版式与行文真值,不是数据来源**。任何数字都不许从它里面抄,连临时占位都不行;
只能在自己算完之后拿它对答案。

⛔ **同事那份模板（`assets/colleague-template-2026Q3-EN.docx`）不是运行时要打开的东西。**
Alex 2026-08-26 定死:「我所有说按同事的报告格式的,都是要你**记住格式**,而不是每次运行的
时候去看同事的报告。」—— 理由很实在:后续季度它可能根本不在手边。
所以凡是「跟同事的报告一样」的东西(表头、最左列、图形状、纵轴刻度、列宽、分组行底色…),
一律已经**抄成字面量落在账本里**,清单见账本顶层 `_frozen_colleague_formats` 与
`references/report-spec.md` §「记住的同事版式」。运行时只读账本,不读那份 docx。
那份 docx 留着只为一件事:**追某个字面量当初是从哪儿来的**(存疑时人工回看)。
Every new issue should look like a sibling of that document: a reader flipping between
quarters should see the identical framework with fresh data.

---

## ⛔ 缺料：跳过，并从报告里整块删掉（2026-11 起，覆盖本 skill 里所有旧的缺件说法）

缺源文件是常态，不是错误。旧做法（发对话框四选一、标 "not updated this quarter — source not provided"、保留上季图、沿用上季值）**全部作废**：

1. **先清点**：取数之前跑 `python3 pc_intake.py`，它按账本 `src_files` 列出缺哪些来源、影响哪些图。
2. **不问、不等、不沿用**：再跑 `python3 pc_intake.py --apply`，把靠缺失文件的 exhibit 写进账本 `meta.skipped`（`{"slug", "missing", "rq"}`）。被跳过的图本季不追加新点，历史原样留给下季。
3. **整块删掉，不留痕迹**：`exhibits.load()` 自动读 `meta.skipped` —— 删掉的图不占编号、后面顺延；并排的另一张改单独一行；`build_doc.py` 的 `ex1` / `expair` / `tbl` 自动不插。正文里仍写着 `{{ex:<被删的 slug>}}` 的句子会报错 —— 那句、那张表行、Summary 里对应的条目一起删，不写缺件说明。一小节的图和论据全来自缺件 → 整小节删；一节全删 → 整节删（例：`Competitor/` 的 PitchBook 筛选表缺 → §9 Competitor Analysis 整节删）。
4. **联网补槽不变**：本来就靠联网的槽（Related news、公开市场对照、券商观点更新）照常联网；文件夹来源缺了**不**改用联网顶替同一张图。
5. **交付说明里列出**缺了哪些文件、因此删了哪些图和小节（无人值守的运行写进它要求的 "Notes for the reviewer"）。
6. **什么都不剩才停**：`Market/` 与 `Fund/` 都空，没有可写的正文 —— 说清缺什么，停下。

| 缺的来源 | 本季删掉 |
|---|---|
| `Market/` PitchBook 年度/中期私债报告 | AUM、dry powder、募资相关图（Ex 1、3–4）及对应段落 |
| `Market/` MS Private Credit Tracker（也可能在 `Broker/`） | 杠杆信贷版图、回报/收益率、利差、契约/PIK、违约相关图及段落 |
| `Market/` S&P Direct Lending deck | S&P 违约口径图、MM CLO 发行与 AAA 利差图 |
| `Market/` LCD / PitchBook 季度 wrap | 直贷量、交易数、LBO 占比图 |
| `Broker/` 某一家 | Exhibit 30 里该家那一列及正文引用 |
| `Fund/` 某只基金的季报 | §8 该基金整块（snapshot、组合、业绩三部分）及 Summary 对应行；只缺上季那份 → 只删 QoQ 列 |
| Guggenheim 回报指标（不在任何文件里） | 有人值守时照硬要求十八发对话框问；问了没给、或无人值守（如研究面板的 AI 生成）就按「缺料」删掉这些格与叠加点 |
| `Competitor/` PitchBook 筛选表 | §9 Competitor Analysis 整节 |

## 从附件运行（Claude API、AID 研究面板的「AI 生成」）

拿不到 `04 Research/Private Credit/` 文件夹和 `_charts/` 账本时（源文件随请求附上或传进容器，研究面板的 AI 生成就是这样）：

- 每个附件按**内容**归到 `Broker/` `Fund/` `Market/` `Competitor/` 四类（首页、标题、报告期、sheet 名），文件名可能被改短，压缩包已解开。不在附件里的来源按上面「缺料」处理。
- 没有账本历史：账本从 `series_template.json` 新建，每张图只用附件本身的数据；需要附件里没有的历史 → 按缺料跳过。
- 本 skill 自带的 `scripts/` 照常可用（`PC_UPLOADS` 指向附件所在目录）；依赖上季账本或 OneDrive 路径的检查改为手工做到同样标准，不因路径不存在而停。
- 不往任何文件夹回写；文档按运行指令给的位置和文件名产出（如 `/tmp/outputs/`）。
- 「门」按运行指令处理：指令说没有人值守时，自己核图核数后继续，把本来要问的写进指令要求的说明里。

## ⛔⛔⛔ 第零条:正文的每一个字都从本季文件夹来。抄上一份报告 = 交废稿。

> Alex 2026-08-25 的原话:「skill 最底层给我写死 不允许抄前一份报告内容,
> 所有正文内容都必须从文件路径下的报告中获取,根据框架的要求。」

**这条压在所有其他规矩之上。冲突时以这条为准。**

**适用范围 = 全部。** 不只是图上的数,还包括:题注、图下 Note、**侧栏 / bullet**、
Things We Should Know、Sentiment 表的每一格、每一句形容词。凡是会印到纸上的,都算正文。

**「上一份报告」指两样东西,两样都不许当来源:**

| | 文件 | 唯一允许的用途 |
|---|---|---|
| 同事最初的模板 | `assets/colleague-template-*.docx` | **仅人工溯源** —— 运行时不许打开。版式已抄成字面量落账本(`_frozen_colleague_formats`) |
| 本项目上一版/上一季成稿 | `assets/baseline-*.docx`、`Junson_Private_Credit_Report_*_v*.docx` | ① 算完之后对答案 ② 抄版式与行文风格 |

**允许的来源只有三个,按顺序:**

1. 本季文件夹 `<Q>\` 里的源文件 —— 首选,`src` 必须写到文件名 + slide/sheet 标题
2. 联网 —— `src` 必须写出版方 + 日期 + URL,Note 里标 "web research"
3. **用户给的数**（Guggenheim 回报指标：随请求给的，或有人值守时照硬要求十八问到的）—— `src` 写「用户 <日期> 提供」+ 用户说的口径

三个都拿不到 → **按「缺料」跳过，报告里整块删掉**。⛔ 不许拿上一份报告的值顶上,连临时占位都不行。

### 比抄更严重的错:把抄的写成自己取的

2026Q3 实测(Alex 2026-08-25 抓出来):图 31 侧栏第一条 bullet 的 `194 → 207`
是从同事报告搬的(他自己诚实标了 "approximate readings from the source chart"),
而我给那条 bullet 写的 `src` 是:

```
'src': 'PitchBook | LCD 的 BDC maturity wall 图（本 exhibit 自己的两期数据，账本 stacks）'
```

侧栏的 `_src` 还写了「三条论据的数字**全部**取自本季文件夹」。**这两句对第一条 bullet 是假的。**
抄一个数,review 还能抓到;抄完再盖一个「已核过来源」的章,就永远抓不到了。

**所以 `src` 的规矩是:**

- `src` 只写**你真的打开过、核对过**的那个位置。没核过就不许写。
- 数是从上一份报告搬的 → 要么别用,要么**在 `src` 里写明是搬的**并当场标为待替换。
  ⛔ 写成「取自本季文件夹」= 造假,不是笔误。
- 一段 `_src` 用了「全部 / 逐条 / 都」这种全称词,就必须**逐条**回去核过才能写。
  写不出逐条,就把范围缩小到你真核过的那几条。

### 配套的机械检查(九道,都要过)

```
python3 src_audit.py            # 账本里每个 src 是否指向本季文件夹里真实存在的文件（含侧栏/bullet 级）
python3 pc_lastpoint.py --strict      # **末点**：每条画出来的序列末期都得有值，不许「账本里有、图上不画」
python3 pc_notecheck.py --strict      # **Note**：默认只写 Source 一行，多写的要有 _note_extra_reason
python3 pc_newscheck.py <稿>.docx --strict  # §6.2 每条 ≤100 词；个股研报不许进券商表；方向性主张要有据
python3 pc_hdrcheck.py --strict       # §8 的结构 / 表头 / 图形形态（report-spec §8 写死的那些）
python3 pc_gugcheck.py --strict       # 古根海姆八个槽：哪些还空着要问用户、已填的 src 有没有标来源
python3 pc_factcheck.py --strict      # **图内一致性**：一张图的散文里的数，必须在这张图自己的数据字段里
python3 pc_review_sheet.py --strict   # src 命中 _v\d / 报告名 → 直接 fail
python3 pc_crosscheck.py <稿>.docx    # 全文数字回账本核；值池只认数据字段，散文不算判据
```

`pc_factcheck.py` 是 2026Q3 之后加的,专门堵「同一张图两套数」:
`pc_crosscheck` 拿**全本账本**当值池,所以图 31 侧栏那个错数「在账本里」就算命中;
`pc_factcheck` 把范围收到**单张图内**,题注/Note/侧栏/bullet 里的每个数只允许来自这张图的
数据字段(外加 `meta.screen / as_of / periods / comparator_set` 这些全局口径数)。
同一事实两个版本,必有一个落在图外 —— 一定被抓到。

> **推论(硬要求):正文里印出来的每个数都必须有一个数据字段做家。**
> 引用第三方研报的统计也一样 —— 2026Q3 补了 `side_panel.cited_counts`(S&P 35%/30%、
> MS 19%/32%/55%/134 家)、`aux.labelled_split_2025_pct`、`aux.ytd_change_bps`、
> `aux.counterparty_concentration_pct`、六张 PAG 图的 `aux.denominator`(US$1,258m / 20 笔)。
>
> 口径门槛(「total assets above $50m」「rolling 90-day」「less than 25% called」)不是数值主张,
> 走 `_prose_exempt`。⛔ 豁免必须**逐条写理由**(脚本强制 ≥6 字),目的是让豁免看得见,
> 而不是让检查安静下来。

---

## ⛔ 再严一层:2026Q3 之后追加的硬要求

**一、重画就要把源图的瑕疵解决掉,不许复刻。**

我们是**重画**,不是影印。源图因为自己的轴上限把线裁断、把标签压掉、把末点挤出画框 ——
这些是源图的瑕疵,照着画出来在我们的图上就是渲染 bug(Alex 2026-08-25:「你为什么不把纵坐标轴
拉长一点?」)。处理顺序:**抬轴留余量 → 缺口画成显式断口(空心端点 + 虚线横档 + 图内小字)
→ Note 写清源图在哪里裁的**。⛔ 但抬轴**不会**把源图裁掉的数变出来:数据缺口只能标注,
不许插值,也不许拿相邻点顶上。

**二、关于「源文件里有没有」的断言,必须先穷举检索并留证。**

「Lincoln 在这份源文件里就只有这么长」「这张图没有任何明标数值可以当锚点」——
这两句 2026Q3 都说错过,都是只看了一页就下全局结论。规矩:凡是要说
**「源文件里只有…」「文件夹里没有…」**,必须先跑一遍**全文件夹**检索
(每个 PDF `pdftotext`、每个 xlsx 解 XML),把命中清单(文件 + 页 + 上下文行)写进账本,
再下结论。检索结果写在该 exhibit 的 `_anchors` 里,下季可复核。

**三、薄弱数必须在图上和 Note 里同时标出来。**

聚合值背后的观测数少于应有的一半,就要在图上用**空心点/虚线**标、并在 Note 里写清几个观测。
实例:图 7 的「2020 年均利差 175bps」其实只有 **Feb-20 与 Mar-20 两个月**(而且是新冠崩盘**之前**
的定价),账本 `aux.spread_months_observed` 记了每年的观测月数,图上 <9 个月的年份画空心点。
⛔ 这种点正文一律不许说成 "full-year average"。

**四、同色的柱与线,必须用「下方像素」判据分离。**

图 7 的源图里 MM 柱与 MM 利差线是**同一个橙色**,而 MM 柱叠在 BSL 柱上面 ——
MM 那层薄的时候,柱顶和细线在像素上完全一样。只按 run 厚度筛会把十几个柱顶读成利差点。
正确判据:再看该 run **下方 3–9px** 是不是柱色(蓝或橙),是就是柱顶。
(同类坑还有图例色块:扫色前先把图例所在行带砍掉,否则会量出 6.3x / 7.4% 这种离谱值。)

**五、少画几年用 `x_start`,不许从账本里删数。**

> Alex 2026-08-25:「图53需要从19年开始画,图54需要从13年开始画就行。」

`x_start` 是**固定起点**(每季只在右端加一期,左端不动),写在该 exhibit 上,出图时由
`js.xwin()` 切;账本里更早的期**一个都不删**(铁律一)。滚动窗口用 `window_max`,
⛔ 两者不许同时给。起点改了要**重冻 y 轴**并在 `_ylim_frozen` 里记一笔 ——
这是「只扩不缩」唯一允许的例外(口径被显式改动)。

**六、必须更新到最新。有 YTD 就画 YTD,不完整不是不画的理由。**

> ⛔⛔ Alex 2026-08-25 定死:「图7 你要定死,必须更新到最新,就算没有完整一年的,
> 但是 YTD,你就要画出来。」
> (起因:「Exhibit 7 的 2026 年为什么不画?YTD 不是有数据吗」)

**这条对所有时间轴 exhibit 生效,图 7 只是被抓到的那个。**
源文件走到哪一期,图就画到哪一期 —— 包括只有几个月的 YTD、只有一两个月观测的年份。
观测期不足是**画法问题**,用空心点 / 虚线 / 图内小字 + Note 写清几个观测;
⛔ **不是不画的理由**。账本里有值却不画 = 自己藏数据,下季换个人跑会以为源文件没有。

图 7 的 `26 YTD` 利差点(144bps,3 个月)一直在账本里,却没画,理由写的是
「三个月的窗口与年均不可比」。**这个理由自相矛盾** —— 同一张图上 2020 只有 2 个月、
2021 只有 7 个月、2022 只有 6 个月,全都画了,而且正是为此才有「<9 个月画空心点」这个约定。
既然 2 个月的 2020 能画空心点,3 个月的 26 YTD 就必须同等对待。

规矩:**要排除某一期,就把标准写出来、对所有期一致适用**;标准之外的单期理由不成立。

`pc_lastpoint.py` 强制这条:每条画出来的序列末期不许是 `None`。真的要留空,必须在该
exhibit 上写 `_last_null_reason`,**逐条**说明是哪条序列、并且理由必须**指到本季文件夹里的
具体文件 + slide/表/页**(脚本会核这个文件是否真的在文件夹里)。
只写「不可比 / 太短 / 不完整」直接顶回来。本季两条合法留空:图 23 与图 25 的
`Public Loan Borrowers (Single B)` —— tracker p24 那张 slide 上,蓝(Fitch)与金(Lincoln)
都画到 1Q26,深绿点线明显短一截,300dpi 逐列扫色确认过。这两条**每季都要回去重看源图是否补上**。

**七、别用「关键词是否出现」当守卫,那种守卫会静默失效。**

`pc_stalecheck` 的 y 轴检查里写过 `if m2 and 'ylim' not in ln:` —— 而
`set_ylim` **本身就含 "ylim"**,守卫永远为真,整条检查一直是死的(2026-08-25 实测)。
图 7 的右轴 `top = np.nanmax(vals)` / `ax2.set_ylim(0, top*1.45)` 就是这么漏过去的。
两条要求:

1. 守卫要查**语义**(有没有引用 `ent['ylim']` / `ent.get('rhs_ylim')`),不是查子串。
2. **每加一条检查,必须先故意把错误注回去、确认它会响**,再算这条检查写好了。
   本次就是这么验的:把 build_s3 改回 autoscale → 检查报「1 处(两行式)」;改回走账本 → ✓。

**八、配色只有 `palette.py` 一处真值,六色按顺序取。**

> ⛔⛔ Alex 2026-08-25 指定,改一个字都要他点头:
>
> | 位 | HEX | RGB | 角色 |
> |---|---|---|---|
> | C1 | `#1F2B44` | 31, 43, 68 | 主序列 / 深色柱 |
> | C2 | `#7A9CB7` | 122, 156, 183 | 第二序列 / 右轴叠加线 |
> | C3 | `#2EA69F` | 46, 166, 159 | 第三序列 |
> | C4 | `#6B5FA8` | 107, 95, 168 | 第四序列(兼自家基金高亮 HILITE) |
> | C5 | `#A1B6CC` | 161, 182, 204 | 第五序列 |
> | C6 | `#2F7D51` | 47, 125, 81 | 第六序列 |
>
> **用的时候按顺序**:第 1 条序列 C1、第 2 条 C2……多序列图一律 `js.SERIES[i]`。

- ⛔ 出图脚本里**不许出现十六进制字面量**,一律用名字。`pc_audit` D 组会扫,包括
  `junson_style.py` 自己 —— 2026-08-25 就是在它的 `rcParams` 里逮到写死的
  `axes.edgecolor="#8C97A5"`(而且刚好是退役的旧色),换色系后 41 张图里还残留着。
- ⛔ `junson_style.py` 只做**取名与排版**,不许再重新赋值色量。同一天还逮到它
  `from palette import BANDS` 之后又写了一遍 `BANDS = [...]` 覆盖掉 —— 于是
  palette 换了色、评级带图还是旧色,肉眼看不出来。
- 角色名(NAVY / GOLD / …)是**位次的别名**,字面意思已经不准(GOLD 现在是蓝灰),
  别照名字挑颜色,看 `SERIES` 那一行。
- 改配色的完整动作:改 `palette.py` → 重跑全部 `build_s*.py` → `pc_audit` D 组
  (含**扫 46 张 PNG 确认没有退役色值**)→ 逐张看一遍(见步骤 6)→ 重出稿。
- ⚠ 换色系会暴露原本被旧配色掩盖的**标签压叠**:对比度一变,原来看不出的重叠就显出来了。
  柱值标签与右轴折线的避让已抽成 `js.place_bar_labels()` —— **按实测 bbox 判断**,
  不许用「两个轴的归一化高度差 < 阈值」去估(估过一版,把线在柱顶下方的两根也判成撞了,
  标签移进柱内正好压上)。

**九、图下 Note 默认只写 `Source:` 一行。**

> ⛔⛔ Alex 2026-08-25:「所有图片下面的 Note 一般只要写 source 就行,除非出现需要额外说明的
> 比如一些特有的词汇。」

口径、方法、末期理由、数据质量分级 —— 这些的家在**账本**(`_method` / `_caveat` /
`_anchors` / `source_latest_period`),不是图下。只有五种情况允许在 `Source:` 前加**一句**:
自定义词汇/标记(`26 YTD`、`UOP`、`†` `*`)、值是从图上量的、一图两基准日、
图上有断口/空心点/不报的格子、数字是 Junson 自算的。
判据:这句删掉读者会**读错图**吗?会 → 留;只是知道更多 → 删,搬去账本。
细则与例子见 `references/prose-spec.md` 第四节;`pc_notecheck.py` 盯着,
多写的句子必须在该 exhibit 上写 `_note_extra_reason="<类别> — <理由>"`。

**十、固定列序 / 固定列名的表,写死在账本里,不许照源表的样子重排。**

- **Ex 8**(`ret_risk_return_table`):`S&P 500` 那一列**固定在最右**。列序 =
  Metric → 私债四档 → 公开信用三档 → S&P 500。理由:S&P 500 是股票,与前七列不同类,
  放中间会被当成同组比较。⛔ 下季照抄,不许因为源表列序改回去。见账本 `_col_order`。
- **Ex 16**(`cf_provider_compare_table`):七列,**列名全部固定**,只有倒数第二、第三列
  是季度,跟着报告走 ——
  `Provider | Sample / scope | Definition / methodology | <periods[0]> | <periods[1]> | Trend | Cohort`
  那两个期名从**本图自己的 `periods`** 读(源表 p27 的列头就印着),
  ⛔ 不许借 `meta.periods` 的任何一层:market 层是 1Q26/2Q26、fund 层这季刚好等于
  4Q25/1Q26 是巧合,下季就会错开。见账本 `_header_spec` / `_periods_src`。
  `Cohort` 是**体量分档标签**(Core-to-upper MM / Lower MM / Upper MM / All included),
  ⚠ 源表没有这一列 —— 每格的依据逐行记在 `_cohort_basis`,其中 KBRA DLD 的 Upper MM
  源文件里推不出来、是 Junson 的行业判断,已标明。正文不许说成「各家自己的分类」。

**十一、逐图指定的配色分档与朝向,写在账本字段里,由出图脚本读 —— 不许写死索引。**

- **Ex 19**(`cf_fitch_default_by_sector`)三档(Alex 2026-08-25:「Total 是深蓝色,
  software 是亮蓝色,其他是比深蓝色稍浅的色」):
  `emphasis="Total"` → **C1** `#1F2B44`;`highlight="Technology Software"` → **C3** `#2EA69F`
  (六色里最亮的那个 —— 同事 E21 的高亮用的就是这个青蓝);其余 → **C2** `#7A9CB7`。
  颜色由 `emphasis` / `highlight` 两个字段驱动,下季行业集合变了也不会错位。
- **Ex 21**(`cf_recovery_by_sector`)**竖版**(Alex 2026-08-25:「要竖着,像同事报告里的 E21 一样」):
  `orientation="vertical"`,走 `build_s2.vbars_hl()`。纵轴冻结 `[0,80]/10`,
  柱值标柱顶上方,Software 高亮 C3、其余 C1。

> ⚠ **抄同事的版式时必须注意 1:1 版面锁。** 同事的 E21 在 Word 里也是插 3.35in,
> 但他的源 PNG 只有 640×570 —— 等于按更宽的画布出图再缩进去,**图内字被一起缩小了**。
> 我们按 1:1 出(图内写多少 pt 纸上就是多少 pt),同样 8 个行业标签在 3.35in 里
> 45° 两行就压叠(guards 抓到两处)。解法是**转 90° 竖排 + 缩写成单行**,
> 缩写文本放账本 `label_wrap`、角度放 `label_rotation`,⛔ 不许在脚本里写死行业名。
> **抄版式可以,抄「靠缩图掩盖压叠」不行。**

**十二、图例放**图内**,不放图下。**

> ⛔⛔ Alex 2026-08-25:「Exhibit 23 中的图注要放在图里,而不是图的下面,不止 E23,
> 这个也要写在阶段一生图的底层。」

**这是阶段一出图的通则,所有出图函数一律走 `js.legend_inside()`**,⛔ 不许再用
`ax.legend(bbox_to_anchor=(0.5, -0.x))` 把图例甩到轴外。理由:图例在图下会和 Word 侧的
「题注 → 图 → Note」三段挤在一起,并排图(3.35 in)下方本来就要留 Note 的位置。

选位规则:
1. 先读账本 `legend_loc`(**冻结值**,四个角之一)。
2. 账本没有 → `legend_inside()` **实测四角的数据墨量**、挑最空的一角,并打印一行建议值。
   看过图之后把它写进账本冻结。⛔ 不许让它每季自动重选 —— 自动选会让同一张图的图例
   跨季跳位置,读者会以为图变了。
3. 图例带 82% 白底(`framealpha`),压在网格线上仍读得清,但不许压在数据上 ——
   `guards` 会抓压叠,抓到就换角或抬 y 轴上限。

**图例色块可能被读成数据点时 → `legend_boxed: true`,不是把图例赶出去。**

> ⛔ Alex 2026-08-25:「这两个也是要放在图内的,可以用个细的黑色矩形框线把图标框起来,
> 就不会读错了。」

`legend_boxed: true` = **实心白底 + 0.6pt 黑框**。框一上,那块区域就读作图例、不再读作散点。
**Ex 51 / 52**(`ca_traj_*`)是实例:8-24 那次被读成「2027 年有数据」,是因为图例色块**无框**、
又正好落在 2027Q1–Q3 的横轴位置上 —— 加框解决,**原来的「图例放图外」例外已取消**。
⛔ 判据:图上只有少数散点、而图例用的是同样的 marker 时,一律 `legend_boxed`。

**唯一剩下的一类例外:密集图没有空角。**
**Ex 20**(`cf_recovery_path`,四组×四条)四个角墨量都 3000–9000,guards 抓到图例项与柱值
100% 压叠。解法**不是**把图例赶出去,而是**抬 y 轴上界**给顶部腾一整条
(`[0,90]`→`[0,110]`,只扩不缩,已在 `_ylim_frozen` 记因),图例两列放左上。

**十三、券商观点表的 QoQ Chg:开头写 `New …`,而且必须带数字。**

> ⛔ Alex 2026-08-25:「E30 的表里,QoQ Chg 部分,要包含数字,要写 New xxxxxxxxx,
> 你参考同事报告的这部分。」

- 本季新增的东西开头写 **`New …`** —— 新券商、新预测框架、新量化口径都算。
- **必须带数字**,不许只写形容词。「Tone improved vs 1Q」这种空句要么补上变了什么数、要么删掉。
- 数字只能来自本季文件夹(第零条),取各家 `view` / `points` 里已经核过源的那些。
- 一格 1–3 句。
- ⚠ **「New this quarter」需要上季的券商名单**,而上季名单只在上一份报告里 —— 按第零条不能拿它当来源。
  所以账本里加了 `sent_broker_summary.broker_history`(逐季只追加):
  **本季名单里有、上季名单里没有 → 才允许写 New**。下季起靠它判定,不许靠印象或翻旧报告。

**十四、§6.2 Related news 每条 ≤100 词(不含末尾链接)。**

> ⛔ Alex 2026-08-25:「6.2 Related news 的新闻长度,最长不允许超过 100 个单词,
> 不含末尾新闻链接。」

一条新闻 = 一个判断句开头 + 支撑数字 + 对 Junson 的含义,**100 词以内讲完**。
超了就是把三条挤成一条 —— 拆开或删掉次要的。`pc_newscheck.py` 数词,超了直接 ✗。
(⚠ 2026Q3 那一版 5 条里 4 条超:137 / 173 / 110 / 121 词,下次重出正文时必须压。)

**十五、券商观点表只收行业层面观点,个股研报一律排除。**

> ⛔ Alex 2026-08-25:「ARES 这种肯定不能出现的,一定要把 specific 的公司排除!」

排除范围:个股/单一发行人研报(含评级、目标价、管理层交流纪要)、只讲某一只基金或某一家 BDC
的单标的报告、非私募信贷主题的报告。**判据:标题或正文里出现具体公司名 + 评级/目标价 → 排除。**
既不进 `reports` 串,也不进 View / Key points / QoQ。

⛔ 排除的要在 `rows` 里留 `_excluded_from_table` 写明理由 —— 证明**读过并主动排除**,
不是漏掉。2026Q3 的实例:MS 的 *Ares Management Corp: Private Credit Discussion Takeaways*
(Equal-weight、目标价 $178)原来挂在 MS 的 reports 串里(`ARES Discussion 4/2`),已摘掉。
`pc_newscheck.py` 会扫 reports 串里的公司名/评级词。

**十六、QoQ Chg 里的方向性主张必须有账本记着的上季立场做依据。**

> ⛔ Alex 2026-08-25 抓到:我给 GS 写「Call unchanged at modest widening」,
> 同事写「Tone improved vs 1Q」—— **方向相反**。

**谁对?两个都不能由本季文件夹证明。** 文件夹里只有本季这一份 GS 报告,没有上季的 GS 观点;
同事有上季上下文所以敢写 improved,我没有却写了 unchanged —— **那句是无据断言,已删**,
改成只写本季报告自己能证明的东西(标题口径 + 数字)。

规矩:
- 「vs 上季 / improved / unchanged / upgraded / downgraded」这类**跨季**方向词,
  必须能在账本 `sent_broker_summary.stance_history` 里查到上季那家的立场。查不到 → 不许写方向。
- **同季内**比较可以(两份报告都在本季文件夹里),但要把**两个端点都写出来** ——
  例:「July tone better than April」,而不是光写「tone improved」。
- `stance_history` 逐季只追加(本季已记 5 家的立场原话 + reports 串),
  下季判 tone 变化查它,⛔ 不许靠印象、也不许翻旧报告(第零条)。

**十七、§8 Fund Update 的结构、表头、图形形态全部写死 —— 见 `references/report-spec.md` §8。**

> ⛔ Alex 2026-08-25:「每个 fund 下面的结构都要是一样的,要包含 Fund snapshot、
> Portfolio composition、Fund level performance detail」「E32 和 E33 都必须是饼图,
> E35 的柱状图必须竖着」「E36/37/38 的表格的左侧和顶部的表头也必须是一样的(跟同事的报告)」
> 「E41 和 E42 也是要跟同事的报告里的表格的表头一样,E43 必须是饼图」

要点(细则在 report-spec §8):

1. **三只基金三段同构**:`Fund snapshot` → `Portfolio composition` → `Fund level performance detail`。
   段名、段序、表结构完全一致;缺料写 not disclosed,**段不许省**。
2. **Fund snapshot = 两张表 + 两条 bullet**。
   表 A 六行固定:`Strategy / Total commitments / Final close / Investment period ends /
   Initial term ends / Status`(⚠ 同事那版三只各写各的,现在统一成这六行);
   表 B 固定 `Metric | <pq> | <cq> | QoQ Δ`;下面固定 `· Quarter activity:` 与
   `· Manager commentary:` 两条 bullet。
3. **图形形态由 `chart_form` 定死,不由数据启发式定**:E32 / E33 / E43 饼图、
   E35 / **E44** 竖版柱(E44 的加权平均参考线从竖线改成水平虚线)。
   `shares()` 原来按 `DONUT_MAX=5` / `DONUT_MIN_SLICE=8` 自动挑,切片一多一小就悄悄退化成
   横柱 —— 已改成 `chart_form` 优先。
   ⛔ 饼图配色:前 6 大用 SERIES 六色、第 7 个起用 `PIE_OTHER` 中性灰,
   **不许 `SERIES[i % 6]` 循环**(那样第 7 片与第 1 片同色,实测撞过)。
4. **E45 的 QoQ 必须写出是哪个项目**:净增/净减写 `+1 (项目名)` / `-1 (项目名)`,
   多笔并列 `+2 (A, B)`,无变动写 `–`。⛔ 不许编名字 —— 要能在 `fund_hsbc_portfolio` 的
   rows 里找到;判定靠本季持仓表与上季正文名单取差集。
5. **八张表的表头逐字写死在账本的 `header` 字段里**(E36/37/38/41/42/45/46/**47**),
   ⛔ 不许只写在 `build_doc` 的调用里 —— 写在调用里下季改代码就悄悄漂了。
   季度标签从**该 exhibit 自己的 `periods`** 读(基金层三只报告期不一定同步,不许借 `meta.periods`)。
   ⚠ E37 是**本季在前、上季在后**(`Metric | <cq> | <pq>`,同事那版就是 Q1 2026 | Q4 2025)。
   ⚠ **E47 有两个换季必错的点**,单独说:
   - 第三列是**基准季标签**。真值是 `header_template` 里的 `<rq>` 占位,
     `build_doc` 从 `template + meta.rq` **现算**。⛔ 不许读账本里 `header` 那份本季快照 ——
     下季 `meta.rq` 变成 2026Q4 而快照还写着 2026Q3,就会印出旧季度。
     `pc_hdrcheck` 把 template 解析后与 `header` 对比,换季时这就是哨兵。
   - 三个 Δ 列(`QoQ Δ` / `Cohort Δ` / `Pct Δ`)本季全是 n/a,**是因为没有上季,不是算不出来**。
     `ca_scorecard.history[<季>]` 已存下本季九行的 `value / value_num / cohort_median /
     cohort_n / percentile / basis / marker`(逐季只追加)。下季算法(三列各有自己的分母,不许混):
     ```
     QoQ Δ    = 本季 value          − history[上季][key].value_num
     Cohort Δ = 本季 cohort_median  − history[上季][key].cohort_median
     Pct Δ    = 本季 percentile     − history[上季][key].percentile   （pp）
     key = "<fund> — <metric>"
     ```
     ⛔ 上季值只能从 `history` 取,**不许翻上一季成稿**(第零条)。
     ⛔ 下季这三列**不许再是 n/a** —— 只有 `history` 里查不到上季那一条才允许(例:基金本季新进池),
     并在该行注明原因;有上季记录却写 n/a,`pc_hdrcheck` 直接报错。
     ⚠ `cohort_median` / `percentile` 每季都要用**当季 PitchBook 导出**重算(池子会变),
     `history` 只用来做差,不许拿它的旧值当本季值。

6. **E48 `ca_named_comparators`:九列 + 两行灰底分组标题。**

   > ⛔ Alex 2026-08-25:「E48 这个表头也是固定的,表的左侧的表头必须也是一样,
   > 要加上 Core-to-upper MM 和 Low-to-core MM,背景是灰色的。」

   `Fund | Vintage | Size ($m) | Net IRR | TVPI | DPI | Called % | Dry powder % | PB quartile`
   （原来只有八列,缺 `Dry powder %`,已补）。

   **最左列整列逐格照同事那版**（不只是两行分组标题）—— 账本 `row_labels_fixed.expected`
   存了 12 个字面量，`pc_hdrcheck` 逐格比：

   ```
   Junson — PAG BRS III (SRT)        Core-to-upper MM                  Low-to-core MM
   Junson — Guggenheim PDF IV †      KKR Lending Partners IV           TPG Twin Brook Direct Lending VI
   Junson — HSBC RCF *               Ares Senior Direct Lending Fund II  Golub Capital Partners 15
                                     Apollo Origination Partnership I  HarbourVest Direct Lending Fund II
                                                                       Oaktree Direct Lending Fund
   ```

   ⛔ **竞品行不许加「House — 」前缀** —— 我们原来写 `KKR — KKR Lending Partners IV`，
   他写 `KKR Lending Partners IV`。只有自家三只以 `Junson — ` 开头。
   ⛔ `†` / `*` 标记是**列名的一部分**，直接写在 `row_label` 里，不再由 `basis_marker` 拼。
   表上印 `row_label`；`label` 留作内部标识（别处引用它，改了会断）。
   下季基金集合会变时:自家三只那三行字面量**永不变**;竞品行照当季 PitchBook 的基金全名写，
   同样不加前缀、同样按同事的简写习惯（省掉可省的 "Fund" 之类以控列宽）。
   分组行:整行灰底 `E8E8E8`(同事那版就是这个色)、首格加粗、**其余格留空但不合并**;
   ⛔ **不许 merge 那一行的单元格** —— python-docx 合并时会把 9 个格子的段落全搬进合并后那一格,
   于是那格有 1 个带字段落 + 8 个空段落,整行变成 9 行高、灰底拉出一大块空白
   (2026-08-25 实测,Alex 一眼看出来)。同事那版本来也没合并。
   数据行隔行浅底 `F2F5F9`。机制在 `docx_helpers.data_table(group_rows=…, zebra=…)`。
   ⛔ 分组名从账本 `tier_labels` 读,**不在 build_doc 里写死** —— 下季基金集合会变,tier 名不会。

`pc_hdrcheck.py` 逐字核对表头、六行行标、两条 bullet、五张图的 `chart_form`、
E45 的项目名、E47 的 history/Δ、E48 的两行分组标题 —— 对不上直接 ✗。

**十八、古根海姆的回报数每季**手动问用户**,取数阶段一开头先跑 `pc_gugcheck.py`。**（无人值守的运行没法问：有人值守时照硬要求十八发对话框问；问了没给、或无人值守（如研究面板的 AI 生成）就按「缺料」删掉这些格与叠加点）

> ⛔⛔ Alex 2026-08-24:「以后每个季度更新的时候刚刚那几张图古根海姆缺的数不从我刚刚发的
> excel 里更新,你要主动发对话框让用户手动输入,这个 excel 不会接入文件夹让 skill 自动读取。」
> ⛔⛔ Alex 2026-08-25 再强调:「E49 和 E50 的图里的古根海姆的数据也是到时候 skill 运行的时候
> 需要手动输入的。」

- **AID Portfolio Tracking Master 那份 excel 不进季度文件夹**,skill 不许读它、
  它里面的数不许进账本。
- 有 Guggenheim 坑的**八个槽**记在 `series_bank.gug_internal_returns.fill_checklist`:
  **E47** `ca_scorecard`、**E49** `ca_momentum_irr`、**E50** `ca_momentum_tvpi`、
  E51/E52 `ca_traj_*`(每季档);E56/E57/E58 `ca_apx_*`(年度档,附录刷新年才问)。
- **`pc_gugcheck.py` 在取数阶段一开头跑**:逐槽列出「还空着、要问用户」的位置,
  并核已填的那些 `src` 有没有标「用户提供 / 授权例外」——
  ⛔ 有值但 src 没标,说明是从别处偷来的,直接 ✗。
- 问用户时必须一并确认三件事:①截至哪一期;②IRR 口径(YTD 年化 vs 成立以来 ITD ——
  同事 2026Q3 用 YTD 年化,PitchBook cohort 是 ITD,用哪个让用户拍板);③标 † computed
  internally by Junson。
- ⛔ 用户不给数就**留空 + 写 gap 说明**,绝不拿上季的值顶上。

**十九、交付完要自己列一遍目标目录。**

2026Q3 踩过:说了「已改」但没发文件,用户看的还是旧版。
`device_commit_files` 之后必须 `device_bash ls` 目标目录确认文件真的在那儿、时间戳是新的,
再向用户报「已交付」。

⛔ 还有一条人肉规矩,脚本替不了:**改一个数,就全文搜一遍这个事实** ——
题注、Note、侧栏、正文、跨节引用,一处不改就是一处矛盾。
`fix_*.py` 那种对单个字段做 `.replace()` 的订正脚本是 2026Q3 漏掉侧栏的直接原因:
它只改了 `note`,同一句话在 `side_panel.bullets[0].text` 里还有一份,活到了 v4。

---

## 下一季怎么跑(操作清单)

用户给一个季度文件夹(如 `…\04 Research\Private Credit\2026Q4`)就按下面走:

```
阶段一
 0  确认季度标签与语言(只英文 / 英文+中文);更新账本 meta:
    rq / report_date / periods / as_of / screen                 → 见 §1
 0b **换季体检**:python3 pc_stalecheck.py  ⛔ 不通过就别往下跑
    —— 扫出「本该随季度变、却锁在上一季」的东西(期名标签、
    出稿日、季度目录路径),这类错出来的稿是「新数据配旧期名」,
    版面检查抓不到(文件名与页眉会一起错)
 1  device_list_dir 递归列文件夹,device_stage_files 暂存        → 见 §2
 2  从 <父目录>\_charts\series.json 读上季账本(没有就从
    scripts/series_template.json 建);⛔ 账本跨季共用,不进季度文件夹
 3  逐张按 references/exhibit_contracts.md 取数写账本 + src     → 见 §3
    ⛔ 每张图的「下季去哪儿看源末期」就写在契约的 🕐 末期与新鲜度 里
 4  Guggenheim 的 IRR/TVPI/DPI/called% —— 有人值守时照硬要求十八发对话框问；问了没给、或无人值守（如研究面板的 AI 生成）就按「缺料」删掉这些格与叠加点:
    先跑 python3 pc_gugcheck.py 列出八个槽,逐项过              → 见 硬要求十八
    ⛔ AID master excel 不进文件夹、不许读、数不许进账本
 5  联网补槽(ICE 那条只追加一期,历史冻结)                        → 见 §3b/§4
 6  出图:python3 build_s2.py … build_s7.py                      → 见 §5
 7  末期核对:pc_period_check.py + period_evidence.py            → 见 §5b
 8  自己逐张看 PNG;src_audit.py;gen_contracts.py 重出契约        → 见 §6
 9  pc_review_sheet.py --strict;pc_audit.py                     → 见 §7
10  🚪 把图 + out/REVIEW_*.md 交用户,**等签收**                  → 见 §8
    用户说签收后:python3 approve.py --sign

阶段二
11  approve.py --check 验签                                     → 见 §9
12  写正文:先读 references/prose-spec.md(怎么写),
    再读 references/report-spec.md(写什么)                       → 见 §10
13  出稿:python3 build_doc.py                                    → 见 §11
14  五道自查:pc_docxcheck.py / exhibits.py --check /
    pc_crosscheck.py / pc_lastpoint.py / pc_factcheck.py
    —— 五个都要 ✗ 为 0                                           → 见 §13
15  export_sources.py 出来源清单;交付 + device_commit_files      → 见 §14
```

**最容易忘的三件事**:①账本在 `_charts\`(父目录)不在季度文件夹;②Guggenheim 要问用户;
③附录 Ex 54–58 是**年度**刷新,不是每季都动。

---

## 四条铁律

**一、账本先行。数据只追加,不重算。**

```
exhibit = junson_style.py（样式,定稿后不改） × series.json 的切片（数据,只追加）
```

`series.json` 是这套东西的心脏 —— 58 个 exhibit 的每一个数据点、每个点的出处都在里面。
它记住历史,所以每季只需要放进**本季新增的**那几份报告 —— 基金那三份尤其:
组合 QoQ 表和 KPI 环比表从账本读上季,不需要再翻上季的投资人报告。

#### ⛔ 目录约定(2026Q3 踩过,写死)

```
04 Research\Private Credit\
├── _charts\                      ← ⛔ 跨季共用,**永远只有这一个,不许每季新建**
│   ├── series.json               ← 账本本体。每季在原地追加,不复制不改名
│   └── ICE_BofA_US_HY_YTW_*.xlsx ← 冻结外部序列的原始文件(只追加)
├── 2026Q3\                       ← 本季源文件夹(用户给的就是这一层)
│   ├── Broker\ Fund\ Market\ Competitor\
│   └── _charts_snapshot\         ← **本季留痕,每季一个**,出稿后写:
│       ├── charts_2026Q3.zip            (定稿的 46 张 PNG)
│       ├── series_2026Q3_signed.json    (签收当时的账本副本)
│       ├── APPROVED_2026Q3.json         (签收记录:sha256)
│       ├── REVIEW_2026Q3.md             (核对清单)
│       └── exhibit_contracts_2026Q3.md  (本季契约)
└── Test\                         ← ⛔ **成稿一律落这里**,不许再往父目录根扔
    ├── Junson_Private_Credit_Report_2026Q3_EN_v*.docx
    └── sources_ledger_2026Q3.md
```

> ⛔ Alex 2026-08-25:「后续我们这里再生成报告 放到这个文件夹下,不然太乱了
> `…\04 Research\Private Credit\Test`」
>
> 三个落点互不替代,别混:
>
> | 东西 | 落点 | 节奏 |
> |---|---|---|
> | 成稿 docx + `sources_ledger_<Q>.md` | `<PC 根>\Test\` | 每季新文件 |
> | 账本 `series.json` | `<PC 根>\_charts\` | 原地覆盖,跨季共用 |
> | 本季留痕 5 件 | `<PC 根>\<Q>\_charts_snapshot\` | 每季一个 |
>
> ⛔ **账本不许塞进 `Test\`** —— 它跨季共用,进了 Test 下季就找不到。
> 落点由 `pcpaths.deliver_targets(<PC 根>)` 算,路径与季度都不许手打。

**⛔ 季度、路径、源文件名 —— 一律由 `scripts/pcpaths.py` 从账本 `meta.rq` 推,
脚本里不许写季度目录、不许写源文件全名。**

```python
import pcpaths as P
P.rq()                                            # '2026Q4' ← 唯一真值源 = meta.rq
P.quarter_dir()                                   # 本季源文件夹(找不到就报错并列出实际有哪些季度)
P.one('Competitor/PitchBook_Search_Result_*.xlsx')  # 按通配符取唯一一份;零个或多个都报错
P.report_name()                                   # 成稿文件名(季度来自账本)
```

下季文件名一定变(带季度、带导出时间戳),所以取文件**一律用通配符**,不写全名。
`P.quarter_dir()` 找不到本季文件夹时会报错并列出暂存目录里实际有哪些季度 ——
**绝不静默退回上一季**。已实测:把 `meta.rq` 改成 2026Q4 后,`src_audit` / `ca_compute` /
`gen_contracts` 三个脚本全部 exit=1 并提示「先把 2026Q4 暂存进来,不许改用别的季度顶上」。

#### ⛔⛔ `RQ`(命名季)与数据季是两个季度,不许混用

> Alex 2026-08-25:「文件名和最终生成的报告的标题或者页眉里出现的季度是 **skill 运行时的季度**。
> 因为现在是 Q3,但是报告季报最新甚至只有 Q1,但你在报告命名的时候还得是用 skill 运行时候的季度。
> **这个要写死。**」（做法照 OTF `02_quarter_window.md` §2.1.1）

| 记号 | 含义 | 怎么定 |
|---|---|---|
| **`RQ` = `meta.rq`** | **报告季 = 撰写这份报告的时间** | **从运行日的日历季度来**,不是从源文件来。2026 年 8 月跑 → `2026Q3` |
| `market_cq/pq` | 市场层数据季 | 本季文件夹里最新的市场类研报/xlsx 自己的期 |
| `fund_cq/pq/ppq` | 基金层数据季 | 三份投资人报告的期(**通常滞后市场层 1–2 季**) |
| `competitor.export_date` | 竞品层基准 | PitchBook 导出日 |

| 只有这三处用 `RQ` | 其余一律用数据季 |
|---|---|
| **文件名** `Junson_Private_Credit_Report_<RQ>_EN_v<n>.docx` | 正文里所有数字、所有 QoQ 对比 |
| **首页大标题**里的季度 | 所有图的轴标签、图例、题注、Note |
| **页眉**的季度 | 所有表的「本季 / 上季」列头 |
| — | `series.json` 的期次 key、`APPROVED_<RQ>.json` 用 RQ、`REVIEW_<RQ>.md` 用 RQ |

**判据:凡描述数据的时间一律用数据季,一个字都不改;只有文件名、首页标题、页眉这三处用 `RQ`。**
2026Q3 的实例:命名是 `2026Q3`,但基金层数据只到 `1Q26`、市场层到 `2Q26` —— 三个季度同时出现在
同一份报告里是**正常的**,不是错。反过来把文件名写成 `2026Q1`(跟着最旧的数据走)才是错。

`pc_stalecheck.py` 每季硬查:`meta.rq` 必须等于**运行日**的日历季度(补做旧季度会提示确认),
并且提示 `meta.rq` 与各数据层季度的关系,防止把数据季当成命名季。

#### ⛔ y 轴冻结在账本里,不许每季 autoscale

照 OTF `02_quarter_window.md` §3.5.1。窗口一滚或新点一来,autoscale 会把 y 轴上下界跟着改,
**同一张图这季顶到 18、下季顶到 16,曲线形状看着完全不同,读者会以为数据变了。**

- `ylim` / `ytick`(右轴 `rhs_ylim` / `rhs_ytick`)存进 `series.json`,当成样式的一部分冻结;
  出图直接用,**不调 autoscale**。出图脚本里若没有账本值才允许兜底 autoscale。
- **只扩不缩。** 新点真的越界才向外扩一个刻度,并在该 exhibit 的 `_ylim_frozen` 里记一笔
  「从 A 改到 B,因为 X」。窗口滚掉一个高点**不构成收窄理由** —— 缩了跨季就对不上。
- 首次设定:取历史全量 min/max 各留 12–15% 余量,向外取整到刻度步长。
  ⚠ **余量要给图内注释留位置,不只给数据** —— 2026Q3 踩过:Ex 50 按数据算 1.4,
  TVPI/DPI 两个组标题顶到边被压叠检查拦下,扩到 1.6 才过。
- `pc_stalecheck.py` 会扫出出图脚本里仍按数据 autoscale 的 y 轴。

#### 滚动窗口:`window_max`

PC 这套 58 张图里**绝大多数是「照源图重画」**(MS tracker / S&P deck / LCD wrap 的图),
横轴跨度**由源图决定,左端永不裁** —— 所以 `window_max` 一律 `null`,出图不做切片。
这与 OTF 图 15–19 的例外同理:砍成两年会跟源图对不上,等于自废交叉验证,还会砍掉正文论点
(例:Ex 9 的 2015→今、Ex 26 的 37 个季度,正文都在用长序列讲周期)。
只有**自己从 filings 抽数攒起来的**序列(如 `ca_traj_*` 的分位轨迹)才需要设窗口;
届时按 OTF 的做法:先只往右加,满 8 期(两年)才开始裁左端,并同步改三处 ——
题注里的期间串、Note 里的首末期、正文里「五个季度以来」这类相对表述。

#### 上季数不从当季报告的对比列取

投资人报告的对比列常常是**上一年年末**而不是上一季,而且会按新口径重述。
**上季数一律从上季那份报告自己取**(账本已存,不必重翻)。2026Q3 的 PAG 3Q25 就是从
`PAG BRS Fund III L.P. - 2025 Q4 Quarterly Newsletter.pdf` 自己取的,不是从 1Q26 那份的对比列。

**⛔ 季度相关的一切都从账本 `meta` 读,脚本里不许写字面量。**
`meta.rq`(季度标签,决定标题/页眉/文件名)、`meta.report_date`(出稿日)、
`meta.periods`(各层的本季/上季/上上季标签,表头与正文印期名都用它)、
`meta.as_of`(三层基准日)、`meta.screen`(筛选口径 + `criteria_en`)。
2026Q3 踩过:`build_doc.py` 里 `RQ`、三张基金表的表头、方法论段的 "as of 2Q26"
全是写死的 —— 下季换文件夹跑,出来是**新数据配旧期名**,而且
`pc_docxcheck` 的「文件名与页眉一致」还会通过(两处一起错)。
现在这些全部从 `meta` 读,`pc_stalecheck.py` 每季开跑前硬查一遍。

**两个目录别搞混:**
- `_charts\`(父目录)= **跨季一个**,只放账本与冻结的外部原始文件。
- `2026Q3\_charts_snapshot\`= **每季一个**,放本季的定稿留痕(只读存档,下季不从这儿取数)。

⛔ **不许把带季度后缀的产物(`APPROVED_*.json`、`charts_*.zip`、`REVIEW_*.md`)写进
`_charts\`** —— 2026Q3 我误建了 `_charts\out\` 往里堆,那样每季都会在共用目录里
积一层季度垃圾。那些一律进本季的 `_charts_snapshot\`。
⛔ 留痕必须在**出稿之后**写,而且是**定稿版**。2026Q3 第一次写留痕是在半途,
后来图改了六七处、账本改了十几处,留痕成了旧版 —— 交付前要重写一次。

**二、`series.json` 的 key 是稳定 slug,不是 exhibit 编号。**

编号每季会变(增删一张图后面全要重排),slug 不会。`exhibit_manifest.json` 定义文档顺序,
`exhibits.py` 从它推编号。**正文里一律写 `{{ex:slug}}` 占位符,绝不手写数字** ——
最后一步统一替换。手工维护 58 个编号,第二季必错。

**三、两阶段中间有一道硬门。**

出图和写正文之间必须停下来,把图和核对清单交用户逐项校对、签收之后才允许写正文。
理由:正文一旦写起来,一个错数会同时污染表格、图下 Note、跨节引用,
改一个数的代价从「重跑 2 分钟脚本」变成「重写半个章节」。
签收会记下 `series.json` 和每张 PNG 的 sha256;之后任何一张图重出过就自动失效。

**四、上一版报告只能用来对答案,绝不能当数据源。**

`Junson_Private_Credit_Report_*_v*.docx` 里的数是加工结果,属二手数据。
`pc_review_sheet.py` 有硬检查:`src` 命中 `_v\d` / 报告名 直接 fail。
上一版的正确用途只有三个:**跑完之后逐张对数值**、**抄样式**,
以及 —— 见下面第五条 —— **核对每张图的口径有没有被自己悄悄换掉**。

> **⛔ 基线的数会从侧栏、Note、题注这种「散文缝隙」漏进来。** 2026Q3 踩过实测:
> Ex 31 的图下 Note 写 `2031–2033 grew from US$195bn to US$209bn`(xlsx 精确值),
> 同一张图的**侧栏 bullet** 却还留着基线从 PDF 图上读的 `US$194bn to US$207bn` ——
> 一张图里两个数、差 2bn,而 `pc_crosscheck` 报了 0 矛盾。
> 原因是那句话本身写在账本的 `side_panel.bullets[].text` 里,而检查脚本会从账本的
> **散文字段**抽数字当「权威值池」—— 于是错数自己把自己验证成「命中账本」。
>
> 两条硬规矩,都已落到脚本里:
> 1. `pc_crosscheck.py` 的值池**只认数据字段**:`SKIP_KEYS` 加上 `text/title/conclusion/rule/…`,
>    字符串长度上限从 400 收到 80(只允许 `↑ +0.1pp`、`1,258 / 132%`、`0.30x` 这种带修饰的短值)。
>    **散文只能被检查,不能当判据。**
> 2. 改一个数就得**全图搜一遍这个事实**:题注、图下 Note、侧栏、正文、跨节引用,
>    一处不改就是一处矛盾。订正时在账本里留 `⛔ 订正记录(日期)` 写清原值来自哪、为什么换。
>
> **推论:正文里出现的每个数都要有账本里的「数据字段」做家,不能只活在散文里。**
> 同一轮还揪出三个只写在散文里的数(`333` 行数、Ares Emerald 的 `$370m / 27.3%`、
> MS 的 `134` 家软件借款人),已分别落成 `meta.screen.export_row_count`、
> `meta.comparator_set.excluded_examples`、`side_panel.cited_counts` —— 各带 `src`。

**五、口径由框架定死。可以改配色和画法,不许改「画的是什么」。**

> Alex 2026-08-24 的原话:「图不要改,你可以改颜色 改画法。但是该有什么日期 类型的数据,
> 你都必须要有。你只是在原本报告数据上增加一下检查审核的机制,而不是把数据删了,
> 或者重新换了个主题。」

每张 exhibit 画什么由 `references/report-spec.md` 定,**不由「我手上哪份数据更精确」定**。
2026Q3 踩过四个实例,四个都是同一个错:

| Exhibit | 框架要的 | 我换成了 | 为什么会换错 |
|---|---|---|---|
| 5 | 月度 refi/non-refi 堆叠 + % non-refi 线（KBRA,要从 tracker 图上测） | 季度 volume + 笔数 | 在 LCD wrap 的 xlsx 里找到了季度**精确值**,拿「精确」换掉了「口径」 |
| 6 | BSL vs 私募的 LBO **笔数** + % private LTM 线 | 只有私募一边的 volume + 笔数 | 同上;**BSL 对比整个丢了**,本节要回答的问题就没答 |
| 7 | 年度柱 + **最后一根 `26 YTD`** | 只到 2025 | YTD 的数在账本 `ytd` 里、正文也引了,但**忘了画上去** |
| 45 | 按行业的**持仓笔数**环比 | 基金 KPI 环比表 | 顺手把另一套数放进了这个位置 |

**出稿前必须做的口径核对**(交付清单的一部分,不是可选项):

```
# 58 个题注逐个跟基线比,相似度低的必须逐个解释清楚是「动态题注按本季数据重写」
# 还是「口径被换了」—— 后者一律算 bug
python3 - <<'EOF'
import re, zipfile, difflib
def caps(p):
    z=zipfile.ZipFile(p); x=z.read('word/document.xml').decode()
    ps=[''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', m.group(0)))
        for m in re.finditer(r'<w:p[ >].*?</w:p>', x, re.S)]
    d={}
    for t in (t.strip() for t in ps):
        m=re.match(r'Exhibit (\d+)\s*[:：]\s*(.*)', t)
        if m: d[int(m.group(1))]=m.group(2).strip()
    return d
B=caps('assets/baseline-2026Q3-EN.docx'); M=caps('out/<成稿>.docx')
for n in sorted(B):
    r=difflib.SequenceMatcher(None,B[n].lower(),M.get(n,'').lower()).ratio()
    if r<0.80: print(n, r, '|', B[n], '||', M.get(n))
EOF
```

题注只是入口。**题注一样也可能丢数据**(Ex 7 就是),所以还要查:
- 每张图的**期数与起止**跟上一版比有没有缩;基线出现过的 `YTD` / 部分期列有没有被砍掉
- 每张图的**序列条数**有没有少(基线题注里的 "with Junson funds"、"vs BSL" 这类词就是线索)
- 基线有侧栏/子面板的(2026Q3 的 Ex 31),侧栏还在不在

⚠ 但**侧栏和题注里的数字仍然不许从上一版抄** —— 恢复的是**结构与要回答的问题**,
数字必须用本季来源重新取。2026Q3 恢复 Ex 31 侧栏时,基线那三条引的
`~$430bn / $230–250bn / CDLI ~3x` 在本季文件夹里追不到出处,就全部换成了
本季 S&P 与 MS 报告里能追到的数,并逐条写了 `src`。

⛔ **对账结果要写进账本，不许只写「比过了」。** 契约里那行「口径对账」如果永远印同一句
「已并排比过四项」，它就只是个装饰 —— 比出出入的那几张反而看不出来。所以对账有出入的
exhibit 必须在账本里落 `_baseline_reconciliation`，`gen_contracts.py` 会把它逐条印进契约：

```json
"_baseline_reconciliation": {
  "compared":   ["横轴起止", "序列条数", "口径", "端点值"],
  "match":      ["…哪几项一致…"],
  "differs":    ["…出入是什么，用数字说，不用形容词…"],
  "conclusion": "采用哪一边、依据哪条铁律",
  "open_decision": "需要用户拍的选项（没有就省略）",
  "checked_by": "谁比的、哪天、证据是什么"
}
```

2026Q3 落了两条：
- **Ex 9** —— 基线三条线画满 4Q14–1Q26，本季 Lincoln/LSTA 只有 4Q17 起。把基线那张图逐像素量回来
  和源图对：4Q17–1Q22 段 Lincoln 差 −1.4…+1.0pp、LSTA single-B 在 2020–21 段差 +1.8…+2.3pp，
  只有末点一致 —— 基线那 12 期在文件夹里追不到出处，按铁律四不采用。
  ⚠ 同页右图 "Annual Total Returns" 确实从 Dec-14 起，但那是**回报**，序列里有 −8.8% 和 +18.7%，
  收益率不可能有 —— **两张图起点不同是口径不同，不是谁砍了谁**。
- **Ex 31** —— 基线 Note 写 "approximate readings from the source chart"，实际是 sheet 精确值；
  基线正文的 194 / 207 与 sheet 的 195.4 / 209.0 不符，本季订正为 195 / 209。

---

## 冻结行名分两类 —— 别把数据当契约

> ⛔ 2026-08-26 的教训：Alex 说「表头顺序都给我定死，以及最左边的这一列」，
> 我把 E38/E41/E42/E46/E48 的行名当**永久契约**冻死了。可那些行本来每季就会变
> （前十大投资重排、GICS 子行业进出、本季成交完全不同、组合新投退出、竞品基金集合变）。
> 冻死它们等于保证下季硬失败。他要的是**列序与写法**固定，不是「这十一个项目名永远不变」。

`row_labels_fixed.structural` 说清是哪一类：

| | 是什么 | 对不上怎么办 |
|---|---|---|
| `structural: true` | **固定词汇表** —— KPI 名、Fund snapshot 的条目名 | 硬失败。必须写 `_structural_why` |
| `structural: false` | **本季数据** —— 持仓名、行业名、本季成交、竞品集合 | 带 `_rq` 戳：**同季**对不上 = 出稿代码拼错了，硬失败；**跨季**对不上 = 数据本来就该变，打印差异让用户确认，**不失败**。必须写 `_rq` / `_varies_why` / `_frozen_part` |

`_frozen_part` 写的是**真正不许变的那部分**（列序、缩进结构、命名习惯、有没有前缀）。
`build_doc._fixcol()` 与 `pc_hdrcheck` 都按这个分流。

## `src_files` —— 结构化的源文件清单

⛔ **不许再从 `src` 散文里用正则抠文件名。** 真实文件名带空格、逗号、括号、中文引号，
正则要么截断（`"Macro Credit Views_ Dispersion, not disruption.pdf"` 在逗号处断）
要么把前面的中文吞进来（`"的数取自 PAG BRS …"`）—— 2026-08-26 两种都踩了。

每个 exhibit 落 `src_files: [相对本季文件夹的路径, …]` + `_src_files_rq`，由取数阶段维护。
`src_audit` 拿它**逐个**比对文件夹：

- **同季**缺文件 → ✗ 真错。⛔ 原来的判据是「任意命中即过」，多源 exhibit 少一个源会被静默放过
  （实测：券商表引用 9 份，抽掉 1 份照样判过，表上照印那一家）。
- **跨季**缺文件 → ⚠「本季没更新这张图」，走 `pc_intake.py` 的待决清单，不算错。

## §6.1 券商表跟文件夹走，不跟账本走

本季文件夹里有几家券商的研报就出几列（判据是 `rows[*].file`）。某一家一份都没有 →
这一列不出，进 `DROPPED_HOUSES`，交付说明必须写「X 家本季未提供」。
开头那句 "N sell-side reports across M houses" 的数字是现算的。
⛔ 另有一道门：正文点名的券商必须在本季表里 —— 少了一家而正文那句还留着，出稿终止。

## 每个数都要有书面来源(这条不变)

报告主人要求**每个数的出处都写下来**,落在两处:

1. **文档里** —— 每张 exhibit 带 `Note: ... Source: ...`,而且必须区分数据质量:
   - *exact / as-labelled / as-disclosed* —— 直接取自源表格或标签
   - *digitised approximations* —— 从源图上读的(只能说趋势)
   - *Junson calculations* —— 分位数、IQR、环比、投资人层指标
   - *web research* —— 注明出版方与日期
2. **账本里** —— `series.json` 每个 exhibit 有图级 `src`,差异点有点级 `src`。
   ⛔ **`src` 必须含文件名,且不许只靠 slide 号定位** —— MS Tracker 的 slide 号每季一定挪。
   要写 slide 的**标题文字**,页码只做辅助。`pc_review_sheet.py` 会查这两条。
3. 出稿时从账本导出 `sources_ledger_<quarter>.md`(一行一个数),和 docx 一起交付。

**追不到来源的数不进报告。**

---

## Inputs

- **本季文件夹**(必需):`.../Private Credit/<YYYYQn>/`,含 `Broker/` `Fund/` `Market/` `Competitor/`。
- **账本**(必需):`<父目录>\_charts\series.json`。第一次跑就从 `series_template.json` 建。
- **上一季成稿**(可选,只用来对答案):不参与取数。
- **联网**:每次都跑,补文件夹填不了的槽 —— 见 `references/source-map.md` § Web research。

---

## 阶段一 · 出图与核对清单

### 1. 确认运行参数

一轮问清(已经说过的不要再问):
- **季度标签**(如 2026Q4)—— 决定标题、页眉、文件名、账本 `meta.rq`
- **语言**:仅英文,还是英文 + 中文

### 2. 清点与暂存来源

`device_list_dir` 递归列本季文件夹,`device_stage_files` 全部暂存(大就分批)。
按 `references/source-map.md` 的常见来源清单报告找到了什么、缺了什么。
**缺料不致命,但绝不静默。** ⛔ Alex 2026-08-26:「不要太死板哦」—— 缺一两份源报告是常态。

**先跑 `python3 pc_intake.py`**（取数之前，不是之后）：它拿每个 exhibit 的 `src_files`
反推「本季需要哪些来源」，跟文件夹里实际有的比对，列出缺料清单。然后跑
`python3 pc_intake.py --apply`：靠缺失文件的 exhibit 写进账本 `meta.skipped`，本季整块删掉，
不问用户、不标 not updated、不沿用上季值 —— 规则见本文开头「缺料」一节。

**硬失败只留给三类**：账本自相矛盾（恒等式不过）、纸面与账本不一致、出稿代码拼错。
缺一份源报告**不属于**这三类。

**某个数本季没披露**（报告给了，但里面某个指标不再披露）：用 `build_doc.qoq_cells()` ——
本季格印 `n/d`、QoQ Δ 印 `n/a`；反过来上季缺本季有则 Δ 印 `new`。
⛔ **绝不拿另一头顶上**。有 `n/d` 的 exhibit 必须在账本写 `_gap_note`，否则出稿终止。
`pc_hdrcheck` 另外核一条：有一头是 `n/d`，Δ 就必须是 `n/a` 或 `new`。

### 3. 取数写进账本

⛔ **每张图必须能追到本季文件夹里的具体文件路径**（Alex 2026-08-24）。
顺序是：先在文件夹里找（`Broker/` `Fund/` `Market/` `Competitor/`）→ 本来就靠联网的槽才联网 →
**找不到就按「缺料」跳过并删掉，不许自己拍、不再发对话框**。
`src` 里要写到 `<子目录>/<文件名>` + **slide 的标题文字**（不写页码 —— MS tracker 的页码每季都挪）
或 **sheet 名 + 列名**。取完数立刻跑 `scripts/src_audit.py`，58 张必须 58 张都能追到。

读 `references/source-map.md`(哪个来源喂哪一节)+ `references/report-spec.md`(每张图的定义)。
PDF 用 pdfplumber/pymupdf 文本抽取 + 图页读图;xlsx 用 openpyxl/pandas。

**每抽一个数,立刻写进 `series.json` 对应 slug,同时写 `src`。** 不要先攒着后面补。

三层数据的基准日各不相同,**必须分别填进 `meta.as_of`**:

| 层 | 基准 | 来源 |
|---|---|---|
| market | 本季或上季(看数据商) | MS Tracker / S&P / PitchBook·LCD / KBRA / Fitch |
| fund | **通常滞后市场层 1–2 季** | 三份投资人报告 |
| competitor | PitchBook **导出日** | Competitor/ 的 xlsx |

基金报告读得最细(见 `source-map.md`)。Competitor 那节从 PitchBook 原始列**重算**
cohort 中位数、分位数、IQR,不许抄上季。

### 3b. 外部数据源：一次找定，之后只追加

⛔ **凡是需要联网取的外部序列，第一次找到就把整段历史冻结进 `series.json`，并把「下季从哪儿取」写进 `aux`。**
下一季只追加新增的那一期，历史点一个都不重取（Alex 2026-08-24）。

2026Q3 定下来的一条（图 9 的 HY 对照线）：

| 项 | 值 |
|---|---|
| 序列 | `BAMLH0A0HYM2SYTW` — ICE BofA US High Yield Index **Semi-Annual Yield to Worst** |
| 取数地址 | https://fred.stlouisfed.org/series/BAMLH0A0HYM2SYTW |
| 冻结区间 | 4Q14–1Q26 共 46 个季末值，已在账本 `ret_yield_vs_singleb.lines` 里 |
| 原始文件 | `_charts/ICE_BofA_US_HY_YTW_20142026.xlsx`（日频 3,302 行，与账本一起归档） |
| 下季怎么做 | 从上面那个地址取**新增的那一个季末值**追加。⛔ 不许重取 46 期历史 |

⚠ 两个坑，写在这里免得下季再踩：

1. **口径是 YTW，不是 effective yield。** 别取成 `BAMLH0A0HYM2EY`（两个 ID 差一截，很容易拿错）。
   上一版成稿的图例写 YTW 但值实际是 effective yield，本季已按真 YTW 改正。
2. **FRED 自 2026-04 起只保留 3 年滚动窗口** —— ICE 收回了转载授权，页面写 "Starting in April 2026,
   this series will only include 3 years of observations"。所以更早的历史**只能靠账本冻结**，
   FRED 上已经取不到了。这正是账本「只追加不重算」要解决的情况。
3. **授权边界**：ICE 指数数据仅限内部使用，未经书面许可不得对外转载。本报告的免责声明写的就是
   "For internal research use only. Not for distribution outside Junson Capital"，落在允许范围内。
   ⛔ 这条序列不许出现在任何对外版本里。

**通用规矩**（不只这一条）：联网取来的序列，`aux` 里必须有 `url` + `method` + 至少两个独立校验点，
并写明「下季只追加」。取数前的顺序永远是：**本季文件夹 → 联网 → 都没有就按「缺料」跳过并删掉**。

### 3c. `series_bank`：找定了就存，哪怕本季没图在画它

⛔ **凡是费了力气从源图里量出来、或从网上找定的整段序列，一律进账本 —— 不管本季有没有 exhibit 在用它。**

> Alex 2026-08-24：「历史数据点记得都写进账本」「以后重要的点就可以放在 series 里，
> 不用以后季度重新找了」

账本顶层因此有 `series_bank`，和 `exhibits` 平级。它存**已经找定、跨季只追加**的序列：

```json
"series_bank": {
  "ms_p41R_annual_total_returns": {
    "_what": "Annual (T12M) total returns：Lincoln Senior Debt Index vs Morningstar LSTA
              US Single B Loans。⚠ 这是**回报**，不是收益率 —— 与收益率序列永远不许互填。",
    "src": "…tracker.pdf，p41，slide \"Performance | Private Versus Public Credit Yields
            and Returns\"，页面【右】半边那张 \"Annual Total Returns\"",
    "periods": ["4Q14", …, "1Q26"],
    "_method": "像素还原：y 用 9 个刻度标签行标定，0% 取 0 轴灰线中心；x 用 23 个横轴标签…",
    "_anchors": {"1Q26 Lincoln": {"measured": 8.73, "source_text": 8.7, "diff_pp": 0.03}, …},
    "_traps": ["图例白底方框里有线样，不排掉会量出 26.4% 的假值", …],
    "source_latest_period": {…},
    "_used_by": "本季没有 exhibit 画它；存进来是因为它是全文件夹唯一能回到 4Q14 的 Lincoln 序列。"
  }
}
```

必填：`_what`（含口径警告）、`src`（文件 + slide 标题 + 左/右哪半边）、`_method`、`_anchors`、
`_traps`、`source_latest_period`、`_used_by`。

⚠ **`_what` 里的口径警告不是客套。** 2026Q3 踩过：tracker p41 的左图是**收益率**（Dec-17 起）、
右图是**回报**（Dec-14 起）。回报序列里有 −8.8% 和 +18.7% 这种值，收益率序列不可能有 ——
两张图起点不同是**口径不同**，不是谁砍了谁。上一版成稿把图 9 标成 "yields" 却混进了别的数，
2014–15 段整个是错的。**拿一个口径的序列去补另一个口径的历史，是实质性错误。**
`series_bank` 的条目一旦被误当成同口径来源，比不存更危险，所以口径警告写在第一个字段。

最终定稿（Alex 2026-08-24）：图 9 画 p41 **右**图的两条回报线 + ICE HY **YTW** 收益率线，
**起点写死 2015/12**（源图从 4Q14 起，那 4 期不画，全量冻结在 series_bank） —— 「yield 跟 annual total return 可以画在一起，但不是说这两个是
一个意思」，所以题注、图例、Note 三处各自标明口径。收益率序列（p41 左，4Q17 起）退到
`series_bank.ms_p41L_yields`，正文只引用其明标水平。

### 4. 联网补槽

按 `source-map.md` § Web research 填。每个联网来的数在账本里记出版方 + 日期,
exhibit 的 Note 里写 "web research"。

### 5. 出图

读 `references/style-guide.md` § Charts,**用 `scripts/junson_style.py`**,不许手工调样式。
  需要从研报图里读数的,先读 `references/digitising.md`,工具是 `scripts/digq.py` / `scripts/dig_lines.py` —— **不许目测估数**,每张测出来的图都要有锚点校验和残差记录。

```python
import junson_style as js
fig, ax = js.figure('pair', h=2.4)      # 并排 3.35 in ｜ 'solo' = 6.74 in ｜ 'tall' = 5.30 in（窄高单图，Word 居中插）
...
js.save(fig, 'charts/mkt_fundraising.png')   # 自动跑版面锁 + guards
```

- **画布宽 = Word 插入宽(1:1)** —— 图内写多少 pt 纸上就是多少 pt。`js.save()` 会硬拦。
- **图内不放标题、不放脚注** —— 题注和 Note/Source 都在 Word 侧。
- 折线描点直径 = 线宽 × 2(`js.ms(lw)`);图内数值标签一律水平。
- **重画源图,不许截图。** 从图上读的序列在 Note 里诚实标 digitised。

### 5b. 末期：源文件走到哪，图就画到哪

⛔ **每季更新必须先去文件夹里看源文件更新到哪一期，再决定图画到哪一期**（Alex 2026-08-24）：

> 「以后不管每次更新都是要去文件路径下面的文件夹看最新的报告资料/excel 更新到哪一期，
> 或者给的 pitchbook 的资料画到那一期来决定的。」

账本里每张时间轴图都有 `source_latest_period`：

```json
"source_latest_period": {
  "this_quarter": "May-26",              // 本季**该口径的源文件**走到哪一期
  "chart_ends": "May-26",               // 图实际画到哪一期（必须等于 this_quarter）
  "how_to_find_next_quarter": "Market/MS Private Credit 1Q26 tracker.pdf，slide
     \"Deal Activity | Refinancing and New Money Both Slowed in May\" 右上图横轴最后一个月",
  "folder_freshest": {                  // 本季文件夹里**同主题**最新的料走到哪一期
    "period": "2Q26",
    "file": "q2-...-quarterly-wrap.xlsx，sheet \"01 DL Volume\"",
    "same_measure": false,              // 是不是和本图完全同口径
    "why_not_used": "那张 sheet 是季度直贷总量，本图是月度 refi / non-refi 拆分 ——
       全文件夹只有 tracker（1Q26 deck，月度到 May-26）给这个拆分。"
  }
}
```

⛔ **只声明「源文件走到哪」不够，必须同时声明「文件夹里最新的料走到哪」。**
Alex 2026-08-24：「图5图6图7 全部都不是最新的数据…你自己看看其他的有没有更新的到最新的数据？
**为什么 skill 连这个最简单的一点都没规定**」。当时数据其实没取错，错在**读者看不出末期是源头的
极限还是取旧了** —— 三条时间线（图末期 / 该口径源上限 / 文件夹最新）必须都摆在账本里。

出图后跑 `python3 pc_period_check.py`，它判五件事：

| 判据 | 结果 |
|---|---|
| `this_quarter != chart_ends` | ✗ 不通过 |
| 时间轴图漏 `source_latest_period` | ✗ 不通过 |
| 时间轴图漏 `folder_freshest` | ✗ 不通过 |
| `folder_freshest` 比图末期新且 `same_measure=true` | ✗ **硬错** —— 文件夹里有同口径新数没用上 |
| `folder_freshest` 比图末期新、`same_measure=false`、但 `why_not_used` 空 | ✗ 不通过 |
| 末期比本季早两年以上 | ? 点名人工确认（例：Ex 12 源表只到 2024 vintage，属正常） |

横轴不是时间的图（到期年份分档、行业、基金名…）在账本里标 `"axis_kind": "category"`，检查会跳过。

**Note 里也要写「为什么停在这里」。** 账本对了但 Note 不写，读者一样看成取旧了。
2026Q3 的写法（照抄这个语气）：

> The monthly series ends in May 2026 because its only source in this quarter's folder is
> Morgan Stanley's 1Q26 tracker, whose monthly panel runs through May 2026. The 2Q26
> PitchBook | LCD wrap carries quarterly direct-lending volume through 2Q26 but not the
> refinancing / non-refinancing split, so no later print of this measure exists.

2026Q3 实测：20 张时间轴图全部 `chart_ends == this_quarter`；其中 8 张 `folder_freshest`
比图末期新但口径不同（Ex 5/6/10 的 LCD wrap、Ex 12 的契约问卷、Ex 26–29 的 Barclays 2Q26
七家 BDC 单家读数），八张各自写了 `why_not_used`，也都写进了 Note。

⛔ **末期一定要上横轴刻度。** 抽稀标签时最后一期没被选中，图上就读成数据停在更早一期 ——
2026Q3 踩过，而且不止一张：图 5 数据到 May-26 但末标签停在 Aug-25、图 6 停在 2Q25、
图 54 停在 2025、图 53 停在 '24。四张都是「数据是新的，图看起来是旧的」。
刻度下标一律用 `js.tick_idx(len(periods), step)` 生成，画完用 `js.assert_last_ticked(ax, n)` 兜底 ——
末期不在刻度里直接抛错。

### 6. ⭐ 自己逐张看一遍

`guards.check()` 只能抓 bbox 级的压叠,抓不到「两个标签贴太近读不清」「数字压在折线上」
「图例盖住末点」。**打开 `charts/` 里每张 PNG 看一遍,发现文字重叠就重做那张图** ——
调偏移、隔点标注、抬 y 轴上限、图例挪出图外。**不许用 `skip_check=True` 绕过。**

### 7. 出核对清单

```
python3 pc_review_sheet.py --strict
```

生成 `out/REVIEW_<quarter>.md`,含:算术恒等式(占比加总、堆叠分项=总计、分位数域、
cohort 样本数、基准日错位、src 可追溯性)、**带数据主张的 15 个题注**、本季新增的每一个数、
以及覆盖检查(哪个 exhibit 一行数据都没出)。

**恒等式不通过不许进门。** 覆盖检查里点名的 exhibit 必须解决。

### 8. 🚪 门 —— 停在这里

把图 + `out/REVIEW_<quarter>.md` 交给用户,**明确说「等你签收之后我才开始写正文」**。

用户说签收后:

```
python3 approve.py --sign      # 记 series.json 与每张 PNG 的 sha256，并归档一份账本原样
```

⛔ **签收只能由用户说。不许自己代签,不许跳过这一步。**

---

## 阶段二 · 正文与出稿

### 9. 验签

```
python3 approve.py --check     # 不通过就退回阶段一
python3 approve.py --diff      # --check 失败时先跑这个，看清到底改了哪个字段
```

`--check` 只会说「账本被改过」,`--diff` 才说清改了什么,并且分成两类:

| 改动落在 | 后果 |
|---|---|
| 会画到图上的字段(`stacks` / `lines` / `rows` / `vals` / `history` …) | 图必须重出、清单必须重交、必须让用户重签 |
| 只是文字或派生字段(`note` / `src` / `aux` / `_gap_note`) | 图不用重出,但仍要把改动摊给用户看过再 `--sign` 补记录 |

⚠ **阶段二自己往账本里写派生值(`aux`)会让签收失效** —— 这是设计如此,不是 bug:
凡是要印进正文的派生数(平均单笔、占比、合计),都得先落进账本再从账本读,
落进去账本就变了。正确做法是**写完 `aux` 之后立刻 `--diff` 给用户看一眼、请用户补签**,
不是自己 `--sign` 蒙过去。

### 10. 写正文

先读 `references/prose-spec.md` —— **逐节行文契约**:每节几段、每段多少词、论证顺序
（先水平、再变动、后归因）、来源代号（L=账本读 / N=当季新抽 / W=联网 / H=问用户）、
禁止项、以及从上一版成稿挖出来的标杆句式（**摘录里的数字全部作废,只学写法**）。
再读 `references/report-spec.md` —— 逐节内容契约:章节顺序、每段论证什么、每张 exhibit 的定义。
两份都照做。写作规则:

- **凡 exhibit 上出现过的数,一律从 `series.json` 读,禁止为写正文再抽一遍。**
  否则图上写 2.8%、正文写 2.9%,两处各自自洽,通读发现不了。
- 更新数字**和**叙述。数据换方向,文字必须跟着换方向 —— **绝不把上季的形容词留在本季的数上**。
- **加粗:每段至多一个「头条数字」。** ⛔ Alex 2026-08-25 纠正 —— 这条规矩原文写的是
  「关键数字加粗」,我照着把几乎每个数都加粗了(正文 369 处 ≈ 6 处/段,是基线的 12 倍),
  满屏黑点反而没有重点。基线成稿实测**只有 0.78 处/段(含标题行)**:每节一个头条数字
  (US$2,557bn / 508bp / 4.37% / 5.7x / 2.8% / 14.7% 这类)+ bullet 的引导短语
  (`Quarter activity:`、新闻条导语、TWSK 的判断句)。`build_doc.py` 的 `_bold_policy()`
  机械保证每段只留第一处,`pc_docxcheck` 查密度(>1.6 处/段判不通过)。
- **引用 exhibit 一律写 `{{ex:slug}}`**,不写数字。
- **15 个带数据主张的题注**(`caption_dynamic=true`)必须按本季数据重写,
  且题注里每个数字都要能在账本里找到。
- **第 8 节开头必须显式声明基金层的基准日滞后** —— 例:
  "based on each manager's <季> investor report; all valuations are as of <日>
  and therefore predate the <季> public-market repricing discussed above."
- **Things We Should Know 恰好五条**原创观察,是框架各节**没覆盖**的,每条以对 Junson 组合的
  含义收尾。这是全篇最有价值的一节,**最后写**。
- Related news 每条来源**必须是超链接,且指向那一篇的完整 URL**。
  只到域名不算 —— 用 `docx_helpers.hyperlink()`,它会硬拦。拿不到准确网址就删掉这一条。
- Sentiment 那张表:**本季文件夹里实际有的每份 broker 报告各占一列**,带 QoQ change 行。

### 11. 出 docx

读 `references/style-guide.md` § Document,用 `scripts/docx_helpers.py`。
`assets/baseline-2026Q3-EN.docx` 是**版式**真值 —— 段落/表格/页眉的**构造**拿不准可以解开它照抄。
> ⛔ 但「同事那版长什么样」这类问题不许靠打开 docx 回答 —— 表头、最左列、图形状、纵轴刻度、
> 列宽这些都已经是账本里的字面量(`_frozen_colleague_formats` 列了全部),照账本做。
> ⛔ 但它同时是一份**上一版报告**:里面的任何数值都不许当来源。
> 2026Q3 的实例:同事的 `CA_snapshot_2026Q3.json` 里有 Guggenheim 的 IRR 9.3 / TVPI 1.20 / DPI 0.18,
> 而 Guggenheim 季报里根本没有回报指标 —— 那三个数在本季文件夹里找不到出处。
> 默认处理是**留空并写明缺口**(见 `series.json` 的 `_gap_note` 与 `history_gaps`),不是拿旧值顶上。
> 后续（Alex 2026-08-24 拍板）:那三个数是同事**用 Guggenheim 内部投资报告算的**,不是抄报告,
> 授权用于 **Ex 49/50**;账本 `_gug_decision` 记了授权原话与出处,Note 写
> "computed internally by Junson from the manager's internal investor reporting"。
> 这不推翻铁律四 —— 界线是:**追不到源的数不许用;追到「内部计算」这个源、且报告主人确认过的,**
> **按内部计算口径标注后可用。**（Alex 随后把授权扩到 §9 全部 Guggenheim 位置,并给了上游:
> AID Portfolio Tracking Master 的 "Guggenheim" sheet,投资人层月度跟踪。）
>
> ⛔ **每季怎么拿这几个数(Alex 2026-08-24 定死,两条都是硬规矩):**
> ① **不许从 AID Portfolio Tracking Master 取数** —— 那份 excel 不进季度文件夹,2026Q3 当场核对
> 用过一次就到此为止;它里面的数**不能存进账本**。
> ② **靠账本里的清单在运行时问用户**（有人值守时照硬要求十八发对话框问；问了没给、或无人值守（如研究面板的 AI 生成）就按「缺料」删掉这些格与叠加点）—— `series_bank.gug_internal_returns.fill_checklist`
> 逐张列了哪几张图有 Guggenheim 的坑(8 处:记分卡三行、动量两张、轨迹两张、附录三个叠加点)、
> 每处要问什么、每季问还是年度问(附录 Ex 54–58 按 report-spec §9.6 是 **annual refresh**,
> 别当季度活)。**取数阶段必须把这个清单逐项过一遍** ——
> 不照清单对就会漏填,这正是清单存在的原因。问时一并确认:截至哪一期、IRR 口径
> (同事用 YTD 年化;PitchBook cohort 是成立以来口径,用哪个让用户拍板)。
> 用户不给数就删掉这些格与叠加点（「缺料」），绝不拿上季的值顶。数据质量标注不变:
> computed internally by Junson, marked †。

```python
import exhibits, docx_helpers as H
EX = exhibits.load()
H.exhibit(doc, EX.caption('mkt_aum_by_channel', y0=2015, y1=2026),
          'charts/mkt_aum_by_channel.png', note='Note: ...  Source: PitchBook.')
for L, R in EX.pairs():
    H.exhibit_pair(doc, (EX.caption(L), f'charts/{L}.png', noteL),
                        (EX.caption(R), f'charts/{R}.png', noteR))
body_text = exhibits.resolve(body_text)      # {{ex:slug}} -> Exhibit N
```

关键机械细节:并排是无框线 1×2 表格,每格 题注 → 图 → Note;数据表深蓝表头
(`#1F3B5B`,白粗体 7.5pt)+ `#C9D2DC` 细网格 + **表头行带 `w:tblHeader`**;
色值一律从 `scripts/palette.py` 取(`DOCX` / `DOCX_TEXT`),不在代码或文档里另写 hex;
**单图插入宽上限 17.12cm**(基线成稿有两张 17.53cm 溢出了页面,`H.exhibit()` 会拦)。

### 12. 更新账本的追加项

把本季的 `percentile_history` 追加一期(不改历史),写回 `series.json`。
`ca_traj_*` 那两张轨迹图之后可以只靠账本重建。

### 13. 出稿后五道自查 + 导出来源清单

```
python3 pc_docxcheck.py  <成稿>.docx     # 纸张/边距/字号/图宽/1:1/表格/编号/链接/占位
python3 exhibits.py --check <成稿>.docx   # 编号连续、无断号重号、无残留占位、题注无未填占位
python3 pc_crosscheck.py <成稿>.docx     # 全文数字回账本核，抓「近似但不相等」
python3 pc_lastpoint.py --strict         # 末点：账本里有值就必须画出来（YTD 也要画）
python3 pc_factcheck.py --strict         # 图内一致性：一张图的散文数值必须在这张图的数据字段里
python3 export_sources.py                # 从账本导出 out/sources_ledger_<quarter>.md
python3 pc_period_check.py               # 末期核对：图末期 / 该口径源上限 / 文件夹最新，三条线都要对上
python3 period_evidence.py               # 末期证据表：逐张摆「图到哪 / 源上限 / 文件夹同主题最新」，交用户看的
```

**五个都要 ✗ 为 0 才能交稿。** 抽查不算数 —— 几百个数抽十个的覆盖率是 3%。

**再加一道:按铁律五跑口径核对**(58 个题注比一遍 + 期数/序列数/侧栏三查)。
三道自查全绿也挡不住「口径被换掉」—— 它们只查版面、编号和数字回账本,
不查「这张图画的还是不是同一件事」。

⚠ **动态题注的 `{cq}` / `{tot}` 这类花括号占位是会印到纸上的。**
2026Q3 踩过:5 个动态题注因为 `caption()` 调用时没传值,`exhibits.py` 当时只在
「传了 fmt 但缺键」时报错,一个 fmt 都没传就直接跳过格式化 —— 花括号原样进了成稿,
而两个检查器都只查 `{{ex:...}}`,查不出来。现在两处都堵上了:
`caption()` 只要发现残留花括号就抛错,`exhibits.py --check` 也单独查这一类。
**动态题注的文本一律取账本的 `caption_rendered`**(那是本季重写过、
且被核对清单逐个数检查过的版本);manifest 里的模板只作兜底,两处不一致直接报错。

### 14. 交付

`SendUserFile` 发 docx + `sources_ledger_<quarter>.md`,然后 `device_commit_files` 写回:

| 写到哪 | 写什么 |
|---|---|
| **`Private Credit\Test\`** | 成稿 docx、`sources_ledger_<Q>.md` ⛔ 不许写到父目录根(Alex 2026-08-25) |
| `Private Credit\_charts\` | 更新后的 `series.json`(**原地覆盖,不改名不加季度后缀**) |
| `Private Credit\<Q>\_charts_snapshot\` | `charts_<Q>.zip`、`series_<Q>_signed.json`、`APPROVED_<Q>.json`、`REVIEW_<Q>.md`、`exhibit_contracts_<Q>.md` |

落点不许手打,从解析器拿:

```python
import pcpaths as P
T = P.deliver_targets(PC_ROOT)      # PC_ROOT = 用户给的 …\04 Research\Private Credit
# T['report']   → …\Private Credit\Test\Junson_Private_Credit_Report_<Q>_EN_v<n>.docx
# T['sources']  → …\Private Credit\Test\sources_ledger_<Q>.md
# T['ledger']   → …\Private Credit\_charts\series.json          ⛔ 不进 Test
# T['snapshot_dir'] → …\Private Credit\<Q>\_charts_snapshot\
```

一两句话说清落在哪、哪些 exhibit 因缺料没更新。
⛔ 留痕在**这一步**写(定稿之后),不许中途写完就不管 —— 见铁律一的目录约定。
⛔ 交付完要**自己列一遍目标目录确认文件真的在那儿** —— 2026Q3 踩过:
说了「已改」但没发文件,用户看的还是旧版(见第零条那节的教训)。

---

## 用户说「不用重新取数」时

改了样式或版面之后不需要重跑取数 —— 出图只读账本,几十秒。照做,但三件事不许省:

1. 出图脚本必须按当前 `style-guide.md` 重新生成,不许复用上次那份 ——
   版面规则改了而出图脚本没改,等于什么都没改。
2. 不许复用旧 PNG。判据是画布宽:必须是 3.35 / 6.74 / 5.30 in（pair / solo / tall）。
3. **PNG 变了签收就失效**,`approve.py --check` 会拒绝。重新出清单、重新让用户签。

---

## 文件索引

| 文件 | 什么时候读 |
|---|---|
| `references/exhibit_contracts.md` | **出图前必读 —— 58 张图逐张的完整契约**：位置/形状/出图调用/数据源（`<子目录>/<文件名>` + slide 或 sheet 定位）/取数与构成/锚点校验/脚注模板/口径对账。同事原来那份 spec 是 5 行一张，2026Q3 踩的 15 处错全在它没写到的字段上；这份是 ~28 行一张，照我们 OTF 那份的标准写的 |
| `references/prose-spec.md` | **写正文前必读 —— 逐节行文契约**：段数/词数/论证顺序/来源代号/禁止项/标杆句式（从上一版成稿挖出，数字作废只学写法）。2026Q3 的 Methodology 段教训催生的这份文件 |
| `references/report-spec.md` | 写正文前 —— 逐节内容契约 + 快照 schema（图表口径见 `exhibit_contracts.md`；行文写法见 `prose-spec.md`） |
| `references/source-map.md` | 取数前 —— 来源→章节映射、常见来源、联网清单 |
| `references/style-guide.md` | 出图/出稿前 —— 配色、字体、表格与图表规格 |
| `references/ledger.md` | 建账本前 —— `series.json` 的形状与恒等式 |
| `scripts/pc_intake.py` | **取数之前**跑 —— 清点本季来源，缺的列成待决清单交用户选（不失败） |
| `scripts/pc_audit.py` | **签收之前跑一次** —— 一次性过 6 组自动检查：账本完整性、占位符残留、图与 manifest 对齐、配色规则、脚本可用性、文档与代码一致性 |
| `references/digitising.md` | **从研报图里读数前** —— 先找明值再测量、标定/锚点/交叉校验的做法，以及图例色块、同色双线、轴上限裁剪这三个必踩的坑 |
| `exhibit_manifest.json` | 增删 exhibit 时 —— 唯一定义文档顺序的地方 |
| `assets/baseline-2026Q3-EN.docx` | 版面**构造**拿不准时 —— 2026Q3 定稿,**仅样式与写法**真值;数字一律不许从它抄 |
| `assets/colleague-template-2026Q3-EN.docx` | ⛔ **运行时不打开** —— 同事那份模板,版式已抄成字面量落在账本 `_frozen_colleague_formats`;这份 docx 只在人工溯源某个字面量的出处时回看 |
| `scripts/junson_style.py` | 每个出图脚本都 import |
| `scripts/docx_helpers.py` | 组装 docx 时 import |
| `scripts/exhibits.py` | 编号与题注的唯一来源 |
| `scripts/guards.py` | 由 `js.save()` 自动调用 |
| `scripts/pc_review_sheet.py` | 阶段一末 —— 恒等式 + 核对清单 |
| `scripts/approve.py` | 门 —— 签收 / 验签 / `--diff` 看账本改了什么 |
| `scripts/export_sources.py` | 交付前 —— 从账本导出 `sources_ledger_<quarter>.md`,一行一个数 |
| `scripts/pcpaths.py` | **每个要碰文件的脚本都 import** —— 季度与路径的唯一解析入口:`rq()` / `quarter_dir()` / `one(<通配符>)` / `report_name()`。找不到本季文件夹就报错,不静默退回上一季 |
| `scripts/pc_stalecheck.py` | **每季第一件事** —— 换季体检:账本 meta 是否齐、出图/出稿脚本里有没有锁在上一季的期名标签、meta 与账本末期是否自洽。不通过就别往下跑 |
| `scripts/pc_period_check.py` | **出图后跑** —— 图末期 vs 该口径源上限 vs 文件夹同主题最新；漏 `source_latest_period` 或 `folder_freshest` 都判不通过 |
| `scripts/period_evidence.py` | **交图给用户时一起交** —— 逐张列「图到哪一期 / 源上限 / 文件夹里同主题最新」，用户一眼看出是源头到这儿还是取旧了 |
| `scripts/src_audit.py` | **取数后立刻跑** —— 逐张核 `src` 有没有指到本季文件夹里真实存在的文件；追不到就是必须补的洞 |
| `scripts/gen_contracts.py` | 出图后跑 —— 从账本重生成 `exhibit_contracts.md`，保证契约与实际做法不脱节 |
| `scripts/pc_crosscheck.py` | 阶段二末 —— 全文数字回账本核 |
| `scripts/pc_docxcheck.py` | 阶段二末 —— 成稿版面自查 |
| `scripts/pc_lastpoint.py` | 出图后 + 出稿后 —— 末点:账本里有值就必须画(YTD 也要画),留空要指到源文件 |
| `scripts/pc_factcheck.py` | 出图后 + 出稿后 —— 图内一致性:一张图的散文数值必须在这张图的数据字段里 |
