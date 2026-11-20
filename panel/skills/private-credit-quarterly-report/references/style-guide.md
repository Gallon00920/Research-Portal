# Style guide — exact formatting specs

Ground truth: `assets/baseline-2026Q3-EN.docx`. If anything below seems ambiguous, unzip
the example (`unzip -d unpacked baseline-2026Q3-EN.docx`) and inspect
`word/document.xml` / `word/styles.xml` directly.

## Palette (used in both document and charts)

> **文档侧配色也走 OTF（Alex 2026-08-21 定）。** 唯一来源是 `scripts/junson_style.py` 里的
> `DOCX` 字典，`docx_helpers.py`（出稿）与 `pc_docxcheck.py`（校验）都从它 import ——
> 不许在这两个文件里另写常量。数值出自 OTF skill 的 `references/08_tables.md`：
>
> | 用途 | 值 |
> |---|---|
> | 全部框线（含内框线），sz=4 = 0.5pt single | `#C9D2DC` |
> | 表头行底色（白字加粗）| `#1F3B5B` |
> | 正文字色 | `#000000` 纯黑 |
> | 表下小注 | `#5A6B7B` 灰斜体 |
>
> ⚠ 表头底色 `#1F3B5B` 比图里的标题深蓝 `#16283F` **浅一档**，这是 OTF 明文规定的
> （白字要在底色上读得清），不是不一致，别去「统一」成 `#16283F`。
>
> ⛔ 同事 v2 的旧值 `#BFC7D1`（框线）与 `#1F3864`（表头）**已作废**。
> 这两个值曾经改过一次又被覆盖回去，导致同一份 Word 里图和表两套深蓝；
> 现在集中到一处 + `pc_audit.py` 有同源检查，不会再漂。

> ⛔ **下面这张表是当前有效值。唯一来源是 `scripts/palette.py`** ——
> 出图 (`junson_style`)、出稿 (`docx_helpers`)、校验 (`pc_docxcheck`) 都从它 import。
> 不要在任何脚本或本文档里另写 hex。v2 旧值到新值的逐项对照在 `palette.V2_TO_OTF`。

### 图表侧 —— Alex 2026-08-25 指定的六色，**按顺序取**

| 位 | Hex | RGB | palette.py | 角色 |
|---|---|---|---|---|
| C1 | `#1F2B44` | 31, 43, 68 | `C1` / `NAVY` | 主序列 / 深色柱 |
| C2 | `#7A9CB7` | 122, 156, 183 | `C2` / `GOLD` / `RHS` | 第二序列 / 右轴叠加线 |
| C3 | `#2EA69F` | 46, 166, 159 | `C3` / `BLUE` | 第三序列 |
| C4 | `#6B5FA8` | 107, 95, 168 | `C4` / `GREYBL` / `HILITE` | 第四序列；兼自家基金高亮 |
| C5 | `#A1B6CC` | 161, 182, 204 | `C5` / `LIGHTBL` | 第五序列 |
| C6 | `#2F7D51` | 47, 125, 81 | `C6` / `SLATE` | 第六序列 |

多序列图一律 `js.SERIES[i]`。⛔ 角色名（NAVY / GOLD / …）只是**位次的别名**，
字面意思已经不准（GOLD 现在是蓝灰），别照名字挑颜色。

图内 chrome（不参与顺序）：`AXIS #9BA6B5` 轴框线、`GRID #E3E7EC` 网格线、
`GRAY #5A6B7B` Note/Source、`BODY #000000` 轴与数据标签、`PIE_OTHER #D7DEE6` 饼图 Other、
`BANDS` 评级带底色（由 C5/C2 派生的浅→深四档）。

### 文档侧 —— 与图表色**解耦**，2026-08-25 换图表色时没有跟着变

| Role | Hex | palette.py |
|---|---|---|
| Navy —— 标题 / 小节标题 / 题注 / 页眉下横线 | `#16283F` | `DOCX_TEXT["navy"]` |
| Navy fill —— **表头行填充**（浅一档，让白字读得清）| `#1F3B5B` | `DOCX["header_fill"]` |
| Blue —— "Research" 字样 / 二级小节标题 | `#2E6DA4` | `DOCX_TEXT["accent"]` |
| Grey blue —— 季度标签 / 覆盖行 / 页脚 | `#8C97A5` | `DOCX_TEXT["meta"]` |
| Body text —— 正文、表格正文，**纯黑** | `#000000` | `BODY` |
| Gray（图下 Note / Source）| `#5A6B7B` | `GRAY` |
| Table grid —— 全部框线 0.5pt single | `#C9D2DC` | `DOCX["grid"]` |

> ⛔ 文档侧原来写成 `navy=NAVY / accent=BLUE / meta=GREYBL`（指向图表序列名），
> 结果一换图表色，"Research" 变青绿、季度标签变紫。现在钉死字面量 ——
> 要连文档一起换必须单独说。

## Document

- Page: A4, margins L/R 1.94cm, T/B 1.59cm. Default font Calibri (DengXian for East
  Asian), body size 9.5pt, language en-HK.
- All paragraphs use style `Normal` (bullets use `List Paragraph`); formatting is
  applied at run level, not via named heading styles.

| Element | Format |
|---|---|
| Title line 1 | "JUNSON Capital " bold 26pt #16283F + "Research" 26pt #2E6DA4 |
| Title line 2 | report name 20pt #16283F + "  (YYYYQn)" 13pt #8C97A5 |
| Coverage/date line | 8.5pt #8C97A5, right-aligned tab for the date; below it a thin rule |
| Section heading (Market Size...) | bold 18pt #16283F |
| Subsection heading | bold 12.5pt #2E6DA4 —— ⛔ **不带节号**，见下 |
| Body | 9.5pt **#000000（纯黑）**; key numbers bold |
| Exhibit caption | bold 8.5pt #16283F, "Exhibit N: title" |
| Exhibit note/source | 7pt #5A6B7B, single paragraph: `Note: ...  Source: ...` |
| Bullets | List Paragraph, small round bullet, bold lead-in phrase |
| Header | `JUNSON Capital｜ Private Credit Quarterly<TAB>YYYYQn`, 8.5pt gray, bottom border #16283F |
| Footer | `Fundamental Analysis Report — For internal research use only`, 8.5pt gray |

### 六色序列的顺序（2026-08-26 调过）

> ⛔ Alex 2026-08-26:「把图里紫色的重要性下降到第六位,亮绿色的重要性提高。」
> 追问确认:「亮绿色」= C3 `#2EA69F`(青绿),提到**第 2 位**;HILITE「换成刚提上来的那个绿」。

| 位 | 色值 | 名字 | 角色别名 |
|---|---|---|---|
| 1 | `#1F2B44` | 深藏蓝 | `NAVY` —— 主序列 / 深色柱 / 图内标题 |
| 2 | `#2EA69F` | 青绿 | `GOLD` `RHS` —— 右轴线 / 第二组柱（34 处），也是 `HILITE` |
| 3 | `#7A9CB7` | 蓝灰 | `BLUE` |
| 4 | `#A1B6CC` | 浅蓝灰 | `GREYBL` `ROSE` |
| 5 | `#2F7D51` | 森林绿 | `LIGHTBL` `LIGHTGY` |
| 6 | `#6B5FA8` | 紫 | `SLATE` `MAROON` |

换位前是 `[C1, C2, C3, C4, C5, C6]`(深藏蓝/蓝灰/青绿/紫/浅蓝灰/森林绿)。

⛔ **角色别名一律写 `SERIES[i]`,不许再绑 `C1..C6` 的字面名。** 换位那天就是因为别名直接
绑在 C 常量上,一改顺序全对不上 —— E19 的 Software 差点从青绿变成蓝灰（它的冻结要求是
「Total 深蓝 / software 亮蓝 / 其余比深蓝稍浅」,那是**视觉**要求,所以 `build_s5.hbars_hl`
现在写 `SERIES[0] / SERIES[1] / SERIES[2]`,换位前后同色）。

**堆叠图的取色**:位 2 是留给右轴那条线的,所以有右轴线的图堆叠分项取 `[0, 2, 3, 4]`,
没有右轴线的取 `[0, 1, 2, 3]`（E1 就属于后者,第二段是青绿）。

**自家三只基金**(E51/E52/E56/E57/E58 同图出现三只):颜色必须互不相同,一律走
`palette.OWN_FUNDS = [HILITE, SERIES[2], SERIES[5]]` = 青绿 / 蓝灰 / 紫,
`OWN_FUND_FALLBACK = SERIES[3]`。palette 里有断言兜住。
⚠ 换位的代价说清楚:`HILITE` 现在等于位 2 序列色,所以它**不再是「只给自家基金」的专属色**
—— 同一张图里第二组柱或右轴线也是这个绿。Alex 知道并选了这个。
`pc_audit` D 组逐条查:六个色值、顺序、`HILITE`、`OWN_FUNDS` 三色互不相同。

### 估算值一律加 `~`

> ⛔ Alex 2026-08-26:「E1 的图的每一个数 如果是估算的那就在数的前面加个 `~`,严谨一点。
> 避免每次出来的版本不一样。」

图上印出来的数,只要**含**测量/推算成分,标签前面就加 `~`（例 `~606`）;三段全是源文件
明标值的那一根不加（例 2025 的 `2,557`）。判据落在账本,不在出图脚本里:

```json
"estimated_periods": ["2015", …, "2024"],
"_estimated_why": "哪几期算估算、为什么（必填,pc_audit 查）"
```

出图脚本只读不判 —— 换季某一年拿到了明值,从名单里删掉那一年就行,不用改代码。

配套还有一条**冻结**:像素测量每跑一次都可能差一点点,所以已经对过账的那组值钉死。

```json
"_frozen_values": {"paths": ["stacks/Institutional", …], "n": 33,
                   "sha256": "…", "_changelog": []}
```

`pc_audit` A 组会重算 sha256。要改（源方修订了历史、或只是追加新年份）必须在
`_changelog` 里写清改了哪一期、为什么、新的对账结果,再更新 `n` 与 `sha256`。

### E56/E57/E58:基金名标在点旁边

> ⛔ Alex 2026-08-26:「E56 E57 E58 的图里的 fund 的名字标在出现的点的旁边。」

标签 = 名字 + 数值(例 `PAG BRS III 14.7%`),图例只留 `P25–P75` 与 `Median`
—— 三只基金的图例条目撤掉,否则同一个名字和数值在一张图上出现两遍。

标签长了三四倍,所以两件事跟着做:
1. **82% 白底** —— 在 3.35in 画布上横穿中位数折线或 P25–P75 带是躲不掉的
   (实测 Ex 57 的 `Guggenheim PDF IV† 1.20x` 被线划掉一道)。
2. **实测碰撞后择位** —— 先按原规则(远离中位数线那侧)给首选位,再逐个候选位量真实 bbox,
   避开已放的标签、**所有标记**、以及轴外。原来只避线不避点,实测 Ex 58 的 Guggenheim
   标签正好压在 PAG 的菱形上(两点不同 vintage,分组逻辑管不到)。
   所有候选都撞就退回首选位并打印警告,让人去看一眼。

### 末值标签越界:先翻标签,不许推轴

> ⛔ Alex 2026-08-26:「E5 这一张图的右侧部分（最后一根柱子到右侧 y 轴的距离太宽了,缩小一下）」

根因:右轴末值标签放在最后一个点的**右**下方外侧,`fit_right` 为了给它让位把 x 上限
从 64.90 推到 72.36 —— 末柱和右轴之间凭空多出约十个柱宽的空白。

现在的次序是:**先翻标签**（`js.flip_if_overflow`）→ 还越界才由 `fit_right` 推轴兜底。
翻的时候按末段方向躲开折线:末段在涨,线占左下方 → 标签放左**上**;末段在跌 → 放左**下**。
翻过去落在数据区里,所以一律加 82% 白底（跟 `legend_inside` 同一处理),
不然文字会被折线或柱子划掉一道。

另外 `ax2.set_xlim` 的右边界改成 `len(p) - 1 + 0.7`,和左边的 `-0.7` 对称
（原来写 `len(p) - 0.1`,右边比左边宽 0.2 个单位）。

### 标题不带节号

> ⛔ Alex 2026-08-26:「把每个标题前面的几点几都去掉,比如 9.1  Positioning scorecard,
> 只要去掉数字和小数点,标题部分其他不变。」

纸上任何标题都不许出现 `9.1` / `2.4` 这种前缀。做法:`build_doc` 的调用点**仍写**
`sub('9.1  Positioning scorecard')` —— 节号是 `report-spec` 的节序契约,删了就没法核顺序 ——
由 `sub()` 在 append 之前用 `_SECNO` 正则剥掉前缀,标题其余部分一个字不动。
一级章节标题（`sec()`）本来就没有节号。

`pc_docxcheck.py` 有一条硬检查:扫全部段落,凡短行且以「数字.数字 空格」开头就 ✗。

⚠ 连带影响:正文里 24 处 `Section 5.1` 这类交叉引用,纸上已经看不到对应的节号了。
一级章节本来就是这样（正文写 `Section 9`,标题只印 `Competitor Analysis`），
读者按章节顺序数 —— 小节现在跟一级章节同一个约定。要改成写节名的话得 Alex 点头。

## Data tables

- Total width 9800 dxa; all borders single 0.5pt `#C9D2DC`; tight cell margins
  (left/right ~10 dxa at table level, cells override to ~70).
- **内容行隔行底色（房子默认）**：白 / `#F2F5F9` 交替，**表头不算**，从第一条内容行
  开始就是白的。⛔ Alex 2026-08-26:「E8 和 E30 的表格,以及报告中所有出现的表格的背景,
  都需要像 Fund snapshot 的表格背景一样 一条白 一条灰。不包含表头,仅限表格内容部分的
  背景,不含任何文字。」实现在 `docx_helpers.data_table()`：`zebra=None` 就用默认色,
  要关掉必须显式传 `zebra=False`（目前没有需要关掉的表）。E48 那两行分组标题行是
  `#E8E8E8` 整行灰底,不参与交替也不打断交替。`pc_docxcheck` 逐张核内容行是否真的在交替
  （用 python-docx 走含嵌套表的树,正则分不开嵌套）。
- Header row: fill `#1F3B5B`, bold white 7.5pt, centered，
  **并且 `trPr` 里必须有 `<w:tblHeader/>`** —— 表头跨页重复。
  2026Q3 成稿 36 张表只有 12 张有，剩下 24 张跨页后读者看不到列名。
  `docx_helpers.data_table()` 现在自动加。
- Body cells: 7.5pt #000000（纯黑）, numbers centered, first column left; row labels may be
  bold. Sub-rows indented with "– " prefix.
- Zebra/emphasis: Junson's own rows in comparator tables may use a light fill; check
  the example for the exact case.
- Spacing: ~20 twips after cell paragraphs; keep tables compact.

## Exhibit layout

- **Full-width exhibit**: caption paragraph → image paragraph → note paragraph。
  **插入宽上限 17.12cm**（= 21 − 1.94×2，正文可用宽）。
  ⛔ 早前写的 "16.5–17.5cm" 里 17.5cm 会溢出 0.38cm —— 2026Q3 成稿里那两张 17.53cm 的图
  确实溢出了页面。`docx_helpers.exhibit()` 现在会断言拦下来。
- **Side-by-side pair**: a 1×2 layout table, width 9700 dxa, all borders explicitly set
  to `none` (val="none" sz=0 color=FFFFFF), cell margins L/R 10 dxa; each cell holds its
  own caption → image (**8.51cm**，两张 + 0.1cm gap ≈ 17.12cm) → note. Both cells in one row so charts sit level.
- **Fund snapshot**: 1×2 borderless table whose left cell holds a rendered
  snapshot image (a compact label/value card produced as a chart/figure); right cell
  text or empty. Clone construction from the example.
- Exhibit numbering is document-global and sequential.

## Charts (matplotlib via scripts/junson_style.py)

- Import `junson_style` and call `apply()` before plotting; use `PALETTE` constants.
- Look: white background, no top/right spines, left/bottom spines light gray, y-grid
  only `GRID` `#E3E7EC`。**图例一律用 `js.legend_inside()`**，不要自己写 `ax.legend()`：
  位置读账本冻结的 `legend_loc`（没冻结就实测四角最空的那个并打印建议，看过之后写进账本），
  底色 82% 白 —— 无框图例会被数据线穿过去，2026-08-25 实测 `mkt_dl_origination` 的
  "Refi"、`mkt_inst_aum_decomp` 的 "Dry powder as % of NAV (rs)" 都被右轴折线划了一道。
  有右轴（`twin_right`）的图，`legend_inside` 会自动把图例挂到**最上面那层轴**上 ——
  twin 是后画的一层，挂在主轴上的图例连白底一起会被它的线盖住（`zorder` 管不了跨 Axes 的
  绘制顺序）。
  > ⛔ 早前这里写「tick labels ~13pt（图先画大再在文档里缩小）」—— **已作废**。
  > 现在是 1:1 锁死（见下面的尺寸表），画布宽就是插入宽，所以刻度字号本来就是纸上字号：
  > `pair` 档 6pt、`solo` 档 7pt，由 `junson_style.FS` 统一给，不要手工设。
- Bars / Lines 的序列色**按 `palette.SERIES` 的顺序取**，不要按角色名硬记 ——
  Alex 2026-08-25 换过一整套：`#1F2B44`(深藏蓝) → `#7A9CB7`(蓝灰) → `#2EA69F`(青绿)
  → `#6B5FA8`(紫) → `#A1B6CC`(浅蓝灰) → `#2F7D51`(绿)。超过六条用 `js.series_ext(n)`
  （六色 × 三档白混，18 色；再多直接报错，不许循环回第一色）。
  角色别名（`NAVY`/`GOLD`/`BLUE`/`GREYBL`/`LIGHTBL`/`SLATE`/`RHS`）现在都指向这六色之一，
  **名字是历史遗留，别照名字猜颜色**（`GOLD` 现在是蓝灰 `#7A9CB7`，不是金色）。
  堆叠柱的总计标签加粗、深藏蓝、放柱顶上方（水平，不许竖排）。
  **柱状图的数值轴一律从 0 起**（`guards.assert_bar_baseline_zero` 硬查）。
- Lines: 叠加线 / 加权平均 / 阈值线用 `GOLD`（换色后是蓝灰 `#7A9CB7`，阈值线用虚线），
  末点或引出标注加粗；右轴序列用 `RHS`（同为 `#7A9CB7`）。
  ⛔ **色值只有 `palette.py` 一处真值** —— 出图脚本里不许写死十六进制，这份文档里的具体色号
  只是当下的快照，改色时改 `palette.py`，`pc_audit` 组 D 会查两边一致。
  描点直径 = 线宽 × 2（`js.ms(lw)`）。折线可以不从 0 起。
  **高亮某一行/某根柱用 `GOLD`；`HILITE` 那个红只留给 Junson 自己的基金。**
- Value labels: bold, navy, placed above bars / at line endpoints; label the latest
  point of every important series (the reader should get the current level without
  squinting).
- **Sizes — 画布宽 = Word 插入宽（1:1），写死两档:**

  | 档 | `figsize[0]` | Word 插入宽 | 图内字号 |
  |---|---|---|---|
  | `pair`（并排）| **3.35 in** | 3.35 in（一组两张 + 0.04 gap = 6.74 in）| 轴 6.5 / 刻度 6.0 / 标签 6.0 |
  | `solo`（单图）| **6.74 in** | 6.74 in = 正文可用宽，**不许再大** | 轴 7.5 / 刻度 7.0 / 标签 7.0 |
  | `tall`（窄高单图）| **5.30 in** | 5.30 in（13.46 cm），Word 侧**居中**插入 | 同 solo；Ex 9 用它（Alex 2026-08-24：长度缩短、高度拉高，默认 h=4.2）|

  入口只有一个: `fig, ax = js.figure('pair', h=2.4)` / `js.figure('solo', h=3.2)`，
  落盘用 `js.save(fig, path)`（dpi 200，**不用 `bbox_inches='tight'`** —— 它会裁掉白边破坏 1:1）。
  `js.save()` 会硬拦画布宽不对的图，并顺带跑 `guards.check()`。

  > ⛔ **早前写的 "half ≈ 7×5 in → placed ~8.5cm" 已作废。** 实测:那个规格落盘 5.95 in，
  > 插到 3.35 in 是 56%，图内 13pt 只显示 7.3pt；而 2026Q3 成稿那批画布是 4.1–5.3 in，
  > 显示约 8.8pt。也就是照旧规格做，字会比参照小 17%，而且每季都这样漂。
  > 1:1 之后，**图内写多少 pt 纸上就是多少 pt**，不用再算比例。

- **图内不放标题、不放脚注。** `Exhibit N: 题注` 和 `Note: … Source: …` 都在 Word 侧
  （由 `exhibits.py` 和 `docx_helpers.py` 生成）。图内只有数据、坐标、图例、数值标签。
- **折线描点直径 = 线宽 × 2**（`js.ms(lw)`）。点比线粗一倍多会盖住线和相邻的点。
- **图内数值标签一律水平**（`rotation=0`）。条形图上的数值尤其不许竖排。
  以上两条由 `guards.py` 硬查。
- ⛔ **图上不许出现样本数标注。** `n=26`、`(n=11)`、`Vintage  (n = funds: ’19 12 …)` 这类
  一个都不许有 —— Alex 说过两次（8-25「n=几全都删去 包括括号」、8-26「这一行都删掉，
  **不允许出现**」），所以现在是硬闸：`guards.assert_no_sample_counts()` 在 `js.save()`
  里拦，命中直接抛错。样本数留在账本 `n` 字段里，要说样本量就写进正文或 Note；
  Note 里也不许写（`pc_notecheck` 查），更不许说「样本数印在轴下方」——那东西不存在了。
- **Ex 56/57/58 没有横轴标题。** 刻度本来就是年份、题注里也写着 by vintage，那行是冗余；
  同事那三张也没有。`median_band()` 的 `show_n` 参数已作废，留着只为不改调用签名。
- **末点标签别顶到右边框上。** 有右轴的图，坐标区右边框外面就是右轴的刻度和刻度标签，
  末点标签一越界就压在它们身上（2026Q3 踩过：Ex 26 的 "10.7" 被右边框和右轴刻度 "12"
  切成两半）。靠 `xlim` 里拍一个「周期数 × 7%」的余量不管用 —— 余量按周期数算，标签宽度
  按字数算。改法：`js.save()` 之前调 **`js.fit_right(ax)`**，它在 `tight_layout` 之后
  实测越界多少像素、把 x 上限往右推多少（迭代到不越界，只动 xlim，1:1 锁不受影响）。
  没调的图 `js.save()` 会打印 ⚠ 点名。
- **一对柱（Fund vs cohort median）的两个数值标签**：柱心只隔 0.36 个轴单位（`pair` 档
  约 9pt），四字标签宽约 14pt，横向必然重叠，靠的是**纵向**错开。两根柱高度差不到一行字高
  时，把浅色柱那个数写**进浅色柱里**（`#D7DEE6` 底 + 深藏蓝字）；浅色柱太矮塞不进字的，
  把深色柱那个抬高一行让开。见 `build_s7._pair_value_labels()`。
- Special charts: rating-band positioning graphics (Ex 22/24) are horizontal shaded
  bands (#F4F6F8 → #A8CBEA gradient of blues) with navy diamond markers and text
  labels, drawn with axhspan + scatter; bubble chart (Ex 55) uses navy bubbles, size =
  fund count, inverted x-axis, leader-line labels; percentile trajectory lines carry
  P25/P50/P75 reference bands in light gray.
- **柱状图的数值轴一律从 0 起。**（Alex 2026-08-21 定）柱子的长度就代表数值本身，
  截断基线会把 4.4%→6.0% 这种变化画得像翻倍。**研报原图截断不算理由** —— 照抄就是
  把别人的失真搬进自己的报告。典型的坑：MS tracker 里 Fitch 那张 TTM 违约率
  （原图纵轴自 3.0% 起）、S&P deck 里几张窄区间的柱。
  - 遇到「窄区间、看不出变化」的，两条出路：① 改画折线（**折线可以不从 0**，
    本来就是看走势）；② 保留柱、从 0 起，把区间写进 `Note:`。
  - 账本里用 `_source_axis_min` 记下原图的轴起点，方便日后核对。
  - 这一条由 `guards.py` 的 `assert_bar_baseline_zero()` 硬查：竖柱查 ylim[0]、
    横柱查 xlim[0]，非 0 直接抛错。确有例外（瀑布图之类）给该 ax 打
    `_allow_nonzero_base = True`，并在账本里写清为什么。
- Save PNG **without** `bbox_inches='tight'`（`js.save()` 已经这么做了）。
  tight 会按内容裁掉白边，落盘宽度就不再等于画布宽度，1:1 锁死随之失效。
  transparent=False，白底。

- **`HILITE` 只给 Junson 自己的基金。**（变量名里的 `RED` 是历史遗留 —— 换色之后它是
  紫 `#6B5FA8`。）别的地方要突出某一行/某一根柱
  （行业均值、Total、基准线之类），用 `GOLD`，不要占红。否则读者一看到红就以为是我们的基金。
  账本里如果这一行确实是我们自己的基金，写 `highlight_is_own_fund: true`，作图函数才用红。

### 图例不许被读成数据点

坑是真的：上一版的 Ex 51/52（百分位轨迹，全图只有 2026Q3 一列点）把图例放在图内右下，
三个图例色块正好落在 2027Q1–Q2 的横轴位置上，被报告主人读成「2027 年有数据」。
guards 抓不到这种错 —— 色块没压任何文字，版面完全合法，但语义上是假数据点。

⛔ **但解法不是把图例挪到坐标区外。** Alex 2026-08-25：「这两个也是要放在图内的，
可以用个细的黑色矩形框线把图标框起来，就不会读错了。」
所以：**所有图的图例都在坐标区内**，靠离散标记承载数据的图（散点 / 轨迹 / 只有一列点的）
在账本里打 `legend_boxed: true` —— `js.legend_inside()` 会给它实心白底 + 0.6pt 黑框，
框起来之后读作图例，不再读作散点。

**同一 vintage / 同一期上两个标记重合的，也要让开。** 数值相同是真实情况，不许改数；
能改的是画法 —— 标记左右错开一点、标签一上一下。2026Q3 实测两处：Ex 52 的 Guggenheim 与
HSBC 的 TVPI 都是 P100，后画的把先画的整个盖住，两个 "P100" 也叠成一个；Ex 58 的
1.20x / 1.21x 同理。见 `build_s7.pct_points()` 与 `build_s6.median_band()`。

**叠点标签一律放在「远离中位数线」的那一侧**，那一侧出轴就翻面。原来按「第一个标下方、
第二个标上方」的顺序排，只看顺序不看图上有什么 —— Ex 56 的 PAG 14.7% 就正好标在中位数
折线上，数字被线穿过。

## 来源链接

Related news 每条来源**必须是 Word 超链接，且目标是那一篇文章的完整 URL**（带路径）。
只到域名（`bain.com`、`bloomberg.com`）算错 —— 读者点进去落到首页找不到原文。
用 `docx_helpers.hyperlink()`，它会拦裸域名。**拿不到准确网址的新闻就删掉这一条**，
不许用域名凑。2026Q3 成稿 0 个超链接，这一条是新增要求。

## Writing style

- Dense, analytical, number-forward sell-side English; em-dashes for elaboration;
  every paragraph earns its place by answering the section's fixed question.
- Direction words tied to arithmetic ("edged down", "rose to", "converged into a
  505–516bp band") — verify each against the computed delta.
- Caveats are part of the house voice: smoothing/fair-value caveats, basis changes,
  vintage effects, sample-size warnings are stated plainly in text and notes.
- Chinese version (when requested): translate body text and table cells; keep charts,
  fund/manager names, metric acronyms (IRR, TVPI, DPI, PIK, MM CLO) and exhibit
  captions' technical terms in English where natural; file name `_CN_`.
