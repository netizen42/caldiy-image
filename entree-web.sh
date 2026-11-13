#!/bin/sh
# Démarrage de l'application web Cal.diy : migrations de la base, apps du store (Google Agenda, Meet), puis Next.js.
# Remplace scripts/start.sh de cal.diy, qui réécrit des fichiers de l'image (impossible sans root) et passe par turbo.
set -e
cd /calcom
npx --no prisma migrate deploy --schema /calcom/packages/prisma/schema.prisma
npx --no ts-node --transpile-only /calcom/scripts/seed-app-store.ts
cd /calcom/apps/web
exec /calcom/node_modules/.bin/next start -p 3000 -H 0.0.0.0
