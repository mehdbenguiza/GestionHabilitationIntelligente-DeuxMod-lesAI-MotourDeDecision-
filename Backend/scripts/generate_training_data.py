# scripts/generate_training_data.py

import pandas as pd
import random
import os
from datetime import datetime, timedelta

# ==================== DONNÉES DE BASE BANCABLES ====================

TEAMS = ["MOE", "MOA", "RESEAU", "SECURITE", "TEST_FACTORY", "DATA", "MXP", "CONFORMITE", "MONETIQUE", "TRADING", "AUDIT_INTERNE"]
APPLICATIONS = ["T24", "MUREX", "SWIFT", "AML_TIDE", "E_BANKING", "CRM_SIEBEL", "QUANTARA"]
ENVIRONMENTS = ["DEV2", "DVR", "TST", "QL2", "CRT", "UAT", "INV", "PRD"]
ACCESS_TYPES = ["READ", "WRITE", "EXECUTE", "UPDATE", "DELETE", "FULL_ACCESS", "DBA_ACCESS"]
RESOURCES = ["DONNEES_CLIENTS_SENSIBLES", "TRANSACTIONS_FINANCIERES", "LOGS_SECURITE", "CODE_SOURCE", "CLEFS_CRYPTOGRAPHIQUES", "DONNEES_CARRIERES_RH", "OTHER"]

ROLES_PER_TEAM = {
    "MOE": ["DEVELOPPEUR", "TECH_LEAD", "CHEF_DE_PROJET", "STAGIAIRE"],
    "MOA": ["BUSINESS_ANALYST", "PRODUCT_OWNER", "CHEF_DE_PROJET"],
    "RESEAU": ["INGENIEUR_RESEAU", "ADMINISTRATEUR", "STAGIAIRE"],
    "SECURITE": ["ANALYSTE_SOC", "RSSI", "PENTESTER"],
    "TEST_FACTORY": ["TESTEUR_QA", "TEST_LEAD", "AUTOMATICIEN"],
    "DATA": ["DATA_SCIENTIST", "DATA_ENGINEER", "DATA_ANALYST"],
    "MXP": ["INTEGRATEUR", "CHEF_DE_PROJET", "INGENIEUR_EXPLOITATION"],
    "CONFORMITE": ["OFFICIER_CONFORMITE", "AML_ANALYST"],
    "MONETIQUE": ["INGENIEUR_MONETIQUE", "EXPLOITATION_MONETIQUE"],
    "TRADING": ["FRONT_OFFICE_TRADER", "MIDDLE_OFFICE"],
    "AUDIT_INTERNE": ["AUDITEUR_IT", "INSPECTEUR"]
}

MANAGERS = ["CHEF_DE_PROJET", "TECH_LEAD", "PRODUCT_OWNER", "ADMINISTRATEUR", "RSSI", "TEST_LEAD", "OFFICIER_CONFORMITE", "INSPECTEUR"]
RESTRICTED = ["STAGIAIRE", "BUSINESS_ANALYST", "FRONT_OFFICE_TRADER"]

# ==================== RÈGLES DE CLASSIFICATION METIER (AMÉLIORÉES) ====================

def get_label(team, role, application, environment, access_type, resource, user_seniority, request_reason, approval_status):
    risk = 0
    is_sensitive_res = resource in ["DONNEES_CLIENTS_SENSIBLES", "TRANSACTIONS_FINANCIERES", "CLEFS_CRYPTOGRAPHIQUES"]
    
    # --- 1. BASE APPLICATIONS ---
    if application in ["SWIFT", "T24", "MUREX"]:
        risk += 30
    elif application in ["AML_TIDE", "E_BANKING"]:
        risk += 20

    # --- 2. BASE ENVIRONNEMENT & ACCES (Règles refondues) ---
    if environment == "PRD":
        risk += 40
        if access_type == "FULL_ACCESS":
            risk += 60 # 1.2 PRD + FULL_ACCESS -> CRITICAL direct
        if access_type in ["DELETE", "DBA_ACCESS"]:
            risk += 40
        if access_type == "READ" and is_sensitive_res:
            risk += 30 # 1.1 READ en PRD sous-estimé
    elif environment in ["INV", "CRT", "UAT"]:
        risk += 20
        if access_type == "FULL_ACCESS":
            risk += 30
    else: # DEV
        if access_type == "FULL_ACCESS":
            risk += 15 # 1.2 DEV + FULL_ACCESS -> ok-ish

    if access_type == "DBA_ACCESS":
        risk += 50 # 1.8 DBA_ACCESS massif
        
    if access_type in ["WRITE", "UPDATE", "DELETE"] and environment != "PRD":
        risk += 15

    # --- 3. RESSOURCES ---
    if is_sensitive_res:
        risk += 30
    if resource == "DONNEES_CARRIERES_RH":
        risk += 20 # 1.9 RESOURCE RH oubliée
    if resource in ["LOGS_SECURITE", "CODE_SOURCE"]:
        risk += 15

    # --- 4. ROLES ET SENIORITE (1.4) ---
    if user_seniority == "junior":
        if environment != "PRD": 
            risk += 5 # junior en DEV -> souvent safe
        else:
            risk += 25
    else: # senior
        if access_type == "FULL_ACCESS" and environment == "PRD":
            risk += 40 # senior + FULL_ACCESS + PRD -> critique

    # --- 5. LOGIQUE D'EQUIPE (1.5, 1.6, 1.7) ---
    if team == "MOA":
        if access_type != "READ":
            risk += 25
            
    if team == "SECURITE":
        if environment == "PRD" and access_type in ["DELETE", "DBA_ACCESS", "FULL_ACCESS"]:
            risk += 40 # Securite en prd c'est ok sauf si destructif
            
    if team in ["AUDIT_INTERNE", "CONFORMITE"]:
         if is_sensitive_res:
             risk -= 10 # Acces sensible MAIS reduit car c'est leur job
             
    if team == "TRADING":
         if application not in ["MUREX", "T24"]:
             risk += 40 # 1.6 TRADING hors MUREX/T24 -> +40
         if is_sensitive_res and access_type != "READ":
             risk += 30 # Trading + modif sensible -> toujours suspect
             
    if role in ["DEVELOPPEUR", "STAGIAIRE", "INTEGRATEUR"] and environment == "PRD":
         # 1.7 DEV en PRD -> +30 sauf incident approved
         if not (request_reason == "incident_production_bloquant" and approval_status == "approved"):
             risk += 30

    # PÉRIMÈTRE LOGIQUE D'ENVIRONNEMENT BASIQUE
    if team == "DATA" and environment not in ["DEV2", "TST", "QL2", "INV"]:
        risk += 20

    # --- 6. REQUEST REASON (1.10) ---
    if request_reason == "incident_production_bloquant":
        if approval_status == "approved":
            risk -= 10
        else:
            risk += 20
    elif request_reason == "audit_reglementaire_bct":
        risk -= 15
    elif request_reason == "demande_metier_urgente":
        risk += 10
    elif request_reason == "maintenance_preventive":
        risk += 0 # neutre
        
    # --- 7. MANAGER APPROVAL (1.3) ---
    if approval_status == "approved":
        if risk < 80: # Si score deja tres critique, on ignore l'approval !
            risk -= 20

    # Conflits ou bruits (2.3 Borderline, 2.1 Conflits)
    # Ajouter un tres léger bruit stat
    risk += random.randint(-5, 5)
    
    # Thresholds fixes modifiés pour les distributions
    if risk >= 85:
        return "CRITICAL"
    elif risk >= 50:
        return "SENSITIVE"
    else:
        return "BASE"

# ==================== GÉNÉRATION DIVERSIFIÉE (2.2, 3.1, 3.2, 3.3) ====================

def generate_ticket(ticket_id):
    # La distribution visée: BASE(60%), SENSITIVE(25%), CRITICAL(15%)
    # On va utiliser des weights pour forcer différents types de comportements
    scenario_type = random.choices(["SAFE_DEV", "STANDARD_READ", "BORDERLINE", "DANGEROUS", "RARE_EVENT", "CONTRADICTORY"], 
                                   weights=[40, 35, 10, 5, 5, 5], k=1)[0]
    
    team = random.choice(TEAMS)
    role = random.choice(ROLES_PER_TEAM[team])
    application = random.choice(APPLICATIONS)
    environment = random.choice(ENVIRONMENTS)
    access_type = random.choice(ACCESS_TYPES)
    resource = random.choice(RESOURCES)
    user_seniority = random.choices(["junior", "senior"], weights=[30, 70], k=1)[0]
    request_reason = random.choices(
        ["incident_production_bloquant", "deploiement_version", "audit_reglementaire_bct", "demande_metier_urgente", "maintenance_preventive", "cloture_comptable_fin_de_mois"], 
        weights=[10, 20, 5, 20, 35, 10], k=1)[0]
    approval_status = random.choices(["approved", "pending", "none"], weights=[30, 20, 50], k=1)[0]
    
    if scenario_type == "SAFE_DEV":
        environment = random.choice(["DEV2", "DVR", "TST"])
        access_type = random.choice(["READ", "WRITE", "UPDATE", "FULL_ACCESS"])
        resource = "CODE_SOURCE" if environment == "DEV2" else "OTHER"
    elif scenario_type == "STANDARD_READ":
        environment = random.choices(ENVIRONMENTS, weights=[10, 10, 10, 10, 20, 10, 10, 20], k=1)[0]
        access_type = "READ"
        if application in ["MUREX", "T24", "SWIFT"] and environment == "PRD" and random.random() > 0.5:
             # Generer du READ en PRD sur du sensible
             resource = "TRANSACTIONS_FINANCIERES"
        else:
             resource = random.choice(["OTHER", "DONNEES_CARRIERES_RH"])
    elif scenario_type == "DANGEROUS":
        environment = "PRD"
        access_type = random.choice(["DELETE", "FULL_ACCESS", "DBA_ACCESS", "UPDATE"])
        resource = random.choice(["TRANSACTIONS_FINANCIERES", "DONNEES_CLIENTS_SENSIBLES", "CLEFS_CRYPTOGRAPHIQUES"])
        approval_status = "none"
        if random.random() < 0.3:
            role = "STAGIAIRE"
            user_seniority = "junior"
    elif scenario_type == "RARE_EVENT":
        # 3.3 Rare events
        is_crypto = random.random() > 0.5
        if is_crypto:
             resource = "CLEFS_CRYPTOGRAPHIQUES"
             access_type = "READ"
             environment = "PRD"
             team = "SECURITE"
             role = "RSSI"
        else:
             access_type = "DBA_ACCESS"
             environment = "PRD"
             team = "MOE"
    elif scenario_type == "CONTRADICTORY":
        # junior + READ + DEV = normalement safe mais on force une erreur
        # senior + DELETE + PRD = extremement dangereux 
        if random.random() > 0.5:
            user_seniority = "junior"
            access_type = "READ"
            environment = "DEV2"
        else:
            user_seniority = "senior"
            access_type = "DELETE"
            environment = "PRD"
            approval_status = "approved"

    label = get_label(team, role, application, environment, access_type, resource, user_seniority, request_reason, approval_status)
    created_at = datetime.now() - timedelta(days=random.randint(0, 365))
    
    return {
        "ticket_id": f"TKT{str(ticket_id).zfill(5)}",
        "employee_id": f"EMP-{random.randint(100, 999)}",
        "team": team,
        "role": role,
        "application": application,
        "environment": environment,
        "access_type": access_type,
        "resource": resource,
        "user_seniority": user_seniority,
        "request_reason": request_reason,
        "manager_approval_status": approval_status,
        "label": label,
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")
    }

def generate_dataset(nb_tickets=5000):
    print(f"Generation de {nb_tickets} tickets ultra-realistes...")
    tickets = []
    for i in range(1, nb_tickets + 1):
        ticket = generate_ticket(i)
        tickets.append(ticket)
        # 3.2 Duplication intelligente
        if random.random() < 0.05: # 5% de chance de cloner ce ticket pour simuler un pattern frequent
            cloned = dict(ticket)
            cloned['ticket_id'] = f"TKT{str(i+nb_tickets).zfill(5)}"
            tickets.append(cloned)
    
    df = pd.DataFrame(tickets)
    return df

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
    print("📊 STATISTIQUES DU DATASET RÉALISTE")
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
    df = generate_dataset(5000) # Demande de base, on aura un peu plus avec la duplication
    filepath = save_dataset(df)
    show_statistics(df)
    print("\n✅ Script terminé avec succès !")