#!/bin/bash
# Kaggle VS Code Connection Helper for Linux/Mac

echo "=========================================="
echo "  Kaggle VS Code Connection Helper"
echo "=========================================="

# Check if ssh is installed
if ! command -v ssh &> /dev/null; then
    echo "Error: SSH is not installed"
    exit 1
fi

# Prompt for connection details
read -p "Enter zrok hostname (e.g., abc123.share.zrok.io): " HOSTNAME
read -p "Enter password [kaggle123]: " PASSWORD
PASSWORD=${PASSWORD:-kaggle123}

echo ""
echo "Connecting to Kaggle..."
echo "Password: $PASSWORD"
echo ""

ssh root@$HOSTNAME
