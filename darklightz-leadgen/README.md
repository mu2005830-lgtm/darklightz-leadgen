# Darklightz Lead Generator v2.0

**Professional Google Maps Lead Generation Suite**  
*Developed by Darklightz Studio*

---

## What It Does

Searches Google Maps for businesses matching your keyword and city, then collects their complete contact information — but **only includes businesses that do NOT have a dedicated real website**. These are your target customers: businesses on Instagram, Facebook, or WhatsApp only, or with no online presence at all.

---

## Features (v2.0)

| Feature | Description |
|---|---|
| **Complete lead data** | Name, category, phone, mobile, WhatsApp, email, Instagram, Facebook, website, address, Google Maps link, lat/lng, rating, reviews, opening hours |
| **Pakistani phone validation** | Mobile vs landline detection; WhatsApp links ONLY for mobile numbers |
| **Smart website filtering** | Skips only real business websites — Instagram/Facebook/WhatsApp counts as "no website" |
| **Lead Table** | Sortable, filterable, searchable table with all 21 fields; double-click to open URLs; right-click for actions |
| **Collections** | Group leads into named projects |
| **Excel export** | Styled .xlsx with hyperlinks |
| **CSV export** | Universal format |
| **PDF export** | Landscape A4 with branding |
| **Auto-update** | Checks GitHub Releases on startup |
| **SQLite storage** | All data stored locally, survives reinstalls |

---

## Installation

### Requirements

- Windows 10/11 (or Linux/macOS for source run)
- Python 3.11+
- Chromium (installed via Playwright)

### Quick Start (from source)

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Playwright's Chromium browser
playwright install chromium

# 3. Run
python main.py
```

### Windows Executable

Run `build.bat` (requires PyInstaller):

```batch
build.bat
```

Produces `dist\DarklightzLeadGenerator\DarklightzLeadGenerator.exe` — copy the entire folder to any Windows PC, no installation required.

---

## Usage

1. **Lead Search** — enter a keyword (e.g. "Salon") and a city (e.g. "Lahore"), set the number of leads, click **Start Search**.
2. **Lead Table** — view, sort, filter, and manage collected leads.
3. **Export** — export to Excel, CSV, or PDF.
4. **Settings** — configure headless mode, scroll delay, and auto-update.
5. **About** — check for updates manually.

---

## Data Stored Per Lead

| Field | Description |
|---|---|
| Business Name | As shown on Google Maps |
| Category | Business category |
| Phone | All available phone numbers |
| Mobile | Mobile numbers only |
| WhatsApp | wa.me link (mobile only, never landlines) |
| Email | Publicly displayed email |
| Instagram | Profile URL |
| Facebook | Page URL |
| Website | Only if a real website is found |
| Address | Full address |
| Google Maps Link | Direct profile link |
| Latitude / Longitude | Extracted from Maps URL |
| Rating | Star rating |
| Reviews | Total review count |
| Opening Hours | All opening times |
| Status | New / Contacted / Follow-up / Interested / Closed / Not Interested |
| Notes | Free-text notes |

---

## Phone & WhatsApp Rules

- Pakistani mobile numbers (`03xx xxxxxxx`) are automatically converted: `03351234567` → `wa.me/923351234567`
- Landline numbers **never** get a WhatsApp link
- If mobile/landline cannot be determined, WhatsApp is generated as best-effort

---

## Auto-Update System

The app checks **GitHub Releases** (`DarklightzStudio/lead-generator`) on startup.  
To update: close the app, download the new version from the release page, extract it over the existing folder — your SQLite database is untouched.

To disable startup update check: go to **Settings → Application → Check for updates automatically on startup**.

---

## Legal

This tool collects publicly available information from Google Maps.  
Google's Terms of Service prohibit automated data collection.  
Use responsibly and in compliance with local laws.  
The developer assumes no liability for misuse.

---

*© 2025 Darklightz Studio. All rights reserved.*
