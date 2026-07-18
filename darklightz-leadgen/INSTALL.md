# Installation Guide — Darklightz Studio Lead Generation Suite

> Developed exclusively for **Darklightz Studio**  
> Professional Web Design & Digital Solutions

---

## Prerequisites

### Python 3.11 (recommended) or 3.10 / 3.12

1. Visit **https://www.python.org/downloads/**
2. Download the latest **Python 3.11.x Windows installer** (64-bit)
3. Run the installer
4. ✅ **IMPORTANT:** Check **"Add Python to PATH"** before clicking Install
5. Click **Install Now**

Verify:
```
Win+R → cmd → python --version
```
You should see `Python 3.11.x`.

---

## Method 1 — Run from Source (easiest, no build step)

1. Copy the `darklightz-leadgen` folder to your PC (e.g. `C:\DarklightzLeadGenerator`)
2. Open **Command Prompt** in that folder:
   - Hold `Shift`, right-click the folder → **Open command window here**  
   - Or: `Win+R` → `cmd` → `cd C:\DarklightzLeadGenerator`
3. Run these three commands one at a time:

```batch
pip install -r requirements.txt
playwright install chromium
python main.py
```

The Darklightz Studio splash screen will appear, then the main window opens.  
All data is saved automatically to `C:\Users\YourName\.darklightz\leads.db`.

---

## Method 2 — Build a Standalone `.exe`

This creates a self-contained executable **with Chromium bundled inside** — the
target PC does not need Python or Playwright installed at all.

### Step 1 — Copy the project folder to your PC

Place `darklightz-leadgen` anywhere, e.g. `C:\DarklightzLeadGenerator`.

### Step 2 — Run the build script

Double-click **`build.bat`** inside the folder.

The script will:
1. Create a Python virtual environment
2. Install all required packages (PyQt6, Playwright, openpyxl, reportlab …)
3. Download the Chromium browser used for scraping
4. Bundle everything with PyInstaller (exe + Playwright driver)
5. **Copy the Chromium browser into `dist\DarklightzLeadGenerator\ms-playwright\`**
   so the application finds it on any machine without additional setup

**This takes 3–8 minutes** on first run (mostly downloading Chromium ~130 MB).  
An internet connection is required for this step only.

### Step 3 — Find your `.exe`

```
darklightz-leadgen\
└── dist\
    └── DarklightzLeadGenerator\
        ├── DarklightzLeadGenerator.exe   ← Double-click to launch
        ├── ms-playwright\                ← Bundled Chromium (do not delete!)
        └── ...                           ← Other runtime files
```

The executable will show:
- **Darklightz Studio icon** in the taskbar and title bar
- **Splash screen** on startup
- Window title: **Darklightz Studio — Lead Generation Suite**

### Step 4 — (Optional) Create a Desktop Shortcut

Right-click `DarklightzLeadGenerator.exe` → **Send to → Desktop (create shortcut)**.

The shortcut will use the Darklightz Studio icon automatically.

---

## Sharing with Another PC

1. ZIP the entire `dist\DarklightzLeadGenerator\` folder  
2. Copy the ZIP to the target PC  
3. Extract and double-click the `.exe`

The target PC **does not need Python, Playwright, or Chromium installed** —
Chromium is bundled inside the `ms-playwright` sub-folder.

---

## How Chromium Is Found (Technical Detail)

When the `.exe` runs, it checks whether an `ms-playwright` folder exists next
to itself. If found, it sets `PLAYWRIGHT_BROWSERS_PATH` to that path before
launching the browser. This is why:

- The entire `dist\DarklightzLeadGenerator\` folder must stay together.
- Do **not** move just the `.exe` without the `ms-playwright` folder.
- If you delete `ms-playwright` accidentally, re-run `build.bat`.

---

## Updating / Reinstalling

To update the app:
1. Replace the source files
2. Re-run `build.bat`
3. Replace the `dist\DarklightzLeadGenerator\` folder

Your database (`~\.darklightz\leads.db`) is stored in your home folder and is **not** affected by reinstalls.

---

## Troubleshooting

### "Python not found" when running build.bat
→ Re-install Python and check **"Add Python to PATH"**

### "Failed to launch browser: BrowserType.launch: Executable doesn't exist"
→ This means Chromium was not bundled or was deleted.  
  Option A: Re-run `build.bat` on the build machine and re-ZIP the `dist` folder.  
  Option B: On the target PC, run `playwright install chromium` once.

### Splash screen doesn't appear / logo missing
→ Ensure `assets\logo.png` and `assets\icon.ico` are present in the project folder.  
   The app still runs without them — branding is gracefully degraded.

### "No results" for every search
→ Google Maps layout may have changed. Try:
- A simpler keyword (`cafe`, `salon`)
- A major city (`Karachi`, `Lahore`)
- Disable headless mode in **Settings** to watch the browser

### The .exe is flagged by antivirus
→ This is a false positive common with PyInstaller bundles.  
Add an exclusion for the `dist\DarklightzLeadGenerator\` folder in Windows Security.

### Export produces empty file
→ Make sure you have at least one lead in the table before exporting.

### Log file location
→ `C:\Users\<YourName>\.darklightz\app.log`  
Open it in Notepad for detailed error messages.

---

## Data Location

All leads, settings, and search history are stored in:
```
C:\Users\<YourName>\.darklightz\leads.db
```

Back up this file to preserve your data.

---

## System Requirements

| Requirement | Minimum |
|-------------|---------|
| OS          | Windows 10 or 11 (64-bit) |
| RAM         | 4 GB (8 GB recommended for large searches) |
| Disk space  | ~700 MB (Chromium is bundled in the dist folder) |
| Internet    | Required during build and during search; not needed otherwise |

---

## Copyright

© Darklightz Studio. All rights reserved.  
Developed exclusively for Darklightz Studio.
