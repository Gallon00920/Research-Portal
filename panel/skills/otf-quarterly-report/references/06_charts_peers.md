# 图 10–14 · BDC 竞品对比（§2.6.2 / §2.6.3）

### § 2.6.2 / 2.6.3 BDC 竞品对比（图 10–14）


六家：**OTF、ARCC、BXSL、OBDC、TSLX、GBDC**。起始 6 期（`1Q25 – 2Q26` 式标签），按 §3.5 只右加不删，累积到 8 期两年后才裁左端。
数据源：`competitor earnings\` 五份当季 filings + `OTF\` 当季 10-Q；历史各期从各家历史 filing / earnings release 取。
**GBDC 财年 9/30**，一律换算到日历季度并在注释写明。

> ### ⛔ 这五张图的配色已改：纯白底 + Palette A
>
> - **底色必须是纯白 `#FFFFFF`**，不是米黄 `#FCFCFB`。figure 和 axes 都要设。
> - **字体 Lato**，跟全篇一致，不用 DejaVu Sans。
> - **线条颜色只能取 §4.3 的 ticker 配色表**：OTF `#A93226`（唯一红色，`lw=4`、`ms=8`）、ARCC `#4B5B6E`、BXSL `#C9A227`、OBDC `#9DB8D2`、TSLX `#AEB4BC`、GBDC `#2E6DA4`；peer `lw=2.2`、`ms=6`。原来那套亮蓝 `#2A78D6` / 琥珀 `#EDA100` / 翠绿 `#008300` / 紫 `#4A3AA7` / 亮红 `#E60012` **全部作废**。
> - 标题色 `#16283F`、副标题与底部注释 `#5A6B7B`、网格 `#E3E7EC`、右侧数值列 `#000000`（纯黑）。
> - **版式不变**：左对齐标题 + 副标题 + 右侧「虚线 → ticker 粗体 → 数值列」三段式 + 底部注释 + 无图例。逐项照做，见 §4.3。
> - 同一个 ticker 在图 9 和图 10–14 里必须是同一个颜色，出图后并排看一眼确认。

| # | 位置 | 标题 | 副标题 | y 轴 | 特殊规则 |
|---|---|---|---|---|---|
| **10** | 2.6.2（与图 11 并排） | `BDC NAV per Share  \|  {首期} – {CQ}` | `Net asset value (NAV) per share, USD at quarter end   ·   Source: company 10-Q filings and quarterly earnings releases` | USD，不从 0 起 | 数值 2 位小数。**注意**：`{首期}` 随 §3.5 的窗口滚动而变，标题里的期间串要跟着改 |
| **11** | 2.6.2（与图 10 并排） | `BDC Dividend Yield on NAV  \|  …` | `Annualized dividend yield on net asset value, %   ·   Source: …` | `%` 整数刻度 | 口径 =（当季宣派 base + supplemental/special）× 4 ÷ 期末 NAV/股；OTF 的 $0.05 特别股息按 OTF 自己归属的季度计入；数值 1 位小数 |
| **12** | 2.6.2（单独一行，居中） | `BDC PIK Income  \|  …` | `Payment-in-kind income as a share of total investment income, %   ·   Source: company 10-Q and 10-K filings` | `%` | 注释写明「BXSL / TSLX 只披露 PIK interest」「无独立 filing 的季度用 10-K 减 10-Q YTD」；数值 1 位小数 |
| **13** | 2.6.3（与图 14 并排） | `BDC Non-Accrual Rate  \|  …` | `Non-accrual investments as a share of the total portfolio at fair value, %   ·   Source: company earnings releases and 10-Q filings` | `%`，1 位小数刻度 | **披露为 `<0.1%` 的点画在 0.05%**，注释明确「读作低于 0.1%」；注释写明「ARCC / BXSL 分子只含 non-accrual loans，读数略低」 |
| **14** | 2.6.3（与图 13 并排） | `BDC Portfolio Company Average EBITDA  \|  …` | `Average annual EBITDA of the underlying portfolio companies, USD millions   ·   Source: company earnings and investor presentations` | USD mm，不从 0 起 | **GBDC 只披露中位数** → ticker 写成 `GBDC*`，注释说明「读趋势不读绝对水平」；注释列出各家口径差异（ARCC 公司投资、公允值加权；BXSL private debt LTM；OBDC 债券组合 91.5%；TSLX core portfolio；OTF 一二级抵押借款人）；数值取整 |

---
