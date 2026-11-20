# 数据纪律（红线）

### 5. 数据纪律（红线）


0. **上一版报告只能用来对答案，绝不能当数据源。** `OTF_<季度>_OTF update_v1.docx`、`OTF_<季度>_Fundamental_Analysis_Report.docx` 这类**上一版成稿**里的图和表都是加工结果，属二手数据。规则：
   - **不许**把上一版报告里的数字写进 `series.json`，**连"先填上占位、以后再核"都不许** —— 占位一旦落盘就没人再回去核了。
   - 缺数就让脚本**报错退出**，不要塞占位值让它跑通。
   - `selfcheck.py` 里有硬检查：扫全部 `src`，命中 `_v1|\.docx|报告表|上一版报告` 直接 fail；`src` 必须含**文件名**（`.pdf` / SEC accession 号 / 研报名），写「same」「each period's own filing」不合格。**不要求页码**（页码每季会挪，见 §3.3）。
   - 上一版报告的正确用途只有两个：**跑完之后逐张对数值**，以及**抄样式**（配色、脚注写法、表格框线色号）。
   > 实战教训：本 prompt 的作者自己就在 T1 上犯过这个错 —— 图省事把 v1 报告表格里的十行数当占位写进脚本，回 10-Q 一核发现 v1 那张表的 `Memo: senior secured debt` 是错的（81.5%/81.4% 应为 81.2%/81.1%，把 specialty finance debt 那 0.3pp 算进了 senior secured，而同一张表第 3 行已经算过一次）。**二手数据会把上游的错原样传下来。**

1. **图里每一个数字都必须能在文件夹的文件里指出落点**（哪份 PDF、哪张表 / 哪一段）。做完每张图列一张「数字 → 落点」对照，自己过一遍。
2. **不确定就不放。** 缺一期就断线留空（`np.nan`），**绝不插值、绝不线性外推、绝不用"上季数近似"**。图 6 的 fair-value 序列前三期就是这么留空的。
3. **从研报里读出来的点，标注 `digitised from the source chart`**；能直接读到披露数值的点（如 Tracker 正文写的 2.8%、6.4%）优先用披露值。
4. **交叉验证**：10-Q 与 earnings deck 都披露的口径（first-lien 占比、组合收益率、非应计、PIK、NAV/股）两边对一遍，不一致就以 **10-Q** 为准并在脚注写明差异。
5. **环比靠两季各自的 filing**，不靠单份 filing 的对比列（见 §2.5）。
6. 单位/口径写清楚：`% of total investments at fair value` vs `at amortized cost`、`% of total investment income` vs `% of net investment income` —— 这两组一错整张图的结论就反了。
7. 图 8–9 的股价用**未调整收盘价**（unadjusted for dividends），并在脚注写明。
8. 出图后**重新读一遍自己画的 PNG**（把图当图片读进来看），确认没有标签重叠、没有文字出界、没有数字错位。

---
