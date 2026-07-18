"""
Export leads to CSV — Darklightz Lead Generator v2.0.

v2.0: All new fields added (email, mobile, category, maps_link,
latitude, longitude, opening_hours).
"""

from __future__ import annotations

import csv
import os
from typing import Sequence

HEADERS = [
    "Business Name", "Category", "Phone", "Mobile", "WhatsApp", "Email",
    "Instagram", "Facebook", "Website", "Address", "Google Maps Link",
    "Latitude", "Longitude", "Rating", "Reviews", "Opening Hours",
    "Lead Type", "Status", "City", "Keyword", "Notes", "Date Added",
]

KEYS = [
    "name", "category", "phone", "mobile", "whatsapp", "email",
    "instagram", "facebook", "website", "address", "maps_link",
    "latitude", "longitude", "rating", "reviews", "opening_hours",
    "lead_type", "status", "city", "keyword", "notes", "created_at",
]


def export(leads: Sequence[dict], output_path: str) -> str:
    """Write *leads* to *output_path* (.csv).  Returns absolute path."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(HEADERS)
        for lead in leads:
            writer.writerow([str(lead.get(k, "") or "") for k in KEYS])

    return os.path.abspath(output_path)
