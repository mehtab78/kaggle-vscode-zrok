# Kaggle VS Code Connection Helper for Windows PowerShell

Write-Host "=========================================="
Write-Host "  Kaggle VS Code Connection Helper"
Write-Host "=========================================="

# Prompt for connection details
$Hostname = Read-Host "Enter zrok hostname (e.g., abc123.share.zrok.io)"
$Password = Read-Host "Enter password (default: kaggle123)"
if ([string]::IsNullOrEmpty($Password)) {
    $Password = "kaggle123"
}

Write-Host ""
Write-Host "Connecting to Kaggle..."
Write-Host "Password: $Password"
Write-Host ""

ssh root@$Hostname
