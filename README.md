# AID Research Panel

Live site: the GitHub Pages URL of the repository that hosts it (Settings → Pages).

Internal website that visualises AID quarterly research reports by sector.
Reports are uploaded as `.docx` or `.pdf`, parsed into structured content
(headings, paragraphs, lists, tables, figures) and displayed in a reader that
mirrors the AID Research Portal design. No database: every report lives as
files under `panel/data/reports/<id>/`. The same site also hosts the
**News tracker** and **Fund key factors** (see below); the three features
live in `panel/`, `news/` and `factors/`, and only the shared page shell is in
`web/`.

## Run

```bash
panel\run.bat
```

or

```bash
python -m pip install -r panel/requirements.txt
python panel/backend/server.py
```

Then open <http://127.0.0.1:8765>. Python 3.10+ is required.

## Features

- Only **full reports in the current report language** are listed. The
  English / 简体中文 switch in the top bar changes the interface language
  only; the EN / 中文 switch next to **Upload report** on a report page
  changes the report language (remembered across pages). Summaries are
  never listed, but the Full / Summary switch beside it opens the summary of
  the same sector, quarter and language when one exists. All three are flip
  switches: a click always jumps to the other option.
- **Dashboard** (`#/`): a card per sector (code, latest quarter, coverage,
  quarters available) and a right-hand panel with the 6 most recently
  uploaded reports in the current language from any sector. Sector names
  also form the bar at the top of every page.
- **Sector** (`#/s/<sector>`): opens the most recently uploaded report of
  that sector in the current language straight away (no card grid). If none
  exists you get a notice with an upload button and, when available, a link
  to the other-language version.
- **One edition per sector, quarter, type and language.** Uploading a report
  for a combination that already exists replaces the old one (the upload
  toast says so). A sector's report count is the number of quarters it
  covers: the English and Chinese editions, and the full report and
  summary, of one quarter count once.
- **Report page** (`#/r/<id>`): breadcrumb, **year and quarter pickers** to
  jump to another edition of the same sector, title with period badge,
  keywords, a **sticky toolbar** (exhibits, copy link, download source,
  print, edit, delete, back to top) that stays visible while scrolling,
  contents rail with scroll-spy, article body, an exhibit index in the right
  panel, and the full **exhibit index** at the end of the article. The
  header bar hides while scrolling down and returns on scroll up. The page
  uses the full window width.
- The **Exhibits** button opens the first exhibit full-size in the lightbox;
  ← → or the on-screen arrows step through all of them. The lightbox zooms
  (wheel, +/−, double-click) and pans by dragging. Tables are rendered as
  HTML tables in the article and also as PNG images (`images/tbl_NNN.png`)
  so they open in the lightbox like figures.
- Theme (light / dark / system) and UI language (English / 简体中文) switches
  on every page; both are remembered in the browser.
- **Manage sectors** (dashboard, or the ✎ next to the sector name on a
  report page): add, edit (names, code, region, English and Chinese coverage
  keywords), reorder by dragging rows (this sets the order in the top bar
  and on the dashboard) or remove sectors. Sectors are stored in `data/sectors.json`
  and can also be edited by hand.
- **Portfolio management** (`#/portfolio`): the same dashboard, sector
  pages, reader, upload and manage dialog, for the portfolio funds (Dyal V,
  OTF, Oak Street, … HSBC RCF) instead of the research sectors. The two
  are "spaces": every entry in `data/sectors.json` has a `space` field,
  `research` (the default when missing) or `portfolio`, and a report belongs
  to the space of its sector. Fund pages open at `#/portfolio/s/<id>`;
  report pages keep `#/r/<id>` in both spaces. Each dashboard lists and
  manages only its own space's sectors, and "Upload report" offers only
  them; the manage dialog adds new entries to the space it was opened from
  and leaves the other space's part of the file untouched. Reports are
  stored, parsed and built exactly as research reports.

## Parsing

- `panel/backend/parsers/docx_parser.py` walks the Word body in order: heading
  styles (English or Chinese style names) become headings, and so do
  manually formatted headings (bold, short, larger font) because the AID
  reports use the Normal style throughout. The masthead lines at the top
  ("JUNSON Capital Research", the title, "Coverage: …\tdate") are lifted
  into metadata, and the coverage line supplies the default keywords.
  Numbered or bulleted paragraphs (including literal "•" bullets) become
  lists, inline images are extracted to `images/`, data tables become row
  arrays, 1×2 tables holding figures become side-by-side layout blocks,
  and 1×1 tables become callouts. Paragraphs that look like captions
  ("Exhibit 3:", "图 3：", "Table 1", "表 2") are attached to the adjacent
  figure or table, and "Source:/Note:/资料来源：/注：" lines become notes.
  Exhibits keep the document's own labels ("Exhibit 12", "图3"); those
  without a caption borrow the nearest heading in the index.
- `panel/backend/parsers/pdf_parser.py` (PyMuPDF) extracts text blocks, detects
  headings by font size, finds tables with `find_tables()` and renders
  embedded images and vector charts to PNG.
- Every figure/table is numbered in document order; the list is returned as
  `exhibits` and drives the gallery, the side index and the index at the
  end of the article.
- Keywords come from the upload form, else from the document properties,
  else a simple frequency extraction.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/sectors` | sectors with report counts and periods |
| POST / PUT / DELETE | `/api/sectors[/{id}]` | manage sectors |
| PUT | `/api/sectors-order` | `{"order": [ids]}` sets the sector order |
| GET | `/api/reports?sector=&year=&quarter=&period_from=&period_to=&nature=&language=&q=` | report cards |
| GET | `/api/reports/recent?limit=6` | latest uploads |
| GET | `/api/reports/{id}` | metadata + parsed content |
| PUT / DELETE | `/api/reports/{id}` | edit metadata / remove |
| POST | `/api/reports/{id}/reparse` | re-run the parser on the stored source |
| GET | `/api/reports/{id}/images/{name}` | extracted figure |
| GET | `/api/reports/{id}/source` | original upload |
| POST | `/api/upload` | multipart: file, sector, year, quarter, nature, language, title, keywords |

## Hosting on GitHub (GitHub Pages + Actions)

GitHub is the host: the site is served by GitHub Pages and the Python
parser runs inside a GitHub Actions workflow
(`.github/workflows/build-deploy.yml`). The site is open: no password,
and every parsed report (metadata, content, images and the original file)
is committed to the repository in plain form under `panel/data/reports/`.

### One-time setup

1. Push the repository and let the workflow run once. The URL appears under
   **Settings → Pages** (`https://<owner>.github.io/<repository>/`).
   A private repository can use Pages only on GitHub Pro / Team /
   Enterprise; on a free account make the repository public.
2. Everyone who will **upload or edit** from the site needs a GitHub
   fine-grained personal access token limited to this repository with
   *Contents: Read and write* (GitHub → Settings → Developer settings →
   Personal access tokens → Fine-grained). The site asks for it the first
   time and keeps it in that browser only (top bar → **GitHub token**).
   Reading needs nothing.

### How changes flow

- **Upload** on the site commits the file to `panel/incoming/<id>.<ext>` plus
  a small sidecar with sector, quarter, language, title and keywords.
- **Edit / delete report** and **sector changes** commit small files to
  `panel/ops/` or `panel/data/sectors.json`.
- Every push runs the workflow: it parses new uploads, applies the ops,
  writes `panel/data/reports/<id>/` (meta, content, images, original),
  rebuilds `panel/data/index.json`, commits the result back with
  `[skip ci]`, and deploys the `site/` folder to Pages. Allow about two
  minutes, then refresh.
- `.\panel\publish.ps1` pushes reports that were parsed on a laptop with
  the local server.

### Optional password

Setting a `PANEL_PASSWORD` repository secret switches the whole pipeline
to encrypted files (AES-256-GCM, PBKDF2 key): the site then asks for the
password and decrypts in the browser, and nothing readable is committed.
Run `.\panel\publish.ps1` with the same password afterwards.

### Local use

`python panel/backend/server.py` still works as before with the files in
`panel/data/reports/`.

## News tracker

The "News tracker" tab (`#/news`) is the AID Credit News Radar, merged into
this repository from `Credit_bearing_news_updater`. Everything it needs is
under `news/`:

- `news/scripts/update_news.py` fetches Google News / publisher feeds for the
  monitored institutions, classifies and scores each item with Claude (and
  optionally a ColBERT model), translates it, and appends it to
  `news/data/news.json`. `news/README.md` and `news/docs/news_methodology.md`
  describe the method; `news/config/news_sources.json` holds the sources,
  aliases and weights.
- `.github/workflows/update-news.yml` runs that script every hour (or on
  demand with the "Refresh news" button in the tab), commits the new data and
  dispatches `build-deploy.yml` so GitHub Pages serves it. It needs two
  repository secrets: `ANTHROPIC_API_KEY` (required) and `HF_TOKEN`
  (optional, for the ColBERT model download).
- The page reads `data/news.json`: locally `panel/backend/server.py` serves
  `news/data/news.json` at that path, and `build_static.py` copies it into
  `site/data/` for the static site. Scores are fixed at retrieval; filters,
  weights and the summary run in the browser (`news/web/news.js`,
  `news/web/news.css`).

Run it locally with `python news/scripts/update_news.py --recent-days 3`
(`--dry-run` to preview). The "Refresh news" button asks for a fine-grained
token with *Actions: read and write* on this repository; it is kept in the
browser only.

## Fund key factors

The "Fund key factors" tab (`#/factors`) shows two monthly sub-tabs, one month
on screen at a time:

- **Fund performance**: the fund performance table, drawn as a real table
  (sticky header, completion shading, IRR column).
- **Budget completion**: the budget completion slide, drawn as real charts
  (budget against actual, stacked monthly parts, the slide's commentary).

Nothing is typed in by hand. You upload an **image** of the month's slide or
table (PNG, JPEG or WebP; drop, choose or paste a screenshot), pick the
sub-tab, year and month it belongs to, and Claude reads the image into data.
The page then draws it. The year and month pickers at the top choose which
month is shown; an upload for a month that already has data replaces it.

- `factors/scripts/extract_factors.py` sends the image to the Claude API
  (`claude-opus-5-5` by default, `FACTORS_MODEL` to change it) with a fixed
  JSON shape, parses the numbers and checks the arithmetic: every amount
  column against the total row, every stacked bar against its parts. Anything
  that does not add up is saved as a warning and shown above the chart or
  table, together with a link to the uploaded image, so a misread figure is
  easy to spot. It writes `factors/data/<tab>/<YYYY-MM>.json`, keeps the
  image beside it, and rebuilds `factors/data/index.json`.
- **On GitHub Pages** the site commits the image to
  `factors/incoming/<tab>-<YYYY>-<MM>.<ext>`; `build-deploy.yml` runs the
  script, commits the data and redeploys (about three minutes). It needs the
  `ANTHROPIC_API_KEY` repository secret, the same one the news job uses.
  Without it the upload waits in `factors/incoming/`. An image Claude cannot
  read is moved to `factors/failed/` with the reason.
- **Locally** `POST /api/factors/upload` runs the same script at once; start
  the server with `ANTHROPIC_API_KEY` set and
  `pip install -r factors/requirements.txt`.
- The data is served at `data/factors/…` in both modes. It has no encrypted
  form: a site built with `PANEL_PASSWORD` leaves it out.

**Parts without a number.** A stacked bar can show a part that is labelled by
month and source but has no figure of its own, for example "同4月收息" (the
same as April). Claude is told to list such a part with an empty value, and
the script keeps it: its size is what is left of the bar after the numbered
parts, and it is marked `derived`. The stack then adds up, so no warning is
raised. On the page the part is drawn and labelled as on the slide, without
a number beside the bar; the tooltip and the numbers table give the derived
amount, marked "derived". If several parts of one bar lack a number, the
remainder is split equally and a warning says so. Parts are coloured by
month ("6月收息" and "6月流入" share June's colour). The colours are assigned
once for the whole month's report, so the same colour is the same month in
every chart of every panel, and one legend at the top of the page lists the
months. Beside a bar each part therefore shows only its figure, plus the
source word when the slide has one ("收息 78万"; "同4月收息" keeps its
wording); the month is told by the colour. The tooltip and the numbers table
keep the full labels. `extract_factors.py --recheck` re-runs these checks on
saved months.

**English version.** The slides are usually Chinese. Right after an image is
read, a second Claude call translates its labels and commentary (titles,
column headers, bar labels, legend entries, notes, footnotes) into English.
The translations are stored in the month's file as `en`, a map from the
original text to its English; the original is never changed. With the
interface in English the page shows the English, with it in Chinese the
original. Amounts printed in 万 are shown in millions in English (731万
becomes 7.31M), matching the translated unit in the panel title, and the
translator converts amounts inside sentences the same way. A translated
sentence is only accepted if its figures match the original: every
percentage must reappear, and every 万 amount must reappear divided by 100;
otherwise the original sentence is kept. If an answer leaves items out, they
are asked for once more. If the translation call fails, the
month is still saved in its original language and is translated on a later
run. `extract_factors.py --translate` translates every saved month that
still shows Chinese (the workflow does this on each run); on the local
server, a month without English shows a "Create English labels" link at the
bottom when the interface is in English.

**Wrong date.** If an image was uploaded under the wrong year or month, use
"Change date" at the bottom of that month's page: the data, its notes and
the image move to the date you pick. A month that already has data is only
overwritten if you tick "Replace". Locally it is applied at once
(`POST /api/factors/<tab>/<YYYY-MM>/move`); on GitHub Pages the page commits
`factors/incoming/<tab>-<YYYY>-<MM>.move.json` and the workflow applies it,
before reading any new image. From a terminal:
`extract_factors.py --move-to 2026-09 --tab performance --year 2026 --month 8`.

**Hidden projects in the budget total.** The fund performance table's total row
includes new projects that the table itself does not list, so the budget
column never adds up. `factors/config.json` names those projects and their
budgets (currently New - Fund1 120,000 and New - Fund2 200,000). On every
upload, when the budget total exceeds the sum of the rows by exactly the sum
of those budgets, the script writes a note naming them (`auto_notes`) instead
of a warning. Any other gap, in this or another column, is still a warning.
When the projects or amounts change, edit the list and run
`extract_factors.py --recheck` to apply it to the months already saved; an
empty list turns the rule off.

**Notes.** A month can carry a note, shown in a blue "Note" box above the chart
or table: use it to explain a figure, for example a total that includes rows
the source table hides. Write it on the page: "Explain with a note" in the
warning box, or "Add a note" / "Edit note" at the bottom. In the dialog you
also tick the warnings the note explains; those are then hidden on the page
but stay in the data file (`warnings`, with the explained ones repeated in
`dismissed`), so the record of what the checks found is kept. A new upload
for the same month keeps the note, and keeps a warning hidden only if the new
reading raises exactly the same warning. Locally the note is saved at once
(`PUT /api/factors/<tab>/<YYYY-MM>/notes`); on GitHub Pages the page commits
the month's data file and the site rebuilds. From a terminal:
`extract_factors.py --note "…" --explains-warnings --tab … --year … --month …`.

To enter a month without Claude, write the JSON by hand in the shape Claude
returns and run `extract_factors.py --from-raw file.json --tab … --year …
--month …`; the same checks apply.

## Layout

One folder per feature; the frontend files of all four folders are served
(and built into `site/`) as one flat tree, so `index.html` references
`app.js`, `news.js`, `factors.js` etc. without folder prefixes.

```
web/                         shared shell: index.html (every view's markup), app.css
                             (design system), config.js
panel/                       the research panel
  backend/server.py          FastAPI app + static hosting (+ /data/news.json, /data/factors/)
  backend/build_static.py    parses uploads, applies ops, builds site/ for Pages
  backend/parsers/           docx / pdf parsers and shared helpers
  web/app.js, i18n.js        routing, rendering, UI strings (en / cn)
  web/static_data.js         static-mode data layer (GitHub Pages + Contents API)
  data/sectors.json          sector registry (created on first run)
  data/reports/<id>/         meta.json, content.json, images/, source.<ext>
  incoming/, ops/            uploads and edits waiting for the build workflow
  requirements.txt, run.bat, publish.ps1
news/                        the News tracker
  web/news.js, news.css      the view (module + scoped styles)
  scripts/, config/, docs/   news updater pipeline, its sources / weights, method
  data/news.json             news data (committed hourly by update-news.yml)
factors/                     Fund key factors
  web/factors.js, factors.css  the view: sub-tabs, month picker, charts, table, upload
  scripts/extract_factors.py   image -> Claude -> checked data
  data/<tab>/<YYYY-MM>.json    one month of data (+ the uploaded image); data/index.json
  incoming/, failed/           uploads waiting for, or rejected by, the build workflow
.github/workflows/           build-deploy.yml (panel + factors) and update-news.yml (news)
```

Design reference: the AID Research Portal pages (`AID_Portal_Demo_DT.html`
and `AID_Research_Portal_存档版_2026Q3.html`) in Xiyang Zhao's OneDrive.
