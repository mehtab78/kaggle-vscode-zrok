#!/bin/bash
#===============================================================================
# Quick Install Script for Linux
# Run: curl -sSL https://raw.githubusercontent.com/mehtab78/kaggle-vscode-zrok/main/local/install.sh | bash
#===============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Kaggle VS Code Zrok - Quick Install${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"

# Install zrok if needed
if ! command -v zrok &> /dev/null; then
    echo "Installing zrok..."
    curl -sSf https://get.zrok.io | bash
fi

# Clone or update repository
INSTALL_DIR="${HOME}/.kaggle-vscode-zrok"
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR" && git pull -q
else
    echo "Cloning repository..."
    git clone -q https://github.com/mehtab78/kaggle-vscode-zrok.git "$INSTALL_DIR"
fi

# Create symlink for easy access
mkdir -p "${HOME}/.local/bin"
ln -sf "$INSTALL_DIR/local/connect.py" "${HOME}/.local/bin/kaggle-connect"
chmod +x "${HOME}/.local/bin/kaggle-connect"

echo -e "\n${GREEN}✅ Installation complete!${NC}"
echo ""
echo "Usage:"
echo "  kaggle-connect --token YOUR_ZROK_TOKEN"
echo ""
echo "Or run directly:"
echo "  python $INSTALL_DIR/local/connect.py --token YOUR_ZROK_TOKEN"
