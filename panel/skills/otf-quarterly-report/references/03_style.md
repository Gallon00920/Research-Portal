# 出图总则：配色 / 字体 / 标题 / 标注 / 脚注 / 插入宽度

### 4. 出图总则


### 4.1 技术底座

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 全篇统一 Lato。若未安装：apt-get install -y fonts-lato && rm -rf ~/.cache/matplotlib
matplotlib.rcParams['font.family']      = 'Lato'
matplotlib.rcParams['axes.unicode_minus'] = False
```

- 全部输出 **PNG，dpi=150，`bbox_inches='tight'`**。
- **背景一律纯白 `facecolor='white'`**（figure 和 axes 都要设）。**不许出现米黄底 `#FCFCFB`** —— 全篇 21 张图同一个底色。
- **图内文字一律英文**（标题、轴、图例、脚注）。中文只出现在 Word 正文点评里。
- 负号用 **U+2212 `−`**，不要用 hyphen；箭头用 `↑ ↓`；破折号用 `—`。
- 只留 **y 轴横向网格**，`color='#E3E7EC'`、`lw=0.8`、`set_axisbelow(True)`；不画竖向网格。
- 去掉 top / right spine。图 10–14 连 left spine 也去掉，只留极淡的 bottom。
- **刻度步长必须用 `MultipleLocator` 写死**，不要让 matplotlib 自己选 —— 否则跨季会从「2 一档」跳成「2.5 一档」。
- **文本里的 `$` 必须转义成 `\$`**（或整体关掉 mathtext）。脚注里写 `$42.3mm ÷ $338.0mm` 不转义的话，matplotlib 会把中间那段当公式排成斜体。这个坑一定会踩。

### 4.2 配色总表 —— 全篇 21 张图共用（不再有第二套色系）

全篇只有这一套色板。图 8、9、10–14 里各 ticker 的固定映射见 §4.3；其余各图**按这个顺序取色**，除有专门规定：

| 序 | 色号 | 名 | 惯用角色 |
|---|---|---|---|
| 1 | `#16283F` | navy | 主系列 / 标题 / 本方口径 |
| 2 | `#2E6DA4` | blue | 第二系列 |
| 3 | `#A93226` | red | 负向项、覆盖率折线、**本季高亮点** |
| 4 | `#8C97A5` | gray-blue | 参照系列（行业均值、历史均值） |
| 5 | `#9DB8D2` | light blue | |
| 6 | `#C9A227` | gold | |
| 7 | `#4B5B6E` | slate | |
| 8 | `#C08578` | dusty rose | |
| 9 | `#AEB4BC` | light gray | |
| 10 | `#6E1F18` | dark maroon | |
| — | `#D5DAE0` | pale gray | **专用**：饼图的 "Other" 扇区 |
| — | `#437BAD` | 次级蓝 | 双轴图的右轴系列（图 17） |

固定用色：

```python
TITLE   = '#16283F'   # 标题，bold
TEXT    = '#000000'   # 轴标题、刻度、数据标签（已由 #22303C 改为纯黑）
NOTE    = '#5A6B7B'   # 图内脚注
GRID    = '#E3E7EC'
REFLINE = 'gray'      # 100 基准线：ls='--', lw=1, alpha=0.5
```

**若某图系列数超过 10 个**：自行补色，但只允许在上述色相里加深/减淡，不许引入新色相（不许出现纯绿、纯紫、荧光色）。

### 4.3 ticker 配色：一个 ticker 全篇一个颜色（图 8、9、10–14）

**原来那套独立色系已取消**（米黄底 `#FCFCFB`、DejaVu Sans、亮红/亮蓝/琥珀/翠绿/紫）。图 10–14 与图 8、9 一律走 §4.2 的配色总表：**纯白底、Lato、Palette A 色号**。

同一个 ticker 在全篇任何一张图里都是同一个颜色 —— 这张表是唯一依据：

| Ticker | 色号 | 出现在 |
|---|---|---|
| **OTF** | `#A93226` | 图 8、9、10–14。**唯一的红色**，`lw=4`、`ms=8`、`zorder` 最高 |
| ARCC | `#4B5B6E` | 图 9、10–14 |
| BXSL | `#C9A227` | 图 9、10–14 |
| OBDC | `#9DB8D2` | 图 9、10–14 |
| TSLX | `#AEB4BC` | 图 9、10–14 |
| GBDC | `#2E6DA4` | 图 9、10–14 |
| MSFT | `#4B5B6E` | 图 8 |
| ORCL | `#C9A227` | 图 8 |
| CRM | `#9DB8D2` | 图 8 |
| NOW | `#AEB4BC` | 图 8 |

- peer 线在图 10–14 用 `lw=2.2`、`marker='o'` `ms=6`；在图 8、9（日线）用 `lw=1.6`、无 marker。
- 若某季某条浅色线（`#AEB4BC` / `#9DB8D2`）在图上确实读不清，**只允许在同色相内加深一档**，不许换色相；改了要写回这张表当成固定映射，下季继续用。
- 除 OTF 外**不许再出现任何红色系**（`#A93226` / `#6E1F18` / `#C08578`），红色是标的的专属标识。

**图 10–14 的版式保留不变**（只换了配色和字体）：

1. **左上标题**：`BDC <Metric>  |  <首期>–<末期>`，如 `BDC NAV per Share  |  1Q25 – 2Q26`；bold、色 `#16283F`、`loc='left'`。
2. **标题下一行副标题**：`<口径一句话>   ·   Source: <来源>`，色 `#5A6B7B`。
3. 折线 `lw=2.2`、每点 `marker='o'` `ms=6`；**OTF** `lw=4`、`ms=8`、`zorder` 最高。
4. **右侧三段式收尾**（这套图的签名特征，必须做）：末点 → 水平虚线（同色，`ls='--'`, `lw=1.2`）→ **ticker 粗体**（同色）→ 再右侧独立一列**末期数值**（`#000000`，右对齐，全部数值左边缘对齐成一列）。
5. ticker 与数值标签按末期值排序后**上下错开**。**最小间距按像素算、不按 y 跨度百分比**：
   ```python
   gap = max((ylim[1]-ylim[0]) * 0.032,
             label_fontsize * 1.25 * fig.dpi / 72 / px_per_data_unit)
   ```
   y 跨度大的图（如 NAV 14–28）只按 3.2% 算出来不够，数值列会叠在一起 —— 实测踩过。ticker 和数值必须用**同一个** `yy`，否则两列错位。
6. **不画图例**（右侧 ticker 就是图例）。
7. 底部 2–4 行注释，色 `#5A6B7B`，含指标定义 + 口径差异（如「GBDC 财年 9/30，此处按日历季度」「GBDC 只披露中位数，读趋势不读绝对水平，ticker 加 `*`」）。
8. 网格 `#E3E7EC`；top / right / left spine 去掉，bottom 留极淡一条。

### 4.4 标题 / 数据标签 / 脚注

**标题（图 1–9、15–20）**：居中，`fontsize≈20`（在 16in 宽画布上），bold，色 `#16283F`。

标题分两类，处理方式完全不同：

**A 类 · 固定标题** —— 只有指标名，或只含季度/期间变量。每季照抄，不用重判。**16 张**：

| 图 | 标题模板 |
|---|---|
| 1 | `Portfolio by industry — top 10 + other, {PQ} vs {CQ}` |
| 2 | `Portfolio yields vs funding cost & SOFR` |
| 3 | `NAV per share bridge — {PQ} → {CQ}` |
| 4 | `NII vs dividend & coverage` |
| 5 | `PIK income as % of total investment income` |
| 6 | `Non-accruals — at amortized cost vs at fair value` |
| 7 | `Internal risk ratings distribution` |
| 8 | `OTF vs leading software companies — share price` |
| 9 | `OTF vs leading BDCs — share price` |
| 10–14 | `BDC <Metric>  \|  {首期} – {CQ}` |
| 19 | `PIK as % of net investment income — BDC industry` |
| 21 | `The software stack under AI — <N> layers` |

**B 类 · 带数据描述的标题** —— 破折号后面是对**本季数据**的判断。**5 张，全在 §3.3**：

| 图 | 2026Q2 那一季的写法 | 判断依据 |
|---|---|---|
| 15 | `Borrower leverage — flat to slightly down` | 末值 ≤ 上一期且降幅很小 |
| 16 | `Interest coverage — improved on the quarter, still near lows` | 末值 > 上一期；且末值落在窗口区间下 40% |
| 17 | `Non-accruals across BDCs — average at a five-year high` | 末值 = 近 20 期最高 |
| 18 | `PIK income across BDCs — {值}% of investment income, more high-PIK BDCs` | 数字 = 左轴末值；`more` = 右轴末值 > 上一期 |
| 20 | `Non-accruals by sector — {A} & {B} saw the sharpest rise` | {A}{B} = 当季 vs 三年均值升幅最大的两个行业 |

> ### ⛔ B 类标题每季必须重算，且不许跟图上的数据相违背
>
> 这是最容易出事的地方：数据换了一季、方向反了，标题照抄上季 —— 图上明明在跌，标题写着 `improved`。读者第一眼看标题，比看曲线快。
>
> **规则：**
>
> 1. **B 类标题的判断句由代码从数据算，不许手写。** `series.json` 里把标题拆成 `title_fixed`（破折号前的指标名，固定）和 `title_claim`（破折号后的判断句，每季重算）两段存。
> 2. **判断句只能用下面这套枚举说法**，因为只有枚举里的说法可被机器校验。想表达枚举外的判断 → 先往 `titlecheck.py` 里加谓词，不要自由发挥：
>
>    | 说法 | 成立条件 |
>    |---|---|
>    | `improved` / `rose` / `up` / `higher` | 末值 > 上一期 |
>    | `deteriorated` / `fell` / `down` / `lower` / `declined` | 末值 < 上一期 |
>    | `flat` / `unchanged` / `steady` / `stable` / `range-bound` | \|末值 − 上一期\| ≤ eps（默认 2%）|
>    | `flat to slightly down` / `flat to slightly up` | 方向对且幅度 ≤ eps（默认 3%）|
>    | `near lows` / `still low` | 末值落在窗口区间下 40% |
>    | `near highs` / `still high` | 末值落在窗口区间上 40% |
>    | `at a <N>-year high / low` | 末值 = 近 `N × 4` 期的最大/最小 |
>    | `highest / lowest since <期标签>` | 末值 = 该期以来的最大/最小。**卡在 N 年边界上时改用这个说法**，别硬写 N-year high |
>    | `more / fewer <…>` | 右轴末值 > / < 上一期 |
>    | `sharpest rise / drop (<A>, <B>)` | 括号里点名的 = 按变化量排序的前几名 |
>    | 标题里任何 `<数字>%` | 必须等于左轴或右轴的末值（容差 0.051）|
>
> 3. **出图前跑 `titlecheck.verify()`**，矛盾就 raise，跟压叠检查一样挂死。已实测：六种「照抄上季标题但数据已经反了」的情形全部拦下。
> 4. **不许把 B 类标题降级成 A 类**（比如把 `— improved on the quarter, still near lows` 整段删掉只留 `Interest coverage`）来绕过检查。判断句是这张图的结论，必须有。
> 5. **图内的高亮标注同样算 claim**，一起校验：图 17 末点旁的 `2.8% — 5-yr high`、图 5/图 6 灰线上方那行 `BDC sector average — quarterly through {行业最新期}`。

**数据标签**：

- 柱状图：值标在柱顶外侧，bold，**颜色 = 该系列颜色**。
- 折线图：值标在点上方（下方系列标下方），bold，同系列色。
- 堆叠柱：分段值标在**段内居中、白字 bold**；顶上溢出的小段（如 Rating 4+5）标在柱外，写成 `4+5: 0.5` 形式。
- **本季点高亮**：折线序列图（图 5、6、17、19）的最后一个点换成 `#A93226` 的大圆点（`ms=14`），标签也用 `#A93226`。
- 数据标签小数位与报告表格一致：占比 1 位（`12.5%`）、每股 2 位（`16.48`）、倍数 1 位（`5.9x`）。

**不许压叠 —— 出图前程序化检查，不靠肉眼**：

- 图内**任何两段文字不许互相压叠**：数据标签之间、数据标签与刻度标签、数据标签与轴标题、图例文字与曲线标签、右侧 ticker 与数值列、脚注与刻度标签 —— 全都算。
- 文字**不许压在坐标轴、刻度线、网格线上盖住读数**；不许被坐标区裁掉（`clip_on=True` 的 `ax.text` 跑到坐标区外就会被裁）。
- 这条**必须用代码强制**，写在 `chartlib.check()` 里、`save()` 自动调用：把所有 Text artist 的 display bbox 两两求交，交叠面积超过较小文字框的 18% 就 `raise`；同时检查开了 clip 的 `ax.text` 有没有超出坐标区。**报错就修布局，不许 `skip_check=True` 绕过。**
- 常见修法：加大 `figsize` 或 `subplots_adjust` 的边距、把标签的 `xytext` 偏移量调开、密集序列改成隔点标注、右侧标签按像素间距错开（见 §4.3 第 5 条）、长轴标签分两行。
- 注意 `bbox_inches='tight'` 只会把画布往外扩以容纳 `clip_on=False` 的文字，**不会**帮你解决两段文字互相压叠。

**图内脚注**（每张图都要有，放画布左下）：

- 格式：`* <口径与定义> Source: <具体来源，含页码/幻灯片号>`
- 色 `#5A6B7B`，字号约标题的 55%，非斜体。
- **手动换行，每行都要顶到画布右边缘再折**（用 `\n` 断，别让 matplotlib 自己溢出，也别在中间随意断）。折行后 2–4 行为宜。
- 来源要**具体到可复核**：`Source: OTF {CQ} 10-Q Note 5; {CQ} Earnings Presentation slide 14` / `Re-plotted from "Total Leverage (x)", Morgan Stanley Research, Private Credit Tracker {Q}, p.24` / `Figure 2 "PIK % of Net Investment Income" in J.P. Morgan, BDCs: PIKing into PIK ({date})`。
- 数据有洞就写明：`earlier gaps left blank, not interpolated`、`no {CQ} sector print yet`。

### 4.5 落盘与插入 Word

> ⛔ **下面这张 10.65 in 的宽度表已作废。**
> 报告是 **A4 竖版**（只有 2.6.1 横版），沿用 v3 的 1.15 in 边距，正文可用宽度 **7.12 in**，**图片插入宽 = 正文宽度的 85% = 6.05 in，居中**。
> 新规则是 **画布宽 = 插入宽 = 6.05 in（1:1）**，图内字号按 `00_layout.md` 的新字号表重定
> （标题 13pt / 脚注 7.5pt）。1:1 之后图内写多少 pt 纸上就是多少 pt，不用再算比例。
> v3 的纸已经是 A4 了，但画布还是 12–18 in，所以脚注在纸上只有 2.2–7.8 pt，
> 并排的图 10/11 只剩 2.2–2.4 pt。图 5/图 6 已经窄到 10.43 in，是全篇最好的 7.8 pt。

| 图 | `figsize[0]`（阶段一，写死）| Word 插入宽（阶段二）|
|---|---|---|
| **封面顶部长横条** `fig00_titlebar` | **7.11** | **7.11 in —— 与正文两端同宽，不走 85%** |
| 图 1 双饼（一张 PNG 内含左右两饼）| 6.05 | 6.05 in 居中 |
| 图 2–9、图 12、图 21 | 6.05 | **6.05 in 居中**（= 正文宽 7.12 in 的 85%）|
| **图 10 ‖ 图 11**（2.6.2）| **6.05**（不为并排重出）| **3.50 in 并排** |
| **图 13 ‖ 图 14**（2.6.3）| **6.05**（不为并排重出）| **3.50 in 并排** |
| **图 15 ‖ 16、17 ‖ 18、19 ‖ 20**（3.3，三组）| **6.05**（不为并排重出）| **3.50 in 并排** |
| T1 资产类型表 PNG | 6.05 | 6.05 in |
| T9 六家竞品表 | — | 2.6.1 横版节，10.54 in |

**三档宽度，张数写死**：`7.11 in` 只有封面横条 **1 张**；`3.50 in` 并排正好 **10 张**；其余全部 `6.05 in`。
`docxcheck.py` 会数张数，多一张少一张都报错。

阶段一的画布一律 **6.05 in**（封面横条 7.11 in），1:1，居中，图不再顶到正文两端。
那 10 张在阶段二插入时缩到 3.50 in 并排，每组合计 7.11 in（因此比单图宽一圈），
中间 0.11 in，两图之间不插文字，说明与分析合并成一段放在该组两图下方。
缩到 58% 后图内脚注按 4.3 pt 显示，口径与来源靠下方正文交代。细节见 `00_layout.md` 的「并排」一节。

## 折线的描点尺寸（写死）

**描点直径 = 线宽 × 2。** matplotlib 里 `markersize` 就是直径（pt），`linewidth` 也是 pt，直接乘：

```python
ax.plot(x, y, lw=2.0, marker='o', ms=chartlib.ms(2.0))   # ms = 4.0
```

以前是 `lw=3 / ms=7`，点比线粗一倍多，密集序列里点会盖住线、也会盖住相邻的点。
`guards.assert_marker_size()` 会硬查，不符合直接报错。要改比例改 `chartlib.MARKER_RATIO` 一处。

## 图内数值标签一律水平

**`rotation=0`，不许竖排、不许斜排。** 尤其是条形图上的数值 —— 竖着的数字读起来要歪头。
位置不够就把 y 轴上限抬高，或者把标签标到条形外侧，**不要转 90°**。

`guards.assert_flat_labels()` 扫 `ax.texts`（annotate / text / bar_label 产生的）里所有
`rotation != 0` 的，报错并列出是哪几段文字。x 轴刻度标签不在这个检查范围里 —— 长标签该转就转。

<details><summary>已作废的旧表（仅供追溯）</summary>

> ⛔ **下面这张 10.65 in 的宽度表已作废** —— 报告改成 A4 竖版，正文可用宽度只有 **6.69 in**。
> 所有插入宽度、`figsize` 上限、并排改上下的规则见 `00_layout.md` 的「页面与字体」一节。
> `figsize` 宽必须 ≤ 9.6 in，否则图内脚注插入后会缩到 5pt 以下。



命名：`fig{NN}_{slug}_{CQ}.png`，如 `fig02_cash_yield_Q226.png`。

| 图 | Word 插入宽度 |
|---|---|
| 图 1、2、3、4、7、8、9、15、16、18、19、20 | **10.65 in**（横向页满宽） |
| 图 17 | 10.28 in |
| 图 5 | 10.66 in |
| 图 6 | 10.66 in |
| 图 10 + 图 11 | 并排一行：5.50 in + 5.12 in |
| 图 12 | 8.28 in（单独一行，居中） |
| 图 13 + 图 14 | 并排一行：5.48 in + 5.19 in |
| 图 21 | 6.00 in |

</details>

图下方紧跟 Word 正文点评（正文体，不是斜体注释）；图内已有脚注，**Word 里不要再重复一遍来源**。

---
