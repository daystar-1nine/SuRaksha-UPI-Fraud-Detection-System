# backend/services/history_store.py
"""SQLite persistent history store for UPI threats, complaints, and user feedback."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Tuple
from functools import lru_cache
from config import settings

DB_PATH = settings.DATABASE_PATH


# -------------------------------
# DB CONNECTION (SAFE 🔥)
# -------------------------------
@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Provides a thread-safe context managed SQLite connection with automatic rollback."""
    conn = sqlite3.connect(DB_PATH, timeout=20.0, check_same_thread=False)
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
def init_db() -> None:
    """Initializes schema tables and indexes in the SQLite history database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")  # Enable concurrent reads/writes

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

        # UPI Directory for Safe/Unsafe categories
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS upi_directory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upi_id TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            subtype TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_directory_upi ON upi_directory (upi_id)")

        # Seed initial data for faculty demo
        cursor.execute("SELECT COUNT(*) FROM upi_directory")
        if cursor.fetchone()[0] == 0:
            seeds = [
                # Safe Business
                ("sharmakirana@upi", "safe", "business", "Sharma Kirana Store", "Verified local grocery merchant"),
                ("starcafe@upi", "safe", "business", "Star Cafe", "Verified food and beverage outlet"),
                ("arogyamedical@upi", "safe", "business", "Arogya Pharmacy", "Verified healthcare pharmacy store"),
                ("bookstore@paytm", "safe", "business", "Gyan Book Store", "Verified retail bookstore"),
                ("supermart@okhdfcbank", "safe", "business", "Big Basket Supermart", "Verified grocery merchant"),
                
                # Safe Personal
                ("surajsawant@okaxis", "safe", "personal", "Suraj Sawant", "Verified student account"),
                ("facultyadmin@sbi", "safe", "personal", "College Faculty Advisor", "Verified academic advisor account"),
                ("studentunion@icici", "safe", "personal", "Student Activity Fund", "Verified institutional group account"),
                ("rahulsharma@ybl", "safe", "personal", "Rahul Sharma", "Verified personal account"),
                ("priyasingh@okicici", "safe", "personal", "Priya Singh", "Verified personal account"),
                
                # Unsafe Fraud
                ("scammer@ybl", "unsafe", "fraud", "Fake GPay Rewards Portal", "KYC phishing reward scam"),
                ("prizeclaim@okaxis", "unsafe", "fraud", "KBC Lottery Center", "Fake lottery cashback sweepstakes"),
                ("phishingtrap@okhdfcbank", "unsafe", "fraud", "Phishing Collect Request", "Unverified money collect pressure trap"),
                
                # Unsafe Criminal
                ("electricitysupport@paytm", "unsafe", "criminal", "Fake Electricity Support", "Utility bill payment phishing desk"),
                ("fakebillpay@sbi", "unsafe", "criminal", "SBI Bill Pay Spoof", "Typosquat bank portal redirect link")
            ]
            cursor.executemany("""
            INSERT OR IGNORE INTO upi_directory (upi_id, category, subtype, name, description)
            VALUES (?, ?, ?, ?, ?)
            """, seeds)


# -------------------------------
# SAVE CASE (OPTIMIZED 🔥)
# -------------------------------
def save_case(upi_ids: List[str], fraud_type: str | None, risk_level: str | None) -> None:
    """Saves analyzed UPI threat records to the database history.

    Args:
        upi_ids: List of extracted UPI addresses.
        fraud_type: Type of threat identified (e.g. Cashback Trap).
        risk_level: Aggregated risk classification (e.g. HIGH, CRITICAL).
    """
    if not upi_ids:
        return

    now = datetime.now(timezone.utc).isoformat()

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
        
    get_upi_count.cache_clear()


# -------------------------------
# GET UPI COUNT
# -------------------------------
@lru_cache(maxsize=1024)
def get_upi_count(upi: str) -> int:
    """Returns the total number of times a UPI address was flagged in the history."""
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
def get_recent_cases(limit: int = 10) -> List[Tuple[str, str | None, str | None, str]]:
    """Fetches the most recent threat events recorded in the system."""
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
def get_high_risk_upis() -> List[Tuple[str, int]]:
    """Returns a list of high-risk blacklisted UPIs sorted by frequency."""
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
def save_complaint(upi: str, description: str = "", reporter_ip: str = "") -> None:
    """Saves a user-submitted fraud complaint and adds the target address to history.

    Args:
        upi: Target UPI VPA reported.
        description: Fraud details described by user.
        reporter_ip: Remote address of reporter.
    """
    now = datetime.now(timezone.utc).isoformat()
    clean_upi = upi.lower().strip()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO complaints (upi, description, reporter_ip, created_at)
        VALUES (?, ?, ?, ?)
        """, (clean_upi, description[:500], reporter_ip, now))

    # Also record into history so it affects blacklist
    save_case([clean_upi], "User Report", "HIGH")


# -------------------------------
# 🔥 GET PLATFORM STATS
# -------------------------------
def get_stats() -> Dict[str, int]:
    """Returns aggregated platform metrics for the trust stats bar."""
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
def save_reported_scam(text: str, category: str) -> None:
    """Persists reported fraud description snippet to feed Naive Bayes pipeline."""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO reported_scams (text, category, created_at)
        VALUES (?, ?, ?)
        """, (text.strip(), category, now))


# -------------------------------
# GET ALL REPORTED SCAMS FOR TRAINING
# -------------------------------
def get_reported_scams() -> List[Tuple[str, str]]:
    """Queries all historical user scam submissions for Naive Bayes reinforcement."""
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


# -------------------------------
# LOOKUP UPI IN DIRECTORY
# -------------------------------
@lru_cache(maxsize=256)
def lookup_upi_in_directory(upi_id: str) -> dict | None:
    """Queries the custom upi_directory table for verified safe/unsafe statuses."""
    if not upi_id:
        return None
    clean_upi = upi_id.lower().strip()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT category, subtype, name, description
            FROM upi_directory
            WHERE upi_id = ?
            """, (clean_upi,))
            row = cursor.fetchone()
            if row:
                return {
                    "upi_id": clean_upi,
                    "category": row[0],
                    "subtype": row[1],
                    "name": row[2],
                    "description": row[3]
                }
    except Exception:
        pass
    return None