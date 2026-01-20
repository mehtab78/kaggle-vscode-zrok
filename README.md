# Kaggle VS Code Integration with Zrok

Connect to Kaggle notebooks remotely using VS Code through zrok private tunnels.

**150GB/month free** | **Zero-trust networking** | **Auto-discovery**

## 🚀 Quick Start

### 1. Get Zrok Token
Create a free account at [zrok.io](https://zrok.io) and copy your token.

### 2. On Kaggle
Copy `main.ipynb` to Kaggle, set your `ZROK_TOKEN`, and run both cells.

### 3. On Local Machine
```bash
# Install zrok (one-time)
curl -sSf https://get.zrok.io | bash

# Connect (auto-discovers Kaggle tunnel!)
python local/connect.py --token YOUR_ZROK_TOKEN
```

That's it! VS Code opens automatically.

## ✨ Features

- **Auto-discovery**: No need to copy share tokens manually
- **Private tunnels**: More secure than public endpoints
- **Zrok API integration**: Manages environments automatically
- **VS Code ready**: Opens remote session with one command

## 📁 Structure

```
kaggle-vscode-zrok/
├── main.ipynb              # Run this on Kaggle
├── local/
│   ├── connect.py          # Run this locally
│   ├── install.sh          # Quick installer
│   └── setup_debian12.sh   # Full Debian setup
├── kaggle/
│   ├── setup_kaggle.ipynb  # Alternative notebook
│   └── setup_script.py     # Standalone script
└── tests/                  # Test suite
```

## 🔧 Configuration

### Kaggle (main.ipynb Cell 1)
```python
ZROK_TOKEN = "<YOUR_TOKEN>"    # Required
SSH_PASSWORD = "0"             # SSH password
AUTHORIZED_KEYS_URL = ""       # Optional: URL to public keys
ENV_NAME = "kaggle_server"     # Must match client
```

### Local (connect.py)
```bash
python local/connect.py --token YOUR_TOKEN    # Basic usage
python local/connect.py --token YOUR_TOKEN --no-vscode  # Skip VS Code
python local/connect.py --stop                # Stop tunnel
```

| Option | Default | Description |
|--------|---------|-------------|
| `--token` | (prompt) | Your zrok API token |
| `--name` | kaggle_client | Local environment name |
| `--server-name` | kaggle_server | Server environment name |
| `--port` | 9191 | Local tunnel port |
| `--no-vscode` | false | Skip VS Code launch |
| `--workspace` | /kaggle/working | Remote directory |

## 🔄 How It Works

1. **Kaggle**: Runs SSH server + `zrok share private` (creates tunnel)
2. **Zrok API**: Stores share info in your account
3. **Local**: `connect.py` queries API to find share token automatically
4. **Connect**: `zrok access private` creates local tunnel → SSH → VS Code

## ⚠️ Notes

- Kaggle notebooks have **12-hour runtime limit**
- Save work frequently
- Connection breaks when notebook times out
- Token is saved locally at `~/.kaggle_vscode_config.json`

## 🔐 Security

- **Private tunnels only**: Not publicly accessible
- **Zero-trust**: OpenZiti-based networking
- **No port forwarding**: Works behind NAT/firewalls
- Use SSH keys for better security (set `AUTHORIZED_KEYS_URL`)

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| "Environment not found" | Make sure Kaggle Cell 2 is running |
| "zrok not installed" | Run `curl -sSf https://get.zrok.io \| bash` |
| VS Code won't connect | Install [Remote SSH](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh) extension |
| Connection refused | Check SSH server: run utility cell in notebook |

## 📚 Credits

Based on [int11/Kaggle_remote_zrok](https://github.com/int11/Kaggle_remote_zrok)

## 📝 License

MIT License
