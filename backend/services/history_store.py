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

        # Check if created_at column exists in history table (for backwards compatibility)
        cursor.execute("PRAGMA table_info(history)")
        columns = [col[1] for col in cursor.fetchall()]
        if columns and "created_at" not in columns:
            cursor.execute("ALTER TABLE history ADD COLUMN created_at TEXT")

        # User-submitted fraud reports
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upi TEXT NOT NULL,
            description TEXT,
            reporter_ip TEXT,
            created_at TEXT
        )
        """)

        # Feedback scam messages for Naive Bayes dynamic training
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reported_scams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            category TEXT NOT NULL,
            created_at TEXT
        )
        """)

        # 🔥 Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_upi ON history (upi)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_complaint_upi ON complaints (upi)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reported_scams_cat ON reported_scams (category)")


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


# -------------------------------
# 🔥 SAVE USER COMPLAINT
# -------------------------------
def save_complaint(upi, description="", reporter_ip=""):
    """Save a user-submitted fraud complaint"""
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO complaints (upi, description, reporter_ip, created_at)
        VALUES (?, ?, ?, ?)
        """, (upi.lower().strip(), description[:500], reporter_ip, now))

    # Also record into history so it affects blacklist
    save_case([upi.lower().strip()], "User Report", "HIGH")


# -------------------------------
# 🔥 GET PLATFORM STATS
# -------------------------------
def get_stats():
    """Return aggregate stats for trust-building widget"""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM history")
        total_scans = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT COUNT(*) FROM history
            WHERE risk_level IN ('HIGH', 'CRITICAL')
        """)
        threats_caught = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT COUNT(DISTINCT upi) FROM history
            WHERE upi IS NOT NULL AND upi != ''
        """)
        unique_frauds = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM complaints")
        total_reports = cursor.fetchone()[0] or 0

    return {
        "total_scans": total_scans,
        "threats_caught": threats_caught,
        "unique_frauds": unique_frauds,
        "total_reports": total_reports
    }


# -------------------------------
# SAVE REPORTED SCAM FOR TRAINING
# -------------------------------
def save_reported_scam(text, category):
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO reported_scams (text, category, created_at)
        VALUES (?, ?, ?)
        """, (text.strip(), category, now))


# -------------------------------
# GET ALL REPORTED SCAMS FOR TRAINING
# -------------------------------
def get_reported_scams():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT text, category FROM reported_scams
            """)
            return cursor.fetchall()
    except sqlite3.OperationalError:
        # Table might not exist yet if database was not initialized
        return []