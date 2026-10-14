<#
Run before leaving a computer. Lists everything that exists only here: changes
not committed, commits not pushed, stashes, ignored secret files, folders that
are not git repos, Claude memory and SSH keys. Reads only, changes nothing.

  powershell -ExecutionPolicy Bypass -File check.ps1 [-Root path]

Exit code 0 means nothing is lost by emptying the computer; the memory and
SSH lines are reminders and do not count.
#>
param([string]$Root)

. (Join-Path $PSScriptRoot 'lib.ps1')
$config = Get-DevEnvConfig
if ($Root) { $config.root = $Root }

$found = 0
# -Info is shown but does not count: it is a reminder, not something lost.
function Report($title, $lines, [switch]$Info) {
    $lines = @($lines | Where-Object { $_ })
    if (-not $lines) { return }
    if (-not $Info) { $script:found++ }
    Write-Host "`n== $title" -ForegroundColor $(if ($Info) { 'Cyan' } else { 'Yellow' })
    $lines | ForEach-Object { Write-Host "   $_" }
}

# Ignored files that usually hold secrets; never in git, so lost with the disk.
$secretPattern = '(^|/)\.env(\..+)?$|\.dev\.vars$|\.pem$|\.pfx$|\.key$|(^|/)secrets?\.json$|(^|/)credentials\.json$'

if (-not (Test-Path $config.root)) {
    Write-Warning "No repo folder at $($config.root). Pass -Root if they live elsewhere."
} else {
    foreach ($dir in Get-ChildItem $config.root -Directory) {
        $p = $dir.FullName
        if (-not (Test-Path (Join-Path $p '.git'))) {
            Report "$($dir.Name): not a git repo, copy by hand if you need it" @('(whole folder)')
            continue
        }
        if (-not (git -C $p remote)) {
            Report "$($dir.Name): no remote, everything in it exists only here" @('(whole repo)')
            continue
        }
        Report "$($dir.Name): not committed" (git -C $p status --porcelain)
        # One line per branch: a branch squash-merged on GitHub still lists every
        # commit, and the branch is what you push or delete.
        Report "$($dir.Name): not pushed" (
            git -C $p for-each-ref refs/heads --format='%(refname:short)' | ForEach-Object {
                $n = [int](git -C $p rev-list --count $_ --not --remotes)
                if ($n) { "$_  ($n commit(s) on no remote)" }
            })
        Report "$($dir.Name): stashes" (git -C $p stash list)
        Report "$($dir.Name): ignored files that look like secrets, move with wsg secret" (
            git -C $p ls-files --others --ignored --exclude-standard --directory |
                Where-Object { $_ -match $secretPattern })
    }
}

$projects = Join-Path $HOME '.claude\projects'
if (Test-Path $projects) {
    Report 'Claude memory, per project (copy the folders if you want them)' (
        Get-ChildItem $projects -Directory |
            Where-Object { Test-Path (Join-Path $_.FullName 'memory') } |
            ForEach-Object { "$($_.Name)\memory" }) -Info
}

$ssh = Join-Path $HOME '.ssh'
if (Test-Path $ssh) {
    Report 'SSH keys: do not move them, remove their public key from servers once this computer is gone' (
        Get-ChildItem $ssh -Filter '*.pub' | ForEach-Object { "$($_.Name)  $((Get-Content $_.FullName) -split ' ' | Select-Object -Last 1)" }) -Info
}

if ($found) {
    Write-Host "`n$found thing(s) above exist only on this computer." -ForegroundColor Yellow
    exit 1
}
Write-Host "`nNothing lost: everything is pushed, this computer can be emptied." -ForegroundColor Green
