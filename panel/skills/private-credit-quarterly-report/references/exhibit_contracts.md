# 图表契约 · 58 张 exhibit 逐张

> 格式照 `otf-quarterly-report/references/05_charts_otf.md`。每张一个块，字段固定。
> **spec 没写的地方就是下一季会出错的地方** —— 上一季踩过 15 处，全在原先没写到的字段上。

> ⚠ 本文件由 `gen_contracts.py` 从 `series.json` + `exhibit_manifest.json` 自动生成（本季 = 2026Q3）。改了账本就重跑，别手改这份。
>
> **真值来源**：口径与版式的真值是**上一版成稿**（`assets/example-*.docx`），数字一律不许从它抄；
> 数值的真值是本季文件夹里的源文件。每块的「数据源」都给到 `<子目录>/<文件名>` + slide/sheet 定位。
>
> **下一季怎么用**：照「数据源」那一行去本季文件夹找同名（或同位置）的新文件，
> 按「构成」和「锚点校验」重取一遍。**文件名会变，子目录和 slide 标题一般不变 ——
> 所以定位一律写 slide 的标题文字，不写页码**（MS tracker 的页码每季都挪）。

---

#### 图 1 · Private debt AUM (US$bn) by channel, 2015–2025

- **slug**：`mkt_aum_by_channel`（稳定标识，编号会变、slug 不变）
- **位置**：`2.1`，版式 `solo`（满宽单图）
- **形状**：`series_stacked`　**出图函数**：`stacked_with_rhs()` in `build_s2.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  stacked_with_rhs('mkt_aum_by_channel', 'solo', 3.1, '',
  ['Institutional', 'Retail', 'Insurance estimate'], rhs=False,
  label_last_only=False, dollar_y=True,
  legend_loc='upper left', legend_ncol=3)
  ```
- **数据源**：
  - `2026Q3/Market/2025-annual-global-private-debt-report.pdf`
  - `2026Q3/Market/2025-annual-global-private-debt-report-summary-xls.xlsx`
  - 定位：「Debt AUM」 / 「*As of 6/30/2025」 / 「Private debt AUM ($B) by channel」 / 「Share of private debt AUM by channel」
- **取数与构成**（本季实际做法，下季照做）：
  - 机构渠道 = 2025-annual-global-private-debt-report-summary-xls.xlsx，sheet "Debt AUM" 第 8/9/10 行（Dry powder / NAV / Total AUM ($B)），标注 "*As of 6/30/2025"，逐年精确值。
  - 零售与保险 = 2025-annual-global-private-debt-report.pdf 第 3 页（印刷页 2）"Private debt AUM ($B) by channel" 堆叠图，按像素测量色带高度反算（#1D5080 机构 / #6185A6 零售 / #40C2C9 保险），标定用机构段对齐 xlsx 精确值，2015–2024 误差 −1.8%~+0.5%；2025 一列改用第 5 页（印刷页 4）donut "Share of private debt AUM by channel" 的明标值（总额 $2,557B，机构 77.1% / 零售 15.5% / 保险 7.4%），属 exact 而非近似。
  - ⚠ 与 v2 成稿的数字化结果有差异：v2 的各年总计为 609/704/851/988/1109/1326/1605/1800/2231/2372/2557，本次为 606/705/849/995/1114/1336/1630/1830/2251/2402/2557，中间年份最大差约 30bn。
  - 两者都是从同一张图数字化，本次的方法以 xlsx 精确机构值做标定（误差 −1.8%~+0.5%）、且 2025 用 donut 明标值，故采用本次结果。
  - 差异已记录，供人工裁定
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 2025 一列改用第 5 页（印刷页 4）donut "Share of private debt AUM by channel" 的明标值（总额 $2,557B，机构 77.1% / 零售 15.5% / 保险 7.4%），属 exact 而非近似
  - 两者都是从同一张图数字化，本次的方法以 xlsx 精确机构值做标定（误差 −1.8%~+0.5%）、且 2025 用 donut 明标值，故采用本次结果
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`2025`　｜　该口径源上限：`2025`
  - 本季文件夹里同主题最新：`2025`（同口径）—— 2025-annual-global-private-debt-report(-summary-xls).pdf/xlsx（PitchBook 年度私债报告，全书最新一期是 2025 年度）
  - 下季去哪儿看源末期：Market/2025-annual-global-private-debt-report-summary-xls.xlsx，sheet "Debt AUM" 最后一个有值的年份列
- **脚注（本季实际印出的）**：
  ```
  Note: Institutional bars are exact PitchBook values (dry powder + NAV) as of 30 Jun 2025; retail and insurance are digitised from the source stacked chart for 2015–2024 and exact for 2025 (total US$2,557bn, split at the labelled 77.1 / 15.5 / 7.4 %; retail and insurance as of 31 Dec 2025). Source: PitchBook.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 1 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 2 · US leveraged credit market in 1Q26 — total US$4.4tn

- **slug**：`mkt_us_levcredit_split`（稳定标识，编号会变、slug 不变）
- **位置**：`2.1`，版式 `solo`（满宽单图）
- **形状**：`shares`　**出图函数**：`two_panel_pie()` in `build_s2.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  two_panel_pie('mkt_us_levcredit_split', h=2.9)
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Market Technicals | Sizing the Private Credit (Direct Lending) Market」 / 「US Leveraged Credit Market in 1Q26 / Total: $4.4 Trillion」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Market Technicals | Sizing the Private Credit (Direct Lending) Market"，图 "US Leveraged Credit Market in 1Q26 / Total: $4.4 Trillion" 的明标值（Leveraged Loans $1.5tn 35% / High Yield $1.5tn 33% / Private Credit $1.4tn 32%；持有人 BDCs 38% / Direct Lending Funds 29% / PC CLOs 14% / Pensions 11% / Insurers 8%）。
  - 来源行照抄 slide 脚注：PitchBook | LCD, ICE, BDC Collateral, Moody's, Public Pension Data, Morgan Stanley Research
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Market Technicals | Sizing the Private Credit (Direct Lending) Market"，图 "US Leveraged Credit Market in 1Q26 / Total: $4.4 Trillion" 的明标值（Leveraged Loans $1.5tn 35% / High Yield $1.5tn 33% / Private Credit $1.4tn 32%
- **脚注（本季实际印出的）**：
  ```
  Note: Left: US leveraged credit by market. Right: holders of the US$1.4tn private credit stack. All values as labelled in the source. Insurer and pension exposure are estimates (2.2% and 2% respectively per the source note). Source: PitchBook | LCD, ICE, BDC Collateral, Moody's, Public Pension Data, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 2 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 3 · Private debt institutional fund AUM (US$bn)

- **slug**：`mkt_inst_aum_decomp`（稳定标识，编号会变、slug 不变）
- **位置**：`2.2`，版式 `pairL`（并排左）
- **形状**：`series_stacked`　**出图函数**：`stacked_with_rhs()` in `build_s2.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  stacked_with_rhs('mkt_inst_aum_decomp', 'pair', 2.5, '',
  ['Dry powder', 'NAV'], rhs=True, label_total=False, dollar_y=True)
  ```
- **数据源**：
  - `2026Q3/Market/2025-annual-global-private-debt-report.pdf`
  - `2026Q3/Market/2025-annual-global-private-debt-report-summary-xls.xlsx`
  - 定位：「Debt AUM」 / 「*As of 6/30/2025」
- **取数与构成**（本季实际做法，下季照做）：
  - 2025-annual-global-private-debt-report-summary-xls.xlsx，sheet "Debt AUM" 第 8/9/10 行（Dry powder / NAV / Total AUM ($B)），标注 "*As of 6/30/2025"；Dry powder as % of NAV 为自算 = Dry powder ÷ NAV
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`2025`　｜　该口径源上限：`2025`
  - 本季文件夹里同主题最新：`2025`（同口径）—— 2025-annual-global-private-debt-report(-summary-xls).pdf/xlsx（PitchBook 年度私债报告，全书最新一期是 2025 年度）
  - 下季去哪儿看源末期：同上
- **脚注（本季实际印出的）**：
  ```
  Note: Institutional channel only; dry powder plus NAV. The right-hand line is dry powder as a percentage of NAV (Junson calculation). Source: PitchBook, as of 30 Jun 2025.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 3 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 4 · Private debt fundraising activity

- **slug**：`mkt_fundraising`（稳定标识，编号会变、slug 不变）
- **位置**：`2.2`，版式 `pairR`（并排右）
- **形状**：`series_stacked`　**出图函数**：`stacked_with_rhs()` in `build_s2.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  stacked_with_rhs('mkt_fundraising', 'pair', 2.5, '',
  ['Capital raised'], rhs=True, rhs_fmt='{:.0f}',
  label_last_only=False)
  ```
- **数据源**：
  - `2026Q3/Market/2025-annual-global-private-debt-report.pdf`
  - `2026Q3/Market/2025-annual-global-private-debt-report-summary-xls.xlsx`
  - 定位：「Debt fundraising」 / 「*As of 12/31/2025」
- **取数与构成**（本季实际做法，下季照做）：
  - 2025-annual-global-private-debt-report-summary-xls.xlsx，sheet "Debt fundraising" 第 7/8 行（Capital raised ($B) / Fund count），标注 "*As of 12/31/2025"
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`2025`　｜　该口径源上限：`2025`
  - 本季文件夹里同主题最新：`2025`（同口径）—— 2025-annual-global-private-debt-report(-summary-xls).pdf/xlsx（PitchBook 年度私债报告，全书最新一期是 2025 年度）
  - 下季去哪儿看源末期：同上（sheet 里 Capital raised / fund count 的最后一年）
- **脚注（本季实际印出的）**：
  ```
  Note: Equity capital only, counted at final close; 2025 understates the final total because of late-reporting funds. Source: PitchBook, as of 31 Dec 2025.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 4 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 5 · Direct lending origination (US$bn, monthly)

- **slug**：`mkt_dl_origination`（稳定标识，编号会变、slug 不变）
- **位置**：`2.3`，版式 `pairL`（并排左）
- **形状**：`series_stacked`　**出图函数**：`stacked_with_rhs()` in `build_s2.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  stacked_with_rhs('mkt_dl_origination', 'pair', 2.5, 'US$bn',
  ['Refi', 'Non-refi'], rhs=True, rhs_fmt='{:.0f}%',
  label_total=False, dollar_y=True,
  legend_loc='below', legend_ncol=3)
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Deal Activity | Refinancing and New Money Both Slowed in May」 / 「Direct Lending Origination ($B)」 / 「~$87bn」 / 「-24% y/y」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide "Deal Activity | Refinancing and New Money Both Slowed in May" 右上图 "Direct Lending Origination ($B)"（来源标 KBRA, Morgan Stanley Research），Refi/Nonrefi 两色堆叠，Jan-21–May-26 共 65 个月，按像素测量。
  - y 轴用左侧 10 个刻度标签（$45…$0）线性拟合，最大残差 0.09bn。
  - ⚠ 扫描窗口必须避开 y 500–545（x 2615–2733）的图例色块 —— 第一次没避开，图例被并进相邻柱，出现一根满格假柱。
  - 锚点：测出的 2026 年 1–5 月合计 86.2bn，对同一 slide 披露的 "~$87bn" 差 -0.9%；测出的同比 -24.6%，对披露的 "-24% y/y" 差 0.6pp。
  - % non-refi 是 Junson 用测出的两个分项算的 3 个月移动平均。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - y 轴用左侧 10 个刻度标签（$45…$0）线性拟合，最大残差 0.09bn
  - 锚点：测出的 2026 年 1–5 月合计 86.2bn，对同一 slide 披露的 "~$87bn" 差 -0.9%
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`May-26`　｜　该口径源上限：`May-26`
  - 本季文件夹里同主题最新：`2Q26`（**口径不同**）—— q2-2026-us-private-credit-and-middle-market-quarterly-wrap.xlsx，sheet "01 DL Volume"
  - 为什么不能用它续：那张 sheet 是季度直贷总量，本图是月度 refi / non-refi 拆分 —— 全文件夹只有 tracker（1Q26 deck，月度到 May-26）给这个拆分。2Q26 的季度总量已写进本图 aux 与正文，但不能拿去续这条月度线。
  - 下季去哪儿看源末期：Market/MS Private Credit 1Q26 tracker.pdf，slide "Deal Activity | Refinancing and New Money Both Slowed in May" 右上图横轴最后一个月
- **脚注（本季实际印出的）**：
  ```
  Note: Monthly refi / non-refi origination values are digitised approximations from the source chart; the % non-refi share of total (right scale) is a three-month moving average calculated by Junson from those approximations. Our digitised Jan–May 2026 total of US$86.2bn reconciles to the ~US$87bn (-24% y/y) disclosed on the same slide. The monthly series ends in May 2026 because its only source in this quarter’s folder is Morgan Stanley’s 1Q26 tracker, whose monthly panel runs through May 2026. The 2Q26 PitchBook | LCD wrap carries quarterly direct-lending volume through 2Q26 but not the refinancing / non-refinancing split, so no later print of this measure exists. Source: KBRA, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 5 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 6 · LBOs financed in BSL vs private markets (by count)

- **slug**：`mkt_lbo_bsl_vs_private`（稳定标识，编号会变、slug 不变）
- **位置**：`2.3`，版式 `pairR`（并排右）
- **形状**：`series_grouped`　**出图函数**：`grouped_with_rhs()` in `build_s2.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  grouped_with_rhs('mkt_lbo_bsl_vs_private', 'pair', 2.5, 'LBO count')
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Deal Activity | Refinancing and New Money Both Slowed in May」 / 「LBOs Financed in BSL vs Private Markets (By Count)」 / 「% Private Credit in LTM (rs)」 / 「~80%」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Deal Activity | Refinancing and New Money Both Slowed in May"（与 Ex 5 同一张）右下图 "LBOs Financed in BSL vs Private Markets (By Count)"（来源标 PitchBook | LCD, Morgan Stanley Research），Syndicated Loans / Private Credit 两色分组柱 + "% Private Credit in LTM (rs)" 折线，1Q19–1Q26 共 29 个季度，按像素测量。
  - 左轴用 90…0 十个刻度标定（6.0375 px/笔），右轴用 100%…0% 标定（5.433 px/%）。
  - ★ 交叉校验：用测出的笔数自己算 LTM 占比，与测出的绿线逐点比，26 个可比点差 +0.0~+1.1pp（系统性略高，来自柱顶取整），末点 83.3% 对 82.5%；slide 标题写 "~80%"，基线成稿写 "ends ~83%" —— 三者一致。
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`1Q26`　｜　该口径源上限：`1Q26`
  - 本季文件夹里同主题最新：`2Q26`（**口径不同**）—— q2-2026-us-private-credit-and-middle-market-quarterly-wrap.xlsx，sheet "03 LBO Volume"
  - 为什么不能用它续：那张 sheet 只有 Period / Estimated volume ($B) / Count 三列（逐 sheet 查过），没有「银团 vs 私募」的拆分；本图画的就是这个拆分，全文件夹只有 tracker 有。
  - 下季去哪儿看源末期：同一 slide 右下图横轴最后一个季度
- **脚注（本季实际印出的）**：
  ```
  Note: LBO count financed in the broadly syndicated market versus the private markets. Bar values and the % private credit LTM line (right scale) are digitised approximations from the source chart. As a check, recomputing the LTM share from our own digitised counts reproduces the source line to within 1.1pp at every point and ends at 83.3% against the 82.5% we read off the line. The series ends in 1Q26 because the broadly-syndicated-versus-private split by deal count appears only in Morgan Stanley’s 1Q26 tracker. The 2Q26 PitchBook | LCD wrap reports private-market LBO volume and counts through 2Q26 but gives no syndicated-versus-private split, so no later print of this measure exists. Source: PitchBook | LCD, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 6 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 7 · US MM CLO new issuance and avg. MM CLO 'AAA' spread

- **slug**：`mkt_mmclo_issuance_spread`（稳定标识，编号会变、slug 不变）
- **位置**：`2.4`，版式 `solo`（满宽单图）
- **形状**：`series_stacked`　**出图函数**：`bars_with_rhs_gappy()` in `build_s3.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  bars_with_rhs_gappy('mkt_mmclo_issuance_spread', 'solo', 2.9, 'New issuance (US$bn)')
  ```
- **数据源**：
  - `2026Q3/Market/2Q26 S&P Direct Lending.pdf`
  - 定位：「CLO Issuance | 'AAA' Spreads Widen; Basis Widens Between BSL And MM CLOs」 / 「Private Credit And Middle-Market CLO Quarterly – Q2 2026」 / 「New issue (U.S. bil. $)」 / 「spread annual averages approximated from source chart」
- **取数与构成**（本季实际做法，下季照做）：
  - 2Q26 S&P Direct Lending.pdf（S&P Global Ratings, "Private Credit And Middle-Market CLO Quarterly – Q2 2026"），slide 标题 "CLO Issuance | 'AAA' Spreads Widen; Basis Widens Between BSL And MM CLOs"。
  - 柱子（年度 MM CLO 新发）取该 slide 下方 "New issue (U.S. bil. $)" 表格里的明值，逐年精确，不是量出来的；MM 占全部 CLO 发行的比例、resets/refis、YTD 三个月和同比变动，同表明值。
  - AAA 利差线：该 slide 的图是月度的（Jan 2020–Mar 2026），原图无点值，按颜色扫列像素还原后再按年取均值 —— 这一步和 report-spec 里 "spread annual averages approximated from source chart" 一致。
  - y 轴标定：左轴 0 在 y=719、50 在 y=423（11 条网格线等距校验过），右轴 0–300 bps 共用同一像素跨度。
  - 交叉校验（重要）：把量出来的月度柱值按年加总，和表格明值对比 —— MM 2020/21/22/23/24/25 差 −1.8/−4.7/+0.2/−0.3/−1.3/−2.6%，BSL 差 −2.6/−1.3/−2.1/−2.5/+2.6/−1.3%，2025 年 1–3 月 MM 量得 10.13 对明值 10.13 完全吻合。
  - 说明同一套 y 标定误差在 ±3% 内，利差线用的是同一标定，所以可信区间同量级。
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`26 YTD`　｜　该口径源上限：`26 YTD`
  - 本季文件夹里同主题最新：`26 YTD`（同口径）—— 2Q26 S&P Direct Lending.pdf，New issue 表（表头自己写 "2026 YTD through March"）
  - 下季去哪儿看源末期：Market/2Q26 S&P Direct Lending.pdf 的 "New issue (U.S. bil. $)" 表：最后一个完整年度 + 本年 YTD 那一列（本季是 through March）
- **脚注（本季实际印出的）**：
  ```
  Note: Bars show annual US middle-market CLO new issuance as disclosed by S&P Global Ratings; the line shows the average middle-market CLO ‘AAA’ tranche spread over SOFR, computed as the mean of the monthly prints shown in the source chart, which begins in January 2020. Issuance figures are exact as disclosed; spread averages are approximated from the source chart. Hollow markers mark periods for which the source chart shows fewer than nine monthly spread prints (2020: two months, both before the March 2020 selloff; 2021: seven; 2022: six; 2026 year to date: three), and those means are not full-year averages. ‘26 YTD’ is the source’s own year-to-date definition — the S&P table header reads ‘2026 YTD through March’ — not a window we shortened; its issuance is US$9.54bn and its spread mean 144bp. Sources: S&P Global Ratings and LevFin Insights.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 7 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 8 · Private debt vs public assets: return, volatility and Sharpe (2015 – Mar 2026)

- **slug**：`ret_risk_return_table`（稳定标识，编号会变、slug 不变）
- **位置**：`3.1`，版式 `table`（表格）
- **形状**：`rows_flat`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Performance | Private Versus Public Credit Performance Summary」 / 「Total returns, volatility, Sharpe ratio, and correlation across assets / 2015 - 2026 (Mar)」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Performance | Private Versus Public Credit Performance Summary"，表 "Total returns, volatility, Sharpe ratio, and correlation across assets / 2015 - 2026 (Mar)" 的全部明标值，文本层可直接读出。
  - 来源行照抄 slide 脚注：Lincoln International VOG, PitchBook | LCD, Bloomberg, Morgan Stanley Research
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Performance | Private Versus Public Credit Performance Summary"，表 "Total returns, volatility, Sharpe ratio, and correlation across assets / 2015 - 2026 (Mar)" 的全部明标值，文本层可直接读出
- **脚注（本季实际印出的）**：
  ```
  Note: Quarterly returns, 2015 to March 2026; the source states data are as of 4Q25. Private debt returns and Sharpe ratios are based on the Lincoln International index, which is valued by a discounted-cash-flow "fair value" approach rather than market prices — the low volatility and high Sharpe ratios are partly a smoothing artefact and are not comparable with mark-to-market series. Source: Lincoln International VOG, PitchBook | LCD, Bloomberg, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 8 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 9 · Private vs public credit: Lincoln senior debt vs single-B loans trailing 12-month total returns, with US high yield yield-to-worst (quarterly)

- **slug**：`ret_dl_vs_bsl_total_return`（稳定标识，编号会变、slug 不变）
- **位置**：`3.1`，版式 `solo`（满宽单图）
- **形状**：`series_lines`　**出图函数**：`qlines()` in `build_s5.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  qlines('ret_dl_vs_bsl_total_return', 'tall', 4.2, 'Percent', every=4, fmt='{:.1f}%',
  dys=[9, -14, -14], styles=('-', '-', '--')
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Performance | Private Versus Public Credit Yields and Returns」 / 「Annual Total Returns」 / 「Yield (2017-Now)」 / 「2015 - 2026 (Mar)」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Performance | Private Versus Public Credit Yields and Returns"，页面【右】半边那张图 "Annual Total Returns"（三条线：Lincoln Senior Debt Index / Morningstar LSTA US Single B Loans / Morningstar LSTA US Lev Loans；纵轴 -15%–25%；横轴 Dec-14 至 Mar-26，标签每两季一个，共 46 期）。
  - ⚠ 这是**回报**口径，和同一页左图的**收益率**（Ex 9）不是一件事 —— 两张图起点不同是因为 MS 自己的收益率历史只到 2017（同一份 deck 的 p40 汇总表把收益率那行单独标成 "Yield (2017-Now)"，回报那几行标的是 "2015 - 2026 (Mar)"）。
  - 全序列像素还原：y 轴用 9 个刻度标签的像素行定间距（25% 在 y=1483，-15% 在 y=2067，每 1pp 14.60px），零点取源图 0 轴灰线的中心 y=1851（不用标签中心，差 3px = 0.2pp）；x 轴用 23 个横轴标签定间距（每 2 季 60.32px → 每季 30.16px），4Q14 在 x=2164，末点算出 x=3521 与轴线末端 3525 吻合。
  - 锚点校验用同一页正文的三句话：1Q26 Lincoln 量得 8.73（正文写 8.7，残差 0.03pp）、1Q26 Morningstar 量得 4.83（正文写 4.8，残差 0.03pp）、近 10 年两者均值差量得 2.49pp（正文写 2.6pp，残差 0.11pp）。
  - 三个坑：图例是白底方框（y1438–1576 / x2156–2951），不排掉会量出 26.4% / 23.4% 的假值；两条 Morningstar 线同色 (208,184,106)、大部分区间几乎重合，本序列取每列金色的下沿，只在 3Q20/3Q23/1Q24/2Q24 能分出两段；4Q14 与 1Q15 折线压在 0 轴上量不出来 —— 源图在那儿画的就是 0（T12M 回报需要 12 个月历史），按 Alex 要求显式填 0 画出来，不留空。
  - 另：1Q21 那根金色尖峰的顶伸进图例框，量到 18.73%，源图肉眼约 19.5%，可能被白底削平一截。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 锚点校验用同一页正文的三句话：1Q26 Lincoln 量得 8.73（正文写 8.7，残差 0.03pp）、1Q26 Morningstar 量得 4.83（正文写 4.8，残差 0.03pp）、近 10 年两者均值差量得 2.49pp（正文写 2.6pp，残差 0.11pp）
- ⛔ **横轴写死**：⛔ 横轴全数字 YYYY/MM，**起点 2015/12，写死**（Alex 2026-08-24 最终版：「把14年的数据取消，从2015年12月开始画。现在写死这个」）。逐年 12 月一个刻度。4Q14–3Q15 那 4 期不画，但全量历史冻结在 series_bank（回报 + ICE 各一条），不许删。
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`1Q26`　｜　该口径源上限：`1Q26`
  - 本季文件夹里同主题最新：`1Q26`（同口径）—— MS Private Credit 1Q26 tracker.pdf p41 右图；Broker\Connecting the Dots Around Private Credit.pdf p20 Exhibit 34 是同一条序列的另一次发表，但只到 Dec-25，更短
  - 下季去哪儿看源末期：回报两条看下一季 tracker 同一张 slide "Performance | Private Versus Public Credit Yields and Returns" 的【右】图横轴末期；ICE 看 FRED BAMLH0A0HYM2SYTW 的最新季末。⛔ 历史点冻结，只追加。
- **脚注（本季实际印出的）**：
  ```
  Note: Trailing-twelve-month total return on Lincoln International’s senior debt index versus Morningstar LSTA US single-B loans, quarterly from 4Q15, with the ICE BofA US High Yield index semi-annual yield-to-worst overlaid for context. The two loan-market lines are total returns and the high-yield line is a yield — different measures shown on one chart, not one series: returns here fall to -8.8% (1Q20) and rise to 18.7% (1Q21), ranges a yield cannot take. Lincoln returns are fair-value based estimates from proprietary discounted cash flows, not observed market prices. The chart begins in 4Q15 by the report owner’s choice; the source chart runs from 4Q14, and the four earlier quarters remain frozen in the data ledger. Return endpoints are as stated in the source text (8.7% and 4.8% in 1Q26); intermediate points are digitised approximations that reproduce those endpoints to within 0.03pp and the source’s stated ten-year average gap of 2.6pp to within 0.11pp. High-yield values are exact daily index data taken at each quarter end. The source chart also plots Morningstar LSTA US leveraged loans (all loans); it is drawn in the same colour as the single-B line and is visually inseparable from it in all but four quarters, so it is not reproduced here. Sources: Lincoln International VOG and PitchBook | LCD via Morgan Stanley Research; ICE BofA via FRED (BAMLH0A0HYM2SYTW).
  ```
- **口径对账**（与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 9 并排比过，比了：横轴起止、序列条数、口径、端点值、2014–15 段）：
  - ✓ 一致：横轴 4Q14–1Q26 共 46 期（基线也是 2014/12 起）
  - ✓ 一致：序列三条
  - ✗ **有出入**：基线把这张图标成 "yields" 并印了收益率端点 9.7/8.4，但它 2014–2021 段的形状既不匹配 p41 左图（收益率）也不匹配右图（回报）—— 尤其 4Q14–1Q15 画成了 8.7%/12.7% 一带，而回报源图那两期是 0。Alex 2026-08-24 确认：同事的本意就是画 MS 的回报图，「不过他是把 14 15 部分数据点画错了」。
  - ✗ **有出入**：本季端点标签是 8.7 / 4.8（回报）+ 7.4（YTW），不是基线的 9.7 / 8.4 / 7.3 —— 前者是回报口径的正确端点，后两个收益率水平改在正文里引用（aux.yield_context）。
  - ✗ **有出入**：起点：基线画 2014/12 起；本季按 Alex 2026-08-24 最终指示从 2015/12 起画（正好避开 T12M 前两期为 0 的那段），4Q14–3Q15 冻结在 series_bank。
  - 结论：按 Alex 指示重画为「回报两条 + HY YTW 一条」，46 期全从源头取数（回报像素还原带三锚点，HY 为 FRED 精确值），2014–15 的 0 显式画出。
  - 谁比的：Claude 2026-08-24，Alex 2026-08-24 定稿
  - 下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 10 · DL new origination spreads vs Single B BSL (bps)

- **slug**：`ret_dl_spread_vs_bsl`（稳定标识，编号会变、slug 不变）
- **位置**：`3.2`，版式 `pairL`（并排左）
- **形状**：`series_lines`　**出图函数**：`lines()` in `build_s2.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  lines('ret_dl_spread_vs_bsl', 'pair', 2.5, 'bps', fmt='{:,.0f}', step=6)
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Deal Activity | Deal Pricing Still Stable Despite Stress in Public Loans」 / 「Direct Lending New Origination Spreads」 / 「Unitranche Deals (Rolling 90 Days)」 / 「Single B BSL」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide "Deal Activity | Deal Pricing Still Stable Despite Stress in Public Loans" 左图 "Direct Lending New Origination Spreads"（来源标 KBRA, PitchBook | LCD, Morgan Stanley Research），两条线 "Unitranche Deals (Rolling 90 Days)" 与 "Single B BSL"，Nov-22–May-26 共 43 个月，按像素测量。
  - y 轴用 9 个刻度标签（700…300）线性拟合，最大残差 0.32bp。
  - ★ 三个锚点：末点 unitranche 量得 505.4 对图上明标 508（−2.6bp）、single B 量得 428.8 对明标 430（−1.2bp）、Feb-26 量得 489.1 对同页正文 "the trough of 490bp in February"（−0.9bp），且该点正是全序列最低 —— 三个锚点都在 3bp 内。
  - 两个末点入账用明标值 508 / 430。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - y 轴用 9 个刻度标签（700…300）线性拟合，最大残差 0.32bp
  - ★ 三个锚点：末点 unitranche 量得 505.4 对图上明标 508（−2.6bp）、single B 量得 428.8 对明标 430（−1.2bp）、Feb-26 量得 489.1 对同页正文 "the trough of 490bp in February"（−0.9bp），且该点正是全序列最低 —— 三个锚点都在 3bp 内
  - 两个末点入账用明标值 508 / 430
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`May-26`　｜　该口径源上限：`May-26`
  - 本季文件夹里同主题最新：`2Q26`（**口径不同**）—— q2-2026-us-private-credit-and-middle-market-quarterly-wrap.xlsx，sheet "05 Spread"
  - 为什么不能用它续：那张 sheet 是季度新发利差，本图是 rolling-90-day 月度口径，两者不是同一条线的延续。2Q26 的季度值已写进正文。
  - 下季去哪儿看源末期：tracker slide "Deal Activity | Deal Pricing Still Stable Despite Stress in Public Loans" 左图横轴最后一个月
- **脚注（本季实际印出的）**：
  ```
  Note: Direct lending new-origination spreads over base rate — unitranche deals on a rolling 90-day basis against single-B broadly syndicated loans. The two endpoints (508bp and 430bp) are as labelled in the source; intermediate points are digitised approximations that reproduce the labelled endpoints to within 3bp and independently reproduce the February trough of 490bp stated in the source text. The rolling-90-day series ends in May 2026 because its source is the 1Q26 tracker’s monthly panel. The 2Q26 PitchBook | LCD wrap reports quarterly new-issue spreads through 2Q26, but on a quarterly rather than a rolling-90-day basis, so it is not a continuation of this series. Source: KBRA, PitchBook | LCD, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 10 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 11 · Spread of DL new originations by EBITDA cohort (bps)

- **slug**：`ret_dl_spread_by_ebitda`（稳定标识，编号会变、slug 不变）
- **位置**：`3.2`，版式 `pairR`（并排右）
- **形状**：`bars_grouped_categorical`　**出图函数**：`grouped_cat2()` in `build_s5.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  grouped_cat2('ret_dl_spread_by_ebitda', 'pair', 2.9, 'Spread (bp)',
  wrap=lambda s: _W11.get(s, s)
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Deal Activity | Deal Pricing Still Stable Despite Stress in Public Loans」 / 「Spread of Direct Lending New Originations (bp)」 / 「像素行→bp」 / 「upper MM spreads widened the most across size cohorts (+23bp YTD)」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Deal Activity | Deal Pricing Still Stable Despite Stress in Public Loans"，右下图 "Spread of Direct Lending New Originations (bp)"（分组柱，三个系列 YE 24 / YE25 / May 26，五个类别：EBITDA <$20m / $20m–<$50m / $50m–<$100m / $100m+ / Single B Syndicated Loans）。
  - May 26 那一组五根柱子图上都标了数（516 / 505 / 511 / 516 / 430），直接取用；YE24 与 YE25 无标注，像素还原 —— 标定方式是拿这 5 个明标点对「像素行→bp」做一次线性拟合（value = −0.67775·y + 1180.94），回代残差最大 0.35bp，比先按刻度标签标定更稳（按刻度标签会整体偏 20bp，因为最上面那个标签是 560 不是 580）。
  - 独立校验（关键）：拟合出来的 YE25 让 $100m+ 的 YTD 变动正好是 +23bp，与 slide 正文 "upper MM spreads widened the most across size cohorts (+23bp YTD)" 完全一致；而 sub-$50mm 两档量得 +3bp / +1bp，也对应正文 "spread changes have been more muted for sub-$50mm cohorts"。
  - ⚠ 原图纵轴截断在 380bp，本报告按新规则重画为从 0 起。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - YE24 与 YE25 无标注，像素还原 —— 标定方式是拿这 5 个明标点对「像素行→bp」做一次线性拟合（value = −0.67775·y + 1180.94），回代残差最大 0.35bp，比先按刻度标签标定更稳（按刻度标签会整体偏 20bp，因为最上面那个标签是 560 不是 580）
- **脚注（本季实际印出的）**：
  ```
  Note: Spread over the reference rate on new direct lending originations by borrower EBITDA cohort, comparing year-end 2024, year-end 2025 and May 2026, with single-B syndicated loans as the public-market comparator. Spreads widened most in the upper middle market (+23bp year-to-date for the $100m+ cohort) in sympathy with the public loan selloff, while sub-$50m cohorts were little changed. May 2026 values are as printed in the source; the two year-end series are read from the source chart. Sources: KBRA, PitchBook | LCD, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 11 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 12 · Financial covenants across vintages and segments (% of deals)

- **slug**：`prc_covenants_by_vintage`（稳定标识，编号会变、slug 不变）
- **位置**：`4.2`，版式 `pairL`（并排左）
- **形状**：`groups_stacked`　**出图函数**：`groups_stacked()` in `build_s2.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  groups_stacked('prc_covenants_by_vintage', 'pair', 2.9)
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Deal Activity | Looser Covenant and Higher PIKs for Upper Middle-Market Cohorts」 / 「Financial Covenants Across Vintages and Segments」 / 「32–47%」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Deal Activity | Looser Covenant and Higher PIKs for Upper Middle-Market Cohorts"，左图 "Financial Covenants Across Vintages and Segments"（1 or more financial covenants vs Cov-lite，三个规模段 × 2021–2024 四个年份，共 12 根柱子）。
  - 原图无柱值标注，用像素测量：因为每根柱子都是 100% 堆叠，蓝色段占整根柱子的比例可以直接量，不需要先标定 y 轴。
  - 锚点校验两处，都对上了 —— ① 上中端 2024 年份 cov-lite 量得 63%，slide 正文明标 63%；② 上中端 2021–2023 量得 47/37/32%，slide 正文明标区间 "32–47%"，量出来的最小最大值正好是这两个端点。
  - 数值取整（原图刻度 20% 一格，S&P 披露到整数百分点）。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 锚点校验两处，都对上了 —— ① 上中端 2024 年份 cov-lite 量得 63%，slide 正文明标 63%
  - ② 上中端 2021–2023 量得 47/37/32%，slide 正文明标区间 "32–47%"，量出来的最小最大值正好是这两个端点
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`2024`　｜　该口径源上限：`2024`
  - 本季文件夹里同主题最新：`2Q26`（**口径不同**）—— q2-2026-us-private-credit-and-middle-market-quarterly-wrap.xlsx，sheet "19 Direct Lending Covenants" / "20 Covenant Changes"
  - 为什么不能用它续：那两张是问卷（受访者比例），本图是 S&P 按 vintage 统计的契约结构表 —— 口径不同，不能接。本图卡在 2024 vintage 是因为 S&P 那张表 2025 vintage 样本不足。
  - 下季去哪儿看源末期：Market/2Q26 S&P Direct Lending.pdf，"Financial covenants across vintages and segments" 表的最后一个 vintage 列。⚠ 这张按 vintage 分组不是按时间轴，源表本季只到 2024 vintage（2025 vintage 的契约样本还不够）—— 下季看那张表有没有多出 2025 列
- **脚注（本季实际印出的）**：
  ```
  Note: Share of direct lending deals with at least one maintenance financial covenant versus cov-lite, by origination vintage and market segment. Lower-middle-market deals retained a financial covenant in every vintage, while 63% of 2024-vintage upper-middle-market deals were cov-lite versus 32–47% for the 2021–2023 vintages. Values read from the chart; the 63% and the 32–47% range are stated in the source. Source: S&P Global Ratings via Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 12 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 13 · % of deals with PIK toggle across vintages

- **slug**：`prc_pik_toggle_share`（稳定标识，编号会变、slug 不变）
- **位置**：`4.2`，版式 `pairR`（并排右）
- **形状**：`groups_bars`　**出图函数**：`groups_bars()` in `build_s2.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  groups_bars('prc_pik_toggle_share', 'pair', 2.9)
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Deal Activity | Looser Covenant and Higher PIKs for Upper Middle-Market Cohorts」 / 「% of Deals with PIK Toggle across Vintages」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Deal Activity | Looser Covenant and Higher PIKs for Upper Middle-Market Cohorts"，右图 "% of Deals with PIK Toggle across Vintages"（三个规模段各一组，组内按 2021/2022/2023/2024 四个年份排列，图例色序 深蓝/金/深绿/亮蓝）。
  - 原图无柱值标注，用像素测量：以两个明标值做标定 —— 核心中端 2024 = 22%、上中端 2024 = 41%，分别得 13.773 和 13.805 px/%，两者一致度 99.77%，取均值 K = 13.789 px/%。
  - 量柱子时要求像素紧贴基线（y=1129 上下 6px 内），把图例色块排除在外。
  - 量得柱高 68px→4.93%、150px→10.88%、303px→21.97%、566px→41.05%，四个都落在整数百分点 ±0.15pp 内，故取整为 5 / 11 / 22 / 41。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 原图无柱值标注，用像素测量：以两个明标值做标定 —— 核心中端 2024 = 22%、上中端 2024 = 41%，分别得 13.773 和 13.805 px/%，两者一致度 99.77%，取均值 K = 13.789 px/%
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`2024`　｜　该口径源上限：`2024`
  - ⚠ 缺 `folder_freshest` —— `pc_period_check.py` 会判不通过
  - 下季去哪儿看源末期：同一份 deck 的 "PIK toggle option by vintage" 表，最后一个 vintage 列
- **_gap_note**：原图这两格是空的。空柱有两种可能：真的是 0，或者 S&P 样本不足没披露。原图和 slide 正文都没说明，所以按「未披露」处理，画图时留空，正文不许把它当 0 来说「零 PIK」。
- **脚注（本季实际印出的）**：
  ```
  Note: Share of direct lending deals originated with a PIK toggle, by vintage and segment. 41% of 2024-vintage upper-middle-market deals carried a PIK feature versus 22% in the core middle market, while PIK toggles remain uncommon in the lower middle market across all vintages. The source chart shows no bar for the 2021 core-middle-market and 2022 upper-middle-market vintages; these are shown as not reported rather than as zero. The 22% and 41% figures are stated in the source; the remaining bars are read from the chart. Source: S&P Global Ratings via Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 13 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 14 · S&P Credit-estimate default rates vs US spec-grade (TTM, %)

- **slug**：`cf_sp_default_vs_specgrade`（稳定标识，编号会变、slug 不变）
- **位置**：`5.1`，版式 `pairL`（并排左）
- **形状**：`series_lines`　**出图函数**：`long_lines()` in `build_s3.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  long_lines('cf_sp_default_vs_specgrade', 'pair', 2.9, 'TTM default rate (%)',
  dy=[9, -13, -13], tick_every=18, fmt='{:.2f}')
  ```
- **数据源**：
  - `2026Q3/Market/2Q26 S&P Direct Lending.pdf`
  - 定位：「Defaults | Selective Defaults Continue To Trend Down For Credit-Estimated Companies」 / 「Private Credit And Middle-Market CLO Quarterly – Q2 2026」 / 「。数据基准：slide 脚注 」
- **取数与构成**（本季实际做法，下季照做）：
  - 2Q26 S&P Direct Lending.pdf（S&P Global Ratings, "Private Credit And Middle-Market CLO Quarterly – Q2 2026"），slide 标题 "Defaults | Selective Defaults Continue To Trend Down For Credit-Estimated Companies"，图题 "Credit estimate default rates versus S&P Global Ratings U.S. speculative-grade corporate default rate (July 2017-March 2026)"。
  - 数据基准：slide 脚注 "Data as of first-quarter 2026"。
  - 原图无点值标注，按颜色扫列做像素还原：y 轴用 0% 和 8% 两条网格线标定（y=1078 / y=479，74.875 px 每 1%），x 轴 105 个月按 Jul 2017–Mar 2026 均分。
  - 两条 credit estimate 线同为青色、只靠虚实区分，所以每列取最上面一段作 including、最下面一段作 excluding。
  - 锚点校验：Mar 2026 including 量得 4.40%，报告正文明标 4.37%（差 0.03pp）；Dec 2025 including 量得 4.93%，正文明标 4.95%（差 0.02pp）。
  - 常识校验：美国投机级 TTM 违约率峰值量得 6.66%（2020 年末），与公开披露的约 6.6% 一致。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 锚点校验：Mar 2026 including 量得 4.40%，报告正文明标 4.37%（差 0.03pp）
  - Dec 2025 including 量得 4.93%，正文明标 4.95%（差 0.02pp）
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`Mar 2026`　｜　该口径源上限：`Mar 2026`
  - 本季文件夹里同主题最新：`Mar 2026`（同口径）—— 2Q26 S&P Direct Lending.pdf（本季最新的 S&P deck，TTM 图本身到 Mar 2026）
  - 下季去哪儿看源末期：Market/2Q26 S&P Direct Lending.pdf 的 TTM 违约率图横轴末月
- **脚注（本季实际印出的）**：
  ```
  Note: Trailing-12-month default rates. The credit-estimate series covers obligors with S&P Global Ratings credit estimates, shown including and excluding selective defaults, against the US speculative-grade corporate default rate. Monthly, July 2017 to March 2026. The credit-estimate default rate including selective defaults stood at 4.37% at end-1Q26 versus 4.95% at end-2025. Values other than the two cited figures are read from the chart. Source: S&P Global Ratings.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 14 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 15 · S&P T12M default rate: direct lending 4.4% vs BSL 3.3%

- **slug**：`cf_sp_dl_vs_bsl_default`（稳定标识，编号会变、slug 不变）
- **位置**：`5.1`，版式 `pairR`（并排右）
- **形状**：`series_lines`　**出图函数**：`qlines()` in `build_s7.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  qlines('cf_sp_dl_vs_bsl_default', 'pair', 2.9, 'T12M default rate (%)', every=24,
  fmt='{:.1f}%', dys=[9, -12], styles=('-', '-')
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Defaults | We Expect 8% Default Rate in Private Credit as AI-Disruption Unfolds」 / 「T12M Default Rate (%)」 / 「Defaults based on S&P moderated to 4.4% in March 2026」 / 「28」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Defaults | We Expect 8% Default Rate in Private Credit as AI-Disruption Unfolds"，右图 "T12M Default Rate (%)"（两条线：Direct Lending Defaults / BSL Defaults；纵轴 0–9；横轴 Mar-18 至 Mar-26 共 97 个月点，标签每 12 个月一个）。
  - 两个端点图上明标 4.4% / 3.3%，账本末点直接用明标值。
  - 中间点像素还原（扫描窗口限定 y∈[890,1180] —— 图例色块在 y=878–879，不排掉会把它和折线一起平均，在 2019 年初和 2023 年初各造出一段假的方波，第一次就是这么错的）：y 轴用 0 与 9 两个刻度标签的像素行标定（y=1173.5 / y=863.5，34.44px 每 1 个百分点）。
  - 锚点残差：末点量得 DL 4.36%（明标 4.4%，差 0.05pp）、BSL 3.30%（明标 3.3%，差 0.01pp）。
  - ⭐ 跨文档交叉校验：Ex 14 用的是 S&P 自己那份 deck 里的 credit-estimate 含 SD 违约率，Mar-2026 独立量得 4.40%；本图 Direct Lending 末点量得 4.36% —— 两张不同文档、不同版式的图，两次独立像素测量，差 0.04pp，互为印证。
  - （tracker 第 28 页正文也写 "Defaults based on S&P moderated to 4.4% in March 2026"，第三处一致。
  - ）
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 两个端点图上明标 4.4% / 3.3%，账本末点直接用明标值
  - 锚点残差：末点量得 DL 4.36%（明标 4.4%，差 0.05pp）、BSL 3.30%（明标 3.3%，差 0.01pp）
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`Mar 2026`　｜　该口径源上限：`Mar 2026`
  - 本季文件夹里同主题最新：`Mar 2026`（同口径）—— MS Private Credit 1Q26 tracker.pdf，"T12M Default Rate (%)" 图（月点到 Mar-26）
  - 下季去哪儿看源末期：同上
- **脚注（本季实际印出的）**：
  ```
  Note: Trailing-12-month issuer default rates for direct lending versus broadly syndicated loans, monthly. The direct lending rate stood at 4.4% in March 2026 against 3.3% for syndicated loans. Morgan Stanley expects direct lending defaults to reach 8%, similar to the COVID peak, concentrated in software and AI-adjacent sectors rather than broad-based as in 2020. Endpoints are as printed; intermediate points are read from the source chart. Sources: S&P Global Ratings, PitchBook | LCD, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 15 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 16 · Summary of private credit default measures (4Q25 vs 1Q26)

- **slug**：`cf_provider_compare_table`（稳定标识，编号会变、slug 不变）
- **位置**：`5.1`，版式 `table`（表格）
- **形状**：`rows_qoq`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Defaults | More Complicated Than You Think」 / 「Summary of private credit default measures」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Defaults | More Complicated Than You Think"，表 "Summary of private credit default measures" 全部明标值（含 4Q25 / 1Q26 两列、样本、定义、口径）。
  - 来源行照抄 slide 脚注：Fitch, S&P, KBRA DLD, Lincoln International VOG, Proskauer, Morgan Stanley Research
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Defaults | More Complicated Than You Think"，表 "Summary of private credit default measures" 全部明标值（含 4Q25 / 1Q26 两列、样本、定义、口径）
- **脚注（本季实际印出的）**：
  ```
  Note: Definitions and sample universes differ by provider, so levels are not comparable across rows — only the direction within each row is. Two providers reported lower defaults q/q, two higher, and one was broadly flat. Source: Fitch, S&P, KBRA DLD, Lincoln International VOG, Proskauer, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 16 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 17 · Fitch TTM private credit default rate: 6.0% at Apr 2026, up from 5.7% at end-1Q26

- **slug**：`cf_fitch_ttm_default`（稳定标识，编号会变、slug 不变）
- **位置**：`5.1`，版式 `pairL`（并排左）
- **形状**：`series_stacked`　**出图函数**：`bars_simple()` in `build_s4.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  bars_simple('cf_fitch_ttm_default', 'pair', 2.9, 'TTM default rate (%)',
  every=4, label_all=False)
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Defaults | Metrics by Rating Agencies」 / 「TTM Private Credit Default Rate (Fitch)」 / 「Fitch reported a TTM default rate of 6.0% as of Apr 2026」 / 「ticking up from end of 1Q26」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Defaults | Metrics by Rating Agencies"，左下图 "TTM Private Credit Default Rate (Fitch)"（月度柱，Dec-24 至 Apr-26 共 17 个月）。
  - 原图无柱值，量柱顶；y 轴用刻度标签像素行标定（原图纵轴从 3.0% 起，3.0% 在 y=1183，每 1.0% 占 112px）。
  - 锚点校验：Apr-26 量得 5.98%，正文明标 "Fitch reported a TTM default rate of 6.0% as of Apr 2026"；Mar-26（1Q26 末）量得 5.67%，正文说 4 月是"ticking up from end of 1Q26"，方向一致。
  - 另一重校验：17 个测量值全部落在 0.1pp 网格上，最大偏离 0.03pp —— 说明标定没有系统性偏移，故账本存 0.1pp 精度的取整值。
  - 注意：原图纵轴截断在 3.0%，本报告重画时的纵轴起点见 _source_axis_min 和作图约定。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 锚点校验：Apr-26 量得 5.98%，正文明标 "Fitch reported a TTM default rate of 6.0% as of Apr 2026"
  - 另一重校验：17 个测量值全部落在 0.1pp 网格上，最大偏离 0.03pp —— 说明标定没有系统性偏移，故账本存 0.1pp 精度的取整值
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`Apr-26`　｜　该口径源上限：`Apr-26`
  - 本季文件夹里同主题最新：`Apr-26`（同口径）—— MS Private Credit 1Q26 tracker.pdf，"TTM Private Credit Default Rate (Fitch)"（月柱到 Apr-26）
  - 下季去哪儿看源末期：tracker 的 Fitch TTM 违约率图横轴末月
- **脚注（本季实际印出的）**：
  ```
  Note: Trailing-12-month default rate for Fitch's private credit portfolio, which the agency tracks across roughly 1,200 issuers. Fitch reported 6.0% as of April 2026, up from 5.7% at end-1Q26. The 6.0% figure is as disclosed; the remaining months are read from the source chart. Source: Fitch Ratings, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 17 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 18 · KBRA DLD issuer TTM default rate: direct lending vs BSL

- **slug**：`cf_kbra_dld_default`（稳定标识，编号会变、slug 不变）
- **位置**：`5.1`，版式 `pairR`（并排右）
- **形状**：`bars_grouped_categorical`　**出图函数**：`grouped_cat()` in `build_s4.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  grouped_cat('cf_kbra_dld_default', 'pair', 2.9, 'Issuer TTM default rate (%)',
  wrap=lambda s: s.replace('Direct Lending ', 'DL\n')
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Defaults | Metrics by Rating Agencies」 / 「Issuer TTM Default Rate (%)」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf(⚠ 同一份 deck 在文件夹里出现两次:Market/MS Private Credit 1Q26 tracker.pdf 与 Broker/Private Credit Tracker 1Q26 – Softening Fundamentals.pdf,md5 相同 1b4730b8…,取数以 Market/ 那份为准),slide 标题 "Defaults | Metrics by Rating Agencies",右上图 "Issuer TTM Default Rate (%)"(分组柱,两个系列 Apr '26 / Dec '25,五个类别:Direct Lending All / Direct Lending Sponsored / Direct Lending Lower MM(Private Market)、Syndicated Loans / High Yield Bonds(Public Market)),页码辅助 p28。
  - 原图无柱值 —— 全部像素还原,标定与锚点见 _method / _anchors。
  - KBRA 的违约数据只从 2023 年起(slide 正文自己说的),所以这里给的是两个时点而不是时序。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 原图无柱值 —— 全部像素还原,标定与锚点见 _method / _anchors
- **脚注（本季实际印出的）**：
  ```
  Note: Issuer trailing-12-month default rates per KBRA DLD, comparing April 2026 with December 2025. The three private-market categories all declined over the period while high-yield bonds rose. KBRA default data begin in 2023. The chart carries no printed data labels, so all values here are read from it. The direct-lending-overall reading ties to the 2.2% and 1.6% printed for KBRA DLD in the provider summary table on the preceding slide of the same deck (shown in {{ex:cf_provider_compare_table}}), within the 0.1pp rounding of a digitised read and the one-month difference in as-of date; the sponsored and lower-middle-market breakdowns are printed nowhere in this quarter's sources and rest on the digitisation alone. Source: KBRA, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 18 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 19 · Fitch LTM default rate by sector (%)

- **slug**：`cf_fitch_default_by_sector`（稳定标识，编号会变、slug 不变）
- **位置**：`5.1`，版式 `solo`（满宽单图）
- **形状**：`bars_categorical`　**出图函数**：`hbars_hl()` in `build_s5.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  hbars_hl('cf_fitch_default_by_sector', 'solo', 4.4, 'LTM default rate (%)')
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「AI Risk | Benign Ratings Trend and Muted Defaults in Software So Far」 / 「LTM Default Rate by Sector」 / 「the overall default rate in direct lending (5.7%)」 / 「the trailing 12m default stood at 2.3% for software」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "AI Risk | Benign Ratings Trend and Muted Defaults in Software So Far"，右图 "LTM Default Rate by Sector"（Fitch，横条，21 个类别，含一行 Total）。
  - ⭐ 这张不需要像素测量 —— 每根条子的百分比都在 PDF 文字层里，逐个取的明值。
  - 锚点校验两处：Total 5.7%，与该 slide 正文 "the overall default rate in direct lending (5.7%)" 一致；Technology Software 2.3%，与正文 "the trailing 12m default stood at 2.3% for software" 一致。
  - 注意行业名在 PDF 文字层里被拆字（"Pharmaceuti cal s"、"Tec hnology Software"、"Aeros pace And Defence" 等），已按 Fitch 的标准写法还原；下季重跑要重新核一遍拼写。
  - 另：Broker 目录下的 "Private Credit Tracker 1Q26 – Softening Fundamentals.pdf" 与 Market 目录下的 "MS Private Credit 1Q26 tracker.pdf" 是同一份文件（md5 相同 1b4730b8…），别当成两个来源重复计。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 锚点校验两处：Total 5.7%，与该 slide 正文 "the overall default rate in direct lending (5.7%)" 一致
- **_highlight_note**：基线高亮的是 Technology Software，第一版我错高亮成了 Total。Total 那行仍在图上，只是不再着色。
- **脚注（本季实际印出的）**：
  ```
  Note: Fitch trailing-12-month default rate by sector across the middle-market names it tracks, as of 1Q26. The overall direct lending default rate was 5.7%; technology software, despite AI-disruption concerns, was among the lowest at 2.3%, while broadcasting and media was the highest at 22.2%. All values are as printed in the source. Source: Fitch Ratings, Morgan Stanley Research. Technology Software is highlighted because software is the stress theme running through this report.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 19 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 20 · Average implied recoveries (2025 defaults), unweighted

- **slug**：`cf_recovery_path`（稳定标识，编号会变、slug 不变）
- **位置**：`5.2`，版式 `pairL`（并排左）
- **形状**：`bars_grouped_categorical`　**出图函数**：`grouped_cat3()` in `build_s7.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  grouped_cat3('cf_recovery_path', 'pair', 3.0, 'Implied recovery (pt)', fmt='{:.1f}',
  wrap=lambda s: s.replace('Direct lending — ', 'DL\n')
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Recovery Rates | Recovery Rates Screened Lower in Direct Lending」 / 「Average Implied Recoveries (2025), Unweighted」 / 「非 PIK 比 PIK 高 11pt」 / 「2025 (full year)」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Recovery Rates | Recovery Rates Screened Lower in Direct Lending"，左图 "Average Implied Recoveries (2025), Unweighted"（分组柱：四个类别 × 四个时点）。
  - ⭐ 这张不需要像素测量 —— 16 根柱子的数值图上全部标了，逐个抄的明值。
  - 锚点校验两处，都对上：① 违约当日 直贷 45pt vs 银团 53pt，差 8pt，与 slide 正文明标一致；② 非 PIK 52.6pt 减 PIK 41.6pt = 11.0pt，与正文 "非 PIK 比 PIK 高 11pt" 一致。
  - ⚠ 口径：2025 全年、未加权平均，不是 1Q26 的数 —— 与本节其他 exhibit 的基准日不同，as_of 记的是 "2025 (full year)"，正文不许说成「本季」。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 锚点校验两处，都对上：① 违约当日 直贷 45pt vs 银团 53pt，差 8pt，与 slide 正文明标一致
- **脚注（本季实际印出的）**：
  ```
  Note: Average implied recovery rates on 2025 defaults, unweighted, measured at four points ahead of default. Direct lending recovered 45 points at the default date versus 53 for syndicated loans, and non-PIK direct lending loans recovered 11 points more than PIK loans. Figures cover full-year 2025, not the current quarter. All values are as printed in the source. Sources: KBRA, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 20 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 21 · Implied recovery average across sectors (2023–2026)

- **slug**：`cf_recovery_by_sector`（稳定标识，编号会变、slug 不变）
- **位置**：`5.2`，版式 `pairR`（并排右）
- **形状**：`bars_categorical`　**出图函数**：`hbars()` in `build_s2.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  hbars('cf_recovery_by_sector', 'pair', 3.0, 'Implied recovery (pt)', fmt='{:.1f}')
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Recovery Rates | Recovery Rates Screened Lower in Direct Lending」 / 「Implied Recovery Average Across Sectors (2023-2026)」 / 「Sector 3/4/6/7/8」 / 「averaged at ~48pt for software loans」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Recovery Rates | Recovery Rates Screened Lower in Direct Lending"，右图 "Implied Recovery Average Across Sectors (2023-2026)"。
  - 八根柱子的值图上都标了（66.8 / 61.3 / 50.7 / 49.1 / 47.8 / 46.3 / 45.7 / 44.7），明值直抄。
  - ⚠ 行业名此前误留了 "Sector 3/4/6/7/8" 五个占位符（PDF 文字层里斜排的类别名抽不全），已渲染该页读图补齐：Industrial & Manufacturing / Com & Pro Svcs / Healthcare / Consumer / Food & Bev。
  - 锚点校验：Software 量到 47.8pt，slide 标题写 "averaged at ~48pt for software loans"，一致。
  - ⚠ 基准与口径：slide 脚注写 "Sample is First Lien Loans only, Data as of Apr 26" —— 所以 as_of 是 Apr 2026 而不是 1Q26，且只含一顺位贷款；柱值本身是 2023–2026 的三年均值，不是单季数。
  - 三点都要在正文里说明。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 锚点校验：Software 量到 47.8pt，slide 标题写 "averaged at ~48pt for software loans"，一致
- **脚注（本季实际印出的）**：
  ```
  Note: Average implied recovery by sector, 2023–2026 average, first-lien loans only, data as at April 2026. Software sits mid-table at 47.8 points, against 66.8 for building/construction/engineering at the top and 44.7 for food and beverage at the bottom. All values are as printed in the source. Sources: KBRA, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 21 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 22 · Gross leverage in US leveraged credit

- **slug**：`cf_leverage_band`（稳定标识，编号会变、slug 不变）
- **位置**：`5.3`，版式 `pairL`（并排左）
- **形状**：`band_positioning`　**出图函数**：`band_chart()` in `build_s2.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  band_chart('cf_leverage_band')
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Gross Leverage in US Leveraged Credit」 / 「高度=倍数」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Credit Fundamentals | Private Credit Borrowers Comparable to Low Single B/CCC Profiles in Public Market"，图 "Gross Leverage in US Leveraged Credit" 的明标定位（HY 3.6x / Syndicated Loans 4.0x / Direct Lending 5.7x），评级带 AAA-BBB / BB1-BB3 / B1-B3 / CCC 照图。
  - ⚠ 2026-08-24 复核发现并已改：源图的纵向是**连续的杠杆刻度**（菱形高度 ∝ 数值，HY 3.6x 在 BB 带底部、不与另外两个同高），第一版把三个菱形都画在 B1-B3 带中线上，丢了「高度=倍数」这层信息。
  - 现按像素标定的连续刻度重画（见 scale._src）。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Credit Fundamentals | Private Credit Borrowers Comparable to Low Single B/CCC Profiles in Public Market"，图 "Gross Leverage in US Leveraged Credit" 的明标定位（HY 3.6x / Syndicated Loans 4.0x / Direct Lending 5.7x），评级带 AAA-BBB / BB1-BB3 / B1-B3 / CCC 照图
- **脚注（本季实际印出的）**：
  ```
  Note: Positioning of each market against public-market rating bands. Private credit borrowers are typically 5–7x levered with 1–2x EBITDA coverage, broadly a single-B to CCC profile. Marker values are as labelled in the source; vertical positions follow the source’s continuous scale, and the rating-band boundaries are digitised from the chart. Source: Fitch, S&P, KBRA, Lincoln International VOG, Bloomberg, FactSet, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 22 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 23 · Total leverage (x): Fitch private MM vs Lincoln vs public single B

- **slug**：`cf_leverage_timeseries`（稳定标识，编号会变、slug 不变）
- **位置**：`5.3`，版式 `pairR`（并排右）
- **形状**：`series_lines`　**出图函数**：`qlines()` in `build_s5.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  qlines('cf_leverage_timeseries', 'pair', 2.9, 'Total leverage (x)', every=4,
  fmt='{:.1f}x', dys=[9, -12, 7])
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Credit Fundamentals | Direct Lending Fundamentals Broadly Stable」 / 「Total Leverage (x)」 / 「fell to 5.9x from 6.0x per Fitch's monitored portfolio」 / 「median gross leverage flatlined at 5.2x based on Lincoln International」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Credit Fundamentals | Direct Lending Fundamentals Broadly Stable"，左下图 "Total Leverage (x)"。
  - 三条线：Fitch – Private MM Portfolio（蓝、菱形点）、Lincoln（金、方点）、Public Loan Borrowers (Single B)（深绿点线）。
  - 横轴 4Q20–1Q26 共 22 个季度，标签每两季一个。
  - 原图无点值，按颜色扫列像素还原，y 轴用刻度标签的像素行标定。
  - 深绿那条是点线（虚线），采样时会落进断口，所以它的不确定度按 ±0.1 记，比另两条大；而且它在 1Q26 没有点（原图就到 4Q25 为止），账本留 None，不许拿 4Q25 的值顶上。
  - （4.0x 在 y=1182、7.5x 在 y=840.5，97.57px 每 1.0x）。
  - 锚点校验两处，都对上了：1Q26 Fitch 量得 5.89x，slide 正文明标 "fell to 5.9x from 6.0x per Fitch's monitored portfolio"，而 4Q25 量得 5.97x ≈ 6.0x；Lincoln 1Q26 与 4Q25 量得同为 5.19x，正文说 "median gross leverage flatlined at 5.2x based on Lincoln International" —— 走平且四舍五入到 5.2x，完全一致。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 锚点校验两处，都对上了：1Q26 Fitch 量得 5.89x，slide 正文明标 "fell to 5.9x from 6.0x per Fitch's monitored portfolio"，而 4Q25 量得 5.97x ≈ 6.0x
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`1Q26`　｜　该口径源上限：`1Q26`
  - 本季文件夹里同主题最新：`1Q26`（同口径）—— MS Private Credit 1Q26 tracker.pdf，slide "Direct Lending Fundamentals Broadly Stable"
  - 下季去哪儿看源末期：tracker 的杠杆时序图横轴末季
- **脚注（本季实际印出的）**：
  ```
  Note: Median total leverage (debt/EBITDA). Fitch's monitored private middle-market portfolio fell to 5.9x in 1Q26 from 6.0x, while Lincoln International's median was flat at 5.2x. The public single-B comparator is shown to 4Q25, the last quarter plotted in the source. Endpoint figures are as disclosed; intermediate points are read from the source chart. Fitch’s series is observed annually from 2020 through 2024 and quarterly from 1Q25; the straight segments between year-end observations follow the source chart’s own interpolation and are not additional data points. Sources: Fitch Ratings, Bloomberg, FactSet, Lincoln International VOG, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 23 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 24 · Interest coverage in US leveraged credit

- **slug**：`cf_icr_band`（稳定标识，编号会变、slug 不变）
- **位置**：`5.4`，版式 `pairL`（并排左）
- **形状**：`band_positioning`　**出图函数**：`band_chart()` in `build_s2.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  band_chart('cf_icr_band')
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Interest Coverage in US Leveraged Credit」 / 「22」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Credit Fundamentals | Private Credit Borrowers Comparable to Low Single B/CCC Profiles in Public Market"，图 "Interest Coverage in US Leveraged Credit" 的明标定位（HY 4.7x / Syndicated Loans 4.0x / Direct Lending 2.0x）。
  - ⚠ 方向与落带逐点核过源图（tracker 第 22 页右图，400dpi 渲染后看图）：这张图的箭头是 High 在上、Low 在下（与左边的杠杆图相反）；HY 4.7x 的菱形压在 BB3/B1 交界，Syndicated 4.0x 在 B1 带内，Direct Lending 2.0x 压在 B3/CCC 交界（不是整格落在 CCC 里）。
  - 我第一版把箭头画反了、且把 DL 整格放进了 CCC，已改。
  - 。
  - ⚠ 2026-08-24 复核同左图：纵向是连续的覆盖倍数刻度，改为按数值定位（见 scale._src）——DL 2.0x 自然落在 B/CCC 界上方一点，与源图一致，不再需要 band_edge 硬编码。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Credit Fundamentals | Private Credit Borrowers Comparable to Low Single B/CCC Profiles in Public Market"，图 "Interest Coverage in US Leveraged Credit" 的明标定位（HY 4.7x / Syndicated Loans 4.0x / Direct Lending 2.0x）
- **脚注（本季实际印出的）**：
  ```
  Note: Mirror image of the leverage positioning — on interest coverage the scale runs the other way, and direct lending sits at the bottom of the single-B band, on the B3/CCC boundary. Marker values are as labelled in the source; vertical positions follow the source’s continuous scale, and the rating-band boundaries are digitised from the chart. Source: Fitch, S&P, KBRA, Lincoln International VOG, Bloomberg, FactSet, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 24 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 25 · EBITDA coverage (x): Fitch and Lincoln both around 2.0x in 1Q26, up from 2023 troughs near 1.4x

- **slug**：`cf_ebitda_coverage_ts`（稳定标识，编号会变、slug 不变）
- **位置**：`5.4`，版式 `pairR`（并排右）
- **形状**：`series_lines`　**出图函数**：`qlines()` in `build_s5.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  qlines('cf_ebitda_coverage_ts', 'pair', 2.9, 'EBITDA coverage (x)', every=4,
  fmt='{:.1f}x', dys=[9, -12, 7])
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Credit Fundamentals | Direct Lending Fundamentals Broadly Stable」 / 「EBITDA Coverage(x)」 / 「At Lincoln International and Fitch, coverage is now hovering around 2.0x」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "Credit Fundamentals | Direct Lending Fundamentals Broadly Stable"，右下图 "EBITDA Coverage(x)"。
  - 三条线：Fitch – Private MM Portfolio（蓝、菱形点）、Lincoln（金、方点）、Public Loan Borrowers (Single B)（深绿点线）。
  - 横轴 4Q20–1Q26 共 22 个季度，标签每两季一个。
  - 原图无点值，按颜色扫列像素还原，y 轴用刻度标签的像素行标定。
  - 深绿那条是点线（虚线），采样时会落进断口，所以它的不确定度按 ±0.1 记，比另两条大；而且它在 1Q26 没有点（原图就到 4Q25 为止），账本留 None，不许拿 4Q25 的值顶上。
  - （1.0x 在 y=1163.5、4.0x 在 y=847，105.5px 每 1.0x）。
  - 锚点校验：1Q26 Fitch 量得 1.98x、Lincoln 量得 1.90x，slide 正文说 "At Lincoln International and Fitch, coverage is now hovering around 2.0x"，两边都落在 2.0x 附近，一致。
  - 注意 Lincoln 这条从 1Q22 才开始（原图如此），前 5 个季度留 None。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 锚点校验：1Q26 Fitch 量得 1.98x、Lincoln 量得 1.90x，slide 正文说 "At Lincoln International and Fitch, coverage is now hovering around 2.0x"，两边都落在 2.0x 附近，一致
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`1Q26`　｜　该口径源上限：`1Q26`
  - 本季文件夹里同主题最新：`1Q26`（同口径）—— MS Private Credit 1Q26 tracker.pdf，同上 slide
  - 下季去哪儿看源末期：tracker 的覆盖率时序图横轴末季
- **脚注（本季实际印出的）**：
  ```
  Note: Median EBITDA-to-cash-interest coverage. Coverage improved again in 1Q26, with both Fitch's monitored private middle-market portfolio and Lincoln International hovering around 2.0x, up from troughs near 1.4x–1.6x in 2023. Lincoln's series begins in 1Q22 and the public single-B comparator is shown to 4Q25, matching the source. Values are read from the source chart. Sources: Fitch Ratings, Bloomberg, FactSet, Lincoln International VOG, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 25 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 26 · Nonaccruals across BDCs: average at cost up to 2.8%, a five-year high

- **slug**：`cf_bdc_nonaccrual_avg`（稳定标识，编号会变、slug 不变）
- **位置**：`5.5`，版式 `pairL`（并排左）
- **形状**：`series_lines`　**出图函数**：`lines_rhs()` in `build_s4.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  lines_rhs('cf_bdc_nonaccrual_avg', 'pair', 2.9, 'Avg nonaccrual at cost (%)', every=8,
  dy=-11, rdy=8)
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「BDCs | Nonaccruals and PIKs Trending Worse」 / 「Nonaccruals Across BDCs」 / 「五年最高」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "BDCs | Nonaccruals and PIKs Trending Worse"，右上图 "Nonaccruals Across BDCs"（左轴 Avg (at Cost) 0–5%，右轴 % BDCs with 8%+ Nonaccruals 0–15%，横轴 1Q17–1Q26 共 37 个季度，标签每 4 季一个）。
  - 原图无点值，按颜色扫列做像素还原。
  - y 轴标定用坐标轴刻度标签的像素行位置（不是估的）：左轴 0.0% 在 y=567、每 1.0% 占 55px；右轴 0% 同在 y=567、每 3% 占 55px。
  - 锚点校验：1Q26 平均非应计量得 2.75%，slide 正文明标 2.8%（四舍五入吻合）—— 账本里末点直接用明标的 2.8。
  - 正文的「五年最高」也对得上：2Q21–1Q26 这个窗口里此前最高是 3Q25 的 2.58%。
  - 峰值量得 2Q20 = 4.45%，与新冠期间的已知高点量级一致。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 锚点校验：1Q26 平均非应计量得 2.75%，slide 正文明标 2.8%（四舍五入吻合）—— 账本里末点直接用明标的 2.8
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`1Q26`　｜　该口径源上限：`1Q26`
  - 本季文件夹里同主题最新：`2Q26`（**口径不同**）—— Barclays_US_HG_Research_Business_Development_Companies_Early_Themes_and_Trends_from_2Q_Reporting.pdf，FIGURE 4 与 p8
  - 为什么不能用它续：那份 broker 报告只有七家 IG BDC 的 2Q26 单家读数（APODS/ARCC/BCRED/HTGC/GBDC/GCRED/NMFC），本图画的是 tracker 的全体 BDC 加权平均时序 —— 七家拼不出全体口径。2Q26 的方向已写进正文与 sentiment 表。
  - 下季去哪儿看源末期：tracker slide "BDCs | …" 的非应计图横轴末季
- **脚注（本季实际印出的）**：
  ```
  Note: Average nonaccrual rate at cost across BDCs with total assets above $50m, quarterly. The average rose to 2.8% in 1Q26, the highest in five years, and the share of BDCs reporting nonaccruals above 8% rose to about 11%. The 2.8% endpoint is as disclosed; the remaining points are read from the source chart. The right-hand scale is drawn to 20% so that the series clears the frame; in 2Q20 and 3Q20 that series rose above the 15% maximum of the source chart's own axis and was cut off there, so no value can be read for those two quarters — the break is shown as a dashed bracket rather than interpolated. Source: BDC Collateral, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 26 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 27 · Average nonaccruals at cost: public vs private BDCs

- **slug**：`cf_bdc_nonaccrual_pubpriv`（稳定标识，编号会变、slug 不变）
- **位置**：`5.5`，版式 `pairR`（并排右）
- **形状**：`series_lines`　**出图函数**：`lines_rhs()` in `build_s4.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  lines_rhs('cf_bdc_nonaccrual_pubpriv', 'pair', 2.9, 'Nonaccruals at cost (%)', every=6)
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「BDCs | Divergence Between Public and Private BDCs」 / 「Average Nonaccruals at Cost」 / 「public BDC nonaccruals reaching new post-COVID highs」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "BDCs | Divergence Between Public and Private BDCs"，左下图 "Average Nonaccruals at Cost"（两条线：Public BDCs / Private BDCs，左轴 0–6%，横轴 1Q19–1Q26 共 29 个季度，标签每 4 季一个）。
  - 原图无点值，按颜色扫列像素还原；y 轴用刻度标签像素行标定（0% 在 y=1140，每 1% 占 50.92px）。
  - 扫的时候把 y=851–854 的图例色块排除掉了 —— 不排除会把图例行和折线行平均，私募那条会凭空多出三个 3.3–3.5% 的假尖峰。
  - 交叉校验（关键）：把 public / private 两条与 Ex 26 / Ex 28 的全样本均值逐季比对，1Q23–1Q26 共 13 个季度，每一季全样本值都落在 public 与 private 之间，26 次夹逼检验全部通过。
  - 另外与正文说法对得上：公募 1Q26 量得 4.52%，是 2020 年新冠峰值（量得 4.76%）之后的最高点，正文说 "public BDC nonaccruals reaching new post-COVID highs"。
  - ⭐ 替代锚点：源图没有任何印出来的点值，没有锚点可用。
  - 改用与 cf_bdc_nonaccrual_avg 的结构一致性做校验 —— 全体均值必须落在公募与私募两条之间（±0.3pp 容差），本季 29/29 期通过。
  - 下季必须重跑这条；不通过说明两张图里至少一张测错了。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - ⭐ 替代锚点：源图没有任何印出来的点值，没有锚点可用
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`1Q26`　｜　该口径源上限：`1Q26`
  - 本季文件夹里同主题最新：`2Q26`（**口径不同**）—— Barclays_US_HG_Research_Business_Development_Companies_Early_Themes_and_Trends_from_2Q_Reporting.pdf，FIGURE 4 与 p8
  - 为什么不能用它续：同上：七家单家 2Q26 读数，不是本图的「公众 BDC vs 私募 BDC」两条聚合线。
  - 下季去哪儿看源末期：同上
- **脚注（本季实际印出的）**：
  ```
  Note: Average nonaccrual rate at cost, public versus private BDCs, for BDCs with total assets above $50m. Public BDCs reached 4.5% in 1Q26, a post-COVID high, while private vehicles remained near 2.0%. Values are read from the source chart. Source: BDC Collateral, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 27 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 28 · % PIK income over total investment income: average up to 6.4%

- **slug**：`cf_bdc_pik_avg`（稳定标识，编号会变、slug 不变）
- **位置**：`5.6`，版式 `pairL`（并排左）
- **形状**：`series_stacked`　**出图函数**：`bars_rhs()` in `build_s4.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  bars_rhs('cf_bdc_pik_avg', 'pair', 2.9, 'PIK / total inv. income (%)', every=3)
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「BDCs | Nonaccruals and PIKs Trending Worse」 / 「%PIK Income over Total Investment Income」 / 「close to 8%」 / 「vs 7% in the previous quarter」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "BDCs | Nonaccruals and PIKs Trending Worse"，左下图 "%PIK Income over Total Investment Income"（柱=Avg，左轴 0–10%；线=% BDCs with 12%+ PIK，右轴 0–12%；横轴 1Q23–1Q26 共 13 个季度）。
  - 原图无点值，按颜色扫列做像素还原。
  - y 轴标定用坐标轴刻度标签的像素行位置（不是估的）：左轴 0.0% 在 y=1168、每 1.0% 占 32px；右轴 0.0% 同在 y=1168、每 4% 占 107px。
  - 锚点校验三处：① 1Q26 平均 PIK 量得 6.41%，正文明标 6.4%（差 0.01pp）；② 1Q26 有 12%+ PIK 的 BDC 占比量得 7.6%，正文说 "close to 8%"；③ 上一季（4Q25）量得 6.5%，正文说 "vs 7% in the previous quarter"（四舍五入吻合）。
  - 账本里柱的末点用明标的 6.4。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - 锚点校验三处：① 1Q26 平均 PIK 量得 6.41%，正文明标 6.4%（差 0.01pp）
  - 账本里柱的末点用明标的 6.4
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`1Q26`　｜　该口径源上限：`1Q26`
  - 本季文件夹里同主题最新：`2Q26`（**口径不同**）—— Barclays_US_HG_Research_Business_Development_Companies_Early_Themes_and_Trends_from_2Q_Reporting.pdf，p7（某家 2Q26 PIK 投资收入 5.6%，上季 7%）
  - 为什么不能用它续：那是单家 PIK 投资收入占比，本图是 tracker 的全体 BDC PIK 收入占比时序 —— 口径不同。
  - 下季去哪儿看源末期：tracker 的 PIK 图横轴末季
- **脚注（本季实际印出的）**：
  ```
  Note: PIK income as a share of total investment income across BDCs with total assets above $50m, quarterly. The average ticked up to 6.4% in 1Q26 and close to 8% of BDCs reported PIK above 12% of investment income, versus 7% in the prior quarter. The 6.4% endpoint is as disclosed; the remaining points are read from the source chart. Source: BDC Collateral, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 28 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 29 · Average PIK rate: public BDCs up to 7.9% while private stayed range-bound near 5.6%

- **slug**：`cf_bdc_pik_pubpriv`（稳定标识，编号会变、slug 不变）
- **位置**：`5.6`，版式 `pairR`（并排右）
- **形状**：`series_grouped`　**出图函数**：`grouped_ts()` in `build_s4.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  grouped_ts('cf_bdc_pik_pubpriv', 'pair', 2.9, 'PIK / total inv. income (%)', every=3)
  ```
- **数据源**：
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「BDCs | Divergence Between Public and Private BDCs」 / 「%PIK Income over Total Investment Income」 / 「risen … while stayed range bound within private ones」
- **取数与构成**（本季实际做法，下季照做）：
  - MS Private Credit 1Q26 tracker.pdf，slide 标题 "BDCs | Divergence Between Public and Private BDCs"，右上图 "%PIK Income over Total Investment Income"（分组柱：Public BDCs Avg PIK / Private BDCs Avg PIK，左轴 0–10%，横轴 1Q23–1Q26 共 13 个季度）。
  - 原图无柱值，量柱顶；y 轴用刻度标签像素行标定（0% 在 y=605，每 1% 占 30.2px）。
  - 扫的时候把 y<352 排掉以避开图例色块 —— 不排掉会让私募的 4Q23/3Q24/4Q24 三根柱读成 10.2/10.2/9.2%（那是图例，不是柱）。
  - 交叉校验（关键）：把 public / private 两条与 Ex 26 / Ex 28 的全样本均值逐季比对，1Q23–1Q26 共 13 个季度，每一季全样本值都落在 public 与 private 之间，26 次夹逼检验全部通过。
  - 与 slide 标题也对得上：公募从 5.70% 升到 7.88%（+2.2pp），私募一直在 4.9–6.3% 区间里晃，正文说 "risen … while stayed range bound within private ones"。
  - ⭐ 替代锚点：源图没有任何印出来的点值，没有锚点可用。
  - 改用与 cf_bdc_pik_avg 的结构一致性做校验 —— 全体均值必须落在公募与私募两条之间（±0.3pp 容差），本季 13/13 期通过。
  - 下季必须重跑这条；不通过说明两张图里至少一张测错了。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - ⭐ 替代锚点：源图没有任何印出来的点值，没有锚点可用
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`1Q26`　｜　该口径源上限：`1Q26`
  - 本季文件夹里同主题最新：`2Q26`（**口径不同**）—— Barclays_US_HG_Research_Business_Development_Companies_Early_Themes_and_Trends_from_2Q_Reporting.pdf，p7
  - 为什么不能用它续：同上：单家读数，不是本图的公众/私募两条聚合线。
  - 下季去哪儿看源末期：同上
- **脚注（本季实际印出的）**：
  ```
  Note: PIK income as a share of total investment income, public versus private BDCs, for BDCs with total assets above $50m. The public-BDC average rose from 5.7% in 1Q23 to 7.9% in 1Q26, while the private average stayed within a 4.9%–6.3% range. Values are read from the source chart. Source: BDC Collateral, Morgan Stanley Research.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 29 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 30 · Broker summary — private credit views, key points and QoQ change

- **slug**：`sent_broker_summary`（稳定标识，编号会变、slug 不变）
- **位置**：`6.1`，版式 `table`（表格）
- **形状**：`rows_flat`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Broker/JPM_J_P__Morgan_Life_Ins_2026-06-26_5348342.pdf`
  - `2026Q3/Broker/Barclays_US_HG_Research_Business_Development_Companies_Early_Themes_and_Trends_from_2Q_Reporting.pdf`
  - `2026Q3/Broker/Private Credit Pressures Contained Not Resolved.pdf`
  - `2026Q3/Broker/ued42349.pdf`
  - `2026Q3/Broker/Connecting the Dots Around Private Credit.pdf`
  - `2026Q3/Broker/Private Credit Discussion.pdf`
  - `2026Q3/Broker/Macro Credit Views_ Dispersion, not disruption.pdf`
  - `2026Q3/Market/MS Private Credit 1Q26 tracker.pdf`
  - 定位：「Private Credit Tracker 1Q26 – Softening Fundamentals.pdf」 / 「MS Private Credit 1Q26 tracker.pdf」 / 「Downloaded by steven.xu@junsoncapital.com」 / 「For the exclusive use of XIYANG.ZHAO@JUNSONCAPITAL.COM」
- **取数与构成**（本季实际做法，下季照做）：
  - 2026Q3/Broker/ 目录下 8 份 PDF，逐份读首页/执行摘要后归纳。
  - 每行都锁死了机构 / 团队 / 报告名 / 发布日 / 作者 / 文件名 / 页数，可逐条回溯：Morgan Stanley《Connecting the Dots Around Private》2026-04-02（Connecting the Dots Around Private Credit.pdf）；Morgan Stanley《Private Credit: Pressures Containe》2026-07-12（Private Credit Pressures Contained Not Resolved.pdf）；Morgan Stanley《Private Credit Tracker 1Q26 – Soft》2026-06-23（Private Credit Tracker 1Q26 – Softening Fundamentals.pdf）；Morgan Stanley《Ares Management Corp: Private Cred》2026-04-02（Private Credit Discussion.pdf）；Barclays《Business Development Companies: Ea》2026-08-04（Barclays_US_HG_Research_Business_Development_Companies_Early_Themes_and_Trends_from_2Q_Reporting.pdf）；UBS《Public and Private Credit Outlook》2026-07-22（ued42349.pdf）；Goldman Sachs《Macro Credit Views: Dispersion, no》2026-06-29（Macro Credit Views_ Dispersion, not disruption.pdf）；J.P. Morgan《J.P. Morgan Life Insurance: Privat》2026-06-26（JPM_J_P__Morgan_Life_Ins_2026-06-26_5348342.pdf）。
  - ⚠ 目录里 8 份文件只对应 7 条独立观点 —— "Private Credit Tracker 1Q26 – Softening Fundamentals.pdf" 与 Market 目录下的 "MS Private Credit 1Q26 tracker.pdf" 是同一份（md5 都是 1b4730b8f1fc7cf1607f5dc73893f6e9），这里按一条计，别数成两家。
  - ⚠ 文件名不可靠：UBS 那份叫 ued42349.pdf、MS 的两份靠标题才分得清团队 —— 一律认内页标题与作者。
  - ⚠ 取阅记录：MS 的几份页脚写 "Downloaded by steven.xu@junsoncapital.com"，GS 那份写 "For the exclusive use of XIYANG.ZHAO@JUNSONCAPITAL.COM" —— 都是内部取阅，转发受限，正文引用只写机构与报告名，不要把这些字段贴进报告。
  - 本节是观点归纳，不含任何本报告自行计算的数字；表里出现的数字（如 UBS 的利差预测、Barclays 引用的 Cliffwater 年份数据）都是原报告的原话。
- **脚注（本季实际印出的）**：
  ```
  Note: Summary of sell-side views on private credit published between April and August 2026, as read from the reports in the quarter's broker folder. Each row records the publisher, report title, date and authors so the view can be traced back. Figures quoted are the publishers' own. Sources: Morgan Stanley, Barclays, UBS, Goldman Sachs and J.P. Morgan research, as listed.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 30 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 31 · BDC maturity wall (US$bn): Dec-25 vs Mar-26 snapshot, with vintage timing

- **slug**：`tws_extra_exhibit`（稳定标识，编号会变、slug 不变）
- **位置**：`7`，版式 `solo`（满宽单图）
- **形状**：`series_stacked`　**出图函数**：`grouped_bars()` in `build_s2.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  grouped_bars('tws_extra_exhibit', 'pair', 2.5, 'US$bn', label_all=False, label_last=True)
  ```
- **数据源**：
  - `2026Q3/Market/q2-2026-us-private-credit-and-middle-market-quarterly-wrap.xlsx`
  - `2026Q3/Market/q2-2026-us-private-credit-and-middle-market-quarterly-wrap.pdf`
  - 定位：「07 BDC Maturity Wall」
- **取数与构成**（本季实际做法，下季照做）：
  - q2-2026-us-private-credit-and-middle-market-quarterly-wrap.xlsx，sheet "07 BDC Maturity Wall"（PitchBook | LCD，US private credit & middle market quarterly wrap，2Q26），两列快照 As of Dec. 31, 2025 / As of March 31, 2026
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`Mar-26`　｜　该口径源上限：`Mar-26`
  - 本季文件夹里同主题最新：`Mar-26`（同口径）—— q2-2026-us-private-credit-and-middle-market-quarterly-wrap.xlsx，sheet "07 BDC Maturity Wall"（只有 Dec-25 / Mar-26 两列）
  - 下季去哪儿看源末期：Market/q2-2026-…-quarterly-wrap.xlsx，sheet "07 BDC Maturity Wall" 的最后一个到期桶
- **脚注（本季实际印出的）**：
  ```
  Note: BDC debt maturity profile, two snapshots three months apart; excludes equity and CLO holdings; data through 31 March 2026. The 2026 and 2027 buckets shrank while 2031–2033 grew from US$195bn to US$209bn, i.e. near-dated maturities were termed out rather than repaid. Bar values are exact as disclosed in the source workbook (sheet “07 BDC Maturity Wall”), not readings off a chart. The exhibit shows two dated snapshots rather than a time series, and that sheet carries only these two columns — 31 December 2025 and 31 March 2026 — so no later snapshot exists in this quarter’s folder. Source: PitchBook | LCD, 2Q26 US private credit & middle-market quarterly wrap workbook, sheet “07 BDC Maturity Wall”; side comments: S&P Global Ratings and Morgan Stanley Research, this quarter’s broker folder.
  ```
- **口径对账**（与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 31 并排比过，比了：分档、两个快照日、口径、数值）：
  - ✓ 一致：分档（2026…2031-2033）
  - ✓ 一致：两个快照日（Dec-25 / Mar-26）
  - ✓ 一致：口径
  - ✗ **有出入**：基线的 Note 写 "approximate readings from the source chart"，但六个值其实是 `07 BDC Maturity Wall` sheet 的精确值；基线正文的 194 / 207 也与 sheet 的 195.4 / 209.0 不符。
  - 结论：本季改为 as-disclosed，并把两个总数订正成 195 / 209。
  - 谁比的：Claude 2026-08-24，逐格核过该 sheet 的 I1:K7
  - 下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 32 · PAG BRS III — investment amount by portfolio type

- **slug**：`fund_pag_comp_type`（稳定标识，编号会变、slug 不变）
- **位置**：`8.1`，版式 `pairL`（并排左）
- **形状**：`shares`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2025 Q4 Quarterly Newsletter.pdf`
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf`
  - 定位：「Fund Overview」 / 「Investment Overview」 / 「Net MOIC」 / 「构成未变，因本季无新增投资」
- **取数与构成**（本季实际做法，下季照做）：
  - PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf，第 6 页 "Fund Overview"（本季与上季两列并排，直接抄明值，非计算、非测量）与第 8 页 "Investment Overview"（四个饼图的百分比都在 PDF 文字层里）。
  - 上上季（3Q25）的数取自 PAG BRS Fund III L.P. - 2025 Q4 Quarterly Newsletter.pdf 第 6 页的对照列。
  - ⚠ 术语对照：PAG 报表写 "Net MOIC"，本报告 §9 统一叫 TVPI，是同一个东西，别当两个指标。
  - 本图 = 按 portfolio type 的投资金额占比。
  - ⚠ 四个构成饼图在 2025Q4 与 2026Q1 完全相同（占比一个字都没变），原因是投资总额两季都是 USD1,258M、期间没有新增投资（投资笔数 20 笔未变，只是其中 1 笔从 current 转为 exited）。
  - 这不是抄错也不是没更新 —— 正文要写明「构成未变，因本季无新增投资」，不许含糊地说「构成基本稳定」。
  - 已逐页核对过 2025Q4 报告第 8 页。
- **脚注（本季实际印出的）**：
  ```
  Note: PAG BRS Fund III investment amount by portfolio type, as a share of the US$1,258m invested to date, as at 31 March 2026. Composition is unchanged from 4Q25 because no new investments were made during the quarter. Source: PAG BRS Fund III quarterly newsletter, Q1 2026.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 32 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 33 · PAG BRS III — investment amount by geography

- **slug**：`fund_pag_comp_geo`（稳定标识，编号会变、slug 不变）
- **位置**：`8.1`，版式 `pairR`（并排右）
- **形状**：`shares`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2025 Q4 Quarterly Newsletter.pdf`
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf`
  - 定位：「Fund Overview」 / 「Investment Overview」 / 「Net MOIC」 / 「构成未变，因本季无新增投资」
- **取数与构成**（本季实际做法，下季照做）：
  - PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf，第 6 页 "Fund Overview"（本季与上季两列并排，直接抄明值，非计算、非测量）与第 8 页 "Investment Overview"（四个饼图的百分比都在 PDF 文字层里）。
  - 上上季（3Q25）的数取自 PAG BRS Fund III L.P. - 2025 Q4 Quarterly Newsletter.pdf 第 6 页的对照列。
  - ⚠ 术语对照：PAG 报表写 "Net MOIC"，本报告 §9 统一叫 TVPI，是同一个东西，别当两个指标。
  - 本图 = 按 geography 的投资金额占比。
  - ⚠ 四个构成饼图在 2025Q4 与 2026Q1 完全相同（占比一个字都没变），原因是投资总额两季都是 USD1,258M、期间没有新增投资（投资笔数 20 笔未变，只是其中 1 笔从 current 转为 exited）。
  - 这不是抄错也不是没更新 —— 正文要写明「构成未变，因本季无新增投资」，不许含糊地说「构成基本稳定」。
  - 已逐页核对过 2025Q4 报告第 8 页。
- **脚注（本季实际印出的）**：
  ```
  Note: PAG BRS Fund III investment amount by geography, as a share of the US$1,258m invested to date, as at 31 March 2026. Composition is unchanged from 4Q25 because no new investments were made during the quarter. Source: PAG BRS Fund III quarterly newsletter, Q1 2026.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 33 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 34 · PAG BRS III — investment amount by currency

- **slug**：`fund_pag_comp_ccy`（稳定标识，编号会变、slug 不变）
- **位置**：`8.1`，版式 `pairL`（并排左）
- **形状**：`shares`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2025 Q4 Quarterly Newsletter.pdf`
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf`
  - 定位：「Fund Overview」 / 「Investment Overview」 / 「Net MOIC」 / 「构成未变，因本季无新增投资」
- **取数与构成**（本季实际做法，下季照做）：
  - PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf，第 6 页 "Fund Overview"（本季与上季两列并排，直接抄明值，非计算、非测量）与第 8 页 "Investment Overview"（四个饼图的百分比都在 PDF 文字层里）。
  - 上上季（3Q25）的数取自 PAG BRS Fund III L.P. - 2025 Q4 Quarterly Newsletter.pdf 第 6 页的对照列。
  - ⚠ 术语对照：PAG 报表写 "Net MOIC"，本报告 §9 统一叫 TVPI，是同一个东西，别当两个指标。
  - 本图 = 按 currency 的投资金额占比。
  - ⚠ 四个构成饼图在 2025Q4 与 2026Q1 完全相同（占比一个字都没变），原因是投资总额两季都是 USD1,258M、期间没有新增投资（投资笔数 20 笔未变，只是其中 1 笔从 current 转为 exited）。
  - 这不是抄错也不是没更新 —— 正文要写明「构成未变，因本季无新增投资」，不许含糊地说「构成基本稳定」。
  - 已逐页核对过 2025Q4 报告第 8 页。
- **脚注（本季实际印出的）**：
  ```
  Note: PAG BRS Fund III investment amount by currency, as a share of the US$1,258m invested to date, as at 31 March 2026. Composition is unchanged from 4Q25 because no new investments were made during the quarter. Source: PAG BRS Fund III quarterly newsletter, Q1 2026.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 34 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 35 · PAG BRS III — investment amount by bank counterparty

- **slug**：`fund_pag_comp_bank`（稳定标识，编号会变、slug 不变）
- **位置**：`8.1`，版式 `pairR`（并排右）
- **形状**：`shares`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2025 Q4 Quarterly Newsletter.pdf`
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf`
  - 定位：「Fund Overview」 / 「Investment Overview」 / 「Net MOIC」 / 「构成未变，因本季无新增投资」
- **取数与构成**（本季实际做法，下季照做）：
  - PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf，第 6 页 "Fund Overview"（本季与上季两列并排，直接抄明值，非计算、非测量）与第 8 页 "Investment Overview"（四个饼图的百分比都在 PDF 文字层里）。
  - 上上季（3Q25）的数取自 PAG BRS Fund III L.P. - 2025 Q4 Quarterly Newsletter.pdf 第 6 页的对照列。
  - ⚠ 术语对照：PAG 报表写 "Net MOIC"，本报告 §9 统一叫 TVPI，是同一个东西，别当两个指标。
  - 本图 = 按 bank counterparty 的投资金额占比。
  - ⚠ 四个构成饼图在 2025Q4 与 2026Q1 完全相同（占比一个字都没变），原因是投资总额两季都是 USD1,258M、期间没有新增投资（投资笔数 20 笔未变，只是其中 1 笔从 current 转为 exited）。
  - 这不是抄错也不是没更新 —— 正文要写明「构成未变，因本季无新增投资」，不许含糊地说「构成基本稳定」。
  - 已逐页核对过 2025Q4 报告第 8 页。
  - ⚠ 银行交易对手这张饼 PAG 只给占比、不披露银行名字（原图饼上就只有百分比，连图例都没有），所以标签只能写 Counterparty 1–12，按占比从大到小排。
  - 这张图的看点是集中度：最大一家 17%、前三家 47%、前五家 73%。
  - 正文不许编银行名字。
- **脚注（本季实际印出的）**：
  ```
  Note: PAG BRS Fund III investment amount by bank counterparty, as a share of the US$1,258m invested to date, as at 31 March 2026. Composition is unchanged from 4Q25 because no new investments were made during the quarter. Counterparty names are not disclosed by the fund; shares are ordered largest to smallest. The largest counterparty accounts for 17%, the top three for 47% and the top five for 73%. Source: PAG BRS Fund III quarterly newsletter, Q1 2026.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 35 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 36 · PAG BRS III — composition QoQ: by portfolio type and by currency (% of total investment amount)

- **slug**：`fund_pag_comp_qoq`（稳定标识，编号会变、slug 不变）
- **位置**：`8.1`，版式 `table`（表格）
- **形状**：`rows_qoq`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2025 Q4 Quarterly Newsletter.pdf`
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf`
  - 定位：「Fund Overview」 / 「Investment Overview」 / 「Net MOIC」 / 「构成未变，因本季无新增投资」
- **取数与构成**（本季实际做法，下季照做）：
  - PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf，第 6 页 "Fund Overview"（本季与上季两列并排，直接抄明值，非计算、非测量）与第 8 页 "Investment Overview"（四个饼图的百分比都在 PDF 文字层里）。
  - 上上季（3Q25）的数取自 PAG BRS Fund III L.P. - 2025 Q4 Quarterly Newsletter.pdf 第 6 页的对照列。
  - ⚠ 术语对照：PAG 报表写 "Net MOIC"，本报告 §9 统一叫 TVPI，是同一个东西，别当两个指标。
  - ⚠ 四个构成饼图在 2025Q4 与 2026Q1 完全相同（占比一个字都没变），原因是投资总额两季都是 USD1,258M、期间没有新增投资（投资笔数 20 笔未变，只是其中 1 笔从 current 转为 exited）。
  - 这不是抄错也不是没更新 —— 正文要写明「构成未变，因本季无新增投资」，不许含糊地说「构成基本稳定」。
  - 已逐页核对过 2025Q4 报告第 8 页。
- **脚注（本季实际印出的）**：
  ```
  Note: Quarter-on-quarter change in PAG BRS Fund III portfolio composition. Every share is unchanged from 4Q25 because no new investments were made in the quarter; total invested stayed at US$1,258m across 20 investments. Source: PAG BRS Fund III quarterly newsletters, Q1 2026 and Q4 2025.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 36 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 37 · PAG BRS Fund III — key performance and capital metrics, 1Q26 vs 4Q25

- **slug**：`fund_pag_kpi_qoq`（稳定标识，编号会变、slug 不变）
- **位置**：`8.1`，版式 `table`（表格）
- **形状**：`rows_qoq`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2025 Q4 Quarterly Newsletter.pdf`
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf`
  - 定位：「Fund Overview」 / 「Investment Overview」 / 「Net MOIC」 / 「6」
- **取数与构成**（本季实际做法，下季照做）：
  - PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf，第 6 页 "Fund Overview"（本季与上季两列并排，直接抄明值，非计算、非测量）与第 8 页 "Investment Overview"（四个饼图的百分比都在 PDF 文字层里）。
  - 上上季（3Q25）的数取自 PAG BRS Fund III L.P. - 2025 Q4 Quarterly Newsletter.pdf 第 6 页的对照列。
  - ⚠ 术语对照：PAG 报表写 "Net MOIC"，本报告 §9 统一叫 TVPI，是同一个东西，别当两个指标。
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`1Q26`　｜　该口径源上限：`1Q26`
  - 本季文件夹里同主题最新：`1Q26`（同口径）—— PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf（本季文件夹里最新的基金报告就是 1Q26）
  - 下季去哪儿看源末期：Fund/PAG BRS Fund III L.P. - <本季> Quarterly Newsletter.pdf 第 6 页 "Fund Overview" 的当季列
- **脚注（本季实际印出的）**：
  ```
  Note: PAG BRS Fund III key metrics as at 31 March 2026, with the prior two quarters for comparison. Net IRR eased to 14.7% from 15.6% while net MOIC rose to 1.11x from 1.09x and DPI advanced to 0.30x from 0.18x as distributions grew to US$167m. All figures as reported by the fund. Source: PAG BRS Fund III quarterly newsletters, Q1 2026 and Q4 2025.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 37 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 38 · PAG BRS Fund III — top 10 current investments by investment amount

- **slug**：`fund_pag_top10`（稳定标识，编号会变、slug 不变）
- **位置**：`8.1`，版式 `table`（表格）
- **形状**：`rows_flat`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf`
  - 定位：「Current Investments」 / 「Unrealized Value 971」 / 「投资金额合计 978.7」 / 「Investment Amount 1,258」
- **取数与构成**（本季实际做法，下季照做）：
  - PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf，第 9 页 "Current Investments" 表格。
  - 17 笔在投逐行抄自 PDF 文字层（含 Owen 那笔 —— 它的 spread 是 N/A、货币是 USD+GBP，用正则按百分号取会漏掉，必须按名单核对行数）。
  - 按投资金额降序取前 10。
  - ⭐ 加总校验（四列全部对上原表 Total 行）：投资金额 978.7 / 已实现 125.2 / 未实现 971.0 / 总价值 1,096.4，原表 Total 行是 978.7 / 125.2 / 971.1 / 1,096.3，差异只在四舍五入的 0.1。
  - 再交叉一层：未实现合计 971.0 与第 6 页 Fund Overview 的 "Unrealized Value 971" 一致。
  - 注意「投资金额合计 978.7」是 17 笔在投的合计，与 Fund Overview 的 "Investment Amount 1,258"（含 3 笔已退出）不是同一口径，正文不许混用。
- **脚注（本季实际印出的）**：
  ```
  Note: PAG BRS Fund III ten largest current investments by invested amount as at 31 March 2026, out of 17 current positions. The ten account for 74.5% of the US$979m currently invested; the fund has invested US$1,258m in total across 20 investments, three of which have exited. Position names are the fund's own project code names. Spreads are over the relevant floating reference rate. Source: PAG BRS Fund III quarterly newsletter, Q1 2026.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 38 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 39 · Guggenheim PDF IV — GICS sub-industry mix (% of par)

- **slug**：`fund_gug_gics_mix`（稳定标识，编号会变、slug 不变）
- **位置**：`8.2`，版式 `pairL`（并排左）
- **形状**：`shares`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Fund/Guggenheim PDF IV Report - Q4 2025.pdf`
  - `2026Q3/Fund/Guggenheim PDF IV Report - Q1 2026.pdf`
  - 定位：「Guggenheim Private Debt Fund IV — Aggregate Private Debt Characteristics (as of 3.31.2026)」 / 「PDF IV Portfolio」 / 「PDF IV」 / 「Invested Capital」
- **取数与构成**（本季实际做法，下季照做）：
  - Guggenheim PDF IV Report - Q1 2026.pdf，第 5 页 "Guggenheim Private Debt Fund IV — Aggregate Private Debt Characteristics (as of 3.31.2026)"，以及第 3–4 页 "PDF IV Portfolio" 逐笔持仓表。
  - 上季对照取自 Guggenheim PDF IV Report - Q4 2025.pdf 同名页。
  - ⚠ 口径：报告里的 "PDF IV" 是三只载体的合计（Guardian (U), L.P. / PDF IV-A / PDF IV-B），不是单一基金；"Invested Capital" 是 40 笔投资的累计投放额。
  - 本图 = 按 par 的 GICS 子行业占比，原图 25 个切片。
  - ⚠ 25 个切片的明标值加总是 101%，不是 100% —— 每片都四舍五入到整数百分点造成的，不是抄错。
  - 账本里 all_slices 存原始 25 项明值；作图只画前 12 大，其余 13 项（每项 1–2%）合成 "Other"，否则 25 个标签在 3.35in 画布上必然重叠。
  - ⭐ 已把 25 个标签逐个对着渲染图核过一遍（文字层里标签跨行会被截断，例如 "Personal Care\nProducts, 5%"，只靠正则会读成 "Products 5%"）。
  - 原图 25 个切片的明标值加总 101%（每片各自四舍五入到整数百分点）。
  - 作图时把 1pp 残差归进 "Other" 桶：前 12 大合计 75%，Other 记 25% （而不是 13 项明值直接相加的 26%）。
  - 这是残差归并的标准做法，原始 25 项明值一个不动地存在 all_slices 里，可随时复核。
  - 正文引用单个行业占比时用 all_slices 的原值，不要用归并后的 Other。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - ⚠ 25 个切片的明标值加总是 101%，不是 100% —— 每片都四舍五入到整数百分点造成的，不是抄错
  - 原图 25 个切片的明标值加总 101%（每片各自四舍五入到整数百分点）
  - 作图时把 1pp 残差归进 "Other" 桶：前 12 大合计 75%，Other 记 25% （而不是 13 项明值直接相加的 26%）
  - 这是残差归并的标准做法，原始 25 项明值一个不动地存在 all_slices 里，可随时复核
- **恒等式容差**：±2.0 —— 源报告印的是四舍五入到整数的百分比，25 个子行业相加得 101% —— 舍入残差，不是错数。第一版把 13 个小项并成 "Other" 时正好凑到 100，现在按基线逐个点名就露出了这个残差。
- **_prev_collapsed_note**：第一版只点名了 12 个、把其余 13 个并成 "Other (13 sub-industries) 25%"，基线是 21 个点名 + Other(4)。现按账本 all_slices 全部点名。
- **脚注（本季实际印出的）**：
  ```
  Note: GICS sub-industry mix as a share of par, all 25 sub-industries shown individually; the two software sub-industries are highlighted because software is the stress theme running through this report. Source: Guggenheim Investments PDF IV quarterly report, Q1 2026. Individual shares are as printed in the source (rounded to whole percentage points), so they sum to 101% rather than exactly 100%.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 39 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 40 · Guggenheim PDF IV — sponsored vs non-sponsored (% of NAV)

- **slug**：`fund_gug_sponsored`（稳定标识，编号会变、slug 不变）
- **位置**：`8.2`，版式 `pairR`（并排右）
- **形状**：`shares`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Fund/Guggenheim PDF IV Report - Q4 2025.pdf`
  - `2026Q3/Fund/Guggenheim PDF IV Report - Q1 2026.pdf`
  - 定位：「Guggenheim Private Debt Fund IV — Aggregate Private Debt Characteristics (as of 3.31.2026)」 / 「PDF IV Portfolio」 / 「PDF IV」 / 「Invested Capital」
- **取数与构成**（本季实际做法，下季照做）：
  - Guggenheim PDF IV Report - Q1 2026.pdf，第 5 页 "Guggenheim Private Debt Fund IV — Aggregate Private Debt Characteristics (as of 3.31.2026)"，以及第 3–4 页 "PDF IV Portfolio" 逐笔持仓表。
  - 上季对照取自 Guggenheim PDF IV Report - Q4 2025.pdf 同名页。
  - ⚠ 口径：报告里的 "PDF IV" 是三只载体的合计（Guardian (U), L.P. / PDF IV-A / PDF IV-B），不是单一基金；"Invested Capital" 是 40 笔投资的累计投放额。
  - 本图 = Sponsor vs Non-Sponsor（按 NAV 占比）：72% / 28%，加总 100%。
- **脚注（本季实际印出的）**：
  ```
  Note: Guggenheim PDF IV sponsored versus non-sponsored exposure as a share of NAV, as at 31 March 2026. Source: Guggenheim Investments PDF IV quarterly report, Q1 2026.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 40 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 41 · Guggenheim PDF IV — composition QoQ: GICS sub-industry mix and sponsored split

- **slug**：`fund_gug_comp_qoq`（稳定标识，编号会变、slug 不变）
- **位置**：`8.2`，版式 `table`（表格）
- **形状**：`rows_qoq`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Fund/Guggenheim PDF IV Report - Q4 2025.pdf`
  - `2026Q3/Fund/Guggenheim PDF IV Report - Q1 2026.pdf`
  - 定位：「Guggenheim Private Debt Fund IV — Aggregate Private Debt Characteristics (as of 3.31.2026)」 / 「PDF IV Portfolio」 / 「PDF IV」 / 「Invested Capital」
- **取数与构成**（本季实际做法，下季照做）：
  - Guggenheim PDF IV Report - Q1 2026.pdf，第 5 页 "Guggenheim Private Debt Fund IV — Aggregate Private Debt Characteristics (as of 3.31.2026)"，以及第 3–4 页 "PDF IV Portfolio" 逐笔持仓表。
  - 上季对照取自 Guggenheim PDF IV Report - Q4 2025.pdf 同名页。
  - ⚠ 口径：报告里的 "PDF IV" 是三只载体的合计（Guardian (U), L.P. / PDF IV-A / PDF IV-B），不是单一基金；"Invested Capital" 是 40 笔投资的累计投放额。
  - 本表 = 账户概览的季度对比。
  - Q1 2026：40 笔投资 / 投放 $3,202m / 杠杆 4.9x / LTV 38%；Q4 2025：38 笔 / 杠杆 4.9x / LTV 37%；Q4 2025：38 笔 / 投放 $3,035m / 杠杆 4.9x / LTV 37% / sponsored 69%。
  - Q4 的投放额与 sponsor 占比在文字层被版式打散，已渲染 Q4 报告第 5 页读图确认（$3,035m、Sponsor 69% / Non Sponsor 31%），不是从本季值倒推的。
  - ⚠⚠ 口径变了：Q4 2025 的 GICS 饼图标的是 "as % of NAV"，Q1 2026 标的是 "as % of Par" —— 两季分母不同，行业占比不可直接比较。
  - sponsor / non-sponsor 那张两季都是 % of NAV，可以比。
  - 正文写行业构成变化时必须避开跨季比较，或明确写出分母差异。
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`1Q26`　｜　该口径源上限：`1Q26`
  - 本季文件夹里同主题最新：`1Q26`（同口径）—— Fund/Guggenheim PDF IV Report - Q1 2026.pdf（本季文件夹里最新的一期）
  - 下季去哪儿看源末期：Fund/ 目录下 Guggenheim 最新一期季报的 "PDF IV Account Overview" 页；上季列取上一期季报的同一页（账本已存，不必重翻）
- **脚注（本季实际印出的）**：
  ```
  Note: Guggenheim PDF IV account overview, quarter on quarter. The portfolio grew to 40 investments from 38 and invested capital to US$3,202m from US$3,035m; leverage was unchanged at 4.9x, LTV rose 1pp to 38% and the sponsored share of NAV rose 3pp to 72%. The GICS mix is reported as a share of par this quarter but as a share of NAV last quarter, so the two are not comparable. Sources: Guggenheim Investments PDF IV quarterly reports, Q1 2026 and Q4 2025.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 41 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 42 · Guggenheim PDF IV — 1Q26 closed transactions (three deals, all sponsor-backed)

- **slug**：`fund_gug_closed_deals`（稳定标识，编号会变、slug 不变）
- **位置**：`8.2`，版式 `table`（表格）
- **形状**：`rows_flat`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Fund/Guggenheim PDF IV Report - Q1 2026.pdf`
  - 定位：「1Q26 Closed Transactions Case Studies」 / 「S+550」 / 「E+475」 / 「PF Adj. EBITDA」
- **取数与构成**（本季实际做法，下季照做）：
  - Guggenheim PDF IV Report - Q1 2026.pdf，第 6–9 页 "1Q26 Closed Transactions Case Studies"（每笔一页：标题给公司与业务描述，中间一条给结构 / 净杠杆 / 定价 / LTV / 差异化点，下半页是四栏叙述）。
  - 本季 3 笔，全部标注 Sponsored。
  - 逐页抄自 PDF 文字层。
  - ⚠ 定价里的基准要还原全称：原文写 "S+550"、"E+475"，S = SOFR、E = EURIBOR，别在正文里保留单字母缩写。
  - ⚠ 杠杆口径不统一：Cellulose Fibers 与 Adevinta 写的是 net leverage，Wells Concrete 写的是 "PF Adj. EBITDA"（proforma 调整后），三笔不能直接比大小，正文要提一句。
  - ⚠ 三笔都只披露到「~47% / ~35% / ~49%」这种约数 LTV，不要在正文里给到小数位。
- **脚注（本季实际印出的）**：
  ```
  Note: Guggenheim PDF IV transactions closed in 1Q26, all sponsor-backed. Pricing is the spread over the relevant base rate at the stated original issue discount. Leverage is reported on a net basis for the first two deals and on a pro-forma adjusted-EBITDA basis for Wells Concrete, so the three are not directly comparable. Loan-to-value figures are disclosed as approximations. Source: Guggenheim Investments PDF IV quarterly report, Q1 2026.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 42 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 43 · HSBC RCF — current portfolio by sector (share of 11 investments)

- **slug**：`fund_hsbc_sector`（稳定标识，编号会变、slug 不变）
- **位置**：`8.3`，版式 `pairL`（并排左）
- **形状**：`shares`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Fund/RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf`
  - 定位：「Portfolio Overview」 / 「Portfolio Statistics」 / 「HSBC RCF Partnership Fund RAIF SICAV-S.A. …」 / 「Number of investments at settled status 9」
- **取数与构成**（本季实际做法，下季照做）：
  - RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf，第 10 页 "Portfolio Overview" 的持仓汇总表（项目 / 国家 / 行业 / 子行业 / 到期 / 现行适用保证金 / 观察名单状态），配合第 6 页 "Portfolio Statistics" 的加权平均数。
  - ⚠⚠ 文件名陷阱：这份与 Q4 2025 那份 "HSBC RCF Partnership Fund RAIF SICAV-S.A. …" 是同一只基金，内页标题都是 HSBC RCF Partnership Fund —— 认内页标题不认文件名。
  - 本图 = 11 笔在投（含 2 笔 in settlement）按 RCF 承诺额的行业占比，合计 EUR 85.30m。
  - ⭐ 三重校验，全部对上：① 9 笔 settled 承诺额按承诺加权的平均保证金算出来 319.6 bps，报告第 6 页明标 319.6 bps，差 0.0 bps；② settled 笔数 9，与明标 "Number of investments at settled status 9" 一致；③ 平均单笔 8.4m，与明标 "Average size of RCF commitment (EURm) 8.4" 一致。
  - 其中 Project Oliver 的承诺是 GBP 7.5m（全组合唯一一笔非欧元），报告没给欧元等值，用 settled 合计 75.3m 减去其余 8 笔的 66.63m 倒推得 8.67m —— 这个倒推值正是让上面三个校验同时成立的值，可信；账本里已注明它是倒推而非明值。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - ⭐ 三重校验，全部对上：① 9 笔 settled 承诺额按承诺加权的平均保证金算出来 319.6 bps，报告第 6 页明标 319.6 bps，差 0.0 bps
  - ② settled 笔数 9，与明标 "Number of investments at settled status 9" 一致
  - ③ 平均单笔 8.4m，与明标 "Average size of RCF commitment (EURm) 8.4" 一致
- **脚注（本季实际印出的）**：
  ```
  Note: Share of the 11 current (unrealised) investments by count, so each holding is 1/11 = 9.1%. Sectors with two holdings therefore show twice that. A commitment-weighted version of the same split is given in the text. Source: HSBC AM.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 43 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 44 · HSBC RCF — current margin by project (bps)

- **slug**：`fund_hsbc_margin`（稳定标识，编号会变、slug 不变）
- **位置**：`8.3`，版式 `pairR`（并排右）
- **形状**：`bars_categorical`　**出图函数**：`cat_hbars()` in `build_s7.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  cat_hbars('fund_hsbc_margin', 'pair', 3.2, 'Margin over base rate (bp)',
  vline=319.6, vlabel='wtd avg 319.6bp')
  ```
- **数据源**：
  - `2026Q3/Fund/RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf`
  - 定位：「Portfolio Overview」 / 「Portfolio Statistics」 / 「HSBC RCF Partnership Fund RAIF SICAV-S.A. …」 / 「Number of investments at settled status 9」
- **取数与构成**（本季实际做法，下季照做）：
  - RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf，第 10 页 "Portfolio Overview" 的持仓汇总表（项目 / 国家 / 行业 / 子行业 / 到期 / 现行适用保证金 / 观察名单状态），配合第 6 页 "Portfolio Statistics" 的加权平均数。
  - ⚠⚠ 文件名陷阱：这份与 Q4 2025 那份 "HSBC RCF Partnership Fund RAIF SICAV-S.A. …" 是同一只基金，内页标题都是 HSBC RCF Partnership Fund —— 认内页标题不认文件名。
  - 本图 = 各项目现行适用保证金（bps，基准利率之上），按高到低排。
  - 基准不统一：Emerald 是 SOFR、Media 是 SONIA，其余是 EURIBOR，账本里 base_rate 字段有记；图上只画 spread，不同基准的绝对收益不可直接相加，正文要提一句。
  - ⭐ 三重校验，全部对上：① 9 笔 settled 承诺额按承诺加权的平均保证金算出来 319.6 bps，报告第 6 页明标 319.6 bps，差 0.0 bps；② settled 笔数 9，与明标 "Number of investments at settled status 9" 一致；③ 平均单笔 8.4m，与明标 "Average size of RCF commitment (EURm) 8.4" 一致。
  - 其中 Project Oliver 的承诺是 GBP 7.5m（全组合唯一一笔非欧元），报告没给欧元等值，用 settled 合计 75.3m 减去其余 8 笔的 66.63m 倒推得 8.67m —— 这个倒推值正是让上面三个校验同时成立的值，可信；账本里已注明它是倒推而非明值。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - ⭐ 三重校验，全部对上：① 9 笔 settled 承诺额按承诺加权的平均保证金算出来 319.6 bps，报告第 6 页明标 319.6 bps，差 0.0 bps
  - ② settled 笔数 9，与明标 "Number of investments at settled status 9" 一致
  - ③ 平均单笔 8.4m，与明标 "Average size of RCF commitment (EURm) 8.4" 一致
- **脚注（本季实际印出的）**：
  ```
  Note: HSBC RCF Partnership Fund current applicable margin over the relevant base rate, by investment, as at 31 March 2026. Margins range from 260bp to 353bp with a commitment-weighted average of 319.6bp across the nine settled investments. Base rates differ by deal — SOFR for Emerald, SONIA for Media, EURIBOR for the rest — so margins are comparable but all-in yields are not. Source: HSBC RCF Partnership Fund quarterly report, Q1 2026.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 44 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 45 · HSBC RCF — composition QoQ: current portfolio by sector (count of investments)

- **slug**：`fund_hsbc_comp_qoq`（稳定标识，编号会变、slug 不变）
- **位置**：`8.3`，版式 `table`（表格）
- **形状**：`rows_qoq`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Fund/RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf`
  - 定位：「Portfolio Overview」
- **取数与构成**（本季实际做法，下季照做）：
  - RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf 的 "Portfolio Overview" 持仓表（11 笔）与 2025Q4 投资人报告正文 "The Fund holds 8 investments as of Q4 2025: Projects Emerald, Connect, Media, Alpha, Pique, Ink, Service, Freeze"。
  - 按行业归类后计数，两期都不含 4Q25 已退出的 Project Vision 与 Project Clark。
- **脚注（本季实际印出的）**：
  ```
  Note: By count of current (unrealised) investments. Projects Vision and Clark were realised in 4Q25 and are excluded from both columns. Source: HSBC AM.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 45 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 46 · HSBC RCF — current portfolio summary

- **slug**：`fund_hsbc_portfolio`（稳定标识，编号会变、slug 不变）
- **位置**：`8.3`，版式 `table`（表格）
- **形状**：`rows_flat`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Fund/RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf`
  - 定位：「Portfolio Overview」 / 「Portfolio Statistics」 / 「HSBC RCF Partnership Fund RAIF SICAV-S.A. …」 / 「Number of investments at settled status 9」
- **取数与构成**（本季实际做法，下季照做）：
  - RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf，第 10 页 "Portfolio Overview" 的持仓汇总表（项目 / 国家 / 行业 / 子行业 / 到期 / 现行适用保证金 / 观察名单状态），配合第 6 页 "Portfolio Statistics" 的加权平均数。
  - ⚠⚠ 文件名陷阱：这份与 Q4 2025 那份 "HSBC RCF Partnership Fund RAIF SICAV-S.A. …" 是同一只基金，内页标题都是 HSBC RCF Partnership Fund —— 认内页标题不认文件名。
  - 本表 = 11 笔在投逐行。
  - ⭐ 三重校验，全部对上：① 9 笔 settled 承诺额按承诺加权的平均保证金算出来 319.6 bps，报告第 6 页明标 319.6 bps，差 0.0 bps；② settled 笔数 9，与明标 "Number of investments at settled status 9" 一致；③ 平均单笔 8.4m，与明标 "Average size of RCF commitment (EURm) 8.4" 一致。
  - 其中 Project Oliver 的承诺是 GBP 7.5m（全组合唯一一笔非欧元），报告没给欧元等值，用 settled 合计 75.3m 减去其余 8 笔的 66.63m 倒推得 8.67m —— 这个倒推值正是让上面三个校验同时成立的值，可信；账本里已注明它是倒推而非明值。
- ⭐ **锚点校验**（必须记进 `src`，不通过不许进门）：
  - ⭐ 三重校验，全部对上：① 9 笔 settled 承诺额按承诺加权的平均保证金算出来 319.6 bps，报告第 6 页明标 319.6 bps，差 0.0 bps
  - ② settled 笔数 9，与明标 "Number of investments at settled status 9" 一致
  - ③ 平均单笔 8.4m，与明标 "Average size of RCF commitment (EURm) 8.4" 一致
- **脚注（本季实际印出的）**：
  ```
  Note: HSBC RCF Partnership Fund current portfolio at 31 March 2026 — eleven investments, of which nine are settled and two (Tooth, Box) in settlement. Project Oliver is committed in sterling (GBP 7.5m); its euro equivalent of EUR 8.67m is derived from the fund's disclosed settled commitment total. Margins are over the base rate shown. Source: HSBC RCF Partnership Fund quarterly report, Q1 2026.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 46 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 47 · Positioning scorecard — Junson holdings vs vintage-matched cohorts (baseline: 2026Q3)

- **slug**：`ca_scorecard`（稳定标识，编号会变、slug 不变）
- **位置**：`9.1`，版式 `table`（表格）
- **形状**：`rows_qoq`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx`
  - `2026Q3/Fund/RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf`
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf`
  - 定位：「相对一个外部北美同业基准的位置」 / 「同组内排名」 / 「6」 / 「4」
- **取数与构成**（本季实际做法，下季照做）：
  - 分位数由本季重算：基金侧数值取自各基金季报 PDF 明值 —— PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf 第 6 页（Net IRR 14.7% / Net MOIC 1.11x / DPI 0.30x）、RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf 第 4 页（IRR 34.50% / TVPI 1.21x / DPI 0.14x）；cohort 侧取自 2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx（导出日 2026-08-13，331 只）。
  - 分位定义按 report-spec：cohort 里严格低于本基金值的占比。
  - vintage 约定 = 首笔投资年份（PAG 2023、Guggenheim 2024、HSBC 2024）。
  - ⭐ 独立对账：6 个分位（两只基金 × 三个指标）连样本数一起与同事快照逐个比对，6/6 完全一致 —— PAG 92/28/72（n=26/25/25）、HSBC 100/100/62（n=11/8/8）。
  - ⚠⚠ Guggenheim 三行本季留空，原因见 rows[].gap 与 _gap_note。
  - ⚠⚠ 口径披露：⚠⚠ 口径披露（Alex 2026-08-21 决定：筛选不改，但必须写清）：这份 PitchBook 筛选限定 Fund Location = Americas › North America，共 331 只基金。
  - Junson 自己的三只基金 —— PAG BRS III（香港）、HSBC RCF（卢森堡 RAIF）、Guggenheim PDF IV —— 在这 331 只里一只都没有命中（各按 Investor 与 Funds 两列做正则检索，命中数 0/0/0）。
  - 所以 §9 的分位数是「相对一个外部北美同业基准的位置」，不是「同组内排名」，PAG 以亚洲为主、HSBC 以欧洲为主，存在地域错配。
  - §9 开头段和附录方法论段都必须显式写出这一点，不许让读者误以为我们在池内。
- **_gap_note**：Guggenheim 季报无任何回报指标（两季全文检索零命中）。三行数值为同事基于 Guggenheim 内部投资报告的计算值（Alex 2026-08-24 授权使用），基准日为快照导出日 2026-08-13，† 标注在表内。百分位为我们用 PitchBook 原始导出独立重算。
- **脚注（本季实际印出的）**：
  ```
  Note: Scorecard of Junson holdings against vintage-matched PitchBook cohorts. † Guggenheim PDF IV figures are computed internally by Junson from the manager’s internal investor reporting (its quarterly report discloses no return metrics); percentiles for all funds are recomputed by Junson from the PitchBook export. * HSBC RCF readings are ramp-up artefacts on a thin cohort. Sources: fund quarterly reports; Junson internal calculations; PitchBook.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 47 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 48 · Junson holdings vs named competitor funds (latest flagship vehicles)

- **slug**：`ca_named_comparators`（稳定标识，编号会变、slug 不变）
- **位置**：`9.2`，版式 `table`（表格）
- **形状**：`rows_flat`　（表格，由 build_doc 直接排）
- **数据源**：
  - `2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx`
  - 定位：「Data」 / 「单纯 vintage 最新」 / 「相对一个外部北美同业基准的位置」 / 「同组内排名」
- **取数与构成**（本季实际做法，下季照做）：
  - 2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx，sheet "Data"。
  - PitchBook 检索：Fund Strategy = Direct Lending；Fund Location = Americas > North America。
  - 导出日 2026-08-13，导出人 Xiyang Zhao (Junson Capital)，检索链接 https://my.pitchbook.com/?pcc=1372632-49（导出日 2026-08-13，331 只基金）。
  - 选取规则：取该管理人旗舰 direct lending 系列的最新一只（Alex 2026-08-21 定）。
  - 不用「单纯 vintage 最新」—— 那样 Ares 会取到 Emerald（$370m 的小体量专户，IRR 27.3%），拿它当旗舰对标会误导。
  - 系列用基金名正则锁定，不用 Investor 字段，因为 PitchBook 的 Investor 写法每季会变（例：Twin Brook 有时写成 TPG Angelo Gordon）。
  - ⚠⚠ 口径披露（Alex 2026-08-21 决定：筛选不改，但必须写清）：这份 PitchBook 筛选限定 Fund Location = Americas › North America，共 331 只基金。
  - Junson 自己的三只基金 —— PAG BRS III（香港）、HSBC RCF（卢森堡 RAIF）、Guggenheim PDF IV —— 在这 331 只里一只都没有命中（各按 Investor 与 Funds 两列做正则检索，命中数 0/0/0）。
  - 所以 §9 的分位数是「相对一个外部北美同业基准的位置」，不是「同组内排名」，PAG 以亚洲为主、HSBC 以欧洲为主，存在地域错配。
  - §9 开头段和附录方法论段都必须显式写出这一点，不许让读者误以为我们在池内。
  - Junson 三只基金的行待从基金季报 PDF 提取后补上（见 _todo）。
  - Junson 三只基金的行已补：PAG 与 HSBC 取自各自季报明值（见 §8 的 Ex 37 / Ex 45），Guggenheim 留空。
  - ⚠ 这三行与 PitchBook 那批不同源、也不同口径：规模 PAG 用承诺额、HSBC 是欧元未换算；called% PAG 用 capital contributions、HSBC 用已缴/基金规模；三只都没有 PitchBook 四分位（不在筛选池内）。
  - 表里要留出「口径」一列，不许把它们和 PitchBook 那批当同一口径读。
- **脚注（本季实际印出的）**：
  ```
  Note: Named flagship direct lending funds from the same PitchBook screen — the latest fund in each manager's flagship series. Metrics are as reported by PitchBook at the 13 August 2026 export date. * marks funds still ramping (less than 25% called), whose IRR and TVPI are not yet meaningful. Junson's own funds are shown above the comparators; they are not constituents of this screen, carry no PitchBook quartile, and their size and called-percentage bases differ from the PitchBook fields — see the basis note on each row. Guggenheim PDF IV discloses no return metrics. Source: PitchBook.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 48 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 49 · Baseline levels: fund IRR vs vintage cohort median

- **slug**：`ca_momentum_irr`（稳定标识，编号会变、slug 不变）
- **位置**：`9.3`，版式 `pairL`（并排左）
- **形状**：`rows_qoq`　**出图函数**：`level_vs_median()` in `build_s7.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  level_vs_median('ca_momentum_irr', 'pair', 3.0, 'Net IRR (%)', fmt='{:.1f}')
  ```
- **数据源**：
  - `2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx`
  - `2026Q3/Fund/RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf`
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf`
  - 定位：「Baseline quarter: record levels instead」 / 「Data」
- **取数与构成**（本季实际做法，下季照做）：
  - 本季是账本基线季 —— report-spec §9.3 明确写「Baseline quarter: record levels instead」，所以这里记的是水平值而不是 QoQ 变动，相对动量要等 2026Q4 有了第二个季度才能算。
  - 数值与 Ex 47 同源：PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf、RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf、2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx。
  - Guggenheim 无可核来源，留空。
  - 定位同 Ex 47（ca_scorecard）：基金侧取各基金季报的明值页，cohort 侧取 PitchBook 导出的 "Data" sheet。
- **脚注（本季实际印出的）**：
  ```
  Note: Fund net IRR against the vintage-matched cohort median. This is the first quarter recorded, so levels are shown; quarter-on-quarter momentum begins from next quarter. Guggenheim PDF IV figures are computed internally by Junson from the manager’s internal investor reporting, as its quarterly report discloses no return metrics. Sources: fund quarterly reports; Junson internal calculations (Guggenheim); PitchBook.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 49 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 50 · Baseline levels: fund TVPI and DPI vs vintage cohort medians

- **slug**：`ca_momentum_tvpi`（稳定标识，编号会变、slug 不变）
- **位置**：`9.3`，版式 `pairR`（并排右）
- **形状**：`rows_qoq`　**出图函数**：`level_vs_median()` in `build_s7.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  level_vs_median('ca_momentum_tvpi', 'pair', 3.0, 'TVPI (x)', fmt='{:.2f}')
  ```
- **数据源**：
  - `2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx`
  - `2026Q3/Fund/RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf`
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf`
  - 定位：「Baseline quarter: record levels instead」 / 「TVPI and DPI」 / 「Data」 / 「6」
- **取数与构成**（本季实际做法，下季照做）：
  - 本季是账本基线季 —— report-spec §9.3 明确写「Baseline quarter: record levels instead」，所以这里记的是水平值而不是 QoQ 变动，相对动量要等 2026Q4 有了第二个季度才能算。
  - 数值与 Ex 47 同源：PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf、RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf、2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx。
  - Guggenheim 无可核来源，留空。
  - 。
  - DPI 一组：PAG 0.30x（季报第 6 页明值）、HSBC 0.14x（投资人报告第 4 页明值）；cohort 中位数 PAG 2023v 0.15x、HSBC/GUG 2024v 0.10x（meta.cohorts 重算值）。
  - 第一版漏了 DPI 这一组（题注写的是 "TVPI and DPI"），已补。
  - 定位同 Ex 47（ca_scorecard）：基金侧取各基金季报的明值页，cohort 侧取 PitchBook 导出的 "Data" sheet。
- **脚注（本季实际印出的）**：
  ```
  Note: Fund TVPI and DPI against the vintage-matched cohort medians. Guggenheim PDF IV figures are computed internally by Junson from the manager’s internal investor reporting, as its quarterly report discloses no return metrics. Sources: fund quarterly reports; Junson internal calculations (Guggenheim); PitchBook.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 50 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 51 · IRR percentile rank within vintage cohort — trajectory (baseline point)

- **slug**：`ca_traj_irr_pct`（稳定标识，编号会变、slug 不变）
- **位置**：`9.4`，版式 `pairL`（并排左）
- **形状**：`pct_history`　**出图函数**：`pct_points()` in `build_s7.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  pct_points('ca_traj_irr_pct', 'pair', 3.0, 'Net IRR percentile')
  ```
- **数据源**：
  - `2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx`
  - `2026Q3/Fund/RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf`
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf`
  - 定位：「看起来缺了」 / 「Data」
- **取数与构成**（本季实际做法，下季照做）：
  - 分位轨迹是**只追加**的：本季是第一个点，2026Q3。
  - 数值与 Ex 47 同源：PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf、RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf、2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx。
  - 算法同 Ex 47（严格低于本基金值的 cohort 占比）。
  - Guggenheim 本季无点（无可核来源），history 留空数组 —— 不要因为「看起来缺了」而去补，缺的原因写在 Ex 47 的 rows[].gap 里。
  - 下季只许 append，历史点一个都不能改。
  - 定位同 Ex 47（ca_scorecard）：基金侧取各基金季报的明值页，cohort 侧取 PitchBook 导出的 "Data" sheet。
- **history_gaps**：{"_resolved": "Guggenheim 已按内部计算口径入点（Alex 2026-08-24 授权），下季照旧：值问同事要内部计算，百分位从 PitchBook 导出重算。"}
- **脚注（本季实际印出的）**：
  ```
  Note: Net IRR percentile against the vintage-matched cohort, one point added per quarter. The series starts this quarter. Guggenheim PDF IV values are computed internally by Junson from the manager’s internal investor reporting (marked †), as its quarterly report discloses no return metrics. Sources: fund quarterly reports; PitchBook.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 51 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 52 · TVPI percentile rank within vintage cohort — trajectory (baseline point)

- **slug**：`ca_traj_tvpi_pct`（稳定标识，编号会变、slug 不变）
- **位置**：`9.4`，版式 `pairR`（并排右）
- **形状**：`pct_history`　**出图函数**：`pct_points()` in `build_s7.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  pct_points('ca_traj_tvpi_pct', 'pair', 3.0, 'TVPI percentile')
  ```
- **数据源**：
  - `2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx`
  - `2026Q3/Fund/RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf`
  - `2026Q3/Fund/PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf`
  - 定位：「看起来缺了」 / 「Data」
- **取数与构成**（本季实际做法，下季照做）：
  - 分位轨迹是**只追加**的：本季是第一个点，2026Q3。
  - 数值与 Ex 47 同源：PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf、RCF Capital Solutions Fund Alternatives Investment Report - Q1 2026 - Investor Report_Final.pdf、2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx。
  - 算法同 Ex 47（严格低于本基金值的 cohort 占比）。
  - Guggenheim 本季无点（无可核来源），history 留空数组 —— 不要因为「看起来缺了」而去补，缺的原因写在 Ex 47 的 rows[].gap 里。
  - 下季只许 append，历史点一个都不能改。
  - 定位同 Ex 47（ca_scorecard）：基金侧取各基金季报的明值页，cohort 侧取 PitchBook 导出的 "Data" sheet。
- **history_gaps**：{"_resolved": "Guggenheim 已按内部计算口径入点（Alex 2026-08-24 授权），下季照旧：值问同事要内部计算，百分位从 PitchBook 导出重算。"}
- **脚注（本季实际印出的）**：
  ```
  Note: TVPI percentile against the vintage-matched cohort, one point added per quarter. The series starts this quarter. Guggenheim PDF IV values are computed internally by Junson from the manager’s internal investor reporting (marked †), as its quarterly report discloses no return metrics. Sources: fund quarterly reports; PitchBook.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 52 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 53 · Cohort dispersion: interquartile range width by vintage (IRR, pp; TVPI, x)

- **slug**：`ca_cohort_iqr`（稳定标识，编号会变、slug 不变）
- **位置**：`9.5`，版式 `solo`（满宽单图）
- **形状**：`bars_categorical_dual`　**出图函数**：`dual_bars()` in `build_s6.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  dual_bars('ca_cohort_iqr', 'solo', 2.9, 'Net IRR IQR (pp)', 'TVPI IQR (x)', every=1)
  ```
- **数据源**：
  - `2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx`
  - 定位：「Data」 / 「333 funds」 / 「离散度为零」 / 「该 vintage 总基金数≥5」
- **取数与构成**（本季实际做法，下季照做）：
  - 2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx，sheet "Data"。
  - 筛选口径：PitchBook 检索：Fund Strategy = Direct Lending；Fund Location = Americas > North America。
  - 导出日 2026-08-13，导出人 Xiyang Zhao (Junson Capital)，检索链接 https://my.pitchbook.com/?pcc=1372632-49。
  - 样本 331 只基金 —— 注意 report-spec 写的「333 funds」是数表格行数（表头后 333 行 = 331 只基金 + 1 个空行 + 1 行 PitchBook 版权声明），真实样本数 331，下季不要去凑 333。
  - 所有统计都是从这份导出表直接算的（分位数用线性插值口径）。
  - ⭐ 独立对账：与同事的 CA_snapshot_2026Q3.json 逐项比 36 项（4 个 vintage × 3 个指标 × n/中位/IQR），0 项不一致 —— 两边各自从同一份 xlsx 算出同样的结果。
  - （同事快照里 q1/q3 的命名是 PE 惯例，q1 = 表现更好那端，和统计学反着，对账按 IQR 比。
  - ） 本图 = 各 vintage 的四分位距（P75−P25）：IRR 以百分点计、TVPI 以倍数计。
  - 只画 2010–2025 这 16 个 vintage —— 这段每年 n≥5，是连续的；被排除的 vintage（1997, 2000, 2002, 2005, 2006, 2007, 2008, 2009, 2026）样本太薄（多数 n=1–3），IQR 没有意义，尤其 2026 只有 1 只基金、IQR 会算成 0，画出来会被误读成「离散度为零」。
  - 只画两个指标各自都有 n≥5 的 vintage：2010–2025，共 16 个。
  - （之前是按「该 vintage 总基金数≥5」筛的，那样会放进 IRR 有 5 只但 TVPI 只有 3 只的年份，IQR 不可比。
  - ）2026 只有 1 只基金，IQR 会算成 0，画出来会被误读成「离散度为零」，必须排除。
- **脚注（本季实际印出的）**：
  ```
  Note: Interquartile range of net IRR (percentage points) and TVPI (multiple) across North American direct lending drawdown funds in the PitchBook screen, by vintage year, from the 2019 vintage onward. Widening dispersion within a vintage is an early sign that industry stress is reaching fund marks. Vintages with fewer than five ranked funds on either measure are excluded. Screen exported 2026-08-13; 331 funds. Source: PitchBook.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 53 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 54 · Peer universe by vintage: aggregate fund size and fund count

- **slug**：`ca_apx_universe`（稳定标识，编号会变、slug 不变）
- **位置**：`9.6`，版式 `solo`（满宽单图）
- **形状**：`series_stacked`　**出图函数**：`size_and_count()` in `build_s6.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  size_and_count('ca_apx_universe', 'solo', 2.9, 'Aggregate fund size (US$bn)', every=1)
  ```
- **数据源**：
  - `2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx`
  - 定位：「Data」 / 「333 funds」 / 「有披露 Fund Size」 / 「平均基金规模」
- **取数与构成**（本季实际做法，下季照做）：
  - 2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx，sheet "Data"。
  - 筛选口径：PitchBook 检索：Fund Strategy = Direct Lending；Fund Location = Americas > North America。
  - 导出日 2026-08-13，导出人 Xiyang Zhao (Junson Capital)，检索链接 https://my.pitchbook.com/?pcc=1372632-49。
  - 样本 331 只基金 —— 注意 report-spec 写的「333 funds」是数表格行数（表头后 333 行 = 331 只基金 + 1 个空行 + 1 行 PitchBook 版权声明），真实样本数 331，下季不要去凑 333。
  - 所有统计都是从这份导出表直接算的（分位数用线性插值口径）。
  - ⭐ 独立对账：与同事的 CA_snapshot_2026Q3.json 逐项比 36 项（4 个 vintage × 3 个指标 × n/中位/IQR），0 项不一致 —— 两边各自从同一份 xlsx 算出同样的结果。
  - （同事快照里 q1/q3 的命名是 PE 惯例，q1 = 表现更好那端，和统计学反着，对账按 IQR 比。
  - ） 本图 = 每个 vintage 的基金只数与规模合计。
  - ⚠ 规模合计只加总「有披露 Fund Size」的基金，各 vintage 的披露率不同（存在 n_with_size 字段里），所以规模条和只数线不是同一个分母，正文不许拿两者相除当「平均基金规模」。
  - 横轴用连续年份 2005–2026（这段每年都有基金，是连续的）。
  - 2005 年以前只有 3 个 vintage、共 3 只基金（1997, 2000, 2002，各 1 只），不画进轴里 —— 之前把「有基金的 vintage」直接排一排，1997→2000 的间隔和 2023→2024 一样宽，会被读成连续年份，属于失真。
- 🕐 **末期与新鲜度**（下季更新前先对这三条）：
  - 图画到：`2026`　｜　该口径源上限：`2026`
  - 本季文件夹里同主题最新：`2026`（同口径）—— PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx（导出日 2026-08-13，全文件夹最新的一份料）
  - 下季去哪儿看源末期：同上（这张不设 n≥5 门槛，取导出里最后一个 vintage）
- **脚注（本季实际印出的）**：
  ```
  Note: Peer universe by vintage year from 2013 onward — number of funds (right axis) and aggregate fund size for those funds that disclose size (left axis). Disclosure rates differ by vintage, so the two series do not share a denominator and their ratio is not an average fund size. Screen exported 2026-08-13; 331 North American direct lending drawdown funds across vintages from 1997, of which the 2013 and later vintages are shown here. Source: PitchBook.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 54 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 55 · Manager consistency: average PitchBook quartile vs median net IRR (≥4 ranked funds)

- **slug**：`ca_apx_mgr_consistency`（稳定标识，编号会变、slug 不变）
- **位置**：`9.6`，版式 `solo`（满宽单图）
- **形状**：`scatter_bubble`　**出图函数**：`bubbles()` in `build_s6.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  bubbles('ca_apx_mgr_consistency', 'solo', 3.2,
  'Average PitchBook fund quartile (1 = top)
  ```
- **数据源**：
  - `2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx`
  - 定位：「Data」 / 「至少有 4 只基金拿到 PitchBook 四分位评级」 / 「相对一个外部北美同业基准的位置」 / 「同组内排名」
- **取数与构成**（本季实际做法，下季照做）：
  - 2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx，sheet "Data"。
  - PitchBook 检索：Fund Strategy = Direct Lending；Fund Location = Americas > North America。
  - 导出日 2026-08-13，导出人 Xiyang Zhao (Junson Capital)，检索链接 https://my.pitchbook.com/?pcc=1372632-49（导出日 2026-08-13，331 只基金）。
  - 按 Investor 字段分组，只保留「至少有 4 只基金拿到 PitchBook 四分位评级」的管理人，共 29 家。
  - x = 平均四分位（1 = 最好，越靠左越强，作图时 x 轴反向）；y = 该管理人全部基金的 IRR 中位数；气泡大小 = 有评级的基金只数。
  - PitchBook 四分位取值分布：1 档 68 只 / 2 档 98 只 / 3 档 85 只 / 4 档 67 只（共 318 只有评级）。
  - ⚠⚠ 口径披露（Alex 2026-08-21 决定：筛选不改，但必须写清）：这份 PitchBook 筛选限定 Fund Location = Americas › North America，共 331 只基金。
  - Junson 自己的三只基金 —— PAG BRS III（香港）、HSBC RCF（卢森堡 RAIF）、Guggenheim PDF IV —— 在这 331 只里一只都没有命中（各按 Investor 与 Funds 两列做正则检索，命中数 0/0/0）。
  - 所以 §9 的分位数是「相对一个外部北美同业基准的位置」，不是「同组内排名」，PAG 以亚洲为主、HSBC 以欧洲为主，存在地域错配。
  - §9 开头段和附录方法论段都必须显式写出这一点，不许让读者误以为我们在池内。
  - 因此本图无法叠加 Junson 自己的基金（report-spec 里写的「Junson funds highlighted」本季做不到），这一点要在图注里说明，不能留白让人以为忘了画。
  - 图上标注 10 家代表性管理人（平均四分位最好的 3 家、IRR 中位最高的 3 家、有评级基金最多的 3 家、平均四分位最差的 2 家，去重后）—— 不标全部 29 家，否则文字会糊成一片；其余点保持无标注，账本里有全表。
  - 另外要在正文里说清：x 轴（PitchBook 四分位）本身就是按业绩定的，所以「四分位越好、IRR 中位越高」是同义反复，这张图的看点是**离散度**（同一四分位档里 IRR 中位差多少）和**气泡大小**（谁的样本厚），不是那条正相关。
  - 。
  - ⚠ 第一版只点名了 10 家、没有叠自家基金、也没有气泡大小图例；基线三样都有。
  - 现全部 29 家点名，并按 overlay_note 的口径叠上 PAG 与 HSBC。
- **overlay_note**：自家基金按「cohort 分位反推的等效 PitchBook 四分位」放在横轴上 —— PAG 的 IRR 分位 92、HSBC 100，都落在第一四分位，故 x=1.0。这是 Junson calculation，不是 PitchBook 给的四分位（我们三只都不在那 331 只池里）。
- **脚注（本季实际印出的）**：
  ```
  Note: Manager consistency across the PitchBook screen — average PitchBook fund quartile (1 = top) against the median net IRR of the manager's funds, for managers with at least four ranked funds. Bubble size is the number of ranked funds. PitchBook assigns quartiles on performance, so the upward slope is definitional; what the chart shows is the spread of median IRR within each quartile band and how many funds each manager's record rests on. Junson's own funds are not constituents of this screen and therefore cannot be overlaid. Source: PitchBook.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 55 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 56 · Net IRR by vintage: median and interquartile range, with Junson funds

- **slug**：`ca_apx_irr_by_vintage`（稳定标识，编号会变、slug 不变）
- **位置**：`9.6`，版式 `pairL`（并排左）
- **形状**：`median_iqr_by_vintage`　**出图函数**：`median_band()` in `build_s6.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  median_band('ca_apx_irr_by_vintage', 'pair', 3.0, 'Net IRR (%)', '{:.1f}%', every=3)
  ```
- **数据源**：
  - `2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx`
  - 定位：「Data」 / 「333 funds」
- **取数与构成**（本季实际做法，下季照做）：
  - 2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx，sheet "Data"。
  - 筛选口径：PitchBook 检索：Fund Strategy = Direct Lending；Fund Location = Americas > North America。
  - 导出日 2026-08-13，导出人 Xiyang Zhao (Junson Capital)，检索链接 https://my.pitchbook.com/?pcc=1372632-49。
  - 样本 331 只基金 —— 注意 report-spec 写的「333 funds」是数表格行数（表头后 333 行 = 331 只基金 + 1 个空行 + 1 行 PitchBook 版权声明），真实样本数 331，下季不要去凑 333。
  - 所有统计都是从这份导出表直接算的（分位数用线性插值口径）。
  - ⭐ 独立对账：与同事的 CA_snapshot_2026Q3.json 逐项比 36 项（4 个 vintage × 3 个指标 × n/中位/IQR），0 项不一致 —— 两边各自从同一份 xlsx 算出同样的结果。
  - （同事快照里 q1/q3 的命名是 PE 惯例，q1 = 表现更好那端，和统计学反着，对账按 IQR 比。
  - ） 本图 = 各 vintage 的 Net IRR (%) 中位数与 P25–P75 带。
  - 只画 2010–2025（每年 n≥5，连续）；每个 vintage 实际用到的样本数存在 n 字段里，画图时必须把 n 标出来或写进 Note —— 2024/2025 的 n 只有 8–11，和 2021 的 32 不是一个可信度。
  - 只画该指标自己 n≥5 的 vintage：2008–2025，共 17 个 —— 注意是按**这个指标的披露只数**筛，不是按 vintage 总只数；例如 2010 年有 5 只基金，但只有 3 只披露 called%，所以 called% 这张图里没有 2010。
  - 每个 vintage 用到的 n 存在 n 字段里，作图时必须标出来：最新两个 vintage 的 n 是 11 和 6，和 2021 那种 30 多只不是一个可信度，正文引用时要带上样本数。
  - 另外：2008 这些 vintage 虽然 n≥5，但被 n<5 的年份（如 2009 只有 3 只）与主段隔开了，等距横轴会把它们画成相邻年份，属于失真，所以只取最长的连续段 2010–2025。
  - 被排除的 vintage 数据在 meta.cohorts 里都有。
  - Junson 点位已叠加：PAG BRS III（2023 年份）与 HSBC RCF（2024 年份）取自各自季报明值；Guggenheim 无可核来源，不叠点，图注要写明。
- **脚注（本季实际印出的）**：
  ```
  Note: Net IRR (%) by vintage year across North American direct lending drawdown funds in the PitchBook screen — median with the interquartile range shown as a band. Only vintages with at least 5 funds disclosing this metric are shown; sample size per vintage is printed below the axis; recent vintages rest on far fewer funds and are still ramping. Screen exported 2026-08-13. Junson's PAG BRS III (2023 vintage) and HSBC RCF (2024 vintage) are overlaid; Guggenheim PDF IV is not shown because its report discloses no return metrics. Junson funds are not constituents of the screen. Guggenheim PDF IV values are computed internally by Junson from the manager’s internal investor reporting (marked †), as its quarterly report discloses no return metrics. Sources: PitchBook; fund quarterly reports.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 56 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 57 · TVPI by vintage: median and interquartile range, with Junson funds

- **slug**：`ca_apx_tvpi_by_vintage`（稳定标识，编号会变、slug 不变）
- **位置**：`9.6`，版式 `pairR`（并排右）
- **形状**：`median_iqr_by_vintage`　**出图函数**：`median_band()` in `build_s6.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  median_band('ca_apx_tvpi_by_vintage', 'pair', 3.0, 'TVPI (x)', '{:.2f}x', every=3)
  ```
- **数据源**：
  - `2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx`
  - 定位：「Data」 / 「333 funds」
- **取数与构成**（本季实际做法，下季照做）：
  - 2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx，sheet "Data"。
  - 筛选口径：PitchBook 检索：Fund Strategy = Direct Lending；Fund Location = Americas > North America。
  - 导出日 2026-08-13，导出人 Xiyang Zhao (Junson Capital)，检索链接 https://my.pitchbook.com/?pcc=1372632-49。
  - 样本 331 只基金 —— 注意 report-spec 写的「333 funds」是数表格行数（表头后 333 行 = 331 只基金 + 1 个空行 + 1 行 PitchBook 版权声明），真实样本数 331，下季不要去凑 333。
  - 所有统计都是从这份导出表直接算的（分位数用线性插值口径）。
  - ⭐ 独立对账：与同事的 CA_snapshot_2026Q3.json 逐项比 36 项（4 个 vintage × 3 个指标 × n/中位/IQR），0 项不一致 —— 两边各自从同一份 xlsx 算出同样的结果。
  - （同事快照里 q1/q3 的命名是 PE 惯例，q1 = 表现更好那端，和统计学反着，对账按 IQR 比。
  - ） 本图 = 各 vintage 的 TVPI (x) 中位数与 P25–P75 带。
  - 只画 2010–2025（每年 n≥5，连续）；每个 vintage 实际用到的样本数存在 n 字段里，画图时必须把 n 标出来或写进 Note —— 2024/2025 的 n 只有 8–11，和 2021 的 32 不是一个可信度。
  - 只画该指标自己 n≥5 的 vintage：2010–2025，共 16 个 —— 注意是按**这个指标的披露只数**筛，不是按 vintage 总只数；例如 2010 年有 5 只基金，但只有 3 只披露 called%，所以 called% 这张图里没有 2010。
  - 每个 vintage 用到的 n 存在 n 字段里，作图时必须标出来：最新两个 vintage 的 n 是 8 和 6，和 2021 那种 30 多只不是一个可信度，正文引用时要带上样本数。
  - Junson 点位已叠加：PAG BRS III（2023 年份）与 HSBC RCF（2024 年份）取自各自季报明值；Guggenheim 无可核来源，不叠点，图注要写明。
- **脚注（本季实际印出的）**：
  ```
  Note: TVPI (x) by vintage year across North American direct lending drawdown funds in the PitchBook screen — median with the interquartile range shown as a band. Only vintages with at least 5 funds disclosing this metric are shown; sample size per vintage is printed below the axis; recent vintages rest on far fewer funds and are still ramping. Screen exported 2026-08-13. Junson's PAG BRS III (2023 vintage) and HSBC RCF (2024 vintage) are overlaid; Guggenheim PDF IV is not shown because its report discloses no return metrics. Junson funds are not constituents of the screen. Guggenheim PDF IV values are computed internally by Junson from the manager’s internal investor reporting (marked †), as its quarterly report discloses no return metrics. Sources: PitchBook; fund quarterly reports.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 57 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

#### 图 58 · Called-down % by vintage: median and interquartile range, with Junson funds

- **slug**：`ca_apx_called_by_vintage`（稳定标识，编号会变、slug 不变）
- **位置**：`9.6`，版式 `solo`（满宽单图）
- **形状**：`median_iqr_by_vintage`　**出图函数**：`median_band()` in `build_s6.py`
- **出图调用**（画布宽与高由此锁死，不许改宽）：
  ```python
  median_band('ca_apx_called_by_vintage', 'solo', 2.9, 'Called down (%)', '{:.0f}%', every=2)
  ```
- **数据源**：
  - `2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx`
  - 定位：「Data」 / 「333 funds」
- **取数与构成**（本季实际做法，下季照做）：
  - 2026Q3/Competitor/PitchBook_Search_Result_Columns_2026_08_13_16_08_16.xlsx，sheet "Data"。
  - 筛选口径：PitchBook 检索：Fund Strategy = Direct Lending；Fund Location = Americas > North America。
  - 导出日 2026-08-13，导出人 Xiyang Zhao (Junson Capital)，检索链接 https://my.pitchbook.com/?pcc=1372632-49。
  - 样本 331 只基金 —— 注意 report-spec 写的「333 funds」是数表格行数（表头后 333 行 = 331 只基金 + 1 个空行 + 1 行 PitchBook 版权声明），真实样本数 331，下季不要去凑 333。
  - 所有统计都是从这份导出表直接算的（分位数用线性插值口径）。
  - ⭐ 独立对账：与同事的 CA_snapshot_2026Q3.json 逐项比 36 项（4 个 vintage × 3 个指标 × n/中位/IQR），0 项不一致 —— 两边各自从同一份 xlsx 算出同样的结果。
  - （同事快照里 q1/q3 的命名是 PE 惯例，q1 = 表现更好那端，和统计学反着，对账按 IQR 比。
  - ） 本图 = 各 vintage 的 Called down (%) 中位数与 P25–P75 带。
  - 只画 2010–2025（每年 n≥5，连续）；每个 vintage 实际用到的样本数存在 n 字段里，画图时必须把 n 标出来或写进 Note —— 2024/2025 的 n 只有 8–11，和 2021 的 32 不是一个可信度。
  - 只画该指标自己 n≥5 的 vintage：2008–2025，共 16 个 —— 注意是按**这个指标的披露只数**筛，不是按 vintage 总只数；例如 2010 年有 5 只基金，但只有 3 只披露 called%，所以 called% 这张图里没有 2010。
  - 每个 vintage 用到的 n 存在 n 字段里，作图时必须标出来：最新两个 vintage 的 n 是 8 和 5，和 2021 那种 30 多只不是一个可信度，正文引用时要带上样本数。
  - 另外：2008 这些 vintage 虽然 n≥5，但被 n<5 的年份（如 2009 只有 3 只）与主段隔开了，等距横轴会把它们画成相邻年份，属于失真，所以只取最长的连续段 2011–2025。
  - 被排除的 vintage 数据在 meta.cohorts 里都有。
  - Junson 点位已叠加：PAG BRS III（2023 年份）与 HSBC RCF（2024 年份）取自各自季报明值；Guggenheim 无可核来源，不叠点，图注要写明。
  - ⚠ called% 口径不同：PitchBook 的 Called Down % 是对基金规模的已缴比例；PAG 用季报的 capital contributions 59%；HSBC 用已缴 8.4m ÷ 基金规模 334.8m = 2.5%（还在建仓）。
  - 三者不是严格同一算法，叠加只作方位参考，正文不许拿差值说事。
- **脚注（本季实际印出的）**：
  ```
  Note: Called down (%) by vintage year across North American direct lending drawdown funds in the PitchBook screen — median with the interquartile range shown as a band. Only vintages with at least 5 funds disclosing this metric are shown; sample size per vintage is printed below the axis; recent vintages rest on far fewer funds and are still ramping. Screen exported 2026-08-13. Junson's PAG BRS III (2023 vintage) and HSBC RCF (2024 vintage) are overlaid; Guggenheim PDF IV is not shown because its report discloses no return metrics. Junson funds are not constituents of the screen. Guggenheim PDF IV is plotted at 50% called (marked †), from Junson’s own investor-level tracking of its $50m commitment; the Guggenheim quarterly report itself discloses no capital-called figures. Sources: PitchBook; fund quarterly reports.
  ```
- **口径对账**：已与上一版成稿 `assets/baseline-<quarter>-EN.docx` 的图 58 并排比过 —— 横轴起止、序列条数、口径、端点值四项。下一季出图后**必须重跑这一步**（见 SKILL.md 铁律五）。

---

