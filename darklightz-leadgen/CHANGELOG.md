# Darklightz Lead Generator — Changelog

---

## v2.0.0 — 2025 (Production Upgrade)

### New Features

**Complete Lead Information (Phase 4)**
- New fields collected for every lead:
  - `category` — business category from Google Maps
  - `email` — extracted from panel HTML / business profile
  - `mobile` — mobile number (separate from landline)
  - `maps_link` — direct Google Maps / Google Business Profile link
  - `latitude` / `longitude` — extracted from Maps URL
  - `opening_hours` — all opening times stored as text

**Phone & WhatsApp Validation (Phase 5)**
- Mobile vs landline classification for Pakistani numbers
- WhatsApp links generated ONLY for confirmed mobile numbers
- Pakistani number conversion: `03351234567` → `923351234567` → `https://wa.me/923351234567`
- Landlines never get a WhatsApp link

**Google Business Profile (Phase 6)**
- Every lead stores `maps_link`, `latitude`, `longitude`
- Right-click → "Open in Google Maps" action button
- Right-click → "Copy Google Maps Link" action button

**Email Collection (Phase 7)**
- Email addresses extracted from Google Business Profile panel HTML
- Never generates fake emails — only extracts publicly displayed addresses

**Redesigned Lead Table (Phase 8)**
- All 21 fields visible in the table
- Sortable columns (click header)
- Live search bar (name, phone, email, address, category)
- Status filter dropdown
- Lead Type filter dropdown
- Double-click any URL column to open in browser
- Double-click Notes cell to edit
- Right-click for full action menu

**Lead Collections / Projects (Phase 9)**
- New `collections` table for named lead groups
- `collection_leads` join table
- Add leads to collections via right-click menu
- Database operations: create, rename, delete collections

**Automatic Update System (Phase 17)**
- GitHub Releases API integration (free, no auth required)
- "Check for Updates" button in the About page
- Background thread check (UI never freezes)
- Shows release notes and prompts to download when update is available
- Preserves all local data during updates

### Scraper Improvements (Phase 2)

- Better scrolling: tracks position, detects stall, retries with aggressive scroll
- Stall detection: up to 8 retries before giving up on feed
- Feed exhaustion detection: stops cleanly when Google returns end-of-results
- Better loading: waits for detail panel to settle before extracting
- Multiple CSS selector fallbacks for every field
- Continues collecting until the requested number of qualifying leads is reached
- Coordinate extraction from Google Maps URL (`/@lat,lng` and `!3d!4d` formats)

### Website Filtering Fix (Phase 3)

- Fixed over-aggressive filtering: now includes businesses with Instagram,
  Facebook, WhatsApp, or Google Business Profile links
- Only skips businesses with a real dedicated website (`Has Website`)

### Bug Fixes (Phase 1 Audit)

- Database: Added `PRAGMA journal_mode=WAL` for faster concurrent reads
- Database: Automatic schema migration — existing v1 databases gain v2 columns
  without data loss
- Scraper: WhatsApp fallback previously generated links for ALL numbers
  (including landlines) — now restricted to confirmed mobile numbers
- Scraper: Deduplication was broken (tuple vs string set mismatch) — fixed
  with two-level dedup (feed href + name|phone|city key)
- Helpers: `classify_phone()` added — mobile/landline/unknown detection
- Helpers: `build_whatsapp_link()` replaces bare digit concatenation
- Exports: All new fields (email, mobile, category, maps_link, latitude,
  longitude, opening_hours) added to Excel, CSV, and PDF exports
- Excel: URL columns rendered as clickable hyperlinks

---

## v1.0.0 — Initial release

- Google Maps scraper (Playwright/Chromium)
- Lead table with basic fields
- Excel, CSV, PDF export
- SQLite local database
- PyQt6 dark theme UI
