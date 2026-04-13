# app/services/feature_extractor.py

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import joblib
import os

class FeatureExtractor:
    """
    Service d'extraction de features pour le modèle de classification
    Transforme un ticket brut en vecteur de nombres compréhensible par le ML
    """
    
    def __init__(self):
        self.label_encoders = {}
        self.feature_columns = None
        self.is_fitted = False
    
    def fit(self, df):
        """
        Entraîne les encodeurs sur le dataset
        df: DataFrame contenant les données d'entraînement
        """
        print("🔧 Entraînement des encodeurs...")
        
        # 1. Encodage des variables catégorielles
        categorical_cols = ['team', 'role', 'application', 'environment', 'access_type', 'resource', 'user_seniority', 'request_reason', 'manager_approval_status']
        
        for col in categorical_cols:
            le = LabelEncoder()
            # On vérifie si la colonne existe pour ne pas planter
            if col in df.columns:
                df[col + '_encoded'] = le.fit_transform(df[col])
                self.label_encoders[col] = le
            else:
                # Fallback
                self.label_encoders[col] = LabelEncoder()
                df[col + '_encoded'] = 0
            
        # 2. Features binaires
        df['is_production'] = (df['environment'] == 'PRD').astype(int)
        df['is_critical_app'] = df['application'].isin(['T24', 'SWIFT', 'MUREX']).astype(int)
        df['is_critical_env'] = df['environment'].isin(['INV', 'PRD', 'CRT']).astype(int)
        df['is_sensitive_team'] = df['team'].isin(['SECURITE', 'CONFORMITE', 'TRADING']).astype(int)
        df['is_full_access'] = df['access_type'].isin(['DELETE', 'FULL_ACCESS', 'DBA_ACCESS']).astype(int)
        df['is_personal_data'] = df['resource'].isin(['DONNEES_CLIENTS_SENSIBLES', 'TRANSACTIONS_FINANCIERES', 'CLEFS_CRYPTOGRAPHIQUES']).astype(int)
        df['is_manager'] = df['role'].isin(["CHEF_DE_PROJET", "TECH_LEAD", "PRODUCT_OWNER", "ADMINISTRATEUR", "RSSI", "TEST_LEAD", "OFFICIER_CONFORMITE", "INSPECTEUR"]).astype(int)
        df['is_restricted_role'] = df['role'].isin(["STAGIAIRE", "BUSINESS_ANALYST", "FRONT_OFFICE_TRADER"]).astype(int)
        
        # Nouvelles briques métier
        df['is_approved'] = (df.get('manager_approval_status', '') == 'approved').astype(int)
        df['is_urgent'] = df.get('request_reason', '').isin(['incident_production_bloquant', 'demande_metier_urgente']).astype(int)
        df['is_junior'] = (df.get('user_seniority', '') == 'junior').astype(int)
        # 3. Liste exhaustive des colonnes features
        self.feature_columns = [
            'team_encoded', 'role_encoded', 'application_encoded', 
            'environment_encoded', 'access_type_encoded', 'resource_encoded',
            'user_seniority_encoded', 'request_reason_encoded', 'manager_approval_status_encoded',
            'is_production', 'is_critical_app', 'is_critical_env', 'is_sensitive_team',
            'is_full_access', 'is_personal_data', 'is_manager', 'is_restricted_role',
            'is_approved', 'is_urgent', 'is_junior'
        ]
        
        self.is_fitted = True
        return self
    
    def transform(self, df):
        """
        Transforme un DataFrame en features
        """
        if not self.is_fitted:
            raise Exception("Le FeatureExtractor doit d'abord être entraîné avec fit()")
        
        df_features = df.copy()
        
        # Assurer les colonnes manquantes
        for col in ['user_seniority', 'request_reason', 'manager_approval_status']:
            if col not in df_features.columns:
                if col == 'user_seniority': df_features[col] = 'senior'
                elif col == 'request_reason': df_features[col] = 'normal'
                else: df_features[col] = 'none'

        # Appliquer les encodeurs
        def safe_transform(le, value):
            if value in le.classes_:
                return le.transform([value])[0]
            else:
                return -1

        for col, le in self.label_encoders.items():
            try:
                df_features[col + '_encoded'] = df_features[col].map(lambda s: safe_transform(le, s))
            except Exception:
                df_features[col + '_encoded'] = -1
        
        # Features binaires
        df_features['is_production'] = (df_features['environment'] == 'PRD').astype(int)
        df_features['is_critical_app'] = df_features['application'].isin(['T24', 'SWIFT', 'MUREX']).astype(int)
        df_features['is_critical_env'] = df_features['environment'].isin(['INV', 'PRD', 'CRT']).astype(int)
        df_features['is_sensitive_team'] = df_features['team'].isin(['SECURITE', 'CONFORMITE', 'TRADING']).astype(int)
        df_features['is_full_access'] = df_features['access_type'].isin(['DELETE', 'FULL_ACCESS', 'DBA_ACCESS']).astype(int)
        df_features['is_personal_data'] = df_features['resource'].isin(['DONNEES_CLIENTS_SENSIBLES', 'TRANSACTIONS_FINANCIERES', 'CLEFS_CRYPTOGRAPHIQUES']).astype(int)
        df_features['is_manager'] = df_features['role'].isin(["CHEF_DE_PROJET", "TECH_LEAD", "PRODUCT_OWNER", "ADMINISTRATEUR", "RSSI", "TEST_LEAD", "OFFICIER_CONFORMITE", "INSPECTEUR"]).astype(int)
        df_features['is_restricted_role'] = df_features['role'].isin(["STAGIAIRE", "BUSINESS_ANALYST", "FRONT_OFFICE_TRADER"]).astype(int)
        
        # Nouvelles briques métier
        df_features['is_approved'] = (df_features['manager_approval_status'] == 'approved').astype(int)
        df_features['is_urgent'] = df_features['request_reason'].isin(['incident_production_bloquant', 'demande_metier_urgente']).astype(int)
        df_features['is_junior'] = (df_features['user_seniority'] == 'junior').astype(int)
        
        return df_features[self.feature_columns]
    
    def transform_single_ticket(self, ticket_dict):
        """
        Transforme un ticket unique (dictionnaire) en vecteur de features
        """
        df = pd.DataFrame([ticket_dict])
        return self.transform(df)
    
    def save(self, path="models/feature_extractor.pkl"):
        """Sauvegarde l'extracteur"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'label_encoders': self.label_encoders,
            'feature_columns': self.feature_columns,
            'is_fitted': self.is_fitted
        }, path)
        print(f"✅ FeatureExtractor sauvegardé : {path}")
    
    def load(self, path="models/feature_extractor.pkl"):
        """Charge l'extracteur"""
        data = joblib.load(path)
        self.label_encoders = data['label_encoders']
        self.feature_columns = data['feature_columns']
        self.is_fitted = data['is_fitted']
        print(f"✅ FeatureExtractor chargé : {path}")