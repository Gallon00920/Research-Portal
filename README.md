# AID Research Panel

Internal website that visualises AID quarterly research reports by sector.
Reports are uploaded as `.docx` or `.pdf`, parsed into structured content
(headings, paragraphs, lists, tables, figures) and displayed in a reader that
mirrors the AID Research Portal design. No database: every report lives as
files under `data/reports/<id>/`.

## Run

```bash
run.bat
```

or

```bash
python -m pip install -r requirements.txt
python backend/server.py
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

## Parsing

- `backend/parsers/docx_parser.py` walks the Word body in order: heading
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
- `backend/parsers/pdf_parser.py` (PyMuPDF) extracts text blocks, detects
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

## Deploying for a public URL

The app is a single Python process, so any container host works. A
`Dockerfile` and a Render blueprint (`render.yaml`) are included:

1. Push this repository to GitHub.
2. On <https://render.com> choose **New → Blueprint**, pick the repository,
   and when asked enter a `PANEL_PASSWORD` (the shared sign-in password).
   Render builds the Docker image, attaches a 5 GB disk at `data/reports`
   so uploads survive restarts, and gives you a
   `https://research-portal-….onrender.com` URL.
3. Share the URL and the password with the team. Everyone signs in on
   `/login.html`; the session cookie lasts 30 days and **Sign out** in the
   top bar ends it. Change the password in Render → Environment at any
   time (existing sessions stay valid until `SECRET_KEY` is also rotated).

Locally, `python backend/server.py` runs without a password unless you set
`PANEL_PASSWORD` in the environment first.

The uploaded reports are never committed to git (`data/reports/` is
ignored); they live only on the server's disk.

## Layout

```
backend/server.py          FastAPI app + static hosting of web/
backend/parsers/           docx / pdf parsers and shared helpers
web/index.html, app.css    page shell and design system
web/app.js, i18n.js        routing, rendering, UI strings (en / cn)
data/sectors.json          sector registry (created on first run)
data/reports/<id>/         meta.json, content.json, images/, source.<ext>
```

Design reference: the AID Research Portal pages (`AID_Portal_Demo_DT.html`
and `AID_Research_Portal_存档版_2026Q3.html`) in Xiyang Zhao's OneDrive.
