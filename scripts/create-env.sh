#!/usr/bin/env bash
# Cria o .env a partir do .env.example, com segredos aleatórios.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -e .env ]]; then
  echo ".env já existe; nada foi alterado." >&2
  exit 1
fi

secret() { openssl rand -hex 24; }
# A Fernet key é base64 url-safe de 32 bytes.
fernet_key="$(openssl rand -base64 32 | tr '+/' '-_')"

umask 077
sed \
  -e "s|^AIRFLOW_DB_PASSWORD=.*|AIRFLOW_DB_PASSWORD=$(secret)|" \
  -e "s|^DW_PASSWORD=.*|DW_PASSWORD=$(secret)|" \
  -e "s|^AIRFLOW_ADMIN_PASSWORD=.*|AIRFLOW_ADMIN_PASSWORD=$(secret)|" \
  -e "s|^AIRFLOW_JWT_SECRET=.*|AIRFLOW_JWT_SECRET=$(secret)|" \
  -e "s|^FERNET_KEY=.*|FERNET_KEY=${fernet_key}|" \
  .env.example > .env

echo ".env criado. A senha do Airflow está em AIRFLOW_ADMIN_PASSWORD."
