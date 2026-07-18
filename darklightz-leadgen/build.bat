@echo off
:: =========================================================================
:: Darklightz Lead Generator — Windows Build Script
:: =========================================================================
:: Run this ONCE on your Windows PC inside the darklightz-leadgen folder:
::     build.bat
::
:: What it does
::   1. Creates a Python virtual environment
::   2. Installs all dependencies (PyQt6, Playwright, openpyxl, reportlab …)
::   3. Installs Playwright's Chromium browser
::   4. Kills any running copy of the app and clears the old dist folder
::      (prevents the "Access is denied" error when rebuilding)
::   5. Bundles everything into a standalone .exe with PyInstaller
::   6. Copies the Chromium browser into the dist folder
::      (so the .exe works on any PC without installing Playwright)
::
:: Requirements
::   - Python 3.10, 3.11, 3.12, or 3.13 must be installed and on PATH
::     Download: https://www.python.org/downloads/
::     Tick "Add Python to PATH" during installation!
::   - Internet access for the first run (downloads packages + Chromium)
::
:: Output
::   dist\DarklightzLeadGenerator\DarklightzLeadGenerator.exe
::   dist\DarklightzLeadGenerator\          (ZIP this folder to share)
::
:: NOTE — Chromium is bundled in the ms-playwright sub-folder next to the
::        .exe.  The application sets PLAYWRIGHT_BROWSERS_PATH at runtime
::        so it always finds Chromium, even on a fresh Windows PC.
:: =========================================================================

setlocal enabledelayedexpansion

echo.
echo  ======================================================================
echo   Darklightz Lead Generator — Build Script
echo  ======================================================================
echo.

:: ---------------------------------------------------------------------------
:: Step 1 — Verify Python
:: ---------------------------------------------------------------------------
echo [1/7] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python not found on PATH.
    echo  Download from https://www.python.org/downloads/
    echo  Check "Add Python to PATH" during setup!
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Found Python %PYVER%
echo.

:: ---------------------------------------------------------------------------
:: Step 2 — Virtual environment
:: ---------------------------------------------------------------------------
echo [2/7] Setting up virtual environment...
if not exist ".venv" (
    python -m venv .venv
    if errorlevel 1 (
        echo  ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  Created .venv
) else (
    echo  Using existing .venv
)
echo.
call .venv\Scripts\activate.bat

:: ---------------------------------------------------------------------------
:: Step 3 — Install Python dependencies
:: ---------------------------------------------------------------------------
echo [3/7] Installing dependencies (this may take a few minutes)...
pip install --upgrade pip --quiet
if errorlevel 1 (
    echo  WARNING: pip upgrade failed — continuing with existing pip version.
)

pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo  ERROR: pip install failed. Check your internet connection.
    pause
    exit /b 1
)

pip install pyinstaller
if errorlevel 1 (
    echo.
    echo  ERROR: PyInstaller installation failed.
    pause
    exit /b 1
)
echo  All packages installed.
echo.

:: ---------------------------------------------------------------------------
:: Step 4 — Install Playwright Chromium browser
:: ---------------------------------------------------------------------------
echo [4/7] Installing Playwright Chromium browser (~130 MB)...
playwright install chromium
if errorlevel 1 (
    echo.
    echo  ERROR: Playwright Chromium install failed.
    echo  Try running manually inside the .venv:
    echo      .venv\Scripts\playwright install chromium
    echo.
    pause
    exit /b 1
)
echo  Playwright Chromium installed.
echo.

:: ---------------------------------------------------------------------------
:: Step 5 — Kill any running app instance and clear the old dist folder
::           (prevents "Access is denied" PermissionError during rebuild)
:: ---------------------------------------------------------------------------
echo [5/7] Preparing build environment...

:: Kill any running instance — Windows locks .pyd files while the exe is open
echo  Stopping any running DarklightzLeadGenerator.exe...
taskkill /F /IM "DarklightzLeadGenerator.exe" /T >nul 2>&1
:: Give Windows 2 seconds to fully release the file handles
timeout /t 2 /nobreak >nul

:: Delete the old dist folder NOW so PyInstaller never has to do it.
:: PyInstaller's own deletion fails with "Access is denied" when antivirus
:: or Windows Defender is scanning freshly-built files; doing it ourselves
:: first avoids the race condition.
if exist "dist\DarklightzLeadGenerator" (
    echo  Removing old dist\DarklightzLeadGenerator ...
    rmdir /S /Q "dist\DarklightzLeadGenerator" >nul 2>&1

    :: Verify it is actually gone; if not, try a forced rename as a fallback
    if exist "dist\DarklightzLeadGenerator" (
        echo  WARNING: Could not fully delete old dist folder on first attempt.
        echo  Retrying in 5 seconds — please close any open file managers
        echo  or Explorer windows pointing at dist\DarklightzLeadGenerator ...
        timeout /t 5 /nobreak >nul
        rmdir /S /Q "dist\DarklightzLeadGenerator" >nul 2>&1
    )

    if exist "dist\DarklightzLeadGenerator" (
        echo.
        echo  ERROR: The old dist\DarklightzLeadGenerator folder is still
        echo  locked by Windows.  Please:
        echo    1. Close any open Explorer windows pointing at that folder.
        echo    2. Temporarily pause Windows Defender real-time protection.
        echo    3. Re-run build.bat.
        echo.
        pause
        exit /b 1
    )

    echo  Old dist folder removed successfully.
)

:: Ensure assets folder exists
if not exist "assets" mkdir assets
echo  Build environment ready.
echo.

:: ---------------------------------------------------------------------------
:: Step 6 — Build with PyInstaller
:: ---------------------------------------------------------------------------
echo [6/7] Building Windows executable (this takes 2-5 minutes)...

:: Find the Playwright driver directory (contains the node runtime + playwright.js)
for /f "delims=" %%d in ('python -c "import playwright, os; print(os.path.join(os.path.dirname(playwright.__file__), 'driver'))"') do (
    set PLAYWRIGHT_DRIVER=%%d
)

echo  Playwright driver: %PLAYWRIGHT_DRIVER%
echo.

:: NOTE: --noconfirm is safe here because we already deleted the dist folder above.
:: --collect-all playwright pulls in the full playwright package including hooks.
:: playwright._impl._api_types was removed in Playwright >=1.50; do NOT list it.
pyinstaller ^
    --noconfirm ^
    --clean ^
    --onedir ^
    --windowed ^
    --name "DarklightzLeadGenerator" ^
    --icon "assets\icon.ico" ^
    --add-data "assets;assets" ^
    --add-data "database;database" ^
    --add-data "backend;backend" ^
    --add-data "frontend;frontend" ^
    --add-data "exports;exports" ^
    --add-data "utilities;utilities" ^
    --add-data "%PLAYWRIGHT_DRIVER%;playwright/driver" ^
    --collect-all playwright ^
    --collect-all PyQt6 ^
    --hidden-import "PyQt6" ^
    --hidden-import "PyQt6.QtWidgets" ^
    --hidden-import "PyQt6.QtCore" ^
    --hidden-import "PyQt6.QtGui" ^
    --hidden-import "PyQt6.sip" ^
    --hidden-import "PyQt6.QtNetwork" ^
    --hidden-import "playwright" ^
    --hidden-import "playwright.sync_api" ^
    --hidden-import "playwright._impl._driver" ^
    --hidden-import "openpyxl" ^
    --hidden-import "openpyxl.styles" ^
    --hidden-import "reportlab" ^
    --hidden-import "reportlab.platypus" ^
    --hidden-import "reportlab.lib.styles" ^
    --hidden-import "lxml" ^
    --hidden-import "lxml.etree" ^
    --hidden-import "bs4" ^
    --hidden-import "sqlite3" ^
    --hidden-import "logging.handlers" ^
    main.py

if errorlevel 1 (
    echo.
    echo  ERROR: PyInstaller build failed. See error output above.
    echo.
    echo  Most common causes:
    echo    - Old dist folder still locked  ^(close Explorer / pause Defender^)
    echo    - A source .py file has a syntax error  ^(run: python main.py^)
    echo    - Missing assets\icon.ico  ^(the file must exist^)
    echo.
    pause
    exit /b 1
)

:: ---------------------------------------------------------------------------
:: Step 7 — Copy Chromium browser into the dist folder
::           (so the .exe works on any PC without installing Playwright)
:: ---------------------------------------------------------------------------
echo.
echo [7/7] Copying Chromium browser into dist folder...
echo  (Makes the .exe work on any PC without installing Playwright)

:: Locate the ms-playwright browsers directory.
:: On Windows, Playwright installs browsers to %LOCALAPPDATA%\ms-playwright.
for /f "delims=" %%d in ('python -c "import os; p=os.path.join(os.environ.get('LOCALAPPDATA',''), 'ms-playwright'); print(p)"') do (
    set MS_PLAYWRIGHT=%%d
)

echo  Playwright browsers source: %MS_PLAYWRIGHT%

if not exist "%MS_PLAYWRIGHT%" (
    echo.
    echo  WARNING: Could not find the ms-playwright directory at:
    echo    %MS_PLAYWRIGHT%
    echo.
    echo  The .exe was built but Chromium is NOT bundled.
    echo  On the target machine you must run:
    echo      playwright install chromium
    echo  before launching DarklightzLeadGenerator.exe.
    echo.
    goto :build_done
)

:: Copy the entire ms-playwright folder into dist\DarklightzLeadGenerator\ms-playwright\
xcopy "%MS_PLAYWRIGHT%" "dist\DarklightzLeadGenerator\ms-playwright" /E /I /Q /Y
if errorlevel 1 (
    echo.
    echo  WARNING: xcopy failed — Chromium may not be bundled correctly.
    echo  Try copying manually:
    echo    xcopy "%MS_PLAYWRIGHT%" "dist\DarklightzLeadGenerator\ms-playwright" /E /I /Y
    echo.
) else (
    echo  Chromium successfully copied to dist folder.
)

:build_done
echo.
echo  ==============================================================
echo   Build complete!
echo.
echo   Application ready at:
echo   dist\DarklightzLeadGenerator\DarklightzLeadGenerator.exe
echo.
echo   To share or install on another PC:
echo     ZIP the entire  dist\DarklightzLeadGenerator\  folder
echo     and extract it on the target machine — no install needed.
echo  ==============================================================
echo.

pause
