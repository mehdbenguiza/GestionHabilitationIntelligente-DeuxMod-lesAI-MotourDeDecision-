import sqlite3
import os

db_path = "test.db"

def alter_db():
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    new_columns = [
        ("risk_score_rules", "INTEGER"),
        ("decision_source", "VARCHAR(50) DEFAULT 'HYBRID (ML + RULES)'"),
        ("consistency_status", "VARCHAR(20)"),
        ("consistency_message", "TEXT"),
        ("triggered_rules", "JSON"),
        ("recommended_action", "VARCHAR(50)"),
        ("confidence_level_label", "VARCHAR(50)")
    ]

    for col_name, col_type in new_columns:
        try:
            print(f"Adding column {col_name} to classification_results...")
            cur.execute(f"ALTER TABLE classification_results ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding {col_name}: {e}")

    conn.commit()
    conn.close()
    print("Database upgrade completed successfully.")

if __name__ == "__main__":
    alter_db()
