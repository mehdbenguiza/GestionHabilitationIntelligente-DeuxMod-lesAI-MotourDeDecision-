# tests/test_auth.py

import requests

BASE_URL = "http://127.0.0.1:8000"

# 1. Se connecter
print("🔐 Connexion...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "benguiza", "password": "Mehdimehdi123!"}
)

if login_response.status_code != 200:
    print(f"❌ Erreur login: {login_response.status_code}")
    print(login_response.text)
    exit()

token = login_response.json()["access_token"]
print(f"✅ Token obtenu: {token[:50]}...")

# 2. Tester l'API IA
print("\n🧪 Test API IA...")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

data = {
    "team": "MOE",
    "application": "MXP",
    "environment": "DEV2",
    "access_type": "READ",
    "resource": "OTHER"
}

response = requests.post(
    f"{BASE_URL}/ai/classify",
    json=data,
    headers=headers
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ Succès!")
    print(response.json())
else:
    print("❌ Erreur:")
    print(response.text)