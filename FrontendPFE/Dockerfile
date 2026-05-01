# ════════════════════════════════════════════════════════════════════════════
#  Dockerfile — Frontend React/Vite (Multi-Stage Build)
#  Projet PFE : Gestion Intelligente des Habilitations IT — BIAT 2026
#
#  Stage 1 (builder) : Node.js compile le code React → dist/
#  Stage 2 (runtime) : Nginx sert les fichiers statiques (~25MB final)
# ════════════════════════════════════════════════════════════════════════════

# ── STAGE 1 : Build ───────────────────────────────────────────────────────
FROM node:20-alpine AS builder

LABEL stage="builder"

WORKDIR /app

# Copier les manifestes de dépendances EN PREMIER (optimisation cache)
COPY package*.json ./

# Installer les dépendances (npm ci = installation reproductible et stricte)
RUN npm ci

# Copier tout le code source
COPY . .

# Variables d'environnement pour Vite (build time)
ENV VITE_API_URL=http://localhost:8000

# Construire le bundle de production optimisé
RUN npm run build

# ── STAGE 2 : Runtime ─────────────────────────────────────────────────────
FROM nginx:alpine AS runtime

LABEL maintainer="BIAT PFE 2026"
LABEL description="Frontend React — Gestion Intelligente des Habilitations"
LABEL version="1.0.0"

# Copier UNIQUEMENT le build final depuis le stage 1 (pas node_modules !)
COPY --from=builder /app/dist /usr/share/nginx/html

# Copier la configuration Nginx personnalisée
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Port exposé
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost:80/ || exit 1
