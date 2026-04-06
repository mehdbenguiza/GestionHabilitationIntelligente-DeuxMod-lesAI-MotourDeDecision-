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
        categorical_cols = ['team', 'role', 'application', 'environment', 'access_type', 'resource']
        
        for col in categorical_cols:
            le = LabelEncoder()
            df[col + '_encoded'] = le.fit_transform(df[col])
            self.label_encoders[col] = le
            print(f"   → {col}: {len(le.classes_)} catégories encodées")
        
        # 2. Features binaires
        df['is_production'] = (df['environment'] == 'PRD').astype(int)
        df['is_critical_app'] = (df['application'] == 'T24').astype(int)
        df['is_critical_env'] = df['environment'].isin(['INV', 'PRD']).astype(int)
        df['is_sensitive_team'] = (df['team'] == 'SECURITE').astype(int)
        df['is_full_access'] = df['access_type'].isin(['DELETE', 'FULL_ACCESS']).astype(int)
        df['is_personal_data'] = (df['resource'] == 'PERSONAL_DATA').astype(int)
        df['is_night_hour'] = ((df['hour'] < 8) | (df['hour'] > 20)).astype(int)
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_manager'] = df['role'].isin(["CHEF_DE_PROJET", "TECH_LEAD", "PRODUCT_OWNER", "ADMINISTRATEUR", "RSSI", "TEST_LEAD"]).astype(int)
        df['is_restricted_role'] = df['role'].isin(["STAGIAIRE", "BUSINESS_ANALYST"]).astype(int)
        
        # 3. Liste des colonnes features
        self.feature_columns = [
            'team_encoded',
            'role_encoded',
            'application_encoded', 
            'environment_encoded',
            'access_type_encoded',
            'resource_encoded',
            'hour',
            'day_of_week',
            'is_production',
            'is_critical_app',
            'is_critical_env',
            'is_sensitive_team',
            'is_full_access',
            'is_personal_data',
            'is_night_hour',
            'is_weekend',
            'is_manager',
            'is_restricted_role'
        ]
        
        self.is_fitted = True
        print(f"✅ {len(self.feature_columns)} features préparées")
        
        return self
    
    def transform(self, df):
        """
        Transforme un DataFrame en features
        """
        if not self.is_fitted:
            raise Exception("Le FeatureExtractor doit d'abord être entraîné avec fit()")
        
        df_features = df.copy()
        
        # Appliquer les encodeurs
        for col, le in self.label_encoders.items():
            df_features[col + '_encoded'] = le.transform(df_features[col])
        
        # Features binaires
        df_features['is_production'] = (df_features['environment'] == 'PRD').astype(int)
        df_features['is_critical_app'] = (df_features['application'] == 'T24').astype(int)
        df_features['is_critical_env'] = df_features['environment'].isin(['INV', 'PRD']).astype(int)
        df_features['is_sensitive_team'] = (df_features['team'] == 'SECURITE').astype(int)
        df_features['is_full_access'] = df_features['access_type'].isin(['DELETE', 'FULL_ACCESS']).astype(int)
        df_features['is_personal_data'] = (df_features['resource'] == 'PERSONAL_DATA').astype(int)
        df_features['is_night_hour'] = ((df_features['hour'] < 8) | (df_features['hour'] > 20)).astype(int)
        df_features['is_weekend'] = (df_features['day_of_week'] >= 5).astype(int)
        df_features['is_manager'] = df_features['role'].isin(["CHEF_DE_PROJET", "TECH_LEAD", "PRODUCT_OWNER", "ADMINISTRATEUR", "RSSI", "TEST_LEAD"]).astype(int)
        df_features['is_restricted_role'] = df_features['role'].isin(["STAGIAIRE", "BUSINESS_ANALYST"]).astype(int)
        
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