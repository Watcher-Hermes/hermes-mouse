<#
.SYNOPSIS
    Hermes Mouse — one-line installer.
.DESCRIPTION
    Downloads hermesmouse.py and adds it to PATH.
    Usage: iex "& { $(irm https://raw.githubusercontent.com/Watcher-Hermes/hermes-mouse/main/install.ps1) }"
#>

$Repo  = "https://raw.githubusercontent.com/Watcher-Hermes/hermes-mouse/main"
$Dest  = "$env:USERPROFILE\hermesmouse.py"
$Bat   = "$env:USERPROFILE\hermesmouse.bat"
$Bin   = "$env:USERPROFILE\.hermes-mouse-bin"
$BinPy = "$Bin\hermesmouse.py"

Write-Host "=== Hermes Mouse Installer ===" -ForegroundColor Cyan

# --- Python check ---
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) {
    $py = (Get-Command python3 -ErrorAction SilentlyContinue).Source
}
if (-not $py) {
    Write-Host "[HATA] Python bulunamadi. Lutfen python.org'dan yukleyin." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Python: $py" -ForegroundColor Green

# --- Download hermesmouse.py ---
Write-Host "[..] Indiriliyor: hermesmouse.py" -NoNewline
try {
    $script = Invoke-WebRequest -Uri "$Repo/hermesmouse.py" -UseBasicParsing
    [System.IO.Directory]::CreateDirectory($Bin) | Out-Null
    [System.IO.File]::WriteAllText($BinPy, $script.Content, [System.Text.Encoding]::UTF8)
    Write-Host " -> OK" -ForegroundColor Green
} catch {
    Write-Host " -> HATA: $_" -ForegroundColor Red
    exit 1
}

# --- Create batch wrapper in USERPROFILE ---
$batContent = @"
@echo off
python "$BinPy" %*
"@
[System.IO.File]::WriteAllText($Bat, $batContent, [System.Text.Encoding]::ASCII)

# --- Add to PATH (User level) ---
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$Bin*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$Bin", "User")
    # Also update current session
    $env:Path = "$env:Path;$Bin"
    Write-Host "[OK] PATH'e eklendi: $Bin" -ForegroundColor Green
} else {
    Write-Host "[OK] PATH zaten ayarli" -ForegroundColor Green
}

# --- Verify ---
Write-Host "[..] Dogrulaniyor..." -NoNewline
try {
    $test = & python $BinPy pos
    if ($test -match "^\d+ \d+$") {
        Write-Host " -> OK (cursor: $test)" -ForegroundColor Green
    } else {
        Write-Host " -> $test" -ForegroundColor Yellow
    }
} catch {
    Write-Host " -> HATA: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Kullanim / Usage:" -ForegroundColor Cyan
Write-Host "  hermesmouse pos" -ForegroundColor White
Write-Host "  hermesmouse click 500 300" -ForegroundColor White
Write-Host "  hermesmouse element Notepad list" -ForegroundColor White
Write-Host "  hermesmouse key esc" -ForegroundColor White
Write-Host "  hermesmouse screenshot" -ForegroundColor White
Write-Host "  hermesmouse run workflow.json" -ForegroundColor White
Write-Host ""
Write-Host "Dokuman: https://github.com/Watcher-Hermes/hermes-mouse" -ForegroundColor Cyan
