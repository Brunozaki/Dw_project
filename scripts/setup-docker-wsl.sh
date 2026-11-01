#!/usr/bin/env bash
# Instala o Docker Engine no Ubuntu do WSL a partir do repositório oficial.
# Uso: sudo bash scripts/setup-docker-wsl.sh <usuario-linux>
set -euo pipefail

linux_user="${1:?Informe o usuário Linux que usará o Docker}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Rode como root (sudo)." >&2
  exit 1
fi
id "$linux_user" >/dev/null

if [[ "$(ps -p 1 -o comm=)" != "systemd" ]]; then
  printf '[boot]\nsystemd=true\n' >> /etc/wsl.conf
  echo "systemd ativado. Rode 'wsl --shutdown' no Windows e execute este script de novo." >&2
  exit 1
fi

. /etc/os-release

apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

usermod -aG docker "$linux_user"
systemctl enable --now docker

docker run --rm hello-world
docker --version
docker compose version
