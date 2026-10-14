<#
Sets up a computer for WeSports development, or brings one up to date.
Safe to run again: what already exists is left alone.

  powershell -ExecutionPolicy Bypass -File bootstrap.ps1
  powershell -ExecutionPolicy Bypass -File bootstrap.ps1 -Personal erikbulowwesports/dev-env
  powershell -ExecutionPolicy Bypass -File bootstrap.ps1 -DryRun

-Root and -Personal are remembered in ~/.ws-dev-env.json, so a re-run needs
no arguments. Secrets and SSH keys are never copied: each computer logs in and
gets a key of its own.
#>
param(
    [string]$Personal,  # owner/repo of your own layer, same layout as this repo
    [string]$Root,      # where repos are cloned, default ~/source/repos
    [switch]$DryRun     # show what would happen, change nothing
)

$ErrorActionPreference = 'Continue'
$here = $PSScriptRoot
. (Join-Path $here 'lib.ps1')

$config = Get-DevEnvConfig
if ($Root) { $config.root = $Root }
if ($Personal) { $config.personal = $Personal }

function Step($text) { Write-Host "`n=== $text" -ForegroundColor Cyan }

function Act($what, [scriptblock]$do) {
    if ($DryRun) { Write-Host "   would: $what" -ForegroundColor DarkGray }
    else { Write-Host "   $what"; & $do }
}

function Refresh-Path {
    # winget writes PATH to the registry, not into this running window.
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User')
}

function Has($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

# Layers: this repo, then the personal one once it is cloned.
function Layers {
    $l = @($here)
    if ($config.personal) {
        $p = Join-Path $config.root ($config.personal.Split('/')[1])
        if (Test-Path $p) { $l += $p }
    }
    $l
}

# --- 1. Programs -------------------------------------------------------------
function Install-Packages($layer) {
    $file = Join-Path $layer 'packages.json'
    if (-not (Test-Path $file)) { return }
    Act "winget import $file" {
        winget import -i $file --ignore-unavailable --accept-package-agreements --accept-source-agreements
    }
    Refresh-Path
}

Step 'Programs'
Install-Packages $here
if (-not (Has 'pnpm')) { Act 'npm install -g pnpm@9' { npm install -g pnpm@9 } }

# --- 2. Git and GitHub -------------------------------------------------------
Step 'Git and GitHub'
if (-not (git config --global user.email)) {
    Write-Warning "git has no user.email. Set it with: git config --global user.email you@wesportsgroup.com"
}
if (-not (git config --global user.name)) {
    Write-Warning "git has no user.name. Set it with: git config --global user.name 'Your Name'"
}
gh auth status *> $null
if ($LASTEXITCODE -ne 0) { Act 'gh auth login (a browser window opens)' { gh auth login --hostname github.com --git-protocol https --web } }
Act 'gh auth setup-git' { gh auth setup-git }

# --- 3. Repos ----------------------------------------------------------------
function Clone($repo) {
    $path = Join-Path $config.root ($repo.Split('/')[1])
    if (Test-Path $path) { Write-Host "   exists: $repo"; return }
    Act "clone $repo" { gh repo clone $repo $path }
}

Step "Repos in $($config.root)"
Act "mkdir $($config.root)" { New-Item -ItemType Directory -Force $config.root | Out-Null }
if ($config.personal) { Clone $config.personal }
foreach ($layer in Layers) {
    if ($layer -ne $here) { Install-Packages $layer }
    $list = Join-Path $layer 'repos.txt'
    if (Test-Path $list) {
        Get-Content $list | Where-Object { $_ -match '^\s*[^#\s]' } | ForEach-Object { Clone $_.Trim() }
    }
}

# --- 4. Claude ---------------------------------------------------------------
Step 'Claude Code'
$claude = Join-Path $HOME '.claude'
$skills = Join-Path $claude 'skills'
Act "mkdir $skills" { New-Item -ItemType Directory -Force $skills | Out-Null }

# Each layer's CLAUDE.md is imported into the personal ~/.claude/CLAUDE.md, so
# nobody's own instructions are overwritten and a git pull updates everyone.
$memory = Join-Path $claude 'CLAUDE.md'
$current = if (Test-Path $memory) { Get-Content $memory -Raw } else { '' }
foreach ($layer in Layers) {
    $file = Join-Path $layer 'claude\CLAUDE.md'
    if (-not (Test-Path $file)) { continue }
    $line = '@' + (Get-ImportPath $file)
    if ($current -and $current.Contains($line)) { Write-Host "   imported: $line"; continue }
    Act "add $line to $memory" { Add-Content -Path $memory -Value "`n$line" -Encoding UTF8 }
}

# Skills are linked as directory junctions, which need neither admin nor
# Developer Mode. A skill that is already there is left alone.
foreach ($layer in Layers) {
    $dir = Join-Path $layer 'claude\skills'
    if (-not (Test-Path $dir)) { continue }
    foreach ($s in Get-ChildItem $dir -Directory) {
        $target = Join-Path $skills $s.Name
        if (Test-Path $target) { Write-Host "   exists: skills\$($s.Name)"; continue }
        Act "link skills\$($s.Name)" { New-Item -ItemType Junction -Path $target -Target $s.FullName | Out-Null }
    }
}

# wsg: Microsoft 365, Teams, Arena and one-time secret links, with its own skill.
python -m wsg --version *> $null
if ($LASTEXITCODE -ne 0) {
    Act 'install wsg-cli' { python -m pip install --user --upgrade git+https://github.com/Wesports-Scandinavia-AB/wsg-cli }
}
if (-not (Test-Path (Join-Path $skills 'wsg'))) { Act 'wsg skill install' { python -m wsg skill install } }

# --- 5. SSH key for this computer --------------------------------------------
Step 'SSH key'
$key = Join-Path $HOME '.ssh\id_ed25519'
if (Test-Path $key) {
    Write-Host "   exists: $key"
} else {
    Act "ssh-keygen $key" {
        New-Item -ItemType Directory -Force (Split-Path $key) | Out-Null
        # '""' because Windows PowerShell drops a bare empty argument.
        ssh-keygen -t ed25519 -f $key -N '""' -C "$env:USERNAME@$env:COMPUTERNAME"
    }
}
if (Test-Path "$key.pub") {
    Write-Host "   public key, safe to send to whoever adds it on a server:"
    Write-Host "   $(Get-Content "$key.pub")" -ForegroundColor Yellow
}

# --- 6. Done -----------------------------------------------------------------
if (-not $DryRun) { Save-DevEnvConfig $config }

Step 'Installed'
foreach ($cmd in 'git', 'gh', 'node', 'pnpm', 'python', 'code', 'claude', 'herdr') {
    if (Has $cmd) { Write-Host "   OK       $cmd" -ForegroundColor Green }
    else { Write-Host "   MISSING  $cmd  (open a new terminal and run again)" -ForegroundColor Yellow }
}
Write-Host "`nNext: open a new terminal, run 'claude' and log in, then 'python -m wsg graph login'." -ForegroundColor Cyan
