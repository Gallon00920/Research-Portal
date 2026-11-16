# Credit — broker registry

All brokers configured for the Credit section. Process only those uploaded this week.
Same conventions as `macro.md`: match by filename pattern, confirm by page-1 title + logo,
render each broker as a first-level bullet with extracted content beneath it.

---

## GS

- **Report identifier**: filename contains `Global_Credit_Trader` — pattern
  `Global Credit Trader__{subtitle}.pdf` (e.g.
  `Global_Credit_Trader__Credit_volatility__Positioning_for_normalization.pdf`); report title
  on page 1 reads **"GLOBAL CREDIT TRADER"** with that week's issue title beneath it, under the
  header **"Credit Strategy Research"**. **Logo cue**: the **Goldman Sachs** stacked serif
  logotype ("Goldman" over "Sachs") next to **"Research"** at the top-left of page 1 — the
  same logo as GS macro, so the logo alone does NOT disambiguate the two GS reports.
  **Disambiguate by series title**: this is "GLOBAL CREDIT TRADER" / "Credit Strategy
  Research" (Credit section); the macro one is "Global Economics Wrap-Up". If a GS file's
  series title is unclear, check page 1 before assigning a section.
- **Display name**: `GS`
- **Targets**:
  - **Executive summary** — type: `text-summary`
    - locate: **page 1 only**, the boxed executive summary. It is built from a small set of
      **bold mini-section headers**, each followed by source bullets — typically:
      "Better US data, higher US yields"; "Implications for our spread forecasts: …"; and
      "The 'left tail' … credit volatility" (headers vary week to week with the issue's theme).
      The same content is mirrored on the cover. Summarize the box; do NOT mine the body Q&A.
    - output: condense the executive summary into GS-style **atomic English bullets**, one
      theme per bullet, sitting **directly under "GS"** (no mini-section sub-heading bullets).
      Use the **same `text-summary` style as GS in `macro.md`** — preserve key figures, compact
      notation (bp, pp, m/m, y/y, q/q, +/−), and write each bullet **clear and self-contained**
      (one idea, spelled out — don't chain points together cryptically). **Focus on the
      US / USD view.** **Count: typically 3–4.** Themes to keep: (1) the **Fed rate-path** input
      (cut timing/number, plus unemployment & terminal-rate context and any flat-path caveat);
      (2) the **higher US Treasury yield "floor"**; (3) the **net change to the USD spread
      forecast** vs the prior baseline and the two drivers behind it; (4) the **residual USD
      directional spread call** and the "left-tail" risk behind it (e.g. commodity disruption).
      Enrich the US points with the page-2 body detail that elaborates the same theme (e.g. the
      exact unemployment / terminal-rate / 10y figures) — it's the same view, just fuller.
    - **Exclude (do NOT bullet):** the week's featured tactical theme/trade (e.g. a
      buy-credit-vol call and its 1m/3m-tenor mechanics) and the precise spread-target
      tables/numbers (the 4Q26 IG/HY targets etc.). **De-emphasize EUR** — mention it only in
      passing if it directly bears on the US view, otherwise omit. This is a US-focused digest
      of the credit *view*, not the report's trade idea.
  - **Relative value views table (Regional + USD market only)** — type: `image`
    - locate: the **"Forecast dashboard: Relative value views"** section, and within it the
      **FIRST figure under that section heading** — a "Relative value views" table. **Locate by
      the section heading + "first figure", NOT by exhibit number**: the exhibit number drifts
      week to week (it was "Exhibit 16" this issue), but it is always the first figure in this
      section. (It's a text table, not a chart, but treat it as an `image` target — rasterize
      and crop.)
    - crop: the table has three horizontal **bands labelled in the far-left column —
      `Regional`, `USD market`, `EUR market`, in that top-to-bottom order**, separated by
      heavier horizontal rules that span the full table width (the inner row dividers are
      narrower). **Capture only the top two bands — `Regional` and `USD market` — plus the
      table header** (the blue "Relative value views" bar, the "Corporate Credit" subheader) and
      the exhibit title line. **Drop the `EUR market` band entirely.** Because Regional and USD
      market are the top two contiguous bands, this is a single crop: from the top of the table
      down to the **band-separator rule between `USD market` and `EUR market`**.
    - method: rasterize the page with `pdftoppm` at ~300 DPI. Find the band-separator rules
      programmatically (e.g. pdfplumber `pg.rects`/`pg.lines`): the band separators are the
      wide rules that also extend across the left band-label column (≈ full-table-width),
      whereas intra-band row dividers start further right (under the views columns only). The
      bottom crop edge = the separator just below the last `USD market` row (the one
      immediately above the `EUR market` band). Left edge just inside the table box, right edge
      just past it.
    - ignore / never include: the per-recipient **"for the exclusive use of …" watermark**
      (rotated text in the far-left margin — keep the left crop edge to the right of it so it
      never appears) and the page header/footer.
    - output: embed the cropped image **under "GS"**, after the bullets.
  - **Performance table (USD markets only)** — type: `image`
    - locate: the **"Performance dashboard: Cash and synthetic markets"** section, and within
      it the **FIRST figure under that section heading** — a "Performance of USD and EUR
      markets" table. Again, **locate by section heading + "first figure", NOT by exhibit
      number** (it was "Exhibit 17" this issue; the number drifts week to week).
    - crop: the table opens with a **dark-blue header row** (the column labels — Market /
      Current: Spread, Yield / Total return: MTD, QTD, YTD / Spread change / Yield change),
      then stacks **USD** row-groups (USD Corporate bonds, USD Leveraged Loans, USD Securitized
      products, USD Macro indices/CDX) and **then the EUR** row-groups (EUR Corporate bonds
      onward, ending with the iTraxx indices). **Capture from the dark-blue header row down
      through the entire USD section — i.e. through the last `USD Macro indices` row (CDX HY) —
      and stop there. Drop everything from `EUR Corporate bonds` down (the whole EUR block).**
      Do NOT include the exhibit title line above the blue header (the title names "USD and EUR
      markets", which would misdescribe a USD-only crop); start at the dark-blue header row.
    - method: rasterize at ~300 DPI. The USD/EUR boundary is the row where the **first `EUR`
      group subheader** (`EUR Corporate bonds`) begins; set the bottom crop edge at the rule
      just **above** that subheader band (i.e. the bottom of the last `USD Macro indices` row).
      Find it via the grey group-subheader bands / separator rules (pdfplumber `rects`), not by
      a hardcoded pixel. Left/right edges just inside/outside the table box.
    - ignore / never include: the per-recipient watermark in the far-left margin (keep the left
      crop edge to its right) and the page header/footer.
    - output: embed the cropped image **under "GS"**, after the Relative-value-views image.
  - **CLO valuation — first two figures (side by side)** — type: `image`
    - locate: the **"Valuation dashboard: CLOs"** section, and within it the **FIRST TWO
      figures**, which sit side by side in the **top row** — a left "CLO spread percentile
      ranks" table and a right "CLO equity vs. CLO BB yield" chart (they were "Exhibit 45" and
      "Exhibit 46" this issue). **Locate by section heading + "first two figures / top row",
      NOT by exhibit number** (the numbers drift; the format/layout does not). Two more figures
      sit in the row below (this issue: Exhibit 47/48) — exclude them.
    - crop: the two top-row figures are **already laid out horizontally**, so this is a
      **single crop of the whole top row** — no stitching needed. Capture from the two exhibit
      **title lines** down through both figures **and their "Source:" notes**, stopping at the
      rule **above the second-row figure titles**. Span the full page text width so both the
      left and right figures are fully included.
    - method: rasterize at ~300 DPI. Top edge = just above the top-row exhibit titles; bottom
      edge = just below the top-row "Source:" lines and above the second row's exhibit titles
      (find the second-row title `top` via the text and cut above it). Left edge just left of
      the left figure, right edge at the page text-area margin.
    - ignore / never include: the per-recipient watermark in the far-left margin (keep the left
      crop edge to its right) and the page header/footer.
    - output: embed the single cropped image **under "GS"**, after the performance-table image.
    - ignore: the full body Q&A / deep-dive, the relative-value views table, ALL dashboards and
      exhibits (spreads, returns, issuance, defaults, ratings migration, vol charts, flows),
      and the Disclosure Appendix. Also ignore the per-recipient "for the exclusive use of …"
      watermark/footer — never reproduce it.

---

## MS

- **Report identifier**: recognize primarily by the **cover**, page 1. **Logo cue**: the
  **Morgan Stanley** logo (the stacked grey/black wordmark — on this report it sits at the
  **top-right** of page 1) alongside the series title **"Investment Grade Corporate Credit
  Dashboard"** (the part after the colon is that week's theme, e.g. ": Testing the Bull Case",
  and changes weekly — match on the stable series title, not the theme). Filename is a
  secondary, opaque cue: it looks like `ARSIGLE{YYYYMMDD}{digits}.pdf` (e.g.
  `ARSIGLE20260610162004820.pdf`) and on its own does not reveal the broker or section, so the
  cover (logo + title) is the reliable signal. **Disambiguate from MS macro by series title**:
  this is "Investment Grade Corporate Credit Dashboard" (Credit section); the macro one is
  "US Economics Weekly | North America". Same logo, different series title.
- **Display name**: `MS`
- **Targets**:
  - **Page-1 executive summary** — type: `text-lift`
    - locate: **page 1**, the bulleted executive summary directly under the title. Each bullet
      opens with a **bold category lead-in** — typically Valuations, AI Debt Financing Tracker,
      Supply, Ratings Migrations, Fund Flows (categories vary week to week). This is MS's
      equivalent of the macro "Key Takeaways" box.
    - output: **same `text-lift` treatment as MS in `macro.md`** — lift each summary bullet as
      its own bullet, **near-verbatim with only light tightening**, preserving the bold
      category lead-in, the figures, the wording, and the order; do NOT re-summarize, merge, or
      re-order. Bullets sit directly under "MS". (The whole report is US IG, so no
      US/EUR trimming is needed here.)
    - ignore: everything after page 1 — all the body slides/dashboards (spread & performance,
      valuation comparison, AI debt tracker, issuance, M&A pipeline, screens, ratings
      migrations, fund flows, curve dynamics, credit/equity screens, currency-hedged yields),
      the Valuation Methodology & Risks page, and the entire Disclosure Section.

---

## Barclays

- **Report identifier**: the filename **always begins with `Barclays_`** and, for this report,
  contains `US_Credit_Alpha` (e.g. `Barclays_US_Credit_Alpha_Overview.pdf`); report title on
  page 1 reads **"US Credit Alpha"** with **"Overview"** as the section header beneath it,
  under the header **"FICC Research / Credit Strategy"** (top-right of page 1), dated that week.
  **Logo cue**: the **Barclays** wordmark (with its spread-eagle device) at the top of page 1 —
  the **same logo as Barclays macro**, so the logo alone does NOT disambiguate the two Barclays
  reports. **Disambiguate by series title**: this is "US Credit Alpha" / "Overview" /
  "FICC Research → **Credit Strategy**" (Credit section); the macro one is "US Outlook" /
  "FICC Research → **Economics**". Same `Barclays_` filename prefix and same logo — tell them
  apart by the page-1 series title + the "Credit Strategy" vs "Economics" sub-header. If a
  Barclays file's series title is unclear, check page 1 before assigning a section.
- **Display name**: `Barclays`
- **Targets**:
  - **Overview** — type: `text-summary`
    - locate: the **"Overview"** section, which is the prose narrative spanning **pages 1–2**
      (it ends at the bottom of page 2, immediately before the Figure 1 / Figure 2 page). It is
      written as running paragraphs, several led by a **bold lead-in sentence** marking a theme
      shift (e.g. "Strong macro, limited spread upside"; the all-in-yield paragraph; the inflows
      paragraph; the AI-capex/supply paragraph). Read the whole Overview, not just page 1.
    - output: condense the Overview into the **GS `text-summary` style** — atomic English
      bullets, one theme each. **Keep each bullet SHORT: a single tight sentence (one idea),
      not a multi-sentence paragraph** — lead with the point, then only the few figures that
      carry it (drop the supporting narrative). Use compact notation (bp, pp, m/m, y/y, q/q,
      +/−). The whole report is **US / USD**, so no US/EUR
      trimming is needed. **Count: aim for 6 (range 5–7).** Themes to keep, in order: (1) credit sitting
      near the tights with unusually low spread vol (IG/HY ~unchanged w/w, tight 2-week ranges);
      (2) the strengthening macro backdrop (ISM, labor/ADP/JOLTS, payrolls expectation, surprise
      index); (3) the resulting **policy/inflation risk** — elevated prices-paid, oil, the jump
      in the implied 2026-hike probability, and the "wider spreads + higher vol, not a full
      credit-cycle reset" conditional; (4) **demand anchored by all-in yield rather than spread**
      (IG/HY spread-vs-yield comparison to the prior tights, and the preferred curve point); (5)
      **record IG inflows**; (6) the **AI-capex financing shift** toward equity/hybrids/converts
      (Alphabet/Oracle) and its implication for IG supply/balance-sheet pressure (compress the
      single-name color — keep it as the structural credit-supply theme, not a name-by-name
      recap). Bullets sit **directly under "Barclays"** (no mini-header sub-bullets).
  - **Figures 1 & 2 (side-by-side row)** — type: `image`
    - locate: **page 3**, the **two figures laid out side by side in a single row** — Figure 1
      "Weekly index changes" (left, a small table: Corporate Index / CDX.IG / HY Index / CDX.HY
      × Wednesday Close / Last Week Close / 4-Week Average) and Figure 2 "Economic surprises
      index …" (right, a line chart). These are the **only two figures** in the Overview cut —
      capture **both**.
    - crop: they are **already laid out horizontally**, so this is a **single horizontal crop of
      the whole row** — no stitching. Capture from the **"FIGURE 1 / FIGURE 2" title lines** down
      through both figures **and their two "Source:" lines**, spanning the full page text width so
      both figures are fully included.
    - method: rasterize page 3 with `pdftoppm` at ~300 DPI. Find bounds with pdfplumber rather
      than hardcoding pixels: top edge just above the "FIGURE" title `top` (≈ 62pt on a 612×792
      page), bottom edge just below the lower "Source:" `bottom` (≈ 270pt), left edge just inside
      the text margin (≈ x 54pt), right edge just past the right figure (≈ x 552pt).
    - ignore / never include: the page header ("Barclays | US Credit Alpha"), the footer
      ("{date} … {page}"), and any per-recipient watermark.
    - output: embed the single cropped image **under "Barclays"**, after the bullets.
    - ignore (report-wide): everything else after the Overview — the entire analyst-certification
      / disclosures / disclaimer block (pages 4–7). Also ignore the cross-references to other
      sections of the full US Credit Alpha ("see this week's IG/HY section", "see …") — this
      upload is the Overview cut only. Never reproduce the per-recipient footer /
      "Restricted - External" line or the analysts' contact details.

---

## UBS

- **Report identifier**: recognize primarily by the **cover**, page 1. **Logo cue**: the **UBS**
  three-keys symbol + "UBS" wordmark at the **top-left** of page 1, with **"Global Research"**
  and the **"Powered by UBS Evidence Lab"** stamp, headed **"Global Strategy"**. Series title:
  the recurring monthly **"US/EU Credit Default and Recovery Rate Analysis"**, published as
  **"{Month} Default Report: …"** (e.g. "May Default Report: Global loan default count reaches
  post-2023 highs" — the part after "Default Report:" is that month's headline and changes
  monthly; match on the stable "… Default Report" / "Credit Default and Recovery Rate Analysis"
  series). Filename is a secondary, **opaque** cue: it looks like `ued{digits}.pdf` (e.g.
  `ued45520.pdf`) and on its own does not reveal the broker or section, so the cover
  (logo + series title) is the reliable signal — same approach as MS. (No UBS report is
  configured in other sections; if one is added later, disambiguate by series title.)
- **Display name**: `UBS`
- **Targets**:
  - **Page-1 executive summary** — type: `text-summary`
    - locate: **page 1**, the executive summary — a lead line naming the markets covered (US HY
      bonds, US LL, European HY, European LL, Private Credit) followed by **four numbered
      sections**: (1) the LL-vs-HY default bifurcation + three takeaways (high-frequency split,
      the private-market picture, fallen-angel/rising-star dormancy), (2) US HY, (3) US LL,
      (4) EU HY/LL. Read all four; the headline figures are mirrored in Figure 1.
    - output: **same short `text-summary` style as Barclays/GS in this file** — atomic English
      bullets, **one idea each, a single tight sentence** with only the key figures, compact
      notation (bp, pp, m/m, y/y, +/−). **Count: aim for 6 (range 5–7).** Themes to keep, in
      order: (1) the **headline** — global loan default count at post-2023 highs, LL defaults
      rising while HY stable; (2) the **high-frequency (3m) split** — US/EU LL jumping vs US/EU
      HY flat-to-down, plus the "short-lived stability / AI-disruption" caveat; (3) **US HY**
      LTM issuer/par/recovery + FY26 forecast; (4) **US LL** LTM issuer/par/recovery + FY26
      forecast (note the headline LTM rate masks the high-frequency upturn / record monthly
      count); (5) **Europe** — EU HY and EU LL LTM rates/recovery + FY26 forecasts; (6) the
      **private-credit + fallen-angel/rising-star** color. **Unlike GS, keep BOTH US and EU** —
      this report is fundamentally a US/EU default comparison, so do not drop the EU lines.
      Bullets sit **directly under "UBS"** (no numbered-section sub-bullets).
  - **Figures 1 & 2 (side-by-side row)** — type: `image`
    - locate: **page 2**, the **top-row pair laid out side by side** — Figure 1 "Current Default
      Statistics Summary" (left, a table: US HY / US LL / EU HY / EU LL × LTM issuer default /
      par default / recovery / default loss) and Figure 2 "We expect higher defaults in US and
      Europe for FY 2026 …" (right, a grouped bar chart: May'25 / Current / Baseline forecast).
      Capture **both**.
    - crop: they are **already laid out horizontally**, so this is a **single horizontal crop of
      the whole top row** — no stitching. Capture from the **"Figure 1 / Figure 2" title lines**
      down through both figures **and their two "Source:" lines**, spanning the full page text
      width so both are fully included. (Figures 3–6 begin the next row below — exclude them.)
    - method: rasterize page 2 with `pdftoppm` at ~300 DPI (note: this is an **A4** page,
      595×842 pt). Find bounds with pdfplumber: top edge just above the "Figure" title `top`
      (≈ 66pt), bottom edge just below the lower "Source:" `bottom` (≈ 290pt), left edge just
      inside the text margin (≈ x 45pt → cut at ~40pt), right edge just past the right figure
      (≈ x 550pt → cut at ~556pt).
    - ignore / never include: the page header ("Global Strategy {date} ab {page}") and footer,
      and any per-recipient watermark.
    - output: embed the single cropped image **under "UBS"**, after the bullets.
    - ignore (report-wide): everything else — Figures 3–39 (the per-market high-frequency,
      distressed-ratio, sector-price, CCC-share, fallen-angel/rising-star charts and the
      trailing-12m default/recovery charts), the issuer-default detail tables (Figures 24, 29,
      34, 39), the UBS Evidence Lab note, the Valuation Method & Risk statement, and the entire
      Required Disclosures / Global Research Disclaimer (pages 11–16). Never reproduce the
      analysts' contact details.

---

## BAML

- **Report identifier**: publisher is **BofA / BofA Securities** (Bank of America / Merrill
  Lynch — "BAML"). **Logo cue**: the **"BofA SECURITIES"** wordmark with its red flag/ribbon
  device at the **top-right** of page 1, and the **"BofA GLOBAL RESEARCH"** banner at the
  top-left; page 1 is headed **"US Fixed Income Strategy"** with the series title **"The US
  Fixed Income Weekly"** directly beneath it. Filename is a secondary cue: it looks like
  `The_US_Fixed_Income_Weekly*.pdf` (e.g. `The_US_Fixed_Income_Weekly.pdf`). **BAML publishes
  several weekly series under the same BofA Global Research / BofA Securities logo, so the logo
  alone does NOT disambiguate BAML's reports** — a different-theme BAML report may belong to a
  different section (or need its own entry). **Disambiguate by the page-1 series title**: this
  one is "The US Fixed Income Weekly" (Credit section). If a BAML file's series title is
  unclear, check page 1 before assigning a section. (Same principle as GS / Barclays / MS.)
- **Display name**: `BAML`
- **Targets**:
  - **Front-page summary** — type: `text-summary`
    - locate: the report's **front-page summary** — a stack of **bold sub-market section
      headers**, each followed by a short blurb. This issue's headers were **Economics**,
      **Rates**, **The Flow Show**, **Securitized Products**, **Investment Grade Credit**,
      **High Yield Credit**, **Municipals** (the set, order, and count vary week to week; some
      issues also carry EM / FX / other blocks). Each blurb is itself a **précis of the matching
      body section** later in the report. **Read ONLY this front-page summary** — do NOT use
      "The CIO Summary" (the prose overview on the page(s) right after it), and do NOT mine the
      body "Sector highlights", the exhibit/monitor tables, or the forecast tables. The summary
      usually fits on **page 1**, but in larger issues it can spill onto the next page — capture
      **all of it** wherever it runs.
    - output: produce **one atomic English bullet per summary sub-market**, in the report's own
      order, **covering every summary block with none omitted** — further condense each
      already-short blurb into its key point (a block may take **two** bullets only if it packs
      two genuinely distinct ideas). Each bullet **opens with its sub-market name as a bold
      lead-in** (e.g. `**Rates:**`, `**IG Credit:**`, `**HY Credit:**`) so every block is
      traceable and none is dropped — this is the explicit per-entry exception to the SKILL.md
      "no section-name sub-heading" rule (a lead-in on the content line, not a standalone
      heading bullet). Use the **same `text-summary` style as GS / Barclays in this file** — one
      idea per bullet, clear and self-contained, rewritten in your own words (do NOT lift
      verbatim), preserving key figures with compact notation (bp, pp, m/m, y/y, q/q, +/−). The
      bullet count scales to the number of summary blocks that week (this issue: 7). Bullets sit
      **directly under "BAML"**.
    - ignore: everything after the front-page summary — "The CIO Summary", the full body Sector
      highlights (Economics, Rates, Front end, Technicals, Securitized Products and its
      sub-sectors, IG, HY, Munis, EM, FX, The Flow Show), all exhibits/charts, the
      market-performance and cross-product pricing/risk-monitor tables, the Economics / Rates /
      Commodities forecast tables, the acronym glossaries, and the entire Disclosures /
      Research-Analysts block. Never reproduce the per-recipient "This report is intended for …"
      / "Unauthorized redistribution … prohibited" footer.

---

<!-- Add further Credit brokers below, following the same schema. -->
