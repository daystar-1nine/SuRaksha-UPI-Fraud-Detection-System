# backend/services/history_store.py

import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = "fraud_history.db"


# -------------------------------
# DB CONNECTION (SAFE 🔥)
# -------------------------------
@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# -------------------------------
# INIT DATABASE
# -------------------------------
def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upi TEXT,
            fraud_type TEXT,
            risk_level TEXT,
            created_at TEXT
        )
        """)

        # 🔥 Index for fast lookup
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_upi ON history (upi)
        """)


# -------------------------------
# SAVE CASE (OPTIMIZED 🔥)
# -------------------------------
def save_case(upi_ids, fraud_type, risk_level):
    if not upi_ids:
        return

    now = datetime.utcnow().isoformat()

    records = [
        (upi, fraud_type, risk_level, now)
        for upi in upi_ids
    ]

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.executemany("""
        INSERT INTO history (upi, fraud_type, risk_level, created_at)
        VALUES (?, ?, ?, ?)
        """, records)


# -------------------------------
# GET UPI COUNT
# -------------------------------
def get_upi_count(upi):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT COUNT(*) FROM history WHERE upi = ?
        """, (upi,))

        result = cursor.fetchone()
        return result[0] if result else 0


# -------------------------------
# 🔥 NEW: GET RECENT CASES
# -------------------------------
def get_recent_cases(limit=10):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT upi, fraud_type, risk_level, created_at
        FROM history
        ORDER BY created_at DESC
        LIMIT ?
        """, (limit,))

        return cursor.fetchall()


# -------------------------------
# 🔥 NEW: GET HIGH-RISK UPIs
# -------------------------------
def get_high_risk_upis():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT upi, COUNT(*) as count
        FROM history
        WHERE risk_level = 'HIGH'
        GROUP BY upi
        ORDER BY count DESC
        LIMIT 20
        """)

        return cursor.fetchall()