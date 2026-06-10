
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("Adding columns to anomaly_logs...")
    try:
        conn.execute(text("ALTER TABLE anomaly_logs ADD COLUMN status VARCHAR(20) DEFAULT 'PENDING'"))
    except Exception as e:
        print(f"Status column might already exist: {e}")
        
    try:
        conn.execute(text("ALTER TABLE anomaly_logs ADD COLUMN resolved_at DATETIME"))
    except Exception as e:
        print(f"Resolved_at column might already exist: {e}")
        
    conn.commit()
    print("Done.")
