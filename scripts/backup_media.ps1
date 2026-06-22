# PowerShell wrapper for Windows (development)
param(
    [string]$ProjectDir = "D:\\ndeascloud\\byetu\\backend",
    [string]$Python = "python",
    [string]$BackupDir = "D:\\ndeascloud\\byetu\\backend\\backups"
)

$EnvFile = Join-Path $ProjectDir ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^\s*#") { return }
        if ($_ -match "^\s*$") { return }
        $parts = $_ -split "=", 2
        if ($parts.Length -eq 2) { $name = $parts[0].Trim(); $value = $parts[1].Trim(); $Env:$name = $value }
    }
}

Set-Location $ProjectDir
& $Python "scripts\\backup_and_upload_media.py" --backup-dir $BackupDir --media-root "$ProjectDir\\media" --upload --remove-local-zip
