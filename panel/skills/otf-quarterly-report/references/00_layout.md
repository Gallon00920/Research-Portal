# 最终版布局与行文规格

## 两份来源怎么用

| 来源 | 提供什么 | 冲突时 |
|---|---|---|
| **v1 报告**（`OTF_<季度>_OTF update_v1.docx`）| **章节顺序、标题、层级、图表位置** | **以它为准** |
| **V4 细化行文结构**（`2026Q1 OTF季度更新—细化行文结构 V4.docx`）| **行文规格**：密度、口吻、每格几条、禁用词、环比记法、各节要件 | 布局上不听它 |

V4 是 2026Q1 的版本，跟最终版有四处已知不一致，**按最终版走**：news 后置、4.1 把 broker 与 company 合并、章节编号变了、划线那几项（Implied TP 表、Position monitoring 表、GS 软件敞口图）最终版已删。

**若用户本季另附了新框架**（V5 等），以附件为准，并把与本文件的差异逐条列出来给用户确认，不要默默按新的做。

## 最终版章节骨架

```
标题行 + 渐变条（图 0）
Summary                          三个小标题，每块恰好 3 条 bullet
1. News
  1.1 Key news on Blue Owl & OTF
  1.2 Key private credit news
  1.3 AI related news
2. OTF update
  2.1 Portfolio composition
      Capital structure          T1（PNG）
      Industry                   图 1 + T2
      Software layer exposure    T3
      Borrower fundamentals      T4
  2.2 Financial & debt
      Cash yield trend           图 2
      NAV bridge                 图 3
      NII & dividend coverage    图 4
      Financing profile          T5
      Leverage ratio             文字 + T6
  2.3 Default concern            本节开头不写导语
      PIK                        图 5
      Non-accrual                图 6
      Internal risk rating       图 7
  2.4 Sell-side view & TP        文字 + T7
  2.5 Price comparison           图 8、图 9 + T8
  2.6 Competitor analysis
      2.6.1 BDC competitor analysis   Thesis 段 + T9
      2.6.2 Return comparison         图 10 ‖ 图 11（并排，分析在两图下方）、图 12（单图 6.05 in）
      2.6.3 Asset quality comparison  图 13 ‖ 图 14（并排，说明与分析在两图下方）
  2.7 Things we should know      0–2 个议题，**写不出来就整节不要**
3. Private credit & public BDC industry
  3.1 Broker view summary        T10
  3.2 Consensus & key debate
  3.3 Fundamentals               图 15‖16、图 17‖18、图 19‖20（三组并排，每组一段合并分析）
  3.4 Things we should know
      3.4.1 Software exposure in leveraged credit
4. Software industry by AI impact
  4.1 Broker & company view summary   T11 + T12 + T13 + T14
  4.2 Things we should know      至多 1–3 条
  4.3 AI impact on software layers    图 21 + 各层定义斜体段
```

## 分页

**Summary 与「1. News」之间必须插硬分页符，News 从新的一页开始。**

docx 里写法是在 Summary 最后一段之后、`1. News` 标题所在段落的第一个 run 里放 `<w:br w:type="page"/>`，或者给 `1. News` 那个标题段落加 `<w:pageBreakBefore/>`（后者更稳，不会因为 Summary 长度变化而漂）。

其余各节**不额外强制分页** —— 只有这一处是写死的。

## 全篇写作总则（V4 提供，逐条照做）

**语言：全部英文。** 正文、标题、表格、图内文字一律英文。（注意：用户另外几个中文块 skill 的「中文正文」规则**不适用于本报告**。）

**定位**：家办内部季度跟踪报告，读者是投委会。每节**先结论后论据**，要「判断」，不要把研报/filings 搬进正文。

**口径**：每节呈现「本季水平 + QoQ 环比」。数字环比基准 = 上季 filings；观点环比基准 = 上季报告结论。环比记法 `↑ +0.6pp` / `↓ 10bp` / `flat`。

**数字格式**：`$0.9bn` / `$285mm` / `13.1%`。描述任何变化都用具体数字 + 幅度。

**禁用主观定性词**：strong / solid / robust / impressive / modest / significant / improved（作为形容而非可校验判断时）/ better than peers 之类一律换成数字与幅度。转述券商结论要注明「per <broker>」。

**密度**：每个表格格子 3–4 条、每条 ≤2 行、一条一个独立判断。**绝不堆砌** ticker 清单、目标价清单、子指标流水账。

**不重复**：一个事实/数字全篇只出现一次。写完每节通读删重复与废话。

**尽量不用括号。** 2.6.1 那一段**全段禁用括号**。真需要括注解释时才用。

**broker view 表格里不出现研究员姓名。** 只写机构名（BofA、J.P. Morgan、Morgan Stanley…）。

**提到回购必须注明是哪家公司**的回购。

**排版**：全篇等线；表格按 `08_tables.md` 的真实样式（**有框线、有底色**，不是无框无色）；图不另加题注 —— 标题已经烧在 PNG 里；图片宽度按 `03_style.md` 的表，与正文两端同宽。

**纪律**：事实与数字只来自素材或明确标注的联网检索。缺料写「本季缺 X 输入」，不臆造。不写「数据基准/覆盖至 X 月」这类元信息，不写免责段。
---

# 页面与字体（**推翻早前的「全篇横向」设定**）

## 页面

**A4 竖版，除 2.6.1 BDC competitor analysis 那一页外全部竖版。**

| 项 | 值 |
|---|---|
| 纸张 | A4（`w:pgSz w:w="11906" w:h="16838"`）|
| 方向 | **竖版**；仅 2.6.1 那一节为横版（`w:orient="landscape"` 且 pgSz 宽高互换）|
| 左右边距 | **沿用 V1 的 830 / 832 twips = 合计 1.15 in** |
| **正文可用宽度** | **7.12 in** |
| **图片插入宽度** | **6.05 in = 正文宽度的 85%**，水平居中 |
| **例外 · 封面顶部长横条** | **7.11 in —— 与正文两端同宽，不走 85%** |
| **例外 · 并排图（10 张）** | 各 **3.50 in**，见下方「并排」一节 |

边距沿用 v3 的 830/832（1.15 in）而不是改成 2 cm —— v3 已经是 A4 结构，边距是既有样式，不动。

## 字体

| 用途 | 字体 | 字号 | 颜色 |
|---|---|---|---|
| **正文** | **Calibri Light** | **小四 = 12 pt**（docx `w:sz="24"`，半点制）| **纯黑 `#000000`**（`w:color w:val="000000"`）|
| 标题 | 沿用原有层级配色与字号 | — | 沿用原有 |
| 图内文字 | Lato（烧在 PNG 里）| 见下方新字号表 | 主文字纯黑 `#000000`；脚注 `#5A6B7B`；标题 `#16283F` |

**⛔ 早前的正文色 `#22303C`（深灰蓝）已作废，一律改纯黑 `#000000`。** `docxcheck.py` 会查「最常见的字体颜色」是不是纯黑。

容器里没有 Calibri Light（只有度量兼容的 Carlito），所以本地转 PDF 预览时字体会被替换，但 docx 里写的字体名是对的，在 Windows 上正常显示。**不要因为预览里看着不像就去改字体名。**

## 页面尺寸的事实基准（**量的是 v3，`OTF_2026Q3_OTF update_v3.docx`**）

**v3 就是 A4 结构，以它为准。** 拆开 `document.xml` 实测：

| 项 | v3 实测值 | 结论 |
|---|---|---|
| 第 1 节 | `pgSz 11906×16838` | **A4 竖版** ✓ |
| 第 2 节 | `pgSz 16838×11906 orient="landscape"` | **A4 横版**，就是 2.6.1 BDC competitor ✓ |
| 第 3 节 | `pgSz 11906×16838` | A4 竖版 ✓ |
| 左右边距 | `w:left="830" w:right="832"` = **1.15 in** | 三节一致 ✓ |
| **竖版正文可用宽** | **7.12 in** | 图片实际插入宽 **7.11 in** ✓ |
| **横版节可用宽** | **10.54 in**（11.69 − 1.15）| T9 六家竞品表放这里 |
| 页眉 | `JUNSON Capital\| Blue Owl Technology Finance Corp.` + 右侧季度；首页 `JUNSON Capital Research` | 沿用 |
| 页脚 | 左 `Fundamental Analysis Report` / 右 `For internal research use only` | 沿用 |
| 表格 | 14 张，**全部已带 `w:tblHeader`** | 已达标 ✓ |

**页面结构、边距、插入宽度、表头重复这四项 v3 已经全对，不用动。** 还差两件事：

**① 正文字体**：`docDefaults` 写的是 `Calibri Light`，但正文 run 里有 **509 处 `w:ascii="Arial"` 覆盖**，
run 级优先，所以实际渲染是 Arial。字号是对的（12 pt 小四，772 处）。
→ 成稿时把这 509 处 run 级 `w:ascii/w:hAnsi/w:cs="Arial"` 全部改成 `Calibri Light`，
或者干脆删掉这些 run 级 `rFonts`，让它继承 `docDefaults`。

**② 图的画布**：见下。这是 v3 唯一的硬伤。

## ⛔ 为什么不能只靠缩放：V1 自己就是反例

PNG 里的字是**像素**，和线条一起缩。缩放不是解决办法，缩放就是问题本身。

```
图内文字在纸上的实际字号 = 图内写的字号 × Word 插入宽度 ÷ 画布宽度(figsize[0])
```

v3 的纸已经对了，但画布没跟着改 —— 12–18 in 的画布插进 7.11 in，缩到 0.4–0.6 倍。
图内脚注写 `fontsize=11.5`，在 v3 的纸上实际只有 **2.2–7.8 pt**。

v3 实测每张图的画布宽、插入宽、以及图内 11.5 pt 脚注在纸上的实际字号：

| 图 | 画布宽 | v3 插入宽 | **v3 纸上实际 pt** |
|---|---|---|---|
| 图 1 双饼 | 18.03 in | 7.11 in | **4.5** |
| 图 2 | 16.22 in | 7.11 in | **5.0** |
| 图 4 | 16.94 in | 7.11 in | **4.8** |
| 图 5 PIK | 10.43 in | 7.11 in | 7.8 ← 这张已经窄过一轮 |
| 图 6 | 10.45 in | 7.11 in | 7.8 ← 同上 |
| 图 7 | 16.22 in | 7.11 in | **5.0** |
| 图 10 | 17.60 in | **3.65 in** | **2.4** |
| 图 11 | 17.60 in | **3.40 in** | **2.2** |
| 图 12 | 17.60 in | 5.51 in | **3.6** |
| 图 13 | 17.60 in | 3.64 in | **2.4** |
| 图 15 | 12.89 in | 7.11 in | **6.3** |
| 图 21 | 8.12 in | 4.01 in | **5.7** |

**并排那四张（图 10/11/13/14）是最惨的 —— 2.2–2.4 pt，等于没有。**
图 5 / 图 6 已经被人窄到 10.43 in 了，是全篇最好的 7.8 pt —— 说明方向本来就对，只是没做完。

`build_charts.py` 之所以是 12–18 in，是因为它当初是对着旧稿的**像素数**（2433×1396 之类）复刻的，
而不是对着**显示宽度**。这是根因。v3 换纸的时候只改了插入宽度，没改画布，所以字被压得更小。

## ✅ 正确做法：画布宽 = 插入宽，1:1

不要定什么「可读下限」再反推画布，直接把比值锁成 1：

```
figsize[0] = 6.05        # 正文宽度 7.12 in 的 85%，就是图片插入宽度
dpi        = 200         # 只管清晰度（1424 px 宽），不影响字多大
```

**1:1 之后，图内写多少 pt，纸上就是多少 pt**，不用再算比例，肉眼所见即所得。

代价是图内字号要按「相对正文 12 pt」重定 —— 现在这套（标题 19、脚注 11.5）是为 16 in 画布设计的，
1:1 之后会比正文还大。**新的图内字号表：**

| 元素 | 旧（16 in 画布）| **新（6.05 in 画布，1:1）** |
|---|---|---|
| 图标题 | 19 pt bold | **13 pt bold** |
| 副标题 / 口径行 | 13 pt | **9.5 pt** |
| 轴标签 | 13 pt | **9 pt** |
| 刻度标签 | 12.5 pt | **8.5 pt** |
| 数据标签 | 11.5 pt bold | **8.5 pt bold** |
| 图例 | 12.5 pt | **9 pt** |
| 脚注 / Source | 11.5 pt | **7.5 pt** |

配色、线宽、marker、脚注写法**一律不动** —— 变的只有画布尺寸和字号。

## 并排（**共三处、十张图；其余全部单图**）

**这是阶段二的排版规则，跟阶段一出图无关。** 阶段一照旧把 21 张图都出成 6.05 in 画布
（封面横条 7.11 in），**不为并排重出任何一张**；阶段二插入时把这十张缩到 3.50 in 并排。

| 位置 | 并排 | 下方 |
|---|---|---|
| 2.6.2 Return comparison → *NAV per share & Dividend yield* | 图 10 `BDC NAV per Share` ‖ 图 11 `BDC Dividend Yield on NAV` | 一段合并分析，覆盖两图 |
| 2.6.3 Asset quality comparison → *Non-accrual % & Portfolio company average EBITDA* | 图 13 `BDC Non-accrual` ‖ 图 14 `BDC Portfolio Company Average EBITDA` | 同上 |
| **3.3 Fundamentals 第一组** | 图 15 `Borrower leverage` ‖ 图 16 `Interest coverage` | 同上 |
| **3.3 Fundamentals 第二组** | 图 17 `BDC non-accrual (avg)` ‖ 图 18 `PIK / total investment income` | 同上 |
| **3.3 Fundamentals 第三组** | 图 19 `PIK / net investment income` ‖ 图 20 `Non-accrual by sector` | 同上 |

**3.3 的版式写死成这样**（早前「六张图各占一行、每张单独一段分析」已作废）：

```
3.3 Fundamentals
    图 15  ‖  图 16
    ← 一段分析，同时讲这两张 →
    图 17  ‖  图 18
    ← 一段分析，同时讲这两张 →
    图 19  ‖  图 20
    ← 一段分析，同时讲这两张 →
```

**几何**：每组两张各 3.50 in、中间 0.11 in，合计 7.11 in。
放在 1×2 的无框线无底色 Word 表格里，或同段两个 inline 图片 —— 视觉上并排、顶端对齐。

**两图之间不许插文字。** 说明与分析**合并成一段，放在该组两图的下方**，一段话覆盖两张图，
不要写成「图 15 讲……；图 16 讲……」两段。

**不并排的图**：图 1–9、图 12、图 21 一律 **6.05 in 单图居中**；封面横条 **7.11 in**。
注意图 12 `BDC PIK Income` 虽然也在 2.6.2 里，但是单图，不参与并排。
图 1 是一张 PNG 内含左右两个饼，6.05 in。

### 缩到 3.50 in 的后果（知情接受，不是疏漏）

画布 6.05 in 缩到 3.50 in 是 58%，图内字按比例缩：

| 图内元素 | 单图 6.05 in 时 | **并排 3.50 in 时** |
|---|---|---|
| 图标题 13 pt | 13 pt | 7.5 pt |
| 刻度 / 数据标签 8.5 pt | 8.5 pt | 4.9 pt |
| 脚注 7.5 pt | 7.5 pt | **4.3 pt** |

所以**这五组的口径与来源要靠下方那段正文交代**，读者不指望读图内脚注。

`chartlib.save()` 遇到这十张会打印一行提示，说明它们会被缩到多少、图内字会显示多大，
但**不拦** —— 画布必须是 6.05 in，并排是阶段二的事。

## 重出图会让签收失效 —— 应该的

`approve.py --check` 会因为 PNG 的 sha256 变了而拒绝进入阶段二。图变了就必须重新交给用户逐张校对、重新签。

## 表格

14 张 Word 原生表在竖版里列宽按 7.12 in 重新分配（数值型四列表仍按 40 / 18 / 18 / 24 %）。

**T9 六家竞品表**是唯一放不进竖版的 —— 六列 + 行标共七列，所以那一页横版，列宽按横版可用宽度（约 10.0 in）分配。

**表头必须跨页重复**（`w:tblHeader` 在表头行的 `trPr` 里），否则表格跨页之后读者看不到列名。
