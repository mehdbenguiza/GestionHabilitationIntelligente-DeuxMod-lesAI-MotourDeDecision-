import sqlite3

def upgrade():
    try:
        conn = sqlite3.connect('d:\\ProjetPFE\\Backend\\itop_ai.db')
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE dashboard_users ADD COLUMN profile_image VARCHAR(255)")
        conn.commit()
        conn.close()
        print("Successfully added profile_image column to dashboard_users")
    except Exception as e:
        print(f"Error or column already exists: {e}")

if __name__ == '__main__':
    upgrade()
