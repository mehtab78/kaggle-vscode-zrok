# Kaggle VS Code Integration with Zrok

Connect to Kaggle notebooks remotely using VS Code through zrok private tunnels.

**150GB/month free** | **Zero-trust networking** | **Auto-discovery**

## 🚀 Quick Start

### 1. Get Zrok Token
Create a free account at [zrok.io](https://zrok.io) and copy your token.

### 2. On Kaggle
Create a new notebook and run:
```python
!git clone https://github.com/mehtab78/kaggle-vscode-zrok.git
%cd /kaggle/working/kaggle-vscode-zrok
!python3 zrok_server.py --token "YOUR_ZROK_TOKEN" --password "0"
```

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
├── zrok_server.py          # Main server script (run on Kaggle)
├── local/
│   ├── connect.py          # Run this locally
│   └── install.sh          # Quick installer
├── kaggle/
│   └── setup_kaggle.ipynb  # Quick start notebook
└── tests/                  # Test suite
```

## 🔧 Configuration

### Kaggle (zrok_server.py)
```bash
python3 zrok_server.py --token "TOKEN" --password "0"
python3 zrok_server.py --token "TOKEN" --authorized_keys_url "URL"  # With SSH keys
```

| Option | Default | Description |
|--------|---------|-------------|
| `--token` | (required) | Your zrok API token |
| `--password` | 0 | SSH password |
| `--authorized_keys_url` | "" | URL to public keys file |
| `--env-name` | kaggle_server | Environment name |

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
