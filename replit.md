# Darklightz Lead Generator

A professional Windows desktop application that scrapes Google Maps for businesses without a dedicated real website (Instagram/Facebook/WhatsApp-only or no online presence), built by Darklightz Studio.

## Run & Operate

```bash
cd darklightz-leadgen
pip install -r requirements.txt
playwright install chromium
python main.py
```

- **Build Windows exe**: run `darklightz-leadgen/build.bat` (requires PyInstaller on Windows)
- **Database**: SQLite stored at `~/.darklightz/leads.db` — survives reinstalls and updates

## Stack

- Python 3.11+, PyQt6 (desktop GUI), Playwright (Chromium scraper)
- SQLite via built-in `sqlite3` — no external DB needed
- openpyxl (Excel export), reportlab (PDF export)
- PyInstaller (Windows .exe packaging)

## Where things live

```
darklightz-leadgen/
  main.py               — entry point
  requirements.txt      — Python dependencies
  backend/scraper.py    — Google Maps scraper (QThread worker)
  database/models.py    — SQLite schema + migrations
  database/operations.py— all DB read/write functions
  frontend/             — PyQt6 UI widgets (search, leads, export, settings, about)
  exports/              — Excel, CSV, PDF exporters
  utilities/helpers.py  — phone classification, WhatsApp links, email extraction
  utilities/updater.py  — GitHub Releases auto-update check
  assets/               — logo.png, icon.ico
```

## Architecture decisions

- **QThread scraper**: scraping runs in a background QThread; emits signals to the UI thread — never blocks the GUI
- **Lead Collections = Search Sessions**: every "Start Search" click creates a row in `searches`; the Leads page shows each session as a named collection
- **Cross-session duplicate detection**: `lead_exists_in_db()` checks the full DB (by maps URL → coordinates → name+phone) before counting a lead, so skipped duplicates never consume the requested lead count
- **WhatsApp only for confirmed mobiles**: Pakistani 03xx numbers only; landlines never get WhatsApp links
- **Schema migration**: `_migrate_leads_table()` adds v2.0 columns to existing v1 DBs without data loss

## Product

- Search Google Maps by keyword + city
- Collects only businesses without a real website (social-only or no presence)
- Captures: name, category, phone, mobile, WhatsApp, email, Instagram, Facebook, website, address, Maps URL, lat/lng, rating, reviews, opening hours
- Lead Collections view (per-search drill-down), status tracking, notes
- Export to Excel (.xlsx), CSV, PDF — per collection, not the whole database
- Auto-update via GitHub Releases

## User preferences

- DO NOT rebuild the app or change the architecture
- DO NOT replace working features
- Fix bugs and improve the existing project only
- Push completed code to the GitHub repository when ready (user will provide credentials)

## Gotchas

- Playwright Chromium must be installed separately: `playwright install chromium`
- On PyInstaller builds, `ms-playwright` folder must sit next to the `.exe` (handled by `build.bat`)
- Google Maps scraping may slow down or block on high request volume — the scroll delay setting in Settings helps
- `UNIQUE(name, phone, city)` constraint in the DB is a last-resort safety net; the cross-session `lead_exists_in_db()` check in the scraper catches dupes before they're counted

## Pointers

- See the `pnpm-workspace` skill for workspace structure if adding Node.js artifacts alongside this Python app
