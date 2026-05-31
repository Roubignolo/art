#!/usr/bin/env bash
# europeana-keepalive.sh
# Génère une activité API régulière sur la clé Europeana PERSONNELLE (lue depuis
# .env par agents/sources/base.py), afin de débloquer la future demande de clé
# PROJET (production) — Europeana exige de l'activité sur une clé perso d'abord.
#
# - Auto-désactivation après END_DATE (no-op) : laisser le cron en place est sans risque.
# - À retirer du crontab une fois la clé projet obtenue (voir README.md).
# - N'écrit aucun master sur disque : juste quelques appels Search API + un log.

set -uo pipefail

REPO="/Users/jeromefiron/Dev/art"
END_DATE="2026-06-08"            # ~1 semaine d'activité ; no-op au-delà
TODAY="$(date +%Y-%m-%d)"
STAMP="$(date '+%F %T')"

if [[ "$TODAY" > "$END_DATE" ]]; then
  echo "[$STAMP] keepalive: fenêtre terminée (> $END_DATE) — no-op. Pense à retirer le cron."
  exit 0
fi

cd "$REPO" || { echo "[$STAMP] keepalive: repo introuvable ($REPO)"; exit 1; }

python3 - <<'PY'
import sys, datetime
sys.path.insert(0, "agents")
try:
    from sources import europeana  # base.py charge automatiquement .env (clé perso)
except Exception as e:
    print(f"[keepalive] import KO: {e}")
    sys.exit(0)

# 3 requêtes tournantes selon le jour → activité variée mais bornée.
pool = ["botanical illustration", "japanese woodblock print", "celestial map",
        "still life flowers", "ornithology engraving", "antique map",
        "portrait painting", "art nouveau"]
doy = datetime.date.today().timetuple().tm_yday
queries = [pool[(doy + i) % len(pool)] for i in range(3)]

total = 0
for q in queries:
    n = 0
    try:
        for _ in europeana.iter_candidates(q, max_scan=30):
            n += 1
    except Exception as e:
        print(f"[keepalive] '{q}' erreur: {e}")
        continue
    total += n
    print(f"[keepalive] query='{q}' scanned={n}")
print(f"[keepalive] OK total_scanned={total}")
PY

echo "[$STAMP] keepalive: run terminé."
