#!/usr/bin/env bash
# Pousse le repo Art vers GitHub. Lance depuis le dossier Art/ :  bash push.sh
set -e
REMOTE="https://github.com/Roubignolo/art.git"

git init -q
git add .
git commit -q -m "Initial commit — projet Art POD domaine public" || true
git branch -M main
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE"

# Si tu as GitHub CLI installé, il gère l'authentification dans le navigateur :
if command -v gh >/dev/null 2>&1; then
  gh auth status >/dev/null 2>&1 || gh auth login
fi

# Si le repo distant a déjà un commit (README créé à la main), on rebase d'abord.
git pull --rebase origin main 2>/dev/null || true
git push -u origin main
echo "✓ Repo poussé sur $REMOTE"
