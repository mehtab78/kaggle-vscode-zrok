#!/bin/bash
# Setup SSH server on Kaggle

set -e

echo "Installing openssh-server..."
apt-get update -qq
apt-get install -y openssh-server > /dev/null 2>&1

# Create required directories
mkdir -p /run/sshd
mkdir -p /root/.ssh
chmod 700 /root/.ssh

# Configure SSHD
cat > /etc/ssh/sshd_config << 'EOF'
Port 22
PermitRootLogin yes
PasswordAuthentication yes
PubkeyAuthentication yes
X11Forwarding yes
AllowTcpForwarding yes
ClientAliveInterval 60
ClientAliveCountMax 3
Subsystem sftp /usr/lib/openssh/sftp-server
EOF

# Setup authorized_keys if URL provided
if [ -n "$1" ]; then
    echo "Downloading authorized_keys from $1..."
    curl -sL "$1" >> /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
fi

# Save environment variables for SSH sessions
ENV_FILE="/kaggle/working/kaggle_env_vars.txt"
env | grep -E '^(KAGGLE_|CUDA_|PATH|LD_LIBRARY)' | sed 's/^/export /' > "$ENV_FILE"

# Add to bashrc
if ! grep -q "kaggle_env_vars" /root/.bashrc 2>/dev/null; then
    echo "[ -f $ENV_FILE ] && source $ENV_FILE" >> /root/.bashrc
fi

# Generate host keys if missing
ssh-keygen -A > /dev/null 2>&1

# Start SSH server
echo "Starting SSH server..."
/usr/sbin/sshd

echo "✓ SSH server running on port 22"
