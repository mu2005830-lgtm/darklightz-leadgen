"""
Export leads to PDF — Darklightz Lead Generator v2.0.

v2.0: All new fields (email, mobile, category, maps_link, latitude,
longitude, opening_hours) included.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable,
)


# ---------------------------------------------------------------------------
# Theme colours (Catppuccin Mocha)
# ---------------------------------------------------------------------------
C_DARK    = colors.HexColor("#1E1E2E")
C_SURFACE = colors.HexColor("#313244")
C_ALT     = colors.HexColor("#181825")
C_ACCENT  = colors.HexColor("#CBA6F7")
C_TEXT    = colors.HexColor("#CDD6F4")
C_MUTED   = colors.HexColor("#A6ADC8")

COLUMNS = [
    ("Name",          "name",          38 * mm),
    ("Category",      "category",      28 * mm),
    ("Phone",         "phone",         28 * mm),
    ("Mobile",        "mobile",        28 * mm),
    ("WhatsApp",      "whatsapp",      40 * mm),
    ("Email",         "email",         40 * mm),
    ("Instagram",     "instagram",     40 * mm),
    ("Facebook",      "facebook",      40 * mm),
    ("Website",       "website",       40 * mm),
    ("Address",       "address",       48 * mm),
    ("Rating",        "rating",        14 * mm),
    ("Reviews",       "reviews",       16 * mm),
    ("Lead Type",     "lead_type",     24 * mm),
    ("Status",        "status",        22 * mm),
    ("City",          "city",          20 * mm),
    ("Date Added",    "created_at",    28 * mm),
]


def export(leads: Sequence[dict], output_path: str) -> str:
    """Write *leads* to a landscape PDF at *output_path*."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Darklightz Lead Generator — Export",
        author="Darklightz Studio",
    )

    styles   = getSampleStyleSheet()
    elements = []

    # ---- Header ---------------------------------------------------------
    title_style = ParagraphStyle(
        "DLTitle",
        parent=styles["Heading1"],
        textColor=C_ACCENT,
        fontSize=16,
        spaceAfter=2,
        fontName="Helvetica-Bold",
    )
    sub_style = ParagraphStyle(
        "DLSub",
        parent=styles["Normal"],
        textColor=C_MUTED,
        fontSize=8,
        spaceAfter=8,
    )

    elements.append(
        Paragraph("Darklightz Studio — Lead Generation Suite", title_style)
    )
    elements.append(
        Paragraph(
            f"Exported {len(leads)} leads  ·  {datetime.now().strftime('%Y-%m-%d %H:%M')}  "
            f"·  Developed by Darklightz Studio",
            sub_style,
        )
    )
    elements.append(HRFlowable(width="100%", color=C_SURFACE, thickness=1))
    elements.append(Spacer(1, 4 * mm))

    # ---- Table ----------------------------------------------------------
    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        textColor=C_TEXT,
        fontSize=7,
        leading=9,
        wordWrap="CJK",
    )

    col_labels = [Paragraph(f"<b>{col[0]}</b>", ParagraphStyle(
        "Hdr", parent=styles["Normal"],
        textColor=C_ACCENT, fontSize=7.5,
        fontName="Helvetica-Bold",
    )) for col in COLUMNS]
    col_keys   = [col[1] for col in COLUMNS]
    col_widths = [col[2] for col in COLUMNS]

    table_data = [col_labels]
    for lead in leads:
        row = [
            Paragraph(str(lead.get(key, "") or ""), cell_style)
            for key in col_keys
        ]
        table_data.append(row)

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)

    row_count   = len(table_data)
    row_bg_cmds = [
        ("BACKGROUND", (0, i), (-1, i), C_ALT if i % 2 == 0 else C_DARK)
        for i in range(1, row_count)
    ]

    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), C_SURFACE),
        ("TEXTCOLOR",    (0, 0), (-1, 0), C_ACCENT),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 8),
        ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
        ("VALIGN",       (0, 0), (-1, 0), "MIDDLE"),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 7.5),
        ("VALIGN",       (0, 1), (-1, -1), "TOP"),
        ("TEXTCOLOR",    (0, 1), (-1, -1), C_TEXT),
        ("GRID",         (0, 0), (-1, -1), 0.3, C_SURFACE),
        ("LEFTPADDING",  (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        *row_bg_cmds,
    ]))

    elements.append(tbl)
    doc.build(elements)
    return os.path.abspath(output_path)
