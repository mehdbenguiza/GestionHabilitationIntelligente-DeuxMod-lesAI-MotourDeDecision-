# scratch/check_imports.py
import sys
import os

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

try:
    print("Checking app.main imports...")
    from app.main import app
    print("✅ app.main imported successfully.")
except Exception as e:
    print(f"❌ Error importing app.main: {e}")
    import traceback
    traceback.print_exc()
