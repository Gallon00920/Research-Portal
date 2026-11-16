# Private Credit — section rule

Unlike Macro and Credit (which use a per-broker registry with fixed filename patterns and
fixed sections to pull), the Private Credit section uses **one generic, source-agnostic rule**
that applies to ANY private-credit report uploaded this week. Few reports — sometimes none —
are uploaded here each week; process whatever shows up.

The Private Credit section has **two parts**, each independent:
1. **Uploaded reports** — summarized per the per-report procedure below (run only on what was uploaded).
2. **Weekly news scan** — a web search for recent private-credit news (see "Weekly news scan" below); it runs **every week regardless of uploads**.
Include whichever parts have content this week. **Omit the whole Private Credit section only if
BOTH parts are empty** (no PC report uploaded AND no qualifying news in the window).

Render exactly like the other sections: each source is a **first-level bullet** (its display
name), with the extracted **key bullets** as sub-bullets beneath it. Follow all the global
formatting rules in `SKILL.md` (English; key figures preserved; compact notation m/m, y/y,
q/q, bp, pp, +/−; no section-name sub-heading bullets inside a source).

## Per-report procedure

For each uploaded private-credit report, in order:

1. **Identify the source by the page-1 logo.** Recognize the firm from its **logo / wordmark
   at the top of page 1** — this is the primary signal here, because private-credit reports
   come from many issuers and their filenames are not predictable. Examples of logo cues:
   the **Goldman Sachs** stacked serif logotype, the **Morgan Stanley** stacked wordmark, the
   **J.P.Morgan** wordmark, the **Barclays** spread-eagle wordmark, or a specialist provider's
   logo (e.g. a direct-lending index / BDC-tracker / ratings-agency house style). The
   **display name** is that firm's short name (e.g. `GS`, `MS`, `JPM`, `Barclays`, or the
   provider's name). If the logo is missing or ambiguous, fall back to the page-1 title /
   issuer line; if it is still unclear which firm it is, surface it to the user and ask rather
   than guessing.

2. **Decide what to summarize — executive summary vs. whole report.** Check whether the report
   has an **executive summary**: a clearly labelled summary up front — e.g. a section or box
   titled **"Executive Summary"**, **"Summary"**, **"Key Takeaways"**, **"Highlights"**, or a
   boxed abstract on page 1.
   - **If it HAS one** → summarize **only that executive summary** into key bullets. Do not
     mine the body.
   - **If it does NOT** → read the **whole report** and summarize it into key bullets
     (judgment-based: capture the main findings/views and the key data; skip data-dump tables,
     methodology, and disclosures).

3. **Write the key bullets in the same style as Macro.** Use the **`text-summary` style from
   `macro.md`** (the "GS-style" bullets): **atomic English bullets, one idea per bullet**,
   each **clear and self-contained** (spelled out, not chained together with dashes/semicolons),
   preserving key figures and compact notation (m/m, y/y, q/q, bp, pp, +/−). Rewrite in your
   own words. **Let the count scale to how much you're summarizing**, exactly as in `macro.md`:
   a short executive summary → roughly **3–5** bullets (cf. Barclays' page-1 summary); a whole
   report → roughly **5–10** bullets (cf. GS's full section / JPM's whole-report judgment).
   Bullets sit directly under the source's display name. **Write the bullets in English** even
   if the report or the chat is in another language (per the output-language rule in `SKILL.md`).

## Weekly news scan (past 7 days)

In addition to any uploaded reports, run a web search each week for recent **private-credit
news** and render the qualifying items as extra first-level bullets in the Private Credit
section (placed **after** the uploaded-report broker bullets).

**What to search.** Query for private-credit / direct-lending / BDC news (e.g. "private credit",
"direct lending", "BDC redemptions", "private credit default", plus notable managers like
Blackstone/Apollo/Ares/Blue Owl/HPS when relevant). Run a few queries to get good coverage.

**Sources.** Prioritize **Yahoo Finance and Reuters**, but **other mainstream financial outlets
are allowed** (e.g. Bloomberg — usually paywalled, CNBC, PitchBook/LCD, InvestmentNews, Markets
Group, plus Reuters syndications on investing.com / marketscreener). **Avoid** low-quality/SEO
sites, forums, and pure promotional press-release wires unless genuinely newsworthy.

**Time window — strict 7 days.** Include ONLY items published within the **past 7 days** relative
to the update's coverage date. Items outside the window are excluded even if highly relevant
(e.g. a Reuters piece from 9 days ago does NOT qualify). **If nothing qualifies, omit the news
part entirely** — no placeholder, no "no news this week" note.

**Count — max 5.** Cap at **5 items**. If more qualify, keep the 5 most material/representative.
**De-duplicate**: when several outlets cover the same story, render it once (prefer the most
original/authoritative source) — don't list the same event five times.

**Format (matches the broker bullets).** Each news item is a **first-level bullet** = a **one-
sentence summary** of the news (the same level as a broker like GS/MS), ending with a
**`*[Source, date]*`** tag. Beneath it, **sub-bullets** summarize the content in the **same
macro-style** as everything else (atomic, one idea each, key figures, compact notation), usually
**2–3 sub-bullets**. Everything in **English** (per `SKILL.md`).

**Copyright (strict).** Paraphrase in your own words. **At most one short quote (< 15 words) per
source**, in quotes; **never** reproduce article paragraphs or stack multiple quotes; never
reconstruct an article. Keep the source attribution so the item is traceable.

**Full text often unavailable.** Reuters/Yahoo and especially Bloomberg frequently block full
text (paywall / anti-scrape). **Summarize from the accessible search snippet or lede** when the
body can't be fetched — do not force full-text retrieval, and don't fabricate detail beyond what
the snippet supports. Use the actual current date to define the 7-day window and when forming
search queries (don't hard-code a year that makes results stale).

## Ordering & notes

- If more than one private-credit report is uploaded in a week, list the sources in the order
  uploaded (or grouped sensibly by firm); there is no fixed registry order for this section.
- Always ignore the per-recipient **"for the exclusive use of …" watermark** and the page
  header/footer; never reproduce them.
- This generic rule is the default. If a particular private-credit source later needs special
  handling (e.g. a specific index table/chart that should always be embedded as an `image`,
  or a fixed must-keep section), add a per-source override entry below using the registry-entry
  schema from `SKILL.md`, and it takes precedence over the generic rule for that source.

<!-- Per-source overrides (optional) go below, following the SKILL.md registry-entry schema. -->
