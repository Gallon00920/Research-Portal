# Macro — broker registry

All brokers configured for the Macro section. Process only those uploaded this week.

---

## GS

- **Report identifier**: filename like `Global Economics Wrap-Up_ {Month Day, Year}.pdf`
  (e.g. `Global_Economics_Wrap-Up__June_12__2026.pdf`); report title on page 1 reads
  "Global Economics Wrap-Up". **Logo cue**: the **Goldman Sachs** stacked serif logotype
  ("Goldman" over "Sachs") next to the word **"Research"** at the top-left of page 1.
  Note: GS also publishes the *Global Credit Trader* (Credit section) under the same logo —
  disambiguate the two by the series title, not the logo (this one is "Global Economics
  Wrap-Up"; the credit one is "GLOBAL CREDIT TRADER").
- **Display name**: `GS`
- **Targets**:
  - **US Economics section** — type: `text-summary`
    - locate: find the **"US Economics"** heading. The section runs from there until the
      next top-level section heading (**"Europe Economics"**). In a typical issue it spans
      pages 1–2, starting at "Core CPI increased …".
    - output: condense the entire US Economics section into **6–10 atomic English bullets**,
      one theme per bullet, sitting **directly under "GS"** (no "US Economics" sub-heading
      bullet). Preserve key figures; compact notation (m/m, y/y, bp, pp, +/−). Typical themes
      to expect in this report: the CPI print, CPI internals/drivers, rent & OER, the Fed
      rate-path call, the labor-market driver behind it, terminal rate & hike risk, and any
      special swing factor (e.g. one-off events affecting near-term data) with its estimated
      impacts.
    - ignore: all other sections — Global Economics, Europe Economics, Asia/EM Economics,
      the GDP Forecast Tracker, and the Disclosure Appendix.

---

## MS

- **Report identifier**: recognize primarily by the **cover**, page 1. **Logo cue**: the
  **Morgan Stanley** logo (the stacked black wordmark, top-left) alongside the title
  **"US Economics Weekly | North America"**. Filename is a secondary
  cue: it looks like `UNITED_{YYYYMMDD}_{HHMM}.pdf` (e.g. `UNITED_20260612_0500.pdf`) and on
  its own does not reveal the broker or section, so the cover (logo + title) is the reliable signal.
- **Display name**: `MS`
- **Targets**:
  - **Key Takeaways** — type: `text-lift`
    - locate: page 1, the **"Key Takeaways"** box just under the summary abstract (typically
      ~5 bullets).
    - output: lift each Key Takeaway as its own bullet, **near-verbatim with only light
      tightening** — preserve figures, wording, and order; do not re-summarize or merge.
      Bullets sit directly under "MS".
    - ignore: everything else — the body sections (e.g. the Fed-call discussion, consumption,
      oil tracker, financial conditions, tariffs, GDP tracking), all exhibits/charts, the Data
      Review & Preview, the data calendar, the outlook/forecast tables, the scenario matrix,
      and the Disclosure Section.

---

## Barclays

- **Report identifier**: the filename **always begins with `Barclays_`**; the rest is that
  week's varying subtitle (e.g. `Barclays_US_Outlook_Seismic_jobs_data_shift_ground_under_r_debate.pdf`).
  **Logo cue**: the **Barclays** wordmark (with its spread-eagle device) at the top of page 1
  of the economics *US Outlook* series, headed "FICC Research / Economics".
- **Display name**: `Barclays`
- **Targets**:
  - **Page-1 summary bullets** — type: `text-summary`
    - locate: page 1 only, the bullet list **directly under the grey italic summary/abstract
      paragraph** (beneath the bold title). Typically ~3 bullets.
    - output: rewrite into the **GS `text-summary` style** — atomic English bullets, one idea
      each, preserve key figures, compact notation (m/m, y/y, bp, pp, +/−). Do NOT match GS's
      6–10 count: GS draws on a full section, whereas the source here is only the page-1
      summary, so expect roughly **3–5 bullets**. Bullets sit directly under "Barclays".
    - ignore: everything after the page-1 summary — the body discussion, all figures/charts,
      the GDP tracking, Data Review & Preview, the US Snapshot table, and the disclosures.

---

## JPM

- **Report identifier**: filename starts with `JPM_` and contains `US_Weekly_Prospects`
  (e.g. `JPM_US_Weekly_Prospects__2026-06-13_5321927.pdf`). **Logo cue**: the **J.P.Morgan**
  wordmark at the top of page 1, with the title **"US Weekly Prospects"** ("North America
  Economic Research").
- **Display name**: `JPM`
- **Targets**:
  - **Whole-report key points** — type: `text-summary` (judgment-based, not a fixed section)
    - locate: read the whole report and **decide what matters most**. Draw primarily from the
      lead **"United States"** section and **"US Focus"**, plus the most important one or two
      points from **"Global Data Watch"**. The rest of the document — the US Indicator
      forecasts table, the US economic calendar, the multi-page J.P. Morgan US forecast table,
      and the disclosures — is background/data, not material to summarize.
    - output: **5–6** GS-style atomic English bullets capturing JPM's most important calls.
      Prioritize the US macro view (Fed/policy, growth, inflation, labor) over granular
      data-preview detail; include a single compact global/central-bank bullet only if it's
      among the most important points. Rewrite in own words, preserve key figures, compact
      notation (m/m, y/y, bp, pp, +/−). **Keep each JPM bullet short and tight — one idea,
      about one line; don't chain multiple points together with dashes/semicolons.** Bullets
      sit directly under "JPM".
    - ignore: the per-indicator data previews and tables, the economic calendar, the full
      forecast table, and the disclosures.

---

<!-- Add further Macro brokers below, following the same schema. -->
