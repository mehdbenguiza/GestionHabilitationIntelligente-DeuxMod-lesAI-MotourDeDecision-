# scripts/fix_db_v4.py
import sqlite3
import os

def fix_database():
    db_path = 'test.db'
    if not os.path.exists(db_path):
        print(f"❌ Base de données {db_path} introuvable.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🚀 Début de la migration de consolidation (V4)...")

    # --- 1. Fix Table: classification_results ---
    columns_classification = [
        ('explanation', 'TEXT'),
        ('risk_factors', 'JSON'),
        ('source', "VARCHAR(30) DEFAULT 'model'"),
        ('risk_score_rules', 'INTEGER'),
        ('decision_source', "VARCHAR(50) DEFAULT 'HYBRID (ML + RULES)'"),
        ('consistency_status', 'VARCHAR(20)'),
        ('consistency_message', 'TEXT'),
        ('triggered_rules', 'JSON'),
        ('recommended_action', 'VARCHAR(50)'),
        ('confidence_level_label', 'VARCHAR(50)')
    ]

    cursor.execute("PRAGMA table_info(classification_results)")
    existing_classification = [row[1] for row in cursor.fetchall()]

    for col_name, col_type in columns_classification:
        if col_name not in existing_classification:
            try:
                print(f"➕ [classification_results] Ajout de {col_name}...")
                cursor.execute(f"ALTER TABLE classification_results ADD COLUMN {col_name} {col_type}")
                conn.commit()
            except Exception as e:
                print(f"⚠️ Erreur {col_name}: {e}")

    # --- 2. Fix Table: tickets ---
    columns_tickets = [
        ('ai_level', 'VARCHAR(20)'),
        ('ai_confidence', 'FLOAT'),
        ('ai_probabilities', 'JSON'),
        ('ai_risk_score', 'INTEGER'),
        ('ai_consistency', 'VARCHAR(20)'),
        ('ai_recommended_action', 'VARCHAR(50)')
    ]

    cursor.execute("PRAGMA table_info(tickets)")
    existing_tickets = [row[1] for row in cursor.fetchall()]

    for col_name, col_type in columns_tickets:
        if col_name not in existing_tickets:
            try:
                print(f"➕ [tickets] Ajout de {col_name}...")
                cursor.execute(f"ALTER TABLE tickets ADD COLUMN {col_name} {col_type}")
                conn.commit()
            except Exception as e:
                print(f"⚠️ Erreur {col_name}: {e}")

    # --- 3. Table audit_logs ---
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'")
        if not cursor.fetchone():
            print("➕ Création de la table audit_logs...")
            cursor.execute("""
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER,
                ticket_ref VARCHAR(50),
                acteur_name VARCHAR(100) NOT NULL,
                acteur_role VARCHAR(50) NOT NULL,
                action VARCHAR(100) NOT NULL,
                categorie VARCHAR(50) DEFAULT 'Ticket',
                environnement VARCHAR(50),
                resultat VARCHAR(50) DEFAULT 'Succès',
                niveau_acces VARCHAR(50),
                details JSON,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()
    except Exception as e:
        print(f"⚠️ Erreur audit_logs: {e}")

    conn.close()
    print("✨ Migration V4 terminée avec succès !")

if __name__ == "__main__":
    fix_database()
