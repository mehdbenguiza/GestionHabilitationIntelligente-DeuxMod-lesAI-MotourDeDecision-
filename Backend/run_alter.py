import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import engine
from sqlalchemy import text

def add_column():
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE dashboard_users ADD COLUMN profile_image VARCHAR(255)"))
            print("Successfully added profile_image column")
    except Exception as e:
        print(f"Error adding column (it might already exist): {e}")

if __name__ == '__main__':
    add_column()
