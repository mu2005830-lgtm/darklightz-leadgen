"""
Automatic update checker for Darklightz Lead Generator v2.0.

Checks the configured GitHub repository for new releases using the
GitHub Releases API (completely free, no authentication required for
public repos).

Usage
-----
    from utilities.updater import check_for_updates, UpdateInfo

    info = check_for_updates(current_version="2.0.0")
    if info.update_available:
        print(f"New version {info.latest_version} available!")
        print(f"Download: {info.download_url}")

No secrets, no paid APIs — the GitHub API is free and unauthenticated
for public repos (60 requests/hour per IP).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import requests

from utilities.logger import logger

# ---------------------------------------------------------------------------
# Configuration — update this to point to the real GitHub repo
# ---------------------------------------------------------------------------
GITHUB_OWNER   = "DarklightzStudio"
GITHUB_REPO    = "lead-generator"
RELEASES_URL   = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)
REQUEST_TIMEOUT = 10   # seconds


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class UpdateInfo:
    current_version: str
    latest_version: str        = ""
    update_available: bool     = False
    release_name: str          = ""
    release_notes: str         = ""
    download_url: str          = ""
    release_url: str           = ""
    error: Optional[str]       = None
    assets: list[dict]         = field(default_factory=list)


# ---------------------------------------------------------------------------
# Version comparison
# ---------------------------------------------------------------------------

def _parse_version(v: str) -> tuple[int, ...]:
    """
    Parse a version string into a tuple of ints for comparison.
    Handles 'v2.0.0', '2.0', '2.0.1' etc.
    """
    v = v.strip().lstrip("vV")
    parts = re.split(r"[.\-]", v)
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            break
    return tuple(result) if result else (0,)


def _is_newer(latest: str, current: str) -> bool:
    """Return True if *latest* is strictly newer than *current*."""
    return _parse_version(latest) > _parse_version(current)


# ---------------------------------------------------------------------------
# Main checker
# ---------------------------------------------------------------------------

def check_for_updates(current_version: str) -> UpdateInfo:
    """
    Query the GitHub Releases API and return an UpdateInfo.

    Never raises — all errors are captured in UpdateInfo.error.
    """
    info = UpdateInfo(current_version=current_version)

    try:
        resp = requests.get(
            RELEASES_URL,
            timeout=REQUEST_TIMEOUT,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "DarklightzLeadGenerator",
            },
        )

        if resp.status_code == 404:
            info.error = (
                "No releases found on GitHub. "
                "The repository may be private or have no published releases."
            )
            logger.warning("Update check 404: %s", RELEASES_URL)
            return info

        if resp.status_code != 200:
            info.error = f"GitHub API returned HTTP {resp.status_code}."
            logger.warning("Update check HTTP error: %s", resp.status_code)
            return info

        data = resp.json()
        tag: str = data.get("tag_name", "")
        info.latest_version = tag.lstrip("vV")
        info.release_name   = data.get("name", tag)
        info.release_notes  = data.get("body", "")
        info.release_url    = data.get("html_url", "")
        info.assets         = data.get("assets", [])

        # Look for a Windows installer / zip as preferred download
        preferred_extensions = (".exe", ".zip", ".msi", ".tar.gz")
        for asset in info.assets:
            name_lower = asset.get("name", "").lower()
            if any(name_lower.endswith(ext) for ext in preferred_extensions):
                info.download_url = asset.get("browser_download_url", "")
                break

        if not info.download_url:
            info.download_url = info.release_url  # fall back to release page

        if tag and _is_newer(tag, current_version):
            info.update_available = True
            logger.info(
                "Update available: %s → %s", current_version, info.latest_version
            )
        else:
            logger.info(
                "Application is up to date (%s).", current_version
            )

    except requests.exceptions.ConnectionError:
        info.error = "No internet connection. Could not check for updates."
        logger.warning("Update check: no connection.")
    except requests.exceptions.Timeout:
        info.error = "Update check timed out. Please try again later."
        logger.warning("Update check: timeout.")
    except Exception as exc:
        info.error = f"Update check failed: {exc}"
        logger.warning("Update check exception: %s", exc)

    return info
