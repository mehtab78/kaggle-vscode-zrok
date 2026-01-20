# Kaggle VS Code Integration with Zrok

Connect to Kaggle notebooks remotely using VS Code through zrok tunneling.

**Optimized for Debian 12 (Bookworm)**

## 🚀 Quick Start

### One-Line Install (Debian 12)

```bash
curl -sSL https://raw.githubusercontent.com/mehtab78/kaggle-vscode-zrok/main/local/install.sh | sudo bash
```

Or clone and run manually:

```bash
git clone https://github.com/mehtab78/kaggle-vscode-zrok.git
cd kaggle-vscode-zrok/local
sudo ./setup_debian12.sh
```

### Step 1: Get Zrok Token (One-time setup)
1. Go to [https://zrok.io](https://zrok.io)
2. Sign up for a free account
3. Get your zrok token from the dashboard

### Step 2: Setup on Kaggle
1. Create a new Kaggle notebook
2. Enable GPU/TPU if needed
3. Enable Internet access in notebook settings
4. Copy the contents of `kaggle/setup_kaggle.ipynb` or run `setup_script.py`
5. Replace `YOUR_ZROK_TOKEN` with your actual token
6. Run all cells
7. Note the hostname displayed (e.g., `abc123.share.zrok.io`)

### Step 3: Connect from Local Machine

**Interactive Mode:**
```bash
python3 local/connect.py
# Or use the alias after setup:
kaggle-connect
```

**Direct Connection:**
```bash
# SSH terminal connection
python3 local/connect.py -H abc123.share.zrok.io

# Open in VS Code directly
python3 local/connect.py -H abc123.share.zrok.io --vscode
```

## 📁 Repository Structure

```
kaggle-vscode-zrok/
├── kaggle/
│   ├── setup_kaggle.ipynb    # Jupyter notebook for Kaggle
│   └── setup_script.py       # Python script version
├── local/
│   ├── connect.py            # Python connection helper (recommended)
│   ├── setup_debian12.sh     # Debian 12 setup script
│   ├── install.sh            # One-line installer
│   ├── connect.sh            # Legacy bash script
│   ├── connect.ps1           # Windows PowerShell helper
│   └── ssh_config_template   # SSH config template
├── .vscode/
│   ├── settings.json         # VS Code settings
│   └── extensions.json       # Recommended extensions
└── requirements.txt
```

## 🐧 Debian 12 Setup Script

The `setup_debian12.sh` script automatically installs:

- ✅ OpenSSH client
- ✅ sshpass (for password authentication)
- ✅ Python3
- ✅ VS Code (optional)
- ✅ VS Code Remote SSH extension
- ✅ SSH key generation (optional)
- ✅ Shell alias `kaggle-connect`

```bash
sudo ./local/setup_debian12.sh
```

## 🐍 Python Connection Script

The `connect.py` script provides a full-featured connection manager:

```bash
# Interactive menu
python3 local/connect.py

# Direct SSH connection
python3 local/connect.py -H hostname.share.zrok.io

# With custom password
python3 local/connect.py -H hostname.share.zrok.io -p mypassword

# Use SSH key instead of password
python3 local/connect.py -H hostname.share.zrok.io -k

# Open directly in VS Code
python3 local/connect.py -H hostname.share.zrok.io --vscode

# Update SSH config only
python3 local/connect.py --setup-ssh hostname.share.zrok.io

# List saved connections
python3 local/connect.py --list
```

### Features:
- 🔄 Saves last used hostname/password
- 📝 Auto-updates `~/.ssh/config`
- 🚀 Direct VS Code integration
- 🔑 Supports both password and key authentication
- 🎨 Interactive menu mode

## 🔧 Manual Kaggle Setup

```python
# Configuration
ZROK_TOKEN = "your_token_here"
SSH_PASSWORD = "kaggle123"

# Install dependencies
!apt-get update -qq && apt-get install -y -qq openssh-server

# Configure SSH
!echo "root:$SSH_PASSWORD" | chpasswd
!sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
!sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
!service ssh start

# Install zrok
!wget -q https://github.com/openziti/zrok/releases/download/v0.4.44/zrok_0.4.44_linux_amd64.tar.gz
!tar -xzf zrok_0.4.44_linux_amd64.tar.gz && chmod +x zrok && mv zrok /usr/local/bin/

# Enable and start tunnel
!zrok enable $ZROK_TOKEN
!zrok share public --backend-mode tcpTunnel localhost:22
```

## ⚠️ Important Notes

- Kaggle notebooks have a **12-hour runtime limit**
- GPU sessions may have **shorter limits**
- Save your work frequently
- The connection will break when the notebook times out
- Use the "Keep alive" cell to prevent idle timeout

## 🔐 Security

- 🔑 Use SSH key authentication (recommended)
- 🚫 Never share your zrok token
- 🔒 The tunnel is private by default
- 📁 Config file stored securely at `~/.kaggle_vscode_config.json`

## 🛠️ Troubleshooting

**Connection refused:**
- Ensure the Kaggle notebook is still running
- Check that SSH service started successfully
- Verify the zrok tunnel is active

**VS Code won't connect:**
- Install Remote SSH extension: `code --install-extension ms-vscode-remote.remote-ssh`
- Check SSH config: `cat ~/.ssh/config`
- Try manual SSH first: `ssh root@hostname.share.zrok.io`

**Permission denied:**
- Default password is `kaggle123`
- Or use your SSH public key

## 📝 License

MIT License
