"""
General-purpose helper utilities for Darklightz Lead Generator v2.0.

v2.0 additions
--------------
* Pakistani mobile number detection and normalisation (03xx → 923xx)
* Mobile vs landline classification
* WhatsApp link generation ONLY for confirmed mobile numbers
* Email extraction from raw text / HTML
"""

from __future__ import annotations

import re
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Social-media / known domain lists
# ---------------------------------------------------------------------------

SOCIAL_DOMAINS = {
    "facebook.com", "www.facebook.com", "fb.com", "m.facebook.com",
    "instagram.com", "www.instagram.com",
    "wa.me", "api.whatsapp.com", "whatsapp.com",
    "twitter.com", "x.com", "t.co",
    "tiktok.com", "www.tiktok.com",
    "youtube.com", "youtu.be", "www.youtube.com",
    "linkedin.com", "www.linkedin.com",
    "snapchat.com",
    "pinterest.com",
    "linktr.ee",
    "linktree.com",
}

FACEBOOK_PATTERNS  = re.compile(r"facebook\.com|fb\.com|m\.facebook\.com", re.I)
INSTAGRAM_PATTERNS = re.compile(r"instagram\.com", re.I)
WHATSAPP_PATTERNS  = re.compile(r"wa\.me|whatsapp\.com|api\.whatsapp\.com", re.I)

# ---------------------------------------------------------------------------
# Pakistani mobile prefixes
# Operators: Jazz/Warid (030x), Zong (031x), Ufone (033x), Telenor (034x),
#            SCO (082x, 086x)
# ---------------------------------------------------------------------------
_PK_MOBILE_PREFIXES = re.compile(
    r"""
    (?:                     # optional country code
        (?:\+|00)?92        # +92 or 0092
    )?
    (
        03(?:0[0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])  # 030x-035x
        |082[0-9]|086[0-9]                                  # SCO
    )
    [-\s]?\d{7}             # 7 more digits
    """,
    re.VERBOSE,
)

# Pakistani landline area codes (single-digit city code + 7 digits)
_PK_LANDLINE_PREFIX = re.compile(
    r"""
    (?:(?:\+|00)?92)?       # optional country code
    0?                      # optional leading zero
    (?:
        21|22|41|42|51|52|55|61|62|71|81|91|
        011|021|022|041|042|051|052|055|061|062|071|081|091
    )
    [-\s]?\d{7}
    """,
    re.VERBOSE,
)


def classify_phone(phone: str) -> str:
    """
    Classify a phone number as 'mobile', 'landline', or 'unknown'.

    Primary focus is Pakistani numbers; international mobiles are also
    detected via prefix analysis.
    """
    if not phone:
        return "unknown"

    digits = re.sub(r"[^\d+]", "", phone)

    # Strip country code for local analysis
    local = digits
    if local.startswith("+92") or local.startswith("0092"):
        local = "0" + local.lstrip("+").lstrip("0092")[2:]
    elif local.startswith("92") and len(local) == 12:
        local = "0" + local[2:]

    # Pakistani mobile: starts with 03xx
    if re.match(r"0(3\d{2})\d{7}$", local):
        return "mobile"

    # Other known international mobile patterns (India, UAE, US etc.)
    # Heuristic: 10-digit local number, not starting with known landline prefixes
    if re.match(r"03\d{9}$", digits) or re.match(r"3\d{9}$", digits):
        return "mobile"

    # Pakistani landline
    if _PK_LANDLINE_PREFIX.match(phone):
        return "landline"

    # Generic heuristic: if 10-11 digits and not known as landline → mobile
    if 10 <= len(digits) <= 11:
        return "mobile"

    return "unknown"


def to_whatsapp_number(phone: str) -> str | None:
    """
    Convert a Pakistani phone number to international WhatsApp format.

    03351234567 → 923351234567
    +923351234567 → 923351234567

    Returns the numeric string (no '+') or None if conversion fails.
    """
    if not phone:
        return None

    digits = re.sub(r"[^\d]", "", phone)

    # Already in international format with leading 92
    if digits.startswith("92") and len(digits) == 12:
        return digits

    # Local Pakistani format: 03xxxxxxxxx (11 digits)
    if digits.startswith("0") and len(digits) == 11:
        return "92" + digits[1:]

    # 10-digit without leading zero: 3xxxxxxxxxx
    if digits.startswith("3") and len(digits) == 10:
        return "92" + digits

    # International format starting with +92
    if len(digits) == 12 and digits.startswith("92"):
        return digits

    return None


def build_whatsapp_link(phone: str) -> str:
    """
    Return a wa.me deep-link for a confirmed mobile number, or '' if the
    number is not a mobile or cannot be normalised.
    """
    if not phone:
        return ""

    phone_type = classify_phone(phone)
    if phone_type == "landline":
        return ""          # Never generate WhatsApp for landlines

    wa_number = to_whatsapp_number(phone)
    if wa_number:
        return f"https://wa.me/{wa_number}"

    # Fallback: strip all non-digits and use as-is for non-Pakistani mobiles
    if phone_type == "mobile":
        digits = re.sub(r"[^\d]", "", phone)
        if 7 <= len(digits) <= 15:
            return f"https://wa.me/{digits}"

    return ""


def clean_phone(phone: str) -> str:
    """Normalise a phone number string."""
    if not phone:
        return ""
    cleaned = re.sub(r"[^\d+\s\-()]", "", phone).strip()
    return cleaned


# ---------------------------------------------------------------------------
# Lead classification
# ---------------------------------------------------------------------------

def classify_lead(website: str) -> str:
    """
    Classify a business based on its website URL.

    'No Website'          — no URL at all
    'No Online Presence'  — empty / garbage
    'Facebook Only'       — only Facebook page
    'Instagram Only'      — only Instagram profile
    'WhatsApp Only'       — only WhatsApp link
    'Social Only'         — other social platform
    'Has Website'         — real website → should be skipped
    """
    if not website or not website.strip():
        return "No Website"

    url = website.strip().lower()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        hostname = re.sub(r"^www\.", "", hostname)
    except Exception:
        return "No Website"

    if FACEBOOK_PATTERNS.search(hostname):
        return "Facebook Only"
    if INSTAGRAM_PATTERNS.search(hostname):
        return "Instagram Only"
    if WHATSAPP_PATTERNS.search(hostname):
        return "WhatsApp Only"
    if hostname in SOCIAL_DOMAINS or any(
        hostname.endswith("." + d) for d in SOCIAL_DOMAINS
    ):
        return "Social Only"

    return "Has Website"


def should_include_lead(website: str) -> bool:
    """Return True if the business should be collected as a lead."""
    return classify_lead(website) != "Has Website"


# ---------------------------------------------------------------------------
# Email extraction
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(
    r"""
    \b
    [A-Za-z0-9._%+\-]+          # local part
    @
    [A-Za-z0-9.\-]+             # domain
    \.
    [A-Za-z]{2,10}              # TLD
    \b
    """,
    re.VERBOSE,
)

# Domains we know are not real business emails
_EMAIL_BLACKLIST_DOMAINS = {
    "example.com", "test.com", "sentry.io", "google.com",
    "gmail.com", "email.com", "domain.com", "yoursite.com",
    "w3schools.com", "cloudflare.com",
}


def extract_email(text: str) -> str:
    """Extract the first plausible email address from arbitrary text."""
    if not text:
        return ""
    matches = _EMAIL_RE.findall(text)
    for m in matches:
        domain = m.split("@", 1)[1].lower()
        if domain not in _EMAIL_BLACKLIST_DOMAINS:
            return m.lower()
    return ""


# ---------------------------------------------------------------------------
# Social link helpers
# ---------------------------------------------------------------------------

def extract_instagram_from_text(text: str) -> str:
    patterns = [
        r"(instagram\.com/[A-Za-z0-9_.]+)",
        r"@([A-Za-z0-9_.]{3,30})",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(0)
    return ""


def extract_facebook_from_text(text: str) -> str:
    m = re.search(r"(facebook\.com/[^\s\"'>]+)", text, re.I)
    return m.group(0) if m else ""


def truncate(text: str, max_len: int = 60) -> str:
    """Truncate a string for display."""
    return text if len(text) <= max_len else text[: max_len - 3] + "..."
