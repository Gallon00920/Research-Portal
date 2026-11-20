# Source map — what feeds what

## Folder convention

```
.../04 Research/Private Credit/<YYYYQn>/
├── Broker/       sell-side research on private credit (PDFs)
├── Competitor/   PitchBook fund screen export (xlsx)
├── Fund/         the three managers' quarterly investor reports (PDFs)
└── Market/       market-wide trackers and data reports (PDF + xlsx)
```

File names change every quarter; identify sources by content, not by exact name.

> ⛔ **同理，slide 号也每季会挪。** 账本里的 `src` 不许只写 "MS tracker slide 28" ——
> 要写 **slide 的标题文字**，页码只做辅助。`pc_review_sheet.py` 会把只靠 slide 号定位的挑出来。 The
lists below are the *recurring* sources seen at baseline (2026Q3) — expect the same
publishers with new titles each quarter, plus occasional new one-off reports (read
those too; they feed Sentiment and Things We Should Know).

## Market/ → Market Size, Returns & RV, Pricing & Term, Credit Fundamentals

| Recurring source | Baseline example | Feeds |
|---|---|---|
| PitchBook annual/interim global private debt report (+ summary xlsx) | `2025-annual-global-private-debt-report.pdf/.xlsx` | AUM by channel (Ex 1), dry powder, fundraising (Ex 3–4) |
| Morgan Stanley Private Credit Tracker (quarterly) | `MS Private Credit 1Q26 tracker.pdf` | US lev-credit map (Ex 2), returns/yields (Ex 8–9), spreads (Ex 10–11), covenants/PIK (Ex 12–13), default provider table (Ex 16), recoveries (Ex 20–21), leverage/ICR (Ex 22–25), BDC nonaccrual/PIK (Ex 26–29), maturity wall |
| MS Private Credit tracker | `MS Private Credit 1Q26 tracker.pdf` | ⚠ Broker 目录下的 `Private Credit Tracker 1Q26 – Softening Fundamentals.pdf` 与它**是同一份文件**（md5 都是 1b4730b8f1fc7cf1607f5dc73893f6e9）。别当两个来源重复计，也别以为漏了一份研报 |
| S&P Global Direct Lending deck (quarterly) | `2Q26 S&P Direct Lending.pdf` | S&P default measures (Ex 14–15), MM CLO issuance & AAA spread (Ex 7) |
| LCD / PitchBook US private credit & middle market quarterly wrap (PDF + xlsx) | `q2-2026-us-private-credit-...wrap.pdf/.xlsx` | quarterly DL volume & deal count, LBO share (Ex 5–6), LCD survey pricing, spread corroboration |

Note the MS tracker may also appear in Broker/ (same file, either place is fine).

## Broker/ → Sentiment (Exhibit 30 columns), plus color everywhere

Baseline set: Morgan Stanley (tracker + "Connecting the Dots" + "Pressures Contained
Not Resolved"), J.P. Morgan (insurance-lens PC), Goldman Sachs ("Macro Credit Views"),
Barclays (BDC 2Q themes), UBS (public & private credit outlook — file may have an
opaque name like `ued42349.pdf`; identify by opening it).

Each broker report gets one Exhibit-30 column: View / Key points / QoQ change. Keep a
private note of each house's prior-quarter stance (from the prior issue's Exhibit 30)
to write the QoQ row. Broker forecasts (e.g. default forecasts) also feed body sections.

## Fund/ → Fund Update section

| Manager | Baseline example | Watch for |
|---|---|---|
| PAG BRS Fund III (SRT) | `PAG BRS Fund III L.P. - 2026 Q1 Quarterly Newsletter.pdf` | IRR/MOIC/DPI table, 17-position schedule, realised deals, composition splits |
| Guggenheim PDF IV (US DL) | `Guggenheim PDF IV Report - Q1 2026.pdf` | closed deals with pricing/leverage/LTV, GICS mix, sponsored split, monitor list; no fund-level IRR disclosed |
| Guggenheim 回报指标（IRR/TVPI/DPI/called%） | ⛔ **不在文件夹里，也不许读 AID master —— 发对话框请用户手动输入**（有人值守时照硬要求十八发对话框问；问了没给、或无人值守（如研究面板的 AI 生成）就按「缺料」删掉这些格与叠加点）。哪几张图有坑、每处问什么，照账本 `series_bank.gug_internal_returns.fill_checklist` 逐项过 | §9.1–9.4 每季问；§9.6 附录年度刷新才问。口径要问清：YTD 年化 XIRR 还是成立以来 ITD |
| HSBC RCF Partnership Fund | `HSBC RCF Partnership Fund ... Investor Report Final.pdf` | TVPI/DPI/IRR, portfolio table with margins & est. ROIC, watchlist RAG, pipeline projects |

Keep the **prior quarter's** fund reports (or the prior issue's tables) at hand — the
composition QoQ tables (Ex 36/41/45) and KPI-vs-prior-Q tables (Ex 37) need both
quarters. Fund reports lag: the Q3 issue uses Q1 fund reports; use the latest available
and state the as-of date prominently.

## Competitor/ → Competitor Analysis section

`PitchBook_Search_Result_Columns_<date>.xlsx` — re-exported screen of North America
direct lending drawdown funds. Recompute from raw columns each quarter: cohort medians
and IQRs by vintage (net IRR, TVPI, DPI, called-down %), each Junson fund's percentile
in its vintage cohort, the named-comparator rows (KKR/Ares/Apollo/TPG Twin
Brook/Golub/HarbourVest/Oaktree latest flagships), the appendix universe stats, and the
manager-consistency chart (managers with ≥4 ranked funds: average PB quartile vs median
net IRR). Record the export date in the methodology paragraph and snapshot JSON.

## Web research (run automatically every quarter)

Slots the folder usually cannot fill — cite publisher + date in the ledger and mark
"web research" in exhibit notes:

1. **Related news bullets (§6.2)** — search the quarter's private credit news:
   non-traded BDC / interval fund redemption & gating stats (BCRED, Apollo ADS,
   Cliffwater CCLFX, HLEND, GCRED...), the quarter's biggest defaults/restructurings and
   debt-for-control deals, landmark/novel financings, secondaries volumes and pricing,
   regulatory moves (valuation transparency, 401(k)/retail access, Basel/SRT rules).
2. **Public market comparators for charts** — ICE BofA US HY YTW series (Ex 9), Single
   B BSL spread level if fresher than the folder reports, base-rate context.
3. **Broker view updates** — anything the covered houses published after the folder
   reports that changes their stance (only if reliably sourced).
4. **Fund-manager news** — fundraising closes, new vehicles, personnel or strategy news
   for PAG / Guggenheim / HSBC AM and the named competitor managers.
5. **Post-quarter events** — anything material between quarter-end and the production
   date belongs in Sentiment/Things We Should Know with an explicit date.

Prefer primary or top-tier sources (company releases, S&P/Fitch/KBRA/PitchBook
publications, FT/Bloomberg/Reuters/WSJ). If a web fact can't be confirmed by a solid
source, leave it out.

## Missing-source behaviour

If a recurring source is absent this quarter, the exhibits that depend on it are skipped and
dropped from the report, with every sentence, table row and Summary item that cites them; the
remaining exhibits renumber (`pc_intake.py --apply` records them in `meta.skipped`). No
"[Not updated]" note, no last-quarter exhibit, no question to the user. List the missing
sources and the dropped exhibits in the delivery message. Never fabricate or extrapolate a
missing quarter. See "缺料" at the top of SKILL.md.
