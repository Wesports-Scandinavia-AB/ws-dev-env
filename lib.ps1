# Shared by bootstrap.ps1 and check.ps1.

$DevEnvConfigPath = Join-Path $HOME '.ws-dev-env.json'

function Get-DevEnvConfig {
    $c = @{ root = (Join-Path $HOME 'source\repos'); personal = '' }
    if (Test-Path $DevEnvConfigPath) {
        $saved = Get-Content $DevEnvConfigPath -Raw | ConvertFrom-Json
        if ($saved.root) { $c.root = $saved.root }
        if ($saved.personal) { $c.personal = $saved.personal }
    }
    $c
}

function Save-DevEnvConfig($c) {
    $c | ConvertTo-Json | Set-Content -Path $DevEnvConfigPath -Encoding UTF8
}

# Claude's @import takes ~/... or an absolute path with forward slashes.
function Get-ImportPath($file) {
    $full = (Resolve-Path $file).Path
    if ($full.StartsWith($HOME, [StringComparison]::OrdinalIgnoreCase)) {
        $full = '~' + $full.Substring($HOME.Length)
    }
    $full.Replace('\', '/')
}
