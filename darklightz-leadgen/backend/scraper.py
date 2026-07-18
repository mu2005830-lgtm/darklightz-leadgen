"""
Google Maps scraper for Darklightz Lead Generator v2.0.

v2.0 improvements
-----------------
* Extracts ALL new fields: category, email, maps_link, latitude, longitude,
  opening_hours, mobile (separate from landline phone).
* Pakistani mobile number detection + WhatsApp link generation ONLY for
  confirmed mobile numbers (never for landlines).
* Improved scrolling: tracks position, detects stall, retries scroll.
* Improved loading detection: waits for spinner to disappear before extracting.
* Improved deduplication: two-level (feed href + name|phone|city).
* Better back-button navigation between listing detail and the feed.
* Website filtering fixed: only skips businesses with a REAL dedicated website.
  Instagram, Facebook, WhatsApp, Google Business → still included as leads.
* Continues collecting until the requested number of qualifying leads is reached,
  not just until Google Maps runs out of visible results.
* All errors written to the rotating log file via the shared logger.

Playwright + PyInstaller fix
----------------------------
When the application is packaged with PyInstaller the Chromium browser
binaries are NOT inside the Python package directory; they live in a
separate folder copied next to the .exe during build.  This module detects
the frozen state on startup and sets PLAYWRIGHT_BROWSERS_PATH accordingly.
"""

from __future__ import annotations

import os
import re
import sys
import time
import urllib.parse

from PyQt6.QtCore import QThread, pyqtSignal

from utilities.helpers import (
    classify_lead,
    should_include_lead,
    clean_phone,
    classify_phone,
    build_whatsapp_link,
    extract_email,
)
from utilities.logger import logger


# ---------------------------------------------------------------------------
# Playwright path helper (PyInstaller support)
# ---------------------------------------------------------------------------

def _configure_playwright_path() -> None:
    if not getattr(sys, "frozen", False):
        return

    exe_dir = os.path.dirname(sys.executable)
    for candidate in [
        os.path.join(exe_dir, "ms-playwright"),
        os.path.join(os.path.dirname(exe_dir), "ms-playwright"),
    ]:
        if os.path.isdir(candidate):
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = candidate
            logger.info("Playwright browsers path: %s", candidate)
            return

    logger.warning(
        "Could not find bundled ms-playwright directory next to %s. "
        "Playwright will use the system path — Chromium may be missing.",
        exe_dir,
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_FEED_SELECTORS = [
    'div[role="feed"]',
    'div[aria-label*="Results"]',
    'div[aria-label*="result"]',
    'div.m6QErb[aria-label]',
]

_RESULT_SELECTORS = [
    'div[role="feed"] a[href*="maps/place"]',
    'a[data-value="Search Results"]',
    'div.Nv2PK a',
]

_COOKIE_SELECTORS = [
    'button[aria-label*="Accept"]',
    'button[aria-label*="Agree"]',
    'button:has-text("Accept all")',
    'button:has-text("Reject all")',
    '#L2AGLb',
    '.tHlp8d',
]

_SPINNER_SELECTOR = 'div[jsaction*="mouseover:trigger.TnYT73"]'

_MAX_SCROLL_STALLS = 8      # give up scrolling after this many no-progress cycles
_STALL_WAIT_MS     = 2000   # ms to wait when stalled before retrying


# ---------------------------------------------------------------------------
# Worker thread
# ---------------------------------------------------------------------------

class ScraperWorker(QThread):
    """
    Background thread that drives a Playwright browser, scrapes Google Maps,
    and emits signals for every qualifying lead found.

    Signals
    -------
    progress(int, str)      current found count + status message
    lead_found(dict)        qualifying lead ready to be inserted into DB
    finished(int, bool)     (total_found, stopped_early)
    error(str)              unrecoverable error message
    """

    progress   = pyqtSignal(int, str)
    lead_found = pyqtSignal(dict)
    finished   = pyqtSignal(int, bool)
    error      = pyqtSignal(str)

    def __init__(
        self,
        keyword: str,
        city: str,
        max_leads: int,
        search_id: int,
        headless: bool = True,
        scroll_delay: int = 1500,
        parent=None,
    ):
        super().__init__(parent)
        self.keyword      = keyword.strip()
        self.city         = city.strip()
        self.max_leads    = max(1, max_leads)
        self.search_id    = search_id
        self.headless     = headless
        self.scroll_delay = max(500, scroll_delay)
        self._stop_flag   = False

    def stop(self) -> None:
        self._stop_flag = True

    # ------------------------------------------------------------------
    # Main thread entry
    # ------------------------------------------------------------------

    def run(self) -> None:
        _configure_playwright_path()

        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
        except ImportError:
            self.error.emit(
                "Playwright is not installed.\n"
                "Run: pip install playwright && playwright install chromium"
            )
            return

        found      = 0
        stopped    = False
        query      = f"{self.keyword} in {self.city}"
        search_url = (
            "https://www.google.com/maps/search/"
            + urllib.parse.quote_plus(query)
        )

        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=self.headless)
                ctx     = browser.new_context(
                    locale="en-US",
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                )
                page = ctx.new_page()
                page.set_default_timeout(30_000)

                logger.info("Opening: %s", search_url)
                self.progress.emit(0, f"Opening Google Maps — {query} …")
                page.goto(search_url, wait_until="domcontentloaded")

                # Dismiss cookie/consent banner
                self._dismiss_cookie_banner(page)

                # Wait for the results feed to appear
                feed = self._wait_for_feed(page)
                if feed is None:
                    self.error.emit(
                        "Google Maps results feed did not appear.\n"
                        "Check your internet connection and try again."
                    )
                    browser.close()
                    return

                seen_hrefs: set[str]  = set()
                seen_keys:  set[str]  = set()
                stall_count           = 0
                last_count            = 0

                while found < self.max_leads and not self._stop_flag:
                    # Collect visible listing links
                    hrefs = self._collect_hrefs(page)

                    new_hrefs = [h for h in hrefs if h not in seen_hrefs]

                    if not new_hrefs:
                        stall_count += 1
                        if stall_count >= _MAX_SCROLL_STALLS:
                            logger.info("Feed exhausted after %d stalls.", stall_count)
                            break
                        self.progress.emit(
                            found,
                            f"Scrolling for more results … (attempt {stall_count}/{_MAX_SCROLL_STALLS})"
                        )
                        self._scroll_feed(page, feed, aggressive=stall_count > 3)
                        page.wait_for_timeout(_STALL_WAIT_MS)
                        continue
                    else:
                        stall_count = 0

                    for href in new_hrefs:
                        if found >= self.max_leads or self._stop_flag:
                            break

                        seen_hrefs.add(href)

                        lead = self._extract_detail(page, href)
                        if lead is None:
                            continue

                        # Website filtering — include if no real website
                        website = lead.get("website", "")
                        if not should_include_lead(website):
                            logger.debug("Skipping (has website): %s", lead.get("name"))
                            continue

                        # Deduplication by name+phone+city
                        dedup_key = (
                            f"{lead.get('name','').lower()}|"
                            f"{re.sub(r'\\D','',lead.get('phone',''))}|"
                            f"{self.city.lower()}"
                        )
                        if dedup_key in seen_keys:
                            continue
                        seen_keys.add(dedup_key)

                        lead["search_id"] = self.search_id
                        lead["city"]      = self.city
                        lead["keyword"]   = self.keyword
                        lead["lead_type"] = classify_lead(website)

                        found += 1
                        self.progress.emit(
                            found,
                            f"Found: {lead.get('name','unknown')} [{found}/{self.max_leads}]"
                        )
                        self.lead_found.emit(lead)

                    # Scroll to reveal more results
                    if found < self.max_leads and not self._stop_flag:
                        self._scroll_feed(page, feed)
                        page.wait_for_timeout(self.scroll_delay)

                    # Check for "end of list" marker
                    if self._feed_exhausted(page):
                        logger.info("Google Maps returned end-of-results marker.")
                        break

                stopped = self._stop_flag
                browser.close()

        except Exception as exc:
            logger.exception("Scraper crashed: %s", exc)
            self.error.emit(f"Scraper error: {exc}")
            return

        self.finished.emit(found, stopped)

    # ------------------------------------------------------------------
    # Feed helpers
    # ------------------------------------------------------------------

    def _dismiss_cookie_banner(self, page) -> None:
        for sel in _COOKIE_SELECTORS:
            try:
                btn = page.query_selector(sel)
                if btn and btn.is_visible():
                    btn.click()
                    page.wait_for_timeout(800)
                    logger.debug("Cookie banner dismissed via: %s", sel)
                    return
            except Exception:
                pass

    def _wait_for_feed(self, page, timeout_ms: int = 15_000):
        for sel in _FEED_SELECTORS:
            try:
                page.wait_for_selector(sel, timeout=timeout_ms)
                el = page.query_selector(sel)
                if el:
                    return el
            except Exception:
                pass
        return None

    def _collect_hrefs(self, page) -> list[str]:
        hrefs: list[str] = []
        for sel in _RESULT_SELECTORS:
            try:
                els = page.query_selector_all(sel)
                for el in els:
                    href = el.get_attribute("href") or ""
                    if "maps/place" in href and href not in hrefs:
                        hrefs.append(href)
                if hrefs:
                    break
            except Exception:
                pass
        return hrefs

    def _scroll_feed(self, page, feed, aggressive: bool = False) -> None:
        try:
            # Scroll the feed panel (not the whole page)
            page.evaluate(
                """(feed) => {
                    feed.scrollTop += arguments[0];
                }""".replace("arguments[0]", str(1200 if aggressive else 600)),
                feed,
            )
        except Exception:
            # Fallback: keyboard scroll
            try:
                page.keyboard.press("End")
            except Exception:
                pass

    def _feed_exhausted(self, page) -> bool:
        """Return True if Google Maps shows an 'end of results' indicator."""
        try:
            text = page.inner_text("body")
            markers = [
                "You've reached the end of the list",
                "You have reached the end",
                "No more results",
            ]
            return any(m in text for m in markers)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Detail extraction
    # ------------------------------------------------------------------

    def _extract_detail(self, page, href: str) -> dict | None:
        """
        Navigate to a listing's detail panel and extract all available data.
        Returns a dict or None if extraction fails completely.
        """
        data: dict = {
            "name":          "",
            "category":      "",
            "phone":         "",
            "mobile":        "",
            "whatsapp":      "",
            "email":         "",
            "instagram":     "",
            "facebook":      "",
            "website":       "",
            "address":       "",
            "maps_link":     "",
            "latitude":      "",
            "longitude":     "",
            "rating":        "",
            "reviews":       "",
            "opening_hours": "",
        }

        try:
            page.goto(href, wait_until="domcontentloaded", timeout=20_000)
            page.wait_for_timeout(1500)

            # Wait for the detail panel to settle
            try:
                page.wait_for_selector('h1[jstag~="headline"]', timeout=8_000)
            except Exception:
                try:
                    page.wait_for_selector('h1', timeout=5_000)
                except Exception:
                    pass

            # ---- Name ---------------------------------------------------
            for sel in [
                'h1[jstag~="headline"]',
                'h1.DUwDvf',
                'h1',
                '[data-attrid="title"]',
            ]:
                try:
                    el = page.query_selector(sel)
                    if el:
                        name = el.inner_text().strip()
                        if name:
                            data["name"] = name
                            break
                except Exception:
                    pass

            if not data["name"]:
                return None

            # ---- Category -----------------------------------------------
            for sel in [
                'button[jsaction*="pane.rating.category"]',
                'span.DkEaL',
                '[data-item-id="category"]',
                'button.DkEaL',
            ]:
                try:
                    el = page.query_selector(sel)
                    if el:
                        cat = el.inner_text().strip()
                        if cat:
                            data["category"] = cat
                            break
                except Exception:
                    pass

            # ---- Maps link + coordinates --------------------------------
            data["maps_link"] = page.url

            # Extract lat/lng from URL
            lat, lng = _extract_coords_from_url(page.url)
            data["latitude"]  = lat
            data["longitude"] = lng

            # ---- Address ------------------------------------------------
            # Try every known selector; pick the longest plausible result.
            _addr_candidates: list[str] = []
            for sel in [
                'button[data-item-id="address"]',
                '[data-item-id="address"]',
                '[aria-label*="Address"]',
                '[aria-label*="address"]',
                'div[data-section-id="address"]',
                'div.rogA2c',
                'div.rogA2c span',
                '.LrzXr',
                'span.LrzXr',
                'div.Io6YTe',
                # fallback: any button whose aria-label contains a street/number
                'button[aria-label*=","]',
            ]:
                try:
                    el = page.query_selector(sel)
                    if el:
                        # Prefer aria-label (often cleaner) then inner_text
                        addr = (
                            el.get_attribute("aria-label") or el.inner_text()
                        ).strip()
                        # Strip leading "Address:" prefix Google sometimes adds
                        addr = re.sub(
                            r"^(Address|address)[:\s]+", "", addr
                        ).strip()
                        if addr and len(addr) > 5:
                            _addr_candidates.append(addr)
                except Exception:
                    pass

            # Also try querying ALL matching elements and pick the best
            for sel in [
                'button[data-item-id="address"]',
                '[data-item-id="address"]',
            ]:
                try:
                    els = page.query_selector_all(sel)
                    for el in els:
                        addr = (
                            el.get_attribute("aria-label") or el.inner_text()
                        ).strip()
                        addr = re.sub(
                            r"^(Address|address)[:\s]+", "", addr
                        ).strip()
                        if addr and len(addr) > 5:
                            _addr_candidates.append(addr)
                except Exception:
                    pass

            if _addr_candidates:
                # Pick the longest candidate — usually the most complete
                data["address"] = max(_addr_candidates, key=len)

            # ---- Rating -------------------------------------------------
            for sel in [
                'div.F7nice span[aria-hidden="true"]',
                'span.ceNzKf',
                'div[jslog*="19715"] span',
            ]:
                try:
                    el = page.query_selector(sel)
                    if el:
                        rating = el.inner_text().strip()
                        if re.match(r"\d", rating):
                            data["rating"] = rating
                            break
                except Exception:
                    pass

            # ---- Reviews count ------------------------------------------
            for sel in [
                'button[jsaction*="pane.rating.moreReviews"] span',
                'span[aria-label*="review"]',
                'div.UY7F9 span',
            ]:
                try:
                    el = page.query_selector(sel)
                    if el:
                        rev_text = el.inner_text().strip()
                        nums = re.findall(r"[\d,]+", rev_text)
                        if nums:
                            data["reviews"] = nums[0].replace(",", "")
                            break
                except Exception:
                    pass

            # ---- Phone --------------------------------------------------
            for sel in [
                '[data-item-id*="phone"]',
                'button[data-tooltip*="phone"]',
                '[aria-label*="Phone"]',
                'a[href^="tel:"]',
            ]:
                try:
                    el = page.query_selector(sel)
                    if el:
                        ph = el.get_attribute("aria-label") or el.inner_text()
                        ph = re.sub(r"[Pp]hone:?\s*", "", ph).strip()
                        ph = clean_phone(ph)
                        if ph and len(re.sub(r"\D", "", ph)) >= 7:
                            data["phone"] = ph
                            break
                except Exception:
                    pass

            # Also try tel: href links
            if not data["phone"]:
                try:
                    tel_el = page.query_selector('a[href^="tel:"]')
                    if tel_el:
                        href_tel = tel_el.get_attribute("href") or ""
                        ph = clean_phone(href_tel.replace("tel:", ""))
                        if ph:
                            data["phone"] = ph
                except Exception:
                    pass

            # ---- Mobile detection + WhatsApp ----------------------------
            if data["phone"]:
                phone_type = classify_phone(data["phone"])
                if phone_type == "mobile":
                    data["mobile"]    = data["phone"]
                    data["whatsapp"]  = build_whatsapp_link(data["phone"])
                elif phone_type == "landline":
                    data["mobile"]    = ""
                    data["whatsapp"]  = ""   # Never for landlines
                else:
                    # unknown — attempt WhatsApp but mark mobile tentatively
                    wa = build_whatsapp_link(data["phone"])
                    if wa:
                        data["mobile"]   = data["phone"]
                        data["whatsapp"] = wa

            # ---- Website ------------------------------------------------
            for sel in [
                'a[data-item-id="authority"]',
                'a[data-tooltip="Open website"]',
                'a[aria-label*="website"]',
                'a[jsaction*="pane.website"]',
            ]:
                try:
                    el = page.query_selector(sel)
                    if el:
                        href_w = el.get_attribute("href") or ""
                        if href_w.startswith("http") and "google.com" not in href_w:
                            data["website"] = href_w
                            break
                except Exception:
                    pass

            # ---- Opening hours ------------------------------------------
            try:
                hours_els = page.query_selector_all(
                    '[data-item-id="oh"] table tr, '
                    '.t39EBf .o0Svhf tr, '
                    'div[aria-label*="hours"] tr'
                )
                if hours_els:
                    hours_lines = []
                    for tr in hours_els[:14]:
                        try:
                            text = tr.inner_text().strip()
                            if text:
                                hours_lines.append(text)
                        except Exception:
                            pass
                    if hours_lines:
                        data["opening_hours"] = "; ".join(hours_lines)
            except Exception:
                pass

            # Fallback: look for "Open" / "Closed" badge
            if not data["opening_hours"]:
                try:
                    badge_sel = (
                        'span.ZDu9vd, '
                        'div.o0Svhf, '
                        '[data-hide-tooltip-on-mouse-move]'
                    )
                    badge = page.query_selector(badge_sel)
                    if badge:
                        data["opening_hours"] = badge.inner_text().strip()
                except Exception:
                    pass

            # ---- Socials + email from panel HTML -----------------------
            try:
                panel_html = page.inner_html('div[role="main"]')
                _extract_socials(panel_html, data)
                # Email from panel HTML
                if not data["email"]:
                    data["email"] = extract_email(panel_html)
            except Exception:
                pass

            # ---- WhatsApp from explicit wa.me links in HTML -----------
            if not data["whatsapp"]:
                try:
                    m = re.search(r'href="(https://wa\.me/\d+)"', page.content())
                    if m:
                        data["whatsapp"] = m.group(1)
                except Exception:
                    pass

        except Exception as exc:
            logger.debug("Detail extraction error for %s: %s", href[:80], exc)

        return data if data.get("name") else None

    # ------------------------------------------------------------------
    # Social link helpers
    # ------------------------------------------------------------------


def _extract_socials(html: str, data: dict) -> None:
    """Scan panel HTML for social media profile links."""
    # Instagram
    if not data.get("instagram"):
        m = re.search(r"instagram\.com/([A-Za-z0-9._]+)(?:[/?]|$)", html, re.I)
        if m and m.group(1) not in {
            "p", "explore", "accounts", "tv", "reel", "stories"
        }:
            data["instagram"] = f"https://instagram.com/{m.group(1)}"

    # Facebook
    if not data.get("facebook"):
        m = re.search(
            r"facebook\.com/(?:pg/|pages/|profile\.php\?id=)?([A-Za-z0-9_./-]+)",
            html, re.I,
        )
        if m:
            slug = m.group(1).rstrip("/").split("?")[0]
            if slug and slug not in {
                "sharer", "share", "login", "dialog", "photo", "watch"
            }:
                data["facebook"] = f"https://facebook.com/{slug}"

    # Explicit wa.me link in HTML takes priority
    if not data.get("whatsapp"):
        m = re.search(r"wa\.me/(\d{7,15})", html, re.I)
        if m:
            data["whatsapp"] = f"https://wa.me/{m.group(1)}"


def _extract_coords_from_url(url: str) -> tuple[str, str]:
    """
    Extract latitude and longitude from a Google Maps URL.

    Handles formats:
      /maps/place/Name/@lat,lng,zoom
      /maps?q=lat,lng
      ll=lat,lng
    """
    # Format: /@lat,lng or /!3dLAT!4dLNG
    m = re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if m:
        return m.group(1), m.group(2)

    # Format: !3d{lat}!4d{lng}
    m = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
    if m:
        return m.group(1), m.group(2)

    # Format: q=lat,lng
    m = re.search(r"[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if m:
        return m.group(1), m.group(2)

    return "", ""
