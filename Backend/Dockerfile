# ════════════════════════════════════════════════════════════════════════════
#  Dockerfile — Backend FastAPI
#  Projet PFE : Gestion Intelligente des Habilitations IT — BIAT 2026
# ════════════════════════════════════════════════════════════════════════════
FROM python:3.11-slim

LABEL maintainer="BIAT PFE 2026"
LABEL description="Backend FastAPI — Gestion Intelligente des Habilitations"
LABEL version="1.0.0"

# ── Variables d'environnement Python ─────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# ── Dépendances système (nécessaires pour gcc/scipy/sklearn) ─────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# ── Dépendances Python (copiées avant le code → cache Docker optimisé) ───
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Code source ──────────────────────────────────────────────────────────
COPY . .

# ── Répertoires nécessaires ───────────────────────────────────────────────
RUN mkdir -p uploads/profiles data models

# ── Utilisateur non-root (sécurité) ──────────────────────────────────────
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# ── Port exposé ───────────────────────────────────────────────────────────
EXPOSE 8000

# ── Health check intégré ─────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Démarrage ─────────────────────────────────────────────────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
