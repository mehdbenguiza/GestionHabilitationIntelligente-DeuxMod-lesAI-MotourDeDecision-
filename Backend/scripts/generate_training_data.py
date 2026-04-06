# scripts/generate_training_data.py

import pandas as pd
import random
import os
from datetime import datetime, timedelta

# ==================== DONNÉES DE BASE ====================

TEAMS = ["MOE", "MOA", "RESEAU", "SECURITE", "TEST_FACTORY", "DATA", "MXP"]
APPLICATIONS = ["MXP", "QUANTARA", "T24"]
ENVIRONMENTS = ["DEV2", "DVR", "QL2", "CRT", "INV", "PRD"]
ACCESS_TYPES = ["READ", "WRITE", "EXECUTE", "UPDATE", "DELETE", "FULL_ACCESS"]
RESOURCES = ["PRODUCTION", "PERSONAL_DATA", "OTHER"]

ROLES_PER_TEAM = {
    "MOE": ["DEVELOPPEUR", "TECH_LEAD", "CHEF_DE_PROJET", "STAGIAIRE"],
    "MOA": ["BUSINESS_ANALYST", "PRODUCT_OWNER", "CHEF_DE_PROJET"],
    "RESEAU": ["INGENIEUR_RESEAU", "ADMINISTRATEUR", "STAGIAIRE"],
    "SECURITE": ["ANALYSTE_SOC", "RSSI", "PENTESTER"],
    "TEST_FACTORY": ["TESTEUR_QA", "TEST_LEAD", "AUTOMATICIEN"],
    "DATA": ["DATA_SCIENTIST", "DATA_ENGINEER", "DATA_ANALYST"],
    "MXP": ["INTEGRATEUR", "CHEF_DE_PROJET", "DEVELOPPEUR_MXP"]
}

# Rôles avec pouvoirs étendus
MANAGERS = ["CHEF_DE_PROJET", "TECH_LEAD", "PRODUCT_OWNER", "ADMINISTRATEUR", "RSSI", "TEST_LEAD"]
# Rôles ne devant pas toucher au critique backend technique sans encadrement
RESTRICTED = ["STAGIAIRE", "BUSINESS_ANALYST"]

# ==================== RÈGLES DE CLASSIFICATION METIER ====================

def get_label(team, role, application, environment, access_type, resource):
    """Détermine le label selon la logique de la banque et du rôle"""
    
    # 🔴 RÈGLES CRITIQUES (Doute fort / Changements destructifs)
    # 1. Privilèges extrêmes en Prod ou pré-prod (INV, CRT) - Seul un administrateur ou Tech Lead peut faire ça sous exception, sinon critique total
    if access_type in ["FULL_ACCESS", "DELETE"] and environment in ["PRD", "INV", "CRT"]:
        return "CRITICAL"
        
    # 2. Les Stagiaires ou Business Analyst qui demandent des droits d'écriture techniques !
    if role in RESTRICTED and access_type != "READ":
        return "CRITICAL"
    
    # 3. Développeur (MOE) / QA avec droits d'écriture/modif en Prod (Normalement interdit sauf exception majeure)
    if team in ["MOE", "TEST_FACTORY", "MXP"] and environment in ["PRD", "INV"] and access_type != "READ":
        # Même un chef de projet ne devrait pas toucher à la prod directement, mais laissons une différence si c'est un DEV normal
        if role not in MANAGERS:
            return "CRITICAL"
        else:
            return "SENSITIVE" # Un Tech Lead a le droit de demander pour l'équipe, on garde ça Sensible
        
    # 4. Toucher aux données personnelles ou de production en PRD
    if resource in ["PERSONAL_DATA", "PRODUCTION"] and environment == "PRD" and access_type != "READ":
        # Seul un Data Engineer ou Sécurité devrait avoir un passe-droit sensible, le reste c'est Critique
        if role not in ["DATA_ENGINEER", "ANALYSTE_SOC", "PENTESTER"]:
            return "CRITICAL"
        
    # 5. Modification de l'application Core Banking T24
    if application == "T24" and environment == "PRD" and access_type != "READ":
        return "CRITICAL"
        
    # 🟠 RÈGLES SENSIBLES (Match moyen / Suspect mais plausible)
    # 1. MOE demandant de l'écriture en qualif ou certif (Standard pour un Lead, mais Sensible pour un junior)
    if team in ["MOE", "MXP"] and environment in ["QL2", "CRT"] and access_type in ["WRITE", "UPDATE", "EXECUTE", "DELETE"]:
        return "SENSITIVE"
        
    # 2. N'importe quel accès en PRD ou INV (même READ), si pas déjà critique
    if environment in ["PRD", "INV"]:
        return "SENSITIVE"
        
    # 3. Accès aux données personnelles
    if resource == "PERSONAL_DATA":
        return "SENSITIVE"
        
    # 4. Équipes de sécurité demandant des accès non-standards dans les envs inférieurs
    if team in ["SECURITE", "RESEAU"] and access_type in ["FULL_ACCESS", "DELETE"]:
        return "SENSITIVE"
        
    # 🟢 RÈGLES BASE (Match logique total)
    # 1. Accès DEV pour les développeurs:
    if team in ["MOE", "MXP"] and environment in ["DEV2", "DVR"]:
        return "BASE"
        
    # 2. Test factory / MOA en qualif/certif en lecture et exe:
    if team in ["TEST_FACTORY", "MOA"] and environment in ["QL2", "CRT"]:
        if access_type in ["READ", "EXECUTE", "WRITE"]:
            return "BASE"
        
    # 3. Lecture globale hors prod pour tout le monde (sauf données perso)
    if access_type == "READ" and environment not in ["PRD", "INV"] and resource != "PERSONAL_DATA":
        return "BASE"
        
    # Par défaut, le reste est BASE
    return "BASE"

# ==================== GÉNÉRATION ====================

def generate_ticket(ticket_id):
    """Génère un ticket de manière intelligente pour respecter une bonne distribution"""
    
    scenario_type = random.choices(["LOGICAL", "BORDERLINE", "DANGEROUS"], weights=[70, 20, 10], k=1)[0]
    
    application = random.choices(APPLICATIONS, weights=[40, 40, 20], k=1)[0]
    
    if scenario_type == "LOGICAL":
        team = random.choice(TEAMS)
        role = random.choice(ROLES_PER_TEAM[team])
        
        if team in ["MOE", "MXP"]:
            environment = random.choices(["DEV2", "DVR", "QL2"], weights=[45, 45, 10], k=1)[0]
            if role in MANAGERS:
                access_type = random.choices(["READ", "WRITE", "UPDATE", "EXECUTE"], weights=[20, 40, 30, 10], k=1)[0]
            else:
                access_type = random.choices(["READ", "WRITE", "UPDATE"], weights=[50, 40, 10], k=1)[0]
            resource = "OTHER"
        elif team == "TEST_FACTORY":
            environment = random.choices(["QL2", "CRT"], weights=[70, 30], k=1)[0]
            access_type = random.choices(["READ", "EXECUTE", "WRITE"], weights=[50, 40, 10], k=1)[0]
            resource = "OTHER"
        elif team == "MOA":
            environment = random.choices(["DEV2", "QL2", "CRT"], weights=[30, 60, 10], k=1)[0]
            access_type = "READ"
            resource = "OTHER"
        else: # Autres
            environment = random.choice(["DEV2", "QL2", "DVR"])
            access_type = "READ"
            resource = "OTHER"
            
    elif scenario_type == "BORDERLINE":
        team = random.choice(TEAMS)
        role = random.choice(ROLES_PER_TEAM[team])
        environment = random.choices(ENVIRONMENTS, weights=[10, 10, 20, 30, 15, 15], k=1)[0]
        access_type = random.choices(["WRITE", "UPDATE", "EXECUTE", "READ"], weights=[30, 30, 20, 20], k=1)[0]
        resource = random.choice(RESOURCES)
        
    else: # DANGEROUS
        team = random.choices(["MOE", "MOA", "TEST_FACTORY"], k=1)[0]
        role = random.choice(ROLES_PER_TEAM[team])
        environment = random.choices(["PRD", "INV", "CRT"], weights=[60, 20, 20], k=1)[0]
        access_type = random.choices(["FULL_ACCESS", "DELETE", "WRITE", "UPDATE"], weights=[30, 20, 30, 20], k=1)[0]
        resource = random.choices(["PRODUCTION", "PERSONAL_DATA"], weights=[50, 50], k=1)[0]

    if random.random() < 0.90:
        hour = random.randint(8, 18)
        day_of_week = random.randint(0, 4)
    else:
        hour = random.choice([0, 1, 2, 3, 4, 19, 20, 21, 22, 23])
        day_of_week = random.choice([5, 6])
        
    days_ago = random.randint(0, 365)
    created_at = datetime.now() - timedelta(days=days_ago)
    
    label = get_label(team, role, application, environment, access_type, resource)
    
    return {
        "ticket_id": f"TKT{str(ticket_id).zfill(5)}",
        "team": team,
        "role": role,
        "application": application,
        "environment": environment,
        "access_type": access_type,
        "resource": resource,
        "hour": hour,
        "day_of_week": day_of_week,
        "label": label,
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")
    }

def generate_dataset(nb_tickets=5000):
    print(f"🚀 Génération de {nb_tickets} tickets en cours, avec le nouveau modèle logique + ROLE...")
    tickets = []
    for i in range(1, nb_tickets + 1):
        ticket = generate_ticket(i)
        tickets.append(ticket)
        if i % 1000 == 0:
            print(f"   → {i}/{nb_tickets} tickets générés")
    return pd.DataFrame(tickets)

def save_dataset(df, filename="training_dataset.csv"):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)
    data_dir = os.path.join(project_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    filepath = os.path.join(data_dir, filename)
    df.to_csv(filepath, index=False)
    print(f"\n✅ Dataset sauvegardé : {filepath}")
    return filepath

def show_statistics(df):
    print("\n" + "="*50)
    print("📊 STATISTIQUES DU NOUVEAU DATASET LOGIQUE (WITH ROLES)")
    print("="*50)
    print(f"\n📈 Nombre total de tickets : {len(df)}")
    print("\n📈 Distribution des labels :")
    label_counts = df['label'].value_counts()
    print(label_counts)
    total = len(df)
    for label in ["BASE", "SENSITIVE", "CRITICAL"]:
        count = label_counts.get(label, 0)
        percentage = (count / total) * 100
        print(f"   → {label} : {count} tickets ({percentage:.1f}%)")

if __name__ == "__main__":
    df = generate_dataset(5000)
    filepath = save_dataset(df)
    show_statistics(df)
    print("\n✅ Script terminé avec succès !")