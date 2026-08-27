#!/usr/bin/env bash
set -euo pipefail

APP_NAME="ielts-speaking-bot"
APP_USER="ielts-bot"
INSTALL_DIR="/opt/${APP_NAME}"
SERVICE_NAME="${APP_NAME}.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo bash deploy/install.sh"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required. Install it first, e.g.: apt install python3 python3-venv"
  exit 1
fi

if ! id "${APP_USER}" >/dev/null 2>&1; then
  useradd --system --home-dir "${INSTALL_DIR}" --create-home --shell /usr/sbin/nologin "${APP_USER}"
fi

mkdir -p "${INSTALL_DIR}"
rsync -a --delete \
  --exclude '.venv' \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '.env' \
  "${REPO_DIR}/" "${INSTALL_DIR}/"

if [[ ! -f "${INSTALL_DIR}/.env" ]]; then
  cp "${INSTALL_DIR}/.env.example" "${INSTALL_DIR}/.env"
  echo "Created ${INSTALL_DIR}/.env from template — fill in your secrets before starting."
fi

python3 -m venv "${INSTALL_DIR}/.venv"
"${INSTALL_DIR}/.venv/bin/pip" install --upgrade pip
"${INSTALL_DIR}/.venv/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"

chown -R "${APP_USER}:${APP_USER}" "${INSTALL_DIR}"
chmod 600 "${INSTALL_DIR}/.env"

sed "s|@INSTALL_DIR@|${INSTALL_DIR}|g; s|@APP_USER@|${APP_USER}|g" \
  "${SCRIPT_DIR}/ielts-speaking-bot.service" > "/etc/systemd/system/${SERVICE_NAME}"

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"

echo
echo "Installed to ${INSTALL_DIR}"
echo "Edit secrets:  nano ${INSTALL_DIR}/.env"
echo "Start bot:     systemctl start ${SERVICE_NAME}"
echo "View logs:     journalctl -u ${SERVICE_NAME} -f"
echo "Health check:  curl http://127.0.0.1:8080/health"
