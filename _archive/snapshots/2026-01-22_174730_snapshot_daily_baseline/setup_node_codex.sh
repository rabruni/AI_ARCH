#!/usr/bin/env bash

echo "=== SAFE NVM + NODE + CODEX SETUP ==="

# Detect shell + rc file
CURSHELL="$(ps -p $$ -o comm= | tr -d ' ')"
RC="$HOME/.bashrc"
[ "$CURSHELL" = "zsh" ] && RC="$HOME/.zshrc"

echo "Shell: $CURSHELL"
echo "RC file: $RC"
touch "$RC"

# Install nvm if missing
if [ ! -d "$HOME/.nvm" ]; then
  echo "Installing nvm..."
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
else
  echo "nvm already installed"
fi

# Ensure nvm init lines exist (no heredoc nesting)
if ! grep -q 'export NVM_DIR="$HOME/.nvm"' "$RC" 2>/dev/null; then
  echo "Adding nvm init to $RC"
  echo '' >> "$RC"
  echo '# >>> NVM SETUP >>>' >> "$RC"
  echo 'export NVM_DIR="$HOME/.nvm"' >> "$RC"
  echo '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"' >> "$RC"
  echo '[ -s "$NVM_DIR/bash_completion" ] && . "$NVM_DIR/bash_completion"' >> "$RC"
  echo '# <<< NVM SETUP <<<' >> "$RC"
else
  echo "nvm init already present in $RC"
fi

# Load nvm now
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
  . "$NVM_DIR/nvm.sh"
  echo "nvm loaded"
else
  echo "ERROR: nvm.sh not found"
  exit 1
fi

# Install Node LTS
echo "Installing Node LTS..."
nvm install --lts
nvm use --lts
nvm alias default lts/*

# Verify
echo "Node version:"
node -v
echo "npm version:"
npm -v

# Install Codex
echo "Installing Codex CLI..."
npm install -g @openai/codex

echo "Codex check:"
codex --help || echo "Codex installed, but --help failed (restart terminal)"

echo "=== DONE ==="
echo "If anything looks off, restart your terminal once."
