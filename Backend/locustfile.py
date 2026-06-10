from locust import HttpUser, task, between

class APIUser(HttpUser):
    # Temps d'attente entre deux requêtes simulées par un utilisateur (entre 1 et 3 secondes)
    wait_time = between(1, 3)
    
    def on_start(self):
        """
        Exécuté une seule fois par utilisateur virtuel au démarrage.
        Sert à s'authentifier et récupérer le token JWT.
        """
        # Adaptez les identifiants si 'test_superadmin' n'existe pas dans votre base de dev
        response = self.client.post("/auth/login", json={
            "username": "benguiza", 
            "password": "Mehdimehdi1234!"
        })
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            # Ajoute le token dans le header de toutes les futures requêtes
            self.client.headers.update({"Authorization": f"Bearer {token}"})
        else:
            print("⚠️ Échec de la connexion. Vérifiez les identifiants dans locustfile.py.")

    @task(3)
    def classify_base_ticket(self):
        """
        Simule la soumission d'un ticket à faible risque.
        Le poids (3) indique que cette tâche sera exécutée 3 fois plus souvent que l'autre.
        """
        self.client.post("/ai/classify", json={
            "team": "MOE",
            "application": "CRM_SIEBEL",
            "environment": "DEV2",
            "access_type": "READ",
            "resource": "OTHER"
        })

    @task(1)
    def classify_critical_ticket(self):
        """
        Simule la soumission d'un ticket critique (plus lourd à traiter potentiellement).
        """
        self.client.post("/ai/classify", json={
            "team": "TRADING",
            "application": "MUREX",
            "environment": "PRD",
            "access_type": "DELETE",
            "resource": "TRANSACTIONS_FINANCIERES"
        })
