---
name: "aircraft-quarterly-report"
description: "Build Junson AID's quarterly Aircraft Leasing / BCGAF report set (full report + 2-page summary, English and Chinese) from the 04 Research\\Aircraft quarter folder. Use for aircraft quarterly / BCGAF update / 飞机季报 requests."
---

# Junson Aircraft Leasing Quarterly Report (aviation market + BCGAF)

Turn one quarter's folder of broker research, GP updates and competitor data into the
"Aircraft Leasing Quarterly Report" set. Every new issue must look like a sibling of the
2026Q3 baseline issue: same chapter framework, same 19 exhibits, same formatting, fresh
data - and, from the second issue on, real QoQ columns where the baseline printed "n/a" -
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
   `aircraft_config_<RQ>.json` next to `aircraft_config.json` (a copy with `exhibit_count` = N, the keys of
   `required_checks` renumbered, and a `_variant_of` note naming the skipped exhibits and the
   missing inputs; `aircraft_config.json` itself is never changed), work on a copy of the ledger in
   `_charts\<RQ>_run\` whose kept exhibits are renumbered ex01..exN and each carry
   `template_ex` (their number in the full 19-exhibit template), and point steps
   1-8 at the variant config and that copy. On delivery, write the new points back into
   `series.json` under their `template_ex` keys; a later quarter maps by `template_ex`, never
   by key.
6. **Say what was skipped** in the delivery message (in an unattended run, in the "Notes for
   the reviewer" the run asks for): each missing input and the exhibits and sections dropped
   because of it.
7. **Stop only when nothing is left.** If no broker report and no GP update is present there is no report to write: say which inputs are missing and stop.

| Missing input | Dropped this quarter |
|---|---|
| `Broker\` GS Aerospace in Pictures | Ex 3, 7 and the GS-fed text: traffic forecast, yields, orders and cancellations, parked fleet, ISM / PMI, fuel direction, HY airline credit |
| `Broker\` Barclays aviation demand tracker | Ex 1, 5 and the Barclays-fed text: GDP forecasts, European fares, UK card spend, transatlantic fares, TSA volumes |
| `Broker\` JPM aircraft leasing credit | Ex 8-10; Values & Lease Rates; lessor credit and relative value, funding and maturity profile |
| Every `Broker\` report | Their columns of the Sentiment table (Ex 11); with none left, the broker side of Sentiment |
| `Fund\` latest GP update | The Fund Update section (Ex 12-16), the GP narrative in Sentiment, the fund points of Things We Should Know, the fund rows of the Summary |
| `Fund\` prior GP update only | The prior-quarter and QoQ columns of the fund tables; the latest quarter stays |
| `Competitor\` PitchBook fund screen | Ex 17-18, the league table, DPI vs fund age, deployment pace, the momentum ledger |
| ABS pricing (web or `Market\`) | Ex 19 and the ABS funding cost league |
| IATA (web or `Market\`) | Ex 2, 6 and the IATA-fed text |
| Every competitor input | The whole Competitor Analysis section |

## Running from attached files (Claude API, the AID research panel)

When the skill runs without the research folder (the sources are attached to the request or
uploaded into the container, as the research panel's "Generate with AI" does, and
`04 Research\Aircraft`, `_charts\` and the pipeline scripts cannot be reached):

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

Aircraft root (sources are read from its `input\` subfolder, reports are written to its `output\` subfolder; in the enforce commands `<quarter_folder>` = `input\<RQ>` and `<out_dir>` = `output`). If the root still has the old layout (quarter folder and reports directly in the root), read the quarter folder where it is, do not move the user's files without asking, and still write new reports to `output\`:
`C:\Users\GallonXu(Intern)\Junson Capital\Alternative Investment Division - General\04 Research\Aircraft`

| # | File (written to `Aircraft\output\`) | What it is |
|---|---|---|
| 1 | `Junson_Aircraft_Report_<RQ>_EN_v<n>.docx` | Full report, English (master) |
| 2 | `Junson_Aircraft_Report_<RQ>_CN_v<n>.docx` | Full report, Chinese (translation of the signed-off English) |
| 3 | `Junson_Aircraft_<RQ>_Summary_EN.docx` | Summary, English, max 2 pages |
| 4 | `Junson_Aircraft_<RQ>_Summary_CN.docx` | Summary, Chinese, max 2 pages |

The 2026Q3 baseline files are named `BCGAF_Quarterly_Tracker_2026Q3*.docx` and
`BCGAF_2026Q3_Summary_*.docx`; they are the same report family (kept in the root or in `output\2026Q3\`). `<n>` starts at 1 and
increments on every re-issue; never overwrite an existing file in `output\`.

```
04 Research\Aircraft\
├── _charts\                      shared across quarters, exactly one, never re-created
│   ├── series.json               the ledger - appended in place every quarter
│   ├── comp_series.json          competitor / ABS / momentum history (append only)
│   └── pipeline\                 chart / check / build scripts, written once then frozen
├── input\<RQ>\                   the quarter's source folder (what the user points at)
│   ├── Broker\                   GS, JPM, Barclays (and any other sell-side) PDFs
│   ├── Fund\                     Bain Capital Griffin quarterly investor update / overview
│   ├── Competitor\               PitchBook_Search_Result_Columns_*.xlsx; ABS presales if any
│   ├── Market\                   optional - saved IATA releases / ABS pricing PDFs
│   └── _charts_snapshot\         this quarter's audit trail (PNGs zip, signed ledger copy,
│                                 APPROVED_<RQ>.json, REVIEW_<RQ>.md, sources_ledger_<RQ>.md)
└── output\                       the four deliverables; issued reports of earlier quarters sit in
                                  output\<quarter>\ (layout and tone reference only, never data)
```

## Enforced by code (read this first)

The rules in this skill are checked by scripts kept in `04 Research\Aircraft\_charts\pipeline\`.
Stage that folder at the start of every run and read `RUNBOOK.md` there. A step is finished
only when its command exits 0. Where this section and a later section differ, this section wins.

| # | When | Command | Blocks |
|---|---|---|---|
| 0 | Start | `python3 selftest.py` | Guards that no longer fire on planted faults |
| 1 | Meta set | `python3 enforce.py stale aircraft_config.json <ledger_dir> --run-date <today>` | Wrong report quarter; quarters hard-coded in frozen scripts; missing meta or missing frozen script |
| 2 | After extraction | `python3 enforce.py ledger aircraft_config.json <ledger_dir>` | Missing exhibits or fields; issued report as a source; relayed data without its original publisher; dropped latest point; unfrozen axis; open gaps |
| 3 | After extraction | `python3 enforce.py srcaudit aircraft_config.json <ledger_dir> <quarter_folder>` | Source file not in the quarter folder; web figure without a URL |
| 4 | After charts | `python3 enforce.py charts aircraft_config.json <ledger_dir> <charts_dir>` | Missing chart; canvas not at insertion width; overlapping, clipped, rotated or non-English chart text |
| 5 | Before the gate | `python3 enforce.py review aircraft_config.json <ledger_dir> <ledger_dir>/REVIEW_<RQ>.md` | Identities declared in the ledger that do not hold (maturity totals, transaction shares, exposure columns) |
| 6 | Gate | `python3 enforce.py sign aircraft_config.json <ledger_dir> <charts_dir> <quarter_folder> --by "<the user's own words>"` | Signing without the user's words or while steps 2-4 fail |
| 7 | Before any text | `python3 enforce.py check aircraft_config.json <ledger_dir> <charts_dir>` | Text on an unsigned or changed ledger or chart set |
| 8 | Four files built | `python3 enforce.py post aircraft_config.json <ledger_dir> <charts_dir> <out_dir>` | Wrong names or quarter; EN/CN number mismatch; numbers not in the ledger; exhibits out of order; wrong page, margins or image widths; placeholders, including any leftover "baseline quarter" cell; summary over 2 pages |

What exists and what the first run must add:

- In the folder now: `enforce.py`, `guards.py`, `selftest.py`, `aircraft_config.json`,
  `series_template.json` (19 exhibits with required fields and identity checks),
  `style.py` (frozen palette and sizes) and `docx_render.py` (document layout helpers).
- Not yet written, because no aircraft quarter has been run through this pipeline: the
  extraction scripts and `build_charts.py`. The first run writes them into the same folder.
  `build_charts.py` must save every chart through `style.save()` so the guards run; step 1
  fails until it exists. Start the ledger from `series_template.json`.

Hard rules about the scripts:

- Never edit `enforce.py`, `guards.py` or `aircraft_config.json` to make a check pass, never
  pass a flag that skips a check (`--no-gate` and `--no-trace` are for testing the checker
  only), and never replace a failing command with a manual check. If a rule looks wrong for
  this quarter, stop and ask the user.
- `--rq-reason` (step 1) and `--by` (step 6) carry the user's own words. Never invent them.
- If `_charts\pipeline\enforce.py` is missing or `selftest.py` fails, stop and tell the user.
  Do not rebuild the kit from memory.
- Every exhibit whose source mentions IATA, IBA, Cirium, TSA or Ishka needs `publisher` set,
  and `via` when a broker relays it. Values read off a chart go into
  `readings_<period>.json`; figures taken from source text go into `extra_<RQ>.json` with the
  file and passage. None of these may be typed into a script.
- The text for a quarter is built by `content_<RQ>.py`, written fresh each quarter, and it
  must run step 7 itself before writing anything.
- Any change to the ledger or a chart after step 6 voids the sign-off: re-run steps 2-5,
  show the user, sign again.
- After delivery write back the ledger, the readings / extra files, the sign-off file and any
  new script, and list the folder to confirm they are there.

## Rules that override everything else

1. **Nothing is copied from a previous report.** Earlier issues are the truth for layout
   and tone only. They are never a data source, not even as a temporary placeholder.
   Allowed sources, in order: (a) files in `input\<RQ>\`, (b) web research with publisher + date
   + full URL, (c) asking the user. If none yields the number, leave the slot empty with an
   explicit gap note ("n.d." in tables).
2. **Ledger first, append only.** `exhibit = frozen style x a slice of series.json`. Each
   quarter appends the new period; historical points are never recomputed or deleted.
3. **Every number carries a `src`** naming the file and the page / chart / table actually
   opened, and - for broker-relayed data - both the relaying broker and the original
   publisher ("IBA via JPM", "Cirium via GS", "TSA via Barclays"). Write `src` only for a
   location that was really checked.
4. **Hard gate between charts and prose.** No valid sign-off, no prose - also when running
   unattended or on a schedule. Stop at the gate and leave the review sheet for the user.
5. **Prose reads numbers from the ledger**, never re-extracts them for the text.
6. **English is the master; Chinese is a translation of the signed-off English.** Same
   numbers, exhibits and order. Charts stay in English in both versions (the same PNG files
   are inserted); captions, notes, tables and body text are translated.
7. **Quarters and months are never hard-coded.** Every period label derives from `meta`.
8. **Keep source wording honest.** Qualitative source statements stay qualitative
   ("marginally negative", "tightened") - never invent a figure for them. Approximations
   are marked `~`; GP estimates are labelled as estimates; fund figures are "unaudited GP
   estimates" until audited.
9. **One reference series per concept.** IATA releases are the reference for traffic, load
   factor and industry profit. When GS, Barclays and IATA readings differ, report the IATA
   figure as the reference and explain the construction difference rather than averaging.

## Which period is which

| Label | Meaning | How it is set |
|---|---|---|
| `RQ` | Report quarter = when the report is written | Calendar quarter of the run date. Confirm with the user if the folder name differs |
| `market_asof` | Cut-off date for market data | Date of the latest broker report in `Broker\` |
| per-series month | Each market series has its own latest month (IATA regional data lags 4-6 weeks; fares, orders and parked fleet are monthly) | Read from each source; store per exhibit as `asof` |
| `fund_cq` / `fund_pq` | Period of the latest and prior GP updates | Read from each update; normally RQ-1 |
| `lessor_ltm` | LTM period of the JPM lessor comps | From the JPM table header |
| `screen_date` | PitchBook fund-screen export date | From the xlsx file-name timestamp `_YYYY_MM_DD_` |

`RQ` appears in exactly three places: file names, the cover title, the page header.
Everything else uses the data period of the series concerned, stated in the caption or note.

## Inputs and what they feed

| Folder | File pattern | Feeds |
|---|---|---|
| `Broker\` | GS `Aerospace & Defense_ Aerospace in Pictures_*.pdf` (monthly) | Traffic forecast, forward capacity (Ex 3), yields, orders and cancellations (Ex 7), parked fleet, ISM / PMI leading indicators, fuel direction, HY airline credit |
| `Broker\` | `Barclays_European_Transportation_Monthly_Aviation_Demand_Tracker_*.pdf` | GDP forecasts (Ex 1), European achieved fares (Ex 5), UK card spend, transatlantic fares, TSA volumes |
| `Broker\` | `JPM_Aircraft_Leasing_Cre*.pdf` | Values and lease rates (Ex 8, IBA data), lessor comps (Ex 9), debt maturities (Ex 10), ratings and relative value, supply-normalisation view, lessor results (e.g. Avolon), jet fuel |
| `Fund\` | Bain Capital Griffin quarterly investor update (latest and prior) and investor overview | Fund Update section, Ex 12-16 |
| `Competitor\` | `PitchBook_Search_Result_Columns_*.xlsx` | Competitor Analysis, Ex 17-18, deployment pace |
| `Market\` (optional) | Saved IATA releases, ABS pricing or presale PDFs | Same exhibits as the two web rows below; a saved file takes priority over the web |
| web | IATA releases (traffic by region, industry outlook) | Ex 2, Ex 6, traffic and profit forecasts |
| web | Aviation ABS pricing: Ishka, KBRA / Fitch presales, trade press | Ex 19 |

Use the latest edition of each monthly broker report; if several months are in the folder,
the latest feeds the exhibits and the earlier ones only give the path within the quarter.
Take files by wildcard, never by full name. A new broker in `Broker\` is added to the
Sentiment table as a new column and flagged `New` in its QoQ row.

**If an input is missing** - in particular the GP update, which is not always saved to the
folder - skip and drop what depends on it: see "Missing inputs" at the top. Never write the
Fund Update from the previous issue.

### Working with the folder

- The folder is OneDrive-synced; many files are cloud-only. Reading them from the shell on
  the user's computer fails with `Input/output error` or `Invalid argument`. Stage the files
  into the working environment first (staging downloads them), then work on staged copies.
- Build charts and documents in the working environment (chart PNGs and broker chart pages
  must be opened and looked at), then write deliverables, ledger and snapshot back.
- Before each run, read `_charts\series.json`, `_charts\comp_series.json` and
  `_charts\pipeline\` back from the folder. If they do not exist, this is a first build.

## Phase one - numbers and exhibits

1. **Set the run parameters** (`RQ`, `market_asof`, `fund_cq`, `fund_pq`, `screen_date`) in
   `meta`. Check that nothing in `meta` or in any script still names last quarter.
2. **Inventory the folder** recursively and stage it. Report gaps against the input table
   before extracting anything.
3. **Extract into the ledger**, exhibit by exhibit. For each store: `title_en`, `kind`,
   `size`, `periods`, `series`, `unit`, `asof`, `src`, `note_en`, frozen `ylim` / `ytick`,
   `legend_loc`, and `aux` for every Junson calculation with formula and inputs. For points
   read off a broker chart rather than printed, record `digitised: true`, and say so in the note.
4. **Market dashboard ledger.** Besides the exhibits, store every headline market reading
   as a named series so QoQ can be computed next quarter: IATA full-year traffic growth
   forecast, YTD RPK growth, load factor, industry net profit and margin, jet fuel
   (assumption and spot), parked fleet %, order backlog, monthly gross orders and
   cancellations by OEM, 10-year-old values and lease rates by type, lessor lease yield,
   10-yr UST, ABS senior spread range, lessor maturities by year.
5. **Junson calculations** - compute in code, store inputs and result in `aux`:
   - Lessor debt maturities by year = sum of issuer-level schedules (list issuers excluded)
   - Fuel: spot versus the per-gallon rate implied by IATA's per-barrel assumption (42 gal/bbl)
   - Fund: % called = contributions / commitments; DPI on contributions; portfolio value as
     % of scaled target; shares of portfolio value by transaction (must sum to 100%)
   - Exposure chart (Ex 13): if the GP chart is unlabelled, measure segment shares from the
     image; each column must reconcile to 100%; mark as approximate readings
   - Effective vintage = year of first investment (PitchBook convention); fund age from it
   - Competitor percentiles: share of the reporting cohort strictly below the subject, with
     the subject excluded; record cohort `n`. While BCGAF is under 50% called its fund-level
     IRR / MoM are "NM"; use the Griffin platform vintages as proxy and label them as such
6. **Competitor screen.** Parse the PitchBook export from the header row `Fund ID`; drop
   the blank and copyright rows; count vehicles and those reporting performance. The screen
   is a keyword search and under-captures the universe (Carlyle SASOF, Castlelake flagship
   funds, Sky Leasing carry no "aircraft" in the name) - say so, and add named funds the
   user supplies. Append this quarter's points to `comp_series.json`.
7. **ABS league (Ex 19).** Append deals priced since the last issue (sponsor, date, size,
   senior class and rating, coupon, spread to Treasuries, senior LTV) and fill earlier
   `n.d.` cells where presales or trade press now disclose them. Each cell needs its own
   source URL; undisclosed stays `n.d.`.
8. **Build the charts** with the frozen style and run the mechanical checks: all chart text
   English; no overlapping text boxes; y-axes from the ledger; last point present.
9. **Look at every PNG yourself** and redo any chart with touching labels, a legend on
   data, or clipped text.
10. **Write `REVIEW_<RQ>.md`**: (a) identity checks - regional and exposure shares
    reconcile, transaction shares sum to 100%, maturity sums equal issuer totals, % called
    and DPI recompute, percentile inputs match cohort `n`; (b) one row per new number:
    exhibit / series / prior / current / change / `src`. A failed identity blocks the gate.
11. **Gate.** Give the user the PNGs and the review sheet, ask them to check every chart and
    row, and stop. On their confirmation write `APPROVED_<RQ>.json` with the sha256 of
    `series.json`, `comp_series.json` and every PNG. Any later change voids it. The gate may
    span sessions - phase two can start in a new session.

### First build (no ledger in `_charts\`)

Start with Ex 2 (IATA regional data) and Ex 10 (JPM maturity schedule) only and compare
against the latest issued report digit by digit; then run the rest. Prior-period points
needed for QoQ are backfilled from the earlier quarter folder's own source files
(`input\2026Q3\Broker\`, `input\2026Q3\Competitor\`, the prior GP update), never from the issued report.
The enforcement kit, `style.py` and `docx_render.py` are already in `_charts\pipeline\`;
use them and do not write replacements. Write only the missing extraction scripts and
`build_charts.py` there. Once the first issue is signed, add those scripts to
`frozen_scripts` in `aircraft_config.json` and tell the user you did.

### Exhibit inventory (19)

| Ex | Title (period parts update each quarter) | Kind / size | Source |
|---|---|---|---|
| 1 | GDP forecasts by economy, % over previous period (saar) | table: Global, US, Euro area, UK, Germany, France, Italy, Spain x six quarters | Barclays |
| 2 | Passenger demand by region, <month>, yoy change in RPKs | horizontal bars, six regions, negative bar grey, full | IATA |
| 3 | Global airline forward scheduled capacity, yoy growth | bars, next three months, small centred | GS |
| 4 | US demand dashboard | table: Metric / Latest reading / Prior quarter / Source | Barclays, GS, IATA |
| 5 | European airline groups - <month> achieved fares, yoy | grouped bars by airline group (intra-Europe short-haul vs North Atlantic economy), small centred | Barclays |
| 6 | Global airline net profit and load factor | bars + line (rhs), actuals and forecast year, full | IATA |
| 7 | Boeing and Airbus gross orders and cancellations, <month> | grouped bars, small centred | GS |
| 8 | 10-year-old aircraft - value and market lease rate change, yoy | table: 777-300ER, A330-300, A320-200, 737-800 | IBA via JPM |
| 9 | Aircraft lessor credit comps - ratings, lease yield, leverage, returns (LTM) | table: Issuer / Moody's-S&P / Lease yield / Net debt-to-equity / RoE | JPM |
| 10 | Aircraft lessor debt maturities by issuer, next three years (US$bn) | stacked bars by issuer, full | JPM; sums = Junson calc |
| 11 | Broker and GP summary - views and key points | table: rows Stance / Key points / Δ QoQ, one column per broker | brokers in `Broker\` |
| 12 | BCGAF - transactions and realisation status | table: Transaction / Units / Lessee status / % of portfolio value / Status | GP update |
| 13 | BCGAF exposure - sector / asset type / market class / lessee / region / credit tier | six 100% stacked columns, monetised assets grey, full | GP update (redrawn) |
| 14 | BCGAF portfolio scorecard - status vs scaled target | table: Parameter / Scaled target / Status / Δ QoQ (11 parameters) | GP update |
| 15 | BCGAF - asset monetisations, closed and in progress | table: Asset-lessee / Market-timing / Status / Gross IRR / Gross MoM | GP update |
| 16 | Griffin platform track record - Vintage 1 & 2 vs Aircraft Fund | table: Gross IRR, Gross MoM, Net IRR, Net MoM, Invested capital, DPI | GP overview |
| 17 | Aviation fund league table - Junson holding vs competitors | table: Fund / Manager / Vintage / Size / Net IRR / TVPI / DPI / Called % | PitchBook; GP; Junson calc |
| 18 | DPI vs fund age - aviation peers, Griffin vintages and BCGAF | scatter with labels, full | PitchBook; GP; Junson calc |
| 19 | Aviation ABS new-issue funding costs - senior tranches | table: Deal / Sponsor / Priced / Size / Senior class / Coupon / Spread / Snr LTV, Griffin rows bold | Ishka, KBRA, Fitch, trade press |

"Δ QoQ" columns were "n/a - baseline quarter" in 2026Q3. From the next issue they must be
filled from the ledger: numeric change where the metric is numeric, `A → B` where it is a
status or stance, `New` for a broker, deal or parameter that was not there last quarter,
`—` for no change. Exhibits tied to a month keep the same design when the month changes.
If a source stops publishing a series, keep the exhibit number, say so in the note, and ask
the user whether to replace it.

### Chart style (frozen)

- Canvas equals insertion size, 200 dpi, white background: full 6.5 x 2.4-2.7 in
  (Ex 13 about 6.3 x 3.6 in); small centred charts 3.0-3.4 in wide.
- Font: DejaVu Sans (the matplotlib default, as in the 2026Q3 charts); ticks and value
  labels 8 pt.
- Palette, in series order: `#1F2A44` (navy, primary), `#3D6B8E` (steel blue), `#2FA6A0`
  (teal, highlight and positive bars), `#5C86AD`, `#63B8B2`, grey `#9AA2AD` for negative /
  monetised / de-emphasised. One palette file; no hex literals inside chart functions.
- No title inside the image. Value labels on bars, horizontal. Light grid, no top or right
  spine unless a right axis is used. Legend inside the plot area, position frozen per
  exhibit. Y-axes frozen in the ledger; widen by one tick only when a new point exceeds
  the range, and log why.
- Broker charts are read and redrawn, never screenshotted; a redraw fixes the source
  chart's flaws rather than reproducing them.

## Phase two - English full report

Verify the sign-off first (hashes must match). Write section by section, showing the user
each major block (market sections, Things We Should Know, Fund Update, Competitor Analysis)
where they are available to review.

### Framework (fixed)

Cover block: `JUNSON Capital Research` / `Aircraft Leasing Quarterly Report (<RQ>)` /
`Coverage: aviation / aircraft leasing / lessors / BCGAF` with the issue date right-aligned.
Section and subsection headings are unnumbered.

| Section | Subsections | Exhibits |
|---|---|---|
| Demand | Macro backdrop; Global passenger traffic; US demand; European airline pricing & consumer demand; Airline profitability & fuel | 1-6 |
| Supply | Order backlog & deliveries; Supply normalisation watch | 7 |
| Values & Lease Rates | Aircraft values & lease rates by segment; Lessor portfolio economics | 8 |
| Financing & Credit | Lessor credit & relative value; Funding & maturity profile; Airline credit backdrop | 9-10 |
| Sentiment | Broker & GP summary (table, then a "GP narrative" paragraph comparing the GP letter with the sell-side view); Related news (about five items, bold lead-in, one to two sentences each) | 11 |
| Things We Should Know | Five numbered observations ordered by importance, each a bold one-sentence claim then the evidence and what it means for the holding; the last one is "Data hygiene for this tracker" | - |
| Fund Update | Intro line (sources, as-of, unaudited); Bain Capital Griffin Aircraft Fund: Fund snapshot (terms table beside QoQ metrics table, then Quarter activity and Manager commentary bullets); Portfolio composition; Fund level performance detail | 12-16 |
| Competitor Analysis | Vintage-convention note; League table; DPI vs fund age; Deployment pace; ABS funding cost league; Momentum ledger; Appendix - peer universe and methodology | 17-19 |

Fund snapshot tables: left - Strategy, Total commitments, Initial close, Final close, Term,
Fees, Status; right - Metric / prior quarter / latest quarter / QoQ Δ for Portfolio value,
% of scaled target, Aircraft / engines, Invested capital, investment-level gross IRR / MoM,
NAV, Contributions and % called, Fund ITD IRR / MoM / DPI.

If Junson adds another aviation holding, the Fund Update gains a block with the same
structure; ask the user before changing the fund list.

### How to write

- Each subsection opens with the judgement, then the numbers, then the read-through for a
  lessor book or for the Fund. One bolded key sentence or figure per paragraph.
- Attribute every market figure to its publisher in the sentence ("per JPM", "IATA's June
  update", "IBA, as cited by JPM"). Where sources disagree, explain why.
- yoy for traffic, fares, values and lease rates; bp for spreads; `US$23bn`, `US$127.1M`
  for fund figures as the GP reports them; aircraft counts as `6x 737-9`.
- Always connect market to holding: which aircraft types, vintages, lessee tiers and
  regions the Fund actually holds, and what this quarter's market data implies for them.
- Track the GP's narrative against the sell-side view every quarter and say whether the
  gap opened or closed. Last quarter's five observations and the Summary's watch list are
  stored in the ledger (`watch`); answer each one explicitly this quarter.
- Fund-level IRR / MoM / DPI are "not meaningful" while the Fund is under 50% called; lean
  on MoM over IRR for short holds; pending monetisation figures are GP estimates.
- Captions `Exhibit N: <title>`, bold, centred. Under every exhibit one italic centred
  note: `Note: <only what prevents misreading>. Source: <publishers>.`
- News items need a source with a full article URL in the ledger; drop any item that
  cannot be sourced.

### Document format (matches the 2026Q3 issue)

- A4 portrait; margins top/bottom 0.63 in, left/right 0.76 in.
- Body Calibri 8 pt, justified. Cover: `JUNSON Capital` 26 pt bold `#1F3864` + `Research`
  26 pt `#2E74B5`; report title 20 pt `#1F3864` with `(<RQ>)` 13 pt grey; coverage line
  8.5 pt grey `#7F8B99`.
- Section headings 18 pt bold `#1F3864`; subsection headings 12.5 pt bold `#2E74B5`.
- Captions 8.5 pt bold `#1F3864`; notes 7 pt italic `#7F8B99`.
- Tables: header row fill `#1F2A44`, white bold text, repeated across pages; body rows
  alternate white and `#F2F4F7`; borders `#C9CED6`; 8 pt.
- Full-width charts inserted at 6.5 in; small charts 3.0-3.4 in, centred.
- Header: `JUNSON Capital｜ Aircraft Leasing Quarterly` left, `<RQ>` right, rule beneath.
  Footer: `Fundamental Analysis Report — For internal research use only`.

### Checks after building the docx (all must pass)

These are run by step 8 (`enforce.py post`), which must exit 0 for all four files together.
The list below says what it checks; it does not replace the command.

1. Every number in the text traces back to the ledger; near-misses are fixed; numbers not
   in the ledger are confirmed against their source and given a home in the ledger.
2. Layout: page size and margins, fonts, image widths, 19 exhibits numbered consecutively
   with caption and note, table header rows repeat, header and file name carry the same
   `RQ`, no leftover "n/a - baseline quarter" where a prior value exists, no placeholders.
3. Render to PDF, look at the pages, and fix orphaned captions and badly broken tables.

## Phase three - Summary (English), max 2 pages

Built only from the finished English report and the ledger - no new numbers.

1. Header `JUNSON Capital | Alternative Investment Division`; title
   `BCGAF Research Report Summary — <RQ>`; italic line: fund name | coverage | market data
   to <date>, fund data to <date>.
2. **Verdict** box (shaded): the Fund's quarter in numbers, the market-side caveat, and a
   one-phrase assessment in quotes.
3. Table "BCGAF key metrics at a glance": Metric / prior quarter / latest quarter / QoQ /
   Notes - portfolio value, capital called, investment-level gross IRR / MoM, NAV, ITD
   distributions, fund ITD IRR / MoM / DPI, aircraft / engines, commitments / final close.
4. Two charts side by side at 3.5 in (Ex 13 and Ex 18) with one caption line.
5. **1. Key News (this quarter)** - five bullets, bold lead-in, source in brackets.
6. **2. Market Trend (industry data)** - table Industry indicator / Reading / Read-through
   (traffic forecast, jet fuel, parked fleet, order backlog, 10-year-old values and lease
   rates, ABS senior spreads, lessor refinancing calendar); two charts (Ex 2 and Ex 6).
7. **3. Impact on Our Portfolio** - three bullets.
8. Aviation fund league table (compact Ex 17).
9. **4. Our Position: Assessment, Watch List & Action** - overall assessment bullet; watch
   list table Item / Current / Trigger or timing / Action if triggered; closing shaded
   **Action** box. Store the watch list in the ledger `watch`.

Format: A4, margins about 0.58 in sides and 0.3-0.35 in top/bottom, Calibri Light, body
7-8.5 pt, table header `#1F3B5B` white, borders `#BFBFBF`, verdict and action boxes
`#DCE6F1`, footer `For internal research use only — Junson AID`. Render to PDF and confirm
it is at most 2 pages; cut words, not font size, to fit.

## Phase four - Chinese versions

Translate the final English report and summary. Rebuild from the same structure so layout,
exhibit order and images are identical; replace text only.

- Simplified Chinese, written as a mainland research report would read. Keep it as tight
  as the English.
- Keep in English: fund, manager, lessor, airline and broker names and tickers (Bain
  Capital Griffin Aircraft Fund, BCGAF, AerCap, AVOL, JPM, GS, Barclays, IATA, IBA),
  aircraft types (737-800, A320ceo, 777-300ER), deal names (GGAM 2025-1), and the terms
  IRR, MoM, DPI, TVPI, NAV, ITD, RPK, RASK, ABS, LTV, JOLCO, LRF, EETC, GP, LP, NM, n.d.
- Numbers are identical to the English: same digits, signs, decimals and units. Use 亿美元
  for US$bn (US$23bn = 230亿美元), 百万美元 for US$m / US$M, 个百分点 for pp, bp stays bp,
  x stays x. Dates as 2026年6月30日. Quarter labels (2Q26, 2026Q3) unchanged.
- Captions `图表N：`; notes `注：…… 资料来源：……。`
- Fonts: Latin Calibri, East Asian DengXian (等线).
- Header `JUNSON Capital｜ 飞机租赁季报` + `<RQ>`; footer `基本面分析报告 — 仅供内部研究使用`.
  Report title `飞机租赁行业季度报告 (<RQ>)`; summary title `BCGAF研究报告摘要 — <RQ>`;
  summary header `JUNSON Capital｜另类投资部(AID)`.

Fixed glossary (use these every quarter):

| English | 中文 |
|---|---|
| Demand / Supply | 需求 / 供给 |
| Values & Lease Rates | 价值与租金 |
| Financing & Credit / Sentiment | 融资与信用 / 情绪 |
| Things We Should Know | 我们需要知道的事 |
| Fund Update / Competitor Analysis | 基金更新 / 竞争对手分析 |
| Macro backdrop / Global passenger traffic | 宏观背景 / 全球客运量 |
| Airline profitability & fuel | 航司盈利与燃油 |
| Order backlog & deliveries | 订单储备与交付 |
| Supply normalisation watch | 供给正常化观察 |
| Broker & GP summary / Related news | 券商与GP观点摘要 / 相关新闻 |
| Fund snapshot / Portfolio composition | 基金速览 / 组合构成 |
| Quarter activity / Manager commentary | 本季动态 / 管理人评论 |
| lessor / lessee / airline | 租赁商 / 承租人 / 航司 |
| narrowbody / widebody / mid-life | 窄体机 / 宽体机 / 中龄 |
| load factor / capacity / achieved fares | 客座率 / 运力 / 实际成交票价 |
| lease rate / lease rate factor | 租金 / 租金率因子 |
| sale-leaseback / parked fleet | 售后回租 / 停场机队 |
| monetisation / realisation | 变现 |
| scaled target / scorecard | 满规模目标 / 记分卡 |
| capital called / commitments | 实缴出资 / 承诺出资 |
| league table / momentum ledger | 排名表 / 动量台账 |
| credit tier / senior tranche | 信用层级 / 优先级 |
| Verdict / Watch list / Action | 结论 / 观察清单 / 行动 |
| yoy / QoQ / YTD | 同比 / 环比 / 年初至今 |

**Parity check (must pass):** extract every number from the English and the Chinese file
paragraph by paragraph and cell by cell; the sequences must match after unit conversion
(bn ↔ 亿). Same count of headings, exhibits, tables and images. Render the Chinese files
to PDF and look at them; the Chinese summary must also fit 2 pages.

## Delivery

1. Write the four files to `Aircraft\output\` with the names above (create the folder if missing).
2. Write back `_charts\series.json`, `_charts\comp_series.json` and any new pipeline file.
3. Write `input\<RQ>\_charts_snapshot\`: zip of the signed PNGs, signed ledger copy,
   `APPROVED_<RQ>.json`, `REVIEW_<RQ>.md`, and `sources_ledger_<RQ>.md` (every exhibit,
   every web-sourced figure with its URL, every out-of-ledger number with its source).
4. Tell the user in a few lines: the four file names, the missing inputs and the exhibits
   and sections dropped because of them, cells still `n.d.`, series a broker stopped
   publishing, and which watch-list triggers fired.

## When the user says "no need to re-extract"

Rebuild charts from the existing ledger and continue, provided the data periods in `meta`
are unchanged and the ledger has no empty required slot. Regenerated PNGs void the old
sign-off - re-issue the review sheet and get a new signature. If the user says "charts are
fine, only redo the text", verify the sign-off hashes and go straight to phase two.

## Mistakes not to make

1. Using an issued report (any version) as a data source or placeholder - above all for
   the Fund Update when the GP update is not in the folder.
2. Writing prose, summary or translation before a valid sign-off.
3. Naming files by the data period instead of `RQ`, or quoting a monthly reading without
   its month.
4. Leaving "n/a - baseline quarter" in a Δ QoQ cell when the ledger holds the prior value.
5. Presenting broker-relayed data as the broker's own (IBA, Cirium, TSA, IATA), or mixing
   GS / Barclays / IATA traffic readings as if they were one series.
6. Turning a qualitative source statement into a number, or an estimate into a fact.
7. Comparing bases that differ without saying so: GP gross investment-level performance
   versus PitchBook net fund-level figures; DPI on gross invested capital versus on
   contributions; company-reported lease rate factor versus JPM's lease yield.
8. Quoting fund-level IRR / MoM while the Fund is under 50% called.
9. Autoscaling a frozen axis, moving a legend between quarters, or changing palette order.
10. Translating numbers loosely in Chinese (billion / 亿 slips, bp written as %).
11. Letting the summary introduce a number or judgement that is not in the full report.
12. Concluding "the source does not have it" after checking one page - search every broker
    PDF in the folder first and record what was searched.