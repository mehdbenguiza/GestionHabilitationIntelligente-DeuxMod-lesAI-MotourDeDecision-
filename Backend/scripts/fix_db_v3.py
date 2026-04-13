# scripts/fix_db_v3.py
import sqlite3
import os

def fix_database():
    db_path = 'test.db'
    if not os.path.exists(db_path):
        print(f"❌ Base de données {db_path} introuvable.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🚀 Début de la réparation de la base de données...")

    # 1. Ajout des colonnes manquantes dans classification_results
    # On liste toutes les colonnes cibles
    target_columns = [
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

    # Récupérer les colonnes actuelles
    cursor.execute("PRAGMA table_info(classification_results)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    for col_name, col_type in target_columns:
        if col_name not in existing_columns:
            try:
                print(f"➕ Ajout de la colonne {col_name}...")
                cursor.execute(f"ALTER TABLE classification_results ADD COLUMN {col_name} {col_type}")
                conn.commit()
            except Exception as e:
                print(f"⚠️ Erreur lors de l'ajout de {col_name}: {e}")
        else:
            print(f"✅ Colonne {col_name} déjà présente.")

    # 2. Vérification / Création de audit_logs si nécessaire
    # (Parfois create_all échoue si le schéma est en TIME_WAIT ou verrouillé)
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
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
        print("✅ Table audit_logs vérifiée/créée.")
    except Exception as e:
        print(f"⚠️ Erreur audit_logs: {e}")

    conn.close()
    print("✨ Réparation terminée !")

if __name__ == "__main__":
    fix_database()
