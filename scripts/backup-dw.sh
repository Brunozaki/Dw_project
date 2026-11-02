#!/usr/bin/env bash
# Salva uma cópia do data warehouse em backups/, mantendo as 7 mais recentes.
# Uso: bash scripts/backup-dw.sh
set -euo pipefail

cd "$(dirname "$0")/.."
source .env

mkdir -p backups
arquivo="backups/dw_$(date +%Y%m%d_%H%M%S).dump"

if ! docker compose exec -T postgres-dw pg_dump -U "$DW_USER" -d "$DW_DB" -Fc > "$arquivo"; then
  rm -f "$arquivo"
  echo "Falha ao gerar a cópia." >&2
  exit 1
fi

ls -1t backups/dw_*.dump | tail -n +8 | xargs -r rm --
echo "Cópia salva em $arquivo ($(du -h "$arquivo" | cut -f1))."
