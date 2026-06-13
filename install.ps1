<#
.SYNOPSIS
    Hermes Mouse — one-line installer + Hermes Agent skill integration.
.DESCRIPTION
    Installs hermesmouse.py, adds to PATH, and registers the Hermes Agent skill
    so both terminal AND Hermes AI can use mouse/keyboard/element/screenshot commands.

    Usage (PowerShell Admin):
      iex "& { $(irm https://raw.githubusercontent.com/Watcher-Hermes/hermes-mouse/master/install.ps1) }"
#>

$Repo = "https://raw.githubusercontent.com/Watcher-Hermes/hermes-mouse/master"
$Bin  = "$env:USERPROFILE\.hermes-mouse-bin"
$BinPy = "$Bin\hermesmouse.py"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "     Hermes Mouse Kurulumu / Installation" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# ---- 1. Python Check ----
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command python3 -ErrorAction SilentlyContinue).Source }
if (-not $py) {
    Write-Host "[HATA] Python bulunamadi. Lutfen python.org'dan yukleyin." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Python: $py" -ForegroundColor Green

# ---- 2. Download hermesmouse.py ----
Write-Host "[1/4] hermesmouse.py indiriliyor..." -NoNewline
try {
    $script = Invoke-WebRequest -Uri "$Repo/hermesmouse.py" -UseBasicParsing
    [System.IO.Directory]::CreateDirectory($Bin) | Out-Null
    [System.IO.File]::WriteAllText($BinPy, $script.Content, [System.Text.Encoding]::UTF8)
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " HATA: $_" -ForegroundColor Red
    exit 1
}

# ---- 3. Add to PATH ----
Write-Host "[2/4] PATH'e ekleniyor..." -NoNewline
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$Bin*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$Bin", "User")
    $env:Path = "$env:Path;$Bin"
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " OK (zaten var)" -ForegroundColor Green
}

# ---- 4. Hermes Agent Skill Integration ----
$hermesSkills = "$env:LOCALAPPDATA\hermes\skills\windows-automation\mouse-klavye-ctypes"
$skillFile = "$hermesSkills\SKILL.md"
$hermesInstalled = Test-Path "$env:LOCALAPPDATA\hermes"

Write-Host "[3/4] Hermes Agent skill'i araniyor..." -NoNewline
if ($hermesInstalled) {
    Write-Host " bulundu" -ForegroundColor Green
    Write-Host "       Skill indiriliyor: windows-automation/mouse-klavye-ctypes..." -NoNewline
    try {
        [System.IO.Directory]::CreateDirectory($hermesSkills) | Out-Null
        $skillContent = Invoke-WebRequest -Uri "$Repo/SKILL.md" -UseBasicParsing
        [System.IO.File]::WriteAllText($skillFile, $skillContent, [System.Text.Encoding]::UTF8)
        Write-Host " OK" -ForegroundColor Green

        # Skill sync (Hermes'in skill havuzunu yenile)
        $syncScripts = @(
            "$env:LOCALAPPDATA\hermes\hooks\sync_skills_to_obsidian.py",
            "$env:LOCALAPPDATA\hermes\scripts\sync_skills.py",
            "$env:USERPROFILE\.hermes\hooks\sync_skills_to_obsidian.py"
        )
        foreach ($s in $syncScripts) {
            if (Test-Path $s) {
                Write-Host "       Skill havuzu yenileniyor ($(Split-Path $s -Leaf))..." -NoNewline
                try {
                    & python $s 2>&1 | Out-Null
                    Write-Host " OK" -ForegroundColor Green
                } catch {
                    Write-Host " atlandi ($($_.Exception.Message))" -ForegroundColor Yellow
                }
                break
            }
        }
    } catch {
        Write-Host " HATA: $_" -ForegroundColor Red
    }
} else {
    Write-Host " bulunamadi (Hermes Agent yuklu degilse sorun degil)" -ForegroundColor Yellow
    Write-Host "       Hermes Agent kurulumu: https://hermes-agent.nousresearch.com" -ForegroundColor Cyan
}

# ---- 5. Verification ----
Write-Host "[4/4] Dogrulaniyor..." -NoNewline
try {
    $test = & python $BinPy pos
    if ($test -match "^\d+ \d+$") {
        Write-Host " OK (imlec: $test)" -ForegroundColor Green
    } else {
        Write-Host " $test" -ForegroundColor Yellow
    }
} catch {
    Write-Host " HATA: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  KURULUM TAMAMLANDI / INSTALL COMPLETE" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Terminal'den kullanim / CLI usage:" -ForegroundColor White
Write-Host "  hermesmouse pos" -ForegroundColor White
Write-Host "  hermesmouse click 500 300" -ForegroundColor White
Write-Host "  hermesmouse element Notepad list" -ForegroundColor White
Write-Host "  hermesmouse key esc" -ForegroundColor White
Write-Host "  hermesmouse screenshot" -ForegroundColor White
Write-Host "  hermesmouse run workflow.json" -ForegroundColor White
Write-Host ""
Write-Host "Hermes Agent ile kullanim (sohbetten):" -ForegroundColor White
Write-Host "  'Not Defteri'nde Dosya menusune tikla'" -ForegroundColor White
Write-Host "  'Chrome'da adres cubuguna git'" -ForegroundColor White
Write-Host "  'ekran goruntusu al'" -ForegroundColor White
Write-Host "  'hesap makinasini ac'" -ForegroundColor White
Write-Host ""
Write-Host "Dokuman / Docs: https://github.com/Watcher-Hermes/hermes-mouse" -ForegroundColor Cyan
