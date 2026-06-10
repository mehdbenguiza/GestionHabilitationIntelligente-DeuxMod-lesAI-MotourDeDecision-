
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)

def check_table(table_name):
    print(f"\n--- Columns in {table_name} ---")
    columns = inspector.get_columns(table_name)
    for column in columns:
        print(f" {column['name']}: {column['type']}")

check_table("tickets")
check_table("classification_results")
check_table("anomaly_logs")
check_table("automation_rules")
