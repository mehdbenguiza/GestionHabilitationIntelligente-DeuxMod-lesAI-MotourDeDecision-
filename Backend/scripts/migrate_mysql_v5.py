# scripts/migrate_mysql_v5.py
import os
import pymysql
from dotenv import load_dotenv
from urllib.parse import urlparse

# Charger le .env
load_dotenv(dotenv_path='app/.env')

def migrate():
    db_url = os.getenv("DATABASE_URL")
    if not db_url or "mysql" not in db_url:
        print("❌ DATABASE_URL n'est pas configuré pour MySQL.")
        return

    # Parser l'URL (mysql+pymysql://root:@localhost:3306/itop_dashboard)
    raw_url = db_url.replace("mysql+pymysql://", "http://")
    url = urlparse(raw_url)
    db_name = url.path[1:]
    user = url.username
    password = url.password or ""
    host = url.hostname
    port = url.port or 3306

    print(f"🚀 Migration MySQL sur {db_name}@{host}:{port}...")

    try:
        conn = pymysql.connect(
            host=host, port=port, user=user, password=password, db=db_name
        )
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Erreur connexion MySQL : {e}")
        return

    def add_column_if_missing(table, col_name, col_type):
        try:
            # Vérifier si la table existe avant
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if not cursor.fetchone():
                return
                
            cursor.execute(f"SHOW COLUMNS FROM {table} LIKE '{col_name}'")
            if cursor.fetchone():
                print(f"ℹ️ [{table}] {col_name} déjà présent.")
                return
            
            print(f"➕ [{table}] Ajout de {col_name}...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
            conn.commit()
        except Exception as e:
            print(f"⚠️ Erreur sur {table}.{col_name}: {e}")

    # --- 0. Table: employees (Crucial pour la simulation) ---
    print("\n🛠️ Vérification table employees...")
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            team VARCHAR(50),
            role VARCHAR(50),
            seniority VARCHAR(20) DEFAULT 'junior'
        )
        """)
        
        # Vérifier si vide et injecter quelques testeurs
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        if count == 0:
            print("📦 Injection de quelques employés de test...")
            test_data = [
                ('EMP-001', 'Mehdi Ben Guiza', 'mehdi@biat.tn', 'MOE', 'DEVELOPPEUR', 'senior'),
                ('EMP-002', 'Admin Test', 'admin@biat.tn', 'SECURITE', 'RSSI', 'senior'),
                ('EMP-003', 'Junior Dev', 'junior@biat.tn', 'MOE', 'STAGIAIRE', 'junior'),
                ('EMP-004', 'Analyste SOC', 'soc@biat.tn', 'SECURITE', 'ANALYSTE_SOC', 'junior'),
            ]
            cursor.executemany("INSERT INTO employees (id, name, email, team, role, seniority) VALUES (%s, %s, %s, %s, %s, %s)", test_data)
        print("✅ Table employees OK.")
    except Exception as e:
        print(f"⚠️ Erreur employees: {e}")

    # --- 1. Table: classification_results ---
    print("\n🛠️ Vérification table classification_results...")
    columns_classification = [
        ('explanation', 'TEXT'),
        ('risk_factors', 'JSON'),
        ('source', "VARCHAR(30) DEFAULT 'model'"),
        ('risk_score_rules', 'INT'),
        ('decision_source', "VARCHAR(50) DEFAULT 'HYBRID (ML + RULES)'"),
        ('consistency_status', 'VARCHAR(20)'),
        ('consistency_message', 'TEXT'),
        ('triggered_rules', 'JSON'),
        ('recommended_action', 'VARCHAR(50)'),
        ('confidence_level_label', 'VARCHAR(50)')
    ]
    for col, ctype in columns_classification:
        add_column_if_missing('classification_results', col, ctype)

    # --- 2. Table: tickets ---
    print("\n🛠️ Vérification table tickets...")
    columns_tickets = [
        ('ai_level', 'VARCHAR(20)'),
        ('ai_confidence', 'FLOAT'),
        ('ai_probabilities', 'JSON'),
        ('ai_risk_score', 'INT'),
        ('ai_consistency', 'VARCHAR(20)'),
        ('ai_recommended_action', 'VARCHAR(50)')
    ]
    for col, ctype in columns_tickets:
        add_column_if_missing('tickets', col, ctype)

    # --- 3. Table: audit_logs ---
    print("\n🛠️ Vérification table audit_logs...")
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ticket_id INT,
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
        print("✅ Table audit_logs OK.")
    except Exception as e:
        print(f"⚠️ Erreur audit_logs: {e}")

    conn.commit()
    conn.close()
    print("\n✨ Migration MySQL terminée !")

if __name__ == "__main__":
    migrate()
