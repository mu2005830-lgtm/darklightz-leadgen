"""
Database models and schema for Darklightz Lead Generator v2.0.
Uses SQLite via the built-in sqlite3 module — no external DB required.

v2.0 additions
--------------
* New columns: email, mobile, category, maps_link, latitude, longitude,
  opening_hours, website_status
* collections table for Lead Collections (Projects)
* collection_leads join table
* Automatic schema migration: existing databases gain the new columns
  without losing any data.
"""

import sqlite3
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Database path — stored in user's home dir so it survives reinstalls
# ---------------------------------------------------------------------------
DB_DIR = Path.home() / ".darklightz"
DB_PATH = DB_DIR / "leads.db"


def get_connection() -> sqlite3.Connection:
    """Return a database connection with row_factory set for dict-like access."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create all tables and run migrations if upgrading from v1."""
    conn = get_connection()
    with conn:
        conn.executescript("""
            -- ----------------------------------------------------------------
            -- Search sessions — one row per "Start Search" click
            -- ----------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS searches (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword     TEXT    NOT NULL,
                city        TEXT    NOT NULL,
                max_leads   INTEGER NOT NULL DEFAULT 100,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                status      TEXT    NOT NULL DEFAULT 'running'
                            CHECK(status IN ('running','complete','stopped'))
            );

            -- ----------------------------------------------------------------
            -- Leads — one row per business (v2.0 full schema)
            -- ----------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS leads (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                search_id        INTEGER REFERENCES searches(id) ON DELETE CASCADE,
                name             TEXT    NOT NULL DEFAULT '',
                category         TEXT             DEFAULT '',
                phone            TEXT             DEFAULT '',
                mobile           TEXT             DEFAULT '',
                whatsapp         TEXT             DEFAULT '',
                email            TEXT             DEFAULT '',
                instagram        TEXT             DEFAULT '',
                facebook         TEXT             DEFAULT '',
                website          TEXT             DEFAULT '',
                address          TEXT             DEFAULT '',
                maps_link        TEXT             DEFAULT '',
                latitude         TEXT             DEFAULT '',
                longitude        TEXT             DEFAULT '',
                rating           TEXT             DEFAULT '',
                reviews          TEXT             DEFAULT '',
                opening_hours    TEXT             DEFAULT '',
                lead_type        TEXT    NOT NULL DEFAULT 'No Website'
                                 CHECK(lead_type IN (
                                     'No Website','Social Only','No Online Presence',
                                     'Facebook Only','Instagram Only','WhatsApp Only'
                                 )),
                status           TEXT    NOT NULL DEFAULT 'New'
                                 CHECK(status IN (
                                     'New','Contacted','Follow-up',
                                     'Interested','Closed','Not Interested'
                                 )),
                notes            TEXT             DEFAULT '',
                city             TEXT             DEFAULT '',
                keyword          TEXT             DEFAULT '',
                created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at       TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE(name, phone, city)
            );

            -- ----------------------------------------------------------------
            -- Lead Collections (Projects) — named groups of leads
            -- ----------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS collections (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL UNIQUE,
                description TEXT             DEFAULT '',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            -- ----------------------------------------------------------------
            -- Collection membership — many-to-many
            -- ----------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS collection_leads (
                collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
                lead_id       INTEGER NOT NULL REFERENCES leads(id)       ON DELETE CASCADE,
                added_at      TEXT    NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (collection_id, lead_id)
            );

            -- ----------------------------------------------------------------
            -- App settings — key/value store
            -- ----------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS settings (
                key     TEXT PRIMARY KEY,
                value   TEXT NOT NULL DEFAULT ''
            );
        """)

    # ---- Schema migration: add new columns to existing leads table ----------
    _migrate_leads_table(conn)
    conn.close()


# ---------------------------------------------------------------------------
# Migration helpers
# ---------------------------------------------------------------------------

_NEW_COLUMNS = [
    ("category",      "TEXT DEFAULT ''"),
    ("mobile",        "TEXT DEFAULT ''"),
    ("email",         "TEXT DEFAULT ''"),
    ("maps_link",     "TEXT DEFAULT ''"),
    ("latitude",      "TEXT DEFAULT ''"),
    ("longitude",     "TEXT DEFAULT ''"),
    ("opening_hours", "TEXT DEFAULT ''"),
]


def _migrate_leads_table(conn: sqlite3.Connection) -> None:
    """Add any v2.0 columns that don't yet exist in the leads table."""
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(leads)").fetchall()
    }
    for col_name, col_def in _NEW_COLUMNS:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_def}")
