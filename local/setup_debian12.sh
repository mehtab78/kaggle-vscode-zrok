#!/bin/bash
#===============================================================================
# Kaggle VS Code Zrok - Debian 12 Setup Script
# This script installs all dependencies needed for Kaggle remote connection
#===============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script requires root privileges for package installation."
        echo "Please run with: sudo $0"
        exit 1
    fi
}

# Detect Debian version
check_debian() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [ "$ID" != "debian" ] && [ "$ID_LIKE" != "debian" ]; then
            print_warning "This script is optimized for Debian 12."
            read -p "Continue anyway? [y/N]: " confirm
            if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
                exit 1
            fi
        fi
        if [ "$VERSION_ID" != "12" ]; then
            print_warning "Detected $PRETTY_NAME (Script optimized for Debian 12)"
        else
            print_success "Detected Debian 12 (Bookworm)"
        fi
    fi
}

# Update package lists
update_packages() {
    print_info "Updating package lists..."
    apt-get update -qq
    print_success "Package lists updated"
}

# Install SSH client and tools
install_ssh_tools() {
    print_info "Installing SSH tools..."
    apt-get install -y -qq openssh-client sshpass > /dev/null 2>&1
    print_success "SSH tools installed (openssh-client, sshpass)"
}

# Install Python3 and dependencies
install_python() {
    print_info "Installing Python3..."
    apt-get install -y -qq python3 python3-pip python3-venv > /dev/null 2>&1
    print_success "Python3 installed"
}

# Install VS Code (optional)
install_vscode() {
    if command -v code &> /dev/null; then
        print_success "VS Code already installed"
        return
    fi

    read -p "Install VS Code? [Y/n]: " install_code
    if [ "$install_code" = "n" ] || [ "$install_code" = "N" ]; then
        print_info "Skipping VS Code installation"
        return
    fi

    print_info "Installing VS Code..."
    
    # Install dependencies
    apt-get install -y -qq wget gpg apt-transport-https > /dev/null 2>&1
    
    # Add Microsoft GPG key
    wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/packages.microsoft.gpg
    
    # Add VS Code repository
    echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list
    
    # Install VS Code
    apt-get update -qq
    apt-get install -y -qq code > /dev/null 2>&1
    
    print_success "VS Code installed"
}

# Install VS Code Remote SSH extension
install_vscode_extensions() {
    if ! command -v code &> /dev/null; then
        return
    fi

    # Get the actual user (not root)
    ACTUAL_USER=${SUDO_USER:-$USER}
    
    print_info "Installing VS Code Remote SSH extension..."
    sudo -u "$ACTUAL_USER" code --install-extension ms-vscode-remote.remote-ssh --force 2>/dev/null || true
    sudo -u "$ACTUAL_USER" code --install-extension ms-vscode-remote.remote-ssh-edit --force 2>/dev/null || true
    print_success "VS Code extensions installed"
}

# Setup SSH directory and config
setup_ssh_config() {
    ACTUAL_USER=${SUDO_USER:-$USER}
    USER_HOME=$(getent passwd "$ACTUAL_USER" | cut -d: -f6)
    SSH_DIR="$USER_HOME/.ssh"
    
    print_info "Setting up SSH configuration..."
    
    # Create .ssh directory if it doesn't exist
    if [ ! -d "$SSH_DIR" ]; then
        mkdir -p "$SSH_DIR"
        chown "$ACTUAL_USER:$ACTUAL_USER" "$SSH_DIR"
        chmod 700 "$SSH_DIR"
    fi
    
    # Create config file if it doesn't exist
    if [ ! -f "$SSH_DIR/config" ]; then
        touch "$SSH_DIR/config"
        chown "$ACTUAL_USER:$ACTUAL_USER" "$SSH_DIR/config"
        chmod 600 "$SSH_DIR/config"
    fi
    
    print_success "SSH configuration directory ready"
}

# Generate SSH key if not exists
setup_ssh_key() {
    ACTUAL_USER=${SUDO_USER:-$USER}
    USER_HOME=$(getent passwd "$ACTUAL_USER" | cut -d: -f6)
    SSH_KEY="$USER_HOME/.ssh/id_ed25519"
    
    if [ -f "$SSH_KEY" ]; then
        print_success "SSH key already exists"
        return
    fi

    read -p "Generate SSH key for passwordless authentication? [Y/n]: " gen_key
    if [ "$gen_key" = "n" ] || [ "$gen_key" = "N" ]; then
        return
    fi

    print_info "Generating SSH key..."
    sudo -u "$ACTUAL_USER" ssh-keygen -t ed25519 -f "$SSH_KEY" -N "" -C "kaggle-vscode"
    print_success "SSH key generated: $SSH_KEY"
    
    echo ""
    print_info "Your public key (add this to Kaggle notebook):"
    echo ""
    cat "${SSH_KEY}.pub"
    echo ""
}

# Make Python script executable
setup_connect_script() {
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    ACTUAL_USER=${SUDO_USER:-$USER}
    
    if [ -f "$SCRIPT_DIR/connect.py" ]; then
        chmod +x "$SCRIPT_DIR/connect.py"
        chown "$ACTUAL_USER:$ACTUAL_USER" "$SCRIPT_DIR/connect.py"
        print_success "Connection script ready: $SCRIPT_DIR/connect.py"
    fi
}

# Create convenient alias
create_alias() {
    ACTUAL_USER=${SUDO_USER:-$USER}
    USER_HOME=$(getent passwd "$ACTUAL_USER" | cut -d: -f6)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    BASHRC="$USER_HOME/.bashrc"
    ALIAS_LINE="alias kaggle-connect='python3 $SCRIPT_DIR/connect.py'"
    
    if grep -q "kaggle-connect" "$BASHRC" 2>/dev/null; then
        print_info "Alias 'kaggle-connect' already exists"
    else
        echo "" >> "$BASHRC"
        echo "# Kaggle VS Code Connection" >> "$BASHRC"
        echo "$ALIAS_LINE" >> "$BASHRC"
        print_success "Added alias 'kaggle-connect' to .bashrc"
        print_info "Run 'source ~/.bashrc' or restart terminal to use"
    fi
}

# Print summary
print_summary() {
    print_header "Setup Complete!"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    echo "Installed components:"
    echo "  • OpenSSH client"
    echo "  • sshpass (for password authentication)"
    echo "  • Python3"
    
    if command -v code &> /dev/null; then
        echo "  • VS Code with Remote SSH extension"
    fi
    
    echo ""
    echo "Usage:"
    echo "  1. Run the Kaggle notebook to start the tunnel"
    echo "  2. Connect using one of these methods:"
    echo ""
    echo "     # Interactive mode:"
    echo "     python3 $SCRIPT_DIR/connect.py"
    echo ""
    echo "     # Direct connection:"
    echo "     python3 $SCRIPT_DIR/connect.py -H your-hostname.share.zrok.io"
    echo ""
    echo "     # Open in VS Code:"
    echo "     python3 $SCRIPT_DIR/connect.py -H your-hostname.share.zrok.io --vscode"
    echo ""
    echo "     # Or use the alias (after restarting terminal):"
    echo "     kaggle-connect"
    echo ""
}

# Main execution
main() {
    print_header "Kaggle VS Code Zrok - Debian 12 Setup"
    
    check_root
    check_debian
    update_packages
    install_ssh_tools
    install_python
    install_vscode
    install_vscode_extensions
    setup_ssh_config
    setup_ssh_key
    setup_connect_script
    create_alias
    print_summary
}

main "$@"
