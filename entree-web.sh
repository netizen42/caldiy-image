#!/bin/sh
# Démarrage de l'application web Cal.diy : migrations de la base, apps du store (Google Agenda, Meet), puis Next.js.
# Remplace scripts/start.sh de cal.diy, qui réécrit des fichiers de l'image (impossible sans root) et passe par turbo.
set -e
cd /calcom
npx --no prisma migrate deploy --schema /calcom/packages/prisma/schema.prisma
# Pas de tsconfig à la racine de l'image : sans ces options, ts-node refuse les imports JSON (TS2732). Le start.sh
# d'origine n'a pas de `set -e` et continue en silence sans les apps (Google Agenda absent).
TS_NODE_COMPILER_OPTIONS='{"module":"commonjs","moduleResolution":"node","resolveJsonModule":true,"esModuleInterop":true}' \
  npx --no ts-node --transpile-only /calcom/scripts/seed-app-store.ts
cd /calcom/apps/web
exec /calcom/node_modules/.bin/next start -p 3000 -H 0.0.0.0
