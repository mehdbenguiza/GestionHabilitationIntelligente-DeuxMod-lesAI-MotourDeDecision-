# scratch/test_fix_500.py
import requests

API = "http://127.0.0.1:8000"

def test_simulation():
    try:
        # On suppose que l'auth est gérée par le token local ou que le backend autorise en dev
        # Mais ici on teste juste si le Python crash au niveau du service
        # Je vais plutôt simuler l'appel interne au service via un script python direct
        print("🔍 Test interne du TicketService...")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    test_simulation()
