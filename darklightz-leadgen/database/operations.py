"""
Database operations for Darklightz Lead Generator v2.0.

All new v2.0 fields (email, mobile, category, maps_link, latitude,
longitude, opening_hours) are handled here.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from database.models import get_connection


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


# ===========================================================================
# SEARCHES
# ===========================================================================

def create_search(keyword: str, city: str, max_leads: int) -> int:
    """Insert a new search session and return its id."""
    conn = get_connection()
    with conn:
        cur = conn.execute(
            "INSERT INTO searches (keyword, city, max_leads) VALUES (?, ?, ?)",
            (keyword, city, max_leads),
        )
    conn.close()
    return cur.lastrowid


def update_search_status(search_id: int, status: str) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "UPDATE searches SET status=? WHERE id=?",
            (status, search_id),
        )
    conn.close()


def get_searches(limit: int = 100) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM searches ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_searches_with_counts(limit: int = 500) -> list[dict]:
    """Return all search sessions with actual lead count per session."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT s.*, COUNT(l.id) AS lead_count
        FROM searches s
        LEFT JOIN leads l ON l.search_id = s.id
        GROUP BY s.id
        ORDER BY s.created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_search_by_id(search_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM searches WHERE id=?", (search_id,)
    ).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


# ===========================================================================
# LEADS
# ===========================================================================

def insert_lead(data: dict) -> int | None:
    """
    Insert a lead.  Returns the new row id, or None if a duplicate was
    detected (UNIQUE constraint on name, phone, city).
    """
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                """
                INSERT INTO leads (
                    search_id, name, category, phone, mobile, whatsapp, email,
                    instagram, facebook, website, address, maps_link,
                    latitude, longitude, rating, reviews, opening_hours,
                    lead_type, status, notes, city, keyword
                ) VALUES (
                    :search_id, :name, :category, :phone, :mobile, :whatsapp,
                    :email, :instagram, :facebook, :website, :address,
                    :maps_link, :latitude, :longitude, :rating, :reviews,
                    :opening_hours, :lead_type, :status, :notes, :city, :keyword
                )
                """,
                {
                    "search_id":    data.get("search_id"),
                    "name":         data.get("name", ""),
                    "category":     data.get("category", ""),
                    "phone":        data.get("phone", ""),
                    "mobile":       data.get("mobile", ""),
                    "whatsapp":     data.get("whatsapp", ""),
                    "email":        data.get("email", ""),
                    "instagram":    data.get("instagram", ""),
                    "facebook":     data.get("facebook", ""),
                    "website":      data.get("website", ""),
                    "address":      data.get("address", ""),
                    "maps_link":    data.get("maps_link", ""),
                    "latitude":     data.get("latitude", ""),
                    "longitude":    data.get("longitude", ""),
                    "rating":       data.get("rating", ""),
                    "reviews":      data.get("reviews", ""),
                    "opening_hours":data.get("opening_hours", ""),
                    "lead_type":    data.get("lead_type", "No Website"),
                    "status":       "New",
                    "notes":        data.get("notes", ""),
                    "city":         data.get("city", ""),
                    "keyword":      data.get("keyword", ""),
                },
            )
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None  # duplicate
    finally:
        conn.close()


def get_leads(
    status: str | None = None,
    search_id: int | None = None,
    keyword: str | None = None,
) -> list[dict]:
    """Return leads with optional filters."""
    conn = get_connection()
    clauses: list[str] = []
    params: list[Any] = []

    if status and status != "All":
        clauses.append("status = ?")
        params.append(status)
    if search_id is not None:
        clauses.append("search_id = ?")
        params.append(search_id)
    if keyword:
        clauses.append(
            "(name LIKE ? OR address LIKE ? OR phone LIKE ? "
            "OR email LIKE ? OR category LIKE ?)"
        )
        like = f"%{keyword}%"
        params.extend([like, like, like, like, like])

    sql = "SELECT * FROM leads"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY created_at DESC"

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_lead_by_id(lead_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def update_lead_status(lead_id: int, status: str) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "UPDATE leads SET status=?, updated_at=datetime('now') WHERE id=?",
            (status, lead_id),
        )
    conn.close()


def update_lead_notes(lead_id: int, notes: str) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "UPDATE leads SET notes=?, updated_at=datetime('now') WHERE id=?",
            (notes, lead_id),
        )
    conn.close()


def update_lead_field(lead_id: int, field: str, value: str) -> None:
    """Update an arbitrary editable field (notes, status)."""
    allowed = {"notes", "status"}
    if field not in allowed:
        raise ValueError(f"Field '{field}' is not editable via this function.")
    conn = get_connection()
    with conn:
        conn.execute(
            f"UPDATE leads SET {field}=?, updated_at=datetime('now') WHERE id=?",
            (value, lead_id),
        )
    conn.close()


def delete_lead(lead_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM leads WHERE id=?", (lead_id,))
    conn.close()


def delete_leads_by_search(search_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM leads WHERE search_id=?", (search_id,))
    conn.close()


def get_total_leads() -> int:
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    conn.close()
    return count


# ===========================================================================
# DASHBOARD STATS
# ===========================================================================

def get_dashboard_stats() -> dict:
    conn = get_connection()
    stats: dict[str, Any] = {}

    stats["total_leads"]  = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    stats["total_searches"] = conn.execute("SELECT COUNT(*) FROM searches").fetchone()[0]
    stats["new_leads"]    = conn.execute("SELECT COUNT(*) FROM leads WHERE status='New'").fetchone()[0]
    stats["contacted"]    = conn.execute("SELECT COUNT(*) FROM leads WHERE status='Contacted'").fetchone()[0]
    stats["interested"]   = conn.execute("SELECT COUNT(*) FROM leads WHERE status='Interested'").fetchone()[0]
    stats["closed"]       = conn.execute("SELECT COUNT(*) FROM leads WHERE status='Closed'").fetchone()[0]
    stats["follow_up"]    = conn.execute("SELECT COUNT(*) FROM leads WHERE status='Follow-up'").fetchone()[0]

    # Lead type breakdown
    stats["no_website"]   = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE lead_type='No Website'"
    ).fetchone()[0]
    stats["social_only"]  = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE lead_type IN "
        "('Social Only','Facebook Only','Instagram Only','WhatsApp Only')"
    ).fetchone()[0]

    # Recent searches
    rows = conn.execute(
        "SELECT keyword, city, created_at, status FROM searches "
        "ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    stats["recent_searches"] = [_row_to_dict(r) for r in rows]

    conn.close()
    return stats


# ===========================================================================
# COLLECTIONS
# ===========================================================================

def create_collection(name: str, description: str = "") -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute(
            "INSERT INTO collections (name, description) VALUES (?, ?)",
            (name, description),
        )
    conn.close()
    return cur.lastrowid


def get_collections() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT c.*, COUNT(cl.lead_id) as lead_count "
        "FROM collections c "
        "LEFT JOIN collection_leads cl ON cl.collection_id = c.id "
        "GROUP BY c.id ORDER BY c.created_at DESC"
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_collection_leads(collection_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT l.* FROM leads l "
        "JOIN collection_leads cl ON cl.lead_id = l.id "
        "WHERE cl.collection_id = ? ORDER BY cl.added_at DESC",
        (collection_id,),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def add_leads_to_collection(collection_id: int, lead_ids: list[int]) -> int:
    """Add leads to a collection.  Returns number of leads actually added."""
    conn = get_connection()
    added = 0
    with conn:
        for lead_id in lead_ids:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO collection_leads "
                    "(collection_id, lead_id) VALUES (?, ?)",
                    (collection_id, lead_id),
                )
                added += 1
            except sqlite3.IntegrityError:
                pass
    conn.close()
    return added


def remove_lead_from_collection(collection_id: int, lead_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "DELETE FROM collection_leads WHERE collection_id=? AND lead_id=?",
            (collection_id, lead_id),
        )
    conn.close()


def delete_collection(collection_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM collections WHERE id=?", (collection_id,))
    conn.close()


def rename_collection(collection_id: int, name: str) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "UPDATE collections SET name=?, updated_at=datetime('now') WHERE id=?",
            (name, collection_id),
        )
    conn.close()


# ===========================================================================
# SETTINGS
# ===========================================================================

def get_setting(key: str, default: str = "") -> str:
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
    conn.close()


def get_all_settings() -> dict:
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}
