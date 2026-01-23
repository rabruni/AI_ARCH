#!/usr/bin/env bash

echo "=== FIXING NVM PATH FOR BASH ==="

touch "$HOME/.bashrc"

if ! grep -q 'export NVM_DIR="$HOME/.nvm"' "$HOME/.bashrc" 2>/dev/null; then
  echo "Adding nvm initialization to ~/.bashrc"
  echo "" >> "$HOME/.bashrc"
  echo "# >>> NVM SETUP >>>" >> "$HOME/.bashrc"
  echo 'export NVM_DIR="$HOME/.nvm"' >> "$HOME/.bashrc"
  echo '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"' >> "$HOME/.bashrc"
  echo '[ -s "$NVM_DIR/bash_completion" ] && . "$NVM_DIR/bash_completion"' >> "$HOME/.bashrc"
