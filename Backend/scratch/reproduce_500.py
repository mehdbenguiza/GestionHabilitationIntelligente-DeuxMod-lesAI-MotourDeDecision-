# scratch/reproduce_500.py
import sys
import os
from fastapi.testclient import TestClient

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

from app.main import app

client = TestClient(app)

print("\n--- Testing /tickets ---")
try:
    # Need a valid token to bypass 401, but even a 500 would show traceback if it happens early
    # Let's try to reach the endpoint. Since TestClient uses the app object directly,
    # it will show the traceback in the console.
    response = client.get("/tickets")
    print(f"Status: {response.status_code}")
    print(f"Content: {response.text[:200]}")
except Exception as e:
    print(f"Caught Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n--- Testing /ai/metrics ---")
try:
    response = client.get("/ai/metrics")
    print(f"Status: {response.status_code}")
    print(f"Content: {response.text[:200]}")
except Exception as e:
    print(f"Caught Exception: {e}")
    import traceback
    traceback.print_exc()
