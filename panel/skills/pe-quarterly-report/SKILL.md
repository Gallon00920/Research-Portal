---
name: "pe-quarterly-report"
description: "Build Junson AID's quarterly US Private Equity report set (full report + 2-page summary, English and Chinese) from the 04 Research\\PE quarter folder. Use for PE quarterly / PE report / GPS V update / PE季报 requests."
---

# Junson PE Quarterly Report (US Private Equity + GP Stakes V)

Turn one quarter's folder of PitchBook packs, GP letters and competitor data into the
"US Private Equity Quarterly Report" set. Every new issue must look like a sibling of the
2026Q3 issue: same chapter framework, same 47 exhibits, same formatting, fresh data -
less whatever this quarter's inputs cannot support (see "Missing inputs").

## Missing inputs: skip the part, drop it from the report

This rule replaces every older instruction in this skill about a missing input (asking the
user to add the file, keeping the section with "latest period unchanged", carrying the last
point, "[Not updated]" notes). A missing input is normal, not an error.

1. **Inventory first.** Before extracting, mark each input of the table under "Inputs and what
   they feed" as found or missing. An input is missing when no file of this period matches it;
   a file of an earlier period never stands in for it.
2. **Do not ask, do not wait, do not carry over.** Skip everything that depends only on the
   missing input and build the rest.
3. **Drop, don't flag.** A skipped exhibit is left out of the report: no empty frame, no "not
   updated" note, no "input missing" line in the text. A subsection whose exhibits and argument
   all come from missing inputs is dropped; a section whose subsections are all dropped is
   dropped. Every other place that relies on the dropped part loses it too: the overview
   paragraph, Things We Should Know, the implications, and the Summary's tables, charts,
   bullets and Watch List rows. A sentence that mixes available and missing evidence keeps
   only what the available inputs support.
4. **Renumber.** The remaining exhibits are numbered 1..N in document order and the sections
   stay consecutive (no gap where one was dropped). The Chinese versions drop exactly the same
   parts.
5. **Ledger and checks.** Record each skipped exhibit in the ledger `meta.skipped` as
   `{"ex": "ex40", "missing": "<the input>", "rq": "<RQ>"}`. A skipped exhibit gets no new
   point; its history stays in `series.json` untouched for later quarters. The enforcement
   checks expect exhibits ex01..exN, so for this quarter: write a variant config
   `pe_config_<RQ>.json` next to `pe_config.json` (a copy with `exhibit_count` = N, the keys of
   `required_checks` renumbered, and a `_variant_of` note naming the skipped exhibits and the
   missing inputs; `pe_config.json` itself is never changed), work on a copy of the ledger in
   `_charts\<RQ>_run\` whose kept exhibits are renumbered ex01..exN and each carry
   `template_ex` (their number in the full 47-exhibit template), and point steps
   1-8 at the variant config and that copy. On delivery, write the new points back into
   `series.json` under their `template_ex` keys; a later quarter maps by `template_ex`, never
   by key.
6. **Say what was skipped** in the delivery message (in an unattended run, in the "Notes for
   the reviewer" the run asks for): each missing input and the exhibits and sections dropped
   because of it.
7. **Stop only when nothing is left.** If no market pack and no GPS V letter is present there is no report to write: say which inputs are missing and stop.

| Missing input | Dropped this quarter |
|---|---|
| `Market\` US PE Breakdown pack | Ex 1-6, 19-21, 24-25, 27, 29, 31 and Ex 11; 2.1, 2.2, the market parts of 4.1, 4.2 and 5.1; the Summary charts built from Ex 1, 19, 27 |
| `Market\` PE Middle Market pack | Ex 9-10, 13, 15-18, 22-23, 28, 30, 32 and Ex 11; 2.4, 3.2, 5.2 and the middle-market parts of 3.1, 4.1 and 5.1 (Ex 14 stays when the M&A pack has it) |
| `Market\` Global M&A pack | Ex 7-8, 14 and Ex 11; 2.3 |
| `Market\` PE Outlook pack | Ex 26 and the outlook calls |
| `Fund\` latest GPS V letter | Section 8 (Ex 33-39), Ex 42, the GPS V side of Section 9 (Ex 41, 43-46), the fund paragraph of 7.4, the GPS V row of the Summary's "Our Position" and the portfolio bullets that cite fund numbers |
| `Fund\` prior GPS V letter only | The prior-quarter side: the prior half of Ex 37 and the QoQ column of Ex 39; the latest quarter stays |
| `Competitor\` HPC report | 9.2 and Ex 41; the HPC row of "Our Position" |
| `Competitor\` PitchBook fund screen | Ex 40, 43-47; 9.1, 9.3-9.5 |
| Both competitor files | The whole Competitor Analysis section (Ex 40-47) |
| `Broker\` | The Sentiment section |
| Latest Junson Private Credit Quarterly | Ex 12 and the private credit figures in 7.3 (7.3 stays, written from this report) |

## Running from attached files (Claude API, the AID research panel)

When the skill runs without the research folder (the sources are attached to the request or
uploaded into the container, as the research panel's "Generate with AI" does, and
`04 Research\PE`, `_charts\` and the pipeline scripts cannot be reached):

- Classify every attached file by its content (cover page, title, report date, sheet names)
  against the input table; file names may be shortened, and archives arrive already unpacked.
  Inputs not among the files are missing: apply "Missing inputs" above.
- There is no ledger history: build each exhibit from the attached files alone (PitchBook
  packs, letters and decks carry their own history columns). An exhibit that needs history
  the files do not hold is skipped like a missing input.
- The enforcement scripts are not there: do not stop because `enforce.py` or `selftest.py` is
  absent. Apply their rules by hand instead: every number traced to an attached file or a
  cited web source, charts legible at insertion width with no overlapping text, identities
  that must hold, exhibits numbered 1..N, EN/CN parity.
- Nothing is written back to any folder. Produce the documents where the run's instructions
  say (for example `/tmp/outputs/`) with the names they give.
- The sign-off gate follows the run's instructions: when they say no human is present, check
  the exhibits and numbers yourself, carry on, and list what you would have asked in the
  notes the run asks for.

## Deliverables and where they go

PE root (sources are read from its `input\` subfolder, reports are written to its `output\` subfolder; in the enforce commands `<quarter_folder>` = `input\<RQ>` and `<out_dir>` = `output`):
`C:\Users\GallonXu(Intern)\Junson Capital\Alternative Investment Division - General\04 Research\PE`

| # | File (written to `PE\output\`) | What it is |
|---|---|---|
| 1 | `Junson_PE_Report_<RQ>_EN_v<n>.docx` | Full report, English (master) |
| 2 | `Junson_PE_Report_<RQ>_CN_v<n>.docx` | Full report, Chinese (translation of the signed-off English) |
| 3 | `Junson_PE_<RQ>_Summary_EN.docx` | Summary, English, max 2 pages |
| 4 | `Junson_PE_<RQ>_Summary_CN.docx` | Summary, Chinese, max 2 pages |

`<n>` starts at 1 and increments on every re-issue; never overwrite an existing file in `output\`.

```
04 Research\PE\
├── _charts\                      shared across quarters, exactly one, never re-created
│   ├── series.json               the ledger - appended in place every quarter
│   ├── comp_series.json          competitor percentile history (append only)
│   └── pipeline\                 chart / check / build scripts, written once then frozen
├── input\<RQ>\                   the quarter's source folder (what the user points at)
│   ├── Market\                   PitchBook report zips (pdf + summary xlsx)
│   ├── Fund\                     Blue Owl GP Stakes V quarterly investor letters
│   ├── Competitor\               HPC quarterly report; PitchBook_Search_Result_Columns_*.xlsx
│   ├── Broker\                   optional - sell-side PE research, if any
│   └── _charts_snapshot\         this quarter's audit trail (PNGs zip, signed ledger copy,
│                                 APPROVED_<RQ>.json, REVIEW_<RQ>.md, sources_ledger_<RQ>.md)
└── output\                       the four deliverables; issued reports of earlier quarters sit in
                                  output\<quarter>\ (layout and tone reference only, never data)
```

## Enforced by code (read this first)

The rules in this skill are checked by scripts kept in `04 Research\PE\_charts\pipeline\`.
Stage that folder with the ledger at the start of every run and read `RUNBOOK.md` there.
A step is finished only when its command exits 0. Where this section and a later section
differ, this section wins.

| # | When | Command | Blocks |
|---|---|---|---|
| 0 | Start | `python3 selftest.py` | Guards that no longer fire on planted faults |
| 1 | Meta set | `python3 enforce.py stale pe_config.json <ledger_dir> --run-date <today>` | Wrong report quarter; quarters hard-coded in frozen scripts; missing meta |
| 2 | After extraction | `python3 enforce.py ledger pe_config.json <ledger_dir>` | Missing exhibits or fields; issued report as a source; dropped latest point; unfrozen axis; open gaps |
| 3 | After extraction | `python3 enforce.py srcaudit pe_config.json <ledger_dir> <quarter_folder>` | Source file not in the quarter folder; web figure without a URL |
| 4 | After charts | `python3 enforce.py charts pe_config.json <ledger_dir> <charts_dir>` | Missing chart; canvas not at insertion width; overlapping, clipped, rotated or non-English chart text |
| 5 | Before the gate | `python3 review_sheet.py <ledger_dir>/series.json <ledger_dir>/comp_series.json <ledger_dir>/REVIEW_<RQ>.md --strict` | Identities that do not hold |
| 6 | Gate | `python3 enforce.py sign pe_config.json <ledger_dir> <charts_dir> <quarter_folder> --by "<the user's own words>"` | Signing without the user's words or while steps 2-4 fail |
| 7 | Before any text | `python3 enforce.py check pe_config.json <ledger_dir> <charts_dir>` | Text on an unsigned or changed ledger or chart set |
| 8 | Four files built | `python3 enforce.py post pe_config.json <ledger_dir> <charts_dir> <out_dir>` | Wrong names or quarter; EN/CN number mismatch; numbers not in the ledger; exhibits out of order; wrong page, margins or image widths; placeholders; summary over 2 pages |

`run_phase1.sh` runs steps 0-5 in order and stops at the first failure.

Hard rules about the scripts:

- Never edit `enforce.py`, `guards.py`, `pe_config.json` or a frozen script to make a check
  pass, never pass a flag that skips a check, and never replace a failing command with a
  manual check. If a rule looks wrong for this quarter, stop and ask the user.
- `--rq-reason` (step 1) and `--by` (step 6) carry the user's own words. Never invent them.
- If `_charts\pipeline\enforce.py` is missing or `selftest.py` fails, stop and tell the user.
  Do not rebuild the kit from memory.
- Values read off a letter's charts go into `readings_<letter quarter>.json`; tracked-fund
  constants (vintage, final close) go into `funds.json`; figures taken from source text go
  into `extra_<RQ>.json` with the file and passage. None of these may be typed into a script.
- The first-investment dates of GPS V's partners are printed on the letter's partner pages
  as `At Tx. (Mon-YY)`. Read them there before stating a vintage or fund age.
- The text for a quarter is built by `content_<RQ>.py`, written fresh each quarter (no prose
  carried over; `content_2026Q3.py` shows the structure only). It must run step 7 itself
  before writing anything.
- Any change to the ledger or a chart after step 6 voids the sign-off: re-run steps 2-5,
  show the user, sign again.
- After delivery write back the ledger, the readings / funds / extra files, the sign-off
  file and any new script, and list the folder to confirm they are there.

## Rules that override everything else

1. **Nothing is copied from a previous report.** Earlier issues (`Junson_PE_Report_*`,
   `Junson_PE_*_Summary_*`) are the truth for layout and tone only. They are never a data
   source, not even as a temporary placeholder. Allowed sources, in order: (a) files in
   `input\<RQ>\`, (b) web research with publisher + date + full URL, (c) asking the user. If none
   of the three yields the number, leave the slot empty with an explicit gap note.
2. **Ledger first, append only.** `exhibit = frozen style x a slice of series.json`. Each
   quarter appends the new period(s); historical points are never recomputed or deleted.
   Exception: PitchBook restates history in every pack - see "Restatements" below.
3. **Every number carries a `src`** naming the file and the sheet / table / page actually
   opened. Write `src` only for a location that was really checked. Marking a carried-over
   number as "from this quarter's folder" is fabrication, not a typo.
4. **Hard gate between charts and prose.** No valid sign-off, no prose - also when running
   unattended or on a schedule. Stop at the gate and leave the review sheet for the user.
5. **Prose reads numbers from the ledger.** Any figure that appears on an exhibit is read
   from `series.json`, never re-extracted for the text.
6. **English is the master; Chinese is a translation of the signed-off English.** Same
   numbers, same exhibits, same order. Charts stay in English in both versions (the same
   PNG files are inserted); captions, notes, tables and body text are translated.
7. **Quarters are never hard-coded.** Every period label derives from the ledger `meta`.
8. **Missing or thin data is drawn as missing or thin** - gap, hollow marker, `n=` in the
   note. Never interpolate, never substitute a neighbouring period.

## Which quarter is which

| Label | Meaning | How it is set |
|---|---|---|
| `RQ` | Report quarter = when the report is written | Calendar quarter of the run date (run in Nov 2026 -> `2026Q4`). Confirm with the user if the folder name differs |
| `market_cq` / `market_pq` | Latest quarter in the US PE Breakdown and Global M&A packs | Read from the pack itself; normally RQ-1 |
| `mm_cq` | Latest quarter in the PE Middle Market pack | Normally one quarter behind `market_cq` |
| `perf_asof` | As-of date of rolling IRR and dry powder | Lags about three quarters |
| `fund_cq` / `fund_pq` | Period of the latest and prior GPS V letters | Read the report date on each letter; normally RQ-2 |
| `comp_cq` | Period of the latest competitor (HPC) report | Usually one quarter behind `fund_cq` |
| `screen_date` | PitchBook fund-screen export date | From the xlsx file-name timestamp `_YYYY_MM_DD_` |

`RQ` appears in exactly three places: file names, the cover title, the page header.
Everywhere else (text, axis labels, captions, notes, table column heads) uses the data
quarter of the layer concerned. Four different quarters in one report is normal. Each note
states its own as-of date.

## Inputs and what they feed

| Folder | File pattern | Feeds |
|---|---|---|
| `Market\` | `q*_us_pe_breakdown_*.zip` | Ex 1-6, 19-21, 24-25, 27, 29, 31; deals-to-exits; megaexits; fundraising concentration |
| `Market\` | `q*_us_pe_middle_market_report_*.zip` | Ex 9-10, 13, 15-18, 22-23, 28, 30, 32 |
| `Market\` | `q*_global_m_a_report_*.zip` | Ex 7-8, 14, 11 (top layers) |
| `Market\` | `*us_private_equity_outlook*.zip` (semi-annual) | Ex 24-26, inventory, GP-led secondaries, outlook calls |
| `Fund\` | Blue Owl GP Stakes V quarterly letter - latest and prior | Section 8, Ex 33-39, 42 |
| `Competitor\` | HPC GP Stakes quarterly investor report | Section 9.2, Ex 41 |
| `Competitor\` | `PitchBook_Search_Result_Columns_*.xlsx` | Section 9, Ex 40, 43-47 |

Each PitchBook zip holds a PDF and a `*-summary-xls.xlsx`. **Take numbers from the xlsx**
(one sheet per chart: `Deal activity`, `Add-on activity`, `Median deal size`,
`Software deal activity`, `Deals by sector`, `Secondary buyout activity`, `Exit activity`,
`Exits by type`, `Average & median exit size`, `Deals vs. exits`, `Holding period trend`,
`Current PE company inventory`, `Fundraising activity`, `Median and average fund size`,
`Fundraising step ups`, `MM buyout multiples`, `M&A multiples by size`,
`Rolling 1-year IRR chart`, `Capital overhang`, `Deal activity by quarter (NA)`,
`M&A deals by type`, `GP led secondaries`, ...). Sheet names shift between editions, so
match by name, and when no sheet matches list all sheet names and search the PDF before
concluding the series is gone. Use the PDF for narrative, as-of dates and anything only
charted there; read charted-only points off the chart and say so in the note.

Take files by wildcard, never by full name (names carry edition suffixes and timestamps).
Zero matches means the input is missing ("Missing inputs" above). Several matches: take the
latest edition by its own report date. Never fall back to another quarter's folder.

**If an input is missing** (no new GPS V letter, no competitor report, no Outlook pack),
skip and drop what depends on it: see "Missing inputs" at the top.

### Working with the folder

- The folder is OneDrive-synced; many files are cloud-only. Reading them from the shell on
  the user's computer fails with `Input/output error` or `Invalid argument`. Stage the files
  into the working environment first (staging downloads them), then work on the staged copies.
- Build charts and documents in the working environment (chart PNGs must be opened and
  looked at), then write the deliverables, the ledger and the snapshot back to the folder.
- Before each run, read `_charts\series.json` and `_charts\pipeline\` back from the folder.
  If they do not exist, this is a first build (see below).

## Phase one - numbers and exhibits

1. **Set the run parameters.** Determine `RQ` and every data quarter above; write them to
   `meta`. Check that nothing in `meta` or in any script still names last quarter.
2. **Inventory the folder** recursively and stage it. Unzip each PitchBook pack into its own
   empty directory. List what was found against the input table and report gaps before
   extracting anything.
3. **Extract into the ledger**, exhibit by exhibit, following the inventory below. For each
   exhibit store: `title_en`, `kind`, `size` (full / half), `periods`, `series`, `unit`,
   `asof`, `src` (exhibit level, with point-level overrides only where they differ),
   `note_en`, frozen `ylim` / `ytick` (and `rhs_ylim` / `rhs_ytick`), `legend_loc`, and
   `aux` for every Junson calculation with its formula and inputs.
4. **Junson calculations** - compute in code, store inputs and result in `aux`:
   - Buyout/LBO share of global M&A = buyout value / (buyout + corporate M&A value)
   - Runway (years) = total dry powder / same-calendar-year total deal value
   - Deals-to-exits ratio; QoQ and YoY changes; sector shares of YTD deal value
   - Nesting layers (global M&A > NA M&A > US PE deal value > US PE buyout > middle market);
     middle market = buyout value x MM share
   - GP holding value shares by manager; valuation bridge check
     (opening + upsize - realized + unrealized change = closing, per manager and in total)
   - Competitor percentiles: share of the reporting cohort strictly below the subject, with
     the subject excluded; record cohort `n` per metric
   - Effective vintage = year of first investment (PitchBook convention); fund age from it
5. **Competitor screen.** Parse the PitchBook export from the header row `Fund ID`; drop the
   blank row and the copyright row; count funds, funds with a vintage, funds reporting
   performance. Append this quarter's percentile point for each tracked fund to
   `comp_series.json`. GPS V and HPC rows come from manager reporting, not from PitchBook.
6. **Build the charts** with the frozen style, then run the mechanical checks: all chart
   text English; no overlapping text boxes; no missing last point without a recorded reason;
   y-axes taken from the ledger, not autoscaled.
7. **Look at every PNG yourself.** Open each image. Labels touching, a legend sitting on
   data, a value label on a line - redo that chart. Do not hand the user a chart you have
   not looked at.
8. **Write `REVIEW_<RQ>.md`**: (a) identity checks - shares sum to 100%, bridge reconciles,
   TVPI = DPI + RVPI where both are reported, nesting layers decrease monotonically,
   percentile inputs match cohort `n`; (b) one row per new number: exhibit, series, prior,
   current, change, `src`. A failed identity blocks the gate - fix the number first.
9. **Gate.** Give the user the PNGs and the review sheet, ask them to check every chart and
   every row, and stop. On their confirmation write `APPROVED_<RQ>.json` holding the sha256
   of `series.json`, `comp_series.json` and every PNG. Any change after signing voids it:
   rebuild, re-issue the review sheet, sign again. The gate may span sessions - phase two
   can start in a new session from the ledger, the PNGs and the sign-off file.

### Restatements

PitchBook revises history every edition. For annual and quarterly PitchBook series,
replace the full series with the current pack's values, and for each period whose value
moved by more than 2% log `{period, old, new, pack}` under the exhibit's `_restated`.
The review sheet lists these. Prior-quarter comparisons in the text use the current pack's
restated prior value and say "restated" where the difference matters. Fund, competitor and
percentile series are never restated - append only.

### First build (no ledger in `_charts\`)

Start with Ex 1 (xlsx extraction) and Ex 38 (letter table extraction) only; compare against
the latest issued report digit by digit; then run the rest. Prior-period fund and
competitor points are backfilled from the earlier quarter folders' own source files
(for example `input\2026Q3\Fund\`, `input\2026Q3\Competitor\`), never from the issued report. The
pipeline already exists in `_charts\pipeline\` (built and tested on the 2026Q3 folder):
`pb.py`, `extract.py`, `extract_fund.py`, `extract_comp.py`, `style.py`, `build_charts.py`,
`review_sheet.py`, `review_pack.py`, `docx_render.py`, `summary_charts.py`, plus the
enforcement kit (`enforce.py`, `guards.py`, `selftest.py`, `pe_config.json`). Use these;
do not write replacements. The scripts listed under `frozen_scripts` in `pe_config.json`
are frozen: change one only when a source file's layout has changed, say so to the user,
and re-run `selftest.py` and steps 1-5 afterwards.

### Exhibit inventory (47)

F = full width, H = half width (two side by side). Section numbers follow the report.

| Ex | Title | Kind / size | Source |
|---|---|---|---|
| 1 | US PE deal value and count by quarter | bars + line (count, rhs), F | Breakdown `Deal activity` |
| 2 | Add-on share of US buyout count | line, H | Breakdown `Add-on activity` |
| 3 | Median and average PE deal size (US$m) | two lines, H | Breakdown `Median deal size` |
| 4 | US software deal value and count by quarter | bars + line, F | Breakdown `Software deal activity` |
| 5 | Share of YTD deal value by sector | horizontal bars, H | Breakdown `Deals by sector`; Junson calc |
| 6 | Secondary buyouts, share of buyout value | line, H | Breakdown `Secondary buyout activity` |
| 7 | North America M&A deal value and count by quarter | bars + line, H | M&A `Deal activity by quarter (NA)` |
| 8 | Buyout/LBO share of global M&A value | line, H | M&A `M&A deals by type`; Junson calc |
| 9 | US PE middle-market deal activity | bars + line, H | MM `Deal activity` |
| 10 | MM share of all US PE buyout value | line, H | MM report |
| 11 | How the volume measures nest | nested-bar diagram, F | Junson calc from Ex 1, 7, 8, 9 |
| 12 | Where private credit connects | table, 3 columns | Latest Junson Private Credit Quarterly; this report |
| 13 | MM buyout median EV/EBITDA (NA & Europe) | bars, H | MM `MM buyout multiples` |
| 14 | M&A EV/EBITDA by deal size | two lines, H | MM / M&A `M&A multiples by size` |
| 15 | Median US PE MM buyout EV/EBITDA | bars, H | MM `MM buyout multiples` |
| 16 | Median US PE MM buyout EV/revenue | bars, H | MM `MM buyout multiples` |
| 17 | US rolling one-year horizon IRR by segment | three lines, last values labelled, F | MM `Rolling 1-year IRR chart` |
| 18 | Europe rolling one-year horizon IRR by segment | three lines, F | Same sheet if present, else PitchBook European PE pack; record which |
| 19 | US PE exit value and count by quarter | bars + line, F | Breakdown `Exit activity` |
| 20 | Exit value by route (quarterly) | stacked bars, H | Breakdown `Exits by type` |
| 21 | Median and average exit size (US$m) | two lines, H | Breakdown `Average & median exit size` |
| 22 | US PE MM exit value and count by quarter | bars + line, H | MM `Exit activity` |
| 23 | US PE MM exit value by route | stacked bars, H | MM `Exit flow by type` |
| 24 | Median PE holding period (years) | line, H | Breakdown `Holding period trend` |
| 25 | PE company inventory by years held | bars, H | Breakdown `Current PE company inventory` |
| 26 | Global GP-led secondary exit value (US$bn) | bars, H (stands alone) | Outlook `GP led secondaries` |
| 27 | US PE fundraising: capital raised and fund count | bars + line, F | Breakdown `Fundraising activity` |
| 28 | US PE MM fundraising | bars + line, H | MM `Fundraising activity` |
| 29 | US PE median and average fund size (US$m) | two lines, H | Breakdown `Median and average fund size` |
| 30 | MM buyout capital raised as share of all US PE buyout capital | line, H | MM report |
| 31 | US PE median fund step-up | line, H | Breakdown `Fundraising step ups` |
| 32 | US PE dry powder by fund size, and deployment runway | stacked bars + line (rhs), F | MM `Capital overhang`; runway = Junson calc |
| 33 | Partner manager asset exposure | donut, H | GPS V letter, Portfolio Diversification |
| 34 | Partner manager underlying portfolio companies by sector | donut, H | same |
| 35 | GP holding value by partner manager | donut with centre total, H | GPS V letter, GP Holding Value |
| 36 | Net TVPI progression (LP net blended) | stacked DPI + RVPI bars, H | GPS V letters, Fund Overview |
| 37 | Composition QoQ - by asset class and by partner manager | two tables side by side | GPS V letters (latest and prior) |
| 38 | Quarterly valuation bridge and movers | table | GPS V letter, Quarterly Change in GP Valuation |
| 39 | Key performance and capital metrics, QoQ | table | GPS V letters |
| 40 | GP-stakes league table | table | PitchBook screen; manager reporting |
| 41 | GPS V vs HPC Fund I - latest reported quarters | table | GPS V letter; HPC report |
| 42 | DPI performance trends - buyout vintages, tracked funds marked | four-panel quartile curves, F (tall) | GPS V letter market-commentary figure, digitised; markers = Junson calc |
| 43 | Net IRR vs reporting-peer median | bars, H | Junson calc |
| 44 | TVPI and DPI vs reporting-peer medians | grouped bars, H | Junson calc |
| 45 | Net IRR percentile within reporting peers - trajectory | line, one point per quarter, H | `comp_series.json` |
| 46 | TVPI and DPI percentile - trajectory | lines, H | `comp_series.json` |
| 47 | GP-stakes peer universe: formation and size by vintage | bars + line, F | PitchBook screen |

Annual series with a partial current year are labelled `2026*` and the note says what the
star covers (YTD through which date). Always plot the partial period. Multiples built on
few observations carry `n=` in the note and are called indicative in the text. From the
second ledger quarter onward Ex 43-44 show QoQ momentum versus the peer median instead of
levels, and Ex 45-46 become real time series; update captions accordingly.
If a benchmark figure such as Ex 42's source chart is absent from the new letter, drop
Ex 42 this quarter ("Missing inputs").

### Chart style (frozen)

- Canvas equals insertion size, 200 dpi, white background: full 6.72 x 3.0 in (Ex 42 about
  6.72 x 4.85 in), half 3.125 x 2.3 in. Text in the image therefore prints at its true size.
- Font: DejaVu Sans (the matplotlib default, as in the 2026Q3 charts). Tick labels 8 pt,
  value labels 8 pt bold, legend 8 pt.
- Palette, in series order: `#2E6DA4` (primary bars and lines), `#16283F` (second series,
  count lines), `#6B97BE`, `#A0BAD3`, then `#1F4E79`, `#155E75`, `#B07D3F` for many-slice
  donuts. One palette file; no hex literals inside chart functions.
- No title inside the image (the caption sits in the document). Legend inside the plot
  area, position frozen per exhibit in the ledger. Light horizontal grid only; no top or
  right spine except where a right axis is used. Right-axis series labelled "(rs)" in the legend.
- Label the latest value on line charts. Value labels are horizontal. Y-axes frozen in the
  ledger: widen by one tick only when a new point exceeds the range, and log why.
- A redraw fixes the source chart's flaws (clipped lines, crowded labels) rather than
  reproducing them. Research charts are read and redrawn, never screenshotted.

## Phase two - English full report

Verify the sign-off first (hashes must match). Then write section by section; show the user
each major block (market sections, Things We Should Know, Fund Update, Competitor Analysis)
before moving on where they are available to review.

### Framework (fixed)

Cover block: `JUNSON Capital Research` / `US Private Equity Quarterly Report (<RQ>)` /
`Coverage: US PE / buyout & LBO / middle market / GP stakes` with the issue date right-aligned.

| Section | Content | Exhibits |
|---|---|---|
| 1 Market Overview | One paragraph: the quarter in four or five bolded numbers and the through-line | - |
| 2 Deal Activity | 2.1 Deal value and count; 2.2 Deal composition (add-ons, size, sector rotation, secondary buyouts); 2.3 LBO volume in M&A context; 2.4 Middle market; 2.5 How the volume measures nest - and where private credit connects | 1-12 |
| 3 Valuations, Performance & Financing | 3.1 Entry multiples; 3.2 Fund performance: rolling horizon IRR (US, then Europe) | 13-18 |
| 4 Exits & Liquidity | 4.1 Exit activity (market, then middle market); 4.2 Holding periods and inventory | 19-26 |
| 5 Fundraising & Dry Powder | 5.1 Fundraising (market, then middle market, fund sizes, step-ups); 5.2 Dry powder and deployment runway | 27-32 |
| 6 Sentiment | Only when `Broker\` contains sell-side PE research: one broker-views table (stance / key points / QoQ change, industry-level views only) and related news. Otherwise omit the section; the sections after it renumber | - |
| 7 Things We Should Know | 7.1 and 7.2: this quarter's two most important themes (chosen fresh each quarter); 7.3 How the PE market impacts the private credit market; 7.4 How the PE market impacts GP-stakes funds; 7.5 Implications for Junson, ending with "what would change our mind" thresholds | - |
| 8 Fund Update | 8.1 Blue Owl GP Stakes V: intro; 8.1.1 Fund snapshot (terms table, QoQ metrics table, Quarter activity and Manager commentary bullets); 8.1.2 Portfolio composition; 8.1.3 Fund-level performance | 33-39 |
| 9 Competitor Analysis | Vintage-convention note; 9.1 Positioning vs the GP-stakes universe; 9.2 Head-to-head QoQ: GPS V vs HPC Fund I; 9.3 DPI benchmark; 9.4 Relative momentum and percentile trajectory; 9.5 Appendix - peer universe and methodology | 40-47 |

If Junson adds or exits a PE holding, section 8 gains or loses an 8.x block with the same
three-part structure; ask the user before changing the fund list.

### How to write

- Each subsection: an opening sentence that states the judgement, then the supporting
  numbers, then what it means. Key figures in bold. Dense, no filler, no hedging adverbs.
- Lead with change: QoQ and YoY for flows, pp for shares and IRR, turns (x) for multiples.
  Money as `US$177.3bn` / `US$53.4m`; percentages to one decimal; multiples as `12.5x`.
- State lags plainly ("as of 30 Sep 2025 - performance lags about three quarters").
- Section 7.3 and Ex 12 cross-reference the latest Junson Private Credit Quarterly: cite
  its section numbers and figures only after opening that report; if it is not available,
  drop Ex 12 and the cross-reference figures and write 7.3 from this report alone.
- 7.5 and each "Implication for Junson" sentence must follow from numbers in this report.
  Last quarter's "what would change our mind" thresholds and the Summary's Watch List are
  stored in the ledger (`watch`); answer each one explicitly this quarter.
- Captions `Exhibit N: <title>`; full-width captions bold. Under every exhibit one note
  line: `Note: <only what the reader needs to avoid misreading>. Source: <publisher>; as of <date>.`
  Method detail belongs in the ledger, not under the chart.
- Fund section notes cite the letter, its report date, received date and page numbers.
- Nothing from news or the web without a full article URL.

### Document format (matches the 2026Q3 issue)

- A4 portrait; margins top/bottom 0.63 in, left/right 0.76 in (text width 6.74 in).
- Body Calibri 8 pt, justified. Cover: `JUNSON Capital` 26 pt bold `#16283F` + `Research`
  26 pt bold `#2E6DA4`; report title 20 pt; coverage line small grey.
- Heading 1: 18 pt bold `#16283F`. Heading 2: 12.5 pt bold `#2E6DA4`, numbered `2.1`.
- Notes 7 pt `#5A6B7B`. Negative QoQ cells in tables may use `#C00000`.
- Tables: header row fill `#1F3B5B` with white bold text, repeated across pages; body rows
  alternate white and `#F2F5FB`; thin borders; 8 pt.
- Full-width exhibits inserted at 6.72 in. Half-width pairs sit in a borderless two-column
  table, each cell holding caption, image at 3.125 in, note.
- Header: `JUNSON Capital Research · US PE Quarterly Report (<RQ>)`. Footer: `Page N`.

### Checks after building the docx (all must pass)

These are run by step 8 (`enforce.py post`), which must exit 0 for all four files together.
The list below says what it checks; it does not replace the command.

1. Every number in the text is traced back to the ledger; anything that is close to but
   not equal to a ledger value is fixed. Numbers not in the ledger are confirmed against
   their source one by one and given a home in the ledger.
2. Layout: page size and margins, fonts and sizes, image widths (6.72 / 3.125 in only),
   47 exhibits numbered consecutively with caption and note, table header rows repeat,
   header and file name carry the same `RQ`, no placeholder text.
3. Render to PDF, look at the pages, and fix orphaned captions, split pairs and tables
   breaking badly.

## Phase three - Summary (English), max 2 pages

Built only from the finished English report and the ledger - no new numbers.

1. Header line `JUNSON Capital | Alternative Investment Division`; title
   `US Private Equity Research Summary — <RQ>`.
2. **Conclusion** paragraph: market verdict, the dispersion that matters, the vintage /
   allocation view, the holding's quarter and a one-phrase assessment in quotes.
3. Table "Key market indicators at a glance (<market_cq>)": Indicator / Reading / Context /
   Direction (↑ ↓ Flat) - deal value, exit value, fundraising, dry powder, entry multiples,
   rolling one-year IRR. As-of line beneath.
4. Two charts side by side (Ex 1 and Ex 19 re-rendered at 3.375 in) with one caption line.
5. **1. Key News** - five bullets, bold lead-in then numbers.
6. **2. Market Trend** - table Indicator / Reading / Interpretation (global M&A, US PE deal
   value, exits, fundraising, dry powder, middle market); two charts (Ex 27 and Ex 32).
7. **3. Impact on Our Portfolio (GP stakes)** - three bullets: fee stream, carry and
   distributions, marks.
8. **4. Our Position** - table Fund / Net IRR / TVPI / DPI / Peer percentile / Comment /
   Action, one row for GPS V and one for the benchmark competitor; footnote with bases and
   portfolio-level actions.
9. **Watch List** - table Item / Current / Signal or timing / Why it matters; store it in
   the ledger `watch` for next quarter.

Format: A4, margins about 0.58 in sides and 0.35-0.4 in top/bottom, Calibri 9 pt body,
7 pt notes, table header `#1F3B5B` white, borders `#C9D3DF`, header
`JUNSON Capital | US PE Quarterly`, footer `For internal research use only — Junson AID`.
Render to PDF and confirm it is at most 2 pages; cut words, not font size, to fit.

## Phase four - Chinese versions

Translate the final English report and summary. Rebuild from the same structure so layout,
exhibit order and images are identical; replace text only.

- Simplified Chinese, written as a mainland research report would read - translate meaning,
  not word order. Keep sentences as tight as the English.
- Keep in English: fund and manager names (Blue Owl GP Stakes V, HPC Fund I, Stonepeak),
  data providers (PitchBook, MSCI Burgiss), and the terms IRR, TVPI, DPI, RVPI, EV/EBITDA,
  LBO, GP, LP, IPO, M&A, BSL, CLO, AI, YTD where they read naturally.
- Numbers are identical to the English: same digits, signs, decimals and units. Use 亿美元
  for US$bn amounts (US$177.3bn = 1,773亿美元), 百万美元 for US$m, 个百分点 for pp, x stays x.
  Dates as 2026年6月30日. Quarter labels (2Q26, 2026Q3) unchanged.
- Captions `图N：`; notes `注：…… 资料来源：……；数据截至……。`
- Fonts: Latin Calibri, East Asian Microsoft YaHei; body colour `#222A35`.
- Header `JUNSON Capital｜ 美国私募股权季度报告 <RQ>`; footer
  `基本面分析报告 — 仅供内部研究使用 · 第 N 页`. Summary title `美国私募股权研究报告摘要 — <RQ>`.

Fixed glossary (use these every quarter):

| English | 中文 |
|---|---|
| Market Overview / Deal Activity | 市场综述 / 交易活动 |
| Valuations, Performance & Financing | 估值、业绩与融资 |
| Exits & Liquidity / Fundraising & Dry Powder | 退出与流动性 / 募资与待投资金 |
| Things We Should Know | 我们应当知道的事 |
| Fund Update / Competitor Analysis | 基金更新 / 竞争对手分析 |
| Implications for Junson | 对Junson的启示 |
| buyout / LBO | 并购 / 杠杆收购 |
| add-on / secondary buyout | 附加收购 / 二次并购 |
| middle market / megafund | 中型市场 / 超大型基金 |
| dry powder / deployment runway | 待投资金 / 投放空间 |
| GP stakes / partner manager | GP少数股权 / 合作管理人 |
| rolling one-year horizon IRR | 滚动一年期内部收益率 |
| entry multiple / step-up | 入场倍数 / 基金规模递增倍数 |
| holding period / inventory | 持有期 / 在持企业存量 |
| GP-led secondaries | GP主导型二级交易 |
| league table / percentile | 联赛表 / 百分位 |
| valuation bridge / markdown | 估值桥 / 估值下调 |
| QoQ / YoY / YTD | 环比 / 同比 / 年初至今 |
| Conclusion / Watch List | 结论 / 观察清单 |
| vintage (first-investment year) | 年份（首笔投资年） |

**Parity check (must pass):** extract every number from the English and the Chinese file
paragraph by paragraph and table cell by table cell; the sequences must match after unit
conversion (bn ↔ 亿). Same count of headings, exhibits, tables and images. Render the
Chinese files to PDF and look at them; the Chinese summary must also fit 2 pages.

## Delivery

1. Write the four files to `PE\output\` with the names above (create the folder if missing).
2. Write back `_charts\series.json`, `_charts\comp_series.json` and any new pipeline file.
3. Write `input\<RQ>\_charts_snapshot\`: zip of the signed PNGs, signed ledger copy,
   `APPROVED_<RQ>.json`, `REVIEW_<RQ>.md`, and `sources_ledger_<RQ>.md` (every exhibit and
   every out-of-ledger number with its source).
4. Tell the user in a few lines: the four file names, the missing inputs and the exhibits
   and sections dropped because of them, restatements above 2%, and the Watch List items that
   triggered.

## When the user says "no need to re-extract"

Rebuild charts from the existing ledger and continue, provided the data quarters in `meta`
are unchanged and the ledger has no empty required slot. Regenerated PNGs void the old
sign-off - re-issue the review sheet and get a new signature. If the user says "charts are
fine, only redo the text", verify the sign-off hashes and go straight to phase two.

## Mistakes not to make

1. Using an issued report (any version) as a data source or placeholder.
2. Writing prose, summary or translation before a valid sign-off.
3. Naming files by the data quarter instead of `RQ`, or mixing data quarters without
   stating each as-of date.
4. Comparing GPS V and HPC as if same-quarter - they report one period apart; say so.
5. Comparing net IRRs across different bases without the caveat (GPS V net blended and
   with / without credit facility; HPC headline versus pro forma excluding the
   subscription line; PitchBook self-reported and lagged).
6. Calling a multiple on a handful of observations a trend; always give `n`.
7. Dropping the partial current year or the latest point because it is incomplete.
8. Autoscaling a frozen axis, moving a legend between quarters, or changing palette order.
9. Translating numbers loosely in Chinese (billion / 亿 slips, pp written as %).
10. Letting the summary introduce a number or a judgement that is not in the full report.
11. Concluding "the source does not have it" after looking at one sheet or one page -
    search every sheet and the PDF first and record what was searched.