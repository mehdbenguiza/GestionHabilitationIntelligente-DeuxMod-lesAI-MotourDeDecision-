import uvicorn
import sys
import os

# Cette ligne permet de lancer depuis n’importe où
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)