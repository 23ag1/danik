#!/usr/bin/env bash
# Публикация проекта в GitHub (запускать на VPS: /root/danik/fraud_monitor)
set -euo pipefail
cd "$(dirname "$0")/.."

REPO_NAME="${1:-danik}"
VISIBILITY="${2:-private}"

if ! command -v gh >/dev/null; then
  echo "Установите GitHub CLI: apt install gh && gh auth login"
  exit 1
fi

echo "=== GitHub user ==="
GH_USER=$(gh api user -q .login)
echo "$GH_USER"

echo "=== Обновление .gitignore, коммит ==="
git add -A
git status --short | head -30

if git diff --cached --quiet; then
  echo "Нет изменений для коммита"
else
  git commit -m "$(cat <<EOF
docs: полная документация проекта и актуальный код прототипа

- docs/PROJECT-OVERVIEW.md для написания диплома
- API, соответствие главам 1-2, ML+frontend+pipeline
EOF
)"
fi

if gh repo view "${GH_USER}/${REPO_NAME}" >/dev/null 2>&1; then
  echo "Репозиторий ${GH_USER}/${REPO_NAME} уже существует"
else
  echo "=== Создание репозитория ${REPO_NAME} (${VISIBILITY}) ==="
  gh repo create "${REPO_NAME}" --"${VISIBILITY}" --source=. --description "Fraud Monitor — диплом ИБ, мониторинг соцсетей"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "https://github.com/${GH_USER}/${REPO_NAME}.git"
else
  git remote add origin "https://github.com/${GH_USER}/${REPO_NAME}.git"
fi

echo "=== Push ==="
git branch -M main 2>/dev/null || true
git push -u origin HEAD:main

echo ""
echo "Готово: https://github.com/${GH_USER}/${REPO_NAME}"
