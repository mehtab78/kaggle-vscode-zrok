# Kaggle VS Code Integration with Zrok

Connect to Kaggle notebooks remotely using VS Code through zrok tunneling.

**Supports both PUBLIC and PRIVATE tunnels** | **Optimized for Debian 12**

## 🚀 Quick Start

### One-Line Install (Debian 12)

```bash
curl -sSL https://raw.githubusercontent.com/mehtab78/kaggle-vscode-zrok/main/local/install.sh | sudo bash
```

## 📋 Tunnel Modes

| Mode | Security | Client Requirements | Best For |
|------|----------|---------------------|----------|
| **PUBLIC** | Lower | SSH only | Quick access, simpler setup |
| **PRIVATE** | Higher | zrok + SSH | Production, sensitive work |

### 🌐 PUBLIC Tunnel
- Direct SSH access: `ssh root@hostname.share.zrok.io`
- No zrok installation needed on client
- Easier to set up and use

### 🔒 PRIVATE Tunnel  
- Requires `zrok access private <token>` on client
- More secure (tunnel not publicly accessible)
- Requires zrok on both Kaggle and local machine

## 📁 Repository Structure

```
kaggle-vscode-zrok/
├── kaggle/
│   ├── setup_kaggle.ipynb    # Jupyter notebook for Kaggle
│   └── setup_script.py       # Python script (supports public/private)
├── local/
│   ├── connect.py            # Connection helper (supports public/private)
│   ├── setup_debian12.sh     # Debian 12 setup script
│   └── install.sh            # One-line installer
└── .vscode/
    ├── settings.json
    └── extensions.json
```

## 🔧 Setup Instructions

### Step 1: Get Zrok Token
1. Go to [https://zrok.io](https://zrok.io)
2. Create a free account
3. Copy your token from the dashboard

### Step 2: On Kaggle

Edit and run `kaggle/setup_script.py`:

```python
# Configuration
ZROK_TOKEN = "your_token_here"
SSH_PASSWORD = "kaggle123"
GITHUB_USERNAME = ""  # Optional: for SSH key auth

# Tunnel mode: "public" or "private"
TUNNEL_MODE = "public"
```

Or copy the notebook `kaggle/setup_kaggle.ipynb` to Kaggle.

### Step 3: Connect from Local Machine

#### PUBLIC Tunnel (Recommended for beginners)

```bash
# Interactive mode
python3 local/connect.py

# Direct SSH connection
python3 local/connect.py -H abc123.share.zrok.io

# Open in VS Code
python3 local/connect.py -H abc123.share.zrok.io --vscode

# Use SSH key instead of password
python3 local/connect.py -H abc123.share.zrok.io -k
```

#### PRIVATE Tunnel (More secure)

```bash
# Connect with share token
python3 local/connect.py --private abc123xyz

# Open in VS Code
python3 local/connect.py --private abc123xyz --vscode

# Custom local port
python3 local/connect.py --private abc123xyz --port 9191
```

## 🐍 Local Connection Script

The `connect.py` script provides a full-featured connection manager:

```bash
Usage: connect.py [OPTIONS]

PUBLIC tunnel options:
  -H, --hostname HOST    Public tunnel hostname (abc123.share.zrok.io)

PRIVATE tunnel options:
  --private TOKEN        Private tunnel share token
  --port PORT            Local port (default: 9191)

Common options:
  -p, --password PASS    SSH password (default: kaggle123)
  -k, --key              Use SSH key authentication
  --vscode               Open in VS Code
  --setup-ssh HOST       Update SSH config only
  --stop                 Stop zrok access process
  --list                 Show saved configuration
```

### Features:
- 🔄 Remembers last used hostname/token
- 📝 Auto-updates `~/.ssh/config`
- 🚀 Direct VS Code integration
- 🔑 Supports password and SSH key auth
- 🎨 Interactive menu mode
- 🔒 Supports both public and private tunnels

## 🐧 Debian 12 Setup

The setup script installs everything you need:

```bash
sudo ./local/setup_debian12.sh
```

Installs:
- ✅ OpenSSH client & sshpass
- ✅ Python3
- ✅ VS Code (optional)
- ✅ VS Code Remote SSH extension
- ✅ SSH key generation (optional)
- ✅ zrok (for private tunnels)

## 🔧 Kaggle Setup Script

The `setup_script.py` supports both tunnel modes:

```python
# ═══════════════════════════════════════════════════════════════
#                     CONFIGURATION
# ═══════════════════════════════════════════════════════════════

ZROK_TOKEN = "YOUR_ZROK_TOKEN"       # Get from https://zrok.io
SSH_PASSWORD = "kaggle123"            # SSH login password
GITHUB_USERNAME = ""                  # Optional: GitHub username for SSH keys

# Tunnel mode: "public" or "private"
TUNNEL_MODE = "public"
```

### PUBLIC Mode Output:
```
🎉 PUBLIC TUNNEL ACTIVE!
═══════════════════════════════════════════════════════════════
📋 CONNECTION INFO:
   Hostname:  abc123.share.zrok.io
   User:      root
   Password:  kaggle123

🔗 CONNECT VIA SSH:
   ssh root@abc123.share.zrok.io
```

### PRIVATE Mode Output:
```
🔒 PRIVATE TUNNEL ACTIVE!
═══════════════════════════════════════════════════════════════
📋 CONNECTION INFO:
   Share Token:  abc123xyz
   User:         root
   Password:     kaggle123

🔗 ON YOUR LOCAL MACHINE:
   Step 1: zrok access private abc123xyz
   Step 2: ssh root@localhost -p 9191
```

## ⚠️ Important Notes

- Kaggle notebooks have a **12-hour runtime limit**
- GPU sessions may have **shorter limits**
- Save your work frequently
- The connection will break when the notebook times out
- PUBLIC tunnels are easier but less secure
- PRIVATE tunnels require zrok on your local machine

## 🔐 Security Recommendations

1. **Use SSH keys** instead of passwords when possible
2. **Use PRIVATE tunnels** for sensitive work
3. **Never share** your zrok token
4. **Change default password** to something secure
5. Config stored securely at `~/.kaggle_vscode_config.json`

## 🛠️ Troubleshooting

**Connection refused:**
- Ensure Kaggle notebook is still running
- Check that SSH service started
- Verify the zrok tunnel is active

**PRIVATE tunnel not working:**
- Ensure zrok is installed locally: `curl -sSf https://get.zrok.io | bash`
- Check `zrok access private <token>` is running
- Default local port is 9191

**VS Code won't connect:**
- Install Remote SSH extension
- Check SSH config: `cat ~/.ssh/config`
- Try manual SSH first

## 📝 License

MIT License
