---
name: weekly-market-update
description: >
  Build the user's Weekly Market Update — a Word (.docx) document, written in English,
  organized into three sections: Macro, Credit, and Private Credit. Each week the user
  uploads broker research PDFs; this skill extracts the pre-defined parts of each broker's
  report and lays them out as bullets under that broker. Use this skill WHENEVER the user
  uploads one or more broker/sell-side research PDFs and asks to "do the weekly market
  update", "do the weekly update", "write the weekly", summarize broker reports into
  Macro/Credit/Private Credit, or anything that looks like the recurring weekly research
  digest — even if they only upload a subset of the usual brokers, even if they refer to it
  loosely with different capitalization or spacing, and even if they don't say "skill".
---

# Weekly Market Update

Produce the recurring weekly research update as an English Word document. The update has
three fixed sections — **Macro**, **Credit**, **Private Credit** — and under each section,
every broker appears as a first-level bullet, with the extracted content as sub-bullets.

## Core design: full registry, partial upload

There are two layers, and the split is the whole point of this skill:

1. **Registry (the full set).** Every broker we have ever configured lives in the
   per-section reference files under `references/`. The registry encodes ALL brokers and
   exactly what to pull from each. It does not change week to week.
2. **Runtime (the weekly subset).** Each week the user uploads only some of those brokers.
   Process only the files that were actually uploaded this week. A broker that is configured
   in the registry but not uploaded this week is simply **omitted** — no placeholder, no
   error, no "report not provided" note.

So: code/configure for everyone; render only who showed up.

## Weekly workflow

1. **Inventory the uploads.** List the files in `/mnt/user-data/uploads/`. Every file the
   user mentions is also on disk there.
   - **Handle archives first.** If the uploads contain one or more `.zip` (or `.tar`/`.tgz`)
     archives, extract them into a working dir (e.g. `unzip -o '/mnt/user-data/uploads/*.zip'
     -d /tmp/reports`) and then inventory the **extracted PDFs** instead. Bundle PDFs may sit in
     subfolders, so search recursively (`find … -name '*.pdf'`). Process the extracted PDFs
     exactly as if they had been uploaded individually.
   - **Recommended upload method (avoids the chat image limit).** Claude.ai renders every page
     of an uploaded PDF as an image for vision, and a chat has a small per-chat image cap, so a
     batch of several multi-page reports can be rejected at upload time ("exceeds the maximum
     image count"). This skill reads PDFs from disk with `pdftotext`/`pdftoppm`/`pdfplumber` and
     does NOT need the page-images, so tell the user to **upload the week's reports as a single
     `.zip`**: archives are stored as files on disk and are NOT rendered as page-images, which
     bypasses the cap (and collapses many files into one). Loose PDFs still work for small
     batches; the zip is the fix when the batch is large.
2. **Read the registry.** Load the relevant section reference file(s):
   - `references/macro.md`
   - `references/credit.md`
   - `references/private_credit.md` *(a generic, source-agnostic rule — not a per-broker
     registry; see that file: identify the source by page-1 logo, then summarize its
     executive summary if it has one, else the whole report, into macro-style key bullets.
     It also defines a weekly web-search NEWS SCAN — past 7 days, ≤5 items — rendered as
     extra first-level bullets in the section)*
3. **Match each uploaded PDF to a registry entry.** Match primarily by the **filename
   pattern** in the entry; confirm with the **report title** on page 1 of the PDF if the
   filename is ambiguous. If an uploaded file matches no entry, do not guess — surface it to
   the user and ask which broker/section it is (and whether to add it to the registry).
4. **Extract per the entry's targets.** For each matched report, work through that entry's
   target list. For each target:
   - `text-summary` → read the specified section (see "Reading PDFs" below) and summarize it
     into bullets exactly as the entry specifies (count, granularity, style).
   - `text-lift` → reproduce the source's own bullets near-verbatim, applying only light
     tightening. Keep one output bullet per source bullet, in the original order; preserve all
     figures and the analyst's meaning. Do NOT re-summarize, merge, reorder, or re-explain.
     (Use when the user wants the broker's stated takeaways lifted, not reworded.)
   - `image` → extract the specified chart/figure and embed it under the broker.
   Follow the entry's locator and style instructions precisely — they are tuned to that
   broker's report and are meant to reproduce identically each week.
5. **Assemble the document** in the fixed structure (below), placing each broker under its
   section in registry order, skipping un-uploaded brokers.
6. **Output as .docx.** Build the Word file by consulting `/mnt/skills/public/docx/SKILL.md`.
   Save to `/mnt/user-data/outputs/` and present it.

## Reading PDFs

Broker reports are PDFs. Consult `/mnt/skills/public/pdf-reading/SKILL.md` for the right
approach. In short:
- For `text-summary` targets, text extraction is enough (`pdftotext` / pypdf). Locate the
  target section by its heading; it runs until the next top-level heading.
- For `image` targets, the chart is usually vector-drawn — rasterize the page with
  `pdftoppm` and crop/screenshot the figure rather than relying on `pdfimages`.
- Note: many broker PDFs carry a per-recipient watermark / "for the exclusive use of …"
  footer. Ignore it; never reproduce it in the output.

## Output document structure

ALWAYS use this exact skeleton. Section order is fixed. Within a section, brokers follow
registry order. Omit any section that has no uploaded brokers this week, and omit any broker
not uploaded.

```
Weekly Market Update {YYYYMM} Week{N}

## Macro
- {Broker display name}
  - {bullet}
  - {bullet}
- {next broker}
  - ...

## Credit
- {Broker display name}
  - ...

## Private Credit
- {Broker display name}
  - ...
```

Formatting rules:
- **Title** is `Weekly Market Update {YYYYMM} Week{N}`, where:
  - `{YYYYMM}` = the year and month the update covers (e.g. June 2026 → `202606`).
  - `{N}` = the week of the month the update covers, using natural weeks that run
    **Monday–Sunday**. Week 1 is the Mon–Sun week that contains the 1st of the month (so if
    the month starts mid-week, those first few days still count as Week 1); each following
    Monday begins the next week (Week 2, 3, …). A report's week number is whichever Mon–Sun
    block its date falls into. Example: June 2026 starts on a Monday, so Week 1 = Jun 1–7 and
    a June 12 report falls in Week 2 → `Weekly Market Update 202606 Week2`. Derive the date
    from the uploaded reports (use the primary report's publication date); if uploads
    disagree or are ambiguous, ask the user which week it is rather than guessing.
- This is the document's top title (not a section heading). It is also the output filename:
  `Weekly Market Update {YYYYMM} Week{N}.docx`.
- **Output language is ALWAYS English.** Every part of the deliverable — the title, all
  bullets, image captions, and any notes — must be written in English, **regardless of the
  language the user is chatting in or the language of their request/instructions, and
  regardless of the source report's language**. The user may write to you in Chinese (or any
  other language); the chat reply can match their language, but the **document content and any
  rendered preview of that content are always in English**. Never translate the output into
  the conversation language. Source reports may be in another language — translate their
  content into English for the bullets.
- Broker display name is the first-level bullet; extracted content sits one level beneath it.
- **No section-name sub-headings inside a broker** (e.g. don't print "US Economics" as a
  bullet) unless an entry explicitly asks for one — bullets sit directly under the broker.
- Preserve key figures. Use compact notation: m/m, y/y, q/q, bp, pp, +/−.

## Registry entry schema

Each broker entry in a section reference file follows this shape, so new brokers stay
consistent:

```
## {Broker display name}
- **Report identifier**: filename pattern (and/or report title on page 1) used to recognize
  this broker's report.
- **Targets**: ordered list. Each target has:
  - name — what it is (for our reference only; not printed unless stated)
  - type — `text-summary`, `text-lift`, or `image`
  - locate — how to find it in the PDF (heading text, page, figure caption, etc.)
  - output — exactly what to produce (bullet count/range, granularity, style; or for images,
    whether to keep the caption)
  - ignore — anything in the report to explicitly skip
```

See `references/macro.md` for the worked example (GS).
