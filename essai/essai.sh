#!/bin/bash
# Essai de bout en bout des images, dans les conditions du serveur. Lancé par le workflow (et rejouable sur une machine
# avec Docker). Échoue au premier écart.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p recu && chmod 777 recu
install -d -m 700 postgres && sudo chown 70:70 postgres
r() { openssl rand -hex 24; }
PG_MDP=$(r); REDIS_MDP=$(r); NEXTAUTH=$(r); CHIFFRE=$(openssl rand -base64 24); JWT=$(r)
printf 'PG_MDP=%s\nREDIS_MDP=%s\n' "$PG_MDP" "$REDIS_MDP" > .env
BASE="postgresql://caldiy:$PG_MDP@postgres:5432/caldiy"
cat > web.env <<FIN
DATABASE_URL=$BASE
DATABASE_DIRECT_URL=$BASE
NEXT_PUBLIC_WEBAPP_URL=https://rdv.symind.ai
NEXTAUTH_URL=https://rdv.symind.ai/api/auth
NEXTAUTH_SECRET=$NEXTAUTH
CALENDSO_ENCRYPTION_KEY=$CHIFFRE
CALCOM_TELEMETRY_DISABLED=1
NEXT_PUBLIC_DISABLE_SIGNUP=true
EMAIL_FROM=rdv@notifications.symind.ai
EMAIL_FROM_NAME=Adrien Beun, Symind
EMAIL_SERVER_HOST=mailpit
EMAIL_SERVER_PORT=1025
CRON_API_KEY=$(r)
FIN
cat > api.env <<FIN
DATABASE_URL=$BASE
DATABASE_READ_URL=$BASE
DATABASE_WRITE_URL=$BASE
REDIS_URL=redis://:$REDIS_MDP@redis:6379
NEXTAUTH_SECRET=$NEXTAUTH
CALENDSO_ENCRYPTION_KEY=$CHIFFRE
JWT_SECRET=$JWT
API_URL=http://127.0.0.1:5555
WEB_APP_URL=https://rdv.symind.ai
API_KEY_PREFIX=cal_
STRIPE_API_KEY=sk_test_inutilise
STRIPE_WEBHOOK_SECRET=whsec_inutilise
IS_TEAM_BILLING_ENABLED=false
LOG_LEVEL=warn
REWRITE_API_V2_PREFIX=true
FIN
docker compose up -d
for i in $(seq 1 120); do
  if curl -fsS -o /dev/null http://127.0.0.1:3000/auth/login && curl -fsS -o /dev/null http://127.0.0.1:5555/health; then
    echo "web et API : prêts après $((i*5)) s"; break
  fi
  [ "$i" = 120 ] && { echo "pas prêts en 10 min"; exit 1; }
  sleep 5
done
docker compose ps
docker stats --no-stream --format '{{.Name}} {{.MemUsage}}'
docker compose exec -T web id
docker compose exec -T api id
python3 essai.py
