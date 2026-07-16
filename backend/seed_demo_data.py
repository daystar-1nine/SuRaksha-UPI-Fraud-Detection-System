import sqlite3
from datetime import datetime, timezone
import os

DB_PATH = 's:/Hackathon/SuRaksha/backend/fraud_history.db'

DUMMY_DATA = [
    # Fraudsters
    ("scammer@ybl", "Lottery Fraud", "CRITICAL"),
    ("kbc.reward@paytm", "Cashback Scam", "CRITICAL"),
    ("electricity.update@sbi", "Phishing Redirect", "CRITICAL"),
    ("kyc.helpdesk@icici", "Customer Care Fraud", "HIGH"),
    ("free.gift@okaxis", "Lottery Fraud", "HIGH"),
    ("refund.support@phonepe", "Refund Scam", "HIGH"),
    ("urgent.bill@hdfc", "Threat/Extortion", "HIGH"),
    ("lucky.winner@ybl", "Cashback Scam", "CRITICAL"),
    ("pm.scheme@sbi", "Government Spoof", "CRITICAL"),
    ("jio.recharge.offer@paytm", "Fake Offer", "HIGH"),
    
    # Trusted (These won't be blocked by complaints, but let's add some positive ones to whitelist if we want, or just let them pass as safe)
]

def seed_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insert complaints so the blacklist triggers
    for upi, fraud_type, risk in DUMMY_DATA:
        # Add 3 complaints for each to trigger the threshold
        for _ in range(3):
            cursor.execute('''
                INSERT INTO complaints (upi, description, reporter_ip)
                VALUES (?, ?, ?)
            ''', (upi, f"User reported {fraud_type}", "127.0.0.1"))
            
        # Add to history to sync blacklist
        cursor.execute('''
            INSERT INTO history (upi, fraud_type, risk_level, created_at)
            VALUES (?, ?, ?, ?)
        ''', (upi, fraud_type, risk, datetime.now(timezone.utc).isoformat()))
        
    conn.commit()
    conn.close()
    print("Successfully seeded database with demo data!")

if __name__ == '__main__':
    seed_db()
