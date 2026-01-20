# Kaggle VS Code Integration with Zrok

Connect to Kaggle notebooks remotely using VS Code through zrok tunneling.

## 🚀 Quick Start

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

### Step 3: Connect from VS Code
1. Install "Remote - SSH" extension in VS Code
2. Copy the SSH command displayed in Kaggle output
3. Add the config to your `~/.ssh/config`
4. Connect using VS Code Remote SSH

## 📁 Repository Structure

```
├── kaggle/
│   ├── setup_kaggle.ipynb    # Jupyter notebook for Kaggle
│   └── setup_script.py       # Python script version
├── local/
│   ├── connect.sh            # Linux/Mac connection helper
│   ├── connect.ps1           # Windows PowerShell helper
│   └── ssh_config_template   # SSH config template
└── .vscode/
    ├── settings.json         # VS Code settings
    └── extensions.json       # Recommended extensions
```

## 🔧 Detailed Instructions

### On Kaggle Notebook:

```python
# Run this in a Kaggle notebook cell
!pip install kaggle-vscode-zrok  # or copy the setup script
```

### Manual Setup:
```python
# Cell 1: Install dependencies
!apt-get update && apt-get install -y openssh-server
!pip install jupyterlab

# Cell 2: Configure SSH
!mkdir -p /root/.ssh
!echo "YOUR_SSH_PUBLIC_KEY" >> /root/.ssh/authorized_keys
!chmod 700 /root/.ssh
!chmod 600 /root/.ssh/authorized_keys
!service ssh start

# Cell 3: Install and setup zrok
!wget https://github.com/openziti/zrok/releases/latest/download/zrok_linux_amd64.tar.gz
!tar -xzf zrok_linux_amd64.tar.gz
!./zrok enable YOUR_ZROK_TOKEN
!./zrok share private --backend-mode tcpTunnel localhost:22 &
```

## ⚠️ Important Notes

- Kaggle notebooks have a 12-hour runtime limit
- GPU sessions may have shorter limits
- Save your work frequently
- The connection will break when the notebook times out

## 🔐 Security

- Use SSH key authentication (recommended)
- Never share your zrok token
- The tunnel is private by default

## 📝 License

MIT License
