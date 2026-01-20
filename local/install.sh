#!/bin/bash
#===============================================================================
# Quick Install Script for Debian 12
# Run: curl -sSL https://raw.githubusercontent.com/mehtab78/kaggle-vscode-zrok/main/local/install.sh | sudo bash
#===============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Kaggle VS Code Zrok - Quick Install${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"

# Install git if needed
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    apt-get update -qq && apt-get install -y -qq git
fi

# Clone repository
INSTALL_DIR="/opt/kaggle-vscode-zrok"
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR" && git pull -q
else
    echo "Cloning repository..."
    git clone -q https://github.com/mehtab78/kaggle-vscode-zrok.git "$INSTALL_DIR"
fi

# Run setup
cd "$INSTALL_DIR/local"
chmod +x setup_debian12.sh
./setup_debian12.sh

echo -e "\n${GREEN}✅ Installation complete!${NC}"
echo "Repository installed at: $INSTALL_DIR"
